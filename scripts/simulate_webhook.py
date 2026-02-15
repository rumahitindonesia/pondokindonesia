#!/usr/bin/env python3
"""
Simulate incoming webhook dari StarSender
Untuk test apakah webhook endpoint berfungsi
"""

import requests
import json

# Webhook URL
WEBHOOK_URL = "https://pondokindonesia.online/webhook/whatsapp/rumah-it/"

# Sample payload dari StarSender
payload = {
    "device": "6281234567890",  # Nomor gateway
    "message": "DAFTAR#Ahmad Rizki#Surabaya",  # Test message dengan format
    "from": "6281999888777",  # Nomor pengirim
    "push_name": "Ahmad",  # Nama pengirim
    "is_me": False  # Bukan echo message
}

print("="*60)
print("TESTING WEBHOOK ENDPOINT")
print("="*60)
print(f"\nWebhook URL: {WEBHOOK_URL}")
print(f"\nPayload:")
print(json.dumps(payload, indent=2))
print("\nSending request...\n")

try:
    response = requests.post(
        WEBHOOK_URL,
        json=payload,
        timeout=10,
        headers={'Content-Type': 'application/json'}
    )
    
    print(f"Response Status: {response.status_code}")
    print(f"Response Body: {response.text}")
    
    if response.status_code == 200:
        print("\n✅ Webhook responded successfully!")
        print("\nSekarang cek:")
        print("1. Admin Panel → WhatsApp Messages (harus ada 1 message baru)")
        print("2. Admin Panel → Leads (harus ada lead 'Ahmad Rizki')")
        print("3. WA nomor 6281999888777 (harus dapat AI greeting)")
        print("4. WA nomor CS (harus dapat notifikasi lead baru)")
    else:
        print(f"\n❌ Webhook returned error: {response.status_code}")
        print("Check logs di VPS untuk detail error")
        
except requests.exceptions.Timeout:
    print("❌ Request timeout - webhook tidak merespons dalam 10 detik")
    print("Kemungkinan service tidak running atau ada error")
    
except requests.exceptions.ConnectionError as e:
    print(f"❌ Connection error: {e}")
    print("Kemungkinan URL salah atau server tidak bisa diakses")
    
except Exception as e:
    print(f"❌ Error: {e}")

print("\n" + "="*60)
