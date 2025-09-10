# main.py
from services.email.email_service import send_emails
from services.sheets.sheets_service import (
    load_recipients_from_sheet,
    write_status_to_sheet,
)
from dotenv import load_dotenv
import os

load_dotenv()


def get_template_by_domain(email):
    """이메일 도메인에 따라 템플릿 파일을 반환"""
    domain = email.split("@")[1].lower()
    if domain == "naver.com":
        return "template/test_naver.html"
    else:
        return "template/test_email.html"


def send_emails_by_domain(email_list, subject, message_text):
    """도메인별로 그룹화하여 이메일 발송"""
    # 도메인별로 이메일 그룹화
    naver_emails = []
    other_emails = []

    for email in email_list:
        domain = email.split("@")[1].lower()
        if domain == "naver.com":
            naver_emails.append(email)
        else:
            other_emails.append(email)

    all_results = {}

    # 네이버 이메일 발송
    if naver_emails:
        print(f"네이버 이메일 발송: {len(naver_emails)}명")
        naver_results = send_emails(
            email_list=naver_emails,
            subject=subject,
            message_text=message_text,
            html_file_path="template/test_naver.html",
        )
        all_results.update(naver_results)

    # 기타 이메일 발송
    if other_emails:
        print(f"기타 이메일 발송: {len(other_emails)}명")
        other_results = send_emails(
            email_list=other_emails,
            subject=subject,
            message_text=message_text,
            html_file_path="template/test_email.html",
        )
        all_results.update(other_results)

    return all_results


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

    # 도메인별 분류 확인
    naver_count = sum(
        1 for email in email_list if email.split("@")[1].lower() == "naver.com"
    )
    other_count = len(email_list) - naver_count
    print(f"  - 네이버: {naver_count}명")
    print(f"  - 기타: {other_count}명")

    # 도메인별 발송
    results = send_emails_by_domain(
        email_list=email_list,
        subject="📩 [JOB FINDER] 이번주 맞춤 채용공고 도착!",
        message_text="안녕하세요!\n\n이것은 테스트 이메일입니다.",
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
