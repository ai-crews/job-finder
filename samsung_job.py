import requests
from bs4 import BeautifulSoup
import time
import random
import os
import json

class SaraminCrawler:
    def __init__(self, base_delay=1, max_delay=3):
        self.base_delay = base_delay
        self.max_delay = max_delay
        
        # 세션 생성 및 헤더 설정
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ko-KR,ko;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
    
    def random_delay(self):
        """랜덤 타임 슬립"""
        delay = random.uniform(self.base_delay, self.max_delay)
        time.sleep(delay)
        print(f"대기 시간: {delay:.2f}초")
    
    def get_job_data(self, base_url, start_page=1, end_page=2):
        """채용 공고 데이터 수집 (기업명, 공고명, 경력사항)"""
        job_data_list = []
        
        for page_num in range(start_page, end_page + 1):
            try:
                # 페이지 URL 생성
                page_url = f"{base_url}&recruitPage={page_num}"
                print(f"페이지 {page_num} 크롤링 중: {page_url}")
                
                # 페이지 요청
                response = self.session.get(page_url)
                response.raise_for_status()
                
                # BeautifulSoup으로 파싱
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # 채용공고 섹션들을 찾기 - 다양한 클래스명 시도
                possible_classes = ['item_recruit', 'list_item', 'recruit_item', 'job_item']
                job_sections = []
                
                for class_name in possible_classes:
                    sections = soup.find_all('div', class_=class_name)
                    if sections:
                        job_sections = sections
                        print(f"'{class_name}' 클래스로 {len(sections)}개 섹션 발견")
                        break
                
                # 만약 위의 클래스들로 찾지 못했다면, 더 일반적인 방법 시도
                if not job_sections:
                    # str_tit 클래스를 가진 링크들의 부모 요소들 찾기
                    str_tit_links = soup.find_all('a', class_='str_tit')
                    print(f"str_tit 링크 {len(str_tit_links)}개 발견")
                    
                    # 각 링크의 부모 div에서 데이터 추출
                    processed_divs = set()
                    
                    for link in str_tit_links:
                        # 부모 요소들을 찾아서 채용공고 정보가 있는 div 찾기
                        current = link
                        for _ in range(5):  # 최대 5단계 부모까지 확인
                            current = current.parent
                            if current and current.name == 'div':
                                div_id = id(current)  # 메모리 주소로 중복 체크
                                if div_id not in processed_divs:
                                    processed_divs.add(div_id)
                                    job_sections.append(current)
                                break
                
                print(f"총 {len(job_sections)}개 채용공고 섹션 발견")
                
                page_count = 0
                for i, section in enumerate(job_sections):
                    try:
                        # 기업명 추출 - company-info가 포함된 링크
                        company_name = ""
                        str_tit_links = section.find_all('a', class_='str_tit')
                        
                        for link in str_tit_links:
                            href = link.get('href', '')
                            if 'company-info' in href:
                                company_name = link.get_text(strip=True)
                                break
                        
                        # 공고명 추출 - jobs/relay가 포함된 링크
                        job_title = ""
                        for link in str_tit_links:
                            href = link.get('href', '')
                            if 'jobs/relay' in href or 'recruit' in href:
                                job_span = link.find('span')
                                if job_span:
                                    job_title = job_span.get_text(strip=True)
                                else:
                                    job_title = link.get_text(strip=True)
                                break
                        
                        # 경력사항 추출 - 다양한 클래스명 시도
                        career = ""
                        career_classes = ['career', 'exp', 'experience', 'condition']
                        for class_name in career_classes:
                            career_elem = section.find('p', class_=class_name)
                            if not career_elem:
                                career_elem = section.find('span', class_=class_name)
                            if not career_elem:
                                career_elem = section.find('div', class_=class_name)
                            
                            if career_elem:
                                career = career_elem.get_text(strip=True)
                                break
                        
                        # 디버깅 정보
                        if i < 3:  # 처음 3개만 디버그 출력
                            print(f"\n--- 섹션 {i+1} 디버깅 ---")
                            print(f"기업명: '{company_name}'")
                            print(f"공고명: '{job_title}'")
                            print(f"경력: '{career}'")
                            print(f"str_tit 링크 수: {len(str_tit_links)}")
                            for j, link in enumerate(str_tit_links[:3]):
                                print(f"  링크 {j+1}: href={link.get('href', '')}, text={link.get_text(strip=True)[:50]}")
                        
                        # 데이터가 있을 때 저장 (모든 필드가 필수는 아님)
                        if company_name or job_title:
                            job_data = {
                                'company_name': company_name,
                                'job_title': job_title,
                                'career': career,
                                'page': page_num
                            }
                            job_data_list.append(job_data)
                            page_count += 1
                    
                    except Exception as e:
                        print(f"개별 섹션 {i} 파싱 오류: {str(e)}")
                        continue
                
                print(f"페이지 {page_num}에서 {page_count}개 데이터 수집")
                self.random_delay()  # 페이지 간 랜덤 딜레이
                
            except Exception as e:
                print(f"페이지 {page_num} 크롤링 오류: {str(e)}")
                continue
        
        print(f"총 {len(job_data_list)}개 채용공고 데이터 수집 완료")
        return job_data_list
    
    def save_html(self, url, filename):
        """HTML 파일 저장"""
        try:
            response = self.session.get(url)
            response.raise_for_status()
            
            # HTML 저장 디렉토리 생성
            os.makedirs('html_files', exist_ok=True)
            
            filepath = os.path.join('html_files', filename)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(response.text)
            
            print(f"HTML 저장 완료: {filepath}")
            return filepath
        except Exception as e:
            print(f"HTML 저장 오류: {str(e)}")
            return None
    
    def analyze_html_structure(self, url):
        """HTML 구조 분석 - 디버깅용"""
        try:
            response = self.session.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            print("=== HTML 구조 분석 ===")
            
            # str_tit 클래스 링크들 분석
            str_tit_links = soup.find_all('a', class_='str_tit')
            print(f"str_tit 링크 총 {len(str_tit_links)}개 발견")
            
            for i, link in enumerate(str_tit_links[:10]):  # 처음 10개만
                href = link.get('href', '')
                text = link.get_text(strip=True)
                print(f"{i+1}. href: {href}")
                print(f"   text: {text[:100]}")
            
            # career 클래스 요소들 분석
            career_elems = soup.find_all(class_='career')
            print(f"\ncareer 클래스 요소 {len(career_elems)}개 발견")
            
            for i, elem in enumerate(career_elems[:5]):
                print(f"{i+1}. {elem.name}: {elem.get_text(strip=True)}")
            
            # 가능한 컨테이너 div들 분석
            print(f"\n=== 가능한 컨테이너 클래스들 ===")
            all_divs = soup.find_all('div', class_=True)
            class_counts = {}
            for div in all_divs:
                classes = div.get('class', [])
                for cls in classes:
                    if any(keyword in cls.lower() for keyword in ['item', 'recruit', 'job', 'list']):
                        class_counts[cls] = class_counts.get(cls, 0) + 1
            
            for cls, count in sorted(class_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
                print(f"{cls}: {count}개")
                
        except Exception as e:
            print(f"HTML 구조 분석 오류: {str(e)}")
    
    def crawl_jobs(self, base_url, start_page=1, end_page=2, save_html=False, analyze=False):
        """전체 크롤링 프로세스"""
        print("=== 사람인 채용공고 크롤링 시작 ===")
        
        # HTML 구조 분석 (옵션)
        if analyze:
            print("HTML 구조 분석 중...")
            self.analyze_html_structure(base_url)
            print("\n" + "="*50 + "\n")
        
        # HTML 저장 (옵션)
        if save_html:
            filename = f"saramin_page_{start_page}-{end_page}.html"
            self.save_html(base_url, filename)
        
        # 채용공고 데이터 수집
        job_data_list = self.get_job_data(base_url, start_page, end_page)
        
        print(f"\n=== 크롤링 완료: {len(job_data_list)}개 데이터 수집 ===")
        return job_data_list
    
    def save_to_json(self, job_data_list, filename='saramin_jobs.json'):
        """JSON 파일로 저장"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(job_data_list, f, ensure_ascii=False, indent=2)
            print(f"데이터 저장 완료: {filename}")
        except Exception as e:
            print(f"JSON 저장 오류: {str(e)}")

# 사용 예제
def main():
    # 크롤러 인스턴스 생성 (딜레이 시간 설정)
    crawler = SaraminCrawler(base_delay=1, max_delay=3)
    
    # 실제 사람인 URL
    base_url = "https://www.saramin.co.kr/zf_user/jobs/list/job-category?cat_kewd=2247%2C2248%2C82%2C83%2C81%2C89%2C1658&panel_type=&search_optional_item=n&search_done=y&panel_count=y&preview=y"
    
    # TODO: 페이지 범위 수정 가능 (현재 1~2페이지)
    # 더 많은 페이지를 크롤링하고 싶으면 end_page 값을 변경하세요
    job_data = crawler.crawl_jobs(
        base_url=base_url,
        start_page=1,
        end_page=2,  # ← 여기서 페이지 범위 수정
        save_html=True,  # HTML 파일도 저장
        analyze=True     # HTML 구조 분석도 실행
    )
    
    # JSON 파일로 저장
    crawler.save_to_json(job_data)
    
    # 결과 출력
    print(f"\n=== 수집된 데이터 샘플 (총 {len(job_data)}개) ===")
    for i, job in enumerate(job_data[:10], 1):  # 처음 10개 출력
        print(f"\n--- 채용공고 {i} ---")
        print(f"기업명: {job['company_name']}")
        print(f"공고명: {job['job_title']}")
        print(f"경력: {job['career']}")
        print(f"페이지: {job['page']}")

if __name__ == "__main__":
    main()
