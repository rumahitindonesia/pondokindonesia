#!/usr/bin/env python3
"""
Test webhook locally to see if it works
"""

import requests
import json

# Test payload (sample dari StarSender)
payload = {
    "device": "6281234567890",
    "message": "DAFTAR#Ahmad Rizki#Surabaya",
    "from": "6281999888777",
    "push_name": "Ahmad",
    "is_me": False
}

# Webhook URL
url = "https://pondokindonesia.online/webhook/whatsapp/rumah-it/"

print("Testing webhook...")
print(f"URL: {url}")
print(f"Payload: {json.dumps(payload, indent=2)}")

try:
    response = requests.post(url, json=payload, timeout=10)
    print(f"\nResponse Status: {response.status_code}")
    print(f"Response Body: {response.text}")
    
    if response.status_code == 200:
        print("\n✅ Webhook responded successfully!")
    else:
        print(f"\n❌ Webhook returned error: {response.status_code}")
        
except requests.exceptions.Timeout:
    print("\n❌ Request timeout - webhook tidak merespons dalam 10 detik")
except requests.exceptions.ConnectionError:
    print("\n❌ Connection error - tidak bisa connect ke webhook URL")
except Exception as e:
    print(f"\n❌ Error: {e}")
