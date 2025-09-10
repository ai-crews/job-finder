import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import os
from .message_builder import load_html_template
from .stmp_service import SMTPEmailService


def send_emails(
    email_list, subject, message_text=None, html_file_path=None, attachment_path=None
):
    """대량 이메일 발송"""
    # 환경변수에서 SMTP 설정 읽기
    smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    sender_email = os.getenv("SENDER_EMAIL")
    sender_password = os.getenv("SENDER_PASSWORD")

    if not sender_email or not sender_password:
        raise ValueError("SENDER_EMAIL과 SENDER_PASSWORD 환경변수를 설정해주세요.")

    # SMTP 서비스 초기화
    email_service = SMTPEmailService(
        smtp_server, smtp_port, sender_email, sender_password
    )

    # HTML 템플릿 로드
    html_content = None
    if html_file_path:
        html_content = load_html_template(html_file_path)

    success_count = 0
    fail_count = 0
    results_map = {}  # {email: ("SUCCESS"/"FAIL", error_message)}

    for email in email_list:
        try:
            result = email_service.send_message(
                to=email,
                subject=subject,
                message_text=message_text,
                html_content=html_content,
                attachment_path=attachment_path,
            )

            if result["status"] == "SUCCESS":
                success_count += 1
                results_map[email] = ("SUCCESS", "")
            else:
                fail_count += 1
                results_map[email] = ("FAIL", result.get("error", "Unknown error"))

        except Exception as e:
            fail_count += 1
            print(f"❌ {email} 발송 실패: {e}")
            results_map[email] = ("FAIL", str(e))

    print(f"\n발송 완료! 성공: {success_count}개, 실패: {fail_count}개")
    return results_map


def send_job_posting_email(recipient_email, html_file_path="templates/email.html"):
    """채용 공고 이메일 발송"""
    return send_emails(
        email_list=[recipient_email],
        subject="채용 공고입니다!",
        message_text="채용 공고를 확인해 주세요.",
        html_file_path=html_file_path,
    )
