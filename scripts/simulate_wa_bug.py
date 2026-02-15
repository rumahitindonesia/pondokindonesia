import os
import django
import sys

# Ensure current directory is in path
sys.path.append('/home/pondok-it/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pondokindonesia.settings')
django.setup()

from core.models import WhatsAppForm, Lead
from tenants.models import Tenant
from core.views import webhook_whatsapp
from django.test import RequestFactory
import json

def simulate_test():
    # 1. Setup Data
    tenant, _ = Tenant.objects.get_or_create(name="Test Tenant", subdomain="test")
    
    # Create the form as described by user
    form, _ = WhatsAppForm.objects.get_or_create(
        tenant=tenant,
        keyword="DAFTAR",
        separator="#",
        defaults={
            'field_map': "nama#kota#sekolah",
            'lead_type': Lead.Type.SANTRI,
            'response_template': "OK {nama}",
            'is_active': True
        }
    )
    
    # 2. Simulate Request
    factory = RequestFactory()
    payload = {
        "device": "628999999",
        "message": "DAFTAR#Budi#Surabaya#SMA 1",
        "from": "628111222333",
        "push_name": "Unknown Sender"
    }
    
    request = factory.post('/webhook/whatsapp/test/', 
                          data=json.dumps(payload), 
                          content_type='application/json')
    
    # Inject tenant since it's usually done by middleware or resolver
    response = webhook_whatsapp(request, tenant_slug="test")
    
    print(f"Response Status: {response.status_code}")
    
    # 3. Check Lead
    lead = Lead.objects.get(phone_number="628111222333")
    print(f"Lead ID: {lead.id}")
    print(f"Lead Name: '{lead.name}'")
    print(f"Lead Data: {lead.data}")

if __name__ == "__main__":
    # Ensure tables exist for simulation (using in-memory or temporary sqlite if needed)
    # But here we use the one in repo, so we might need migrations
    from django.core.management import call_command
    call_command('migrate', verbosity=0)
    
    simulate_test()
