import sys
import os
import json
import time

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

def test_duplicate_prevention():
    print("Testing Lead Duplicate Prevention...")
    try:
        tenant = Tenant.objects.get(subdomain='sekolahit')
    except Tenant.DoesNotExist:
        print("Tenant 'sekolahit' not found")
        return

    # 1. Setup Form
    form, _ = WhatsAppForm.objects.get_or_create(
        tenant=tenant,
        keyword='TESTREG',
        defaults={
            'separator': '#',
            'field_map': 'nama#alamat',
            'lead_type': 'SANTRI',
            'response_template': 'Oke {name}',
            'use_ai_response': False
        }
    )

    # 2. Simulate First Webhook (Create)
    print("Sending First Request (Should Create)...")
    payload1 = {
        "from": "6289990002",
        "pushName": "Duplicate Tester",
        "message": "TESTREG#Budi#Jakarta",
        "timestamp": "11111"
    }
    
    factory = RequestFactory()
    request1 = factory.post('/webhook/whatsapp/sekolahit/', data=json.dumps(payload1), content_type='application/json')
    webhook_whatsapp(request1, tenant_slug='sekolahit')

    # Check Count
    count1 = Lead.objects.filter(phone_number="6289990002").count()
    print(f"Lead Count after 1st request: {count1}")

    # 3. Simulate Second Webhook (Update)
    print("Sending Second Request (Should Update)...")
    payload2 = {
        "from": "6289990002",
        "pushName": "Duplicate Tester",
        "message": "TESTREG#Budi Updated#Bandung",
        "timestamp": "22222"
    }
    request2 = factory.post('/webhook/whatsapp/sekolahit/', data=json.dumps(payload2), content_type='application/json')
    webhook_whatsapp(request2, tenant_slug='sekolahit')

    # Check Count
    count2 = Lead.objects.filter(phone_number="6289990002").count()
    lead = Lead.objects.filter(phone_number="6289990002").first()
    
    print(f"Lead Count after 2nd request: {count2}")
    if lead:
        print(f"Current Lead Name: {lead.name} (Expected: Budi Updated)")
        print(f"Current Lead Data: {lead.data} (Expected Address: Bandung)")

    if count1 == 1 and count2 == 1 and lead.name == "Budi Updated":
        print("\n[SUCCESS] Duplicate Prevention Works!")
    else:
        print("\n[FAILED] Duplicate Prevention Failed.")

if __name__ == "__main__":
    test_duplicate_prevention()
