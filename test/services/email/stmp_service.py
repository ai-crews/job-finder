from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import smtplib
import os


class SMTPEmailService:
    def __init__(self, smtp_server, smtp_port, email, password):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.email = email
        self.password = password

    def create_message(
        self, to, subject, message_text=None, html_content=None, attachment_path=None
    ):
        """이메일 메시지 생성"""
        message = MIMEMultipart("alternative")
        message["From"] = self.email
        message["To"] = to
        message["Subject"] = subject

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

        return message

    def send_message(
        self, to, subject, message_text=None, html_content=None, attachment_path=None
    ):
        """단일 이메일 발송"""
        try:
            message = self.create_message(
                to, subject, message_text, html_content, attachment_path
            )

            # SMTP 서버 연결
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()  # TLS 보안 연결
                server.login(self.email, self.password)
                server.send_message(message)

            print(f"✅ {to}에게 이메일이 성공적으로 발송되었습니다!")
            return {"status": "SUCCESS", "email": to}

        except Exception as error:
            print(f"❌ {to} 이메일 발송 중 오류가 발생했습니다: {error}")
            return {"status": "FAIL", "email": to, "error": str(error)}
