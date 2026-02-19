import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pondokindonesia.settings')
django.setup()

from users.models import User
from tenants.models import Tenant
from core.models import set_current_tenant

print("--- LISTING USERS ---")

# 1. Global Users (if any, though TenantAware might filter them out if tenant is None?)
# TenantAwareModel usually returns objects for current tenant. If no tenant set, it might return empty or global.
# Let's try to fetch all by iterating tenants.

tenants = Tenant.objects.all()
for tenant in tenants:
    set_current_tenant(tenant)
    print(f"\nTenant: {tenant.name}")
    users = User.objects.all()
    for u in users:
        print(f"  - {u.username} (Superuser: {u.is_superuser})")

print("\n--- GLOBAL USER CHECK ---")
set_current_tenant(None)
users = User.objects.all()
for u in users:
    print(f"  - {u.username} (Superuser: {u.is_superuser})")
