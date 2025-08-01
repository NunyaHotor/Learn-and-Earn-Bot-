
"""
Google Sheets Manager for Learn4Cash Bot

This module handles all Google Sheets operations for user data management,
token purchases, and redemption tracking.
"""

import logging
import os
from typing import Optional, Dict, Any, List
from datetime import datetime

import gspread
from google.oauth2.service_account import Credentials
from gspread.exceptions import APIError, WorksheetNotFound, SpreadsheetNotFound

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"# modern_quiz_bot.py
    import random
    import telebot
    from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
    from datetime import datetime

    from sheet_manager import (
        register_user,
        get_user_data,
        update_user_tokens_points,
        reward_referrer,
        log_token_purchase,
        increment_referral_count,
        log_point_redemption  # ensure this exists in sheet_manager.py
    )

    API_KEY = "8470972230:AAFs4wYw94DOiXk2TLpyM0iKlfXLL78JdBE"
    bot = telebot.TeleBot(API_KEY, parse_mode='HTML')

    quizzes = [
        {"q": "Who was Ghana’s first president?", "a": "Kwame Nkrumah", "choices": ["Kwame Nkrumah", "Rawlings", "Mahama", "Busia"]},
        {"q": "When did Ghana gain independence?", "a": "1957", "choices": ["1945", "1957", "1960", "1966"]},
        {"q": "What is the capital of Ghana?", "a": "Accra", "choices": ["Kumasi", "Tamale", "Accra", "Ho"]},
        {"q": "Which region is Lake Volta in?", "a": "Volta", "choices": ["Ashanti", "Volta", "Northern", "Bono"]},
        {"q": "Who led the 1948 Accra Riots?", "a": "The Big Six", "choices": ["Yaa Asantewaa", "The Big Six", "Danquah", "Rawlings"]},
        {"q": "What is the largest country in Africa by land area?", "a": "Algeria", "choices": ["Nigeria", "Algeria", "Egypt", "South Africa"]},
        {"q": "Which African country has the most pyramids?", "a": "Sudan", "choices": ["Egypt", "Sudan", "Ethiopia", "Libya"]},
        {"q": "What is the official language of Angola?", "a": "Portuguese", "choices": ["French", "Portuguese", "English", "Spanish"]},
        {"q": "Which African river is the longest?", "a": "Nile", "choices": ["Congo", "Niger", "Zambezi", "Nile"]},
        {"q": "Which African country is known as the Rainbow Nation?", "a": "South Africa", "choices": ["Ghana", "South Africa", "Kenya", "Tanzania"]},
        {"q": "Which African island nation lies off the southeast coast of Africa?", "a": "Madagascar", "choices": ["Seychelles", "Mauritius", "Madagascar", "Comoros"]},
        {"q": "What is the largest desert in Africa?", "a": "Sahara", "choices": ["Namib", "Sahara", "Kalahari", "Gobi"]},
        {"q": "Which African country was never colonized?", "a": "Ethiopia", "choices": ["Ghana", "Liberia", "Ethiopia", "Morocco"]},
        {"q": "Which African country produces the most cocoa?", "a": "Côte d'Ivoire", "choices": ["Ghana", "Nigeria", "Cameroon", "Côte d'Ivoire"]},
        {"q": "What is the currency of Nigeria?", "a": "Naira", "choices": ["Cedi", "Shilling", "Rand", "Naira"]}
    ]

    pending_momo = {}
    current_question = {}

    TOKEN_PRICING = {
        "1 token (₵2 or $0.20)": {"amount": 1, "price": "2 GHS / 0.20 USD"},
        "5 tokens (₵9 or $0.90)": {"amount": 5, "price": "9 GHS / 0.90 USD"},
        "10 tokens (₵17 or $1.70)": {"amount": 10, "price": "17 GHS / 1.70 USD"}
    }

    REDEEM_OPTIONS = {
        "1 Token": {"points": 100, "reward": "+1 Token"},
        "GHS 5 Airtime": {"points": 250, "reward": "GHS 5 Airtime"},
        "GHS 10 Airtime": {"points": 400, "reward": "GHS 10 Airtime"},
        "5 USDT": {"points": 800, "reward": "5 USDT (Crypto)"}
    }

    PAYMENT_LINKS = {
        "momo": "https://paystack.com/pay/momo-learn4cash",
        "crypto": "https://buycrypto.learn4cash.io"
    }

    PAYMENT_INFO = """
    💸 <b>Payment Instructions</b>

    📲 <b>MoMo</b>: Send payment to <b>0551234567</b> (Learn4Cash)
    🔗 Or pay via: <a href='{momo_link}'>MoMo Online Payment</a>

    💰 <b>Crypto (USDT)</b>: <code>0xYourCryptoWalletAddress</code>
    🔗 Or pay via: <a href='{crypto_link}'>Crypto Payment</a>

    📬 After sending payment, send your screenshot to @Learn4CashAdmin.
    """.format(momo_link=PAYMENT_LINKS['momo'], crypto_link=PAYMENT_LINKS['crypto'])


    @bot.message_handler(commands=['redeem'])
    def redeem_handler(message):
        user = get_user_data(message.chat.id)
        if not user:
            bot.send_message(message.chat.id, "Please /start first.")
            return

        points = user['Points']
        markup = InlineKeyboardMarkup()
        for label, reward in REDEEM_OPTIONS.items():
            if points >= reward['points']:
                markup.add(InlineKeyboardButton(text=f"{label} ({reward['points']} pts)", callback_data=f"redeem:{label}"))
        if markup.keyboard:
            bot.send_message(message.chat.id, "🏭 Choose a reward to redeem:", reply_markup=markup)
        else:
            bot.send_message(message.chat.id, "⚠️ You don't have enough points to redeem any rewards yet.")


    @bot.callback_query_handler(func=lambda call: call.data.startswith("redeem:"))
    def redeem_callback_handler(call):
        chat_id = call.message.chat.id
        label = call.data.split("redeem:")[1]
        reward = REDEEM_OPTIONS[label]
        user = get_user_data(chat_id)

        if user['Points'] < reward['points']:
            bot.send_message(chat_id, "❌ You do not have enough points.")
            return

        new_points = user['Points'] - reward['points']
        update_user_tokens_points(chat_id, user['Tokens'], new_points)

        try:
            log_point_redemption(chat_id, label, reward['points'], datetime.utcnow().isoformat())
        except Exception as e:
            print("[ERROR] Failed to log redemption:", e)

        bot.answer_callback_query(call.id)
        bot.send_message(chat_id, f"✅ You've redeemed <b>{label}</b>. Admin will process your reward soon.")
        bot.send_message(chat_id, "📬 Please send your details/screenshot to @Learn4CashAdmin for confirmation.")

]

