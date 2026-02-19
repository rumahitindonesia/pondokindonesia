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
    
    print(f"Linking Lead {lead.name} to Santri {santri.nama_lengkap}")
    
    lead.santri = santri
    lead.save()
    
    print("Link established successfully.")
    print(f"Lead now points to Santri ID: {lead.santri.id}")
    
except Exception as e:
    print(f"Error: {e}")
