import logging
from datetime import datetime
from services.email_batch_service import EmailBatchService
from config.logging_config import setup_logging
from dotenv import load_dotenv

load_dotenv()
logger = setup_logging()


def main():
    """메인 실행 함수"""
    logger.info("=== 개인화된 채용공고 이메일 발송 시작 ===")

    batch_service = EmailBatchService()
    results = batch_service.send_personalized_emails()

    # 결과 로깅
    logger.info("=== 이메일 발송 완료 ===")
    logger.info(f"총 사용자: {results['total_users']}명")
    logger.info(f"발송 성공: {results['success_count']}건")
    logger.info(f"발송 실패: {results['fail_count']}건")
    logger.info(f"성공률: {results['success_rate']:.1f}%")


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
