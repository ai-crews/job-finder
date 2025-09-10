import os

def load_html_template(html_file_path):
    """HTML 템플릿 파일 로드"""
    try:
        with open(html_file_path, "r", encoding="utf-8") as file:
            return file.read()
    except FileNotFoundError:
        print(f"HTML 파일을 찾을 수 없습니다: {html_file_path}")
        return None
    except Exception as e:
        print(f"HTML 파일 읽기 오류: {e}")
        return None
