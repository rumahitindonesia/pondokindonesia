import sys
import os
import json
import time

# Setup Django environment
sys.path.append('/home/triyono/pondok-django')
import environ
env_file = '/home/triyono/pondok-django/.env'
if os.path.exists(env_file):
    environ.Env.read_env(env_file)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pondokindonesia.settings')

import django
django.setup()

from django.test import RequestFactory
from core.views import webhook_whatsapp
from core.models import WhatsAppForm, Lead
from tenants.models import Tenant

def test_ai_lead_feature():
    print("Testing AI Lead Response Feature...")
    try:
        tenant = Tenant.objects.get(subdomain='sekolahit')
    except Tenant.DoesNotExist:
        print("Tenant not found")
        return

    # 1. Setup Form with AI Enabled
    print("Setting up WhatsAppForm 'DAFTAR' with AI...")
    form, _ = WhatsAppForm.objects.get_or_create(
        tenant=tenant,
        keyword='DAFTAR',
        defaults={
            'separator': '#',
            'field_map': 'nama#alamat',
            'lead_type': 'SANTRI',
            'response_template': 'Buatkan ucapan selamat datang untuk calon santri bernama {name} dari {alamat}.',
            'use_ai_response': True
        }
    )
    # Ensure AI is ON
    form.use_ai_response = True
    form.save()

    # 2. Simulate Webhook
    payload = {
        "from": "6289990001",
        "pushName": "Budi AI Tester",
        "message": "DAFTAR#Budi#Bandung",
        "timestamp": "123456789"
    }
    
    print(f"Simulating Message: {payload['message']}")
    
    factory = RequestFactory()
    request = factory.post(
        '/webhook/whatsapp/sekolahit/',
        data=json.dumps(payload),
        content_type='application/json'
    )

    # Execute View
    response = webhook_whatsapp(request, tenant_slug='sekolahit')
    print(f"Response Code: {response.status_code}")
    
    # 3. Verify Lead Creation
    lead = Lead.objects.filter(phone_number="6289990001", name="Budi").order_by('-created_at').first()
    if lead:
        print(f"\n[SUCCESS] Lead Created: {lead}")
    else:
        print("\n[FAILED] Lead NOT Created.")

    print("Waiting 5s for background AI thread...")
    time.sleep(5)
    print("Test Complete. Check StarSender logs/dashboard for actual message.")

if __name__ == "__main__":
    test_ai_lead_feature()
