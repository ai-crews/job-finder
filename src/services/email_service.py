from auth.gmail_auth import authenticate_gmail
from utils.message_builder import create_message, load_html_template


def send_message(service, user_id, message):
    """이메일 발송"""
    try:
        result = service.users().messages().send(userId=user_id, body=message).execute()
        print(f'이메일이 성공적으로 발송되었습니다! Message ID: {result["id"]}')
        return result
    except Exception as error:
        print(f"이메일 발송 중 오류가 발생했습니다: {error}")
        return None


def send_emails(
    email_list, subject, message_text=None, html_file_path=None, attachment_path=None
):
    """대량 이메일 발송"""
    service = authenticate_gmail()
    sender_email = "me"

    html_content = None
    if html_file_path:
        html_content = load_html_template(html_file_path)

    success_count = 0
    fail_count = 0
    results_map = {}  # {email: ("SUCCESS"/"FAIL", message_id_or_error)}

    for email in email_list:
        try:
            message = create_message(
                sender=sender_email,
                to=email,
                subject=subject,
                message_text=message_text,
                html_content=html_content,
                attachment_path=attachment_path,
            )

            result = send_message(service, "me", message)
            if result:
                success_count += 1
                print(f"✅ {email}에게 발송 완료")
                results_map[email] = ("SUCCESS", result.get("id", ""))
            else:
                fail_count += 1
                print(f"❌ {email} 발송 실패")
                results_map[email] = ("FAIL", "no_result")

        except Exception as e:
            fail_count += 1
            print(f"❌ {email} 발송 실패: {e}")
            results_map[email] = ("FAIL", str(e))

    print(f"\n발송 완료! 성공: {success_count}개, 실패: {fail_count}개")
    return results_map


def send_job_posting_email(recipient_email, html_file_path="templates/email.html"):
    """채용 공고 이메일 발송"""
    return send_emails(
        email_list=[recipient_email],
        subject="채용 공고입니다!",
        message_text="채용 공고를 확인해 주세요.",
        html_file_path=html_file_path,
    )
