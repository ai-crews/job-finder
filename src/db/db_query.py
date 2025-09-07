# db_query.py
class EmailQueries:
    # 사용자 조회
    GET_USER_BY_EMAIL = """
        SELECT user_id, name 
        FROM users 
        WHERE email = %s
    """

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

    # 최근 이메일 발송 로그 조회
    GET_RECENT_EMAIL_LOGS = """
        SELECT user_email, email_subject, status, sent_at, recommended_jobs_count
        FROM email_send_logs 
        ORDER BY sent_at DESC 
        LIMIT %s
    """


class MatchingQueries:
    # 사용자 정보 + 희망조건 조회
    GET_USER_PREFERENCES = """
        SELECT u.user_id, u.email, u.target_edu, u.target_career, 
               u.target_emp_type, u.target_job_role1, u.target_job_role2, u.target_job_role3,
               utc.target_companies_json
        FROM users u
        LEFT JOIN user_target_companies utc ON u.user_id = utc.user_id
        WHERE u.email = %s
    """

    # 활성 채용공고 조회
    GET_ACTIVE_JOB_POSTINGS = """
        SELECT id, company_name, job_title, position_name, experience_level, education, 
               employment_type, application_deadline_date, created_at
        FROM job_postings 
        WHERE application_deadline_date >= CURDATE()
        ORDER BY created_at DESC
    """
