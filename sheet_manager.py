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
    "https://www.googleapis.com/auth/drive"
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
    LAST_CLAIM_DATE = 9

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
                momo_number,
                ''  # Last claim date
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
            while len(data) < UserColumns.LAST_CLAIM_DATE:
                data.append("")

            return {
                "UserID": data[0],
                "Name": data[1],
                "Username": data[2],
                "Tokens": self._safe_int(data[3], 0),
                "Points": self._safe_int(data[4], 0),
                "ReferrerID": data[5],
                "ReferralEarnings": self._safe_float(data[6], 0.0),
                "MoMoNumber": data[7] if len(data) > 7 else "",
                "LastClaimDate": data[8] if len(data) > 8 else ""
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

    def log_token_purchase(self, user_id: int, label: str, quantity: int, payment_method: str = None) -> bool:
        """
        Log a token purchase to the TokenLog sheet.

        Args:
            user_id: Telegram user ID
            label: Purchase label/description
            quantity: Number of tokens purchased
            payment_method: Payment method used (optional)

        Returns:
            True if logging successful, False otherwise
        """
        try:
            token_sheet = self._get_or_create_worksheet(
                TOKEN_LOG_SHEET_NAME,
                headers=["UserID", "TransactionType", "Quantity", "Timestamp", "PaymentMethod", "Status"]
            )
            if not token_sheet:
                return False

            timestamp = datetime.utcnow().isoformat()
            row = [str(user_id), label, quantity, timestamp, payment_method or 'N/A', 'Completed']
            token_sheet.append_row(row)

            logger.info(f"Logged token transaction for user {user_id}: {label} ({quantity} tokens) via {payment_method or 'N/A'}")
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

    def check_and_give_daily_reward(self, user_id: int) -> bool:
        """
        Check if user can claim daily reward and give it if eligible.

        Args:
            user_id: Telegram user ID

        Returns:
            True if reward was given, False if already claimed today
        """
        try:
            row_num = self._get_user_row(user_id)
            if not row_num:
                logger.warning(f"Cannot give daily reward: User {user_id} not found")
                return False

            # Get current date
            today = datetime.utcnow().strftime("%Y-%m-%d")
            
            # Get last claim date
            last_claim_cell = self.main_sheet.cell(row_num, UserColumns.LAST_CLAIM_DATE)
            last_claim = last_claim_cell.value or ""

            # Check if already claimed today
            if last_claim == today:
                return False

            # Give daily reward (1 token)
            current_tokens = self.main_sheet.cell(row_num, UserColumns.TOKENS).value
            new_tokens = self._safe_int(current_tokens, 0) + 1

            # Update tokens and last claim date in batch
            updates = [
                {'range': f'D{row_num}', 'values': [[new_tokens]]},
                {'range': f'I{row_num}', 'values': [[today]]}
            ]

            self.main_sheet.batch_update(updates)
            logger.info(f"Gave daily reward to user {user_id}: +1 token")
            return True

        except APIError as e:
            logger.error(f"API error giving daily reward to {user_id}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error giving daily reward to {user_id}: {e}")
            return False

    def update_last_claim_date(self, user_id: int) -> bool:
        """
        Update the last claim date for a user.

        Args:
            user_id: Telegram user ID

        Returns:
            True if update successful, False otherwise
        """
        try:
            row_num = self._get_user_row(user_id)
            if not row_num:
                logger.warning(f"Cannot update claim date: User {user_id} not found")
                return False

            today = datetime.utcnow().strftime("%Y-%m-%d")
            self.main_sheet.update_cell(row_num, UserColumns.LAST_CLAIM_DATE, today)
            logger.info(f"Updated last claim date for user {user_id}")
            return True

        except APIError as e:
            logger.error(f"API error updating claim date for {user_id}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error updating claim date for {user_id}: {e}")
            return False

    def get_all_users(self):
        """Get all user records for leaderboard and broadcasting."""
        try:
            records = self.main_sheet.get_all_records()
            return records
        except APIError as e:
            logger.error(f"API error getting all users: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error getting all users: {e}")
            return []

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


def log_token_purchase(user_id: int, label: str, quantity: int, payment_method: str = None) -> bool:
    """Log token purchase (backward compatibility)."""
    return get_sheet_manager().log_token_purchase(user_id, label, quantity, payment_method)


def increment_referral_count(referrer_id: int) -> bool:
    """Increment referral count (backward compatibility)."""
    return get_sheet_manager().increment_referral_count(referrer_id)


def log_point_redemption(user_id: int, reward: str, points_used: int, timestamp: str) -> bool:
    """Log point redemption (backward compatibility)."""
    return get_sheet_manager().log_point_redemption(user_id, reward, points_used, timestamp)


def reward_referrer(referrer_id: int) -> bool:
    """Reward referrer (backward compatibility)."""
    return get_sheet_manager().reward_referrer(referrer_id)


def check_and_give_daily_reward(user_id: int) -> bool:
    """Check and give daily reward (backward compatibility)."""
    return get_sheet_manager().check_and_give_daily_reward(user_id)


def update_last_claim_date(user_id: int) -> bool:
    """Update last claim date (backward compatibility)."""
    return get_sheet_manager().update_last_claim_date(user_id)


def get_all_users():
    """Get all users (backward compatibility)."""
    return get_sheet_manager().get_all_users()