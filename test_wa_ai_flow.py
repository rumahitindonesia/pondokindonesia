import json
from django.test import Client
from core.models import Lead, WhatsAppMessage, APISetting
from tenants.models import Tenant
from users.models import User
from core.services.ai_service import AIService
import unittest
from unittest.mock import patch

def test_wa_ai_flow():
    print("--- Testing WA and AI Integration Flow ---")
    
    # 1. Setup
    tenant = Tenant.objects.first()
    if not tenant:
        print("No tenant found. Please create one.")
        return

    client = Client()
    phone_number = "6281234567890"
    
    # 2. Test Public Message (leads to AI)
    print("\n--- Testing Public Message (leads to AI) ---")
    with patch('core.services.ai_service.AIService.get_completion') as mock_ai:
        mock_ai.return_value = "Halo Budi! Saya simpan data Anda ya. [EXEC: SAVE_LEAD] Budi#Jakarta#SMP 1#SANTRI#85"
        
        payload = {
            "device": "6289656463990",
            "message": "Mau daftar, saya Budi dari Jakarta.",
            "from": phone_number,
            "name": "Budi",
            "is_me": False
        }
        
        response = client.post(
            f'/webhook/whatsapp/{tenant.subdomain}/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        # Verify Lead Creation
        lead = Lead.objects.filter(phone_number=phone_number).order_by('-id').first()
        if lead and lead.name == "Budi":
            print(f"Lead created via AI EXEC tag: {lead.name}")
        else:
            print("Lead creation via AI EXEC tag FAILED!")

    # 3. Test Staff Search (CARI)
    print("\n--- Testing Staff Search (CARI) ---")
    staff = User.objects.filter(is_staff=True).exclude(phone_number__isnull=True).exclude(phone_number="").first()
    if not staff:
        # Update first staff or create one
        staff = User.objects.filter(is_staff=True).first()
        if staff:
            staff.phone_number = "628111111111"
            staff.save()
        else:
            staff = User.objects.create(username="teststaff", is_staff=True, phone_number="628111111111")
        
    print(f"Using staff user: {staff.username} ({staff.phone_number})")
    
    search_payload = {
        "device": "6289656463990",
        "message": "CARI any_keyword",
        "from": staff.phone_number,
        "name": staff.username,
        "is_me": False
    }

    response = client.post(
        f'/webhook/whatsapp/{tenant.subdomain}/',
        data=json.dumps(search_payload),
        content_type='application/json'
    )
    
    # Check if outbound message with results was created
    search_msg = WhatsAppMessage.objects.filter(recipient=staff.phone_number, is_outbound=True).order_by('-created_at').first()
    if search_msg and "Hasil Pencarian" in search_msg.message:
        print("Staff search (CARI) verified successfully.")
        print(f"Result snippet: {search_msg.message.splitlines()[0]}")
    else:
        print(f"Staff search (CARI) FAILED or no results returned. Status: {response.status_code}")
        if response.status_code == 500:
             print("Check logs for 500 error.")

    print("\nTesting complete.")

if __name__ == "__main__":
    test_wa_ai_flow()
