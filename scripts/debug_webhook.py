#!/usr/bin/env python3
"""
Debug script untuk webhook WhatsApp
Jalankan di VPS untuk cek konfigurasi dan test flow
"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, '/home/triyono/pondok-django')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pondokindonesia.settings')
django.setup()

from core.models import APISetting, WhatsAppForm
from tenants.models import Tenant
from users.models import User, Role

def check_api_settings():
    """Check if API settings are configured"""
    print("\n" + "="*60)
    print("CHECKING API SETTINGS")
    print("="*60)
    
    # Check StarSender API Key
    starsender = APISetting.objects.filter(
        category='WHATSAPP',
        is_active=True
    ).first()
    
    if starsender:
        print(f"✅ StarSender API Key: Found (value: {starsender.value[:20]}...)")
    else:
        print("❌ StarSender API Key: NOT FOUND")
        print("   → Go to Admin → API Settings → Add new")
        print("   → Category: WhatsApp (StarSender)")
        print("   → Key Name: STARSENDER_API_KEY")
        print("   → Value: <your API key>")
    
    # Check AI Provider
    ai_provider = APISetting.objects.filter(
        key_name='AI_PROVIDER',
        category='AI',
        is_active=True
    ).first()
    
    if ai_provider:
        print(f"✅ AI Provider: {ai_provider.value}")
    else:
        print("❌ AI Provider: NOT FOUND")
        print("   → Go to Admin → API Settings → Add new")
        print("   → Key Name: AI_PROVIDER")
        print("   → Value: GEMINI (or GROQ/OPENAI)")
        print("   → Category: Artificial Intelligence")
    
    # Check AI API Key
    if ai_provider:
        key_name = f"{ai_provider.value}_API_KEY"
        ai_key = APISetting.objects.filter(
            key_name=key_name,
            category='AI',
            is_active=True
        ).first()
        
        if ai_key:
            print(f"✅ {key_name}: Found (value: {ai_key.value[:20]}...)")
        else:
            print(f"❌ {key_name}: NOT FOUND")
            print(f"   → Go to Admin → API Settings → Add new")
            print(f"   → Key Name: {key_name}")
            print(f"   → Value: <your API key>")
            print(f"   → Category: Artificial Intelligence")

def check_whatsapp_forms():
    """Check if WhatsApp forms are configured"""
    print("\n" + "="*60)
    print("CHECKING WHATSAPP FORMS")
    print("="*60)
    
    forms = WhatsAppForm.objects.filter(is_active=True)
    
    if forms.exists():
        print(f"✅ Found {forms.count()} active WhatsApp form(s):")
        for form in forms:
            print(f"\n   Keyword: {form.keyword}")
            print(f"   Separator: {form.separator}")
            print(f"   Fields: {form.field_map}")
            print(f"   Lead Type: {form.lead_type}")
            print(f"   Tenant: {form.tenant or 'Global'}")
    else:
        print("❌ No active WhatsApp forms found")
        print("   → Go to Admin → WhatsApp Forms → Add new")
        print("   → Example:")
        print("      Keyword: DAFTAR")
        print("      Separator: #")
        print("      Field Map: nama#alamat")
        print("      Lead Type: SANTRI")

def check_cs_users():
    """Check if CS users exist"""
    print("\n" + "="*60)
    print("CHECKING CS USERS")
    print("="*60)
    
    cs_role = Role.objects.filter(slug='cs').first()
    
    if not cs_role:
        print("❌ CS Role not found")
        print("   → Go to Admin → Roles → Add new")
        print("   → Name: CS")
        print("   → Slug: cs")
        return
    
    print(f"✅ CS Role found: {cs_role.name}")
    
    cs_users = User.objects.filter(role=cs_role, is_active=True)
    
    if cs_users.exists():
        print(f"✅ Found {cs_users.count()} active CS user(s):")
        for user in cs_users:
            phone = user.phone_number or "NO PHONE"
            print(f"   - {user.username} ({phone})")
            if not user.phone_number:
                print(f"     ⚠️  WARNING: No phone number set!")
    else:
        print("❌ No active CS users found")
        print("   → Go to Admin → Users → Add/Edit user")
        print("   → Set Role: CS")
        print("   → Set Phone Number")

def test_webhook_locally():
    """Test webhook with sample data"""
    print("\n" + "="*60)
    print("TESTING WEBHOOK LOCALLY")
    print("="*60)
    
    # Sample webhook payload
    sample_payload = {
        "device": "6281234567890",
        "message": "DAFTAR#Ahmad Rizki#Surabaya",
        "from": "6281999888777",
        "push_name": "Ahmad",
        "is_me": False
    }
    
    print("\nSample payload:")
    print(f"  Device: {sample_payload['device']}")
    print(f"  From: {sample_payload['from']}")
    print(f"  Message: {sample_payload['message']}")
    
    print("\n⚠️  To test, send this via curl:")
    print(f"\ncurl -X POST https://your-domain.com/webhook/whatsapp/ \\")
    print(f"  -H 'Content-Type: application/json' \\")
    print(f"  -d '{sample_payload}'")

def main():
    print("\n" + "="*60)
    print("WEBHOOK DIAGNOSTIC TOOL")
    print("="*60)
    
    check_api_settings()
    check_whatsapp_forms()
    check_cs_users()
    test_webhook_locally()
    
    print("\n" + "="*60)
    print("DIAGNOSTIC COMPLETE")
    print("="*60)
    print("\nIf all checks pass (✅), webhook should work.")
    print("If any checks fail (❌), fix them first.\n")

if __name__ == '__main__':
    main()
