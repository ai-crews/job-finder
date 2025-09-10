import gspread
from google.oauth2.service_account import Credentials
import os


def get_sheets_client():
    """Google Sheets 클라이언트 인증 및 반환"""
    try:
        # 서비스 계정 JSON 파일 경로
        credentials_file = os.getenv("GOOGLE_CREDENTIALS_FILE", "credentials.json")

        # 스코프 설정
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ]

        # 인증 정보 로드
        credentials = Credentials.from_service_account_file(
            credentials_file, scopes=scopes
        )

        # gspread 클라이언트 생성
        gc = gspread.authorize(credentials)

        return gc

    except Exception as e:
        print(f"Google Sheets 인증 실패: {e}")
        return None
