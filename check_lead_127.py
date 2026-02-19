import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pondokindonesia.settings')
django.setup()

from core.models import Lead

try:
    lead = Lead.objects.get(id=127)
    print(f"Lead 127 FOUND: {lead.name}")
    print(f"Tenant: {lead.tenant}")
    print(f"Data: {lead.data}")
except Lead.DoesNotExist:
    print("Lead 127 NOT FOUND")
