import os
import django
import sys

# Setup Django Environment
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pondokindonesia.settings')
django.setup()

from crm.models import Donatur
from tenants.models import Tenant
from users.models import User

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
D000000001 | Bayani | 83824748687 | INSIDENTIL | sulawesi | kiya
D000000002 | Misniatik | 82236039906 | INSIDENTIL | riau | kiya
D000000003 | syafrizal sya | 81370493934 | INSIDENTIL | batubara | kiya
D000000004 | ellynajaya | 81379286711 | INSIDENTIL | lampung | kiya
D000000005 | dahlia mustika | 82181148084 | INSIDENTIL | lampung | kiya
D000000006 | menikismayawati | 81326234343 | INSIDENTIL | surakarta | kiya
D000000007 | Suryani | 0838-3908-9794 | INSIDENTIL | Yogyakarta | kiya
D000000008 | Tonadji | 82124473435 | INSIDENTIL | balik papan | kiya
D000000009 | ibu lilik setyowati | 83874782863 | INSIDENTIL |  | kiya
D000000010 | nyanyu ayunda | 081-3778-69133 | INSIDENTIL |  | kiya
D000000011 | Rafikah | 0877-4327-2814 | INSIDENTIL | kalsel | kiya
D000000012 | pujirahayu | 0852-4465-7541 | INSIDENTIL | jayapura | kiya
D000000013 | Busran | 0821-7830-2026 | INSIDENTIL | bengkulu | kiya
D000000014 | lira | 0858-4663-3209 | INSIDENTIL | Palembang | kiya
D000000015 | Gunawan | 0878-5680-6969 | INSIDENTIL | lombok | kiya
D000000016 | Karlina | 0821-8683-6308 | INSIDENTIL | lampung | kiya
D000000017 | munirah | 0821-7652-0167 | INSIDENTIL | beltim | kiya
D000000018 | Rosidah | 0852-4105-8934 | INSIDENTIL | sulawesi | kiya
D000000019 | Pujiharti Demak | 0851-0022-2263 | INSIDENTIL |  | kiya
D000000020 | Ibu Mia Ciledug | 0813-9820-1227 | INSIDENTIL |  | kiya
D000000021 | kulaedi | 0813-2371-2180 | INSIDENTIL | bandung | kiya
D000000022 | Carolina helmi | 0815-9172-603 | INSIDENTIL |  | kiya
D000000023 | Rina darno | 0821-4889-7156 | INSIDENTIL | maluku | kiya
D000000024 | ibu mulyana | 0812-8888-9233 | INSIDENTIL |  | kiya
D000000025 | Andi kurnia | 0889-7621-9848 | INSIDENTIL | jakarta | kiya
D000000026 | Nur imaningrum | 0853-3174-0643 | INSIDENTIL |  | kiya
D000000027 | Ibu Sunarti | 0812-7151-8546 | INSIDENTIL |  | kiya
D000000028 | Ibu Anas Cimahi | 0888-0216-8562 | INSIDENTIL |  | kiya
D000000029 | Rini medan | 0821-7384-7641 | INSIDENTIL |  | kiya
D000000030 | Muli Makassar | 0822-1758-8911 | INSIDENTIL |  | kiya
D000000031 | Winda Kaltim | 0896-6623-0808 | INSIDENTIL |  | kiya
D000000032 | awaliyah medan | 0812-6040-7471 | INSIDENTIL |  | kiya
D000000033 | Lies nurhaida lombok | 0823-5904-7097 | INSIDENTIL |  | kiya
"""

    # 3. Parse and Insert
    count = 0
    lines = [l.strip() for l in raw_data.strip().split('\n') if l.strip()]
    
    # Cache PIC users
    user_cache = {}

    for line in lines:
        parts = [p.strip() for p in line.split('|')]
        # Columns: kode_donatur | nama_donatur | no_hp | kategori | alamat | pic_username
        
        kode = parts[0]
        nama = parts[1]
        hp = parts[2]
        kat = parts[3]
        alamat = parts[4]
        pic_user = parts[5].lower() if len(parts) > 5 else None

        # Fetch PIC
        pic_obj = None
        if pic_user:
            if pic_user not in user_cache:
                try:
                    user_cache[pic_user] = User._base_manager.get(username=pic_user)
                except User.DoesNotExist:
                    user_cache[pic_user] = None
                    print(f"Warning: User '{pic_user}' not found.")
            pic_obj = user_cache[pic_user]

        # Create or Update
        donatur, created = Donatur.objects.update_or_create(
            tenant=tenant,
            kode_donatur=kode,
            defaults={
                'nama_donatur': nama,
                'no_hp': hp,
                'kategori': kat,
                'alamat': alamat,
                'pic_fundraiser': pic_obj
            }
        )
        
        status = "Created" if created else "Updated"
        print(f"[{status}] {nama} ({kode}) - PIC: {pic_user}")
        count += 1

    print(f"\nDone! Processed {count} donaturs.")

if __name__ == '__main__':
    run()
