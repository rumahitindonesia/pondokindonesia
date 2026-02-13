import sys
import os
import json
import environ

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

def test_lead_feature():
    print("Testing Lead Registration Feature...")
    try:
        tenant = Tenant.objects.get(subdomain='sekolahit')
    except Tenant.DoesNotExist:
        print("Tenant not found")
        return

    # 1. Setup Form
    print("Setting up WhatsAppForm 'REG'...")
    form, created = WhatsAppForm.objects.get_or_create(
        tenant=tenant,
        keyword='REG',
        defaults={
            'separator': '#',
            'field_map': 'nama#alamat',
            'lead_type': 'SANTRI',
            'response_template': 'Halo {name}, data santri asal {alamat} diterima.'
        }
    )
    if not created:
        # Ensure config matches test expectation
        form.separator = '#'
        form.field_map = 'nama#alamat'
        form.lead_type = 'SANTRI'
        form.save()

    # 2. Simulate Webhook
    payload = {
        "from": "6289990001",
        "pushName": "Budi Tester",
        "message": "REG#Udin#Surabaya",
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
    try:
        response = webhook_whatsapp(request, tenant_slug='sekolahit')
        print(f"Response Code: {response.status_code}")
    except Exception as e:
        print(f"View Error: {e}")
        return

    # 3. Verify Lead
    lead = Lead.objects.filter(phone_number="6289990001").order_by('-created_at').first()
    if lead:
        print(f"\n[SUCCESS] Lead Created!")
        print(f"Name: {lead.name}")
        print(f"Type: {lead.type}")
        print(f"Data: {lead.data}")
        
        if lead.name == "Udin" and lead.data.get('alamat') == "Surabaya":
            print(">> Validation PASSED")
        else:
            print(">> Validation FAILED (Data mismatch)")
    else:
        print("\n[FAILED] Lead NOT Created.")

if __name__ == "__main__":
    test_lead_feature()
