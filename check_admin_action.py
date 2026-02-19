import os
import django
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pondokindonesia.settings')
django.setup()

from crm.admin import TransaksiDonasiAdmin, TagihanSPPAdmin, TagihanProgramAdmin
from django.contrib.admin.sites import AdminSite

def has_action(admin_class, action_name):
    if hasattr(admin_class, action_name):
        return True
    
    actions = getattr(admin_class, 'actions', [])
    if not actions:
        return False
        
    for action in actions:
        if isinstance(action, str) and action == action_name:
            return True
        if callable(action) and getattr(action, '__name__', '') == action_name:
            return True
            
    return False

print("Checking TransaksiDonasiAdmin...")
if has_action(TransaksiDonasiAdmin, 'generate_ipaymu_link'):
    print("Found generate_ipaymu_link in TransaksiDonasiAdmin")
else:
    print("generate_ipaymu_link NOT FOUND in TransaksiDonasiAdmin")

print("\nChecking TagihanSPPAdmin...")
if has_action(TagihanSPPAdmin, 'generate_ipaymu_link'):
    print("Found generate_ipaymu_link in TagihanSPPAdmin")
else:
    print("generate_ipaymu_link NOT FOUND in TagihanSPPAdmin")

if has_action(TagihanSPPAdmin, 'send_invoice_whatsapp'):
    print("Found send_invoice_whatsapp in TagihanSPPAdmin")
else:
    print("send_invoice_whatsapp NOT FOUND in TagihanSPPAdmin")

print("\nChecking TagihanProgramAdmin...")
if has_action(TagihanProgramAdmin, 'generate_ipaymu_link'):
    print("Found generate_ipaymu_link in TagihanProgramAdmin")
else:
    print("generate_ipaymu_link NOT FOUND in TagihanProgramAdmin")

if has_action(TagihanProgramAdmin, 'send_invoice_whatsapp'):
    print("Found send_invoice_whatsapp in TagihanProgramAdmin")
else:
    print("send_invoice_whatsapp NOT FOUND in TagihanProgramAdmin")
