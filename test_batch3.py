import os
import django
import sys
import json
import random
from unittest.mock import MagicMock, patch

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pondokindonesia.settings')
django.setup()

from core.services.ai_service import AIService
from core.models import Lead, MonthlyTarget
from crm.models import Santri
from tenants.models import Tenant
from users.models import User
from django.utils import timezone
from django.test import RequestFactory
from core.views import webhook_whatsapp

def verify_batch3():
    print("--- STARTING VERIFICATION: BATCH 3 (SCORING & SCARCITY) ---")
    tenant, _ = Tenant.objects.get_or_create(subdomain='test', defaults={'name': 'Test Tenant'})
    now = timezone.now()
    
    # 1. Setup Data for Scarcity
    MonthlyTarget.objects.filter(tenant=tenant, month=now.month, year=now.year).delete()
    target = MonthlyTarget.objects.create(
        tenant=tenant, month=now.month, year=now.year,
        target_donasi=5000000, target_santri_baru=5
    )
    print(f"Target set: Donasi=5jt, Santri=5")

    # 2. Verify Prompt Scarcity
    prompt = AIService.get_system_prompt(tenant=tenant, query="Berapa sisa kuota?")
    print("\nVerifying Scarcity in Prompt...")
    if "DATA REAL-TIME (UNTUK SCARCITY LOGIC)" in prompt:
        print("PASSED: Scarcity data injected correctly.")
    else:
        print("FAILED: Scarcity data missing from prompt.")

    # 3. Verify Tag Processing with Score
    with patch('core.services.ai_service.AIService.get_completion') as mock_ai, \
         patch('core.services.starsender.StarSenderService.send_message') as mock_ss:
        
        mock_ai.return_value = "Siswa ini sangat berminat! [EXEC: SAVE_LEAD] Budi High#Solo#SMA 1#SANTRI#95"
        mock_ss.return_value = (True, "sent")
        
        phone = f"62812345{random.randint(100000,999999)}"
        data = {
            "from": phone,
            "message": "Saya ingin daftar sekarang! " + str(random.random()),
            "pushName": "Budi",
            "is_me": False
        }
        
        factory = RequestFactory()
        request = factory.post('/webhook/whatsapp/', data=json.dumps(data), content_type='application/json')
        request.tenant = tenant
        
        print(f"\nSimulating High Score Lead (Phone: {phone})...")
        webhook_whatsapp(request, tenant_slug='test')
        
        lead = Lead.objects.filter(phone_number=phone).first()
        if lead and lead.score == 95:
            print(f"PASSED: Lead created with Score: {lead.score}")
        else:
            print(f"FAILED: Lead score is {lead.score if lead else 'None'}, expected 95.")

    # 4. Verify Dashboard Sorting
    from core.dashboard import dashboard_callback
    # Create another lower score lead
    Lead.objects.create(tenant=tenant, name="Budi Low", phone_number="6281234567811", score=20)
    
    factory = RequestFactory()
    request = factory.get('/central/')
    request.tenant = tenant
    user, _ = User.all_objects.get_or_create(username='testadmin', defaults={'is_superuser': True, 'is_staff': True})
    request.user = user
    
    context = {}
    dashboard_callback(request, context)
    priority_leads = context.get('priority_leads')
    
    print("\nVerifying Dashboard Sorting...")
    if priority_leads and priority_leads[0].score == 95:
        print(f"PASSED: Top lead is {priority_leads[0].name} with score {priority_leads[0].score}")
    else:
        print(f"FAILED: Dashboard sorting incorrect. Top score: {priority_leads[0].score if priority_leads else 'None'}")

if __name__ == "__main__":
    verify_batch3()
