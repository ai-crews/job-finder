import pymysql
from dotenv import load_dotenv
import os

load_dotenv()

connection = pymysql.connect(
    host=os.getenv("DB_HOST"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    port=3306,
)

cursor = connection.cursor()
# 현재 데이터베이스 목록 확인
cursor.execute("SHOW DATABASES;")
databases = cursor.fetchall()
print("사용 가능한 데이터베이스:", databases)

connection.close()
