from django.shortcuts import render, get_object_or_404
from .admin_views import gsheet_sync_view
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.http import HttpResponse, JsonResponse
import json
import logging
import re
from core.models import WhatsAppMessage, WhatsAppForm, Lead, APISetting, PricingPlan
from tenants.models import Tenant
from crm.models import Donatur, TransaksiDonasi
from core.services.starsender import StarSenderService
from core.services.ai_service import AIService
from core.services.ipaymu import IPaymuService
from .views_help import get_tutorial_api, chat_assistant_api

logger = logging.getLogger(__name__)

def homepage(request):
    tenant = getattr(request, 'tenant', None)
    
    if tenant:
        # --- TENANT LANDING PAGE ---
        from crm.models import Program
        programs = Program.objects.filter(tenant=tenant)
        
        return render(request, 'core/tenant_landing.html', {
            'tenant': tenant,
            'programs': programs,
            'seo_title': tenant.seo_title or f"Portal {tenant.name}",
            'seo_description': tenant.seo_description or tenant.description[:160] if tenant.description else "",
        })
    
    # --- GLOBAL HOMEPAGE ---
    tenants = Tenant.objects.filter(is_active=True)
    pricing_plans = PricingPlan.objects.filter(is_active=True).order_by('order')
    return render(request, 'core/homepage.html', {'tenants': tenants, 'pricing_plans': pricing_plans})

def features(request):
    """Features & Solutions Page"""
    return render(request, 'core/features.html')

def musafa(request):
    """MUSAFA Landing Page (Wakaf Quran)"""
    # Try to get dynamic CS Number from APISetting (Global or Tenant)
    tenant = getattr(request, 'tenant', None)
    
    cs_setting = APISetting.objects.filter(key_name='CS_WA_NUMBER', is_active=True)
    
    cs_number = "6289656463990" # Default Fallback

    if tenant:
        # Tenant Context: Strict
        setting = cs_setting.filter(tenant=tenant).first()
        if setting:
            cs_number = setting.value.strip()
    else:
        # Global Context: Try Global (tenant=None) -> Fallback to Main Tenant (ID=1)
        # 1. Global
        g_setting = cs_setting.filter(tenant__isnull=True).first()
        if g_setting:
             cs_number = g_setting.value.strip()
        else:
            # 2. Main Tenant (Pondok IT)
            t_setting = cs_setting.filter(tenant__id=1).first()
            if t_setting:
                 cs_number = t_setting.value.strip()

    return render(request, 'core/musafa_landing.html', {'cs_number': cs_number})

def process_ai_reply(message, tenant, sender, sender_name):
    """
    Background worker to get AI completion and send WA reply.
    """
    import threading
    try:
        from core.services.ai_service import AIService
        from core.services.starsender import StarSenderService
        
        ai_response = AIService.get_completion(message, tenant=tenant, sender_name=sender_name, sender_phone=sender)
        if ai_response:
            StarSenderService.send_message(
                to=sender,
                body=ai_response,
                tenant=tenant
            )
    except Exception as e:
        print(f"Error in background AI process: {e}")

