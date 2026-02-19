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

    @staticmethod
    def parse_datetime(date_str):
        if not date_str: return None
        from datetime import datetime
        # Try parsing various formats
        for fmt in ('%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y', '%Y/%m/%d'):
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        return None

    @staticmethod
    def parse_datetime(date_str):
        if not date_str: return None
        from datetime import datetime
        # Try parsing various formats
        for fmt in ('%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y', '%Y/%m/%d'):
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        return None

    @classmethod
    def sync_transactions(cls, spreadsheet_id, sheet_name=None, tenant=None):
        """
        Sync rows to TransaksiDonasi.
        Expected: Tanggal, Phone Donatur, Nama Program, Nominal, Keterangan
        """
        data, error = GoogleSheetsService.get_sheet_data(spreadsheet_id, sheet_name, tenant)
        if error: return 0, error

        status_col = GoogleSheetsService.find_column_index(spreadsheet_id, sheet_name, 'Status', tenant)
        count = 0

        for i, row in enumerate(data):
            row_lower = {k.lower(): v for k, v in row.items()}
            
            # Skip if already synced
            if status_col and str(row_lower.get('status', '')).upper() == 'SYNCED':
                continue

            phone = str(row_lower.get('phone donatur', '')).strip()
            program_name = str(row_lower.get('nama program', '')).strip()
            nominal_str = str(row_lower.get('nominal', '0')).strip()
            ket = str(row_lower.get('keterangan', '')).strip()
            tgl_str = str(row_lower.get('tanggal', '')).strip()

            if not phone or not program_name:
                continue

            # Parse Nominal
            import re
            nominal = int(re.sub(r'\D', '', nominal_str)) if nominal_str else 0

            # Find Donatur
            donatur = Donatur.objects.filter(tenant=tenant, no_hp=phone).first()
            if not donatur:
                donatur = Donatur.objects.create(
                    tenant=tenant, 
                    no_hp=phone, 
                    nama_donatur="Donatur via GSheet",
                    kategori=Donatur.Kategori.INSIDENTIL
                )

            # Find/Create Program
            from crm.models import Program, TransaksiDonasi
            program, _ = Program.objects.get_or_create(
                tenant=tenant,
                nama_program=program_name,
                defaults={'jenis': Program.Jenis.DONASI}
            )

            # Create Transaction
            trx = TransaksiDonasi.objects.create(
                tenant=tenant,
                donatur=donatur,
                program=program,
                nominal=nominal,
                keterangan=ket,
                status=TransaksiDonasi.Status.VERIFIED # Assume synced data is verified
            )
            
            # Update Date if provided
            parsed_date = cls.parse_datetime(tgl_str)
            if parsed_date:
                trx.tgl_donasi = parsed_date
                trx.save()

            count += 1
            
            # Write processed status back to GSheet
            if status_col:
                GoogleSheetsService.update_cell(
                    spreadsheet_id, 
                    sheet_name, 
                    i + 2, # 1-based index + header
                    status_col, 
                    "SYNCED", 
                    tenant
                )

        return count, None
