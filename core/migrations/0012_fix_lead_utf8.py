from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ('core', '0011_lead_last_draft'),
    ]


def fix_utf8(apps, schema_editor):
    if schema_editor.connection.vendor == 'mysql':
        with schema_editor.connection.cursor() as cursor:
            cursor.execute("ALTER TABLE core_lead CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")

class Migration(migrations.Migration):

    dependencies = [
        ('core', '0011_lead_last_draft'),
    ]

    operations = [
        migrations.RunPython(fix_utf8, migrations.RunPython.noop),
    ]