@csrf_exempt
def webhook_whatsapp(request, tenant_slug=None):
    """
    Webhook endpoint for StarSender WhatsApp messages
    URL: /webhook/whatsapp/ or /webhook/whatsapp/<tenant_slug>/
    """
    # 0. RESOLVE SPECIFIC TENANT (Initialize early to avoid UnboundLocalError)
    from core.services.ai_service import AIService
    current_tenant = None
    if tenant_slug:
        current_tenant = Tenant.objects.filter(subdomain=tenant_slug).first()
        logger.debug(f"Tenant resolved from slug: {current_tenant}")
    
    # Fallback to request context only
    if not current_tenant and hasattr(request, 'tenant') and request.tenant:
        current_tenant = request.tenant
        logger.debug(f"Tenant resolved from request context: {current_tenant}")

    if current_tenant:
        from core.models import set_current_tenant
        set_current_tenant(current_tenant)

    # Log every webhook call immediately
    logger.info(f"[WEBHOOK CALLED] Method: {request.method}, Tenant Slug: {tenant_slug}")
    
    if request.method == 'POST':
        try:
            # Log raw request body for debugging
            raw_body = request.body.decode('utf-8')
            logger.debug(f"[WEBHOOK RAW BODY] {raw_body[:200]}")
            
            data = json.loads(request.body)
            logger.info(f"[WEBHOOK DATA] Parsed successfully: {list(data.keys())}")
            
            # 2. Extraction & Normalization
            device = data.get('device', '').strip()
            message = data.get('message', '').strip()
            sender = data.get('from', '').strip()
            sender_name = data.get('push_name') or data.get('pushName') or data.get('name') or ''
            is_me = data.get('is_me', False)
            
            logger.info(f"[WEBHOOK EXTRACTED] From: {sender}, Device: {device}, Message: {message[:50]}, is_me: {is_me}")

            # Normalize for comparisons and storage
            import re
            def clean_num(n): return re.sub(r'\D', '', str(n)) if n else ""
            c_sender = clean_num(sender)
            c_device = clean_num(device)
            db_sender = c_sender or sender

            # --- CHANNEL DETECTION ---
            prompt_key = 'AI_SYSTEM_PROMPT'
            api_key_name = 'AI_PROVIDER' # Default dummy or global, but we use WHATSAPP key for sending
            channel_type = Lead.Type.SANTRI
            
            cs_santri = clean_num(AIService.get_setting('CS_SANTRI_NUMBER', current_tenant))
            cs_donatur = clean_num(AIService.get_setting('CS_DONATUR_NUMBER', current_tenant))
            
            if c_device and cs_donatur and c_device == cs_donatur:
                prompt_key = 'AI_DONATUR_PROMPT'
                api_key_name = 'WHATSAPP_API_KEY_DONATUR'
                channel_type = Lead.Type.DONATUR
                logger.info("[CHANNEL] Detected: DONATUR")
            elif c_device and cs_santri and c_device == cs_santri:
                prompt_key = 'AI_SANTRI_PROMPT'
                api_key_name = 'WHATSAPP_API_KEY_SANTRI'
                channel_type = Lead.Type.SANTRI
                logger.info("[CHANNEL] Detected: SANTRI")
            else:
                logger.info(f"[CHANNEL] Default: SANTRI (Device: {c_device})")

            # Resolve actual API Key value for sending
            active_api_key = AIService.get_setting(api_key_name, current_tenant) if api_key_name != 'AI_PROVIDER' else None

            # --- INITIAL LOG & DEDUPLICATION ---
            # 1. Deduplication - Block exact duplicate within 30s
            from django.utils import timezone
            from datetime import timedelta
            
            duplicate_exists = WhatsAppMessage.objects.filter(
                sender=db_sender, 
                message=message, 
                created_at__gte=timezone.now() - timedelta(seconds=30)
            ).exists()
            
            if duplicate_exists:
                logger.info(f"[DUPLICATE BLOCKED] Same message from {db_sender} within 30s")
                return HttpResponse('OK', status=200)

            # 2. Log Message (Unified for Inbound & Outbound)
            try:
                WhatsAppMessage.objects.create(
                    tenant=current_tenant,
                    device=device,
                    message=message,
                    sender=db_sender,
                    sender_name=sender_name,
                    is_outbound=is_me,
                    recipient=data.get('to') if is_me else None,
                    raw_data=data
                )
                logger.info(f"Message logged ({'OUT' if is_me else 'IN'}): {db_sender} | {message[:50]}")
            except Exception as e:
                logger.error(f"Failed to log message: {e}")

            # --- SYSTEM & ECHO FILTERS ---
            
            # 1. Handle is_me flag (Gateway notification about new lead)
            # 1. Handle is_me flag (Gateway notification / Outbound Echo)
            if is_me:
                logger.info(f"[is_me=True] Processing outbound message: {message[:100]}")
                
                # Check for recursion/loop (Messages we sent as notifications)
                if message.startswith("🔔") or message.startswith("Lead Baru Terdeteksi!"):
                    logger.info("[is_me=Blocked] Blocking notification loop.")
                    return HttpResponse('OK', status=200)

                # Parse lead info from message
                lead_name = None
                lead_phone = None
                
                if "Lead Baru Terdeteksi!" in message:
                    parts = message.split('\n\n')
                    if len(parts) >= 2:
                        data_parts = parts[1].split('#')
                        if len(data_parts) >= 4:
                            lead_name = data_parts[0].strip()
                            lead_phone = data_parts[3].strip()
                
                if not lead_name or not lead_phone:
                    # Regex Match
                    lead_name_match = re.search(r'Nama:\s*([^,\n]+)', message)
                    lead_phone_match = re.search(r'Phone:\s*(\d+)', message)
                    if lead_name_match and lead_phone_match:
                        lead_name = lead_name_match.group(1).strip()
                        lead_phone = lead_phone_match.group(1).strip()

                if lead_name and lead_phone:
                    from users.models import User, Role
                    cs_role = Role.objects.filter(tenant=current_tenant, slug='cs').first() if current_tenant else Role.objects.filter(tenant__isnull=True, slug='cs').first()
                    
                    if cs_role:
                        cs_users = User.all_objects.filter(tenant=current_tenant, role=cs_role, is_active=True)
                        notification_msg = f"🔔 *Lead Baru Masuk!*\n\nNama: {lead_name}\nPhone: {lead_phone}\n\nSilakan follow up segera."
                        for cs in cs_users:
                            if cs.phone_number and clean_num(cs.phone_number) != lead_phone:
                                StarSenderService.send_message(to=cs.phone_number, body=notification_msg, tenant=current_tenant)
                
                # Finished with is_me logic
                return HttpResponse('OK', status=200)

            # 2. Block if Sender matches Device (Gateway sending to itself)
            if c_device and c_sender == c_device:
                logger.debug(f"Blocked: Sender matches device (gateway self-message)")
                return HttpResponse('OK', status=200)

            # 3. Tenant Gateway Phone Block (Sender is the gateway itself)
            # DISABLED: Allow gateway numbers to also be processed as leads (for testing)
            # if c_sender and Tenant.objects.filter(phone_number__icontains=c_sender[-10:]).exists():
            #     logger.debug(f"Blocked: Sender is a known tenant gateway")
            #     return HttpResponse('OK', status=200)
            
            # 4. Global User Phone Block (Sender is ANY known staff/user)
            # DISABLED: Allow registered users to also be processed as leads
            from users.models import User
            # if c_sender and User.all_objects.filter(phone_number__icontains=c_sender[-10:]).exists():
            #     logger.debug(f"Blocked: Sender is a known staff/user")
            #     return HttpResponse('OK', status=200)

            # Identify Sender
            sender = db_sender 
            internal_user = User.all_objects.filter(
                is_active=True, 
                phone_number__icontains=sender[-10:]
            ).first()
            
            replied = False

            # --- FLOW BRANCHING ---

            if internal_user and internal_user.is_staff:
                # 5. INTERNAL FLOW (Staff Commands)
                logger.info(f"[STAFF] Processing staff command from {internal_user.username}")
                from core.services.staff_command_service import StaffCommandService
                staff_msg = StaffCommandService.process_message_v2(current_tenant, message, internal_user)
                if staff_msg:
                    StarSenderService.send_message(to=sender, body=staff_msg, tenant=current_tenant, api_key_override=active_api_key)
                    logger.info(f"[STAFF] Response sent to {internal_user.username}")
                else:
                    # If it's a staff but not a valid command keyword, use AI fallback
                    logger.info(f"[STAFF] Message from {internal_user.username} - No command matched, using AI fallback")
                    try:
                        # 5b. AI Fallback for Staff (with NLP Command Support)
                        # Inject staff-specific instructions
                        staff_prompt = AIService.get_system_prompt(tenant=current_tenant, query=message, prompt_key=prompt_key)
                        staff_prompt += StaffCommandService.get_ai_instructions()
                        
                        ai_response = AIService.get_completion(
                            message, 
                            tenant=current_tenant, 
                            sender_name=internal_user.username, 
                            sender_phone=sender,
                            system_prompt=staff_prompt
                        )
                        
                        if ai_response:
                            final_msg = ai_response
                            
                            # Detect and Process AI-generated EXEC tags
                            # Format: [EXEC: KEYWORD/data1#data2#...]
                            if "[EXEC:" in ai_response:
                                exec_match = re.search(r'\[EXEC:\s*([^\]]+)\]', ai_response)
                                if exec_match:
                                    cmd_str = exec_match.group(1).strip()
                                    logger.info(f"[STAFF-AI] AI generated EXEC command: {cmd_str}")
                                    
                                    # Execute the extracted command
                                    exec_res = StaffCommandService.process_message_v2(current_tenant, cmd_str, internal_user)
                                    if exec_res:
                                        # Remove the tag from final message and append result
                                        final_msg = ai_response.replace(exec_match.group(0), "").strip()
                                        final_msg += f"\n\n⚙️ *Sistem:* {exec_res}"
                            
                            StarSenderService.send_message(to=sender, body=final_msg, tenant=current_tenant, api_key_override=active_api_key)
                            logger.info(f"[STAFF-AI] Response sent to {internal_user.username}")
                        else:
                            logger.warning(f"[STAFF-AI] No response generated for {internal_user.username}")
                    except Exception as e:
                        logger.error(f"[STAFF-AI] Error: {e}")
                
                # IMPORTANT: Set replied=True so it doesn't fall through to public lead flow
                replied = True
            
            if not replied:
                # 6. EXTERNAL FLOW (Public/Lead)
                # Sort forms by keyword length DESC to avoid "D" matching before "DAFTAR"
                forms = WhatsAppForm.objects.filter(tenant=current_tenant, is_active=True) if current_tenant else WhatsAppForm.objects.filter(tenant__isnull=True, is_active=True)
                forms = sorted(forms, key=lambda x: len(x.keyword.strip()), reverse=True)
                
                for form in forms:
                    keyword = form.keyword.strip()
                    # Use regex for strict matching (Word Boundary or Separator)
                    # Pattern: ^KEYWORD(\b|SEPARATOR|$)
                    import re
                    pattern = rf"^{re.escape(keyword)}(\b|{re.escape(form.separator) if form.separator else ''}|\s|$)"
                    match = re.search(pattern, message, re.IGNORECASE)
                    
                    if match:
                        # Found matching form
                        logger.info(f"[FORM MATCH] Keyword '{keyword}' matched for form ID {form.id}")
                        # Calculate body: remove the matched prefix
                        matched_str = match.group(0)
                        # If the match ended with a separator/boundary char that belongs to the message body, 
                        # we need to be careful. But match.group(0) includes the boundary.
                        
                        # Simpler: just use original length but check if we need to trim the boundary char
                        body = message[len(keyword):].strip()
                        
                        # Clean multiple separators or spaces at start
                        if form.separator:
                            while body.startswith(form.separator) or body.startswith(' '):
                                body = body[1:].strip()
                            
                            # STRICTOR MATCHING:
                            # 1. Body must not be empty (avoid "DAFTAR" alone creating empty leads)
                            # 2. If body has multiple words, separator MUST be present.
                            if not body:
                                logger.info(f"[FORM SKIP] Body is empty, skipping direct form match.")
                                continue
                                
                            if form.separator not in body and len(body.split()) > 1:
                                logger.info(f"[FORM SKIP] Body '{body}' looks like a sentence, skipping direct form match.")
                                continue
                        
                        parts = [p.strip() for p in body.split(form.separator)] if form.separator else [body]
                        fields = [f.strip() for f in form.field_map.split(form.separator)] if form.separator else ['data']
                        
                        # Map data
                        lead_data = {}
                        for i in range(min(len(parts), len(fields))):
                            lead_data[fields[i].lower()] = parts[i]
                        
                        lead_name_from_data = lead_data.get('nama') or lead_data.get('name')
                        # Sanitize: if name in data is same as keyword, it's likely just empty trigger
                        if lead_name_from_data and lead_name_from_data.upper() == keyword.upper():
                            lead_name_from_data = None
                        
                        # PRIORITY: Manual Data > WA Profile Name > Previous Lead Name > "Unknown"
                        lead_name = lead_name_from_data or sender_name or "Unknown"
                        lead_location = lead_data.get('alamat') or lead_data.get('kota') or lead_data.get('asal') or ""
                        
                        # Create or Update Lead
                        logger.info(f"[FORM EXEC] Creating/Updating lead from form match: {lead_name} ({c_sender})")
                        lead, created = Lead.objects.get_or_create(
                            tenant=current_tenant,
                            phone_number=c_sender,
                            defaults={
                                'name': lead_name,
                                'type': channel_type,
                                'data': lead_data,
                                'status': Lead.Status.NEW
                            }
                        )
                        if not created:
                            # If existing lead is "Unknown" or empty, update with new name
                            if lead.name in [None, "", "Unknown", "unknown"] and lead_name != "Unknown":
                                lead.name = lead_name
                            
                            lead.data = lead_data
                            lead.status = Lead.Status.NEW
                            lead.save()
                        logger.info(f"[LEAD-DEBUG] {'CREATED' if created else 'UPDATED'} via FORM: {lead.name} | Status: {lead.status}")
                        
                        # Auto-Assign CS
                        from core.services.lead_workflow_service import LeadWorkflowService
                        assigned_cs = LeadWorkflowService.assign_to_cs(lead)
                        
                        # === STEP 1: Generate AI Greeting for Lead ===
                        ai_greeting = None
                        try:
                            # Build context for AI
                            greeting_context = f"Nama Pendaftar: {lead_name}"
                            if lead_location:
                                greeting_context += f", Asal: {lead_location}"
                            
                            if assigned_cs:
                                greeting_context += f"\nCS yang bertugas: {assigned_cs.get_full_name() or assigned_cs.username} ({assigned_cs.phone_number})"

                            greeting_prompt = (
                                f"Buatkan pesan sambutan hangat untuk calon santri/donatur baru yang baru mendaftar.\n"
                                f"Data pendaftar:\n{greeting_context}\n\n"
                                f"Pesan harus:\n"
                                f"- Menyapa dengan nama pendaftar\n"
                                f"- Mengucapkan terima kasih atas pendaftaran\n"
                                f"- Menginfokan bahwa mereka akan dibantu oleh CS tersebut di atas (sebutkan nama CS-nya) dan akan segera dihubungi melalui nomor pribadinya.\n"
                                f"- Ramah dan profesional\n"
                                f"- Maksimal 3 kalimat"
                            )
                            
                            strict_prompt = (
                                "Role: Friendly Admin of Pondok Pesantren.\n"
                                "Task: Generate a warm greeting message for new registrant.\n"
                                "Constraint: Output ONLY the final message content. NO preamble, NO meta-talk.\n"
                                "Your output will be sent directly to the registrant on WhatsApp."
                            )
                            
                            ai_greeting = AIService.get_completion(
                                greeting_prompt,
                                tenant=current_tenant,
                                sender_name=lead_name,
                                system_prompt=AIService.get_system_prompt(tenant=current_tenant, query=greeting_prompt, prompt_key=prompt_key) + "\n\n" + strict_prompt,
                                sender_phone=sender
                            )
                            
                            if ai_greeting:
                                logger.info(f"[AI GREETING] Generated for {lead_name}")
                            else:
                                logger.warning(f"[AI GREETING] Failed to generate, using fallback")
                                ai_greeting = f"Terima kasih {lead_name} atas pendaftarannya. Tim kami akan segera menghubungi Anda."
                        
                        except Exception as e:
                            logger.error(f"[AI GREETING] Error: {e}")
                            ai_greeting = f"Terima kasih {lead_name} atas pendaftarannya. Tim kami akan segera menghubungi Anda."
                        
                        # === STEP 2: Send AI Greeting to Lead ===
                        if ai_greeting:
                            StarSenderService.send_message(to=sender, body=ai_greeting, tenant=current_tenant, api_key_override=active_api_key)
                            logger.info(f"[GREETING SENT] To lead {lead_name} ({sender})")
                        
                        # === STEP 3: Handle Notifications ===
                        # Redundant manual CS notification removed.
                        # Notification is handled by LeadWorkflowService.assign_to_cs(lead)
                        # and the is_me block in this webhook (for broadcast to all CS).
                        pass
                        
                        # Auto-Insert to CRM if configured
                        if form.auto_insert:
                            try:
                                from crm.services import CRMService
                                res_obj, auto_msg = CRMService.convert_lead(lead, form.lead_type)
                                if res_obj:
                                    logger.info(f"[AUTO INSERT] {auto_msg}")
                            except Exception as e:
                                logger.error(f"[AUTO INSERT] Error: {e}")
                        
                        replied = True
                        break

                # B. AI Fallback (Natural interaction for undefined formats)
                if not replied:
                    logger.info(f"[AI FALLBACK] No form matched, using AI for sender: {sender}")
                    
                    # Synchronous AI response (no threading)
                    try:
                        ai_response = AIService.get_completion(
                            message, 
                            tenant=current_tenant, 
                            sender_name=sender_name, 
                            sender_phone=sender,
                            system_prompt=AIService.get_system_prompt(tenant=current_tenant, query=message, prompt_key=prompt_key)
                        )
                        if ai_response:
                            logger.info(f"[AI RAW RESPONSE] {ai_response}")
                            extra_messages = []
                            
                            # CHECK FOR INVOICE CREATION
                            # Format: [EXEC: CREATE_INVOICE] nominal#keterangan
                            invoice_pattern = r'\\?\[EXEC:\s*CREATE[\\_]*INVOICE\\?\]'
                            if ai_response and re.search(invoice_pattern, ai_response):
                                try:
                                    match = re.search(invoice_pattern + r'\s*(.*)', ai_response)
                                    if match:
                                        raw_data = match.group(1).strip()
                                        ai_response = re.sub(invoice_pattern + r'\s*.*', '', ai_response).strip()
                                        raw_data = raw_data.rstrip(']').strip()
                                        
                                        parts = [p.strip() for p in raw_data.split('#')]
                                        nominal_str = parts[0]
                                        keterangan = parts[1] if len(parts) > 1 else 'Infaq Shodaqoh'
                                        
                                        # Clean nominal
                                        nominal = int(re.sub(r'\D', '', nominal_str))
                                        
                                        # Get/Create Donatur
                                        donatur, _ = Donatur.objects.get_or_create(
                                            tenant=current_tenant,
                                            no_hp=sender,
                                            defaults={
                                                'nama_donatur': sender_name or "Hamba Allah",
                                                'kategori': Donatur.Kategori.INSIDENTIL
                                            }
                                        )
                                        
                                        # Get/Create Default Program
                                        from crm.models import Program, Santri, TagihanProgram
                                        lower_ket = keterangan.lower()
                                        
                                        # --- SCENARIO 1: REGISTRATION (Biaya Pendaftaran) ---
                                        if any(x in lower_ket for x in ['pendaftar', 'daftar', 'registrasi', 'adm', 'formulir']):
                                            logger.info(f"[DEBUG REG] Starting Registration Flow for {sender}")
                                            # 1. Create/Get Santri (Calon)
                                            # Use REG-{phone} as temporary NIS
                                            temp_nis = f"REG-{sender}"
                                            santri, created = Santri.objects.get_or_create(
                                                tenant=current_tenant,
                                                nis=temp_nis,
                                                defaults={
                                                    'nama_lengkap': sender_name or "Calon Santri",
                                                    'nama_wali': sender_name or "Wali Santri",
                                                    'no_hp_wali': sender,
                                                    'status': Santri.Status.CALON
                                                }
                                            )
                                            logger.info(f"[DEBUG REG] Santri: {santri.id} (Created: {created}, Tenant: {santri.tenant})")
                                            
                                            # 2. Get/Create Program Pendaftaran
                                            program, _ = Program.objects.get_or_create(
                                                tenant=current_tenant,
                                                jenis=Program.Jenis.PENDAFTARAN,
                                                defaults={'nama_program': 'Biaya Pendaftaran Santri', 'is_active': True}
                                            )
                                            
                                            # 3. Create TagihanProgram
                                            # Check if unpaid bill exists to avoid duplicates
                                            tagihan = TagihanProgram.objects.filter(
                                                tenant=current_tenant,
                                                santri=santri,
                                                program=program,
                                                status=TagihanProgram.Status.BELUM_LUNAS
                                            ).first()
                                            
                                            if not tagihan:
                                                from django.utils import timezone
                                                import datetime
                                                tagihan = TagihanProgram.objects.create(
                                                    tenant=current_tenant,
                                                    santri=santri,
                                                    program=program,
                                                    nominal=nominal,
                                                    jatuh_tempo=timezone.now().date() + datetime.timedelta(days=7),
                                                    status=TagihanProgram.Status.BELUM_LUNAS,
                                                    catatan=keterangan
                                                )
                                                logger.info(f"[DEBUG REG] Created New Tagihan: {tagihan.id}")
                                            else:
                                                logger.info(f"[DEBUG REG] Using Existing Tagihan: {tagihan.id}")
                                            
                                            # 4. Generate iPaymu Link
                                            service = IPaymuService(tenant=current_tenant)
                                            # Use TAG-PROG-{id} as reference
                                            res, err = service.create_payment(
                                                amount=nominal,
                                                reference_id=f"TAG-PROG-{tagihan.id}",
                                                name=santri.nama_lengkap,
                                                email="calon@pondokit.id",
                                                phone=santri.no_hp_wali,
                                                description=keterangan
                                            )
                                            
                                            if res:
                                                logger.info(f"[DEBUG REG] IPaymu Success. URL: {res['url']}")
                                                tagihan.external_id = res['session_id']
                                                tagihan.payment_url = res['url']
                                                tagihan.save()
                                                logger.info(f"[DEBUG REG] Saved Tagihan with URL")
                                                
                                                ai_response += "\n\nTerima kasih."
                                                extra_messages.append(f"Silakan selesaikan pembayaran pendaftaran via link berikut:\n{res['url']}")
                                                logger.info(f"[AI REGISTRATION] Link generated for {sender}: {res['url']}")
                                            else:
                                                logger.error(f"[AI REGISTRATION] Failed to generate link: {err}")
                                                ai_response += "\n\n(Maaf, sistem sedang gangguan dalam membuat link pembayaran. Mohon coba lagi nanti)."


                                        # --- SCENARIO 2: DONATION (Infaq/Wakaf/etc) ---
                                        else:
                                            program, _ = Program.objects.get_or_create(
                                                tenant=current_tenant,
                                                jenis=Program.Jenis.DONASI,
                                                defaults={'nama_program': 'Donasi Umum', 'is_active': True}
                                            )
                                            
                                            # Create TransaksiDonasi
                                            transaksi = TransaksiDonasi.objects.create(
                                                tenant=current_tenant,
                                                donatur=donatur,
                                                program=program,
                                                nominal=nominal,
                                                keterangan=keterangan,
                                                status=TransaksiDonasi.Status.PENDING
                                            )
                                            
                                            # Generate iPaymu Link
                                            service = IPaymuService(tenant=current_tenant)
                                            res, err = service.create_payment(
                                                amount=nominal,
                                                reference_id=f"DON-{transaksi.id}",
                                                name=donatur.nama_donatur,
                                                email="donatur@pondokit.id",
                                                phone=donatur.no_hp,
                                                description=keterangan
                                            )
                                            
                                            if res:
                                                transaksi.external_id = res['session_id']
                                                transaksi.payment_url = res['url']
                                                transaksi.save()
                                                
                                                ai_response += "\n\nTerima kasih."
                                                extra_messages.append(f"Silakan selesaikan pembayaran donasi via link berikut:\n{res['url']}")
                                                logger.info(f"[AI DONATION] Link generated for {sender}: {res['url']}")
                                            else:
                                                logger.error(f"[AI DONATION] Failed to generate link: {err}")
                                                ai_response += "\n\n(Maaf, sistem sedang gangguan dalam membuat link pembayaran. Mohon coba lagi nanti)."

                                    # --- AUTO-LEAD CREATION FROM INVOICE ---
                                    # Ensure every invoice results in a Lead for CS to track
                                    l_type = Lead.Type.SANTRI if any(x in lower_ket for x in ['pendaftar', 'daftar', 'registrasi', 'adm', 'formulir']) else Lead.Type.DONATUR
                                    
                                    # Robust Lead Retrieval (handle duplicates)
                                    lead_obj = Lead.objects.filter(tenant=current_tenant, phone_number=sender).order_by('-id').first()
                                    l_created = False
                                    if not lead_obj:
                                        lead_obj = Lead.objects.create(
                                            tenant=current_tenant,
                                            phone_number=sender,
                                            name=sender_name or "Hamba Allah",
                                            type=l_type,
                                            score=90,
                                            status=Lead.Status.NEW,
                                            data={'keterangan': keterangan}
                                        )
                                        l_created = True
                                    
                                    if not l_created:
                                        lead_obj.type = l_type
                                        lead_obj.score = 90
                                        if sender_name: lead_obj.name = sender_name
                                        lead_obj.save()

                                    # Auto-Assign CS & Notify
                                    from core.services.lead_workflow_service import LeadWorkflowService
                                    LeadWorkflowService.assign_to_cs(lead_obj)
                                    logger.info(f"[AI AUTO-LEAD] Created/Updated lead for {sender} from Invoice.")

                                except Exception as e:
                                    logger.error(f"[AI DONATION ERROR] {e}")

                            # CHECK FOR LEAD SAVE COMMAND
                            # Format: [EXEC: SAVE_LEAD] nama#kota#sekolah
                            # Regex handles optional backslashes (\[, \_) which AI might output
                            tag_pattern = r'\\?\[EXEC:\s*SAVE[\\_]*LEAD\\?\]'
                            import re
                            if re.search(tag_pattern, ai_response):
                                try:
                                    # Capture everything after the tag
                                    match = re.search(tag_pattern + r'\s*(.*)', ai_response)
                                    if match:
                                        raw_data = match.group(1).strip()
                                        
                                        # Remove the tag and its data from the response sent to user
                                        # Use non-greedy match for the data part until end of line or next bracket
                                        ai_response = re.sub(tag_pattern + r'\s*[^\[]*', '', ai_response).strip()
                                        
                                        # Clean raw_data (remove potential trailing ])
                                        raw_data = raw_data.rstrip(']').strip()
                                        
                                        # Parse data
                                        parts = [p.strip() for p in raw_data.split('#')]
                                        l_name = parts[0] if len(parts) > 0 else "Unknown"
                                        l_city = parts[1] if len(parts) > 1 else "-"
                                        l_school = parts[2] if len(parts) > 2 else "-"
                                        
                                        # New: Handle optional 4th part for lead type
                                        l_type_raw = parts[3].upper() if len(parts) > 3 else channel_type # Default to channel detection
                                        l_type = Lead.Type.DONATUR if "DONA" in l_type_raw else Lead.Type.SANTRI
                                        
                                        # New: Handle optional 5th part for score
                                        try:
                                            l_score = int(parts[4]) if len(parts) > 4 else 0
                                        except:
                                            l_score = 0
                                            
                                        # Robust Lead Retrieval
                                        lead = Lead.objects.filter(tenant=current_tenant, phone_number=sender).order_by('-id').first()
                                        created = False
                                        if not lead:
                                            lead = Lead.objects.create(
                                                tenant=current_tenant,
                                                phone_number=sender,
                                                name=l_name,
                                                type=l_type,
                                                score=l_score,
                                                status=Lead.Status.NEW,
                                                data={'kota': l_city, 'sekolah': l_school}
                                            )
                                            created = True
                                        
                                        if not created:
                                            lead.name = l_name
                                            lead.type = l_type # Update type if it changed during conversation
                                            lead.score = l_score
                                            lead.data.update({'kota': l_city, 'sekolah': l_school})
                                            lead.status = Lead.Status.NEW
                                            lead.save()
                                            
                                        logger.info(f"[AI LEAD MATCH] Created lead {l_name} ({l_type}) from AI conversation.")
                                        
                                        # Auto-Assign CS & Notify
                                        from core.services.lead_workflow_service import LeadWorkflowService
                                        LeadWorkflowService.assign_to_cs(lead)
                                        
                                except Exception as e:
                                    logger.error(f"[AI LEAD ERROR] Failed to save lead from AI: {e}")

                            StarSenderService.send_message(to=sender, body=ai_response, tenant=current_tenant, api_key_override=active_api_key)
                            
                            # Send extra messages (like payment links) separately
                            for extra_msg in extra_messages:
                                import time
                                time.sleep(1) # Small delay for better UX
                                StarSenderService.send_message(to=sender, body=extra_msg, tenant=current_tenant, api_key_override=active_api_key)
                                
                            logger.info(f"[AI] Response sent to {sender} (and {len(extra_messages)} extra messages)")
                        else:
                            logger.warning(f"[AI] No response generated for {sender}")
                    except Exception as e:
                        logger.error(f"[AI] Error generating response: {e}")
                    
                    replied = True

            return HttpResponse('OK', status=200)
        
        except json.JSONDecodeError as e:
            logger.error(f"[WEBHOOK ERROR] JSON decode failed: {e}")
            logger.error(f"[WEBHOOK ERROR] Raw body: {request.body}")
            return HttpResponse('Invalid JSON', status=400)
        
        except Exception as e:
            logger.error(f"[WEBHOOK ERROR] Unexpected error: {e}")
            import traceback
            logger.error(f"[WEBHOOK ERROR] Traceback: {traceback.format_exc()}")
            return HttpResponse('Internal Error', status=500)
            
    return HttpResponse('Method Not Allowed', status=405)

