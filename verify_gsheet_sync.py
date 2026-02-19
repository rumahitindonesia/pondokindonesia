import json
from unittest.mock import patch, MagicMock
from crm.services.gsheet_sync import GSheetSyncService
from core.models import Lead
from tenants.models import Tenant as TenantModel

def verify_gsheet_sync():
    print("--- Verifying Google Sheets Sync Logic ---")
    
    # 1. Setup Tenant
    tenant = TenantModel.objects.first()
    if not tenant:
        print("Creating test tenant...")
        tenant = TenantModel.objects.create(subdomain='test', name='Test Tenant')

    # 2. Mock Data
    mock_data = [
        {'Nama': 'GSheet User 1', 'Phone': '081234567891', 'Kota': 'Jakarta', 'Sekolah': 'SMA 1', 'Catatan': 'Test row 1'},
        {'Nama': 'GSheet User 2', 'Phone': '6281234567892', 'Kota': 'Bandung', 'Sekolah': 'SMA 2', 'Catatan': 'Test row 2'},
        {'Nama': 'Invalid User', 'Phone': '', 'Kota': 'Nowhere', 'Sekolah': 'None', 'Catatan': 'Should skip'}
    ]

    # 3. Test Lead Sync
    print("\nTesting Lead Sync Mapping...")
    with patch('core.services.google_sheets.GoogleSheetsService.get_sheet_data') as mock_get_data:
        mock_get_data.return_value = (mock_data, None)
        
        count, error = GSheetSyncService.sync_leads('mock_spreadsheet_id', tenant=tenant)
        
        if error:
            print(f"Sync error: {error}")
        else:
            print(f"Sync successful. Records processed: {count}")
            
            # Verify database contents
            lead1 = Lead.objects.filter(phone_number='6281234567891').first()
            if lead1 and lead1.name == 'GSheet User 1':
                print("Lead 1 mapped correctly.")
            else:
                print("Lead 1 mapping FAILED!")

            lead2 = Lead.objects.filter(phone_number='6281234567892').first()
            if lead2 and lead2.name == 'GSheet User 2':
                print("Lead 2 mapped correctly.")
            else:
                print("Lead 2 mapping FAILED!")

            invalid_lead = Lead.objects.filter(name='Invalid User').first()
            if not invalid_lead:
                print("Invalid lead skipped correctly.")
            else:
                print("Invalid lead skip FAILED!")

    print("\nVerification complete.")

if __name__ == "__main__":
    verify_gsheet_sync()
