import logging
from db.db_local import Database
from db.db_query.email_query import EmailQueries

logger = logging.getLogger(__name__)


class EmailLogger:
    """이메일 발송 로그 관리"""

    @staticmethod
    def log_result(
        user_id: int, email: str, name: str, status: str, error_msg: str, job_count: int
    ) -> bool:
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
