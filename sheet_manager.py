import os
import time
import logging
from datetime import datetime, timezone
from dotenv import load_dotenv
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class SheetManager:
    def __init__(self):
        scope = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive"
        ]
        creds_path = os.getenv("GOOGLE_CREDENTIALS_PATH")
        if not creds_path or not os.path.exists(creds_path):
            raise ValueError(f"Google credentials file not found at {creds_path}")
        creds = ServiceAccountCredentials.from_json_keyfile_name(creds_path, scope)
        self.client = gspread.authorize(creds)
        spreadsheet_id = os.getenv("SPREADSHEET_ID")
        if not spreadsheet_id or spreadsheet_id == "your-google-sheet-id-here":
            raise ValueError("Invalid or missing SPREADSHEET_ID in .env file")
        self.spreadsheet = self.client.open_by_key(spreadsheet_id)
        self.users_sheet = self.spreadsheet.worksheet("Learn4Cash")
        self.transactions_sheet = self.spreadsheet.worksheet("TokenLog")
        self.referrals_sheet = self.spreadsheet.worksheet("Redemptions")

    def _retry_on_quota_exceeded(self, func, *args, **kwargs):
        attempts = 5
        for i in range(attempts):
            try:
                return func(*args, **kwargs)
            except gspread.exceptions.APIError as e:
                if "Quota exceeded" in str(e):
                    wait_time = 2 ** i
                    logger.warning(f"Quota exceeded, retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    raise e
        raise Exception("Max retries exceeded for Google Sheets API")

    def register_user(self, user_id, name, username, referrer_id):
        try:
            def do_register():
                existing = self.users_sheet.findall(str(user_id))
                if not existing:
                    referral_code = f"REF{str(user_id)[-6:]}"
                    row = [str(user_id), name, username or "", 0, 0, "", referral_code, 0, ""]
                    self.users_sheet.append_row(row)
                    logger.info(f"Registered user: {user_id}")
            self._retry_on_quota_exceeded(do_register)
        except Exception as e:
            logger.error(f"Error registering user {user_id}: {e}")

    def get_user_data(self, user_id):
        try:
            def do_get_user():
                records = self.users_sheet.get_all_records()
                for row in records:
                    if str(row.get('UserID', '')) == str(user_id):
                        return {
                            'UserID': row.get('UserID', ''),
                            'Name': row.get('Name', 'Unknown'),
                            'Username': row.get('Username', ''),
                            'Tokens': float(row.get('Tokens', 0)),
                            'Points': float(row.get('Points', 0)),
                            'ReferralEarnings': float(row.get('ReferralEarnings', 0)),
                            'ReferrerID': row.get('ReferrerID', ''),
                            'MoMoNumber': row.get('MoMoNumber', ''),
                            'LastClaimDate': row.get('LastClaimDate', ''),
                            'referral_code': row.get('referral_code', '')
                        }
                return None
            return self._retry_on_quota_exceeded(do_get_user)
        except Exception as e:
            logger.error(f"Error fetching user data for {user_id}: {e}")
            return None

    def update_user_tokens_points(self, user_id, tokens, points):
        try:
            def do_update():
                cell = self.users_sheet.find(str(user_id))
                if cell:
                    row = cell.row
                    self.users_sheet.update_cell(row, 4, tokens)
                    self.users_sheet.update_cell(row, 5, points)
                    logger.info(f"Updated tokens: {tokens}, points: {points} for user {user_id}")
            self._retry_on_quota_exceeded(do_update)
        except Exception as e:
            logger.error(f"Error updating tokens/points for {user_id}: {e}")

    def reward_referrer(self, referrer_id, tokens):
        try:
            def do_reward():
                cell = self.users_sheet.find(str(referrer_id))
                if cell:
                    row = cell.row
                    current_tokens = float(self.users_sheet.cell(row, 4).value or 0)
                    current_earnings = float(self.users_sheet.cell(row, 8).value or 0)
                    self.users_sheet.update_cell(row, 4, current_tokens + tokens)
                    self.users_sheet.update_cell(row, 8, current_earnings + tokens)
                    logger.info(f"Rewarded {tokens} tokens to referrer {referrer_id}")
            self._retry_on_quota_exceeded(do_reward)
        except Exception as e:
            logger.error(f"Error rewarding referrer {referrer_id}: {e}")

    def log_token_purchase(self, user_id, transaction_id, amount, payment_method):
        try:
            def do_log():
                timestamp = datetime.now(timezone.utc).isoformat()
                row = [str(user_id), transaction_id, amount, payment_method or "N/A", timestamp]
                self.transactions_sheet.append_row(row)
                logger.info(f"Logged token purchase for {user_id}: {amount} tokens")
            self._retry_on_quota_exceeded(do_log)
        except Exception as e:
            logger.error(f"Error logging token purchase for {user_id}: {e}")

    def increment_referral_count(self, referrer_id, referred_id):
        try:
            def do_increment():
                cell = self.users_sheet.find(str(referrer_id))
                if cell:
                    row = cell.row
                    current_count = int(self.users_sheet.cell(row, 8).value or 0)
                    self.users_sheet.update_cell(row, 8, current_count + 1)
                    self.referrals_sheet.append_row([str(referrer_id), str(referred_id), datetime.now(timezone.utc).isoformat()])
                    logger.info(f"Incremented referral count for {referrer_id}")
            self._retry_on_quota_exceeded(do_increment)
        except Exception as e:
            logger.error(f"Error incrementing referral count for {referrer_id}: {e}")

    def log_point_redemption(self, user_id, reward):
        try:
            def do_log_redemption():
                timestamp = datetime.now(timezone.utc).isoformat()
                row = [str(user_id), reward, timestamp]
                self.transactions_sheet.append_row(row)
                logger.info(f"Logged point redemption for {user_id}: {reward}")
            self._retry_on_quota_exceeded(do_log_redemption)
        except Exception as e:
            logger.error(f"Error logging point redemption for {user_id}: {e}")

    def update_user_momo(self, user_id, momo_number):
        try:
            def do_update_momo():
                cell = self.users_sheet.find(str(user_id))
                if cell:
                    row = cell.row
                    self.users_sheet.update_cell(row, 6, momo_number)
                    logger.info(f"Updated MoMo number for {user_id}: {momo_number}")
            self._retry_on_quota_exceeded(do_update_momo)
        except Exception as e:
            logger.error(f"Error updating MoMo number for {user_id}: {e}")

    def check_and_give_daily_reward(self, user_id):
        try:
            def do_check_reward():
                cell = self.users_sheet.find(str(user_id))
                if not cell:
                    return False, 0
                row = cell.row
                last_claim = self.users_sheet.cell(row, 9).value or ""
                today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
                if last_claim != today:
                    current_tokens = float(self.users_sheet.cell(row, 4).value or 0)
                    self.users_sheet.update_cell(row, 4, current_tokens + 1)
                    self.users_sheet.update_cell(row, 9, today)
                    logger.info(f"Daily reward of 1 token given to {user_id}")
                    return True, current_tokens + 1
                return False, float(self.users_sheet.cell(row, 4).value or 0)
            return self._retry_on_quota_exceeded(do_check_reward)
        except Exception as e:
            logger.error(f"Error checking daily reward for {user_id}: {e}")
            return False, 0

    def update_last_claim_date(self, user_id, date):
        try:
            def do_update_date():
                cell = self.users_sheet.find(str(user_id))
                if cell:
                    row = cell.row
                    self.users_sheet.update_cell(row, 9, date)
                    logger.info(f"Updated last claim date for {user_id}: {date}")
            self._retry_on_quota_exceeded(do_update_date)
        except Exception as e:
            logger.error(f"Error updating last claim date for {user_id}: {e}")

    def get_all_users(self):
        try:
            def do_get_users():
                records = self.users_sheet.get_all_records()
                return [row for row in records]
            return self._retry_on_quota_exceeded(do_get_users)
        except Exception as e:
            logger.error(f"Error fetching all users: {e}")
            return []

    def get_pending_transactions(self):
        try:
            def do_get_transactions():
                records = self.transactions_sheet.get_all_records()
                return [row for row in records if "PENDING" in row.get("transaction_id", "")]
            return self._retry_on_quota_exceeded(do_get_transactions)
        except Exception as e:
            logger.error(f"Error fetching pending transactions: {e}")
            return []

    def find_user_by_referral_code(self, referral_code):
        try:
            def do_find():
                records = self.users_sheet.get_all_records()
                for row in records:
                    if row.get("referral_code") == referral_code:
                        return row.get("UserID")
                return None
            return self._retry_on_quota_exceeded(do_find)
        except Exception as e:
            logger.error(f"Error finding user by referral code {referral_code}: {e}")
            return None

    def update_transaction_status(self, transaction_id, new_status):
        try:
            def do_update():
                cell = self.transactions_sheet.find(transaction_id)
                if cell:
                    row = cell.row
                    self.transactions_sheet.update_cell(row, 2, new_status)
                    logger.info(f"Updated transaction {transaction_id} to {new_status}")
            self._retry_on_quota_exceeded(do_update)
        except Exception as e:
            logger.error(f"Error updating transaction status for {transaction_id}: {e}")

sheet_manager_instance = SheetManager()

def get_sheet_manager():
    return sheet_manager_instance

def register_user(user_id, name, username, referrer_id):
    sheet_manager_instance.register_user(user_id, name, username, referrer_id)

def get_user_data(user_id):
    return sheet_manager_instance.get_user_data(user_id)

def update_user_tokens_points(user_id, tokens, points):
    sheet_manager_instance.update_user_tokens_points(user_id, tokens, points)

def reward_referrer(referrer_id, tokens):
    sheet_manager_instance.reward_referrer(referrer_id, tokens)

def log_token_purchase(user_id, transaction_id, amount, payment_method):
    sheet_manager_instance.log_token_purchase(user_id, transaction_id, amount, payment_method)

def increment_referral_count(referrer_id, referred_id):
    sheet_manager_instance.increment_referral_count(referrer_id, referred_id)

def log_point_redemption(user_id, reward):
    sheet_manager_instance.log_point_redemption(user_id, reward)

def update_user_momo(user_id, momo_number):
    sheet_manager_instance.update_user_momo(user_id, momo_number)

def check_and_give_daily_reward(user_id):
    return sheet_manager_instance.check_and_give_daily_reward(user_id)

def update_last_claim_date(user_id, date):
    sheet_manager_instance.update_last_claim_date(user_id, date)

def get_all_users():
    return sheet_manager_instance.get_all_users()

def get_pending_transactions():
    return sheet_manager_instance.get_pending_transactions()

def find_user_by_referral_code(referral_code):
    return sheet_manager_instance.find_user_by_referral_code(referral_code)

def update_transaction_status(transaction_id, new_status):
    sheet_manager_instance.update_transaction_status(transaction_id, new_status)
