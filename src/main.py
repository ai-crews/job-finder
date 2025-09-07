# main.py
from services.email_sender import send_personalized_email
from services.job_matcher import get_personalized_jobs
from db.db_task import Database
from db.db_query import EmailQueries
from dotenv import load_dotenv

load_dotenv()


def main():
    print("=== 개인화된 채용공고 이메일 발송 ===")

    # DB에서 구독자 이메일 가져오기
    try:
        with Database.get_cursor() as (cursor, connection):
            cursor.execute(EmailQueries.GET_ACTIVE_SUBSCRIBERS)
            users = cursor.fetchall()

            if not users:
                print("구독 중인 사용자가 없습니다.")
                return

            print(f"발송 대상: {len(users)}명")

    except Exception as e:
        print(f"DB 조회 오류: {e}")
        return

    # 각 사용자별로 개인화된 이메일 발송
    for user in users:
        user_id, email, name = user[0], user[1], user[2]
        print(f"\n{name}({email})님 처리 중...")

        # 개인화된 채용공고 가져오기
        recommended_jobs = get_personalized_jobs(email, top_n=3)

        if recommended_jobs:
            print(f"추천 공고 {len(recommended_jobs)}개 발견")

            # 개인화된 이메일 발송
            results = send_personalized_email(email, name, recommended_jobs)

            # 발송 결과 로그 기록
            try:
                with Database.get_cursor() as (cursor, connection):
                    status = "SUCCESS" if results[email][0] == "SUCCESS" else "FAILED"
                    error_msg = results[email][1] if status == "FAILED" else None

                    cursor.execute(
                        EmailQueries.INSERT_EMAIL_LOG,
                        (
                            user_id,
                            email,
                            f"{name}님을 위한 맞춤 채용공고",
                            "PERSONALIZED",
                            status,
                            error_msg,
                            len(recommended_jobs),
                        ),
                    )
                    connection.commit()

                    if status == "SUCCESS":
                        print(f"✓ {email} 발송 성공 (로그 기록 완료)")
                    else:
                        print(f"✗ {email} 발송 실패: {error_msg}")

            except Exception as e:
                print(f"로그 기록 실패: {e}")
        else:
            print("추천할 공고가 없습니다.")


if __name__ == "__main__":
    main()
