from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):

    dependencies = [
        ('users', '0003_migrate_roles_data'),
    ]

    operations = [
        # 1. Remove the old CharField 'role'
        migrations.RemoveField(
            model_name='user',
            name='role',
        ),
        # 2. Rename 'role_link' to 'role'
        migrations.RenameField(
            model_name='user',
            old_name='role_link',
            new_name='role',
        ),
    ]
