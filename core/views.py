from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, JsonResponse
import json
from .models import WhatsAppMessage, WhatsAppAutoReply, WhatsAppForm, Lead, PricingPlan
from core.services.starsender import StarSenderService
from core.services.ai_service import AIService
from tenants.models import Tenant
from django.shortcuts import get_object_or_404

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
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            # 2. Extract Basic Data
            device = data.get('device', '').strip()
            message = data.get('message', '').strip()
            sender = data.get('from', '').strip()
            sender_name = data.get('push_name') or data.get('pushName') or data.get('name') or ''
            is_me = data.get('is_me', False)

            # Normalize for comparison
            import re
            def clean_num(n): return re.sub(r'\D', '', str(n))
            
            # 1. Resolve Tenant
            current_tenant = None
            if tenant_slug:
                current_tenant = get_object_or_404(Tenant, subdomain=tenant_slug)
            
            # If still None, try middleware
            if not current_tenant and hasattr(request, 'tenant') and request.tenant:
                current_tenant = request.tenant
            
            # If still None, try to identify by device number
            if not current_tenant and device:
                clean_device = clean_num(device)
                # Check for tenant by phone_number matching (last 10 digits as safe bet)
                current_tenant = Tenant.objects.filter(phone_number__icontains=clean_device[-10:]).first()
                if current_tenant:
                    from core.models import set_current_tenant
                    set_current_tenant(current_tenant)

            # --- GHOST LEAD / ECHO FILTER ---
            c_sender = clean_num(sender)
            c_device = clean_num(device)
            c_tenant_phone = clean_num(current_tenant.phone_number) if current_tenant and current_tenant.phone_number else ""

            # 1. Simple Echo Check (Filter ANY message from our own device/number)
            if is_me:
                return HttpResponse('OK', status=200)
            
            # Match if sender is same as device or same as tenant phone
            is_echo = False
            if c_device and (c_sender == c_device or c_sender.endswith(c_device) or c_device.endswith(c_sender)):
                is_echo = True
            if c_tenant_phone and (c_sender == c_tenant_phone or c_sender.endswith(c_tenant_phone) or c_tenant_phone.endswith(c_sender)):
                is_echo = True
            
            if is_echo:
                return HttpResponse('OK', status=200)

            # 2. Deduplication (10-second window for identical message from same sender)
            from django.utils import timezone
            from datetime import timedelta
            if WhatsAppMessage.objects.filter(sender=sender, message=message, created_at__gte=timezone.now() - timedelta(seconds=10)).exists():
                return HttpResponse('OK', status=200)

            # 3. Log Message
            WhatsAppMessage.objects.create(
                tenant=current_tenant,
                device=device,
                message=message,
                sender=sender,
                sender_name=sender_name,
                raw_data=data
            )
            
            # 4. Identify Sender (Staff vs External)
            from users.models import User
            staff = User.all_objects.filter(
                is_active=True, 
                is_staff=True,
                phone_number__icontains=sender[-10:]
            ).first()
            
            replied = False

            # --- FLOW BRANCHING ---

            if staff:
                # 5. INTERNAL FLOW (Staff)
                from core.services.staff_command_service import StaffCommandService
                staff_msg = StaffCommandService.process_message_v2(current_tenant, message, staff)
                if staff_msg:
                    StarSenderService.send_message(to=sender, body=staff_msg, tenant=current_tenant)
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
                        
                        # Create or Update Lead
                        lead, created = Lead.objects.update_or_create(
                            tenant=current_tenant,
                            phone_number=sender,
                            defaults={
                                'name': lead_name,
                                'type': form.lead_type,
                                'data': lead_data,
                                'status': Lead.Status.NEW
                            }
                        )
                        
                        # Auto-Assign CS
                        from core.services.lead_workflow_service import LeadWorkflowService
                        assigned_cs = LeadWorkflowService.assign_to_cs(lead)
                        
                        # Prepare Response
                        resp = form.response_template
                        try:
                            fmt_data = lead_data.copy()
                            fmt_data['name'] = lead_name
                            if assigned_cs: fmt_data['cs_name'] = assigned_cs.username
                            resp = resp.format(**fmt_data)
                        except: pass

                        # If form is set to use AI, get completion from response_template (acting as prompt)
                        if form.use_ai_response:
                            from core.services.ai_service import AIService
                            # Strict prompt to prevent AI from explaining itself or adding meta-talk
                            strict_prompt = (
                                "Role: Friendly Admin of Pondok Pesantren.\n"
                                "Task: Generate a response message based on the input instruction.\n"
                                "Constraint: Output ONLY the final message content. NO preamble, NO meta-talk, NO 'Here is the message'.\n"
                                "Your output will be sent directly to the requester on WhatsApp."
                            )
                            ai_resp = AIService.get_completion(
                                resp, 
                                tenant=current_tenant, 
                                sender_name=lead_name,
                                system_prompt=strict_prompt
                            )
                            if ai_resp:
                                resp = ai_resp
                        
                        # Auto-Insert to CRM if configured
                        if form.auto_insert:
                            from crm.services import CRMService
                            res_obj, auto_msg = CRMService.convert_lead(lead, form.lead_type)
                            if res_obj:
                                resp = f"{resp}\n\n[Auto-Insert] {auto_msg}"

                        StarSenderService.send_message(to=sender, body=resp, tenant=current_tenant)
                        replied = True
                        break

                # B. AI Fallback (Natural interaction for undefined formats)
                if not replied:
                    import threading
                    # For external numbers, ensure lead exists
                    lead, created = Lead.objects.get_or_create(
                        tenant=current_tenant,
                        phone_number=sender,
                        defaults={'status': Lead.Status.WAITING_DATA}
                    )
                    
                    threading.Thread(
                        target=process_ai_reply, 
                        args=(message, current_tenant, sender, sender_name)
                    ).start()
                    replied = True

            return HttpResponse('OK', status=200)

            return HttpResponse('OK', status=200)
            
            return HttpResponse('OK', status=200)
        except json.JSONDecodeError:
            return HttpResponse('Invalid JSON', status=400)
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"CRITICAL ERROR: {e}")
            return HttpResponse(str(e), status=500)
            
    return HttpResponse('Method Not Allowed', status=405)
