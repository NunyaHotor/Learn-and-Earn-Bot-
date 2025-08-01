# sheet_manager.py
import gspread
from google.oauth2.service_account import Credentials

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

CREDENTIALS_FILE = "learn4cash-key.json"
creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=SCOPES)
client = gspread.authorize(creds)
sheet = client.open("Learn4Cash_Users").sheet1

def get_user_row(user_id):
    records = sheet.get_all_records()
    for idx, row in enumerate(records):
        if str(row['UserID']) == str(user_id):
            return idx + 2  # 1-based indexing + header
    return None

def register_user(user_id, name, username, referrer_id=None, momo_number=''):
    if get_user_row(user_id):
        return
    new_row = [user_id, name, username or '', 3, 0, referrer_id or '', 0, momo_number]
    sheet.append_row(new_row)

def update_user_tokens_points(user_id, tokens, points):
    row = get_user_row(user_id)
    if not row:
        return
    sheet.update_cell(row, 4, tokens)
    sheet.update_cell(row, 5, points)

def get_user_data(user_id):
    row = get_user_row(user_id)
    if not row:
        return None
    data = sheet.row_values(row)
    while len(data) < 8:
        data.append("")
    return {
        "UserID": data[0],
        "Name": data[1],
        "Username": data[2],
        "Tokens": int(data[3]) if data[3].isdigit() else 0,
        "Points": int(data[4]) if data[4].isdigit() else 0,
        "ReferrerID": data[5],
        "ReferralEarnings": float(data[6]) if data[6] else 0,
        "MoMoNumber": data[7]
    }

def update_user_momo(user_id, momo_number):
    row = get_user_row(user_id)
    if row:
        sheet.update_cell(row, 8, momo_number)

def log_token_purchase(user_id, label, quantity):
    sheet_log = client.open("Learn4Cash_Users").worksheet("TokenLog")
    sheet_log.append_row([str(user_id), label, quantity])

def increment_referral_count(ref_id):
    row = get_user_row(ref_id)
    if not row:
        return
    count_cell = sheet.cell(row, 7)
    count = float(count_cell.value or 0)
    sheet.update_cell(row, 7, count + 1)

def log_point_redemption(user_id, reward, points_used, timestamp):
    try:
        sheet_log = client.open("Learn4Cash_Users").worksheet("Redemptions")
    except gspread.exceptions.WorksheetNotFound:
        sheet_log = client.open("Learn4Cash_Users").add_worksheet(title="Redemptions", rows="1000", cols="6")
        sheet_log.insert_row(["UserID", "Reward", "PointsUsed", "Timestamp", "Status"], 1)

    row = [user_id, reward, points_used, timestamp, "Pending"]
    sheet_log.append_row(row)

def reward_referrer(ref_id):
    row = get_user_row(ref_id)
    if not row:
        return
    tokens = sheet.cell(row, 4).value
    new_tokens = int(tokens) + 1 if tokens and tokens.isdigit() else 1
    sheet.update_cell(row, 4, new_tokens)
