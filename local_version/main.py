# main.py
import logging
import os
from datetime import datetime
from services.email_service import SMTPEmailService
from services.job_matcher import get_personalized_jobs
from db.db_local import Database
from db.db_query.email_query import EmailQueries
from dotenv import load_dotenv

# 로거 설정
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("email_sending.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

load_dotenv()


def get_email_service():
    """이메일 서비스 인스턴스 생성"""
    smtp_server = os.getenv("SMTP_SERVER")
    smtp_port = int(os.getenv("SMTP_PORT", 587))
    email = os.getenv("EMAIL_ADDRESS")
    password = os.getenv("EMAIL_PASSWORD")

    return SMTPEmailService(smtp_server, smtp_port, email, password)


def load_email_template():
    """이메일 HTML 템플릿 로드"""
    template_path = "templates/email_template.html"  # 템플릿 파일 경로
    try:
        with open(template_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        logger.error(f"템플릿 파일을 찾을 수 없음: {template_path}")
        return None
    except Exception as e:
        logger.error(f"템플릿 로드 오류: {e}")
        return None


def process_single_user(user_id, email, name, email_service, html_template):
    """단일 사용자 처리"""
    logger.info(f"처리 시작: {name}({email})")

    try:
        # 개인화된 채용공고 가져오기
        recommended_jobs = get_personalized_jobs(email, top_n=10)

        if not recommended_jobs:
            logger.warning(f"추천할 공고가 없음: {email}")
            return log_email_result(
                user_id, email, name, "FAILED", "추천할 공고가 없습니다", 0
            )

        logger.info(f"추천 공고 {len(recommended_jobs)}개 발견: {email}")

        # 개인화된 이메일 발송
        subject = f"{name}님을 위한 맞춤 채용공고"
        result = email_service.send_message(
            to=email,
            subject=subject,
            html_content=html_template,
            job_data=recommended_jobs,
            user_name=name,
        )

        # 발송 결과 처리
        if result["status"] == "SUCCESS":
            return log_email_result(
                user_id, email, name, "SUCCESS", None, len(recommended_jobs)
            )
        else:
            return log_email_result(
                user_id,
                email,
                name,
                "FAILED",
                result.get("error", "알 수 없는 오류"),
                len(recommended_jobs),
            )

    except Exception as e:
        logger.error(f"사용자 처리 중 오류: {email} - {e}")
        return log_email_result(user_id, email, name, "FAILED", str(e), 0)


def log_email_result(user_id, email, name, status, error_msg, job_count):
    """이메일 발송 결과 로깅"""
    try:
        with Database.get_cursor() as (cursor, connection):
            cursor.execute(
                EmailQueries.INSERT_EMAIL_LOG,
                (
                    user_id,
                    email,
                    (
                        f"{name}님을 위한 맞춤 채용공고"
                        if status == "SUCCESS"
                        else "발송 실패"
                    ),
                    "PERSONALIZED",
                    status,
                    error_msg if status == "FAILED" else None,
                    job_count,
                ),
            )
            connection.commit()

            if status == "SUCCESS":
                logger.info(f"발송 성공: {email}")
                return True
            else:
                logger.error(f"발송 실패: {email} - {error_msg}")
                return False

    except Exception as log_error:
        logger.error(f"로그 기록 실패: {email} - {log_error}")
        return False


def get_active_subscribers():
    """활성 구독자 목록 가져오기"""
    try:
        with Database.get_cursor() as (cursor, connection):
            cursor.execute(EmailQueries.GET_ACTIVE_SUBSCRIBERS)
            users = cursor.fetchall()
            return users
    except Exception as e:
        logger.error(f"구독자 조회 오류: {e}")
        return []


def main():
    """메인 실행 함수"""
    logger.info("=== 개인화된 채용공고 이메일 발송 시작 ===")

    # 이메일 서비스 초기화
    email_service = get_email_service()
    if not email_service:
        logger.error("이메일 서비스 초기화 실패")
        return

    # HTML 템플릿 로드
    html_template = load_email_template()
    if not html_template:
        logger.error("HTML 템플릿 로드 실패")
        return

    # 구독자 목록 가져오기
    users = get_active_subscribers()

    if not users:
        logger.warning("구독 중인 사용자가 없습니다.")
        return

    total_users = len(users)
    logger.info(f"발송 대상: {total_users}명")

    # 각 사용자 처리
    success_count = 0
    fail_count = 0

    for i, user in enumerate(users, 1):
        user_id, email, name = user[0], user[1], user[2]
        logger.info(f"[{i}/{total_users}] 처리 중: {email}")

        if process_single_user(user_id, email, name, email_service, html_template):
            success_count += 1
        else:
            fail_count += 1

    # 최종 결과
    logger.info("=== 이메일 발송 완료 ===")
    logger.info(f"총 사용자: {total_users}명")
    logger.info(f"발송 성공: {success_count}건")
    logger.info(f"발송 실패: {fail_count}건")
    logger.info(
        f"성공률: {(success_count/total_users*100):.1f}%"
        if total_users > 0
        else "성공률: 0%"
    )


if __name__ == "__main__":
    start_time = datetime.now()
    logger.info(f"프로그램 시작 시간: {start_time}")

    try:
        main()
    except Exception as e:
        logger.critical(f"프로그램 실행 중 치명적 오류: {e}")
    finally:
        end_time = datetime.now()
        execution_time = end_time - start_time
        logger.info(f"프로그램 종료 시간: {end_time}")
        logger.info(f"총 실행 시간: {execution_time}")
