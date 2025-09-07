# services/email_service.py
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import smtplib
import os
import logging
from services.email_template import EmailTemplate

logger = logging.getLogger(__name__)


class SMTPEmailService:
    def __init__(self, smtp_server, smtp_port, email, password):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.email = email
        self.password = password
        self.template = EmailTemplate()

    @classmethod
    def from_config(cls):
        """설정에서 이메일 서비스 인스턴스 생성"""
        from config.email_config import EmailConfig

        return cls(
            EmailConfig.SMTP_SERVER,
            EmailConfig.SMTP_PORT,
            EmailConfig.EMAIL_ADDRESS,
            EmailConfig.EMAIL_PASSWORD,
        )

    def create_message(
        self,
        to,
        subject,
        message_text=None,
        html_content=None,
        attachment_path=None,
        job_data=None,
        user_name=None,
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

        # HTML 본문 추가 (job_data가 있으면 템플릿에 삽입)
        if html_content:
            if job_data:
                html_content = self.template.insert_job_data(
                    html_content, job_data, user_name or ""
                )
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
        self,
        to,
        subject,
        message_text=None,
        html_content=None,
        attachment_path=None,
        job_data=None,
        user_name=None,
    ):
        """단일 이메일 발송"""
        logger.info(f"이메일 발송: {to}")

        try:
            message = self.create_message(
                to,
                subject,
                message_text,
                html_content,
                attachment_path,
                job_data,
                user_name,
            )

            # SMTP 서버 연결 및 발송
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.email, self.password)
                server.send_message(message)

            logger.info(f"✅ 발송 성공: {to}")
            return {"status": "SUCCESS", "email": to}

        except smtplib.SMTPAuthenticationError as error:
            logger.error(f"인증 실패: {to} - {error}")
            return {"status": "FAIL", "email": to, "error": f"인증 실패: {str(error)}"}

        except smtplib.SMTPRecipientsRefused as error:
            logger.error(f"수신자 오류: {to} - {error}")
            return {
                "status": "FAIL",
                "email": to,
                "error": f"수신자 주소 오류: {str(error)}",
            }

        except Exception as error:
            logger.error(f"❌ 발송 실패: {to} - {error}")
            return {"status": "FAIL", "email": to, "error": str(error)}
