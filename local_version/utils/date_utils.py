# utils/date_utils.py
import logging
from datetime import datetime, date

logger = logging.getLogger(__name__)


def calculate_deadline_info(deadline_date):
    """마감일 정보 계산"""
    if not deadline_date:
        return "마감일 미정"

    try:
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


def get_week_info():
    """현재 주차 정보 반환"""
    now = datetime.now()
    month = now.month
    week = (now.day - 1) // 7 + 1
    return f"{month}월 {week}주차"
