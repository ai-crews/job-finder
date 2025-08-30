import gspread
from google.oauth2.service_account import Credentials as ServiceAccountCredentials
from config.settings import SHEETS_SCOPES, SERVICE_ACCOUNT_FILE


def get_sheets_client():
    """Google Sheets 클라이언트 인증"""
    creds = ServiceAccountCredentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE,
        scopes=SHEETS_SCOPES,
    )
    return gspread.authorize(creds)
