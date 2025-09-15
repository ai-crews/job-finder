import logging
from config.email_config import EmailConfig

logger = logging.getLogger(__name__)


class TemplateLoader:
    """템플릿 로더 서비스"""

    @staticmethod
    def load_email_template() -> str:
        """이메일 HTML 템플릿 로드"""
        try:
            with open(EmailConfig.TEMPLATE_PATH, "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            logger.error(f"템플릿 파일을 찾을 수 없음: {EmailConfig.TEMPLATE_PATH}")
            return None
        except Exception as e:
            logger.error(f"템플릿 로드 오류: {e}")
            return None
