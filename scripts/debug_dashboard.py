import os
import django
import sys
from datetime import datetime
from django.db.models import Sum
from django.utils import timezone

# Setup Django Environment
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pondokindonesia.settings')
django.setup()

from crm.models import TagihanSPP, Tagihan, Program
from tenants.models import Tenant

def run():
    try:
        tenant = Tenant.objects.get(subdomain='rumah-it')
        print(f"Tenant: {tenant} (ID: {tenant.id})")
    except Tenant.DoesNotExist:
        print("Tenant 'rumah-it' not found.")
        return

    now = timezone.now()
    first_day_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    print(f"First Day of Month: {first_day_of_month}")

    # Check TagihanSPP Count
    count_spp = TagihanSPP.objects.filter(tenant=tenant).count()
    print(f"Total TagihanSPP: {count_spp}")

    # Check Unpaid SPP
    unpaid_spp = TagihanSPP.objects.filter(
        tenant=tenant,
        status__in=['BELUM_LUNAS', 'TERLAMBAT']
    ).count()
    print(f"Unpaid SPP (BELUM_LUNAS/TERLAMBAT): {unpaid_spp}")
    
    # Check if simple filter works
    simple_unpaid = TagihanSPP.objects.filter(tenant=tenant, status='BELUM_LUNAS').count()
    print(f"Simple Unpaid (BELUM_LUNAS): {simple_unpaid}")

    # Check Old Tagihan
    unpaid_old = Tagihan.objects.filter(tenant=tenant, status='BELUM').count()
    print(f"Unpaid Old Tagihan: {unpaid_old}")

    # Total Dashboard should show
    print(f"Dashboard 'Tagihan Belum Lunas' should be: {unpaid_spp + unpaid_old}")

if __name__ == '__main__':
    run()
