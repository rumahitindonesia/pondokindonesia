import sys
import os
import environ

# Setup Django environment
sys.path.append('/home/triyono/pondok-django')

# Load .env explicitly
import environ
env_file = '/home/triyono/pondok-django/.env'
if os.path.exists(env_file):
    environ.Env.read_env(env_file)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pondokindonesia.settings')

import django
django.setup()

from tenants.models import Tenant
from core.models import WhatsAppMessage
from core.services.ai_service import AIService
from core.services.starsender import StarSenderService

def debug_and_simulate():
    print("Inspecting Tenant 'sekolahit'...")
    try:
        tenant = Tenant.objects.get(subdomain='sekolahit')
        print(f"Found Tenant: {tenant}")
    except Tenant.DoesNotExist:
        print("Tenant 'sekolahit' NOT FOUND.")
        return

    # 1. Check Recent Messages
    print("\n--- Recent WhatsApp Messages (Last 5) ---")
    msgs = WhatsAppMessage.objects.filter(tenant=tenant).order_by('-created_at')[:5]
    if not msgs:
        print("No messages found.")
        return

    for m in msgs:
        print(f"[{m.created_at}] From: {m.sender} | Body: {m.message}")
        
    last_msg = msgs[0]
    print(f"\n--- Simulating Logic for LAST Message: '{last_msg.message}' ---")
    
    # 2. Simulate AI Call
    print(f"1. Calling AIService.get_completion('{last_msg.message}')...")
    try:
        ai_response = AIService.get_completion(last_msg.message, tenant=tenant, sender_name=last_msg.sender_name)
        
        if ai_response:
            print(f"   [SUCCESS] AI Response: {ai_response[:100]}...")
            
            # 3. Simulate StarSender Call (Dry run / actual send)
            print(f"2. Calling StarSenderService.send_message(to='{last_msg.sender}')...")
            success, response = StarSenderService.send_message(
                to=last_msg.sender,
                body=ai_response,
                tenant=tenant
            )
            
            if success:
                print(f"   [SUCCESS] StarSender: {response}")
            else:
                print(f"   [FAILED] StarSender: {response}")
        else:
            print("   [FAILED] AI Service returned None (Empty response or Error logged).")
            
    except Exception as e:
        print(f"   [EXCEPTION] {e}")

if __name__ == "__main__":
    debug_and_simulate()
