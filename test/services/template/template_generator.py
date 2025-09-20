from typing import List, Dict
import json
from datetime import datetime


class EmailTemplateGenerator:
    def __init__(self, template_path: str):
        self.template_path = template_path
        self.company_logos = self._load_company_logos()

    def _load_company_logos(self) -> Dict[str, str]:
        """회사 로고 URL 매핑"""
        return {
            "삼성": "https://images.samsung.com/kdp/aboutsamsung/brand_identity/logo/720_600_1.png?$720_N_PNG$",
            "삼성전자": "https://images.samsung.com/kdp/aboutsamsung/brand_identity/logo/720_600_1.png?$720_N_PNG$",
            "삼성SDS": "https://images.samsung.com/kdp/aboutsamsung/brand_identity/logo/720_600_1.png?$720_N_PNG$",
            "SK": "https://www.sk.co.kr/lib/images/desktop/about/ci-color-img01_lg.png",
            "LG": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8d/LG_logo_%282014%29.svg/1200px-LG_logo_%282014%29.svg.png",
            "쿠팡": "https://news.coupang.com/wp-content/uploads/2023/01/coupang-bi-brand-logo-230109-01.jpg",
            "카카오": "https://t1.kakaocdn.net/kakaocorp/kakaocorp/admin/mediakit/47e79e4a019300001.png",
            "네이버": "https://upload.wikimedia.org/wikipedia/commons/thumb/2/23/Naver_Logotype.svg/2560px-Naver_Logotype.svg.png",
            "NAVER": "https://upload.wikimedia.org/wikipedia/commons/thumb/2/23/Naver_Logotype.svg/2560px-Naver_Logotype.svg.png",
            "하나카드": "https://www.hanafn.com/assets/img/ko/info/img-hana-symbol.png",
            "하나은행": "https://www.hanafn.com/assets/img/ko/info/img-hana-symbol.png",
            "두산": "https://www.doosanrobotics.com/images/sns-img.png",
            "현대모비스": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d6/Hyundai_Mobis_Logo.svg/512px-Hyundai_Mobis_Logo.svg.png",
            "신한은행": "https://www.shinhanci.co.kr/img/sub/img_ci.png?cache=none",
            "KB증권": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQGdoaWcmoWpggvou-q3kjJzna4pIg5c4LvGQ&s",
            "현대해상": "https://mblogthumb-phinf.pstatic.net/20160728_259/ppanppane_1469695930418AMF3t_PNG/%C7%F6%B4%EB%C7%D8%BB%F3_%B7%CE%B0%ED_%284%29.png?type=w800",
            "토스": "https://framerusercontent.com/images/EhEElRcoy4v5Y9uyUj3XkTWg.jpg",
            "우아한형제들": "https://woowahan-cdn.woowahan.com/static/image/share_kor.jpg",
            "셀트리온": "https://www.celltrion.com/front/assets/common/images/introduce/img_brand_symbol.png",
            "현대자동차": "https://www.hyundai.com/content/dam/hyundai/kr/ko/images/common/sns/og-image-hyundai-motors.jpg",
            "카카오뱅크": "https://daoift3qrrnil.cloudfront.net/company_groups/images/000/004/699/original/img_%285%29.png?1700663411",
            "기아": "https://image-cdn.hypb.st/https%3A%2F%2Fkr.hypebeast.com%2Ffiles%2F2021%2F01%2Fkia-motors-new-logo-brand-slogan-officially-revealed-01.jpg?q=75&w=800&cbr=1&fit=max",
        }

    def generate_personalized_email(
        self, user_data: Dict, matched_jobs: List[Dict]
    ) -> str:
        """개인화된 이메일 HTML 생성"""
        with open(self.template_path, "r", encoding="utf-8") as f:
            template = f.read()

        # 사용자 이름 삽입
        user_name = user_data.get("성함 ", "테스터").strip()

        template = template.replace("테스터님", f"{user_name}님")

        # 채용공고 섹션 생성
        job_cards_html = self._generate_job_cards(matched_jobs)

        # 기존 채용공고 섹션을 새로운 것으로 교체
        start_marker = "<!-- 하나카드 -->"
        end_marker = "<!-- 피드백 섹션 -->"

        start_idx = template.find(start_marker)
        end_idx = template.find(end_marker)

        if start_idx != -1 and end_idx != -1:
            template = template[:start_idx] + job_cards_html + template[end_idx:]

        return template

    def _generate_job_cards(self, matched_jobs: List[Dict]) -> str:
        """채용공고 카드들 HTML 생성"""
        cards_html = ""

        for job_info in matched_jobs:
            job = job_info["job"]
            is_preferred = job_info["is_preferred_company"]

            # 마감일 계산
            deadline_info = self._calculate_deadline(
                job.get("application_deadline_date", "")
            )

            # 고용형태 태그 생성
            employment_tags = self._generate_employment_tags(
                job.get("employment_type", "확인불가")
            )

            # 회사 로고 URL
            company_name = job["company_name"]
            logo_url = self.company_logos.get(
                company_name, "https://via.placeholder.com/68x113?text=Logo"
            )

            # 희망기업 표시
            star_icon = "⭐️ " if is_preferred else ""

            # 직무명 정리
            position_name = job.get("position_name", "미확인")
            if len(position_name) > 50:
                position_name = position_name[:47] + "..."

            card_html = f"""
            <!-- {company_name} -->
            <table width="100%" border="0" cellspacing="0" cellpadding="0" style="border: 1px solid #eeeeee; background-color: #fafafa; margin-bottom: 15px; border-radius: 8px;">
                <tr>
                    <td style="padding: 15px;">
                        <table width="100%" border="0" cellspacing="0" cellpadding="0">
                            <tr>
                                <td width="70" style="padding-right: 15px; vertical-align: top;">
                                    <table width="70" height="130" border="0" cellspacing="0" cellpadding="0" style="background-color: #ffffff; border: 1px solid #eee; border-radius: 6px;">
                                        <tr>
                                            <td align="center" style="vertical-align: middle;">
                                                <img src="{logo_url}" alt="{company_name}" height="auto" style="display: block; max-width: 68px; max-height: 113px;">
                                            </td>
                                        </tr>
                                    </table>
                                </td>
                                <td style="vertical-align: top;">
                                    <div style="font-weight: bold; font-size: 16px; color: #000000; margin-bottom: 4px;">{star_icon}{company_name}</div>
                                    <table width="100%" border="0" cellspacing="0" cellpadding="0">
                                        <tr>
                                            <td width="80" style="padding: 3px 12px 3px 0; vertical-align: middle;">
                                                <span style="color: #444444; font-size: 14px; font-weight: bold;">모집부문</span>
                                            </td>
                                            <td style="padding: 3px 0; vertical-align: middle;">
                                                <span style="color: #000000; font-size: 14px; line-height: 1.4;">{position_name}</span>
                                            </td>
                                        </tr>
                                        <tr>
                                            <td width="80" style="padding: 3px 12px 3px 0; vertical-align: middle;">
                                                <span style="color: #444444; font-size: 14px; font-weight: bold;">직무명</span>
                                            </td>
                                            <td style="padding: 3px 0; vertical-align: middle;">
                                                <span style="color: #000000; font-size: 14px; line-height: 1.4;">{job.get('processed_position_name')}</span>
                                            </td>
                                        </tr>
                                        <tr>
                                            <td width="80" style="padding: 3px 12px 3px 0; vertical-align: middle;">
                                                <span style="color: #444444; font-size: 14px; font-weight: bold;">고용형태</span>
                                            </td>
                                            <td style="padding: 3px 0; vertical-align: middle;">
                                                {employment_tags}
                                            </td>
                                        </tr>
                                        <tr>
                                            <td width="80" style="padding: 3px 12px 3px 0; vertical-align: middle;">
                                                <span style="color: #444444; font-size: 14px; font-weight: bold;">접수마감</span>
                                            </td>
                                            <td style="padding: 3px 0; vertical-align: middle;">
                                                <span style="color: #000000; font-size: 14px; line-height: 1.4;">{deadline_info['date']}</span>
                                                <span style="font-weight: bold; font-size: 14px; color: #000000;">{deadline_info['d_day']}</span>
                                            </td>
                                        </tr>
                                    </table>
                                </td>
                            </tr>
                        </table>
                        <table class="button-table" width="100%" border="0" cellspacing="0" cellpadding="0" style="margin-top: 15px;">
                            <tr>
                                <td class="button-td" style="padding: 0;">
                                    <a href="{job.get('application_link', '#')}" class="button-link" target="_blank" rel="noopener noreferrer" style="display: block; width: 100%; background-color: #f9fafc; border: 1px solid #e3e8ef; padding: 15px 20px; text-align: center; text-decoration: none; color: #2e2e2e; font-size: 14px; font-weight: 500; border-radius: 8px; box-sizing: border-box; -webkit-text-size-adjust: none; min-height: 20px; line-height: 1.2;"> 바로가기</a>
                                </td>
                            </tr>
                        </table>
                    </td>
                </tr>
            </table>
            """

            cards_html += card_html

        return cards_html

    def _generate_employment_tags(self, employment_type: str) -> str:
        """고용형태 태그 HTML 생성"""
        if not employment_type or employment_type == "확인불가":
            return '<span style="display: inline-block; padding: 3px 10px; background-color: #f5f5f5; color: #666666; font-size: 13px; font-weight: 500; border-radius: 4px;">미확인</span>'

        tag_styles = {
            "신입": "background-color: #bdf4ff; color: #000000;",
            "경력": "background-color: #ffe4b5; color: #8b4513;",
            "정규직": "background-color: #eaffce; color: #07632b;",
            "인턴": "background-color: #fff0ae; color: #5e2e00;",
            "계약직": "background-color: #e6d7ff; color: #4a148c;",
            "전환형": "background-color: #e6d7ff; color: #4a148c;",
        }

        tags = []
        employment_types = [
            emp.strip() for emp in employment_type.split(",") if emp.strip()
        ]

        for emp_type in employment_types:
            style = tag_styles.get(
                emp_type, "background-color: #f5f5f5; color: #666666;"
            )
            tags.append(
                f'<span style="display: inline-block; padding: 3px 10px; {style} font-size: 13px; font-weight: 500; margin-right: 5px; border-radius: 4px;">{emp_type}</span>'
            )

        return "".join(tags)

    def _calculate_deadline(self, deadline_date: str) -> Dict[str, str]:
        """마감일 정보 계산"""
        try:
            if deadline_date == "9999-12-31" or not deadline_date:
                return {"date": "상시채용", "d_day": ""}

            # 날짜 형식 처리
            if len(deadline_date) == 10:  # YYYY-MM-DD
                deadline = datetime.strptime(deadline_date, "%Y-%m-%d")
            else:
                return {"date": deadline_date, "d_day": ""}

            today = datetime.now()
            diff = (deadline - today).days

            if diff < 0:
                return {"date": f'~{deadline.strftime("%y.%m.%d")}', "d_day": "(마감)"}
            elif diff == 0:
                return {"date": f'~{deadline.strftime("%y.%m.%d")}', "d_day": "(D-Day)"}
            else:
                return {
                    "date": f'~{deadline.strftime("%y.%m.%d")}',
                    "d_day": f"(D-{diff})",
                }
        except Exception as e:
            print(f"날짜 파싱 오류: {e}")
            return {"date": deadline_date, "d_day": ""}
