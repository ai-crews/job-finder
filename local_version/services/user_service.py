import logging
from typing import List, Tuple
from db.db_local import Database
from db.db_query.email_query import EmailQueries

logger = logging.getLogger(__name__)


class UserService:
    """사용자 관련 서비스"""

    @staticmethod
    def get_active_subscribers() -> List[Tuple]:
        """활성 구독자 목록 가져오기"""
        try:
            with Database.get_cursor() as (cursor, connection):
                cursor.execute(EmailQueries.GET_ACTIVE_SUBSCRIBERS)
                users = cursor.fetchall()
                return users
        except Exception as e:
            logger.error(f"구독자 조회 오류: {e}")
            return []
