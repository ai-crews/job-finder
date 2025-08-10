import os
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders


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
