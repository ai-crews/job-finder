# main.py
from email_service import send_emails
from sheets_service import load_recipients_from_sheet, write_status_to_sheet
from dotenv import load_dotenv
import os

load_dotenv()


def main():
    print("=== SMTP 이메일 발송 테스트 (Google Sheets 연동) ===")

    # 구글 시트 정보
    SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")
    WORKSHEET_NAME = os.getenv("WORKSHEET_NAME", "설문지 응답 시트1")

    # 시트에서 수신자 읽기
    email_list, sh, ws = load_recipients_from_sheet(SPREADSHEET_ID, WORKSHEET_NAME)
    if not email_list:
        print("시트에서 이메일을 찾지 못했습니다. 'email' 컬럼을 확인하세요.")
        return

    print(f"발송 대상: {len(email_list)}명")

    # 발송
    html_file = "test_email.html"
    results = send_emails(
        email_list=email_list,
        subject="📩 [JOB FINDER] 이번 주 맞춤 채용공고 도착!",
        message_text="안녕하세요!\n\n이것은 테스트 이메일입니다.",
        html_file_path=html_file,
    )

    # 시트에 결과 기록
    try:
        if ws is not None:
            records = ws.get_all_records()
            write_status_to_sheet(ws, records, results)
            print("시트에 발송 결과를 기록했습니다.")
    except Exception as e:
        print(f"시트 결과 기록 중 오류: {e}")


if __name__ == "__main__":
    main()
