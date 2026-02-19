import os
import django
import sys

sys.path.append('/home/triyono/pondok-django')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pondokindonesia.settings')
django.setup()

from core.models import Lead
from crm.models import Santri

try:
    lead = Lead.objects.get(id=127)
    santri = Santri.objects.get(id=39)
    
    print(f"Syncing Lead {lead.name} to Santri {santri.nama_lengkap}")
    
    santri.nama_lengkap = lead.name
    santri.alamat = lead.data.get('alamat')
    santri.nama_wali = lead.data.get('nama_ayah') or lead.data.get('nama_ibu') or santri.nama_wali
    
    # Normalisasi HP
    hp = lead.phone_number
    santri.no_hp_wali = hp
    
    tgl_lahir = lead.data.get('tanggal_lahir')
    if tgl_lahir:
        santri.tgl_lahir = tgl_lahir
        
    santri.save()
    print("Santri updated successfully.")
    print(f"Alamat: {santri.alamat}")
    print(f"Wali: {santri.nama_wali}")
    print(f"HP: {santri.no_hp_wali}")
    
except Exception as e:
    print(f"Error: {e}")
