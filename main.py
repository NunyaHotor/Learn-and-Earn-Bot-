#!/usr/bin/env python3
"""
Learn4Cash Main Application
Consolidated version with proper linking and safety checks
"""

import logging
import time
from typing import Dict, Any, Optional
from sheet_manager import (
    get_user_data, update_user_tokens_points, reward_referrer,
    log_token_purchase, increment_referral_count, log_point_redemption,
    update_user_momo, check_and_give_daily_reward, update_last_claim_date,
    get_all_users, get_pending_transactions, find_user_by_referral_code,
    update_transaction_status, register_user
)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_user_data_safe(user_id: str) -> Dict[str, Any]:
    """
    Safe wrapper for get_user_data that handles None returns
    
    Args:
        user_id: The user ID to fetch data for
        
    Returns:
        Dict containing user data with safe defaults
    """
    user = get_user_data(user_id)
    if user is None:
        # Return default values if user not found
        return {
            'UserID': str(user_id),
            'Name': 'Unknown',
            'Username': '',
            'Tokens': 0,
            'Points': 0,
            'ReferralEarnings': 0,
            'MoMoNumber': '',
            'referral_code': f"REF{str(user_id)[-6:]}"
        }
    return user

def validate_user_exists(user_id: str) -> bool:
    """
    Check if a user exists in the system
    
    Args:
        user_id: The user ID to check
        
    Returns:
        True if user exists, False otherwise
    """
    user = get_user_data(user_id)
    return user is not None

def get_user_balance(user_id: str) -> Dict[str, float]:
    """
    Get user's current token and point balance
    
    Args:
        user_id: The user ID to check balance for
        
    Returns:
        Dict with 'tokens' and 'points' keys
    """
    user = get_user_data_safe(user_id)
    return {
        'tokens': float(user.get('Tokens', 0)),
        'points': float(user.get('Points', 0))
    }

def process_referral_reward(referrer_id: str, referred_id: str, reward_amount: float = 10.0) -> bool:
    """
    Process referral reward for both referrer and referred
    
    Args:
        referrer_id: The user who made the referral
        referred_id: The new user who was referred
        reward_amount: Amount of tokens to reward
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Reward the referrer
        reward_referrer(referrer_id, reward_amount)
        
        # Increment referral count
        increment_referral_count(referrer_id, referred_id)
        
        # Log the referral transaction
        log_token_purchase(
            user_id=referrer_id,
            transaction_id=f"REFERRAL_{referred_id}_{int(time.time())}",
            amount=reward_amount,
            payment_method="referral"
        )
        
        return True
    except Exception as e:
        logger.error(f"Error processing referral reward: {e}")
        return False

def update_user_profile(user_id: str, updates: Dict[str, Any]) -> bool:
    """
    Update user profile with given updates
    
    Args:
        user_id: The user ID to update
        updates: Dict of fields to update
        
    Returns:
        True if successful, False otherwise
    """
    try:
        user = get_user_data_safe(user_id)
        
        # Update tokens and points if provided
        if 'tokens' in updates:
            update_user_tokens_points(user_id, updates['tokens'], user.get('Points', 0))
        
        if 'points' in updates:
            update_user_tokens_points(user_id, user.get('Tokens', 0), updates['points'])
        
        if 'momo_number' in updates:
            update_user_momo(user_id, updates['momo_number'])
        
        return True
    except Exception as e:
        logger.error(f"Error updating user profile: {e}")
        return False

# Export commonly used functions
__all__ = [
    'get_user_data_safe',
    'validate_user_exists',
    'get_user_balance',
    'process_referral_reward',
    'update_user_profile',
    'get_user_data',
    'update_user_tokens_points',
    'reward_referrer',
    'log_token_purchase',
    'increment_referral_count',
    'log_point_redemption',
    'update_user_momo',
    'check_and_give_daily_reward',
    'update_last_claim_date',
    'get_all_users',
    'get_pending_transactions',
    'find_user_by_referral_code',
    'update_transaction_status',
    'register_user'
]

if __name__ == "__main__":
    # Test the refactored system
    logger.info("Learn4Cash Main Application - Refactored Version")
    
    # Example usage
    test_user_id = "123456789"
    user_data = get_user_data_safe(test_user_id)
    logger.info(f"Test user data: {user_data}")
