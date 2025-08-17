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

    def get_user_data_flexible(self, user_id):
        """Get user data with flexible column mapping"""
        try:
            all_values = self.users_sheet.get_all_values()
            if not all_values:
                return None
                
            headers = all_values[0]
            
            # Create flexible mapping
            column_map = {}
            for i, header in enumerate(headers):
                header_lower = str(header).lower().strip()
                if 'userid' in header_lower or 'user_id' in header_lower:
                    column_map['UserID'] = i
                elif 'name' in header_lower and 'user' not in header_lower:
                    column_map['Name'] = i
                elif 'username' in header_lower:
                    column_map['Username'] = i
                elif 'tokens' in header_lower:
                    column_map['Tokens'] = i
                elif 'points' in header_lower:
                    column_map['Points'] = i
                elif 'momo' in header_lower or 'mobile' in header_lower:
                    column_map['MoMoNumber'] = i
                elif 'referral_code' in header_lower or 'referralcode' in header_lower:
                    column_map['referral_code'] = i
                elif 'referralearnings' in header_lower or 'referral_earnings' in header_lower:
                    column_map['ReferralEarnings'] = i
            
            # Use default positions if not found
            default_map = {
                'UserID': 0,
                'Name': 1,
                'Username': 2,
                'Tokens': 3,
                'Points': 4,
                'MoMoNumber': 5,
                'referral_code': 6,
                'ReferralEarnings': 7
            }
            
            # Merge with actual mapping
            final_map = {**default_map, **column_map}
            
            # Find user
            for row in all_values[1:]:
                if len(row) > final_map['UserID'] and str(row[final_map['UserID']]) == str(user_id):
                    return {
                        'UserID': str(row[final_map['UserID']]),
                        'Name': str(row[final_map['Name']]) if len(row) > final_map['Name'] else 'Unknown',
                        'Username': str(row[final_map['Username']]) if len(row) > final_map['Username'] else '',
                        'Tokens': float(row[final_map['Tokens']]) if len(row) > final_map['Tokens'] and str(row[final_map['Tokens']]).strip() else 0.0,
                        'Points': float(row[final_map['Points']]) if len(row) > final_map['Points'] and str(row[final_map['Points']]).strip() else 0.0,
                        'ReferralEarnings': float(row[final_map['ReferralEarnings']]) if len(row) > final_map['ReferralEarnings'] and str(row[final_map['ReferralEarnings']]).strip() else 0.0,
                        'MoMoNumber': str(row[final_map['MoMoNumber']]) if len(row) > final_map['MoMoNumber'] else '',
                        'referral_code': str(row[final_map['referral_code']]) if len(row) > final_map['referral_code'] else f"REF{str(user_id)[-6:]}"
                    }
            return None
        except Exception as e:
            logger.error(f"Error fetching user data for {user_id}: {e}")
            return None

sheet_manager_instance = SheetManager()

def get_sheet_manager():
    return sheet_manager_instance

def register_user(user_id, name, username, referrer_id):
    sheet_manager_instance.register_user(user_id, name, username, referrer_id)

def get_user_data(user_id):
    return sheet_manager_instance.get_user_data_flexible(user_id)

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
