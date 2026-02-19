import gspread
import logging
import json
import os
from google.oauth2.service_account import Credentials
from core.models import APISetting

logger = logging.getLogger(__name__)

class GoogleSheetsService:
    SCOPES = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]

    @classmethod
    def get_credentials(cls, tenant=None):
        """
        Retrieves credentials from APISetting (JSON string) or a local file.
        """
        # 1. Try APISetting (Database)
        cred_json = APISetting.get_value("GOOGLE_SHEETS_CREDENTIALS", tenant)
        if cred_json:
            try:
                info = json.loads(cred_json)
                return Credentials.from_service_account_info(info, scopes=cls.SCOPES)
            except Exception as e:
                logger.error(f"Failed to parse Google Credentials from DB: {e}")

        # 2. Try Local File (Fallback)
        cred_path = os.path.join(os.getcwd(), "credentials.json")
        if os.path.exists(cred_path):
            try:
                return Credentials.from_service_account_file(cred_path, scopes=cls.SCOPES)
            except Exception as e:
                logger.error(f"Failed to load Google Credentials from file: {e}")

        return None

    @classmethod
    def get_sheet_data(cls, spreadsheet_id, sheet_name=None, tenant=None):
        """
        Fetch all records from a spreadsheet.
        """
        creds = cls.get_credentials(tenant)
        if not creds:
            return None, "Google API Credentials not configuration found. Please check APISetting 'GOOGLE_SHEETS_CREDENTIALS'."

        try:
            client = gspread.authorize(creds)
            spreadsheet = client.open_by_key(spreadsheet_id)
            
            if sheet_name:
                worksheet = spreadsheet.worksheet(sheet_name)
            else:
                worksheet = spreadsheet.get_worksheet(0) # First sheet

            data = worksheet.get_all_records()
            return data, None
        except gspread.exceptions.SpreadsheetNotFound:
            return None, f"Spreadsheet ID '{spreadsheet_id}' not found. Make sure it is shared with the service account email."
        except Exception as e:
            logger.error(f"Error fetching Google Sheet data: {e}")
            return None, str(e)

    @classmethod
    def get_service_account_email(cls, tenant=None):
        """
        Helper to get the service account email so the user can share the sheet.
        """
        creds = cls.get_credentials(tenant)
        if creds:
            return creds.service_account_email
        return None

    @classmethod
    def get_client(cls, tenant=None):
        creds = cls.get_credentials(tenant)
        if not creds:
            return None
        return gspread.authorize(creds)

    @classmethod
    def find_column_index(cls, spreadsheet_id, sheet_name, header_name, tenant=None):
        """
        Find column index (1-based) for a given header name.
        """
        client = cls.get_client(tenant)
        if not client: return None

        try:
            sh = client.open_by_key(spreadsheet_id)
            ws = sh.worksheet(sheet_name) if sheet_name else sh.get_worksheet(0)
            
            # Get first row
            headers = ws.row_values(1)
            for i, h in enumerate(headers):
                if h.strip().lower() == header_name.lower():
                    return i + 1
            return None
        except Exception as e:
            logger.error(f"Error finding column: {e}")
            return None

    @classmethod
    def update_cell(cls, spreadsheet_id, sheet_name, row, col, value, tenant=None):
        """
        Update a specific cell.
        """
        client = cls.get_client(tenant)
        if not client: return False

        try:
            sh = client.open_by_key(spreadsheet_id)
            ws = sh.worksheet(sheet_name) if sheet_name else sh.get_worksheet(0)
            ws.update_cell(row, col, value)
            return True
        except Exception as e:
            logger.error(f"Error updating cell: {e}")
            return False
