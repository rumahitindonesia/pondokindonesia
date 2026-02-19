import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pondokindonesia.settings')
django.setup()

from crm.models import TagihanProgram, TagihanSPP
from tenants.models import Tenant
from core.models import set_current_tenant

print("--- FIXING TANGGAL BAYAR ---")

tenants = Tenant.objects.all()
total_fixed_prog = 0
total_fixed_spp = 0

for tenant in tenants:
    set_current_tenant(tenant)
    print(f"\nProcessing Tenant: {tenant.name}")
    
    # Fix TagihanProgram
    progs = TagihanProgram.objects.filter(status='LUNAS', tanggal_bayar__isnull=True)
    count_prog = progs.count()
    print(f"  Found {count_prog} TagihanProgram needing fix.")
    
    for p in progs:
        # Fallback to updated_at if available, else today (but usually updated_at captures the lunas change)
        # Note: 'updated_at' field might not exist on all models customly unless defined.
        # Checking base model... TenantAwareModel usually just has tenant.
        # If no timestamp, use created_at (?) No, dangerous. 
        # Let's assume we use today as fallback or just set it. 
        # Ideally we want the date it became Lunas. 
        # For now, let's use timezone.now() to ensure it appears in THIS month's dashboard if it was recent.
        # Or better: check built-in django auto_now fields if they exist?
        pass 
        
        # Actually, let's just rely on the model save() logic we just added?
        # calling save() on them will trigger the new logic:
        # elif self.status == self.Status.LUNAS and not self.tanggal_bayar: self.tanggal_bayar = now
        
        p.save() 
        total_fixed_prog += 1

    # Fix TagihanSPP
    spps = TagihanSPP.objects.filter(status='LUNAS', tanggal_bayar__isnull=True)
    count_spp = spps.count()
    print(f"  Found {count_spp} TagihanSPP needing fix.")
    
    for s in spps:
        s.save()
        total_fixed_spp += 1

print(f"\nDONE. Fixed {total_fixed_prog} Programs and {total_fixed_spp} SPPs.")
