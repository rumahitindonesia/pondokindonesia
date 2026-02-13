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
    tenants = Tenant.objects.filter(is_active=True)
    pricing_plans = PricingPlan.objects.filter(is_active=True).order_by('order')
    return render(request, 'core/homepage.html', {'tenants': tenants, 'pricing_plans': pricing_plans})

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

            # 1. Lead Registration (Forms)
            forms = WhatsAppForm.objects.filter(tenant=current_tenant, is_active=True) if current_tenant else WhatsAppForm.objects.filter(tenant__isnull=True, is_active=True)
            
            for form in forms:
                keyword = form.keyword.strip()
                if message.strip().upper().startswith(keyword.upper()):
                    # Parse
                    body = message[len(keyword):].strip()
                    if form.separator and body.startswith(form.separator): body = body[1:]
                    
                    parts = [p.strip() for p in body.split(form.separator)]
                    fields = [f.strip() for f in form.field_map.split(form.separator)]
                    
                    if len(parts) >= len(fields) and len(fields) > 0:
                        lead_data = {fields[i]: parts[i] for i in range(len(fields))}
                        lead_name = lead_data.get('nama') or lead_data.get('name') or sender_name or parts[0]
                        
                        Lead.objects.update_or_create(
                            tenant=current_tenant, 
                            phone_number=sender, 
                            type=form.lead_type,
                            defaults={
                                'name': lead_name,
                                'data': lead_data
                            }
                        )
                        
                        resp = form.response_template
                        try:
                            fmt = lead_data.copy(); fmt['name'] = lead_name
                            resp = resp.format(**fmt)
                        except: pass
                        
                        # AI Response Logic
                        if form.use_ai_response:
                            # Use the formatted template as a PROMPT for the AI
                            input_prompt = resp
                            system_instruction = (
                                "You are a helpful admin assistant. "
                                "Rewrite the following message to be more personal, warm, and polite. "
                                "Maintain the core information but make it sound human and welcoming. "
                                "Keep it concise (suitable for WhatsApp). "
                                "IMPORTANT: Return ONLY the final message content. "
                                "Do NOT include any introductory text like 'Here is the message' or 'Key changes'. "
                                "Do NOT include any explanations or notes."
                            )
                            # Run AI in background (threaded) to prevent blocking
                            import threading
                            def send_ai_reply(p_prompt, p_sys, p_to, p_tenant):
                                try:
                                    ai_reply = AIService.get_completion(p_prompt, tenant=p_tenant, system_prompt=p_sys)
                                    if ai_reply:
                                        StarSenderService.send_message(to=p_to, body=ai_reply, tenant=p_tenant)
                                except Exception as e:
                                    print(f"Error AI Form Reply: {e}")
                            
                            threading.Thread(target=send_ai_reply, args=(input_prompt, system_instruction, sender, current_tenant)).start()
                        else:
                            # Standard Template Reply
                            StarSenderService.send_message(to=sender, body=resp, tenant=current_tenant)
                        
                        replied = True
                        break

            # 2. Auto Reply Logic
            if not replied:
                replies = WhatsAppAutoReply.objects.filter(tenant=current_tenant, is_active=True) if current_tenant else WhatsAppAutoReply.objects.filter(tenant__isnull=True, is_active=True)
            else:
                replies = []
            for reply in replies:
                if reply.keyword.lower() in message.lower():
                    # Personalize Response
                    response_text = reply.response
                    # Fallback to empty string if name is missing to avoid "Kak Kak" if user typed "Kak {name}"
                    safe_name = sender_name if sender_name else ""
                    try:
                        response_text = response_text.format(name=safe_name)
                    except KeyError:
                        pass # Ignore if placeholder not found or other keys present
                        
                    StarSenderService.send_message(
                        to=sender,
                        body=response_text,
                        tenant=current_tenant
                    )
                    replied = True
                    break
            
            # AI Fallback (If no keyword matched)
            if not replied:
                # Run AI in a separate thread to prevent "Server Jam" (Blocking)
                import threading
                def process_ai_reply(msg, tnt, snd, snd_name):
                    try:
                        ai_response = AIService.get_completion(msg, tenant=tnt, sender_name=snd_name)
                        if ai_response:
                            StarSenderService.send_message(
                                to=snd,
                                body=ai_response,
                                tenant=tnt
                            )
                    except Exception as e:
                        print(f"Error in background AI process: {e}")

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
