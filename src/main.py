# main.py
from services.email_service import send_emails
from database import Database
from queries.email_queries import EmailQueries
from dotenv import load_dotenv
from datetime import datetime
import uuid

load_dotenv()


def main():
    print("=== SMTP 이메일 발송 (데이터베이스 연동) ===")

    # DB에서 구독자 이메일 가져오기
    try:
        with Database.get_cursor() as (cursor, connection):
            cursor.execute(
                EmailQueries.GET_ACTIVE_SUBSCRIBERS
            )  # 수정: 구독중인 사용자 조회
            users = cursor.fetchall()

            if not users:
                print("구독 중인 사용자가 없습니다.")
                return

            email_list = [user[1] for user in users]  # 이메일만 추출
            print(f"발송 대상: {len(email_list)}명")

    except Exception as e:
        print(f"DB 조회 오류: {e}")
        return

    # 이메일 발송
    html_file = "templates/email_final.html"
    results = send_emails(
        email_list=email_list,
        subject="새로운 채용 공고입니다!",
        message_text="안녕하세요!\n\n새로운 채용 공고를 확인해보세요.",
        html_file_path=html_file,
    )

    # 발송 결과를 DB에 로그 기록
    try:
        with Database.get_cursor() as (cursor, connection):
            for user in users:
                user_id, user_email = user[0], user[1]

                if user_email in results:
                    status, error = results[user_email]

                    # 성공한 경우만 로그 기록
                    if status == "SUCCESS":
                        log_id = str(uuid.uuid4())[:64]
                        cursor.execute(
                            EmailQueries.INSERT_EMAIL_LOG,
                            (
                                log_id,
                                user_id,
                                user_email,
                                "JOB_2024_001",
                                datetime.now(),
                            ),
                        )

            connection.commit()
            print("발송 결과를 DB에 기록했습니다.")

    except Exception as e:
        print(f"DB 로그 기록 오류: {e}")


if __name__ == "__main__":
    main()