CREDENTIALS_FILE = "learn4cash-key.json"
SPREADSHEET_NAME = "Learn4Cash_Users"
MAIN_SHEET_NAME = "Sheet1"
TOKEN_LOG_SHEET_NAME = "TokenLog"
REDEMPTIONS_SHEET_NAME = "Redemptions"

# Column indices (1-based for Google Sheets)
class UserColumns:
    USER_ID = 1
    NAME = 2
    USERNAME = 3
    TOKENS = 4
    POINTS = 5
    REFERRER_ID = 6
    REFERRAL_EARNINGS = 7
    MOMO_NUMBER = 8

DEFAULT_USER_TOKENS = 3
REFERRAL_BONUS_TOKENS = 1


class SheetManager:
    """Manages Google Sheets operations for the Learn4Cash bot."""
    
    def __init__(self):
        """Initialize the SheetManager with Google Sheets client."""
        self.client = None
        self.spreadsheet = None
        self.main_sheet = None
        self._initialize_client()
    
    def _initialize_client(self) -> None:
        """Initialize Google Sheets client and verify access."""
        try:
            if not os.path.exists(CREDENTIALS_FILE):
                raise FileNotFoundError(f"Credentials file not found: {CREDENTIALS_FILE}")
            
            creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=SCOPES)
            self.client = gspread.authorize(creds)
            self.spreadsheet = self.client.open(SPREADSHEET_NAME)
            self.main_sheet = self.spreadsheet.sheet1
            
            logger.info("Successfully initialized Google Sheets client")
            
        except (FileNotFoundError, SpreadsheetNotFound) as e:
            logger.error(f"Failed to initialize Google Sheets client: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error initializing client: {e}")
            raise
    
    def _get_user_row(self, user_id: int) -> Optional[int]:
        """
        Get the row number for a specific user.
        
        Args:
            user_id: The Telegram user ID
            
        Returns:
            Row number (1-based) if user exists, None otherwise
        """
        try:
            records = self.main_sheet.get_all_records()
            for idx, row in enumerate(records):
                if str(row.get('UserID', '')) == str(user_id):
                    return idx + 2  # 1-based indexing + header row
            return None
            
        except APIError as e:
            logger.error(f"API error getting user row for {user_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error getting user row for {user_id}: {e}")
            return None
    
    def register_user(self, user_id: int, name: str, username: str = "", 
                     referrer_id: Optional[int] = None, momo_number: str = "") -> bool:
        """
        Register a new user in the system.
        
        Args:
            user_id: Telegram user ID
            name: User's display name
            username: Telegram username (optional)
            referrer_id: ID of the user who referred this user (optional)
            momo_number: Mobile money number (optional)
            
        Returns:
            True if registration successful, False if user already exists
        """
        try:
            # Check if user already exists
            if self._get_user_row(user_id):
                logger.info(f"User {user_id} already registered")
                return False
            
            new_row = [
                user_id,
                name,
                username or '',
                DEFAULT_USER_TOKENS,
                0,  # Initial points
                referrer_id or '',
                0,  # Initial referral earnings
                momo_number
            ]
            
            self.main_sheet.append_row(new_row)
            logger.info(f"Successfully registered user {user_id}")
            return True
            
        except APIError as e:
            logger.error(f"API error registering user {user_id}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error registering user {user_id}: {e}")
            return False
    
    def get_user_data(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Get user data from the spreadsheet.
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            Dictionary with user data or None if user not found
        """
        try:
            row_num = self._get_user_row(user_id)
            if not row_num:
                logger.warning(f"User {user_id} not found")
                return None
            
            data = self.main_sheet.row_values(row_num)
            
            # Ensure we have enough columns
            while len(data) < UserColumns.MOMO_NUMBER:
                data.append("")
            
            return {
                "UserID": data[0],
                "Name": data[1],
                "Username": data[2],
                "Tokens": self._safe_int(data[3], 0),
                "Points": self._safe_int(data[4], 0),
                "ReferrerID": data[5],
                "ReferralEarnings": self._safe_float(data[6], 0.0),
                "MoMoNumber": data[7] if len(data) > 7 else ""
            }
            
        except APIError as e:
            logger.error(f"API error getting user data for {user_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error getting user data for {user_id}: {e}")
            return None
    
    def update_user_tokens_points(self, user_id: int, tokens: int, points: int) -> bool:
        """
        Update user's tokens and points.
        
        Args:
            user_id: Telegram user ID
            tokens: New token count
            points: New points count
            
        Returns:
            True if update successful, False otherwise
        """
        try:
            row_num = self._get_user_row(user_id)
            if not row_num:
                logger.warning(f"Cannot update tokens/points: User {user_id} not found")
                return False
            
            # Update tokens and points in a batch
            updates = [
                {'range': f'D{row_num}', 'values': [[tokens]]},
                {'range': f'E{row_num}', 'values': [[points]]}
            ]
            
            self.main_sheet.batch_update(updates)
            logger.info(f"Updated tokens/points for user {user_id}: {tokens} tokens, {points} points")
            return True
            
        except APIError as e:
            logger.error(f"API error updating tokens/points for {user_id}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error updating tokens/points for {user_id}: {e}")
            return False
    
    def update_user_momo(self, user_id: int, momo_number: str) -> bool:
        """
        Update user's mobile money number.
        
        Args:
            user_id: Telegram user ID
            momo_number: Mobile money number
            
        Returns:
            True if update successful, False otherwise
        """
        try:
            row_num = self._get_user_row(user_id)
            if not row_num:
                logger.warning(f"Cannot update MoMo: User {user_id} not found")
                return False
            
            self.main_sheet.update_cell(row_num, UserColumns.MOMO_NUMBER, momo_number)
            logger.info(f"Updated MoMo number for user {user_id}")
            return True
            
        except APIError as e:
            logger.error(f"API error updating MoMo for {user_id}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error updating MoMo for {user_id}: {e}")
            return False
    
    def log_token_purchase(self, user_id: int, label: str, quantity: int) -> bool:
        """
        Log a token purchase to the TokenLog sheet.
        
        Args:
            user_id: Telegram user ID
            label: Purchase label/description
            quantity: Number of tokens purchased
            
        Returns:
            True if logging successful, False otherwise
        """
        try:
            token_sheet = self._get_or_create_worksheet(TOKEN_LOG_SHEET_NAME)
            if not token_sheet:
                return False
            
            timestamp = datetime.utcnow().isoformat()
            row = [str(user_id), label, quantity, timestamp]
            token_sheet.append_row(row)
            
            logger.info(f"Logged token purchase for user {user_id}: {label} ({quantity} tokens)")
            return True
            
        except APIError as e:
            logger.error(f"API error logging token purchase for {user_id}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error logging token purchase for {user_id}: {e}")
            return False
    
    def increment_referral_count(self, referrer_id: int) -> bool:
        """
        Increment the referral count for a user.
        
        Args:
            referrer_id: ID of the user who made the referral
            
        Returns:
            True if increment successful, False otherwise
        """
        try:
            row_num = self._get_user_row(referrer_id)
            if not row_num:
                logger.warning(f"Cannot increment referral: User {referrer_id} not found")
                return False
            
            current_count = self.main_sheet.cell(row_num, UserColumns.REFERRAL_EARNINGS).value
            new_count = self._safe_float(current_count, 0.0) + 1.0
            
            self.main_sheet.update_cell(row_num, UserColumns.REFERRAL_EARNINGS, new_count)
            logger.info(f"Incremented referral count for user {referrer_id}")
            return True
            
        except APIError as e:
            logger.error(f"API error incrementing referral count for {referrer_id}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error incrementing referral count for {referrer_id}: {e}")
            return False
    
    def log_point_redemption(self, user_id: int, reward: str, points_used: int, timestamp: str) -> bool:
        """
        Log a point redemption to the Redemptions sheet.
        
        Args:
            user_id: Telegram user ID
            reward: Description of the reward
            points_used: Number of points used
            timestamp: ISO timestamp of redemption
            
        Returns:
            True if logging successful, False otherwise
        """
        try:
            redemption_sheet = self._get_or_create_worksheet(
                REDEMPTIONS_SHEET_NAME,
                headers=["UserID", "Reward", "PointsUsed", "Timestamp", "Status"]
            )
            if not redemption_sheet:
                return False
            
            row = [user_id, reward, points_used, timestamp, "Pending"]
            redemption_sheet.append_row(row)
            
            logger.info(f"Logged point redemption for user {user_id}: {reward} ({points_used} points)")
            return True
            
        except APIError as e:
            logger.error(f"API error logging point redemption for {user_id}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error logging point redemption for {user_id}: {e}")
            return False
    
    def reward_referrer(self, referrer_id: int) -> bool:
        """
        Reward a user for successful referral by adding tokens.
        
        Args:
            referrer_id: ID of the user who made the referral
            
        Returns:
            True if reward successful, False otherwise
        """
        try:
            row_num = self._get_user_row(referrer_id)
            if not row_num:
                logger.warning(f"Cannot reward referrer: User {referrer_id} not found")
                return False
            
            current_tokens = self.main_sheet.cell(row_num, UserColumns.TOKENS).value
            new_tokens = self._safe_int(current_tokens, 0) + REFERRAL_BONUS_TOKENS
            
            self.main_sheet.update_cell(row_num, UserColumns.TOKENS, new_tokens)
            logger.info(f"Rewarded referrer {referrer_id} with {REFERRAL_BONUS_TOKENS} tokens")
            return True
            
        except APIError as e:
            logger.error(f"API error rewarding referrer {referrer_id}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error rewarding referrer {referrer_id}: {e}")
            return False
    
    def _get_or_create_worksheet(self, sheet_name: str, headers: Optional[List[str]] = None):
        """
        Get an existing worksheet or create a new one if it doesn't exist.
        
        Args:
            sheet_name: Name of the worksheet
            headers: Optional list of header row values
            
        Returns:
            Worksheet object or None if creation failed
        """
        try:
            return self.spreadsheet.worksheet(sheet_name)
        except WorksheetNotFound:
            try:
                new_sheet = self.spreadsheet.add_worksheet(
                    title=sheet_name, 
                    rows="1000", 
                    cols="10"
                )
                if headers:
                    new_sheet.insert_row(headers, 1)
                logger.info(f"Created new worksheet: {sheet_name}")
                return new_sheet
            except APIError as e:
                logger.error(f"Failed to create worksheet {sheet_name}: {e}")
                return None
    
    @staticmethod
    def _safe_int(value: Any, default: int = 0) -> int:
        """Safely convert value to integer."""
        try:
            if isinstance(value, str) and value.isdigit():
                return int(value)
            elif isinstance(value, (int, float)):
                return int(value)
            return default
        except (ValueError, TypeError):
            return default
    
    @staticmethod
    def _safe_float(value: Any, default: float = 0.0) -> float:
        """Safely convert value to float."""
        try:
            if value:
                return float(value)
            return default
        except (ValueError, TypeError):
            return default


# Global instance
_sheet_manager = None


def get_sheet_manager() -> SheetManager:
    """Get the global SheetManager instance."""
    global _sheet_manager
    if _sheet_manager is None:
        _sheet_manager = SheetManager()
    return _sheet_manager


# Backward compatibility functions
def register_user(user_id: int, name: str, username: str = "", 
                 referrer_id: Optional[int] = None, momo_number: str = "") -> bool:
    """Register a new user (backward compatibility)."""
    return get_sheet_manager().register_user(user_id, name, username, referrer_id, momo_number)


def get_user_data(user_id: int) -> Optional[Dict[str, Any]]:
    """Get user data (backward compatibility)."""
    return get_sheet_manager().get_user_data(user_id)


def update_user_tokens_points(user_id: int, tokens: int, points: int) -> bool:
    """Update user tokens and points (backward compatibility)."""
    return get_sheet_manager().update_user_tokens_points(user_id, tokens, points)


def update_user_momo(user_id: int, momo_number: str) -> bool:
    """Update user MoMo number (backward compatibility)."""
    return get_sheet_manager().update_user_momo(user_id, momo_number)


def log_token_purchase(user_id: int, label: str, quantity: int) -> bool:
    """Log token purchase (backward compatibility)."""
    return get_sheet_manager().log_token_purchase(user_id, label, quantity)


def increment_referral_count(referrer_id: int) -> bool:
    """Increment referral count (backward compatibility)."""
    return get_sheet_manager().increment_referral_count(referrer_id)


def log_point_redemption(user_id: int, reward: str, points_used: int, timestamp: str) -> bool:
    """Log point redemption (backward compatibility)."""
    return get_sheet_manager().log_point_redemption(user_id, reward, points_used, timestamp)


def reward_referrer(referrer_id: int) -> bool:
    """Reward referrer (backward compatibility)."""
    return get_sheet_manager().reward_referrer(referrer_id)
