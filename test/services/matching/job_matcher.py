import json
import os
from typing import List, Dict, Any
from datetime import datetime, timedelta


class JobMatcher:
    def __init__(self, data_folder_path: str):
        self.data_folder = data_folder_path
        self.job_data = self._load_all_job_data()
        self.company_name_mapping = self._build_company_mapping()
        print(f"총 {len(self.job_data)}개의 채용공고를 로드했습니다.")

    def _build_company_mapping(self) -> Dict[str, List[str]]:
        """실제 파일의 company_name과 사용자 선택 회사명 간의 매핑 구축"""
        mapping = {
            # 토스 그룹 (실제 데이터에서 나올 수 있는 company_name들)
            "토스": ["토스"],
            "토스뱅크": ["토스뱅크"], 
            "토스페이먼츠": ["토스페이먼츠"],
            "토스증권": ["토스증권"],
            
            # 한화 그룹 (실제 데이터 기준)
            "한화에어로스페이스": ["한화에어로스페이스"],
            "한화시스템/방산": ["한화시스템/방산", "한화시스템", "한화시스템/ICT"],  # ICT도 추가
            "한화솔루션/케미칼": ["한화솔루션/케미칼", "한화솔루션", "한화케미칼"],
            "한화솔루션/큐셀": ["한화솔루션/큐셀", "한화솔루션", "한화큐셀"],
            "한화생명": ["한화생명"],
            "한화손해보험": ["한화손해보험"],
            
            # 삼성 그룹 (실제 데이터에서 나올 수 있는 형태들)
            "삼성전자 DX부문": ["삼성전자 DX부문", "삼성전자", "삼성전자/DX", "삼성전자DX"],
            "삼성전자 DS부문": ["삼성전자 DS부문", "삼성전자", "삼성전자/DS", "삼성전자DS"],
            "삼성SDI": ["삼성SDI"],
            "삼성전기": ["삼성전기"],
            "삼성SDS": ["삼성SDS"],
            "삼성바이오로직스": ["삼성바이오로직스"],
            "삼성생명": ["삼성생명"],
            "삼성화재": ["삼성화재"],
            "삼성중공업": ["삼성중공업"],
            "삼성E&A": ["삼성E&A"],
            "삼성물산 건설부문": ["삼성물산 건설부문", "삼성물산", "삼성건설", "삼성물산/건설"],
            "삼성물산 상사부문": ["삼성물산 상사부문", "삼성물산", "삼성상사", "삼성물산/상사"],
            "삼성물산 리조트부문": ["삼성물산 리조트부문", "삼성물산", "삼성리조트", "삼성물산/리조트"],
            "삼성물산 패션부문": ["삼성물산 패션부문", "삼성물산", "삼성패션", "삼성물산/패션"],
            "호텔신라": ["호텔신라"],
            "제일기획": ["제일기획"],
            "에스원": ["에스원"],
            
            # SK 그룹
            "SK 텔레콤": ["SK 텔레콤", "SK텔레콤", "SKT"],
            "SK 하이닉스": ["SK 하이닉스", "SK하이닉스"],
            "SK 이노베이션": ["SK 이노베이션", "SK이노베이션"],
            "SK 바이오팜": ["SK 바이오팜", "SK바이오팜"],
            "SK 실트론": ["SK 실트론", "SK실트론"],
            "SKC": ["SKC"],
            "SK 스퀘어": ["SK 스퀘어", "SK스퀘어"],
            "SK 주식회사": ["SK 주식회사", "SK주식회사", "SK"],
            
            # LG 그룹
            "LG이노텍": ["LG이노텍"],
            "LG화학": ["LG화학"],
            "LG생활건강": ["LG생활건강"],
            "LG에너지솔루션": ["LG에너지솔루션"],
            "LG유플러스": ["LG유플러스", "LG U+"],
            "LG AI연구원": ["LG AI연구원"],
            "LG CNS": ["LG CNS"],
            
            # 네이버 그룹
            "NAVER": ["NAVER", "네이버"],
            "NAVER Cloud": ["NAVER Cloud", "네이버클라우드"],
            "NAVER WEBTOON": ["NAVER WEBTOON", "네이버웹툰"],
            "NAVER FINANCIAL": ["NAVER FINANCIAL", "네이버파이낸셜"],
            "NAVERWORKS": ["NAVERWORKS", "네이버웍스"],
            
            # 카카오 그룹
            "카카오": ["카카오"],
            "카카오뱅크": ["카카오뱅크"],
            "카카오페이": ["카카오페이"],
            "카카오모빌리티": ["카카오모빌리티"],
        }
        
        return mapping

    def _load_all_job_data(self) -> List[Dict]:
        """모든 채용공고 JSON 파일 로드"""
        job_data = []
        
        # 폴더 구조를 고려한 재귀적 탐색
        for root, dirs, files in os.walk(self.data_folder):
            for filename in files:
                if filename.endswith(".json"):
                    file_path = os.path.join(root, filename)
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            data = json.load(f)
                            
                            # 파일명에서 회사명 추출하여 추가 (백업용)
                            if "company_name" not in data or not data["company_name"]:
                                company_from_filename = self._extract_company_from_filename(filename)
                                if company_from_filename:
                                    data["company_name_from_file"] = company_from_filename
                            
                            job_data.append(data)
                    except Exception as e:
                        print(f"파일 로드 실패 {filename}: {e}")
        
        return job_data

    def _extract_company_from_filename(self, filename: str) -> str:
        """파일명에서 회사명 추출"""
        # 파일명 패턴: 회사명_숫자ID_날짜_crawling.json
        parts = filename.replace('.json', '').split('_')
        if len(parts) >= 2:
            return parts[0]  # 첫 번째 부분이 회사명
        return ""

    def is_preferred_company(self, target_companies: List[str], job_company: str) -> bool:
        """희망기업 여부 확인 - 개선된 매칭"""
        if not target_companies or not job_company:
            return False
        
        # 1. 직접 매칭 (정확한 이름)
        if job_company in target_companies:
            return True
        
        # 2. 매핑 테이블을 통한 매칭
        for target_company in target_companies:
            mapped_names = self.company_name_mapping.get(target_company, [])
            
            # mapped_names가 리스트가 아닌 경우 리스트로 변환
            if isinstance(mapped_names, str):
                mapped_names = [mapped_names]
            
            # 각 매핑된 이름과 비교
            for mapped_name in mapped_names:
                if mapped_name == job_company:  # 정확한 매칭 우선
                    return True
                    
            # 부분 매칭 (포함 관계)
            for mapped_name in mapped_names:
                if (mapped_name.lower() in job_company.lower() or 
                    job_company.lower() in mapped_name.lower()):
                    return True
        
        # 3. 기본 부분 문자열 매칭 (대소문자 무시, 공백 제거)
        job_company_clean = job_company.lower().replace(" ", "").replace("/", "")
        for target_company in target_companies:
            target_clean = target_company.lower().replace(" ", "").replace("/", "")
            
            # 양방향 포함 관계 확인
            if (target_clean in job_company_clean or 
                job_company_clean in target_clean):
                return True
                
            # 슬래시 기준으로 분리해서 매칭 (예: "한화시스템/ICT"에서 "한화시스템" 추출)
            if "/" in job_company:
                company_base = job_company.split("/")[0].lower().replace(" ", "")
                if target_clean in company_base or company_base in target_clean:
                    return True
        
        return False

    def count_nulls(self, job_dict: Dict) -> int:
        """채용공고의 NULL 개수 계산"""
        check_fields = [
            "min_education_level",
            "min_experience_level", 
            "employment_type",
        ]
        return sum(
            1
            for field in check_fields
            if not job_dict.get(field) or job_dict.get(field) == "확인불가"
        )

    def get_job_role_priority(self, target_jobs: List[str], job: Dict) -> int:
        """직무 우선순위 계산 (낮을수록 우선순위 높음)"""
        for i, target_job in enumerate(target_jobs, 1):
            if target_job and self._is_job_match(job, target_job):
                return i
        return 5

    def get_priority(self, user_values: List[str], job_value: str) -> int:
        """공통 우선순위 계산 함수"""
        if not job_value or job_value == "확인불가":
            return 2
        if not user_values:
            return 3
        return 1 if job_value in user_values else 3

    def apply_basic_filters(self, user_data: Dict, job_postings: List[Dict]) -> List[Dict]:
        """1단계 필터링: 신입 공고만 추출"""
        filtered_jobs = []
        career_preference = user_data.get(
            "찾고 계신 공고의 경력 조건을 선택해주세요.", ""
        )

        for job in job_postings:
            experience_level = job.get("min_experience_level", "")
            if "신입" in career_preference:
                if experience_level in ["신입", "확인불가", ""]:
                    filtered_jobs.append(job)
            else:
                filtered_jobs.append(job)  # 신입이 아닌 경우 모든 공고 포함

        return filtered_jobs

    def filter_by_employment_type(self, user_data: Dict, job_postings: List[Dict]) -> List[Dict]:
        """2단계 필터링: 고용형태"""
        filtered_jobs = []
        target_employment_types = self._parse_employment_types(
            user_data.get("희망 고용 형태 (복수선택)", "")
        )

        for job in job_postings:
            employment_type = job.get("employment_type", "")

            if (
                not employment_type
                or employment_type == "확인불가"
                or not target_employment_types
                or employment_type in target_employment_types
            ):
                filtered_jobs.append(job)

        return filtered_jobs

    def filter_by_job_role(self, user_data: Dict, job_postings: List[Dict]) -> List[Dict]:
        """3단계 필터링: 직무"""
        filtered_jobs = []
        target_jobs = [
            user_data.get("희망 직무 1순위 (필수응답)", ""),
            user_data.get("희망 직무 2순위", ""),
            user_data.get("희망 직무 3순위", ""),
        ]
        target_jobs = [job for job in target_jobs if job]

        for job in job_postings:
            if not target_jobs or self._is_job_match(job, target_jobs):
                filtered_jobs.append(job)

        return filtered_jobs

    def _is_education_match(self, user_edu_list, job_education):
        for user_edu in user_edu_list:
            # 직접 매칭
            if user_edu in job_education:
                return True

            # 4년제 대학 매칭
            if ("학사" in user_edu and "4년" in user_edu) and (
                "대학" in job_education and "4년" in job_education
            ):
                return True

        return False

    def filter_by_education(self, user_data: Dict, job_postings: List[Dict]) -> List[Dict]:
        filtered_jobs = []
        user_education = user_data.get(
            "찾고 계신 공고의 학력 조건을 선택해주세요. (졸업예정자도 선택 가능, 복수선택)",
            "",
        )
        user_edu_list = [
            edu.strip() for edu in user_education.split(",") if edu.strip()
        ]

        for job in job_postings:
            education = job.get("min_education_level", "")

            if (
                not education
                or education == "학력_확인불가"
                or not user_edu_list
                or self._is_education_match(user_edu_list, education)
            ):
                filtered_jobs.append(job)

        return filtered_jobs

    def match_jobs_for_user(self, user_data: Dict, top_n: int = 10) -> List[Dict]:
        """사용자에게 맞는 채용공고 매칭 (단계별 필터링 방식)"""
        print("=== 필터링 시작 ===")

        # 사용자 선호도 추출
        target_companies = self._extract_target_companies(user_data)
        target_jobs = [
            user_data.get("희망 직무 1순위 (필수응답)", ""),
            user_data.get("희망 직무 2순위", ""),
            user_data.get("희망 직무 3순위", ""),
        ]
        target_employment_types = self._parse_employment_types(
            user_data.get("희망 고용 형태 (복수선택)", "")
        )

        print(f"사용자 희망 직무: {target_jobs}")
        print(f"사용자 희망 회사: {target_companies}")
        print(f"사용자 희망 고용형태: {target_employment_types}")

        # 실제 로드된 회사명들 확인 (디버깅용)
        actual_companies = list(set([job.get("company_name", "") for job in self.job_data if job.get("company_name")]))
        print(f"실제 데이터의 회사명들: {actual_companies[:10]}...")  # 처음 10개만 출력

        # 단계별 필터링
        # 1단계: 경력 필터링
        step1_jobs = self.apply_basic_filters(user_data, self.job_data)
        print(f"1단계(경력) 후: {len(step1_jobs)}개 공고")

        # 2단계: 고용형태 필터링
        step2_jobs = self.filter_by_employment_type(user_data, step1_jobs)
        print(f"2단계(고용형태) 후: {len(step2_jobs)}개 공고")

        # 3단계: 직무 필터링
        step3_jobs = self.filter_by_job_role(user_data, step2_jobs)
        print(f"3단계(직무) 후: {len(step3_jobs)}개 공고")

        # 4단계: 학력 필터링
        final_jobs = self.filter_by_education(user_data, step3_jobs)
        print(f"4단계(학력) 후: {len(final_jobs)}개 공고")

        if not final_jobs:
            print("필터링 후 추천할 공고가 없습니다")
            return []

        # 희망기업 분리
        preferred_jobs = []
        other_jobs = []

        for job in final_jobs:
            company_name = job.get("company_name", "") or job.get("company_name_from_file", "")
            if self.is_preferred_company(target_companies, company_name):
                preferred_jobs.append(job)
                print(f"희망기업 매칭: {company_name}")
            else:
                other_jobs.append(job)

        print(f"희망기업 공고: {len(preferred_jobs)}개, 기타 공고: {len(other_jobs)}개")

        # 정렬 키 함수
        def sort_key(job):
            user_education = user_data.get(
                "찾고 계신 공고의 학력 조건을 선택해주세요. (졸업예정자도 선택 가능, 복수선택)",
                "",
            )
            user_edu_list = [
                edu.strip() for edu in user_education.split(",") if edu.strip()
            ]

            return (
                self.count_nulls(job),
                self.get_job_role_priority(target_jobs, job),
                self.get_priority(user_edu_list, job.get("min_education_level", "")),
                self.get_priority(target_employment_types, job.get("employment_type", "")),
                job.get("company_name", ""),
            )

        # 정렬 및 결합
        preferred_jobs.sort(key=sort_key)
        other_jobs.sort(key=sort_key)
        top_jobs = (preferred_jobs + other_jobs)[:top_n]

        print(f"추천 완료: {len(top_jobs)}개 공고 선정")

        # 결과 반환
        return [
            {
                "job": job,
                "is_preferred_company": self.is_preferred_company(
                    target_companies, job.get("company_name", "") or job.get("company_name_from_file", "")
                ),
                "score": 100,  # 기본 점수
            }
            for job in top_jobs
        ]

    def _parse_employment_types(self, employment_str: str) -> List[str]:
        """고용형태 문자열 파싱"""
        if not employment_str:
            return []
        return [emp.strip() for emp in employment_str.split(",") if emp.strip()]

    def _extract_target_companies(self, user_data: Dict) -> List[str]:
        """사용자가 관심있는 회사들 추출"""
        companies = []

        # 각 그룹별 회사 매핑
        company_mappings = {
            "삼성": {
                "key": "삼성 그룹에서 관심 있는 회사를 선택해주세요.",
                "companies": [
                    "삼성전자 DX부문",
                    "삼성전자 DS부문",
                    "삼성SDI",
                    "삼성전기",
                    "삼성SDS",
                    "삼성바이오로직스",
                    "삼성생명",
                    "삼성화재",
                    "삼성중공업",
                    "삼성E&A",
                    "삼성물산 건설부문",
                    "삼성물산 상사부문",
                    "삼성물산 리조트부문",
                    "삼성물산 패션부문",
                    "호텔신라",
                    "제일기획",
                    "에스원",
                ],
            },
            "SK": {
                "key": "SK 그룹에서 관심 있는 회사를 선택해주세요.",
                "companies": [
                    "SK 텔레콤",
                    "SK 하이닉스",
                    "SK 이노베이션",
                    "SK 바이오팜",
                    "SK 실트론",
                    "SKC",
                    "SK 스퀘어",
                    "SK 주식회사",
                ],
            },
            "현대자동차": {
                "key": "현대자동차 그룹에서 관심 있는 회사를 선택해주세요.",
                "companies": ["기아", "현대모비스"],
            },
            "LG": {
                "key": "LG 그룹에서 관심 있는 회사를 선택해주세요.",
                "companies": [
                    "LG이노텍",
                    "LG화학",
                    "LG생활건강",
                    "LG에너지솔루션",
                    "LG유플러스",
                    "LG AI연구원",
                    "LG CNS",
                ],
            },
            "롯데": {
                "key": "롯데 그룹에서 관심 있는 회사를 선택해주세요.",
                "companies": [
                    "롯데칠성음료",
                    "롯데백화점",
                    "롯데마트 • 롯데슈퍼",
                    "롯데하이마트",
                    "롯데홈쇼핑",
                    "롯데면세점",
                    "롯데호텔",
                    "롯데월드",
                    "롯데글로벌로지스",
                    "대흥기획",
                    "롯데물산",
                    "롯데이노베이트",
                    "롯데렌탈",
                    "롯데케미칼",
                    "롯데건설",
                    "롯데에너지머티리얼즈",
                ],
            },
            "한화": {
                "key": "한화 그룹에서 관심 있는 회사를 선택해주세요.",
                "companies": [
                    "한화에어로스페이스",
                    "한화시스템/방산",
                    "한화솔루션/케미칼",
                    "한화솔루션/큐셀",
                    "한화생명",
                    "한화손해보험",
                ],
            },
            "CJ": {
                "key": "CJ 그룹에서 관심 있는 회사를 선택해주세요.",
                "companies": [
                    "CJ제일제당",
                    "CJ프레시웨이",
                    "CJ ENM",
                    "CJ CGV",
                    "CJ대한통운",
                    "CJ올리브네트웍스",
                    "CJ올리브영",
                    "TVING",
                ],
            },
            "카카오": {
                "key": "카카오 그룹에서 관심 있는 회사를 선택해주세요.",
                "companies": ["카카오", "카카오뱅크", "카카오페이", "카카오모빌리티"],
            },
            "쿠팡": {
                "key": "쿠팡 그룹에서 관심 있는 회사를 선택해주세요.",
                "companies": ["쿠팡"],
            },
            "네이버": {
                "key": "NAVER 그룹에서 관심 있는 회사를 선택해주세요.",
                "companies": [
                    "NAVER",
                    "NAVER Cloud",
                    "NAVER WEBTOON",
                    "NAVER FINANCIAL",
                    "NAVERWORKS",
                ],
            },
            "신한금융": {
                "key": "신한금융그룹에서 관심 있는 회사를 선택해주세요.",
                "companies": ["신한은행", "신한카드", "신한투자증권", "신한생명"],
            },
            "KB금융": {
                "key": "KB금융그룹에서 관심 있는 회사를 선택해주세요.",
                "companies": ["KB국민은행", "KB국민카드", "KB증권", "KB손해보험"],
            },
            "하나금융": {
                "key": "하나금융그룹에서 관심 있는 회사를 선택해주세요.",
                "companies": ["하나은행", "하나카드", "하나증권", "하나손해보험"],
            },
            "우리금융": {
                "key": "우리금융그룹에서 관심 있는 회사를 선택해주세요.",
                "companies": ["우리은행", "우리카드", "우리증권"],
            },
            "토스": {
                "key": "토스그룹에서 관심 있는 회사를 선택해주세요.",
                "companies": ["토스", "토스뱅크", "토스페이먼츠", "토스증권"],
            },
            "우아한형제들": {
                "key": "우아한형제들 그룹에서 관심 있는 회사를 선택해주세요.",
                "companies": ["우아한형제들"],
            },
        }

        # 각 그룹에서 선택된 회사들 확인
        for group_name, group_info in company_mappings.items():
            group_selection = user_data.get(group_info["key"], "")
            if group_selection and group_selection.strip():

                # "NAVER 전체", "토스 전체", "삼성 전체" 등의 패턴 확인
                if "전체" in group_selection:
                    companies.extend(group_info["companies"])
                    print(f"'{group_name} 전체' 선택됨 → {len(group_info['companies'])}개 회사 추가")
                else:
                    # 구체적인 회사명들 파싱
                    selected = [c.strip() for c in group_selection.split(",") if c.strip()]
                    companies.extend(selected)
                    print(f"'{group_name}' 개별 선택 → {selected}")

        return list(set(companies))  # 중복 제거

    def _is_job_match(self, job: Dict, target_jobs: List[str]) -> bool:
        """직무 매칭 여부 판단 - processed_position_name 우선 사용"""
        if not target_jobs:
            return True

        # processed_position_name 우선 확인
        processed_position = job.get("processed_position_name", "")
        position_name = job.get("position_name", "")
        job_title = job.get("job_title", "")

        for target_job in target_jobs:
            if not target_job:
                continue

            # 1. processed_position_name으로 매칭 (정확도 높음)
            if processed_position and processed_position != "미분류":
                if self._simple_match(processed_position, target_job):
                    return True

            # 2. position_name으로 키워드 매칭
            if self._keyword_match(position_name, target_job):
                return True

            # 3. job_title로 키워드 매칭
            if self._keyword_match(job_title, target_job):
                return True

        return False

    def _simple_match(self, job_field: str, target_job: str) -> bool:
        """단순 문자열 매칭"""
        if not job_field or not target_job:
            return False
        return target_job.lower().replace(" ", "") in job_field.lower().replace(" ", "")

    def _keyword_match(self, job_field: str, target_job: str) -> bool:
        """키워드 기반 매칭"""
        if not job_field or not target_job:
            return False

        # 키워드 매핑
        job_keywords = {
            "Data Analyst": ["데이터", "분석", "analyst", "data", "데이터분석"],
            "Data Scientist": ["데이터", "사이언티스트", "scientist", "data", "데이터과학"],
            "AI 엔지니어": ["AI", "인공지능", "머신러닝", "ML", "딥러닝", "artificial intelligence"],
            "AI 기획자": ["AI", "인공지능", "기획", "전략", "AI기획"],
            "AI 연구원": ["AI", "인공지능", "연구", "research", "AI연구"],
            "Data Engineer": ["데이터", "엔지니어", "engineer", "data", "데이터엔지니어"],
        }

        keywords = job_keywords.get(target_job, [target_job.lower()])
        job_field_lower = job_field.lower()

        return any(keyword.lower() in job_field_lower for keyword in keywords)

    def debug_company_matching(self, user_data: Dict) -> None:
        """회사 매칭 디버깅을 위한 헬퍼 메서드"""
        target_companies = self._extract_target_companies(user_data)
        print(f"\n=== 회사 매칭 디버깅 ===")
        print(f"사용자 선택 회사: {target_companies}")
        
        # 실제 데이터의 회사명들
        actual_companies = list(set([
            job.get("company_name", "") or job.get("company_name_from_file", "") 
            for job in self.job_data 
            if job.get("company_name") or job.get("company_name_from_file")
        ]))
        
        print(f"실제 데이터 회사명 ({len(actual_companies)}개):")
        for company in sorted(actual_companies):
            print(f"  - {company}")
        
        # 매칭 결과
        print(f"\n매칭 결과:")
        for job in self.job_data[:5]:  # 처음 5개만 확인
            company_name = job.get("company_name", "") or job.get("company_name_from_file", "")
            is_match = self.is_preferred_company(target_companies, company_name)
            print(f"  {company_name} → {'매칭' if is_match else '미매칭'}")