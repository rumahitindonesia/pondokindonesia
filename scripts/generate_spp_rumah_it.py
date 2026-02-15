import os
import django
import sys
from datetime import date


# Setup Django Environment
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pondokindonesia.settings')
django.setup()

from crm.models import Santri, TagihanSPP, Program
from tenants.models import Tenant

def run():
    # 1. Get Tenant
    try:
        tenant = Tenant.objects.get(subdomain='rumah-it')
        print(f"Found tenant: {tenant}")
    except Tenant.DoesNotExist:
        print("Tenant 'rumah-it' not found.")
        return

    # 2. Get SPP Amount
    try:
        program_spp = Program.objects.get(
            tenant=tenant, 
            nama_program='SPP Bulanan', 
            jenis=Program.Jenis.TAGIHAN
        )
        nominal_spp = program_spp.nominal_standar
        print(f"Standard SPP Amount: Rp {nominal_spp:,.0f}")
    except Program.DoesNotExist:
        print("Program 'SPP Bulanan' not found. Using default 2,000,000")
        nominal_spp = 2000000

    # 3. Months to Generate
    months = [
        date(2026, 1, 1), # January 2026
        date(2026, 2, 1)  # February 2026
    ]

    # 4. Process Santri
    santris = Santri.objects.filter(tenant=tenant, status=Santri.Status.AKTIF)
    print(f"Processing {santris.count()} active santris...")

    count_created = 0
    count_skipped = 0

    for santri in santris:
        for bulan in months:
            # Jatuh tempo tanggal 10
            jatuh_tempo = bulan.replace(day=10)
            
            tagihan, created = TagihanSPP.objects.get_or_create(
                tenant=tenant,
                santri=santri,
                bulan=bulan,
                defaults={
                    'jumlah': nominal_spp,
                    'jatuh_tempo': jatuh_tempo,
                    'status': TagihanSPP.Status.BELUM_LUNAS,
                    'catatan': 'Auto-generated during migration'
                }
            )
            
            if created:
                print(f"[Created] Bill {bulan.strftime('%b %Y')} for {santri.nama_lengkap}")
                count_created += 1
            else:
                count_skipped += 1

    print(f"\nDone! Created {count_created} bills. Skipped {count_skipped} (already exist).")

if __name__ == '__main__':
    run()
