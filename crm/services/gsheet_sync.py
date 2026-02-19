import logging
from core.models import Lead
from crm.models import Santri, Donatur
from core.services.google_sheets import GoogleSheetsService
from django.utils import timezone

logger = logging.getLogger(__name__)

class GSheetSyncService:
    @classmethod
    def sync_leads(cls, spreadsheet_id, sheet_name=None, tenant=None):
        """
        Sync rows to Lead model.
        Expected columns: Nama, Phone, Kota, Sekolah, Sumber, Catatan
        """
        data, error = GoogleSheetsService.get_sheet_data(spreadsheet_id, sheet_name, tenant)
        if error:
            return 0, error

        count = 0
        for row in data:
            # Normalize keys to lowercase for case-insensitive matching
            row_lower = {k.lower(): v for k, v in row.items()}
            
            name = str(row_lower.get('nama', '')).strip()
            phone = str(row_lower.get('phone', '')).strip()
            
            if not name or not phone:
                continue

            # Basic phone normalization
            if phone.startswith('0'):
                phone = '62' + phone[1:]
            
            # Check for existing lead
            lead, created = Lead.objects.update_or_create(
                tenant=tenant,
                phone_number=phone,
                defaults={
                    'name': name,
                    'notes': f"GSheet Sync ({timezone.now().date()}): {row_lower.get('catatan', '')}",
                    'data': {
                        'kota': row_lower.get('kota', ''),
                        'sekolah': row_lower.get('sekolah', ''),
                        'source_gsheet': spreadsheet_id
                    }
                }
            )
            if created:
                count += 1
        
        return count, None

    @classmethod
    def sync_donaturs(cls, spreadsheet_id, sheet_name=None, tenant=None):
        """
        Sync rows to Donatur model.
        Expected columns: Nama, Phone, Alamat, Kategori
        """
        data, error = GoogleSheetsService.get_sheet_data(spreadsheet_id, sheet_name, tenant)
        if error:
            return 0, error

        count = 0
        for row in data:
            # Normalize keys to lowercase for case-insensitive matching
            row_lower = {k.lower(): v for k, v in row.items()}

            name = str(row_lower.get('nama', '')).strip()
            phone = str(row_lower.get('phone', '')).strip()
            
            if not name or not phone:
                continue
            
            # Check for existing donatur
            donatur, created = Donatur.objects.get_or_create(
                tenant=tenant,
                no_hp=phone,
                defaults={
                    'nama_donatur': name,
                    'alamat': row_lower.get('alamat', '-'),
                    'kategori': row_lower.get('kategori', Donatur.Kategori.INSIDENTIL)
                }
            )
            if created:
                count += 1
                
        return count, None
