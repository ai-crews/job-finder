import os
from concurrent.futures import ThreadPoolExecutor
from .smtp_client import SMTPEmailService


def send_emails(
    email_list,
    subject,
    message_text=None,
    html_file_path=None,
    attachment_path=None,
    job_data=None,
    user_name=None,
):
    """이메일 일괄 발송 함수"""

    # SMTP 설정
    smtp_server = os.getenv("SMTP_SERVER")
    smtp_port = int(os.getenv("SMTP_PORT", 587))
    sender_email = os.getenv("SENDER_EMAIL")
    sender_password = os.getenv("SENDER_PASSWORD")

    if not all([smtp_server, sender_email, sender_password]):
        raise ValueError("SMTP 설정이 완전하지 않습니다. 환경변수를 확인하세요.")

    # 이메일 서비스 인스턴스 생성
    email_service = SMTPEmailService(
        smtp_server, smtp_port, sender_email, sender_password
    )

    # HTML 파일 읽기
    html_content = None
    if html_file_path and os.path.exists(html_file_path):
        with open(html_file_path, "r", encoding="utf-8") as file:
            html_content = file.read()

    # 발송 결과 저장
    results = {}

    # 단일 이메일인 경우 (개인화된 발송)
    if len(email_list) == 1:
        email = email_list[0]
        result = email_service.send_message(
            to=email,
            subject=subject,
            message_text=message_text,
            html_content=html_content,
            attachment_path=attachment_path,
            job_data=job_data,
            user_name=user_name,
        )
        results[email] = (result["status"], result.get("error"))
        return results

    # 여러 이메일 병렬 발송
    def send_single_email(email):
        try:
            result = email_service.send_message(
                to=email,
                subject=subject,
                message_text=message_text,
                html_content=html_content,
                attachment_path=attachment_path,
                job_data=job_data,
                user_name=user_name,
            )
            return email, (result["status"], result.get("error"))
        except Exception as e:
            return email, ("FAIL", str(e))

    # 병렬 처리로 이메일 발송
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(send_single_email, email) for email in email_list]

        for future in futures:
            email, result = future.result()
            results[email] = result

    return results


def send_personalized_email(email, user_name, recommended_jobs):
    """개인화된 채용공고 이메일 발송"""
    return send_emails(
        email_list=[email],
        subject=f"{user_name}님을 위한 맞춤 채용공고",
        message_text=f"안녕하세요 {user_name}님!\n\n맞춤형 채용공고를 확인해보세요.",
        html_file_path="templates/email_template.html",
        job_data=recommended_jobs,
        user_name=user_name,
    )
