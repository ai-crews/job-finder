from services.matching.job_matcher import JobMatcher
from services.template.template_generator import EmailTemplateGenerator
from services.email.email_service import send_emails_with_gmail_api
from services.sheets.sheets_service import (
    load_recipients_from_sheet,
    write_status_to_sheet,
)
from dotenv import load_dotenv
import os
import tempfile
import time

load_dotenv()


def main():

    # 환경변수 확인
    SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")
    WORKSHEET_NAME = os.getenv("WORKSHEET_NAME", "설문지 응답 시트1")
    DATA_FOLDER = "data"
    TEMPLATE_PATH = "template/test_email.html"

    if not SPREADSHEET_ID:
        print("❌ .env 파일에 SPREADSHEET_ID를 설정해주세요.")
        return

    if not os.path.exists(DATA_FOLDER):
        print(f"❌ 데이터 폴더를 찾을 수 없습니다: {DATA_FOLDER}")
        return

    if not os.path.exists(TEMPLATE_PATH):
        print(f"❌ 템플릿 파일을 찾을 수 없습니다: {TEMPLATE_PATH}")
        return

    # 1. 구글 시트에서 사용자 데이터 로드
    print("🔍 Google Sheets에서 사용자 데이터 로드 중...")
    email_list, sh, ws = load_recipients_from_sheet(SPREADSHEET_ID, WORKSHEET_NAME)

    if not ws:
        print("❌ 워크시트 로드 실패")
        return

    # 전체 사용자 데이터 가져오기
    all_records = ws.get_all_records()
    print(f"📋 총 {len(all_records)}명의 사용자 데이터 로드 완료\n")

    # 신입 공고 희망자만 필터링
    target_records = []
    for record in all_records:
        career_preference = record.get("찾고 계신 공고의 경력 조건을 선택해주세요.", "")
        user_email = record.get("이메일 주소", "").strip()

        if "신입" in career_preference and user_email and "@" in user_email:
            target_records.append(record)

    print(f"🎯 신입 공고 희망자: {len(target_records)}명")

    if not target_records:
        print("❌ 발송 대상자가 없습니다.")
        return

    # 2. 매칭 시스템 초기화
    print("🔄 채용공고 매칭 시스템 초기화 중...")
    try:
        job_matcher = JobMatcher(DATA_FOLDER)
        template_generator = EmailTemplateGenerator(TEMPLATE_PATH)
        print("✅ 매칭 시스템 초기화 완료\n")
    except Exception as e:
        print(f"❌ 매칭 시스템 초기화 실패: {e}")
        return

    print("\n🚀 개인화된 이메일 발송 시작...\n")

    # 4. 각 사용자별 개인화된 이메일 발송
    results = {}
    success_count = 0
    fail_count = 0

    for i, record in enumerate(target_records, 1):
        user_email = record.get("이메일 주소", "").strip()
        user_name = record.get("성함 ", "미확인").strip()

        print(f"[{i}/{len(target_records)}] 👤 {user_name} ({user_email}) 처리 중...")

        try:
            # 사용자 맞춤 채용공고 매칭
            matched_jobs = job_matcher.match_jobs_for_user(record)

            if not matched_jobs:
                print(f"   ❌ 매칭되는 채용공고가 없습니다.")
                results[user_email] = ("FAIL", "매칭되는 채용공고 없음")
                fail_count += 1
                continue

            print(f"   ✅ {len(matched_jobs)}개 채용공고 매칭됨")

            # 매칭된 공고 정보 출력
            preferred_companies = [
                job["job"]["company_name"]
                for job in matched_jobs
                if job["is_preferred_company"]
            ]
            if preferred_companies:
                print(f"   ⭐ 희망기업: {', '.join(preferred_companies[:3])}")

            # 개인화된 이메일 템플릿 생성
            personalized_html = template_generator.generate_personalized_email(
                record, matched_jobs
            )

            # 임시 파일에 저장
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".html", delete=False, encoding="utf-8"
            ) as temp_file:
                temp_file.write(personalized_html)
                temp_file_path = temp_file.name

            # 이메일 발송
            result = send_emails_with_gmail_api(
                email_list=[user_email],
                subject=f"📩 [JOB FINDER] {user_name}님 맞춤 채용공고 도착!",
                html_file_path=temp_file_path,
            )

            # 임시 파일 삭제
            os.unlink(temp_file_path)

            # 결과 저장
            if user_email in result:
                status, error = result[user_email]
                results[user_email] = (status, error)
                if status == "SUCCESS":
                    success_count += 1
                    print(f"📤 이메일 발송 성공!")
                else:
                    fail_count += 1
                    print(f"이메일 발송 실패: {error}")

            # API 제한을 피하기 위한 잠시 대기
            if i % 10 == 0:  # 10명마다 잠시 대기
                print(f"   ⏸️  잠시 대기 중... (API 제한 방지)")
                time.sleep(2)

        except Exception as e:
            print(f"처리 실패: {e}")
            results[user_email] = ("FAIL", str(e))
            fail_count += 1

        print()  # 빈 줄 추가

    # 5. 결과를 시트에 기록
    print("📝 발송 결과를 시트에 기록 중...")
    try:
        write_status_to_sheet(ws, all_records, results)
        print("✅ 시트 기록 완료")
    except Exception as e:
        print(f"❌ 시트 기록 실패: {e}")

    # 6. 최종 결과 요약
    print(f"\n🎉 맞춤형 이메일 발송 완료!")
    print(f"✅ 성공: {success_count}개")
    print(f"❌ 실패: {fail_count}개")
    print(f"📊 성공률: {(success_count/(success_count+fail_count)*100):.1f}%")

    if fail_count > 0:
        print(f"\n❌ 실패한 이메일 목록:")
        for email, (status, error) in results.items():
            if status == "FAIL":
                print(f"  - {email}: {error}")


if __name__ == "__main__":
    main()
