import os
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Gmail API 스코프 설정
SCOPES = ["https://www.googleapis.com/auth/gmail.send"]


def authenticate_gmail():
    """Gmail API 인증"""
    creds = None

    # 기존 토큰이 있으면 로드
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)

    # 유효한 인증 정보가 없으면 새로 로그인
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # credentials.json 파일 사용 (test.json에서 변경)
            if os.path.exists("credentials.json"):
                flow = InstalledAppFlow.from_client_secrets_file(
                    "credentials.json", SCOPES
                )
            else:
                raise FileNotFoundError("credentials.json 파일이 없습니다.")

            creds = flow.run_local_server(port=0)

        # 토큰 저장
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    return build("gmail", "v1", credentials=creds)


def create_message(
    sender, to, subject, message_text=None, html_content=None, attachment_path=None
):
    """이메일 메시지 생성 (텍스트 또는 HTML 지원)"""
    message = MIMEMultipart("alternative")
    message["to"] = to
    message["from"] = sender
    message["subject"] = subject

    # 텍스트 본문 추가
    if message_text:
        text_part = MIMEText(message_text, "plain", "utf-8")
        message.attach(text_part)

    # HTML 본문 추가
    if html_content:
        html_part = MIMEText(html_content, "html", "utf-8")
        message.attach(html_part)

    # 첨부파일이 있으면 추가
    if attachment_path and os.path.exists(attachment_path):
        with open(attachment_path, "rb") as attachment:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(attachment.read())

        encoders.encode_base64(part)
        part.add_header(
            "Content-Disposition",
            f"attachment; filename={os.path.basename(attachment_path)}",
        )
        message.attach(part)

    # base64로 인코딩
    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
    return {"raw": raw_message}


def send_message(service, user_id, message):
    """이메일 발송"""
    try:
        result = service.users().messages().send(userId=user_id, body=message).execute()
        print(f'이메일이 성공적으로 발송되었습니다! Message ID: {result["id"]}')
        return result
    except Exception as error:
        print(f"이메일 발송 중 오류가 발생했습니다: {error}")
        return None


def load_html_template(html_file_path):
    """HTML 템플릿 파일 로드"""
    try:
        with open(html_file_path, "r", encoding="utf-8") as file:
            return file.read()
    except FileNotFoundError:
        print(f"HTML 파일을 찾을 수 없습니다: {html_file_path}")
        return None
    except Exception as e:
        print(f"HTML 파일 읽기 오류: {e}")
        return None


def send_emails(
    email_list, subject, message_text=None, html_file_path=None, attachment_path=None
):
    """대량 이메일 발송"""
    service = authenticate_gmail()
    sender_email = "me"

    # HTML 파일이 있으면 한 번만 로드
    html_content = None
    if html_file_path:
        html_content = load_html_template(html_file_path)

    success_count = 0
    fail_count = 0

    for email in email_list:
        try:
            message = create_message(
                sender=sender_email,
                to=email,
                subject=subject,
                message_text=message_text,
                html_content=html_content,
                attachment_path=attachment_path,
            )

            result = send_message(service, "me", message)
            if result:
                success_count += 1
                print(f"✅ {email}에게 발송 완료")
            else:
                fail_count += 1
                print(f"❌ {email} 발송 실패")

        except Exception as e:
            fail_count += 1
            print(f"❌ {email} 발송 실패: {e}")

    print(f"\n발송 완료! 성공: {success_count}개, 실패: {fail_count}개")


def send_job_posting_email(recipient_email, html_file_path="email.html"):
    """채용 공고 이메일 발송"""
    return send_emails(
        to_email=recipient_email,
        subject="채용 공고입니다!",
        message_text="채용 공고를 확인해 주세요.",
        html_file_path=html_file_path,
    )


# Gmail API 이메일 발송 테스트
if __name__ == "__main__":
    print("=== Gmail API 이메일 발송 테스트 ===")

    # HTML 파일 경로 설정
    html_file = "email.html"

    # 대량 이메일 발송
    email_list = ["eunbi0976@gmail.com", "rudah96@naver.com"]

    send_emails(
        email_list=email_list,
        subject="이메일 발송 테스트",
        message_text="안녕하세요!\n\n이것은 테스트 이메일입니다.",
        html_file_path=html_file,
    )
