import os
import django
import sys
import json
import re
from unittest.mock import MagicMock, patch

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pondokindonesia.settings')
django.setup()

from core.services.ai_service import AIService
from tenants.models import Tenant
from core.models import Lead, AIKnowledgeBase
from crm.models import Donatur
from users.models import User

def verify_fixes():
    print("--- VERIFYING IPAYMU & SIGNAL FIXES ---")
    tenant = Tenant.objects.get(subdomain='test')
    
    # 1. Test Context Sanitization
    print("\n1. Testing RAG Context Sanitization...")
    with patch('core.services.ai_service.AIService.find_relevant_knowledge') as mock_rag:
        mock_rag.return_value = "Silakan transfer ke BSI 7830030012"
        
        prompt = AIService.get_system_prompt(tenant=tenant, query="Mau donasi 150rb")
        print(f"\n--- PROMPT PREVIEW (End) ---\n{prompt[-800:]}")
        
        if "7830030012" in prompt:
            print("FAILED: Bank account number still visible in prompt!")
        elif "[NOMOR REKENING DISEMBUNYIKAN - GUNAKAN LINK PEMBAYARAN]" in prompt:
            print("PASSED: Bank account number masked correctly.")
        else:
            print("FAILED: Bank account context was expected but not found/masked.")

    # 2. Test Money Override Logic
    print("\n2. Testing Money Override Instructions...")
    if "!!! INSTRUKSI DARURAT (PRIORITAS TERTINGGI) !!!" in prompt:
        print("PASSED: Money Override instruction injected.")
    else:
        print("FAILED: Money Override instruction missing.")

    # 3. Test Signal Multiple User Fix
    print("\n3. Testing Signal Multiple User Fix...")
    phone = "6289999999999"
    # Create an existing user with same phone but different tenant or something
    User.all_objects.filter(phone_number=phone).delete()
    
    # Simulate first lead creation
    print("Creating first lead...")
    Lead.objects.create(tenant=tenant, phone_number=phone, name="Lead 1")
    
    # Simulate second lead creation (should not fail with Multiple-Objects returned)
    print("Creating second lead (should not crash)...")
    try:
        Lead.objects.create(tenant=tenant, phone_number=phone, name="Lead 2")
        print("PASSED: Multiple lead creation for same phone didn't crash.")
    except Exception as e:
        print(f"FAILED: Signal crashed: {e}")

    print("\n--- VERIFICATION COMPLETE ---")

if __name__ == "__main__":
    verify_fixes()
