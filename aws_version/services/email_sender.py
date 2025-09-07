import os
import logging
from concurrent.futures import ThreadPoolExecutor
from .smtp_client import SMTPEmailService

# 로거 설정
logger = logging.getLogger(__name__)


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
    logger.info(f"이메일 발송 시작: {len(email_list)}명 대상")

    # SMTP 설정
    smtp_server = os.getenv("SMTP_SERVER")
    smtp_port = int(os.getenv("SMTP_PORT", 587))
    sender_email = os.getenv("SENDER_EMAIL")
    sender_password = os.getenv("SENDER_PASSWORD")

    if not all([smtp_server, sender_email, sender_password]):
        logger.error(
            "SMTP 환경변수 누락: SMTP_SERVER, SENDER_EMAIL, SENDER_PASSWORD 확인 필요"
        )
        raise ValueError("SMTP 설정이 완전하지 않습니다. 환경변수를 확인하세요.")

    logger.info(f"SMTP 설정 확인 완료: {smtp_server}:{smtp_port}")

    # 이메일 서비스 인스턴스 생성
    email_service = SMTPEmailService(
        smtp_server, smtp_port, sender_email, sender_password
    )

    # HTML 파일 읽기
    html_content = None
    if html_file_path:
        if os.path.exists(html_file_path):
            try:
                with open(html_file_path, "r", encoding="utf-8") as file:
                    html_content = file.read()
                logger.info(f"HTML 템플릿 파일 로드 성공: {html_file_path}")
            except Exception as e:
                logger.error(f"HTML 템플릿 파일 읽기 실패: {html_file_path} - {e}")
                html_content = None
        else:
            logger.warning(f"HTML 템플릿 파일을 찾을 수 없음: {html_file_path}")

    # 발송 결과 저장
    results = {}

    # 단일 이메일인 경우 (개인화된 발송)
    if len(email_list) == 1:
        email = email_list[0]
        logger.info(f"개인화된 이메일 발송: {email}")

        if job_data:
            logger.info(f"추천 공고 포함: {len(job_data)}개")

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

        logger.info(f"개인화된 이메일 발송 완료: {email} - {result['status']}")
        return results

    # 여러 이메일 병렬 발송
    logger.info(f"병렬 이메일 발송 시작: {len(email_list)}명 (최대 5개 동시 처리)")

    def send_single_email(email):
        logger.debug(f"병렬 발송 처리 시작: {email}")
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
            logger.debug(f"병렬 발송 처리 완료: {email} - {result['status']}")
            return email, (result["status"], result.get("error"))
        except Exception as e:
            logger.error(f"병렬 발송 처리 실패: {email} - {e}")
            return email, ("FAIL", str(e))

    # 병렬 처리로 이메일 발송
    success_count = 0
    fail_count = 0

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(send_single_email, email) for email in email_list]

        for future in futures:
            email, result = future.result()
            results[email] = result

            if result[0] == "SUCCESS":
                success_count += 1
            else:
                fail_count += 1

    logger.info(f"병렬 이메일 발송 완료: 성공 {success_count}건, 실패 {fail_count}건")
    return results


def send_personalized_email(email, user_name, recommended_jobs):
    """개인화된 채용공고 이메일 발송"""
    logger.info(f"개인화된 채용공고 이메일 발송 요청: {user_name}({email})")

    if not recommended_jobs:
        logger.warning(f"추천 공고가 없음: {email}")

    logger.debug(
        f"발송 상세정보: 제목='{user_name}님을 위한 맞춤 채용공고', 공고수={len(recommended_jobs) if recommended_jobs else 0}"
    )

    try:
        result = send_emails(
            email_list=[email],
            subject=f"{user_name}님을 위한 맞춤 채용공고",
            message_text=f"안녕하세요 {user_name}님!\n\n맞춤형 채용공고를 확인해보세요.",
            html_file_path="templates/email_template.html",
            job_data=recommended_jobs,
            user_name=user_name,
        )

        # 결과 로깅
        if email in result:
            status, error = result[email]
            if status == "SUCCESS":
                logger.info(f"개인화된 이메일 발송 성공: {email}")
            else:
                logger.error(f"개인화된 이메일 발송 실패: {email} - {error}")

        return result

    except Exception as e:
        logger.error(f"개인화된 이메일 발송 중 오류: {email} - {e}")
        return {email: ("FAIL", str(e))}
