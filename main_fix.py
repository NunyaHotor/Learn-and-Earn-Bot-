import os
import logging
import random
import time
import threading
import requests
import schedule
import traceback
from datetime import datetime, timezone
from dotenv import load_dotenv

from telebot import TeleBot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

from sheet_manager import (
    register_user,
    get_user_data,
    update_user_tokens_points,
    reward_referrer,
    log_token_purchase,
    increment_referral_count,
    log_point_redemption,
    update_user_momo,
    check_and_give_daily_reward,
    get_sheet_manager,
    find_user_by_referral_code,
    update_transaction_status
)
from translation_service import translation_service
from exchange_rate_service import exchange_rate_service
from ui_enhancer import ui_enhancer
from user_preference_service import user_preference_service

# --- Setup ---
load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

API_KEY = os.getenv("TELEGRAM_API_KEY") or "YOUR_FALLBACK_API_KEY"
bot = TeleBot(API_KEY, parse_mode='HTML')

# FIX: Make admin IDs configurable via environment variable
ADMIN_CHAT_IDS = [int(id.strip()) for id in os.getenv("ADMIN_CHAT_IDS", "2145372547").split(",") if id.strip()]

USD_TO_CEDIS_RATE = exchange_rate_service.get_rate()
PAYSTACK_LINK = "https://paystack.shop/pay/6yjmo6ykwr"

# ... (keep all existing constants and data structures the same) ...

# --- Utility Functions ---
def is_admin(user_id):
    """Check if user is admin - now supports multiple admin IDs"""
    return int(user_id) in ADMIN_CHAT_IDS

# FIX: Add proper error handling for zone quiz
def get_random_zone_quiz(user_id, zone):
    """Get random quiz for specified zone with better error handling"""
    try:
        if zone not in ZONE_QUIZZES:
            logger.error(f"Invalid zone requested: {zone}")
            return None
            
        if user_id not in zone_question_pools:
            zone_question_pools[user_id] = {}
            
        if zone not in zone_question_pools[user_id]:
            zone_question_pools[user_id][zone] = []
            
        used_questions = zone_question_pools[user_id][zone]
        available_questions = [q for q in ZONE_QUIZZES[zone] if q['q'] not in used_questions]
        
        if not available_questions:
            zone_question_pools[user_id][zone] = []
            available_questions = ZONE_QUIZZES[zone]
            
        selected_quiz = random.choice(available_questions)
        zone_question_pools[user_id][zone].append(selected_quiz['q'])
        return selected_quiz
        
    except Exception as e:
        logger.error(f"Error getting zone quiz: {e}")
        return None

# FIX: Improve zone selection handler
@bot.message_handler(func=lambda message: message.text in ZONE_QUIZZES.keys())
def zone_selection_handler(message):
    """Handle zone selection with proper validation"""
    chat_id = message.chat.id
    zone = message.text
    
    if zone not in ZONE_QUIZZES:
        bot.send_message(chat_id, "❌ Invalid zone selected. Please choose from the available zones.")
        send_zone_menu(chat_id)
        return
    
    # Store selected zone
    user_selected_zone[chat_id] = zone
    
    # Send language selection
    send_language_menu(chat_id)
    
    # Send confirmation
    bot.send_message(chat_id, f"✅ Zone selected: {zone}\nNow choose your preferred language:")

# FIX: Improve language selection handler
@bot.message_handler(func=lambda message: message.text in ["English", "French", "Swahili", "Arabic"])
def language_selection_handler(message):
    """Handle language selection with proper zone validation"""
    chat_id = message.chat.id
    
    # Validate zone selection
    if chat_id not in user_selected_zone:
        bot.send_message(chat_id, "❌ Please select a zone first.")
        send_zone_menu(chat_id)
        return
    
    zone = user_selected_zone[chat_id]
    if zone not in ZONE_QUIZZES:
        bot.send_message(chat_id, "❌ Invalid zone. Please select again.")
        send_zone_menu(chat_id)
        return
    
    # Store language selection
    user_selected_language[chat_id] = message.text
    
    # Start zone quiz
    user_quiz_mode[chat_id] = "zone"
    start_new_quiz(chat_id, "zone")

