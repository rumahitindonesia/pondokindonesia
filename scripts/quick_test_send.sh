#!/bin/bash
# Quick test script untuk kirim WA via StarSender
# Jalankan di VPS: ./scripts/quick_test_send.sh

cd /home/triyono/pondok-django

echo "Testing StarSender API..."
echo "Sending message to: 081517002700"
echo ""

.venv/bin/python3 << 'PYTHON_SCRIPT'
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pondokindonesia.settings')
django.setup()

from core.services.starsender import StarSenderService
from tenants.models import Tenant

# Get tenant
tenant = Tenant.objects.filter(subdomain='rumah-it').first()
if not tenant:
    print("❌ Tenant 'rumah-it' tidak ditemukan")
    sys.exit(1)

print(f"✅ Tenant: {tenant.name}")

# Send test message
test_message = """🧪 Test Message dari Webhook System

Jika Anda menerima pesan ini, berarti StarSender API berfungsi dengan baik!

Silakan balas dengan format:
DAFTAR#Nama Anda#Kota Anda

untuk test webhook flow."""

print(f"\nMengirim pesan...")

success, response = StarSenderService.send_message(
    to='081517002700',
    body=test_message,
    tenant=tenant
)

if success:
    print("\n✅ Pesan berhasil dikirim!")
    print(f"Response: {response}")
else:
    print("\n❌ Gagal mengirim pesan")
    print(f"Error: {response}")

PYTHON_SCRIPT
