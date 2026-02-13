from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ('core', '0011_lead_last_draft'),
    ]

    operations = [
        migrations.RunSQL(
            "ALTER TABLE core_lead CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
        ),
    ]
