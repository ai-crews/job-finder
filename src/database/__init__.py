# database/connection.py
import pymysql
from dotenv import load_dotenv
import os
from contextlib import contextmanager

load_dotenv()


class Database:
    @staticmethod
    def get_connection():
        return pymysql.connect(
            host=os.getenv("DB_HOST"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            port=3306,
            database=os.getenv("DB_NAME"),
            charset="utf8mb4",
        )

    @staticmethod
    @contextmanager
    def get_cursor():
        connection = Database.get_connection()
        try:
            cursor = connection.cursor()
            yield cursor, connection
        except Exception as e:
            connection.rollback()
            raise e
        finally:
            connection.close()
