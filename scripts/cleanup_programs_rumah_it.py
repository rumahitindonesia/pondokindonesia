import os
import django
import sys

# Setup Django Environment
sys.path.append('/home/pondok-it/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pondokindonesia.settings')
django.setup()

from crm.models import Program
from tenants.models import Tenant

def run():
    # 1. Get Tenant
    try:
        tenant = Tenant.objects.get(subdomain='rumah-it')
        print(f"Target tenant: {tenant}")
    except Tenant.DoesNotExist:
        print("Tenant 'rumah-it' not found.")
        return

    # 2. Define Valid Programs (White-list)
    valid_programs = [
        "Zakat Maal (Muzakki Entitas)",
        "Zakat Maal (Muzakki Individu)",
        "Zakat Fitrah",
        "Fidyah",
        "Buka Puasa",
        "Sedekah Umum",
        "Wali Santri IT Berquran",
        "Infaq MPP",
        "Wakaf Quran",
        "Wakaf Masjid",
        "Wakaf Sumur Bor",
        "Wakaf Dipan Santri",
        "Wakaf-Multimedia",
        "Wakaf Peralatan Masjid",
        "Wakaf-Pembebasan Lahan",
        "Wakaf Pembangunan Asrama",
        "Wakaf Produktif",
        "Qurban",
        "Wakaf Semen",
        "Wakaf PLC",
        "Wakaf Hebel",
        "Yatim Bahagia",
        "Hadiah Lebaran Anak Yatim",
        "Hadiah Lebaran Santri & Pengurus",
        "Wakaf AC",
        "Wakaf Meja Santri",
        "Syiar Dakwah",
        "ICH",
        "Infaq Seribu Bulan",
        "Biaya Pendaftaran",
        "Wakaf Bangunan & Fasilitas RIT",
        "Wakaf Bangunan & Fasilitas SIT",
        "SPP Bulanan",
        "SPP Pre-Program (2 Bulan)"
    ]

    # 3. Find invalid programs
    invalid_programs = Program.objects.filter(tenant=tenant).exclude(nama_program__in=valid_programs)
    
    count = invalid_programs.count()
    if count == 0:
        print("No old programs found to delete.")
        return

    print(f"Found {count} old programs to delete:")
    for p in invalid_programs:
        print(f"- {p.nama_program}")

    # 4. Delete
    # confirm = input("Are you sure? (y/n): ") # Skip input for automation script
    invalid_programs.delete()
    print(f"\nSuccessfully deleted {count} programs.")

if __name__ == '__main__':
    run()
