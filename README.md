# Job Finder

> 맞춤형 취업 공고 추천 및 이메일 발송 자동화 시스템

Google 설문지를 통해 수집한 구직자 데이터를 분석하여, 각 지원자의 선호도에 맞는 채용 공고를 매칭하고 개인화된 HTML 이메일을 자동으로 발송하는 시스템입니다.

## 주요 기능

- **공고 매칭**: 4단계 필터링 시스템으로 구직자 선호도에 최적화된 공고 추천
- **개인화된 이메일**: 회사 로고, D-day 정보, 채용 형태 태그가 포함된 맞춤형 HTML 이메일
- **Google Sheets 연동**: 설문 응답 데이터 자동 수집 및 발송 결과 기록
- **Gmail API 통합**: OAuth 2.0 기반 안전한 이메일 발송
- **선호 기업 우선순위**: 지원자가 선택한 대기업 그룹 공고에 별표 표시

## 프로젝트 구조

```
job-finder/test/
├── main.py                          # 메인 실행 파일
├── requirements.txt                 # 패키지 의존성
├── .env                            # 환경 변수 설정 (보안)
├── .env_sample                     # 환경 변수 템플릿
├── credentials.json                # Google OAuth 인증 정보
│
├── data/                           # 채용 공고 데이터 (JSON)
│   ├── 쿠팡_5923444_250917_crawling.json
│   ├── 쿠팡_6753367_250917_crawling.json
│   └── ...
│
├── template/                       # 이메일 템플릿
│   └── test_email.html            # HTML 이메일 기본 템플릿
│
└── services/                       # 핵심 비즈니스 로직
    ├── matching/
    │   └── job_matcher.py         # 공고 매칭 알고리즘
    ├── email/
    │   ├── email_service.py       # 이메일 발송 인터페이스
    │   └── gmail_service.py       # Gmail API 통합
    ├── sheets/
    │   ├── sheets_auth.py         # Google Sheets OAuth 인증
    │   └── sheets_service.py      # Sheets 데이터 읽기/쓰기
    └── template/
        └── template_generator.py  # 개인화 이메일 생성
```

## 시작하기

### 사전 요구사항

- Python 3.7 이상
- Google Cloud Platform 계정
- Gmail API 및 Google Sheets API 활성화된 프로젝트

### 1. Google Cloud 설정

1. [Google Cloud Console](https://console.cloud.google.com/)에서 새 프로젝트 생성
2. **Gmail API**와 **Google Sheets API** 활성화
3. OAuth 2.0 클라이언트 ID 생성 (데스크톱 앱 유형)
4. 인증 정보를 `credentials.json`으로 다운로드하여 프로젝트 루트에 저장

### 2. 환경 설정

```bash
# 1. 저장소 클론
git clone https://github.com/your-username/job-finder.git
cd job-finder/test

# 2. 가상환경 생성 (권장)
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. 패키지 설치
pip install -r requirements.txt

# 4. 환경 변수 설정
cp .env_sample .env
```

### 3. `.env` 파일 수정

```env
SPREADSHEET_ID=your-google-sheet-id-here
WORKSHEET_NAME=설문지 응답 시트1
```

**Google Sheet ID 찾는 방법:**

- Sheets URL: `https://docs.google.com/spreadsheets/d/[SPREADSHEET_ID]/edit`
- 중간의 긴 문자열이 SPREADSHEET_ID입니다.

### 4. 실행

```bash
python main.py
```

**첫 실행 시:**

- 브라우저가 자동으로 열리며 Google 계정 로그인 요청
- Gmail 및 Google Sheets 권한 승인
- `gmail_token.pickle`과 `sheets_token.pickle` 자동 생성
- 이후 실행부터는 토큰 재사용으로 별도 인증 불필요

## 작동 원리

### 전체 프로세스

```
1. Google Sheets에서 설문 응답 데이터 로드
        ↓
2. 신입 공고를 찾는 지원자 필터링
        ↓
3. 각 지원자에 대해:
   ├─ data/ 폴더의 채용 공고와 매칭
   ├─ 개인화된 HTML 이메일 생성
   ├─ Gmail API로 이메일 발송
   └─ 발송 결과 기록
        ↓
4. Google Sheets에 발송 상태 업데이트
        ↓
5. 최종 통계 출력 (성공/실패 건수)
```

### 매칭 알고리즘 (4단계 필터링)

[JobMatcher](services/matching/job_matcher.py) 클래스가 담당:

1. **경력 필터링**: "신입" 조건에 맞는 공고만 선택
2. **고용 형태 필터링**: 희망 고용 형태(정규직, 인턴 등)에 맞춰 필터링
3. **직무 매칭**: 1순위 → 2순위 → 3순위 희망 직무와 공고 비교
4. **학력 조건 필터링**: 지원자 학력 조건 충족 여부 확인

**정렬 우선순위:**

- NULL 필드 개수 (완성도 높은 공고 우선)
- 직무 우선순위 (1순위 매칭 > 2순위 > 3순위)
- 학력 조건 정확도
- 고용 형태 매칭 점수
- 회사명 (동점 시)

**지원 직무:**

- 데이터 분석가
- 데이터 사이언티스트
- 데이터 엔지니어
- AI 엔지니어
- AI 기획자
- AI 연구원

### 이메일 생성

[EmailTemplateGenerator](services/template/template_generator.py)가 담당:

- **템플릿 기반 생성**: [test_email.html](template/test_email.html) 기본 구조 사용
- **동적 컨텐츠 삽입**: 매칭된 공고 카드를 HTML로 변환하여 삽입
- **회사 로고 표시**: 20개 이상 한국 주요 기업 로고 URL 매핑
- **D-day 계산**: 마감일까지 남은 일수 자동 계산
- **고용 형태 태그**: 색상별 뱃지 생성
  - 신입: 하늘색
  - 경력: 복숭아색
  - 정규직: 녹색
  - 인턴: 노란색
  - 계약직/전환형: 보라색
- **선호 기업 표시**: 지원자가 선택한 대기업 공고에 ⭐ 별표 추가

### Google Sheets 데이터 형식

설문 응답 시트에 필요한 컬럼:

| 컬럼명                                         | 설명        | 예시                |
| ---------------------------------------------- | ----------- | ------------------- |
| `성함`                                       | 지원자 이름 | 홍길동              |
| `이메일 주소`                                | 수신 이메일 | example@gmail.com   |
| `찾고 계신 공고의 경력 조건을 선택해주세요.` | 경력 조건   | 신입                |
| `희망 직무 1순위 (필수응답)`                 | 1순위 직무  | 데이터 분석가       |
| `희망 직무 2순위`                            | 2순위 직무  | 데이터 사이언티스트 |
| `희망 직무 3순위`                            | 3순위 직무  | AI 엔지니어         |
| `희망 고용 형태 (복수선택)`                  | 고용 형태   | 정규직, 인턴        |
| `찾고 계신 공고의 학력 조건을 선택해주세요.` | 학력 조건   | 학사 4년제          |
| 대기업 그룹 선택 컬럼들                        | 선호 기업군 | 삼성, SK, LG...     |

## 주요 파일 설명

### [main.py](main.py)

전체 워크플로우를 조율하는 메인 실행 파일입니다.

- 환경 변수 검증
- 데이터 로드 및 필터링
- 이메일 발송 및 결과 기록
- 통계 출력

### [services/matching/job_matcher.py](services/matching/job_matcher.py)

공고 매칭 로직입니다.

- `match_jobs_for_user()`: 사용자당 상위 10개 공고 추천
- 4단계 필터링 시스템
- 키워드 기반 직무명 매칭
- 선호 기업 우선순위 처리

### [services/template/template_generator.py](services/template/template_generator.py)

개인화된 HTML 이메일을 생성합니다.

- 템플릿 치환 (이름, 공고 리스트)
- 회사 로고 삽입
- D-day 계산
- 반응형 모바일 디자인

### [services/email/gmail_service.py](services/email/gmail_service.py)

Gmail API 저수준 작업을 처리합니다.

- OAuth 2.0 인증 흐름
- 토큰 캐싱 및 갱신
- MIME 메시지 생성
- 이메일 발송

### [services/sheets/sheets_service.py](services/sheets/sheets_service.py)

Google Sheets 데이터 작업을 담당합니다.

- `load_recipients_from_sheet()`: 설문 응답 데이터 로드
- `write_status_to_sheet()`: 발송 상태 및 타임스탬프 기록

## 채용 공고 데이터 형식

`data/` 폴더의 JSON 파일 구조:

```json
{
  "group_name": "쿠팡",
  "company_name": "쿠팡",
  "job_title": "[쿠팡로지스틱스서비스] 로켓설치 A/S 운영 담당자",
  "position_name": "로켓설치 A/S 운영 담당자",
  "processed_position_name": "데이터 분석가",
  "min_experience_level": "신입",
  "employment_type": "정규직",
  "min_education_level": "학사 4년제",
  "application_start_date": "2025-09-12",
  "application_deadline_date": "2025-10-15",
  "team_introduction": "팀 소개...",
  "job_duties": "담당 업무...",
  "qualifications": "자격 요건...",
  "preferred_qualifications": "우대 사항...",
  "work_location": "서울",
  "recruitment_process": "서류전형 - 전화면접 - 대면면접",
  "application_link": "https://..."
}
```

## 주요 기능 상세

### 속도 제한 (Rate Limiting)

- 10개 이메일 발송마다 2초 대기
- Gmail API 할당량 초과 방지

### 오류 처리

- 각 이메일 발송 실패 시 계속 진행
- 오류 메시지 Google Sheets에 기록 (최대 50자)
- 최종 성공/실패 통계 출력


### 수정 필요시

- 다음과 같이 확장 가능합니다:

1. **다른 기업 공고 추가**: `data/` 폴더에 동일 형식의 JSON 파일 추가
2. **새로운 직무 추가**: [job_matcher.py:37-42](services/matching/job_matcher.py#L37-L42)의 `JOB_ROLE_KEYWORDS` 딕셔너리 수정
3. **회사 로고 추가**: [template_generator.py:158-181](services/template/template_generator.py#L158-L181)의 `_load_company_logos()` 메서드에 URL 추가
4. **이메일 디자인 변경**: [test_email.html](template/test_email.html) 템플릿 수정

## 문제 해결

### `credentials.json` 오류

```
FileNotFoundError: credentials.json not found
```

→ Google Cloud Console에서 OAuth 인증 정보를 다운로드하여 프로젝트 루트에 저장하세요.

### Gmail API 할당량 초과

```
HttpError 429: Quota exceeded
```

→ `main.py`에서 대기 시간 늘리기 (`time.sleep(2)` → `time.sleep(5)`)

