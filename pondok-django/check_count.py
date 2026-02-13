import sys
import os
import django
sys.path.append('/home/triyono/pondok-django')
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pondokindonesia.settings")
django.setup()
from core.models import WhatsAppMessage
print(f"COUNT: {WhatsAppMessage.objects.count()}")
