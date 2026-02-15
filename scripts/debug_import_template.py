
import os
import django
import traceback
from django.conf import settings
from django.template import loader
from django.test import RequestFactory
from django.contrib.auth import get_user_model

# Setup Django (already setup in shell, but safe to ensure)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pondokindonesia.settings")
django.setup()

def debug_render():
    print("Starting debug render...")
    
    try:
        from crm.models import Donatur
        from crm.resources import DonaturResource
        from import_export.forms import ImportForm
        from import_export.formats import base_formats
        
        factory = RequestFactory()
        request = factory.get('/admin/crm/donatur/import/')
        
        User = get_user_model()
        superuser = User.objects.filter(is_superuser=True).first()
        if not superuser:
            print("No superuser found, creating mock")
            superuser = User(username='mock', is_superuser=True, is_active=True)
            
        request.user = superuser
        
        # Mocking context similar to what ImportMixin.import_action provides
        # https://github.com/django-import-export/django-import-export/blob/main/import_export/admin.py
        
        formats = [base_formats.CSV, base_formats.XLSX]
        if hasattr(ImportForm.__init__, '__code__'):
            print(f"ImportForm init args: {ImportForm.__init__.__code__.co_varnames}")
        form = ImportForm(formats, [DonaturResource()], data=request.POST or None, files=request.FILES or None)
        
        context = {
            'form': form,
            'opts': Donatur._meta,
            'title': 'Import Donatur',
            'has_permission': True,
            'site_header': 'Pondok Admin',
            'site_title': 'Pondok',
            'has_file_field': True,
             # Unfold might need these
            'cl': None, 
            'media': form.media,
            'is_popup': False,
            'save_as': False,
            'errors': [],
            'adminform': None, 
        }
        
        # Try finding the template first
        try:
            template = loader.get_template('admin/import_export/import.html')
            print(f"Template found: {template.template.name}")
        except Exception as e:
            print(f"Could not find template: {e}")
            return

        print("Rendering template...")
        content = loader.render_to_string('admin/import_export/import.html', context, request=request)
        print("Render Success!")
        print("Content length:", len(content))
        
    except Exception as e:
        print("\n!!! EXCEPTION CAUGHT !!!")
        traceback.print_exc()

if __name__ == "__main__":
    debug_render()
