from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, JsonResponse
import json
import logging
from .models import WhatsAppMessage, WhatsAppAutoReply, WhatsAppForm, Lead, PricingPlan
from core.services.starsender import StarSenderService
from core.services.ai_service import AIService
from tenants.models import Tenant
from django.shortcuts import get_object_or_404

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

def process_ai_reply(message, tenant, sender, sender_name):
    """
    Background worker to get AI completion and send WA reply.
    """
    import threading
    try:
        from core.services.ai_service import AIService
        from core.services.starsender import StarSenderService
        
        ai_response = AIService.get_completion(message, tenant=tenant, sender_name=sender_name)
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
            
            # 2. Basic Extraction & Normalization
            device = data.get('device', '').strip()
            message = data.get('message', '').strip()
            sender = data.get('from', '').strip()
            sender_name = data.get('push_name') or data.get('pushName') or data.get('name') or ''
            is_me = data.get('is_me', False)
            
            logger.info(f"[WEBHOOK EXTRACTED] From: {sender}, Device: {device}, Message: {message[:50]}, is_me: {is_me}")

            # Normalize for comparisons
            import re
            def clean_num(n): return re.sub(r'\D', '', str(n)) if n else ""
            c_sender = clean_num(sender)
            c_device = clean_num(device)

            # --- SYSTEM & ECHO FILTERS ---
            
            # 1. Handle is_me flag (Gateway notification about new lead)
            if is_me:
                logger.info(f"[is_me=True] Gateway notification received: {message[:100]}")
                
                # Check for recursion/loop (Messages we sent as notifications)
                # 🔔 *Lead Baru Masuk!* (From broadcast)
                # Lead Baru Terdeteksi! (From LeadWorkflowService)
                if message.startswith("🔔") or message.startswith("Lead Baru Terdeteksi!"):
                    logger.info("[is_me=Blocked] Ignoring our own notification to avoid loop.")
                    return HttpResponse('OK', status=200)

                # Parse lead info from message
                # Format A: "🔔 *Lead Baru Masuk!* Nama: John, Phone: 081234567890" (Echo from our broadcast)
                # Format B: "Lead Baru Terdeteksi! nama#kota#sekolah#phone" (From LeadWorkflowService)
                
                lead_name = None
                lead_phone = None
                
                if "Lead Baru Terdeteksi!" in message:
                    # Parse Format B: Lead Baru Terdeteksi!\n\nnama#kota#sekolah#phone
                    parts = message.split('\n\n')
                    if len(parts) >= 2:
                        data_parts = parts[1].split('#')
                        if len(data_parts) >= 4:
                            lead_name = data_parts[0].strip()
                            lead_phone = data_parts[3].strip()
                
                if not lead_name or not lead_phone:
                    # Try Format A (Regex)
                    lead_name_match = re.search(r'Nama:\s*([^,\n]+)', message)
                    lead_phone_match = re.search(r'Phone:\s*(\d+)', message)
                    if lead_name_match and lead_phone_match:
                        lead_name = lead_name_match.group(1).strip()
                        lead_phone = lead_phone_match.group(1).strip()

                if lead_name and lead_phone:
                    # Find CS users for this tenant
                    from users.models import User, Role
                    cs_role = Role.objects.filter(tenant=current_tenant, slug='cs').first() if current_tenant else None
                    if not cs_role:
                        cs_role = Role.objects.filter(tenant__isnull=True, slug='cs').first()
                    
                    if cs_role:
                        cs_users = User.all_objects.filter(
                            tenant=current_tenant,
                            role=cs_role,
                            is_active=True
                        )
                        
                        # Send notification to each CS
                        notification_msg = f"🔔 *Lead Baru Masuk!*\n\nNama: {lead_name}\nPhone: {lead_phone}\n\nSilakan follow up segera."
                        
                        for cs in cs_users:
                            # Avoid sending to lead themselves if they are CS (unlikely but safe)
                            if cs.phone_number and clean_num(cs.phone_number) != lead_phone:
                                StarSenderService.send_message(
                                    to=cs.phone_number,
                                    body=notification_msg,
                                    tenant=current_tenant
                                )
                                logger.info(f"CS notification sent to {cs.username} ({cs.phone_number})")
                        
                        logger.info(f"CS notification completed for lead: {lead_name} ({lead_phone})")
                    else:
                        logger.warning(f"CS role not found for tenant: {current_tenant}")
                else:
                    logger.warning(f"Could not parse lead info from is_me message: {message[:100]}")
                
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

            # --- INITIAL LOG & DEDUPLICATION ---
            sender = c_sender or sender # Digits only for storage

            # 1. STRONG Deduplication - Block ALL duplicate messages within 30s
            # This prevents double insert when StarSender sends webhook twice:
            # - First: user -> gateway (actual message)
            # - Second: gateway -> user (echo/confirmation)
            from django.utils import timezone
            from datetime import timedelta
            
            # Check for exact duplicate (same sender, same message, within 30s)
            duplicate_exists = WhatsAppMessage.objects.filter(
                sender=sender, 
                message=message, 
                created_at__gte=timezone.now() - timedelta(seconds=30)
            ).exists()
            
            if duplicate_exists:
                logger.info(f"[DUPLICATE BLOCKED] Same message from {sender} within 30s: {message[:50]}")
                return HttpResponse('OK', status=200)

            # 2. Log Message ONLY after passing duplicate check
            try:
                WhatsAppMessage.objects.create(
                    tenant=current_tenant,
                    device=device,
                    message=message,
                    sender=sender,
                    sender_name=sender_name,
                    raw_data=data
                )
                logger.info(f"Message logged: {sender} -> {device} | {message[:50]}")
            except Exception as e:
                logger.error(f"Failed to log message: {e}")
            
            # 4. Identify Sender (Internal User vs External Lead)
            # Filter for ANY internal user (CS, Admin, etc.) to prevent treating them as leads
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
                    StarSenderService.send_message(to=sender, body=staff_msg, tenant=current_tenant)
                    logger.info(f"[STAFF] Response sent to {internal_user.username}")
                else:
                    # If it's a staff but not a valid command keyword, use AI fallback
                    logger.info(f"[STAFF] Message from {internal_user.username} - No command matched, using AI fallback")
                    try:
                        from core.services.ai_service import AIService
                        ai_response = AIService.get_completion(message, tenant=current_tenant, sender_name=internal_user.username)
                        if ai_response:
                            StarSenderService.send_message(to=sender, body=ai_response, tenant=current_tenant)
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
                    if message.upper().startswith(keyword.upper()):
                        # Found matching form
                        logger.info(f"[FORM MATCH] Keyword '{keyword}' matched for form ID {form.id}")
                        body = message[len(keyword):].strip()
                        
                        # Clean multiple separators or spaces at start
                        if form.separator:
                            while body.startswith(form.separator) or body.startswith(' '):
                                body = body[1:].strip()
                        
                        parts = [p.strip() for p in body.split(form.separator)] if form.separator else [body]
                        fields = [f.strip() for f in form.field_map.split(form.separator)] if form.separator else ['data']
                        
                        # Map data
                        lead_data = {}
                        for i in range(min(len(parts), len(fields))):
                            lead_data[fields[i].lower()] = parts[i]
                        
                        lead_name_from_data = lead_data.get('nama') or lead_data.get('name')
                        if lead_name_from_data and lead_name_from_data.upper() == keyword.upper():
                            lead_name_from_data = None
                        
                        lead_name = lead_name_from_data or sender_name or "Unknown"
                        lead_location = lead_data.get('alamat') or lead_data.get('kota') or lead_data.get('asal') or ""
                        
                        # Create or Update Lead
                        # Use clean_num to ensure 6281 and 081 are the same Lead entry
                        lead, created = Lead.objects.update_or_create(
                            tenant=current_tenant,
                            phone_number=c_sender,
                            defaults={
                                'name': lead_name,
                                'type': form.lead_type,
                                'data': lead_data,
                                'status': Lead.Status.NEW
                            }
                        )
                        logger.info(f"[LEAD] {'Created' if created else 'Updated'} lead: {lead_name} ({c_sender})")
                        
                        # Auto-Assign CS
                        from core.services.lead_workflow_service import LeadWorkflowService
                        assigned_cs = LeadWorkflowService.assign_to_cs(lead)
                        
                        # === STEP 1: Generate AI Greeting for Lead ===
                        ai_greeting = None
                        try:
                            from core.services.ai_service import AIService
                            
                            # Build context for AI
                            greeting_context = f"Nama: {lead_name}"
                            if lead_location:
                                greeting_context += f", Asal: {lead_location}"
                            
                            greeting_prompt = (
                                f"Buatkan pesan sambutan hangat untuk calon santri/donatur baru yang baru mendaftar.\n"
                                f"Data pendaftar:\n{greeting_context}\n\n"
                                f"Pesan harus:\n"
                                f"- Menyapa dengan nama\n"
                                f"- Mengucapkan terima kasih atas pendaftaran\n"
                                f"- Menyebutkan bahwa tim CS akan segera menghubungi\n"
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
                                system_prompt=strict_prompt
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
                            StarSenderService.send_message(to=sender, body=ai_greeting, tenant=current_tenant)
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
                    
                    # For external numbers, ensure lead exists
                    lead, created = Lead.objects.get_or_create(
                        tenant=current_tenant,
                        phone_number=sender,
                        defaults={'status': Lead.Status.WAITING_DATA}
                    )
                    
                    # Synchronous AI response (no threading)
                    try:
                        from core.services.ai_service import AIService
                        ai_response = AIService.get_completion(message, tenant=current_tenant, sender_name=sender_name)
                        if ai_response:
                            StarSenderService.send_message(to=sender, body=ai_response, tenant=current_tenant)
                            logger.info(f"[AI] Response sent to {sender}")
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

