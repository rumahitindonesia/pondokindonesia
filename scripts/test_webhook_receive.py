#!/usr/bin/env python3
"""
Simulate incoming webhook dari StarSender dengan payload lengkap
Sesuai dengan dokumentasi StarSender
"""

import requests
import json
import time

# Webhook URL
WEBHOOK_URL = "https://pondokindonesia.online/webhook/whatsapp/rumah-it/"

# Sample payload sesuai dokumentasi StarSender
payload = {
    "device_id": "12345",
    "device": "Gateway - 6281234567890",
    "device_name": "Gateway",
    "chat_type": "personal",
    "message_id": "msg_" + str(int(time.time())),
    "from": "6281122334455",  # Nomor Public (New Lead)
    "push_name": "Test User",
    "message": "Halo, saya mau tanya program donasi",  # Pesan bebas (non-keyword)
    "file": "",
    "is_group": False,
    "is_me": False,  # Bukan echo
    "is_mentioned": False,
    "quoted_message": "",
    "timestamp": int(time.time() * 1000)
}

print("="*70)
print("SIMULATING INCOMING WEBHOOK FROM STARSENDER")
print("="*70)
print(f"\n📍 Webhook URL: {WEBHOOK_URL}")
print(f"\n📦 Payload:")
print(json.dumps(payload, indent=2))
print("\n📤 Sending POST request...\n")

try:
    response = requests.post(
        WEBHOOK_URL,
        json=payload,
        timeout=15,
        headers={'Content-Type': 'application/json'}
    )
    
    print(f"✅ Response Status: {response.status_code}")
    print(f"📄 Response Body: {response.text}")
    
    if response.status_code == 200:
        print("\n" + "="*70)
        print("✅ WEBHOOK RESPONDED SUCCESSFULLY!")
        print("="*70)
        print("\n📋 Sekarang cek di Admin Panel:")
        print("   1. WhatsApp Messages → Harus ada message dari 6281517002700")
        print("   2. Leads → Harus ada lead 'Ahmad Rizki' dari Surabaya")
        print("\n📱 Cek WhatsApp:")
        print("   1. Nomor 6281517002700 → Harus dapat AI greeting")
        print("   2. Nomor CS → Harus dapat notifikasi lead baru")
        print("\n📊 Cek Logs di VPS:")
        print("   tail -f /home/triyono/pondok-django/logs/django.log | grep -E 'WEBHOOK|FORM|LEAD|AI|GREETING|CS'")
        print("\n" + "="*70)
    else:
        print("\n" + "="*70)
        print(f"❌ WEBHOOK RETURNED ERROR: {response.status_code}")
        print("="*70)
        print("\nCheck logs di VPS untuk detail error:")
        print("tail -50 /home/triyono/pondok-django/logs/django.log")
        
except requests.exceptions.Timeout:
    print("\n❌ REQUEST TIMEOUT")
    print("Webhook tidak merespons dalam 15 detik")
    print("\nKemungkinan penyebab:")
    print("- Service tidak running")
    print("- Ada infinite loop di code")
    print("- Database query terlalu lama")
    
except requests.exceptions.ConnectionError as e:
    print(f"\n❌ CONNECTION ERROR: {e}")
    print("\nKemungkinan penyebab:")
    print("- URL salah")
    print("- Server tidak bisa diakses")
    print("- Firewall blocking")
    
except Exception as e:
    print(f"\n❌ UNEXPECTED ERROR: {e}")

print("\n" + "="*70)
