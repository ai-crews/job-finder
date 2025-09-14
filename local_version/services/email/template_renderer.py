# services/email_template.py
import logging
from datetime import datetime
from utils.date_utils import calculate_deadline_info, get_week_info

logger = logging.getLogger(__name__)


class EmailTemplate:
    def insert_job_data(self, html_content, job_data, user_name):
        """HTML 템플릿에 채용공고 데이터 삽입"""
        # 기본 정보 교체
        current_date = datetime.now().strftime("%Y.%m.%d")
        week_info = get_week_info()

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
        deadline_info = calculate_deadline_info(job.get("application_deadline_date"))
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
