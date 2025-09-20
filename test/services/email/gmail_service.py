from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import base64
import os
import pickle
import json

# Gmail API 스코프 (Sheets와 분리된 토큰 사용)
GMAIL_SCOPES = ["https://www.googleapis.com/auth/gmail.send"]


class GmailAPIService:
    def __init__(
        self, credentials_file="credentials.json", token_file="gmail_token.pickle"
    ):
        self.credentials_file = credentials_file
        self.token_file = token_file

        # credentials.json 파일 검증
        self._validate_credentials_file()

        self.service = self._authenticate()

    def _validate_credentials_file(self):
        """credentials.json 파일 유효성 검사"""
        if not os.path.exists(self.credentials_file):
            raise FileNotFoundError(
                f"❌ {self.credentials_file} 파일이 없습니다.\n"
                "Google Cloud Console에서 OAuth 2.0 클라이언트 ID를 생성하고 JSON을 다운로드하세요."
            )

        try:
            with open(self.credentials_file, "r", encoding="utf-8") as f:
                cred_data = json.load(f)

            # 올바른 형식인지 확인
            if "installed" not in cred_data and "web" not in cred_data:
                raise ValueError(
                    f"❌ {self.credentials_file} 파일 형식이 올바르지 않습니다.\n"
                    "OAuth 2.0 클라이언트 ID (데스크톱 애플리케이션)로 생성된 JSON 파일이어야 합니다."
                )

            print(f"✅ {self.credentials_file} 파일 검증 완료")

        except json.JSONDecodeError:
            raise ValueError(
                f"❌ {self.credentials_file} 파일이 유효한 JSON 형식이 아닙니다."
            )
        except Exception as e:
            raise ValueError(f"❌ credentials 파일 검증 중 오류: {e}")

    def _authenticate(self):
        """Gmail API 인증"""
        creds = None

        print("🔐 Gmail API 인증 시작...")

        # 기존 토큰이 있으면 로드
        if os.path.exists(self.token_file):
            try:
                with open(self.token_file, "rb") as token:
                    creds = pickle.load(token)
                print(" 기존 Gmail 토큰 발견")
            except Exception as e:
                print(f" 기존 토큰 로드 실패: {e}")
                creds = None

        # 유효한 자격 증명이 없으면 로그인 플로우 실행
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                print(" Gmail 토큰 갱신 중...")
                try:
                    creds.refresh(Request())
                    print(" Gmail 토큰 갱신 성공")
                except Exception as e:
                    print(f" 토큰 갱신 실패: {e}")
                    creds = None

            if not creds:
                print(" 브라우저에서 Gmail 권한 승인...")

                try:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_file, GMAIL_SCOPES
                    )
                    creds = flow.run_local_server(
                        port=0, prompt="select_account", access_type="offline"
                    )
                    print(" Gmail 권한 승인 완료")
                except Exception as e:
                    raise ValueError(f"❌ OAuth 인증 실패: {e}")

            # 다음 실행을 위해 자격 증명 저장
            try:
                with open(self.token_file, "wb") as token:
                    pickle.dump(creds, token)
                print(f" Gmail 토큰이 {self.token_file}에 저장되었습니다")
            except Exception as e:
                print(f" 토큰 저장 실패: {e}")

        try:
            service = build("gmail", "v1", credentials=creds)
            print(" Gmail API 서비스 초기화 완료")
            return service
        except Exception as e:
            raise ValueError(f"❌ Gmail API 서비스 초기화 실패: {e}")

    def create_message(
        self, to, subject, message_text=None, html_content=None, attachment_path=None
    ):
        """이메일 메시지 생성"""
        message = MIMEMultipart("alternative")
        message["to"] = to
        message["subject"] = subject

        # 텍스트 본문 추가
        if message_text:
            text_part = MIMEText(message_text, "plain", "utf-8")
            message.attach(text_part)

        # HTML 본문 추가
        if html_content:
            html_part = MIMEText(html_content, "html", "utf-8")
            message.attach(html_part)

        # 메시지를 base64로 인코딩
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")
        return {"raw": raw_message}

    def send_message(
        self, to, subject, message_text=None, html_content=None, attachment_path=None
    ):
        """단일 이메일 발송"""
        try:
            message = self.create_message(
                to, subject, message_text, html_content, attachment_path
            )

            result = (
                self.service.users()
                .messages()
                .send(userId="me", body=message)
                .execute()
            )

            print(
                f"✅ {to}에게 이메일이 성공적으로 발송되었습니다! (Message ID: {result['id']})"
            )
            return {"status": "SUCCESS", "email": to, "message_id": result["id"]}

        except Exception as error:
            print(f"❌ {to} 이메일 발송 중 오류가 발생했습니다: {error}")
            return {"status": "FAIL", "email": to, "error": str(error)}
