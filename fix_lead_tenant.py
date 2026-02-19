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
    print(f"Lead Found: {lead.name} (Current Tenant: {lead.tenant})")
    
    # Enable global search for correct santri to get tenant
    # Using the ID 39 from previous context
    santri = Santri.objects.get(id=39)
    print(f"Santri Found: {santri.nama_lengkap} (Tenant: {santri.tenant})")
    
    if lead.tenant != santri.tenant:
        print(f"Updating Lead Tenant to: {santri.tenant}")
        lead.tenant = santri.tenant
        lead.save()
        print("Lead updated successfully.")
    else:
        print("Lead already has correct tenant.")
        
except Exception as e:
    print(f"Error: {e}")
