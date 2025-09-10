import pandas as pd
from datetime import datetime
from .sheets_auth import get_sheets_client


def load_recipients_from_sheet(spreadsheet_id, worksheet_name="Sheet1"):
    """
    스프레드시트에서 수신자 목록(이메일 주소 컬럼)을 읽어 리스트로 반환
    - spreadsheet_id: 구글 시트 ID(주소의 /d/<여기>/edit)
    - worksheet_name: 탭 이름
    """
    gc = get_sheets_client()
    sh = gc.open_by_key(spreadsheet_id)
    ws = sh.worksheet(worksheet_name)

    # get_all_records() 대신 get_all_values() 사용 (구글 폼 응답 시트 호환)
    all_values = ws.get_all_values()
    print(f"총 행 수: {len(all_values)}")

    if len(all_values) < 2:  # 헤더 + 최소 1개 데이터 행
        print("시트에 데이터가 충분하지 않습니다.")
        return [], None, None

    # 첫 번째 행이 헤더
    headers = all_values[0]

    # 헤더에서 '이메일 주소' 컬럼의 인덱스 찾기
    try:
        email_col_index = headers.index("이메일 주소")
        print(f"'이메일 주소' 컬럼 인덱스: {email_col_index}")
    except ValueError:
        raise ValueError("시트에 '이메일 주소' 컬럼이 없습니다.")

    # 데이터 행들에서 이메일 추출
    email_list = []
    for row_idx, row in enumerate(
        all_values[1:], start=2
    ):  # 헤더 제외, 행 번호는 2부터
        if len(row) > email_col_index:
            email = str(row[email_col_index]).strip()
            if email and email != "" and "@" in email:  # 유효한 이메일인지 간단 체크
                email_list.append(email)
                print(f"행 {row_idx}: {email}")

    # 중복 제거
    email_list = list(set(email_list))

    print(f"추출된 이메일 수: {len(email_list)}")
    print(f"최종 이메일 목록: {email_list}")

    return email_list, sh, ws


def write_status_to_sheet(ws, df_records, results_map):
    """
    ws: gspread worksheet
    df_records: get_all_records()로 만든 list (또는 DataFrame으로 변환할 데이터)
    results_map: {email: ("SUCCESS"/"FAIL", message_id_or_error)}
    """
    # get_all_values() 방식으로 데이터를 가져왔을 때를 대비
    all_values = ws.get_all_values()
    if len(all_values) < 2:
        print("시트에 기록할 데이터가 없습니다.")
        return

    headers = all_values[0]

    # 'status'와 'sent_at' 컬럼이 없으면 추가
    status_col_index = None
    sent_at_col_index = None

    if "status" in headers:
        status_col_index = headers.index("status")
    else:
        headers.append("status")
        status_col_index = len(headers) - 1

    if "sent_at" in headers:
        sent_at_col_index = headers.index("sent_at")
    else:
        headers.append("sent_at")
        sent_at_col_index = len(headers) - 1

    # 이메일 주소 컬럼 인덱스
    try:
        email_col_index = headers.index("이메일 주소")
    except ValueError:
        print("'이메일 주소' 컬럼을 찾을 수 없어 결과를 기록할 수 없습니다.")
        return

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 데이터 업데이트
    updated_values = [headers]  # 헤더 추가

    for row in all_values[1:]:  # 데이터 행들
        # 행 길이를 헤더 길이에 맞춤
        while len(row) < len(headers):
            row.append("")

        if len(row) > email_col_index:
            email = str(row[email_col_index]).strip()
            if email in results_map:
                status, msg = results_map[email]
                row[status_col_index] = f"{status} {msg}"
                row[sent_at_col_index] = now

        updated_values.append(row)

    # 시트에 일괄 업데이트
    try:
        ws.update("A1", updated_values)
        print("시트 업데이트 완료")
    except Exception as e:
        print(f"시트 업데이트 중 오류: {e}")
