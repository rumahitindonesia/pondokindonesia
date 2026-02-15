import os
import django
import sys

# Setup Django Environment
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pondokindonesia.settings')
django.setup()

from crm.models import Program
from tenants.models import Tenant

def run():
    # 1. Get Tenant
    try:
        tenant = Tenant.objects.get(subdomain='rumah-it')
        print(f"Found tenant: {tenant}")
    except Tenant.DoesNotExist:
        print("Tenant 'rumah-it' not found. Please create it first.")
        return

    # 2. Define Data
    raw_data = """
Zakat Maal (Muzakki Entitas) | DONASI | 0 | 
Zakat Maal (Muzakki Individu) | DONASI | 0 | 
Zakat Fitrah | DONASI | 0 | 
Fidyah | DONASI | 0 | 
Buka Puasa | DONASI | 0 | 
Sedekah Umum | DONASI | 0 | 
Wali Santri IT Berquran | DONASI | 0 | 
Infaq MPP | DONASI | 0 | 
Wakaf Quran | DONASI | 0 | 
Wakaf Masjid | DONASI | 0 | 
Wakaf Sumur Bor | DONASI | 0 | 
Wakaf Dipan Santri | DONASI | 0 | 
Wakaf-Multimedia | DONASI | 0 | 
Wakaf Peralatan Masjid | DONASI | 0 | 
Wakaf-Pembebasan Lahan | DONASI | 0 | 
Wakaf Pembangunan Asrama | DONASI | 0 | 
Wakaf Produktif | DONASI | 0 | 
Qurban | DONASI | 0 | 
Wakaf Semen | DONASI | 0 | 
Wakaf PLC | DONASI | 0 | 
Wakaf Hebel | DONASI | 0 | 
Yatim Bahagia | DONASI | 0 | 
Hadiah Lebaran Anak Yatim | DONASI | 0 | 
Hadiah Lebaran Santri & Pengurus | DONASI | 0 | 
Wakaf AC | DONASI | 0 | 
Wakaf Meja Santri | DONASI | 0 | 
Syiar Dakwah | DONASI | 0 | 
ICH | DONASI | 0 | 
Infaq Seribu Bulan | DONASI | 0 | 
Biaya Pendaftaran | PANGKAL | 250000 | Wajib
Wakaf Bangunan & Fasilitas RIT | PANGKAL | 8500000 | Sekali diawal
Wakaf Bangunan & Fasilitas SIT | PANGKAL | 20000000 | Sekali diawal
SPP Bulanan | SPP | 2000000 | Wajib
SPP Pre-Program (2 Bulan) | SPP | 2500000 | Wajib
"""

    # 3. Parse and Insert
    count = 0
    lines = raw_data.strip().split('\n')
    for line in lines:
        if not line.strip():
            continue
            
        parts = [p.strip() for p in line.split('|')]
        nama_program = parts[0]
        jenis_raw = parts[1]
        try:
            nominal = int(parts[2])
        except ValueError:
            nominal = 0
        keterangan = parts[3] if len(parts) > 3 else ""

        # Map Kind to Model Choices
        # Model only has TAGIHAN and DONASI
        if jenis_raw == 'DONASI':
            jenis = Program.Jenis.DONASI
        else:
            # SPP, PANGKAL -> TAGIHAN
            jenis = Program.Jenis.TAGIHAN
            # Append original type to description if not present
            if jenis_raw not in keterangan:
                keterangan = f"[{jenis_raw}] {keterangan}"

        # Create or Update
        program, created = Program.objects.update_or_create(
            tenant=tenant,
            nama_program=nama_program,
            defaults={
                'jenis': jenis,
                'nominal_standar': nominal,
                'keterangan': keterangan,
                'is_active': True
            }
        )
        
        status = "Created" if created else "Updated"
        print(f"[{status}] {nama_program} ({jenis}) - Rp {nominal}")
        count += 1

    print(f"\nDone! Processed {count} programs.")

if __name__ == '__main__':
    run()
