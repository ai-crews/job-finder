# queries.py
class EmailQueries:
    # 사용자 조회
    GET_USER_BY_EMAIL = """
        SELECT 사용자_id, 사용자_이름 
        FROM users 
        WHERE 사용자_이메일 = %s
    """

    # 구독 중인 모든 사용자 조회
    GET_ACTIVE_SUBSCRIBERS = """
        SELECT 사용자_id, 사용자_이메일, 사용자_이름 
        FROM users 
        WHERE 사용자_구독해지일시 IS NULL
    """

    # 이메일 발송 로그 삽입
    INSERT_EMAIL_LOG = """
        INSERT INTO email_send_logs 
        (이력_id, 사용자_id, 사용자_이메일, 공고_id, 발송일시) 
        VALUES (%s, %s, %s, %s, %s)
    """

    # 최근 이메일 발송 로그 조회
    GET_RECENT_EMAIL_LOGS = """
        SELECT 사용자_이메일, 공고_id, 발송일시 
        FROM email_send_logs 
        ORDER BY 발송일시 DESC 
        LIMIT %s
    """