# FIX: Improve start_new_quiz with better error handling
def start_new_quiz(chat_id, mode):
    """Start new quiz with comprehensive error handling"""
    try:
        user = get_user_data(chat_id)
        if not user:
            bot.send_message(chat_id, "Please /start first.")
            return
            
        if float(user['Tokens']) <= 0:
            bot.send_message(chat_id, "⚠️ You don't have any tokens! Use '💰 Buy Tokens' to continue playing.")
            return
            
        if chat_id in paused_games:
            markup = InlineKeyboardMarkup()
            markup.add(
                InlineKeyboardButton("▶️ Resume Game", callback_data="resume_game"),
                InlineKeyboardButton("🎮 New Game", callback_data="new_game")
            )
            bot.send_message(chat_id, "⏸️ You have a paused game. Would you like to resume or start a new one?", reply_markup=markup)
            return
            
        # Get appropriate quiz based on mode
        if mode == "general":
            quiz = get_random_general_quiz(chat_id)
            zone_name = "General"
        else:  # zone mode
            zone = user_selected_zone.get(chat_id, "West Africa")
            quiz = get_random_zone_quiz(chat_id, zone)
            zone_name = zone
            
        if not quiz:
            bot.send_message(chat_id, "❌ Error loading quiz questions. Please try again later.")
            return
            
        # Get language preference
        lang = user_selected_language.get(chat_id, "English")
        lang_code = {"English": "en", "French": "fr", "Swahili": "sw", "Arabic": "ar"}[lang]
        
        # Prepare question
        question = translation_service.translate_text(quiz['q'], lang_code)
        choices = [translation_service.translate_text(c, lang_code) for c in quiz['choices']]
        correct = translation_service.translate_text(quiz['a'], lang_code)
        
        current_question[chat_id] = {
            'correct': correct,
            'question': question,
            'choices': choices,
            'skipped': False,
            'mode': mode,
            'original_answer': quiz['a']
        }
        
        # Create answer markup
        answer_markup = InlineKeyboardMarkup()
        for choice in choices:
            answer_markup.add(InlineKeyboardButton(choice, callback_data=f"answer:{choice}"))
        answer_markup.add(
            InlineKeyboardButton("⏭️ Skip", callback_data="skip_question"), 
            InlineKeyboardButton("⏸️ Pause", callback_data="pause_game")
        )
        
        # Send question
        bot.send_message(
            chat_id, 
            f"🧠 <b>{zone_name} Quiz:</b>\n{question}", 
            reply_markup=answer_markup
        )
        
    except Exception as e:
        logger.error(f"Error starting quiz: {e}")
        bot.send_message(chat_id, "❌ An error occurred while starting the quiz. Please try again.")

# FIX: Add proper admin menu creation
def create_admin_menu():
    """Create admin menu with proper formatting"""
    markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
    
    # Create rows for better organization
    markup.add(
        KeyboardButton("📊 Admin Dashboard"),
        KeyboardButton("📋 View Pending Tokens")
    )
    markup.add(
        KeyboardButton("✅ Approve Token Purchase"),
        KeyboardButton("📢 Broadcast Message")
    )
    markup.add(
        KeyboardButton("📈 User Stats"),
        KeyboardButton("🎯 Run Daily Lottery")
    )
    markup.add(
        KeyboardButton("🎰 Run Weekly Raffle"),
        KeyboardButton("🔙 Back to User Menu")
    )
    
    return markup

# FIX: Add admin check decorator for message handlers
def admin_only(func):
    """Decorator to ensure only admins can access certain functions"""
    def wrapper(message):
        if not is_admin(message.chat.id):
            bot.send_message(message.chat.id, "❌ Unauthorized access.")
            return
        return func(message)
    return wrapper

# Apply admin checks to admin functions
@bot.message_handler(func=lambda message: message.text == "📊 Admin Dashboard")
@admin_only
def admin_dashboard_handler(message):
    chat_id = message.chat.id
    try:
        sheet_manager = get_sheet_manager()
        users = sheet_manager.get_all_users()
        total_users = len(users)
        total_tokens = sum(float(user.get('Tokens', 0)) for user in users)
        total_points = sum(float(user.get('Points', 0)) for user in users)
        total_referrals = sum(int(user.get('ReferralEarnings', 0)) for user in users)
        pending_transactions = sheet_manager.get_pending_transactions()
        
        dashboard_message = f"""
📊 <b>Admin Dashboard</b>

👥 <b>Total Users:</b> {total_users}
💰 <b>Total Tokens Distributed:</b> {total_tokens}
🎯 <b>Total Points Earned:</b> {total_points}
👥 <b>Total Referrals:</b> {total_referrals}
📋 <b>Pending Token Purchases:</b> {len(pending_transactions)}
        """
        bot.send_message(chat_id, dashboard_message, reply_markup=create_admin_menu())
    except Exception as e:
        logger.error(f"Error in admin dashboard: {e}")
        bot.send_message(chat_id, "❌ Error loading dashboard data.")

# ... (keep all other handlers the same but add admin checks) ...

# FIX: Add environment variable support for admin configuration
if __name__ == "__main__":
    # Log admin configuration
    logger.info(f"Admin IDs configured: {ADMIN_CHAT_IDS}")
    
    threading.Thread(target=run_scheduler, daemon=True).start()
    
    # Delete webhook before starting polling
    try:
        bot.delete_webhook()
        logger.info("Webhook deleted successfully. Starting polling...")
    except Exception as e:
        logger.warning(f"Could not delete webhook: {e}")
    
    retry_count = 0
    max_retries = 5
    while retry_count < max_retries:
        try:
            bot.polling(none_stop=True, timeout=60, long_polling_timeout=60)
            break
        except requests.exceptions.ReadTimeout as e:
            logger.error(f"ReadTimeout error: {e}")
            retry_count += 1
            logger.info(f"Retrying ({retry_count}/{max_retries}) in 10 seconds...")
            time.sleep(10)
        except Exception as e:
            logger.error(f"Bot polling error: {e}\n{traceback.format_exc()}")
            retry_count += 1
            logger.info(f"Retrying ({retry_count}/{max_retries}) in 10 seconds...")
            time.sleep(10)
    if retry_count >= max_retries:
        logger.error("Max retries reached. Bot polling stopped.")
