# services/job_matcher.py
import logging
import json
from db.db_local import Database
from db.db_query import MatchingQueries

# 로거 설정
logger = logging.getLogger(__name__)


class JobMatcher:
    def __init__(self):
        self.education_scores = {
            "D01": 1,  # 학력무관
            "D02": 2,  # 고등학교졸업
            "D03": 3,  # 대학졸업(2,3년)
            "D04": 4,  # 대학졸업(4년)
            "D05": 5,  # 석사졸업
            "D06": 6,  # 박사졸업
        }
        logger.debug("JobMatcher 초기화 완료")

    def is_preferred_company(self, user_companies, job_company):
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
        except (json.JSONDecodeError, TypeError) as e:
            logger.warning(f"희망기업 데이터 파싱 오류: {e}")
            return False


def count_nulls(job_dict):
    """채용공고의 NULL 개수 계산"""
    null_count = 0
    check_fields = ["education", "experience_level", "employment_type"]

    for field in check_fields:
        if job_dict.get(field) is None:
            null_count += 1

    return null_count


def get_job_role_priority(user_job_roles, job_role):
    """직무 우선순위 계산 (낮을수록 우선순위 높음)"""
    if user_job_roles.get("role1") == job_role:
        return 1  # 1순위 직무
    elif user_job_roles.get("role2") == job_role:
        return 2  # 2순위 직무
    elif user_job_roles.get("role3") == job_role:
        return 3  # 3순위 직무
    elif job_role is None:
        return 4  # NULL (불명확)
    else:
        return 5  # 불일치 직무


def get_education_priority(user_edu, job_edu):
    """학력 우선순위 계산 (낮을수록 우선순위 높음)"""
    if job_edu is None:
        return 2  # 확인불가(NULL)

    user_edu_list = user_edu.split(",") if user_edu else []
    if job_edu in user_edu_list:
        return 1  # 사용자가 선택한 학력
    else:
        return 3  # 불일치 학력


def get_employment_priority(user_emp_types, job_emp_type):
    """고용형태 우선순위 계산 (낮을수록 우선순위 높음)"""
    if job_emp_type is None:
        return 2  # 확인불가(NULL)

    if not user_emp_types:
        return 3  # 사용자 정보 없음

    user_emp_list = user_emp_types.split(",") if user_emp_types else []
    if job_emp_type in [emp.strip() for emp in user_emp_list]:
        return 1  # 사용자가 선택한 고용형태
    else:
        return 3  # 불일치 고용형태


def apply_basic_filters(user_prefs, job_postings):
    """1단계 필터링: 신입 공고만 추출"""
    filtered_jobs = []

    for job in job_postings:
        # 신입 공고만 추출 (경력, 확인불가(NULL) 공고 제외)
        experience_level = job.get("experience_level")
        if experience_level in ["신입", None]:  # 신입 또는 NULL만 통과
            filtered_jobs.append(job)
        else:
            logger.debug(
                f"경력 필터로 제외: {job['company_name']} - {experience_level}"
            )

    return filtered_jobs


def filter_by_employment_type(user_prefs, job_postings):
    """2단계 필터링: 고용형태"""
    filtered_jobs = []
    user_emp_types = user_prefs.get("target_emp_type", "")
    user_emp_list = user_emp_types.split(",") if user_emp_types else []

    for job in job_postings:
        employment_type = job.get("employment_type")

        # 사용자가 선택한 고용형태 또는 NULL인 경우 통과
        if employment_type is None or employment_type in [
            emp.strip() for emp in user_emp_list
        ]:
            filtered_jobs.append(job)
        else:
            logger.debug(
                f"고용형태 필터로 제외: {job['company_name']} - {employment_type}"
            )

    return filtered_jobs


def filter_by_job_role(user_prefs, job_postings):
    """3단계 필터링: 직무"""
    filtered_jobs = []
    user_roles = [
        user_prefs.get("target_job_role1"),
        user_prefs.get("target_job_role2"),
        user_prefs.get("target_job_role3"),
    ]
    user_roles = [role for role in user_roles if role]  # None 제거

    for job in job_postings:
        job_role = job.get("job_role")

        # 사용자가 선택한 직무 또는 NULL인 경우 통과
        if job_role is None or job_role in user_roles:
            filtered_jobs.append(job)
        else:
            logger.debug(f"직무 필터로 제외: {job['company_name']} - {job_role}")

    return filtered_jobs


def filter_by_education(user_prefs, job_postings):
    """4단계 필터링: 학력"""
    filtered_jobs = []
    user_edu = user_prefs.get("target_edu", "")
    user_edu_list = user_edu.split(",") if user_edu else []

    for job in job_postings:
        education = job.get("education")

        # 사용자가 선택한 학력 또는 NULL인 경우 통과
        if education is None or education in user_edu_list:
            filtered_jobs.append(job)
        else:
            logger.debug(f"학력 필터로 제외: {job['company_name']} - {education}")

    return filtered_jobs


