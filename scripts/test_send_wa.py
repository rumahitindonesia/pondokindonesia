#!/usr/bin/env python3
"""
Test script untuk kirim pesan via StarSender API
Pastikan API key sudah benar di API Settings
"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, '/home/pondok-it/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pondokindonesia.settings')
django.setup()

from core.services.starsender import StarSenderService
from tenants.models import Tenant

def test_send_message():
    """Test kirim pesan ke nomor tertentu"""
    
    # Get tenant rumah-it
    tenant = Tenant.objects.filter(subdomain='rumah-it').first()
    if not tenant:
        print("❌ Tenant 'rumah-it' tidak ditemukan")
        return
    
    print(f"✅ Tenant found: {tenant.name}")
    
    # Test nomor (ganti dengan nomor WA yang valid)
    test_number = input("Masukkan nomor WA tujuan (format: 08xxx atau 628xxx): ").strip()
    
    if not test_number:
        print("❌ Nomor tidak boleh kosong")
        return
    
    # Test message
    test_message = "🧪 Test message dari webhook system.\n\nJika Anda menerima pesan ini, berarti StarSender API berfungsi dengan baik!"
    
    print(f"\nMengirim pesan ke: {test_number}")
    print(f"Tenant: {tenant.name}")
    print(f"Pesan: {test_message}\n")
    
    # Send message
    success, response = StarSenderService.send_message(
        to=test_number,
        body=test_message,
        tenant=tenant
    )
    
    if success:
        print("✅ Pesan berhasil dikirim!")
        print(f"Response: {response}")
    else:
        print("❌ Gagal mengirim pesan")
        print(f"Error: {response}")

if __name__ == '__main__':
    test_send_message()
