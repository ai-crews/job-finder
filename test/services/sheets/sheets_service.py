import gspread
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import pickle
import os
from datetime import datetime

# Google Sheets + Drive API 스코프
SHEETS_SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


def authenticate_sheets_oauth():
    """Google Sheets OAuth 인증 (Gmail과 동일한 credentials.json 사용)"""
    creds = None
    token_file = "sheets_token.pickle"

    print("🔐 Google Sheets OAuth 인증 중...")

    # 기존 토큰이 있으면 로드
    if os.path.exists(token_file):
        try:
            with open(token_file, "rb") as token:
                creds = pickle.load(token)
            print("📁 기존 Sheets 토큰 발견")
        except Exception as e:
            print(f"⚠️ 기존 토큰 로드 실패: {e}")
            creds = None

    # 유효한 자격 증명이 없으면 로그인 플로우 실행
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("🔄 Sheets 토큰 갱신 중...")
            try:
                creds.refresh(Request())
                print("✅ Sheets 토큰 갱신 성공")
            except Exception as e:
                print(f"❌ 토큰 갱신 실패: {e}")
                creds = None

        if not creds:
            if not os.path.exists("credentials.json"):
                raise FileNotFoundError(
                    "credentials.json 파일이 필요합니다.\n"
                    "Gmail API와 동일한 OAuth 클라이언트를 사용합니다."
                )

            print("🌐 브라우저에서 Google Sheets 권한 승인...")
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json", SHEETS_SCOPES
            )
            creds = flow.run_local_server(
                port=0, prompt="select_account", access_type="offline"
            )
            print("✅ Google Sheets 권한 승인 완료")

        # 토큰 저장
        try:
            with open(token_file, "wb") as token:
                pickle.dump(creds, token)
            print(f"✅ Sheets 토큰이 {token_file}에 저장되었습니다")
        except Exception as e:
            print(f"⚠️ 토큰 저장 실패: {e}")

    return gspread.authorize(creds)


def load_recipients_from_sheet(spreadsheet_id, worksheet_name):
    """OAuth를 사용한 Google Sheets 데이터 로드"""
    try:
        gc = authenticate_sheets_oauth()
        print("✅ Google Sheets 인증 성공")

        # 스프레드시트 열기
        try:
            sh = gc.open_by_key(spreadsheet_id)
            print(f"📊 스프레드시트 열기 성공: {sh.title}")
        except Exception as e:
            print(f"❌ 스프레드시트 열기 실패: {e}")
            print(f"SPREADSHEET_ID 확인: {spreadsheet_id}")
            return [], None, None

        # 워크시트 선택
        try:
            ws = sh.worksheet(worksheet_name)
            print(f"📄 워크시트 선택 성공: {worksheet_name}")
        except Exception as e:
            print(f"❌ 워크시트 선택 실패: {e}")
            print(f"사용 가능한 워크시트: {[ws.title for ws in sh.worksheets()]}")
            return [], sh, None

        # 데이터 가져오기
        records = ws.get_all_records()
        print(f"총 행 수: {len(records)}")

        if not records:
            print("시트에 데이터가 없습니다.")
            return [], sh, ws
        # 이메일 컬럼 찾기
        email_col = "이메일 주소"

        print(f"✅ '{email_col}' 컬럼에서 이메일 추출 중...")

        # 이메일 주소 추출 및 유효성 검사
        email_list = []
        for i, record in enumerate(records, 2):
            email = record.get(email_col, "").strip()
            if email and "@" in email and "." in email:
                print(f"행 {i}: {email}")
                email_list.append(email)
            elif email:
                print(f"행 {i}: {email} (유효하지 않은 이메일 형식)")

        return email_list, sh, ws

    except Exception as e:
        print(f"❌ Google Sheets 로드 실패: {e}")
        return [], None, None


def write_status_to_sheet(ws, records, results):
    """시트에 발송 결과 기록"""
    try:
        if not ws or not records or not results:
            print("⚠️ 결과 기록을 위한 데이터가 부족합니다.")
            return

        print("📝 시트에 발송 결과 기록 중...")

        # 현재 헤더 가져오기
        headers = ws.row_values(1)
        status_col = len(headers) + 1
        time_col = len(headers) + 2

        # 헤더에 상태 컬럼 추가 (없으면)
        if "발송상태" not in headers:
            ws.update_cell(1, status_col, "발송상태")
            ws.update_cell(1, time_col, "발송시간")
            print("✅ 헤더에 상태 컬럼 추가됨")
        else:
            # 기존 상태 컬럼 위치 찾기
            status_col = headers.index("발송상태") + 1
            if "발송시간" in headers:
                time_col = headers.index("발송시간") + 1

        # 각 행에 결과 기록
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        updated_count = 0

        # 이메일 컬럼 찾기
        email_columns = ["이메일 주소", "email", "Email", "EMAIL", "이메일"]
        email_col_name = None

        for col in email_columns:
            if col in records[0]:
                email_col_name = col
                break

        if not email_col_name:
            print("❌ 이메일 컬럼을 찾을 수 없어 결과 기록을 건너뜁니다.")
            return

        for i, record in enumerate(records, 2):
            email = record.get(email_col_name, "").strip()
            if email in results:
                status, error = results[email]

                # 상태 업데이트
                ws.update_cell(i, status_col, status)

                # 시간 및 오류 메시지 업데이트
                if status == "SUCCESS":
                    ws.update_cell(i, time_col, current_time)
                else:
                    error_msg = f"{current_time} - 실패: {error[:50]}"  # 50자 제한
                    ws.update_cell(i, time_col, error_msg)

                updated_count += 1
                print(f"  행 {i}: {email} → {status}")

        print(f"✅ {updated_count}개 행의 발송 결과가 기록되었습니다")

    except Exception as e:
        print(f"❌ 시트 결과 기록 실패: {e}")
