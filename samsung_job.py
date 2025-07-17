import requests
import json

def fetch_job_detail(seqno):
    url = f"https://www.samsungcareers.com/recruit/detail.data?seqno={seqno}&strCode="
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        print(f"[{seqno}] 요청 실패: {e}")
        return None

    result = data.get('data', {}).get('result', None)
    if not result:
        print(f"[{seqno}] 'result' 없음")
        return None

    # 실제 웹에서 접근 가능한 상세 페이지용 URL 생성
    detail_url = f"https://www.samsungcareers.com/main.html?seq={seqno}"

    return {
        "회사명": result.get('cmpNameKr', '없음'),
        "직무명": result.get('title', '없음'),
        "고용형태": {
            'A': '신입',
            'B': '경력',
            'C': '인턴'
        }.get(result.get('recruitType', ''), '기타'),
        "마감일": parse_deadline(result.get('enddate', '')),
        "상세 정보": detail_url
    }

def parse_deadline(raw):
    return f"{raw[:4]}-{raw[4:6]}-{raw[6:8]} {raw[8:10]}:{raw[10:]}" if len(raw) == 12 else "형식 오류"

# 여러 개 공고 처리(직접 입력)
for seq in ['6750', '20265', '20323']:
    info = fetch_job_detail(seq)
    if info:
        print(json.dumps(info, indent=2, ensure_ascii=False))
