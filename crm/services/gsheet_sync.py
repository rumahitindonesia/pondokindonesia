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

        # Find Status column (optional)
        status_col = GoogleSheetsService.find_column_index(spreadsheet_id, sheet_name, 'Status', tenant)

        count = 0
        for i, row in enumerate(data):
            # Normalize keys to lowercase for case-insensitive matching
            row_lower = {k.lower(): v for k, v in row.items()}
            
            # Check if already synced
            if status_col and str(row_lower.get('status', '')).lower() == 'synced':
                continue
            
            name = str(row_lower.get('nama', '')).strip()
            phone = str(row_lower.get('phone', '')).strip()
            
            if not name or not phone:
                continue

            # Basic phone normalization
            if phone.startswith('0'):
                phone = '62' + phone[1:]
            
            # Check for existing lead
            try:
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
                
                # Write back status
                if status_col:
                    GoogleSheetsService.update_cell(spreadsheet_id, sheet_name, i + 2, status_col, "Synced", tenant)
                    
            except Exception as e:
                logger.error(f"Error syncing row {i+2}: {e}")
        
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

        # Find Status column
        status_col = GoogleSheetsService.find_column_index(spreadsheet_id, sheet_name, 'Status', tenant)

        count = 0
        for i, row in enumerate(data):
            # Normalize keys to lowercase for case-insensitive matching
            row_lower = {k.lower(): v for k, v in row.items()}

            # Check if already synced
            if status_col and str(row_lower.get('status', '')).lower() == 'synced':
                continue

            name = str(row_lower.get('nama', '')).strip()
            phone = str(row_lower.get('phone', '')).strip()
            
            if not name or not phone:
                continue
            
            try:
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
                
                # Write back status
                if status_col:
                    GoogleSheetsService.update_cell(spreadsheet_id, sheet_name, i + 2, status_col, "Synced", tenant)
            
            except Exception as e:
                logger.error(f"Error syncing row {i+2}: {e}")
                
        return count, None

    @classmethod
    def sync_santri(cls, spreadsheet_id, sheet_name=None, tenant=None):
        """
        Sync rows to Santri model.
        Expected: NIS, Nama Lengkap, Nama Panggilan, Nama Wali, No HP Wali, Alamat
        """
        data, error = GoogleSheetsService.get_sheet_data(spreadsheet_id, sheet_name, tenant)
        if error: return 0, error

        status_col = GoogleSheetsService.find_column_index(spreadsheet_id, sheet_name, 'Status', tenant)
        count = 0

        for i, row in enumerate(data):
            row_lower = {k.lower(): v for k, v in row.items()}
            
            if status_col and str(row_lower.get('status', '')).lower() == 'synced':
                continue

            nis = str(row_lower.get('nis', '')).strip()
            nama = str(row_lower.get('nama lengkap', '')).strip()
            
            if not nis or not nama:
                continue
            
            try:
                santri, created = Santri.objects.update_or_create(
                    tenant=tenant,
                    nis=nis,
                    defaults={
                        'nama_lengkap': nama,
                        'nama_panggilan': row_lower.get('nama panggilan', ''),
                        'nama_wali': row_lower.get('nama wali', ''),
                        'no_hp_wali': str(row_lower.get('no hp wali', '')).strip(),
                        'alamat': row_lower.get('alamat', '')
                    }
                )
                if created: count += 1

                if status_col:
                    GoogleSheetsService.update_cell(spreadsheet_id, sheet_name, i + 2, status_col, "Synced", tenant)
            
            except Exception as e:
                logger.error(f"Error syncing santri row {i+2}: {e}")

        return count, None

    @classmethod
    def sync_transactions(cls, spreadsheet_id, sheet_name=None, tenant=None):
        """
        Sync rows to TransaksiDonasi.
        Expected: Phone Donatur, Nama Program, Nominal, Keterangan
        """
        from crm.models import Program, TransaksiDonasi
        
        data, error = GoogleSheetsService.get_sheet_data(spreadsheet_id, sheet_name, tenant)
        if error: return 0, error

        status_col = GoogleSheetsService.find_column_index(spreadsheet_id, sheet_name, 'Status', tenant)
        count = 0

        for i, row in enumerate(data):
            row_lower = {k.lower(): v for k, v in row.items()}
            
            if status_col and str(row_lower.get('status', '')).lower() == 'synced':
                continue

            phone = str(row_lower.get('phone donatur', '')).strip()
            # Normalize phone
            if phone.startswith('0'): phone = '62' + phone[1:]
            
            prog_name = str(row_lower.get('nama program', '')).strip()
            nominal = str(row_lower.get('nominal', '0')).replace(',', '').replace('.', '').strip()
            
            if not phone or not prog_name:
                continue

            try:
                # 1. Get/Create Donatur
                donatur, _ = Donatur.objects.get_or_create(
                    tenant=tenant,
                    no_hp=phone,
                    defaults={'nama_donatur': f"Donatur {phone}", 'kategori': Donatur.Kategori.INSIDENTIL}
                )

                # 2. Find Program
                program = Program.objects.filter(nama_program__icontains=prog_name).first()
                if not program:
                    logger.warning(f"Program '{prog_name}' not found for row {i+2}")
                    continue

                # 3. Create Transaction
                trx = TransaksiDonasi.objects.create(
                    tenant=tenant,
                    donatur=donatur,
                    program=program,
                    nominal=int(nominal) if nominal.isdigit() else 0,
                    keterangan=f"GSheet Import: {row_lower.get('keterangan', '')}",
                    status=TransaksiDonasi.Status.VERIFIED
                )
                
                count += 1

                if status_col:
                    GoogleSheetsService.update_cell(spreadsheet_id, sheet_name, i + 2, status_col, "Synced", tenant)
            
            except Exception as e:
                logger.error(f"Error syncing transaction row {i+2}: {e}")

        return count, None
