import os
import django
import sys

sys.path.append('/home/pondok-it/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pondokindonesia.settings')
django.setup()

from core.models import Lead
from users.models import User
from crm.models import Santri

print("--- Checking LEADS ---")
leads = Lead.objects.filter(name__icontains='Triyono')
if leads.exists():
    for l in leads:
        print(f"Lead Found: ID={l.id}, Name={l.name}, Tenant={l.tenant}, Created={l.created_at}, Data={l.data.keys()}")
else:
    print("No Lead named Triyono found.")

print("\n--- Checking USERS by Phone ---")
users_phone = User.objects.filter(username__icontains='7002700')
for u in users_phone:
    print(f"User (ByPhone) Found: ID={u.id}, Username={u.username}, Phone={u.phone_number}, Tenant={u.tenant}")

print("\n--- Checking SANTRI ---")
santris = Santri.objects.filter(nama_lengkap__icontains='Triyono')
for s in santris:
    print(f"Santri Found: ID={s.id}, Name={s.nama_lengkap}, Tenant={s.tenant}")