def get_personalized_jobs(user_email, top_n=10):
    """채용공고 추천"""
    logger.info(f"채용공고 추천 시작: {user_email} (상위 {top_n}개)")
    matcher = JobMatcher()

    try:
        with Database.get_cursor() as (cursor, connection):
            logger.debug("사용자 정보 조회 시작")
            # 사용자 정보 조회
            cursor.execute(MatchingQueries.GET_USER_PREFERENCES, (user_email,))
            user_data = cursor.fetchone()

            if not user_data:
                logger.warning(f"사용자 정보를 찾을 수 없음: {user_email}")
                return []

            # 사용자 선호도 딕셔너리로 변환
            user_prefs = {
                "user_id": user_data[0],
                "email": user_data[1],
                "target_edu": user_data[2],
                "target_career": user_data[3],
                "target_emp_type": user_data[4],
                "target_job_role1": user_data[5],
                "target_job_role2": user_data[6],
                "target_job_role3": user_data[7],
                "target_companies_json": user_data[8],
            }

            logger.info(
                f"사용자 선호조건: 학력={user_prefs['target_edu']}, 경력={user_prefs['target_career']}, 고용형태={user_prefs['target_emp_type']}"
            )

            logger.debug("활성 채용공고 조회 시작")
            # 활성 채용공고 조회
            cursor.execute(MatchingQueries.GET_ACTIVE_JOB_POSTINGS)
            job_postings = cursor.fetchall()

            logger.info(f"활성 채용공고 {len(job_postings)}개 조회 완료")

            if not job_postings:
                logger.warning("활성 채용공고가 없습니다")
                return []

            # 채용공고를 딕셔너리로 변환
            job_dicts = []
            for job in job_postings:
                job_dict = {
                    "id": job[0],
                    "company_name": job[1],
                    "job_title": job[2],
                    "position_name": job[3],
                    "experience_level": job[4],
                    "education": job[5],
                    "employment_type": job[6],
                    "application_deadline_date": job[7],
                    "created_at": job[8],
                }
                job_dicts.append(job_dict)

            # 단계별 필터링
            logger.info("=== 필터링 시작 ===")

            # 1단계: 경력 필터링 (신입만)
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

            # 정렬 로직
            job_roles = {
                "role1": user_prefs["target_job_role1"],
                "role2": user_prefs["target_job_role2"],
                "role3": user_prefs["target_job_role3"],
            }

            # 희망기업은 최상단으로 먼저 분리
            preferred_jobs = []
            other_jobs = []

            for job in final_jobs:
                if matcher.is_preferred_company(
                    user_prefs["target_companies_json"], job["company_name"]
                ):
                    preferred_jobs.append(job)
                else:
                    other_jobs.append(job)

            # 각각 정렬 (NULL 개수 → 직무 → 학력 → 고용형태 → 기업명)
            def sort_key(job):
                return (
                    count_nulls(job),  # NULL 적은 순
                    get_job_role_priority(
                        job_roles, job.get("job_role")
                    ),  # 직무 일치도
                    get_education_priority(
                        user_prefs["target_edu"], job.get("education")
                    ),  # 학력 일치도
                    get_employment_priority(
                        user_prefs["target_emp_type"], job.get("employment_type")
                    ),  # 고용형태 일치도
                    job["company_name"],  # 기업명 가나다순
                )

            preferred_jobs.sort(key=sort_key)
            other_jobs.sort(key=sort_key)

            # 희망기업을 먼저 배치하고 나머지 추가
            sorted_jobs = preferred_jobs + other_jobs

            # 상위 N개 선택
            top_jobs = sorted_jobs[:top_n]

            logger.info(f"추천 완료: {len(top_jobs)}개 공고 선정")
            for i, job in enumerate(top_jobs):
                null_count = count_nulls(job)
                job_role_priority = get_job_role_priority(
                    job_roles, job.get("job_role")
                )
                edu_priority = get_education_priority(
                    user_prefs["target_edu"], job.get("education")
                )
                emp_priority = get_employment_priority(
                    user_prefs["target_emp_type"], job.get("employment_type")
                )
                is_preferred = matcher.is_preferred_company(
                    user_prefs["target_companies_json"], job["company_name"]
                )

                logger.info(
                    f"추천 {i+1}: {job['company_name']} - {job['job_title']} "
                    f"(NULL: {null_count}, 직무: {job_role_priority}, 학력: {edu_priority}, 고용: {emp_priority}, 희망기업: {is_preferred})"
                )

            # 기존 형식으로 변환하여 반환
            result_jobs = []
            for job in top_jobs:
                result_jobs.append({"job": job, "scores": {"total_score": 0}})

            return result_jobs

    except Exception as e:
        logger.error(f"매칭 서비스 오류: {user_email} - {e}")
        return []


def get_all_users_recommendations(top_n=10):
    """모든 사용자에게 맞춤형 채용공고 추천 (배치 처리용)"""
    logger.info(f"전체 사용자 추천 시작 (상위 {top_n}개씩)")

    try:
        with Database.get_cursor() as (cursor, connection):
            # 모든 활성 사용자 조회
            cursor.execute("SELECT email FROM users WHERE consent = 'Y'")
            users = cursor.fetchall()

            logger.info(f"활성 사용자 {len(users)}명 조회 완료")

            recommendations = {}
            for idx, user in enumerate(users):
                email = user[0]
                logger.info(f"사용자 {idx+1}/{len(users)} 추천 처리 중: {email}")

                user_jobs = get_personalized_jobs(email, top_n)
                recommendations[email] = user_jobs

                logger.debug(f"사용자 {email} 추천 완료: {len(user_jobs)}개 공고")

            logger.info(f"전체 사용자 추천 완료: {len(recommendations)}명")
            return recommendations

    except Exception as e:
        logger.error(f"전체 추천 서비스 오류: {e}")
        return {}
