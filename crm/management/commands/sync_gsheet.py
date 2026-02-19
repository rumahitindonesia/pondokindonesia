from django.core.management.base import BaseCommand
from crm.services.gsheet_sync import GSheetSyncService
from tenants.models import Tenant

class Command(BaseCommand):
    help = 'Sync data from Google Sheets to CRM models'

    def add_arguments(self, parser):
        parser.add_argument('spreadsheet_id', type=str, help='Google Spreadsheet ID')
        parser.add_argument('--model', type=str, default='lead', choices=['lead', 'donatur'], help='Model to sync (lead or donatur)')
        parser.add_argument('--sheet', type=str, default=None, help='Sheet name (optional)')
        parser.add_argument('--tenant', type=str, default=None, help='Tenant slug (optional)')

    def handle(self, *args, **options):
        spreadsheet_id = options['spreadsheet_id']
        model_type = options['model']
        sheet_name = options['sheet']
        tenant_slug = options['tenant']

        tenant = None
        if tenant_slug:
            try:
                tenant = Tenant.objects.get(subdomain=tenant_slug)
            except Tenant.DoesNotExist:
                self.stderr.write(self.style.ERROR(f"Tenant '{tenant_slug}' not found."))
                return

        self.stdout.write(self.style.SUCCESS(f"Starting sync for {model_type} from sheet {spreadsheet_id}..."))

        if model_type == 'lead':
            count, error = GSheetSyncService.sync_leads(spreadsheet_id, sheet_name, tenant)
        elif model_type == 'donatur':
            count, error = GSheetSyncService.sync_donaturs(spreadsheet_id, sheet_name, tenant)

        if error:
            self.stderr.write(self.style.ERROR(f"Sync Failed: {error}"))
        else:
            self.stdout.write(self.style.SUCCESS(f"Sync Successful! {count} records added/updated."))
