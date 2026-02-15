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
            # Resolve Tenant
            current_tenant = None
            if tenant_slug:
                current_tenant = get_object_or_404(Tenant, subdomain=tenant_slug)
            
            data = json.loads(request.body)
            
            # Extract data
            device = data.get('device', '')
            message = data.get('message', '')
            sender = data.get('from', '')
            # Try to get name from 'push_name' (StarSender standard), fallback to 'pushName' or 'name'
            sender_name = data.get('push_name') or data.get('pushName') or data.get('name') or ''
            timestamp = data.get('timestamp', '')
            is_me = data.get('is_me', False)
            
            # Ignore outgoing messages (from bot itself)
            if is_me:
                return HttpResponse('OK', status=200)
            
            # Save Message (associated with tenant if present, or global if None)
            WhatsAppMessage.objects.create(
                tenant=current_tenant,
                device=device,
                message=message,
                sender=sender,
                sender_name=sender_name,
                timestamp=timestamp,
                raw_data=data
            )
            
            replied = False

            # 1. Lead Workflow & Data Extraction
            from core.services.lead_workflow_service import LeadWorkflowService
            
            # Find or initiate lead
            lead, created = Lead.objects.get_or_create(
                tenant=current_tenant, 
                phone_number=sender,
                defaults={'status': Lead.Status.WAITING_DATA}
            )
            
            # Record last message time
            from django.utils import timezone
            lead.last_message_at = timezone.now()
            lead.save()

            replied = False

            # If waiting for info, try to parse
            if lead.status == Lead.Status.WAITING_DATA:
                if LeadWorkflowService.parse_data_format(lead, message):
                    # Data parsed! Assign to CS
                    assigned_cs = LeadWorkflowService.assign_to_cs(lead)
                    if assigned_cs:
                        StarSenderService.send_message(
                            to=sender,
                            body=f"Terima kasih {lead.name}, data Anda sudah diterima dan akan segera dibantu oleh CS kami ({assigned_cs.username}).",
                            tenant=current_tenant
                        )
                    replied = True

            # 2. Lead Registration (Legacy Forms - maintained for compatibility)
            if not replied:
                forms = WhatsAppForm.objects.filter(tenant=current_tenant, is_active=True) if current_tenant else WhatsAppForm.objects.filter(tenant__isnull=True, is_active=True)
                for form in forms:
                    keyword = form.keyword.strip()
                    if message.strip().upper().startswith(keyword.upper()):
                        # (Legacy form logic maintained below)
                        body = message[len(keyword):].strip()
                        if form.separator and body.startswith(form.separator): body = body[1:]
                        parts = [p.strip() for p in body.split(form.separator)]
                        fields = [f.strip() for f in form.field_map.split(form.separator)]
                        
                        if len(parts) >= len(fields) and len(fields) > 0:
                            lead_data = {fields[i]: parts[i] for i in range(len(fields))}
                            lead_name = lead_data.get('nama') or lead_data.get('name') or sender_name or parts[0]
                            
                            lead.name = lead_name
                            lead.data.update(lead_data)
                            lead.save()
                            
                            # Assign CS for legacy forms too
                            LeadWorkflowService.assign_to_cs(lead)
                            
                            resp = form.response_template
                            try:
                                fmt = lead_data.copy(); fmt['name'] = lead_name
                                resp = resp.format(**fmt)
                            except: pass
                            
                            if form.use_ai_response:
                                # ... existing ai logic ...
                                input_prompt = resp
                                system_instruction = "You are a helpful admin assistant..."
                                threading.Thread(target=process_ai_reply, args=(input_prompt, current_tenant, sender, sender_name)).start()
                            else:
                                StarSenderService.send_message(to=sender, body=resp, tenant=current_tenant)
                            replied = True
                            break

            # 3. Auto Reply Logic
            if not replied:
                replies = WhatsAppAutoReply.objects.filter(tenant=current_tenant, is_active=True) if current_tenant else WhatsAppAutoReply.objects.filter(tenant__isnull=True, is_active=True)
                for reply in replies:
                    if reply.keyword.lower() in message.lower():
                        response_text = reply.response
                        safe_name = sender_name if sender_name else ""
                        try:
                            response_text = response_text.format(name=safe_name)
                        except KeyError: pass
                        StarSenderService.send_message(to=sender, body=response_text, tenant=current_tenant)
                        replied = True
                        break
            
            # AI Fallback
            if not replied:
                # If first contact (WAITING_DATA), AI will ask for info
                import threading
                thread = threading.Thread(target=process_ai_reply, args=(message, current_tenant, sender, sender_name))
                thread.start()

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
