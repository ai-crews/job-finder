from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import smtplib
import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class SMTPEmailService:
    def __init__(self, smtp_server, smtp_port, email, password):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.email = email
        self.password = password

    def create_message(
        self,
        to,
        subject,
        message_text=None,
        html_content=None,
        attachment_path=None,
        job_data=None,
        user_name=None,
    ):
        """이메일 메시지 생성"""
        message = MIMEMultipart("alternative")
        message["From"] = self.email
        message["To"] = to
        message["Subject"] = subject

        # 텍스트 본문 추가
        if message_text:
            text_part = MIMEText(message_text, "plain", "utf-8")
            message.attach(text_part)

        # HTML 본문 추가 (job_data가 있으면 템플릿에 삽입)
        if html_content:
            if job_data:
                html_content = self.insert_job_data(
                    html_content, job_data, user_name or ""
                )
            html_part = MIMEText(html_content, "html", "utf-8")
            message.attach(html_part)

        # 첨부파일이 있으면 추가
        if attachment_path and os.path.exists(attachment_path):
            with open(attachment_path, "rb") as attachment:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(attachment.read())
            encoders.encode_base64(part)
            part.add_header(
                "Content-Disposition",
                f"attachment; filename={os.path.basename(attachment_path)}",
            )
            message.attach(part)

        return message

    def send_message(
        self,
        to,
        subject,
        message_text=None,
        html_content=None,
        attachment_path=None,
        job_data=None,
        user_name=None,
    ):
        """단일 이메일 발송"""
        logger.info(f"이메일 발송: {to}")

        try:
            message = self.create_message(
                to,
                subject,
                message_text,
                html_content,
                attachment_path,
                job_data,
                user_name,
            )

            # SMTP 서버 연결 및 발송
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.email, self.password)
                server.send_message(message)

            logger.info(f"✅ 발송 성공: {to}")
            return {"status": "SUCCESS", "email": to}

        except smtplib.SMTPAuthenticationError as error:
            logger.error(f"인증 실패: {to} - {error}")
            return {"status": "FAIL", "email": to, "error": f"인증 실패: {str(error)}"}

        except smtplib.SMTPRecipientsRefused as error:
            logger.error(f"수신자 오류: {to} - {error}")
            return {
                "status": "FAIL",
                "email": to,
                "error": f"수신자 주소 오류: {str(error)}",
            }

        except Exception as error:
            logger.error(f"❌ 발송 실패: {to} - {error}")
            return {"status": "FAIL", "email": to, "error": str(error)}

    def insert_job_data(self, html_content, job_data, user_name):
        """HTML 템플릿에 채용공고 데이터 삽입"""
        # 기본 정보 교체
        current_date = datetime.now().strftime("%Y.%m.%d")
        week_info = self.get_week_info()

        html_content = html_content.replace("{{USER_NAME}}", user_name)
        html_content = html_content.replace("{{CURRENT_DATE}}", current_date)
        html_content = html_content.replace("{{WEEK}}", week_info)

        # 채용공고 카드들 생성
        job_cards_html = "".join(
            self.create_job_card_html(job_info) for job_info in job_data
        )
        html_content = html_content.replace("{{JOB_CARDS}}", job_cards_html)

        logger.info(f"템플릿 생성 완료: {len(job_data)}개 공고")
        return html_content

    def create_job_card_html(self, job_info):
        """개별 채용공고 카드 HTML 생성"""
        job = job_info["job"]
        scores = job_info["scores"]

        # 회사 로고 및 희망기업 표시
        company_logo = job["company_name"][:2] if job["company_name"] else "회사"
        star_icon = "⭐️" if scores.get("company_bonus", 0) > 0 else ""

        # 태그 및 마감일 정보
        tags_html = self.create_tags_html(job)
        deadline_info = self.calculate_deadline_info(
            job.get("application_deadline_date")
        )
        apply_link = job.get("application_link", "#")

        if apply_link == "#":
            logger.warning(f"지원 링크 없음: {job['company_name']}")

        return f"""
        <div class="job-card">
          <div class="job-content">
            <table class="job-header-table">
              <tr>
                <td class="logo-cell">
                  <div class="company-logo">{company_logo}</div>
                </td>
                <td class="info-cell">
                  <div class="company-name">{star_icon}{job['company_name']}</div>
                  <table class="job-info-table">
                    <tr>
                      <td class="job-label-cell"><span class="job-label">공고명</span></td>
                      <td><span class="job-value">{job.get('job_title', '채용공고')}</span></td>
                    </tr>
                    <tr>
                      <td class="job-label-cell"><span class="job-label">고용형태</span></td>
                      <td><span class="tags">{tags_html}</span></td>
                    </tr>
                    <tr>
                      <td class="job-label-cell"><span class="job-label">접수마감</span></td>
                      <td><div class="job-value">{deadline_info}</div></td>
                    </tr>
                  </table>
                </td>
              </tr>
            </table>
            <a href="{apply_link}" class="apply-btn">바로가기</a>
          </div>
        </div>
        """

    def create_tags_html(self, job):
        """경력/고용형태 태그 HTML 생성"""
        tags = []

        # 경력 태그 - 신입만 필터링되므로 신입만 표시
        if job.get("experience_level") in ["신입", "E01", None]:
            tags.append('<span class="tag tag-entry">신입</span>')

        # 고용형태 태그
        emp_type = job.get("employment_type")
        if emp_type == "T01":
            tags.append('<span class="tag tag-fulltime">정규직</span>')
        elif emp_type == "T02":
            tags.append('<span class="tag tag-fulltime">계약직</span>')
        elif emp_type == "T03":
            tags.append('<span class="tag tag-intern">인턴</span>')

        return "".join(tags)

    def calculate_deadline_info(self, deadline_date):
        """마감일 정보 계산"""
        if not deadline_date:
            return "마감일 미정"

        try:
            from datetime import date

            if isinstance(deadline_date, str):
                deadline = datetime.strptime(deadline_date, "%Y-%m-%d").date()
            else:
                deadline = deadline_date

            today = date.today()
            days_left = (deadline - today).days
            deadline_str = deadline.strftime("~%y년 %m월 %d일")

            if days_left < 0:
                return f"{deadline_str} <span class='job-dday'>(마감)</span>"
            elif days_left == 0:
                return f"{deadline_str} <span class='job-dday'>(오늘마감)</span>"
            else:
                return f"{deadline_str} <span class='job-dday'>(D-{days_left})</span>"

        except Exception as e:
            logger.error(f"마감일 계산 오류: {e}")
            return "마감일 확인 필요"

    def get_week_info(self):
        """현재 주차 정보 반환"""
        now = datetime.now()
        month = now.month
        week = (now.day - 1) // 7 + 1
        return f"{month}월 {week}주차"
