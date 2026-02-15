import os
import django
import sys
from datetime import datetime

# Setup Django Environment
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pondokindonesia.settings')
django.setup()

from crm.models import Santri
from tenants.models import Tenant

def run():
    # 1. Get Tenant
    try:
        tenant = Tenant.objects.get(subdomain='rumah-it')
        print(f"Found tenant: {tenant}")
    except Tenant.DoesNotExist:
        print("Tenant 'rumah-it' not found.")
        return

    # 2. Define Data
    raw_data = """
SRIT00000001 | ACHMAD NURUL HUDA |  |  |  |  |  | AKTIF
SRIT00000002 | ARMAN SYA'BANI |  |  |  |  |  | AKTIF
SRIT00000003 | AWTA DUDELA |  |  |  |  |  | AKTIF
SRIT00000004 | DAFFA ADITIYA MAZDA |  |  |  |  |  | AKTIF
SRIT00000005 | DEFENSE IRGI HARYONO |  |  |  |  |  | AKTIF
SRIT00000006 | DIANDRA ABYAN ZAHRAN |  |  |  |  |  | AKTIF
SRIT00000007 | FADHLI AL FAJRI  |  |  |  |  |  | AKTIF
SRIT00000008 | FAHRI  |  |  |  |  |  | AKTIF
SRIT00000009 | FARUK  |  |  |  |  |  | AKTIF
SRIT00000010 | FIRMANSYAH |  |  |  |  |  | AKTIF
SRIT00000011 | IKHYA HASNUANSYAH |  |  |  |  |  | AKTIF
SRIT00000012 | ILHAN ROSHAN |  |  |  |  |  | AKTIF
SRIT00000013 | LUQMAN MALIKI L |  |  |  |  |  | AKTIF
SRIT00000014 | MISBAHUN ALFIANTO  |  |  |  |  |  | AKTIF
SRIT00000015 | MUHAMMAD FARID HUSAIN |  |  |  |  |  | AKTIF
SRIT00000016 | MUHAMMAD NAUFAL RASYID  |  |  |  |  |  | AKTIF
SRIT00000017 | MUHAMMAD RAYHAN SAPUTRA  |  |  |  |  |  | AKTIF
SRIT00000018 | MUHAMMAD TSAQIF ALFARISI |  |  |  |  |  | AKTIF
SRIT00000019 | MUHAMMAD UKASYA  |  |  |  |  |  | AKTIF
SRIT00000020 | RAIHAN NUR ICHSAN |  |  |  |  |  | AKTIF
SRIT00000021 | YUSRIL YUDISTIRA |  |  |  |  |  | AKTIF
SRIT00000022 | ZHAFRAN HARITS |  |  |  |  |  | AKTIF
SRIT00000023 | YUSUF RAMADHANI |  |  |  |  |  | AKTIF
SRIT00000024 | ZIDAN ALBANI |  |  |  |  |  | AKTIF
SRIT00000025 | RAYHAN |  |  |  |  |  | AKTIF
SRIT00000026 | AUFFA BILQIS SIDQIA |  |  |  |  |  | AKTIF
SRIT00000027 | MUHAMMAD ZAKI ATTHORIQ |  |  |  |  |  | AKTIF
SRIT00000028 | FAIRUUZ ZAHRAN |  |  |  |  |  | AKTIF
SRIT00000029 | SENA  ALMAHDI ASHARI WIGUNA  |  |  |  |  |  | AKTIF
SSIT00000001 | BAJA MALIK SYAHID |  |  |  |  |  | AKTIF
SSIT00000002 | LEXY EVANDRA PUTRA ANGGARA |  |  |  |  |  | AKTIF
SSIT00000003 | MUHAMMAD LUTHFI AZIZ |  |  |  |  |  | AKTIF
SSIT00000004 | NABILA MUNAWAROH |  |  |  |  |  | AKTIF
SSIT00000005 | TSABITA ARINAL HAQ |  |  |  |  |  | AKTIF
"""

    # 3. Parse and Insert
    count = 0
    lines = raw_data.strip().split('\n')
    for line in lines:
        if not line.strip():
            continue
            
        parts = [p.strip() for p in line.split('|')]
        # Columns: nis | nama_lengkap | nama_panggilan | tgl_lahir | alamat | nama_wali | no_hp_wali | status
        
        nis = parts[0]
        nama_lengkap = parts[1]
        
        # Handle optionals
        nama_panggilan = parts[2] if parts[2] else ""
        
        tgl_lahir = None
        if parts[3]:
            try:
                tgl_lahir = datetime.strptime(parts[3], '%Y-%m-%d').date()
            except:
                pass # Fail silently
                
        alamat = parts[4] if parts[4] else ""
        
        # Handle Required Fields that are missing in source
        # We will use temporary placeholders
        nama_wali = parts[5] if parts[5] else f"Wali {nama_lengkap}"
        
        # Generate unique dummy phone based on NIS if missing
        # NIS format: SRIT00000001 -> take last 8 digits
        if parts[6]:
            no_hp_wali = parts[6]
        else:
            # Create dummy 62800 + last 8 digits of NIS to ensure uniqueness
            # Handle collision between SRIT and SSIT
            import re
            numeric_part = re.sub(r'\D', '', nis)
            if not numeric_part:
                 numeric_part = str(count).zfill(8)
            
            # Use different prefix for SSIT to avoid collision with SRIT
            # SRIT -> 99, SSIT -> 88
            prefix_code = "99"
            if "SSIT" in nis:
                prefix_code = "88"
            
            # Take last 6 digits only (since we add 2 digits prefix)
            suffix = numeric_part[-6:]
            no_hp_wali = f"62800{prefix_code}{suffix}" 
        
        status_raw = parts[7]
        status = Santri.Status.AKTIF
        if status_raw == 'LULUS': status = Santri.Status.LULUS
        elif status_raw == 'CUTI': status = Santri.Status.CUTI
        elif status_raw == 'KELUAR': status = Santri.Status.KELUAR

        # Create or Update
        santri, created = Santri.objects.update_or_create(
            tenant=tenant,
            nis=nis,
            defaults={
                'nama_lengkap': nama_lengkap,
                'nama_panggilan': nama_panggilan,
                'tgl_lahir': tgl_lahir,
                'alamat': alamat,
                'nama_wali': nama_wali,
                'no_hp_wali': no_hp_wali,
                'status': status
            }
        )
        
        status_msg = "Created" if created else "Updated"
        print(f"[{status_msg}] {nama_lengkap} ({nis})")
        count += 1

    print(f"\nDone! Processed {count} santris.")

if __name__ == '__main__':
    run()
