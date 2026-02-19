
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
from tenants.models import Tenant
from crm.models import Santri, TagihanProgram, Program

# Get Real Tenant
tenant = Tenant.objects.get(subdomain='pondokit') # Use existing tenant

# Define mocks
@patch('core.services.ai_service.AIService.get_completion')
@patch('core.services.starsender.StarSenderService.send_message')
@patch('core.services.ipaymu.IPaymuService.create_payment')
def run_test(mock_ipaymu, mock_starsender, mock_ai):
    print("--- STARTING TEST ---")
    
    # 1. Setup Mocks
    mock_ai.return_value = "Okey siap [EXEC: CREATE_INVOICE] 10000#Biaya Pendaftaran Santri"
    mock_ipaymu.return_value = ({'session_id': 'sess_123', 'url': 'http://ipaymu.com/pay/123'}, None)
    mock_starsender.return_value = (True, "sent")
    
    # 2. Create Request
    data = {
        "from": "628123456789",
        "message": "Saya mau daftar santri",
        "pushName": "Budi Santoso",
        "is_me": False
    }
    
    factory = RequestFactory()
    request = factory.post(
        '/webhook/whatsapp/test/',
        data=json.dumps(data),
        content_type='application/json'
    )
    request.tenant = tenant # Simulate middleware
    
    # 3. Call View
    print("Calling webhook...")
    response = webhook_whatsapp(request, tenant_slug='pondokit')
    print(f"Response Status: {response.status_code}")
    
    # 4. Verification
    print("\n--- VERIFICATION ---")
    santri = Santri.objects.filter(tenant=tenant, no_hp_wali="628123456789").first()
    if santri:
        print(f"SUCCESS: Santri created. ID: {santri.id} | NIS: {santri.nis}")
    else:
        print("FAIL: Santri NOT created.")
        
    tagihan = TagihanProgram.objects.filter(tenant=tenant, santri=santri if santri else None).first()
    if tagihan:
        print(f"SUCCESS: Tagihan created. ID: {tagihan.id} | Amount: {tagihan.nominal}")
        print(f"Payment URL: {tagihan.payment_url}")
    else:
        print("FAIL: Tagihan NOT created.")

if __name__ == "__main__":
    run_test()
