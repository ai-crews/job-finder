import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from config.settings import GMAIL_SCOPES, CREDENTIALS_FILE, TOKEN_FILE
from dotenv import load_dotenv

load_dotenv()


def authenticate_gmail():
    """Gmail API 인증"""
    creds = None

    # 기존 토큰이 있으면 로드
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, GMAIL_SCOPES)

    # 유효한 인증 정보가 없으면 새로 로그인
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # credentials.json 파일 사용
            if os.path.exists(CREDENTIALS_FILE):
                flow = InstalledAppFlow.from_client_secrets_file(
                    CREDENTIALS_FILE, GMAIL_SCOPES
                )
            else:
                raise FileNotFoundError(f"{CREDENTIALS_FILE} 파일이 없습니다.")

            creds = flow.run_local_server(port=0)

        # 토큰 저장
        with open(TOKEN_FILE, "w") as token:
            token.write(creds.to_json())

    return build("gmail", "v1", credentials=creds)
