import os
import pymysql
import logging
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class Database:
    @staticmethod
    def get_connection():
        """Lambda 환경변수를 사용한 DB 연결"""
        try:
            connection = pymysql.connect(
                host=os.getenv("DB_HOST"),
                user=os.getenv("DB_USER"),
                password=os.getenv("DB_PASSWORD"),
                database=os.getenv("DB_NAME"),
                charset="utf8mb4",
                autocommit=False,
            )
            logger.debug("DB 연결 성공")
            return connection
        except Exception as e:
            logger.error(f"DB 연결 실패: {e}")
            raise

    @staticmethod
    @contextmanager
    def get_cursor():
        """커서와 연결 객체를 context manager로 반환"""
        connection = None
        cursor = None
        try:
            connection = Database.get_connection()
            cursor = connection.cursor()
            yield cursor, connection
        except Exception as e:
            if connection:
                connection.rollback()
            logger.error(f"DB 작업 중 오류: {e}")
            raise
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()
            logger.debug("DB 연결 종료")
