# services/matching_service.py
from db.db_task import Database
from db.db_query import MatchingQueries
import json


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

    def calculate_education_score(self, user_edu, job_edu):
        """학력 매칭 점수 계산 (25점 만점)"""
        if job_edu is None:
            return 15  # 학력무관

        user_edu_list = user_edu.split(",") if user_edu else []

        # 학력무관 희망하는 경우
        if "D01" in user_edu_list:
            return 25

        # 정확히 일치하는 경우
        if job_edu in user_edu_list:
            return 25

        # 상위 학력 보유한 경우
        user_max_edu = max(
            [self.education_scores.get(edu.strip(), 0) for edu in user_edu_list],
            default=0,
        )
        job_edu_score = self.education_scores.get(job_edu, 0)

        if user_max_edu > job_edu_score:
            return 20

        return 5  # 기본 점수

    def calculate_career_score(self, user_career, job_career):
        """경력 매칭 점수 계산 (20점 만점)"""
        if job_career is None:
            return 10  # 경력무관

        if user_career == job_career:
            return 20

        return 5  # 기본 점수

    def calculate_employment_type_score(self, user_emp_types, job_emp_type):
        """고용형태 매칭 점수 계산 (15점 만점)"""
        if job_emp_type is None:
            return 10  # 고용형태무관

        if not user_emp_types:
            return 5

        user_emp_list = user_emp_types.split(",") if user_emp_types else []

        if job_emp_type in [emp.strip() for emp in user_emp_list]:
            return 15

        return 5  # 기본 점수

    def calculate_job_role_score(self, user_job_roles, job_role):
        """직무 매칭 점수 계산 (30점 만점)"""
        if job_role is None:
            return 10  # 직무무관

        # 1순위, 2순위, 3순위 직무 확인
        if user_job_roles.get("role1") == job_role:
            return 30
        elif user_job_roles.get("role2") == job_role:
            return 20
        elif user_job_roles.get("role3") == job_role:
            return 10

        return 5  # 기본 점수

    def calculate_company_bonus(self, user_companies, job_company):
        """희망기업 보너스 점수 계산 (10점 만점)"""
        if not user_companies or not job_company:
            return 0

        try:
            company_list = (
                json.loads(user_companies)
                if isinstance(user_companies, str)
                else user_companies
            )
            if job_company in company_list:
                return 10
        except (json.JSONDecodeError, TypeError):
            pass

        return 0

    def calculate_matching_score(self, user_prefs, job_posting):
        """전체 매칭 점수 계산"""
        # 각 요소별 점수 계산
        edu_score = self.calculate_education_score(
            user_prefs["target_edu"], job_posting["education"]
        )
        career_score = self.calculate_career_score(
            user_prefs["target_career"], job_posting["experience_level"]
        )
        emp_score = self.calculate_employment_type_score(
            user_prefs["target_emp_type"], job_posting["employment_type"]
        )

        job_roles = {
            "role1": user_prefs["target_job_role1"],
            "role2": user_prefs["target_job_role2"],
            "role3": user_prefs["target_job_role3"],
        }
        role_score = self.calculate_job_role_score(
            job_roles, job_posting.get("job_role")
        )

        company_bonus = self.calculate_company_bonus(
            user_prefs["target_companies_json"], job_posting["company_name"]
        )

        total_score = edu_score + career_score + emp_score + role_score + company_bonus

        return {
            "total_score": total_score,
            "education_score": edu_score,
            "career_score": career_score,
            "employment_score": emp_score,
            "job_role_score": role_score,
            "company_bonus": company_bonus,
        }


def get_personalized_jobs(user_email, top_n=5):
    """사용자에게 맞춤형 채용공고 추천"""
    matcher = JobMatcher()

    try:
        with Database.get_cursor() as (cursor, connection):
            # 사용자 정보 조회
            cursor.execute(MatchingQueries.GET_USER_PREFERENCES, (user_email,))
            user_data = cursor.fetchone()

            if not user_data:
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

            # 활성 채용공고 조회
            cursor.execute(MatchingQueries.GET_ACTIVE_JOB_POSTINGS)
            job_postings = cursor.fetchall()

            # 각 채용공고별 매칭 점수 계산
            scored_jobs = []
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

                scores = matcher.calculate_matching_score(user_prefs, job_dict)

                scored_jobs.append({"job": job_dict, "scores": scores})

            # 점수 순으로 정렬하고 상위 N개 반환
            scored_jobs.sort(key=lambda x: x["scores"]["total_score"], reverse=True)

            return scored_jobs[:top_n]

    except Exception as e:
        print(f"매칭 오류: {e}")
        return []


def get_all_users_recommendations(top_n=10):
    """모든 사용자에게 맞춤형 채용공고 추천 (배치 처리용)"""
    try:
        with Database.get_cursor() as (cursor, connection):
            # 모든 활성 사용자 조회
            cursor.execute("SELECT email FROM users WHERE consent = 'Y'")
            users = cursor.fetchall()

            recommendations = {}
            for user in users:
                email = user[0]
                user_jobs = get_personalized_jobs(email, top_n)
                recommendations[email] = user_jobs

            return recommendations

    except Exception as e:
        print(f"전체 추천 오류: {e}")
        return {}
