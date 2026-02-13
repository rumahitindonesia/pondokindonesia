import sys
import os
import django
from django.db.models import Count

# Setup Django environment
sys.path.append('/home/triyono/pondok-django')
import environ
env_file = '/home/triyono/pondok-django/.env'
if os.path.exists(env_file):
    environ.Env.read_env(env_file)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pondokindonesia.settings')
django.setup()

from core.models import Lead

def clean_duplicates():
    print("Checking for duplicate Leads...")
    
    # Find duplicates based on phone_number and type
    duplicates = Lead.objects.values('phone_number', 'type').annotate(count=Count('id')).filter(count__gt=1)
    
    if not duplicates:
        print("No duplicates found.")
        return

    print(f"Found {len(duplicates)} sets of duplicates.")
    
    for group in duplicates:
        phone = group['phone_number']
        l_type = group['type']
        count = group['count']
        print(f"Fixing {phone} ({l_type}) - Count: {count}")
        
        # Get all leads for this group, ordered by latest created (keep the latest)
        leads = list(Lead.objects.filter(phone_number=phone, type=l_type).order_by('-created_at'))
        
        # Keep the first one (latest), delete the rest
        keep = leads[0]
        discard = leads[1:]
        
        print(f"  Keeping ID: {keep.id} (Created: {keep.created_at})")
        for d in discard:
            print(f"  Deleting ID: {d.id} (Created: {d.created_at})")
            d.delete()
            
    print("Done cleaning duplicates.")

if __name__ == "__main__":
    clean_duplicates()
