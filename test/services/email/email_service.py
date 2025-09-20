from .gmail_service import GmailAPIService


def load_html_template(html_file_path):
    """HTML 템플릿 파일 로드"""
    try:
        with open(html_file_path, "r", encoding="utf-8") as file:
            return file.read()
    except FileNotFoundError:
        print(f"HTML 파일을 찾을 수 없습니다: {html_file_path}")
        return None
    except Exception as e:
        print(f"HTML 파일 읽기 오류: {e}")
        return None


def send_emails_with_gmail_api(
    email_list, subject, message_text=None, html_file_path=None, attachment_path=None
):
    """Gmail API를 사용한 이메일 발송"""

    # Gmail API 서비스 초기화
    try:
        gmail_service = GmailAPIService()
    except Exception as e:
        raise ValueError(f"Gmail API 인증 실패: {e}")

    # HTML 템플릿 로드
    html_content = None
    if html_file_path:
        html_content = load_html_template(html_file_path)

    success_count = 0
    fail_count = 0
    results_map = {}  # {email: ("SUCCESS"/"FAIL", error_message)}

    for email in email_list:
        try:
            result = gmail_service.send_message(
                to=email,
                subject=subject,
                message_text=message_text,
                html_content=html_content,
                attachment_path=attachment_path,
            )

            if result["status"] == "SUCCESS":
                success_count += 1
                results_map[email] = ("SUCCESS", "")
            else:
                fail_count += 1
                results_map[email] = ("FAIL", result.get("error", "Unknown error"))

        except Exception as e:
            fail_count += 1
            print(f"❌ {email} 발송 실패: {e}")
            results_map[email] = ("FAIL", str(e))

    print(f"\n발송 완료! 성공: {success_count}개, 실패: {fail_count}개")
    return results_map
