import requests
import json
import time

def fetch_job_detail(seqno):
    """삼성 채용 정보를 가져오는 함수"""
    url = f"https://www.samsungcareers.com/recruit/detail.data?seqno={seqno}&strCode="
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    try:
        print(f"[{seqno}] 요청 시작...")
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        
    except requests.exceptions.Timeout:
        print(f"[{seqno}] 요청 시간 초과")
        return None
    except requests.exceptions.RequestException as e:
        print(f"[{seqno}] 네트워크 오류: {e}")
        return None
    except json.JSONDecodeError:
        print(f"[{seqno}] JSON 파싱 오류")
        return None
    
    result = data.get('data', {}).get('result', None)
    items = data.get('data', {}).get('items', [])
    item = items[0] if items else {}
    if not result:
        print(f"[{seqno}] 'result' 데이터 없음")
        return None
        
    
    # 실제 웹에서 접근 가능한 상세 페이지용 URL 생성
    detail_url = f"https://www.samsungcareers.com/main.html?seq={seqno}"
    
    # 고용형태 매핑
    recruit_type_map = {
        'A': '신입',
        'B': '경력',
        'C': '인턴'
    }
    
    job_info = {
    "회사명": result.get("cmpNameKr", "정보 없음"),
    "직무명": item.get("titleKr", "정보 없음"),
    "고용형태": (item.get("memoKr") or "정보 없음").replace("근무형태 : ", ""),
    "전공조건": item.get("favorKr", "정보 없음"),
    "학력조건": "학사 이상" if "학사" in item.get("favorKr", "") else "정보 없음",
    "근무지역": item.get("workPlaceKr", result.get("workArea", "정보 없음")),
    "전문연": "해당" if "병역필" in result.get("qlfctKr", "") else "비해당",
    "개발스킬셋": ", ".join([
        skill for skill in ["Python", "TensorFlow", "PyTorch", "Transformer", "LLM", "AWS"]
        if skill.lower() in item.get("qlfctKr", "").lower()
    ]) or "정보 없음",
    "서류 마감일": parse_deadline(result.get("enddate", "")),
    "지원링크": detail_url
}

    
    
    print(f"[{seqno}] 정보 수집 완료: {job_info['직무명']}")
    return job_info

def parse_deadline(raw):
    """YYYYMMDDHHMM 형식을 YYYY-MM-DD HH:MM 형식으로 변환"""
    if not raw or len(raw) != 12:
        return "마감일 정보 없음"
    
    try:
        year = raw[:4]
        month = raw[4:6]
        day = raw[6:8]
        hour = raw[8:10]
        minute = raw[10:12]
        return f"{year}-{month}-{day} {hour}:{minute}"
    except (ValueError, IndexError):
        return "날짜 형식 오류"

def main():
    """메인 실행 함수"""
    print("=== 삼성 채용 정보 수집 시작 ===")
    
    # 수집할 채용 공고 번호들
   
    job_sequences = ['20367']
    
    collected_jobs = []
    
    for i, seq in enumerate(job_sequences, 1):
        print(f"\n[{i}/{len(job_sequences)}] 공고 번호: {seq}")
        
        job_info = fetch_job_detail(seq)
        if job_info:
            collected_jobs.append(job_info)
            
            # JSON 형태로 출력
            print("수집된 정보:")
            print(json.dumps(job_info, indent=2, ensure_ascii=False))
        else:
            print(f"[{seq}] 정보 수집 실패")
        
        # 요청 간 딜레이 (서버 부하 방지)
        if i < len(job_sequences):
            print("잠시 대기 중...")
            time.sleep(2)
    
    # 최종 결과 요약
    print(f"\n=== 수집 완료 ===")
    print(f"총 {len(collected_jobs)}개 공고 정보 수집 성공")
    
    # 결과를 파일로 저장
    if collected_jobs:
        filename = "samsung_jobs.json"
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(collected_jobs, f, indent=2, ensure_ascii=False)
            print(f"결과가 '{filename}' 파일로 저장되었습니다.")
        except Exception as e:
            print(f"파일 저장 실패: {e}")
    
    return collected_jobs

# 스크립트 직접 실행 시
if __name__ == "__main__":
    try:
        results = main()
        
        # 간단한 통계
        if results:
            print(f"\n=== 수집 통계 ===")
            for job in results:
                print(f"• {job['회사명']} - {job['직무명']} ({job['고용형태']})")
                
    except KeyboardInterrupt:
        print("\n\n사용자가 중단했습니다.")
    except Exception as e:
        print(f"\n예상치 못한 오류: {e}")
