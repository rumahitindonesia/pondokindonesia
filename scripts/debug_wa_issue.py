import os
import django
import sys

# Ensure current directory is in path
sys.path.append('/home/pondok-it/app')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pondokindonesia.settings')
django.setup()

from core.models import WhatsAppMessage, Lead, WhatsAppForm

print("--- RECENT WHATSAPP MESSAGES ---")
messages = WhatsAppMessage.objects.order_by('-created_at')[:5]
for m in messages:
    print(f"ID: {m.id} | Sender: {m.sender} | Device: {m.device} | Msg: {m.message}")
    # print(f"Raw: {json.dumps(m.raw_data, indent=2)}")

print("\n--- RECENT LEADS ---")
leads = Lead.objects.order_by('-created_at')[:5]
for l in leads:
    print(f"ID: {l.id} | Name: {l.name} | Phone: {l.phone_number} | Data: {l.data}")

print("\n--- WHATSAPP FORMS ---")
forms = WhatsAppForm.objects.filter(is_active=True)
for f in forms:
    print(f"ID: {f.id} | Keyword: {f.keyword} | Fields: {f.field_map} | Separator: '{f.separator}'")
