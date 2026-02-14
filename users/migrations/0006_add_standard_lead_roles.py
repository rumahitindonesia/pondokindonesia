from django.db import migrations

def create_lead_roles(apps, schema_editor):
    Role = apps.get_model('users', 'Role')
    
    # Global Roles
    standard_roles = [
        {'name': 'Customer Service', 'slug': 'cs', 'is_system': True},
        {'name': 'Admin PSB & Interview', 'slug': 'admin-psb', 'is_system': True},
    ]
    
    for r_data in standard_roles:
        Role.objects.get_or_create(
            slug=r_data['slug'],
            tenant__isnull=True,
            defaults={
                'name': r_data['name'],
                'is_system': r_data['is_system']
            }
        )

class Migration(migrations.Migration):

    dependencies = [
        ('users', '0005_alter_user_managers_user_phone_number'),
    ]

    operations = [
        migrations.RunPython(create_lead_roles),
    ]
