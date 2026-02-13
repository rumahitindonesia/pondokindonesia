import sys
import os
import django

sys.path.append('/home/triyono/pondok-django')
import environ
env_file = '/home/triyono/pondok-django/.env'
if os.path.exists(env_file):
    environ.Env.read_env(env_file)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pondokindonesia.settings')
django.setup()

from core.models import AIKnowledgeBase
from tenants.models import Tenant

print("Checking Tenants...")
for t in Tenant.objects.all():
    print(f"Tenant: {t.name} ({t.subdomain})")
    kbs = AIKnowledgeBase.objects.filter(tenant=t)
    print(f"  - Knowledge Base Entries: {kbs.count()}")
    for kb in kbs:
        print(f"    - Topic: {kb.topic}")
        print(f"      Content: {kb.content[:50]}...")

print("\nChecking Global Knowledge Base...")
kbs = AIKnowledgeBase.objects.filter(tenant__isnull=True)
print(f"  - Global Entries: {kbs.count()}")
for kb in kbs:
    print(f"    - Topic: {kb.topic}")
