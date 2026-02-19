import os
import django
import sys
import json
from unittest.mock import MagicMock, patch

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pondokindonesia.settings')
django.setup()

from django.test import RequestFactory
from core.views import webhook_whatsapp
from core.models import Lead, MonthlyTarget
from tenants.models import Tenant
from users.models import User, Role

def verify():
    print("--- STARTING VERIFICATION: CS ASSIGNMENT & TARGETS ---")
    tenant = Tenant.objects.get(subdomain='test')
    
    # 1. Create Roles if they don't exist
    cs_pendaftaran, _ = Role.objects.get_or_create(tenant=tenant, slug='cs-pendaftaran', defaults={'name': 'CS Pendaftaran'})
    cs_donasi, _ = Role.objects.get_or_create(tenant=tenant, slug='cs-donasi', defaults={'name': 'CS Donasi'})
    
    # Ensure some users exist for these roles for penugasan
    staff_user = User.all_objects.filter(tenant=tenant, is_staff=True).first()
    if staff_user:
        staff_user.role = cs_pendaftaran
        staff_user.save()
        print(f"Assigned user {staff_user.username} to cs-pendaftaran for testing.")

    # 2. Setup Target for this month
    from django.utils import timezone
    now = timezone.now()
    Target, _ = MonthlyTarget.objects.get_or_create(
        tenant=tenant, month=now.month, year=now.year,
        defaults={'target_donasi': 10000000, 'target_santri_baru': 10}
    )
    print(f"Target set for {now.month}/{now.year}: Rp {Target.target_donasi}")

    # 3. Setup Mock AI Response for SANTRI
    with patch('core.services.ai_service.AIService.get_completion') as mock_ai, \
         patch('core.services.starsender.StarSenderService.send_message') as mock_ss:
        
        mock_ai.return_value = "Tentu Ayah/Bunda! [EXEC: SAVE_LEAD] Ahmad#Yogyakarta#SDIT Amanah#SANTRI"
        mock_ss.return_value = (True, "sent")
        
        data = {
            "from": "6289911223344",
            "message": "Mau tanya info pendaftaran",
            "pushName": "Ahmad",
            "is_me": False
        }
        
        factory = RequestFactory()
        request = factory.post('/webhook/whatsapp/', data=json.dumps(data), content_type='application/json')
        request.tenant = tenant
        
        print("\nSimulating SANTRI lead conversion...")
        # Clear existing lead to ensure fresh test
        Lead.objects.filter(phone_number="6289911223344").delete()
        
        webhook_whatsapp(request, tenant_slug='pondokit')
        
        lead = Lead.objects.filter(tenant=tenant, phone_number="6289911223344").first()
        if lead:
            print(f"SUCCESS: Lead created with type: {lead.get_type_display()}")
            if lead.type == Lead.Type.SANTRI:
                print("PASSED: Lead type is correctly detected as SANTRI.")
                if lead.cs and lead.cs.role.slug == 'cs-pendaftaran':
                     print(f"PASSED: Assigned to CS with role: {lead.cs.role.slug}")
                else:
                     print(f"WARNING: CS role is {lead.cs.role.slug if lead.cs else 'None'}. Make sure a CS with slug 'cs-pendaftaran' exists.")
            else:
                print(f"FAILED: Lead type is {lead.type}, expected SANTRI.")
        else:
            print("FAILED: Lead not found.")

    # 4. Setup Mock AI Response for DONATUR
    with patch('core.services.ai_service.AIService.get_completion') as mock_ai, \
         patch('core.services.starsender.StarSenderService.send_message') as mock_ss:
        
        mock_ai.return_value = "Alhamdulillah Kak! [EXEC: SAVE_LEAD] Siti#Bandung#-#DONATUR"
        mock_ss.return_value = (True, "sent")
        
        data = {
            "from": "6289911223355",
            "message": "Gimana cara donasi?",
            "pushName": "Siti",
            "is_me": False
        }
        
        factory = RequestFactory()
        request = factory.post('/webhook/whatsapp/', data=json.dumps(data), content_type='application/json')
        request.tenant = tenant
        
        print("\nSimulating DONATUR lead conversion...")
        # Clear existing lead to ensure fresh test
        Lead.objects.filter(phone_number="6289911223355").delete()
        
        webhook_whatsapp(request, tenant_slug='pondokit')
        
        lead = Lead.objects.filter(tenant=tenant, phone_number="6289911223355").first()
        if lead:
            print(f"SUCCESS: Lead created with type: {lead.get_type_display()}")
            if lead.type == Lead.Type.DONATUR:
                print("PASSED: Lead type is correctly detected as DONATUR.")
            else:
                print(f"FAILED: Lead type is {lead.type}, expected DONATUR.")
        else:
            print("FAILED: Lead not found.")

if __name__ == "__main__":
    verify()
