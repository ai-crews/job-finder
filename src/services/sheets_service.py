import pandas as pd
from datetime import datetime
from auth.sheets_auth import get_sheets_client


def load_recipients_from_sheet(spreadsheet_id, worksheet_name="Sheet1"):
    """
    스프레드시트에서 수신자 목록(email 컬럼)을 읽어 리스트로 반환
    - spreadsheet_id: 구글 시트 ID(주소의 /d/<여기>/edit)
    - worksheet_name: 탭 이름
    """
    gc = get_sheets_client()
    sh = gc.open_by_key(spreadsheet_id)
    ws = sh.worksheet(worksheet_name)
    records = ws.get_all_records()  # 헤더 기반 dict 리스트

    if not records:
        return [], None, None  # 비어있음

    df = pd.DataFrame(records)
    if "email" not in df.columns:
        raise ValueError("시트에 'email' 컬럼이 없습니다.")

    # 이메일 컬럼에서 빈값 제거 + 중복 제거
    email_list = (
        df["email"]
        .astype(str)
        .str.strip()
        .loc[lambda s: s.str.len() > 0]
        .drop_duplicates()
        .tolist()
    )
    return email_list, sh, ws  # 나중에 로그 쓰고 싶으면 ws 활용


def write_status_to_sheet(ws, df_records, results_map):
    """
    ws: gspread worksheet
    df_records: get_all_records()로 만든 DataFrame
    results_map: {email: ("SUCCESS"/"FAIL", message_id_or_error)}
    """
    df = pd.DataFrame(df_records)
    if "status" not in df.columns:
        df["status"] = ""
    if "sent_at" not in df.columns:
        df["sent_at"] = ""

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    for i, row in df.iterrows():
        email = str(row.get("email", "")).strip()
        if not email:
            continue
        status, msg = results_map.get(email, ("", ""))
        if status:
            df.at[i, "status"] = f"{status} {msg}"
            df.at[i, "sent_at"] = now

    # 시트에 일괄 반영 (A1 기준으로 전체 덮어쓰기)
    values = [df.columns.tolist()] + df.fillna("").values.tolist()
    ws.update("A1", values)
