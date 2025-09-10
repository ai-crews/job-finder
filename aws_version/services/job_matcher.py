# services/job_matcher.py
import logging
import json
from db.db_aws import Database
from db.db_query import MatchingQueries

logger = logging.getLogger(__name__)


def is_preferred_company(user_companies, job_company):
    """희망기업 여부 확인"""
    if not user_companies or not job_company:
        return False

    try:
        company_list = (
            json.loads(user_companies)
            if isinstance(user_companies, str)
            else user_companies
        )
        return job_company in company_list
    except (json.JSONDecodeError, TypeError):
        return False


def count_nulls(job_dict):
    """채용공고의 NULL 개수 계산"""
    check_fields = ["education", "experience_level", "employment_type"]
    return sum(1 for field in check_fields if job_dict.get(field) is None)


def get_job_role_priority(user_job_roles, job_role):
    """직무 우선순위 계산 (낮을수록 우선순위 높음)"""
    if job_role is None:
        return 4

    for i, role_key in enumerate(["role1", "role2", "role3"], 1):
        if user_job_roles.get(role_key) == job_role:
            return i
    return 5


def get_priority(user_values, job_value):
    """공통 우선순위 계산 함수"""
    if job_value is None:
        return 2
    if not user_values:
        return 3

    user_list = [v.strip() for v in user_values.split(",")]
    return 1 if job_value in user_list else 3


def apply_basic_filters(user_prefs, job_postings):
    """1단계 필터링: 신입 공고만 추출"""
    filtered_jobs = []

    for job in job_postings:
        experience_level = job.get("experience_level")
        if experience_level in ["신입", None]:
            filtered_jobs.append(job)

    return filtered_jobs


def filter_by_employment_type(user_prefs, job_postings):
    """2단계 필터링: 고용형태"""
    filtered_jobs = []
    target_emp_type = user_prefs.get("target_emp_type") or ""
    user_emp_list = [emp.strip() for emp in target_emp_type.split(",") if emp.strip()]

    for job in job_postings:
        employment_type = job.get("employment_type")

        if (
            employment_type is None
            or not user_emp_list
            or employment_type in user_emp_list
        ):
            filtered_jobs.append(job)

    return filtered_jobs


def filter_by_job_role(user_prefs, job_postings):
    """3단계 필터링: 직무"""
    filtered_jobs = []
    user_roles = [
        user_prefs.get("target_job_role1"),
        user_prefs.get("target_job_role2"),
        user_prefs.get("target_job_role3"),
    ]
    user_roles = [role for role in user_roles if role]

    for job in job_postings:
        job_role = job.get("job_role")

        if job_role is None or not user_roles or job_role in user_roles:
            filtered_jobs.append(job)

    return filtered_jobs


def filter_by_education(user_prefs, job_postings):
    """4단계 필터링: 학력"""
    filtered_jobs = []
    target_edu = user_prefs.get("target_edu") or ""
    user_edu_list = [edu.strip() for edu in target_edu.split(",") if edu.strip()]

    for job in job_postings:
        education = job.get("education")

        if education is None or not user_edu_list or education in user_edu_list:
            filtered_jobs.append(job)

    return filtered_jobs


def get_personalized_jobs(user_email, top_n=10):
    """채용공고 추천"""
    logger.info(f"채용공고 추천 시작: {user_email}")

    try:
        with Database.get_cursor() as (cursor, connection):
            # 사용자 정보 조회
            cursor.execute(MatchingQueries.GET_USER_PREFERENCES, (user_email,))
            user_data = cursor.fetchone()

            if not user_data:
                logger.warning(f"사용자 정보를 찾을 수 없음: {user_email}")
                return []

            # 사용자 선호도
            user_prefs = {
                "target_edu": user_data[2],
                "target_emp_type": user_data[4],
                "target_job_role1": user_data[5],
                "target_job_role2": user_data[6],
                "target_job_role3": user_data[7],
                "target_companies_json": user_data[8],
            }

            # 활성 채용공고 조회
            cursor.execute(MatchingQueries.GET_ACTIVE_JOB_POSTINGS)
            job_postings = cursor.fetchall()

            if not job_postings:
                logger.warning("활성 채용공고가 없습니다")
                return []

            # 채용공고를 딕셔너리로 변환
            job_dicts = [
                {
                    "id": job[0],
                    "company_name": job[1],
                    "job_title": job[2],
                    "position_name": job[3],
                    "experience_level": job[4],
                    "education": job[5],
                    "employment_type": job[6],
                    "application_deadline_date": job[7],
                    "created_at": job[8],
                    "job_role": job[9] if len(job) > 9 else None,
                }
                for job in job_postings
            ]

            # 단계별 필터링 (플로우차트 방식)
            logger.info("=== 필터링 시작 ===")

            # 1단계: 경력 필터링
            step1_jobs = apply_basic_filters(user_prefs, job_dicts)
            logger.info(f"1단계(경력) 후: {len(step1_jobs)}개 공고")

            # 2단계: 고용형태 필터링
            step2_jobs = filter_by_employment_type(user_prefs, step1_jobs)
            logger.info(f"2단계(고용형태) 후: {len(step2_jobs)}개 공고")

            # 3단계: 직무 필터링
            step3_jobs = filter_by_job_role(user_prefs, step2_jobs)
            logger.info(f"3단계(직무) 후: {len(step3_jobs)}개 공고")

            # 4단계: 학력 필터링
            final_jobs = filter_by_education(user_prefs, step3_jobs)
            logger.info(f"4단계(학력) 후: {len(final_jobs)}개 공고")

            if not final_jobs:
                logger.warning("필터링 후 추천할 공고가 없습니다")
                return []

            # 희망기업 분리
            preferred_jobs = []
            other_jobs = []

            for job in final_jobs:
                if is_preferred_company(
                    user_prefs["target_companies_json"], job["company_name"]
                ):
                    preferred_jobs.append(job)
                else:
                    other_jobs.append(job)

            # 정렬 키 함수
            job_roles = {
                "role1": user_prefs["target_job_role1"],
                "role2": user_prefs["target_job_role2"],
                "role3": user_prefs["target_job_role3"],
            }

            def sort_key(job):
                return (
                    count_nulls(job),
                    get_job_role_priority(job_roles, job.get("job_role")),
                    get_priority(user_prefs["target_edu"], job.get("education")),
                    get_priority(
                        user_prefs["target_emp_type"], job.get("employment_type")
                    ),
                    job["company_name"],
                )

            # 정렬 및 결합
            preferred_jobs.sort(key=sort_key)
            other_jobs.sort(key=sort_key)
            top_jobs = (preferred_jobs + other_jobs)[:top_n]

            logger.info(f"추천 완료: {len(top_jobs)}개 공고 선정")

            # 결과 반환
            return [
                {
                    "job": job,
                    "scores": {
                        "company_bonus": (
                            1
                            if is_preferred_company(
                                user_prefs["target_companies_json"], job["company_name"]
                            )
                            else 0
                        )
                    },
                }
                for job in top_jobs
            ]

    except Exception as e:
        logger.error(f"매칭 서비스 오류: {user_email} - {e}")
        return []
