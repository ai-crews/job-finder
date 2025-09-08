# local_version/db/db_query/email_query.py
class EmailQueries:
    # 구독 중인 모든 사용자 조회
    GET_ACTIVE_SUBSCRIBERS = """
        SELECT user_id, email, name 
        FROM users 
        WHERE consent = 'Y'
    """

    # 이메일 발송 로그 삽입
    INSERT_EMAIL_LOG = """
        INSERT INTO email_send_logs 
        (user_id, user_email, email_subject, email_type, status, error_message, recommended_jobs_count) 
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """
