import gspread
from google.oauth2.credentials import Credentials
import pickle
import os
from dotenv import load_dotenv

load_dotenv()


def check_sheets_columns(spreadsheet_id, worksheet_name):
    """Google Sheets의 모든 컬럼과 샘플 데이터를 확인"""

    # 기존 인증 사용
    gc = authenticate_sheets_oauth()

    try:
        # 스프레드시트 열기
        sh = gc.open_by_key(spreadsheet_id)
        ws = sh.worksheet(worksheet_name)

        # 헤더 행 가져오기
        headers = ws.row_values(1)

        print("=" * 80)
        print(f"Google Sheets 컬럼 분석 ({worksheet_name})")
        print("=" * 80)

        print(f"\n전체 컬럼 수: {len(headers)}")
        print("\n모든 컬럼명:")
        for i, header in enumerate(headers, 1):
            print(f"  {i:2d}. '{header}'")

        # 직무 관련 컬럼만 필터링
        job_columns = []
        for i, header in enumerate(headers, 1):
            if "직무" in header or "순위" in header:
                job_columns.append((i, header))

        print(f"\n직무 관련 컬럼 ({len(job_columns)}개):")
        for col_num, header in job_columns:
            print(f"  {col_num:2d}. '{header}'")

        # 첫 번째 데이터 행 가져오기 (샘플)
        if len(ws.get_all_records()) > 0:
            sample_record = ws.get_all_records()[0]

            print(f"\n샘플 데이터 (첫 번째 응답자):")
            for col_num, header in job_columns:
                value = sample_record.get(header, "N/A")
                print(f"  '{header}': '{value}' (길이: {len(str(value))})")

        # 특정 사용자 찾기 (선택사항)
        email_to_find = input(
            "\n특정 사용자 이메일을 확인하시겠습니까? (엔터로 건너뛰기): "
        ).strip()

        if email_to_find:
            records = ws.get_all_records()
            found_user = None

            for record in records:
                if record.get("이메일 주소", "") == email_to_find:
                    found_user = record
                    break

            if found_user:
                print(f"\n{email_to_find} 사용자의 직무 데이터:")
                for col_num, header in job_columns:
                    value = found_user.get(header, "N/A")
                    print(f"  '{header}': '{value}'")
            else:
                print(f"\n{email_to_find} 사용자를 찾을 수 없습니다.")

        return headers, job_columns

    except Exception as e:
        print(f"오류 발생: {e}")
        return None, None


def authenticate_sheets_oauth():
    """Google Sheets OAuth 인증"""
    creds = None
    token_file = "sheets_token.pickle"

    SHEETS_SCOPES = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]

    print("Google Sheets 인증 중...")

    # 기존 토큰이 있으면 로드
    if os.path.exists(token_file):
        try:
            with open(token_file, "rb") as token:
                creds = pickle.load(token)
            print("기존 토큰 로드됨")
        except Exception as e:
            print(f"토큰 로드 실패: {e}")
            creds = None

    # 유효한 자격 증명이 없으면 새로 인증
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("토큰 갱신 중...")
            try:
                from google.auth.transport.requests import Request

                creds.refresh(Request())
                print("토큰 갱신 완료")
            except Exception as e:
                print(f"토큰 갱신 실패: {e}")
                creds = None

        if not creds:
            if not os.path.exists("credentials.json"):
                raise FileNotFoundError("credentials.json 파일이 필요합니다.")

            print("브라우저에서 Google 권한 승인 중...")
            from google_auth_oauthlib.flow import InstalledAppFlow

            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json", SHEETS_SCOPES
            )
            creds = flow.run_local_server(port=0)
            print("권한 승인 완료")

        # 토큰 저장
        try:
            with open(token_file, "wb") as token:
                pickle.dump(creds, token)
            print("토큰 저장 완료")
        except Exception as e:
            print(f"토큰 저장 실패: {e}")

    return gspread.authorize(creds)


# 사용 예시
if __name__ == "__main__":
    # 여기에 실제 스프레드시트 ID와 워크시트 이름을 입력하세요
    SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")
    WORKSHEET_NAME = os.getenv("WORKSHEET_NAME", "설문지 응답 시트1")

    if SPREADSHEET_ID:
        headers, job_columns = check_sheets_columns(SPREADSHEET_ID, WORKSHEET_NAME)

        if headers and job_columns:
            print(f"\n컬럼 확인 완료!")
            print(f"코드에서 사용할 정확한 컬럼명들:")
            for col_num, header in job_columns:
                print(f'  user_data.get("{header}", "")')
    else:
        print("스프레드시트 ID가 필요합니다.")
