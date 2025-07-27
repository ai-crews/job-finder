import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()
html_file_path = os.path.join(os.path.dirname(__file__), "/email/email.html")
# 보내는 사람과 받는 사람
sender_email = os.getenv("SENDER_EMAIL")
receiver_email = os.getenv("RECEIVER_EMAIL")
password = os.getenv("EMAIL_PW")

# 이메일 메시지 기본 세팅
message = MIMEMultipart("alternative")
message["Subject"] = "채용 공고입니다!"
message["From"] = sender_email
message["To"] = receiver_email


# 현재 스크립트 위치 기준 상대 경로
html_file_path = os.path.join(os.path.dirname(__file__), "email.html")

# HTML 파일 읽기
with open(html_file_path, "r", encoding="utf-8") as file:
    html_content = file.read()

# HTML 내용을 이메일에 붙이기
part = MIMEText(html_content, "html")
message.attach(part)

# Gmail SMTP 서버 통해 메일 보내기
with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
    server.login(sender_email, password)
    server.sendmail(sender_email, receiver_email, message.as_string())
