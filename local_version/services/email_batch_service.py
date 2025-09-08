import logging
from typing import List, Dict, Any
from services.email_service import SMTPEmailService
from services.job_matcher import get_personalized_jobs
from services.template_loader import TemplateLoader
from services.user_service import UserService
from services.email_logger import EmailLogger
from config.email_config import EmailConfig

logger = logging.getLogger(__name__)


class EmailBatchService:
    """이메일 배치 발송 서비스"""

    def __init__(self):
        self.email_service = SMTPEmailService.from_config()
        self.template_loader = TemplateLoader()
        self.user_service = UserService()
        self.email_logger = EmailLogger()

    def send_personalized_emails(self) -> Dict[str, Any]:
        """개인화된 이메일 배치 발송"""
        # HTML 템플릿 로드
        html_template = self.template_loader.load_email_template()
        if not html_template:
            raise RuntimeError("HTML 템플릿 로드 실패")

        # 구독자 목록 가져오기
        users = self.user_service.get_active_subscribers()
        if not users:
            logger.warning("구독 중인 사용자가 없습니다.")
            return self._create_result(0, 0, 0)

        total_users = len(users)
        logger.info(f"발송 대상: {total_users}명")

        # 각 사용자 처리
        success_count = 0
        fail_count = 0

        for i, user in enumerate(users, 1):
            user_id, email, name = user[0], user[1], user[2]
            logger.info(f"[{i}/{total_users}] 처리 중: {email}")

            if self._process_single_user(user_id, email, name, html_template):
                success_count += 1
            else:
                fail_count += 1

        return self._create_result(total_users, success_count, fail_count)

    def _process_single_user(
        self, user_id: int, email: str, name: str, html_template: str
    ) -> bool:
        """단일 사용자 처리"""
        logger.info(f"처리 시작: {name}({email})")

        try:
            # 개인화된 채용공고 가져오기
            recommended_jobs = get_personalized_jobs(
                email, top_n=EmailConfig.MAX_RECOMMENDED_JOBS
            )

            if not recommended_jobs:
                logger.warning(f"추천할 공고가 없음: {email}")
                return self.email_logger.log_result(
                    user_id, email, name, "FAILED", "추천할 공고가 없습니다", 0
                )

            logger.info(f"추천 공고 {len(recommended_jobs)}개 발견: {email}")

            # 개인화된 이메일 발송
            subject = f"{name}님을 위한 맞춤 채용공고"
            result = self.email_service.send_message(
                to=email,
                subject=subject,
                html_content=html_template,
                job_data=recommended_jobs,
                user_name=name,
            )

            # 발송 결과 처리
            if result["status"] == "SUCCESS":
                return self.email_logger.log_result(
                    user_id, email, name, "SUCCESS", None, len(recommended_jobs)
                )
            else:
                return self.email_logger.log_result(
                    user_id,
                    email,
                    name,
                    "FAILED",
                    result.get("error", "알 수 없는 오류"),
                    len(recommended_jobs),
                )

        except Exception as e:
            logger.error(f"사용자 처리 중 오류: {email} - {e}")
            return self.email_logger.log_result(
                user_id, email, name, "FAILED", str(e), 0
            )

    def _create_result(self, total: int, success: int, fail: int) -> Dict[str, Any]:
        """결과 딕셔너리 생성"""
        return {
            "total_users": total,
            "success_count": success,
            "fail_count": fail,
            "success_rate": (success / total * 100) if total > 0 else 0,
        }
