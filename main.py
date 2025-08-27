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
from googletrans import Translator
from telebot import TeleBot, types
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from flask import Flask, request, abort

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
    update_transaction_status,
    get_pending_cleanup_submissions,
    find_cleanup_submission,
    approve_cleanup_submission,
    reject_cleanup_submission,
    sheet_manager_instance
)
from exchange_rate_service import exchange_rate_service
import quiz_manager
from quiz_manager import player_progress
from cleanup_handler import register_cleanup_handlers

# --- Setup ---
load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Parse admin IDs from environment variable
ADMIN_CHAT_IDS = [
    int(admin_id.strip())
    for admin_id in os.getenv("ADMIN_CHAT_IDS", "").split(",")
    if admin_id.strip().isdigit()
]

API_KEY = os.getenv("TELEGRAM_API_KEY") or "YOUR_FALLBACK_API_KEY"
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
NEWSDATA_API_KEY = os.getenv("NEWSDATA_API_KEY")
bot = TeleBot(API_KEY, parse_mode='HTML')
translator = Translator()
app = Flask(__name__)


USD_TO_CEDIS_RATE = 11.8
PAYSTACK_LINK = "https://paystack.shop/pay/6yjmo6ykwr"

TOKEN_PRICING = {
    "5 tokens": {"amount": 5, "price_cedis": 2, "price_usd": round(2/USD_TO_CEDIS_RATE, 2)},
    "15 tokens": {"amount": 15, "price_cedis": 5, "price_usd": round(5/USD_TO_CEDIS_RATE, 2)},
    "40 tokens": {"amount": 40, "price_cedis": 10, "price_usd": round(10/USD_TO_CEDIS_RATE, 2)}
}

REDEEM_OPTIONS = {
    "1 Token": {"points": 10, "reward": "+1 Token", "cedis": 0.4, "usd": round(0.4/USD_TO_CEDIS_RATE, 2), "tier": 1, "amount": 1, "category": "tokens"},
    "3 Tokens": {"points": 60, "reward": "+3 Tokens", "cedis": 1.2, "usd": round(1.2/USD_TO_CEDIS_RATE, 2), "tier": 1, "amount": 3, "category": "tokens"},
    "7 Tokens": {"points": 140, "reward": "+7 Tokens", "cedis": 2.8, "usd": round(2.8/USD_TO_CEDIS_RATE, 2), "tier": 1, "amount": 7, "category": "tokens"},
    "15 Tokens": {"points": 300, "reward": "+15 Tokens", "cedis": 6.0, "usd": round(6.0/USD_TO_CEDIS_RATE, 2), "tier": 2, "amount": 15, "category": "tokens"},
    "25 Tokens": {"points": 500, "reward": "+25 Tokens", "cedis": 10.0, "usd": round(10.0/USD_TO_CEDIS_RATE, 2), "tier": 2, "amount": 25, "category": "tokens"},
    "50 Tokens": {"points": 1000, "reward": "+50 Tokens", "cedis": 20.0, "usd": round(20.0/USD_TO_CEDIS_RATE, 2), "tier": 3, "amount": 50, "category": "tokens"},
    "100 Tokens": {"points": 2000, "reward": "+100 Tokens", "cedis": 40.0, "usd": round(40.0/USD_TO_CEDIS_RATE, 2), "tier": 4, "amount": 100, "category": "tokens"},
    
    "GHS 2 Airtime": {"points": 160, "reward": "GHS 2 Airtime", "cedis": 2, "usd": round(2/USD_TO_CEDIS_RATE, 2), "tier": 2, "category": "airtime"},
    "GHS 5 Airtime": {"points": 300, "reward": "GHS 5 Airtime", "cedis": 5, "usd": round(5/USD_TO_CEDIS_RATE, 2), "tier": 2, "category": "airtime"},
    "GHS 10 Airtime": {"points": 1000, "reward": "GHS 10 Airtime", "cedis": 10, "usd": round(10/USD_TO_CEDIS_RATE, 2), "tier": 3, "category": "airtime"},
    "GHS 20 Airtime": {"points": 1800, "reward": "GHS 20 Airtime", "cedis": 20, "usd": round(20/USD_TO_CEDIS_RATE, 2), "tier": 3, "category": "airtime"},
    
    "500MB Data": {"points": 200, "reward": "500MB Internet Data", "cedis": 3, "usd": round(3/USD_TO_CEDIS_RATE, 2), "tier": 2, "category": "data"},
    "1GB Data": {"points": 400, "reward": "1GB Internet Data", "cedis": 5, "usd": round(5/USD_TO_CEDIS_RATE, 2), "tier": 2, "category": "data"},
    "2GB Data": {"points": 700, "reward": "2GB Internet Data", "cedis": 8, "usd": round(8/USD_TO_CEDIS_RATE, 2), "tier": 2, "category": "data"},
    "5GB Data": {"points": 1200, "reward": "5GB Internet Data", "cedis": 15, "usd": round(15/USD_TO_CEDIS_RATE, 2), "tier": 3, "category": "data"},
    "10GB Data": {"points": 2000, "reward": "10GB Internet Data", "cedis": 25, "usd": round(25/USD_TO_CEDIS_RATE, 2), "tier": 3, "category": "data"},
    
    "GHS 10 MoMo": {"points": 1100, "reward": "GHS 10 MoMo", "cedis": 10, "usd": round(10/USD_TO_CEDIS_RATE, 2), "tier": 3, "category": "momo"},
    "GHS 20 MoMo": {"points": 2100, "reward": "GHS 20 MoMo", "cedis": 20, "usd": round(20/USD_TO_CEDIS_RATE, 2), "tier": 3, "category": "momo"},
    "GHS 50 MoMo": {"points": 5000, "reward": "GHS 50 MoMo", "cedis": 50, "usd": round(50/USD_TO_CEDIS_RATE, 2), "tier": 3, "category": "momo"},
    "GHS 100 MoMo": {"points": 10000, "reward": "GHS 100 MoMo", "cedis": 100, "usd": round(100/USD_TO_CEDIS_RATE, 2), "tier": 4, "category": "momo"},
    "GHS 200 MoMo": {"points": 20000, "reward": "GHS 200 MoMo", "cedis": 200, "usd": round(200/USD_TO_CEDIS_RATE, 2), "tier": 4, "category": "momo"},
    
    "Basic Phone": {"points": 8000, "reward": "Basic Smartphone", "cedis": 400, "usd": round(400/USD_TO_CEDIS_RATE, 2), "tier": 3, "category": "gadgets"},
    "Samsung Phone": {"points": 15000, "reward": "Samsung Galaxy A15", "cedis": 1200, "usd": round(1200/USD_TO_CEDIS_RATE, 2), "tier": 4, "category": "gadgets"},
    "iPhone": {"points": 35000, "reward": "iPhone 13", "cedis": 3500, "usd": round(3500/USD_TO_CEDIS_RATE, 2), "tier": 4, "category": "gadgets"},
    "Budget Laptop": {"points": 25000, "reward": "HP Laptop 14", "cedis": 2800, "usd": round(2800/USD_TO_CEDIS_RATE, 2), "tier": 4, "category": "gadgets"},
    "Gaming Laptop": {"points": 45000, "reward": "Gaming Laptop", "cedis": 5500, "usd": round(5500/USD_TO_CEDIS_RATE, 2), "tier": 4, "category": "gadgets"}
}

# Category definitions
REWARD_CATEGORIES = {
    "tokens": {"name": "🪙 Tokens", "description": "Exchange points for more quiz tokens"},
    "airtime": {"name": "📞 Airtime", "description": "Redeem mobile airtime credit"},
    "data": {"name": "📶 Data", "description": "Get internet data bundles"},
    "momo": {"name": "💰 MoMo", "description": "Mobile money transfers"},
    "gadgets": {"name": "📱 Gadgets", "description": "Premium electronics and devices"}
}

PAYMENT_INFO = """
⚖️ <b>Payment Instructions</b>

📲 <b>MTN MoMo Payment:</b>
• Make payment to MTN merchant ID: <b>474994</b>
• Name: <b>Sufex Technology</b>
• Direct Payment: <a href=\"https://paystack.shop/pay/6yjmo6ykwr\">Pay with Paystack</a>

<b>How to pay MTN MoMo:</b>
1. Dial *170# on your MTN phone
2. Select option 1 (Transfer Money)
3. Select option 3 (To Merchant)
4. Enter Merchant ID: 474994
5. Enter amount and confirm
6. Take screenshot of confirmation

💰 <b>Crypto (USDT TRC20):</b>
• Address: <code>TVd2gJT5Q1ncXqdPmsCFYaiizvgaWbLSGn</code>

<b>How to get USDT and pay:</b>
1. Download Trust Wallet or Binance app
2. Buy USDT using mobile money or bank card
3. Copy our wallet address above
4. Send USDT (choose TRC20 network)
5. Take screenshot of successful transaction

📧 Send payment screenshot to @LearnEarnAfricaAdmin for verification.
⃣ Tokens are added after payment confirmation!
"""

ABOUT_US = """
🎓 <b>About LearnEarnAfrica</b>

We are a revolutionary educational platform that combines learning with earning. Our mission is to make African history and culture accessible while rewarding knowledge seekers.

🌍 <b>Our Vision:</b>
To create a generation of well-informed Africans who are proud of their heritage and financially empowered through education.

📌 <b>What We Do:</b>
• Interactive African-centered quizzes
• Real rewards for learning achievements
• Fair competition system
• Community building through knowledge

ℹ️ <b>Founded:</b> 2024
📍 <b>Based:</b> Ghana, West Africa
✨ <b>Mission:</b> Education + Earning = Empowerment
"""

WELCOME_MESSAGE = """
🎓 <b>Welcome to Learn and Earn Quiz Bot!</b>

Hello {name}! Ready to earn while you learn African history and culture?

{about_us}

🎲 <b>How to Play:</b>
• Answer quiz questions to earn points
• Use tokens to play (1 token per question)
• Earn 10 points per correct answer
• Get streak bonuses for 10-question streaks

🎁 <b>What You Get:</b>
• 3 FREE tokens to start
• 1 FREE token daily (just visit us!)
• 2 tokens for each friend you refer
• Bonus tokens for 10-question streaks
• Exchange points for real rewards!

💰 <b>Rewards Available:</b>
• More tokens • Airtime • Internet data
• Mobile money • Phones • Laptops
• Weekly random raffles with prizes!

📌 <b>Special Features:</b>
• Skip questions (once per question)
• Pause and resume games
• Track your progress
• Compete on leaderboards

🎯 <b>Fair Play:</b>
• Daily, weekly, monthly winners announced
• Transparent lottery system
• Equal chances for all players

{motivation}

<b>Ready to start your learning and earning journey? 🚀</b>
"""


# --- Global State ---
current_question = {}
paused_games = {}
pending_token_purchases = {}
user_feedback_mode = {}
user_actions = {}
custom_token_requests = {}
country_list_page = {}  # Add this line to your global state
user_momo_pending = {}

MOTIVATIONAL_MESSAGES = [
    "🌟 Believe in yourself! Every question you answer makes you smarter!",
    "🚀 Success is a journey, not a destination. Keep learning!",
    "💪 Your potential is limitless! Keep pushing forward!",
    "📌 Focus on progress, not perfection. You're doing great!",
    "🌈 Every expert was once a beginner. Keep going!",
    "✨ Knowledge is power, and you're gaining it every day!",
    "🔥 Champions are made in practice. Keep quizzing!",
    "🎉 You're amazing! Every effort counts towards your success!",
    "💡 Smart minds ask great questions. You're on the right track!",
    "🏆 Winners never quit, and quitters never win. You've got this!",
    "🌱 Growth happens outside your comfort zone. Keep learning!",
    "✪ You're not just earning tokens, you're building knowledge!",
    "🎂 Make learning fun! Every quiz is a step forward!",
    "🦋 Transform your mind one question at a time!",
    "🎊 Celebrate small wins! They lead to big victories!"
]


# --- Utility Functions ---
def is_admin(user_id):
    return int(user_id) in ADMIN_CHAT_IDS

def notify_admin_token_purchase(user_id, package_info, payment_method):
    try:
        user_data = get_user_data(user_id)
        if not user_data:
            return
        message = (
            f"\u2709\uFE0F <b>NEW TOKEN PURCHASE NOTIFICATION</b>\n\n"
            f"\ud83d\udc64 <b>User:</b> {user_data['Name']} (ID: {user_id})\n"
            f"\ud83d\udce6 <b>Package:</b> {package_info.get('amount', 'Custom')} tokens\n"
            f"\ud83d\udcb0 <b>Price:</b> ₢{package_info.get('price_cedis', 'N/A')} / ${package_info.get('price_usd', 'N/A')}\n"
            f"\ud83d\udcb3 <b>Payment Method:</b> {payment_method}\n"
            f"⏰ <b>Time:</b> {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC\n"
            f"📱 <b>User Contact:</b> @{user_data.get('Username', 'No username')}\n"
            f"⃣ Use Admin Dashboard to approve purchase"
        )
        for admin_id in ADMIN_CHAT_IDS:
            bot.send_message(admin_id, message)
    except Exception as e:
        logger.error(f"Error notifying admin: {e}")

def send_feedback_to_admin(user_id, feedback_text):
    try:
        user_data = get_user_data(user_id)
        if not user_data:
            return
        feedback_message = (
            f"💬 <b>USER FEEDBACK RECEIVED</b>\n\n"
            f"\ud83d\udc64 <b>From:</b> {user_data['Name']} (ID: {user_id})\n"
            f"📱 <b>Username:</b> @{user_data.get('Username', 'No username')}\n"
            f"⏰ <b>Time:</b> {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC\n\n"
            f"📝 <b>Message:</b>\n{feedback_text}\n"
            f"📊 <b>User Stats:</b>\n"
            f"• Tokens: {user_data['Tokens']}\n"
            f"• Points: {user_data['Points']}\n"
            f"• Referrals: {int(user_data.get('ReferralEarnings', 0))}"
        )
        for admin_id in ADMIN_CHAT_IDS:
            bot.send_message(admin_id, feedback_message)
    except Exception as e:
        logger.error(f"Error sending feedback to admin: {e}")

def notify_admin_physical_redemption(user_id, reward_info):
    """Notifies admins when a physical reward is redeemed."""
    try:
        user_data = get_user_data(user_id)
        if not user_data:
            return
        message = (
            f"📦 <b>PHYSICAL REWARD REDEEMED</b>\n\n"
            f"👤 <b>User:</b> {user_data['Name']} (ID: <code>{user_id}</code>)\n"
            f"📱 <b>Username:</b> @{user_data.get('Username', 'N/A')}\n"
            f"🎁 <b>Reward:</b> {reward_info['reward']}\n"
            f"💰 <b>Points Cost:</b> {reward_info['points']}\n"
            f"📞 <b>MoMo Number:</b> {user_data.get('MoMoNumber', 'Not provided')}\n"
            f"⏰ <b>Time:</b> {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC\n\n"
            f"Please contact the user to arrange for delivery. The redemption has been logged with PENDING status."
        )
        for admin_id in ADMIN_CHAT_IDS:
            bot.send_message(admin_id, message, parse_mode='HTML')
    except Exception as e:
        logger.error(f"Error notifying admin about physical redemption: {e}")

def translate_text(text, lang_code):
    try:
        return translator.translate(text, dest=lang_code).text
    except Exception as e:
        logger.error(f"Translation error: {e}")
        return text

# --- Registration & MoMo ---
@bot.message_handler(commands=['start'])
def start_handler(message):
    chat_id = message.chat.id

    # Extract referral code from start command
    referral_code = None
    referrer_user = None
    if message.text and len(message.text.split()) > 1:
        referral_code = message.text.split()[1]
        referrer_user = find_user_by_referral_code(referral_code)

    user = get_user_data(chat_id)
    if not user:
        # If referrer_user is found, pass their UserID to register_user
        referrer_id = referrer_user['UserID'] if referrer_user else None
        register_user(chat_id, message.from_user.first_name, message.from_user.username, referrer_id)
        user = get_user_data(chat_id)
        # Reward referrer if this is a new referral
        if referrer_user and user:
            reward_referrer(referrer_user['UserID'], 2)  # 2 tokens for referral
            increment_referral_count(referrer_user['UserID'], chat_id)
            logger.info(f"Referral reward: User {referrer_user['UserID']} got 2 tokens for referring {chat_id}")
            bot.send_message(referrer_user['UserID'], f"✅ You earned 2 tokens for referring {user['Name']}.")
            bot.send_message(chat_id, f"✅ You joined with a referral code from {referrer_user['Name']}. They have been rewarded!")
    if not user.get("MoMoNumber"):
        bot.send_message(chat_id, "📱 Please enter your MoMo number to continue:")
        user_momo_pending[chat_id] = "awaiting_momo"
        return

    welcome_msg = WELCOME_MESSAGE.format(
        name=user.get('Name', message.from_user.first_name),
        about_us=ABOUT_US,
        motivation=random.choice(MOTIVATIONAL_MESSAGES)
    )
    with open('L&E.png', 'rb') as photo:
        bot.send_photo(chat_id, photo)
    bot.send_message(chat_id, welcome_msg, reply_markup=create_main_menu(chat_id))

@bot.message_handler(func=lambda message: message.chat.id in user_momo_pending)
def momo_number_handler(message):
    chat_id = message.chat.id
    if user_momo_pending[chat_id] == "awaiting_momo":
        momo_number = message.text.strip()
        update_user_momo(chat_id, momo_number)
        del user_momo_pending[chat_id]
        bot.send_message(chat_id, "✅ MoMo number saved!", reply_markup=create_main_menu(chat_id))

# --- Quiz Handler ---
@bot.message_handler(func=lambda message: message.text == "🎲 Start Quiz")
def start_quiz_handler(message):
    chat_id = message.chat.id
    start_new_quiz(chat_id)

# --- Unified Quiz Logic ---
def start_new_quiz(chat_id):
    user = get_user_data(chat_id)
    if not user:
        bot.send_message(chat_id, "Please /start first.")
        return
    if float(user['Tokens']) <= 0:
        bot.send_message(chat_id, "⚠️ You don't have any tokens! Use '$💰 Buy Tokens' to continue playing.")
        return
    if chat_id in paused_games:
        markup = InlineKeyboardMarkup()
        markup.add(
            InlineKeyboardButton("▶️ Resume Game", callback_data="resume_game"),
            InlineKeyboardButton("🎲 New Game", callback_data="new_game")
        )
        bot.send_message(chat_id, "⌐️ You have a paused game. Would you like to resume or start a new one?", reply_markup=markup)
        return
    
    quiz = quiz_manager.get_random_question(chat_id)
    if not quiz:
        bot.send_message(chat_id, "❌ Error loading quiz. Please try again.")
        return
    
    lang = "English" # Hardcoded for now, can be changed later
    lang_code = {"English": "en", "French": "fr", "Swahili": "sw", "Arabic": "ar"}[lang]
    question = translate_text(quiz['q'], lang_code)
    choices = [translate_text(c, lang_code) for c in quiz['choices']]
    correct = translate_text(quiz['a'], lang_code)
    current_question[chat_id] = {
        'correct': correct,
        'question': question,
        'choices': choices,
        'skipped': False,
        'original_answer': quiz['a']
    }
    answer_markup = InlineKeyboardMarkup()
    for choice in choices:
        answer_markup.add(InlineKeyboardButton(choice, callback_data=f"answer:{choice}"))
    answer_markup.add(
        InlineKeyboardButton("⏩️ Skip", callback_data="skip_question"),
        InlineKeyboardButton("⏰ Pause", callback_data="pause_game")
    )
    answer_markup.add(InlineKeyboardButton("🏠 Return to Main Menu", callback_data="return_main")
    )
    bot.send_message(chat_id, f"🧠 <b>Quiz:</b>\n{question}", reply_markup=answer_markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("answer:"))
def answer_handler(call):
    chat_id = call.message.chat.id
    user = get_user_data(chat_id)
    if not user or chat_id not in current_question:
        bot.answer_callback_query(call.id, "No active question.")
        return
    answer = call.data.split("answer:")[1]
    correct = current_question[chat_id]['correct']
    tokens = float(user['Tokens'])
    points = float(user['Points'])
    bonus_earned = quiz_manager.update_player_progress(chat_id, answer == correct)
    if answer == correct:
        points += 10
        tokens -= 1
        update_user_tokens_points(chat_id, tokens, points)
        bot.answer_callback_query(call.id, "✅ Correct! +10 points")
        if bonus_earned:
            tokens += 3
            update_user_tokens_points(chat_id, tokens, points)
            bot.send_message(chat_id, "🔥 Streak bonus! +3 tokens")
    else:
        tokens -= 1
        update_user_tokens_points(chat_id, tokens, points)
        bot.answer_callback_query(call.id, "❌ Wrong answer!")
        bot.send_message(chat_id, f"❌ Wrong! The correct answer was: <b>{current_question[chat_id]['original_answer']}</b>")
    bot.send_message(chat_id, f"💰 Balance: {tokens} tokens | {points} points\n🔥 Current Streak: {quiz_manager.player_progress[chat_id]['current_streak']}")
    del current_question[chat_id]
    if tokens > 0:
        start_new_quiz(chat_id)
    else:
        bot.send_message(chat_id, "🌊 End You've run out of tokens. Use '$💰 Buy Tokens' to continue playing!", reply_markup=create_main_menu(chat_id))

@bot.callback_query_handler(func=lambda call: call.data == "skip_question")
def skip_question_handler(call):
    chat_id = call.message.chat.id
    if chat_id in current_question and not current_question[chat_id]['skipped']:
        current_question[chat_id]['skipped'] = True
        bot.send_message(chat_id, "⏩️ Question skipped! No tokens deducted.")
        del current_question[chat_id]
        start_new_quiz(chat_id)
    else:
        bot.send_message(chat_id, "❌ You can only skip once per question.")

@bot.callback_query_handler(func=lambda call: call.data == "pause_game")
def pause_game_handler(call):
    chat_id = call.message.chat.id
    if chat_id in current_question:
        paused_games[chat_id] = current_question[chat_id]
        del current_question[chat_id]
        bot.send_message(chat_id, "⏰ Game paused. Use '🎮 Start Quiz' to resume.")
    else:
        bot.send_message(chat_id, "❌ No active game to pause.")

@bot.callback_query_handler(func=lambda call: call.data == "resume_game")
def resume_game_handler(call):
    chat_id = call.message.chat.id
    if chat_id in paused_games:
        current_question[chat_id] = paused_games[chat_id]
        del paused_games[chat_id]
        quiz = current_question[chat_id]
        answer_markup = InlineKeyboardMarkup()
        for choice in quiz['choices']:
            answer_markup.add(InlineKeyboardButton(choice, callback_data=f"answer:{choice}"))
        answer_markup.add(InlineKeyboardButton("⏩️ Skip", callback_data="skip_question"), InlineKeyboardButton("⏰ Pause", callback_data="pause_game"))
        bot.send_message(chat_id, f"🧠 <b>Quiz:</b>\n{quiz['question']}", reply_markup=answer_markup)
    else:
        bot.send_message(chat_id, "❌ No paused game found.")

@bot.callback_query_handler(func=lambda call: call.data == "new_game")
def new_game_handler(call):
    chat_id = call.message.chat.id
    if chat_id in paused_games:
        del paused_games[chat_id]
    start_new_quiz(chat_id)

@bot.callback_query_handler(func=lambda call: call.data == "return_main")
def return_main_handler(call):
    chat_id = call.message.chat.id
    bot.send_message(chat_id, "Back to main menu.", reply_markup=create_main_menu(chat_id))
    if chat_id in current_question:
        del current_question[chat_id]

# --- Token Purchase Handler ---
@bot.message_handler(func=lambda message: message.text == "💰 Buy Tokens")
def buy_tokens_handler(message):
    chat_id = message.chat.id
    markup = InlineKeyboardMarkup()
    for label, data in TOKEN_PRICING.items():
        price_text = f"{label} (₢{data['price_cedis']} / ${data['price_usd']})"
        markup.add(InlineKeyboardButton(price_text, callback_data=f"buy:{label}"))
    markup.add(InlineKeyboardButton("Custom Amount", callback_data="buy:custom"))
    bot.send_message(chat_id, f"$💰 Choose a token package:\n\n{PAYMENT_INFO}", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("buy:"))
def buy_token_callback(call):
    chat_id = call.message.chat.id
    package_label = call.data.split("buy:")[1]
    if package_label == "custom":
        custom_token_requests[chat_id] = {"waiting_for_amount": True}
        bot.send_message(chat_id, "Please enter the number of tokens you want to buy:")
        bot.answer_callback_query(call.id)
        return
    if package_label not in TOKEN_PRICING:
        bot.answer_callback_query(call.id, "Invalid package.")
        return
    amount = TOKEN_PRICING[package_label]['amount']
    price = TOKEN_PRICING[package_label]['price_cedis']
    transaction_id = f"PENDING_{chat_id}_{int(time.time())}"
    log_token_purchase(chat_id, transaction_id, amount, "MTN MoMo or USDT")
    pending_token_purchases[chat_id] = {"amount": amount, "price_cedis": price, "price_usd": TOKEN_PRICING[package_label]['price_usd'], "package": package_label, "transaction_id": transaction_id}
    notify_admin_token_purchase(chat_id, pending_token_purchases[chat_id], "MTN MoMo or USDT")
    bot.send_message(
        chat_id,
        f"To buy {amount} tokens for GHS {price}, send payment via MTN MoMo or USDT. Your Transaction ID is `{transaction_id}`. An admin will approve it shortly.",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("📱 Notify Admin", callback_data="notify_admin_purchase"))
    )
    bot.answer_callback_query(call.id)

@bot.message_handler(func=lambda message: message.chat.id in custom_token_requests and custom_token_requests[message.chat.id].get('waiting_for_amount'))
def custom_token_handler(message):
    chat_id = message.chat.id
    if message.text.isdigit():
        amount = int(message.text)
        price_cedis = round(amount * 0.4, 2)
        price_usd = round(price_cedis / USD_TO_CEDIS_RATE, 2)
        pending_token_purchases[chat_id] = {"amount": amount, "price_cedis": price_cedis, "price_usd": price_usd, "package": "Custom"}
        notify_admin_token_purchase(chat_id, pending_token_purchases[chat_id], "MTN MoMo or USDT")
        bot.send_message(chat_id, f"To buy {amount} tokens for GHS {price_cedis}, send payment via MTN MoMo or USDT and reply with your transaction ID.\n\n{PAYMENT_INFO}")
        del custom_token_requests[chat_id]
    else:
        bot.send_message(chat_id, "Please enter a valid number for tokens.")

# --- Redeem Rewards Handler ---
@bot.message_handler(func=lambda message: message.text == "🎁 Redeem Rewards")
def redeem_rewards_handler(message):
    chat_id = message.chat.id
    user = get_user_data(chat_id)
    points = user.get('Points', 0)
    
    markup = InlineKeyboardMarkup()
    for category_id, category_info in REWARD_CATEGORIES.items():
        markup.add(InlineKeyboardButton(category_info["name"], callback_data=f"category:{category_id}"))
    
    bot.send_message(chat_id, f"🎁 You have {points} points. Choose a reward category:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("category:"))
def category_selection_handler(call):
    chat_id = call.message.chat.id
    category_id = call.data.split("category:")[1]
    
    if category_id not in REWARD_CATEGORIES:
        bot.answer_callback_query(call.id, "Invalid category.")
        return
    
    user = get_user_data(chat_id)
    points = user.get('Points', 0)
    category_info = REWARD_CATEGORIES[category_id]
    
    # Get rewards for this category
    category_rewards = {k: v for k, v in REDEEM_OPTIONS.items() if v.get('category') == category_id}
    
    if not category_rewards:
        bot.answer_callback_query(call.id, "No rewards available in this category.")
        return
    
    markup = InlineKeyboardMarkup()
    for reward_name, reward_info in category_rewards.items():
        markup.add(InlineKeyboardButton(f"{reward_name} ({reward_info['points']} pts)", callback_data=f"redeem:{reward_name}"))
    
    markup.add(InlineKeyboardButton("⬅️ Back to Categories", callback_data="back_to_categories"))
    
    bot.edit_message_text(
        f"🎁 {category_info['name']}\n{category_info['description']}\n\nYou have {points} points. Choose a reward:",
        chat_id,
        call.message.message_id,
        reply_markup=markup
    )
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data == "back_to_categories")
def back_to_categories_handler(call):
    chat_id = call.message.chat.id
    user = get_user_data(chat_id)
    points = user.get('Points', 0)
    
    markup = InlineKeyboardMarkup()
    for category_id, category_info in REWARD_CATEGORIES.items():
        markup.add(InlineKeyboardButton(category_info["name"], callback_data=f"category:{category_id}"))
    
    bot.edit_message_text(
        f"🎁 You have {points} points. Choose a reward category:",
        chat_id,
        call.message.message_id,
        reply_markup=markup
    )
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data.startswith("redeem:"))
def redeem_callback_handler(call):
    chat_id = call.message.chat.id
    label = call.data.split("redeem:")[1]
    reward = REDEEM_OPTIONS.get(label)
    user = get_user_data(chat_id)
    if not reward or not user:
        bot.answer_callback_query(call.id, "Invalid reward or user.")
        return
    if float(user['Points']) < reward['points']:
        bot.answer_callback_query(call.id, "Not enough points.")
        return

    # Deduct points and add tokens if applicable
    tokens_to_add = reward.get('amount', 0) if reward.get('category') == 'tokens' else 0
    update_user_tokens_points(chat_id, float(user['Tokens']) + tokens_to_add, float(user['Points']) - reward['points'])
    
    # Log the redemption
    log_point_redemption(chat_id, reward['reward'], reward['points'], reward.get('category'))

    # Prepare user message
    user_message = f"🎉 You redeemed: {reward['reward']}!"
    category = reward.get('category')
    if category == 'gadgets':
        user_message += "\n\nOur team will contact you shortly to arrange for delivery. This may take up to 48 hours."
    elif category in ['momo', 'airtime', 'data']:
        user_message += "\n\nYour reward is being processed and will be sent to you soon."
    
    bot.send_message(chat_id, user_message)
    
    # Notify admin if it's a physical item
    if category == 'gadgets':
        notify_admin_physical_redemption(chat_id, reward)

    bot.answer_callback_query(call.id, "Redemption successful!")

# --- Daily Reward Handler ---
@bot.message_handler(func=lambda message: message.text == "🎁 Daily Reward")
def daily_reward_handler(message):
    chat_id = message.chat.id
    user = get_user_data(chat_id)
    if not user:
        bot.send_message(chat_id, "Please /start first.")
        return
    rewarded, new_tokens = check_and_give_daily_reward(chat_id)
    if rewarded:
        bot.send_message(chat_id, f"🎉 You claimed your daily reward! +1 token\n💰 Total tokens: {new_tokens}")
    else:
        bot.send_message(chat_id, "⏰ You've already claimed your daily reward today. Come back tomorrow!")
    bot.send_message(chat_id, "Back to main menu:", reply_markup=create_main_menu(chat_id))

# --- Stats Handler ---
@bot.message_handler(func=lambda message: message.text == "📊 My Stats")
def stats_handler(message):
    chat_id = message.chat.id
    user = get_user_data(chat_id)
    if not user:
        bot.send_message(chat_id, "Please /start first.")
        return
    quiz_manager.init_player_progress(chat_id)
    progress = quiz_manager.player_progress[chat_id]
    stats_message = f"""
📊 <b>Your Stats</b>

👤 <b>Name:</b> {user['Name']}
📱 <b>Username:</b> @{user.get('Username', 'None')}
💰 <b>Tokens:</b> {user['Tokens']}
📌 <b>Points:</b> {user['Points']}
👥 <b>Referrals:</b> {int(user.get('ReferralEarnings', 0))}
🔥 <b>Current Streak:</b> {progress['current_streak']}
🏆 <b>Best Streak:</b> {progress['best_streak']}
✅ <b>Total Correct:</b> {progress['total_correct']}
❓ <b>Total Questions:</b> {progress['total_questions']}

⏩️ <b>Skips Used:</b> {progress['skips_used']}
⏰ <b>Games Paused:</b> {progress['games_paused']}
    """
    bot.send_message(chat_id, stats_message, reply_markup=create_main_menu(chat_id))

# --- Progress Handler ---
@bot.message_handler(func=lambda message: message.text == "📈 Progress")
def progress_handler(message):
    chat_id = message.chat.id
    quiz_manager.init_player_progress(chat_id)
    progress = quiz_manager.player_progress[chat_id]
    accuracy = (progress['total_correct'] / progress['total_questions'] * 100) if progress['total_questions'] > 0 else 0
    progress_message = f"""
📈 <b>Your Progress</b>

🔥 <b>Current Streak:</b> {progress['current_streak']} correct
🏆 <b>Best Streak:</b> {progress['best_streak']} correct
✅ <b>Accuracy:</b> {accuracy:.2f}%
❓ <b>Questions Answered:</b> {progress['total_questions']}
⏩️ <b>Skips Used:</b> {progress['skips_used']}
⏰ <b>Games Paused:</b> {progress['games_paused']}
    """
    bot.send_message(chat_id, progress_message, reply_markup=create_main_menu(chat_id))

# --- Referral Handler ---
@bot.message_handler(func=lambda message: message.text == "👥 Referral")
def referral_handler(message):
    chat_id = message.chat.id
    user = get_user_data(chat_id)
    if not user:
        bot.send_message(chat_id, "Please /start first.")
        return
    referral_code = user.get("referral_code", f"REF{str(chat_id)[-6:]}")
    referral_message = f"""
👥 <b>Referral</b> Invite friends to LearnEarnAfrica and earn <b>2 tokens</b> per referral!
📱 Your referral code: <b>{referral_code}</b>
🔗 Share this link: <code>https://t.me/LearnEarnAfricaBot?start={referral_code}</code>
👥 Total Referrals: <b>{int(user.get('ReferralEarnings', 0))}</b>
    """
    bot.send_message(chat_id, referral_message, reply_markup=create_main_menu(chat_id))

# --- Leaderboard Handler ---
@bot.message_handler(func=lambda message: message.text == "🏆 Leaderboard")
def leaderboard_handler(message):
    chat_id = message.chat.id
    sheet_manager = get_sheet_manager()
    users = sheet_manager.get_all_users()
    sorted_users = sorted(users, key=lambda x: float(x.get('Points', 0)), reverse=True)[:10]
    leaderboard_message = "🏆 <b>Top 10 Leaderboard</b>\n\n"
    for i, user in enumerate(sorted_users, 1):
        leaderboard_message += f"{i}. {user['Name']} (@{user.get('Username', 'None')}) - {user.get('Points', 0)} points\n"
    bot.send_message(chat_id, leaderboard_message, reply_markup=create_main_menu(chat_id))

# --- Help Handler ---
@bot.message_handler(func=lambda message: message.text == "ℹ️ Help")
def help_handler(message):
    chat_id = message.chat.id
    help_message = f"""
ℹ️ <b>Help & Instructions</b>

🎲 <b>How to Play:</b>
• Select 'Start Quiz' to start
• 1 token = 1 question
• Correct answer = 10 points
• 10 correct in a row = +3 tokens
• You can skip 1 question per game (no token cost)
• Pause/resume games anytime

💰 <b>Earning Tokens:</b>
• 3 free tokens on signup
• 1 free token daily (claim via 'Daily Reward')
• 2 tokens per referral
• Buy tokens via MTN MoMo or USDT

🎁 <b>Rewards:</b>
• Redeem points for tokens, airtime, data, MoMo, phones, or laptops
• Check 'Redeem Rewards' for options

👥 <b>Referrals:</b>
• Share your referral link to earn tokens
• Check 'Referrals' for your link

📊 <b>Track Progress:</b>
• 'My Stats' for tokens, points, and streaks
• 'Progress' for quiz performance
• 'Leaderboard' for top players

💬 <b>Support:</b>
• Use 'Send Feedback' for issues
• Contact @LearnEarnAfricaAdmin for payment or reward queries

{ABOUT_US}
    """
    bot.send_message(chat_id, help_message, reply_markup=create_main_menu(chat_id))

# --- Admin Menu Handler ---
@bot.message_handler(func=lambda message: message.text == "🛮️ Admin Menu")
def admin_menu_handler(message):
    chat_id = message.chat.id
    if not is_admin(chat_id):
        bot.send_message(chat_id, "Unauthorized.")
        return
    bot.send_message(chat_id, "🛠️ Admin Menu", reply_markup=create_admin_menu())

# --- Admin Dashboard Handler ---
@bot.message_handler(func=lambda message: message.text == "📊 Admin Dashboard" and is_admin(message.chat.id))
def admin_dashboard_handler(message):
    chat_id = message.chat.id
    sheet_manager = get_sheet_manager()
    users = sheet_manager.get_all_users()
    total_users = len(users)
    total_tokens = sum(float(user.get('Tokens', 0)) for user in users)
    total_points = sum(float(user.get('Points', 0)) for user in users)
    total_referrals = sum(int(user.get('ReferralEarnings', 0)) for user in users)
    pending_transactions = sheet_manager.get_pending_transactions()
    dashboard_message = f"""
📊 <b>Admin Dashboard</b>

👥 Total Users: {total_users}
💰 Total Tokens Distributed: {total_tokens}
📌 Total Points Earned: {total_points}
👥 Total Referrals: {total_referrals}
📃 Pending Token Purchases: {len(pending_transactions)}
    """
    bot.send_message(chat_id, dashboard_message, reply_markup=create_admin_menu())

# --- Run Daily Lottery Handler ---
@bot.message_handler(func=lambda message: message.text == "🏹‍⚠️ Run Daily Lottery" and is_admin(message.chat.id))
def daily_lottery_handler(message):
    chat_id = message.chat.id
    sheet_manager = get_sheet_manager()
    users = sheet_manager.get_all_users()
    eligible_users = [user for user in users if float(user.get('Tokens', 0)) > 0]
    if not eligible_users:
        bot.send_message(chat_id, "No eligible users for the lottery.", reply_markup=create_admin_menu())
        return
    winner = random.choice(eligible_users)
    winner_id = winner['UserID']
    current_tokens = float(winner.get('Tokens', 0))
    sheet_manager.update_user_tokens_points(winner_id, current_tokens + 5, winner.get('Points', 0))
    log_token_purchase(winner_id, f"LOTTERY_{int(time.time())}", 5, "Daily_Lottery")
    bot.send_message(winner_id, "🎉 Congratulations! You won 5 tokens in the daily lottery!")
    bot.send_message(chat_id, f"🏹‍⚠️ Daily Lottery Winner: {winner['Name']} (@{winner.get('Username', 'None')}) - 5 tokens awarded.", reply_markup=create_admin_menu())

# --- Run Weekly Raffle Handler ---
@bot.message_handler(func=lambda message: message.text == "㊗️ Run Weekly Raffle" and is_admin(message.chat.id))
def weekly_raffle_handler(message):
    chat_id = message.chat.id
    sheet_manager = get_sheet_manager()
    users = sheet_manager.get_all_users()
    eligible_users = [user for user in users if float(user.get('Points', 0)) >= 100]
    if not eligible_users:
        bot.send_message(chat_id, "No eligible users for the raffle.", reply_markup=create_admin_menu())
        return
    winner = random.choice(eligible_users)
    winner_id = winner['UserID']
    current_tokens = float(winner.get('Tokens', 0))
    sheet_manager.update_user_tokens_points(winner_id, current_tokens + 10, winner.get('Points', 0))
    log_token_purchase(winner_id, f"RAFFLE_{int(time.time())}", 10, "Weekly_Raffle")
    bot.send_message(winner_id, "㊗️ Congratulations! You won 10 tokens in the weekly raffle!")
    bot.send_message(chat_id, f"㊗️ Weekly Raffle Winner: {winner['Name']} (@{winner.get('Username', 'None')}) - 10 tokens awarded.", reply_markup=create_admin_menu())

# --- View Pending Tokens Handler ---
@bot.message_handler(func=lambda message: message.text == "�참 View Pending Tokens" and is_admin(message.chat.id))
def view_pending_tokens_handler(message):
    chat_id = message.chat.id
    sheet_manager = get_sheet_manager()
    pending_transactions = sheet_manager.get_pending_transactions()
    if not pending_transactions:
        bot.send_message(chat_id, "No pending token purchases.", reply_markup=create_admin_menu())
        return
    pending_message = "�참 <b>Pending Token Purchases</b>\n\n"
    for tx in pending_transactions:
        user_id = tx.get('user_id')
        user = sheet_manager.get_user_data(user_id)
        pending_message += f"""
👤 User: {user['Name']} (@{user.get('Username', 'None')})
📦 Amount: {tx['amount']} tokens
💳 Transaction ID: {tx['transaction_id']}
💰 Payment Method: {tx.get('payment_method', 'N/A')}
⏰ Time: {tx.get('timestamp')}
        """
    bot.send_message(chat_id, pending_message, reply_markup=create_admin_menu())

# --- Approve Token Purchase Handler ---
@bot.message_handler(func=lambda message: message.text == "✅ Approve Token Purchase" and is_admin(message.chat.id))
def approve_token_purchase_handler(message):
    chat_id = message.chat.id
    bot.send_message(chat_id, "Please enter the Transaction ID to approve:")
    bot.register_next_step_handler(message, process_approve_token_purchase)

def process_approve_token_purchase(message):
    chat_id = message.chat.id
    if not is_admin(chat_id):
        bot.send_message(chat_id, "Unauthorized.")
        return
    transaction_id = message.text.strip()
    sheet_manager = get_sheet_manager()
    pending_transactions = sheet_manager.get_pending_transactions()
    for tx in pending_transactions:
        if tx['transaction_id'] == transaction_id:
            user_id = int(tx['user_id'])
            amount = float(tx['amount'])
            user = sheet_manager.get_user_data(user_id)
            if user:
                current_tokens = float(user.get('Tokens', 0))
                sheet_manager.update_user_tokens_points(user_id, current_tokens + amount, user.get('Points', 0))
                new_transaction_id = f"APPROVED_{transaction_id}"
                update_transaction_status(transaction_id, new_transaction_id)
                bot.send_message(user_id, f"✅ Your purchase of {amount} tokens has been approved! Total tokens: {current_tokens + amount}")
                bot.send_message(chat_id, f"✅ Approved {amount} tokens for user {user['Name']} (@{user.get('Username', 'None')}).")
                return
    bot.send_message(chat_id, "❌ Transaction ID not found or already processed.", reply_markup=create_admin_menu())

# --- Broadcast Message Handler ---
@bot.message_handler(func=lambda message: message.text == "💌 Broadcast Message" and is_admin(message.chat.id))
def broadcast_handler(message):
    chat_id = message.chat.id
    bot.send_message(chat_id, "Please enter the message to broadcast to all users:")
    bot.register_next_step_handler(message, process_broadcast_message)

def process_broadcast_message(message):
    chat_id = message.chat.id
    if not is_admin(chat_id):
        bot.send_message(chat_id, "Unauthorized.")
        return
    broadcast_text = message.text.strip()
    sheet_manager = get_sheet_manager()
    users = sheet_manager.get_all_users()
    for user in users:
        user_id = user['UserID']
        try:
            bot.send_message(user_id, f"💌 <b>Announcement</b>\n\n{broadcast_text}")
        except Exception as e:
            logger.error(f"Failed to send broadcast to {user_id}: {e}")
    bot.send_message(chat_id, f"💌 Broadcast sent to {len(users)} users.", reply_markup=create_admin_menu())

# --- User Stats Handler ---
@bot.message_handler(func=lambda message: message.text == "📈 User Stats" and is_admin(message.chat.id))
def user_stats_handler(message):
    chat_id = message.chat.id
    bot.send_message(chat_id, "Please enter the User ID to view stats:")
    bot.register_next_step_handler(message, process_user_stats)

def process_user_stats(message):
    chat_id = message.chat.id
    if not is_admin(chat_id):
        bot.send_message(chat_id, "Unauthorized.")
        return
    user_id = message.text.strip()
    user = get_user_data(user_id)
    if not user:
        bot.send_message(chat_id, "User not found.", reply_markup=create_admin_menu())
        return
    quiz_manager.init_player_progress(user_id)
    progress = quiz_manager.player_progress[user_id]
    stats_message = f"""
📈 <b>User Stats for {user['Name']}</b>

👤 <b>User ID:</b> {user_id}
📱 <b>Username:</b> @{user.get('Username', 'None')}
💰 <b>Tokens:</b> {user['Tokens']}
📌 <b>Points:</b> {user['Points']}
👥 <b>Referrals:</b> {int(user.get('ReferralEarnings', 0))}
🔥 <b>Current Streak:</b> {progress['current_streak']}
🏆 <b>Best Streak:</b> {progress['best_streak']}
✅ <b>Total Correct:</b> {progress['total_correct']}
❓ <b>Total Questions:</b> {progress['total_questions']}
⏩️ <b>Skips Used:</b> {progress['skips_used']}
⏰ <b>Games Paused:</b> {progress['games_paused']}
    """
    bot.send_message(chat_id, stats_message, reply_markup=create_admin_menu())

# --- Back to User Menu ---
@bot.message_handler(func=lambda message: message.text == "⬅️ Back to User Menu" and is_admin(message.chat.id))
def back_to_user_menu_handler(message):
    chat_id = message.chat.id
    bot.send_message(chat_id, "Returning to user menu...", reply_markup=create_main_menu(chat_id))

# --- Current Affairs Handler ---
def fetch_current_affairs():
    try:
        url = f"https://newsdata.io/api/1/news?apikey={NEWSDATA_API_KEY}&country=ng,gh,za,eg,ke&category=business,world"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            articles = data.get("results", [])[:5]
            news = "\n\n".join([f"\ud83d\udcf9 <b>{a['title']}</b>\n{a['link']}" for a in articles])
            return news or "No current news found."
        return "Could not fetch news at this time."
    except Exception as e:
        logger.error(f"Current affairs fetch error: {e}")
        return "Error fetching news."

@bot.message_handler(func=lambda message: message.text == "🌍 Current Affairs")
def current_affairs_handler(message):
    chat_id = message.chat.id
    bot.send_message(chat_id, "Fetching latest African and global business news...")
    news = fetch_current_affairs()
    bot.send_message(chat_id, news, parse_mode="HTML", disable_web_page_preview=True)

# --- Country Bio Handler ---
@bot.callback_query_handler(func=lambda call: call.data.startswith("countrybio:"))
def country_bio_handler(call):
    chat_id = call.message.chat.id
    country_name = call.data.split("countrybio:")[1]
    country = next((c for c in quiz_manager.AFRICAN_COUNTRIES if c["name"] == country_name), None)
    if not country:
        bot.answer_callback_query(call.id, "Country not found.")
        return
    bio = country.get('bio', 'No bio available.')
    website = country.get('website', '#')
    text = f"🌍 <b>{country['name']}</b>\n\n{bio}\n\n🔗 <a href='{website}'>Official Website</a>"
    bot.send_message(chat_id, text, parse_mode="HTML", disable_web_page_preview=False)
    bot.answer_callback_query(call.id)

# --- Pagination for Country List ---
COUNTRIES_PER_PAGE = 8  # You can adjust this number

def get_country_page_markup(page=0):
    start = page * COUNTRIES_PER_PAGE
    end = start + COUNTRIES_PER_PAGE
    markup = InlineKeyboardMarkup()
    for country in quiz_manager.AFRICAN_COUNTRIES[start:end]:
        markup.add(InlineKeyboardButton(country["name"], callback_data=f"countrybio:{country['name']}"))
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton("⬅️ Prev", callback_data=f"countrylist:prev:{page-1}"))
    if end < len(quiz_manager.AFRICAN_COUNTRIES):
        nav_buttons.append(InlineKeyboardButton("Next ➡️", callback_data=f"countrylist:next:{page+1}"))
    if nav_buttons:
        markup.add(*nav_buttons)
    return markup

@bot.message_handler(func=lambda message: message.text == "🌍 African Countries")
def list_african_countries_handler(message):
    chat_id = message.chat.id
    country_list_page[chat_id] = 0
    markup = get_country_page_markup(0)
    bot.send_message(chat_id, "🌍 <b>Select an African country to learn more:</b>", reply_markup=markup, parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data.startswith("countrylist:"))
def countrylist_pagination_handler(call):
    chat_id = call.message.chat.id
    _, direction, page = call.data.split(":")
    page = int(page)
    country_list_page[chat_id] = page
    markup = get_country_page_markup(page)
    bot.edit_message_reply_markup(chat_id, call.message.message_id, reply_markup=markup)
    bot.answer_callback_query(call.id)

# --- Menu Creation Functions ---
def create_main_menu(chat_id):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    user = get_user_data(chat_id)
    if not user:
        return markup
    
    # Basic menu for all users
    markup.add(KeyboardButton("🎲 Start Quiz"), KeyboardButton("🎁 Daily Reward"))
    markup.add(KeyboardButton("💰 Buy Tokens"), KeyboardButton("🎁 Redeem Rewards"))
    markup.add(KeyboardButton("📊 My Stats"), KeyboardButton("📈 Progress"))
    markup.add(KeyboardButton("🏆 Leaderboard"), KeyboardButton("👥 Referral"))
    markup.add(KeyboardButton("🌍 African Countries"), KeyboardButton("🛒 Marketplace"))
    markup.add(KeyboardButton("🗑️ Community Cleanup"), KeyboardButton("ℹ️ Help"), KeyboardButton("💬 Send Feedback")
    )
    
    # Add admin menu for admins
    if is_admin(chat_id):
        markup.add(KeyboardButton("🛮️ Admin Menu"))
    
    return markup

def create_admin_menu():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(KeyboardButton("📊 Admin Dashboard"), KeyboardButton("♻️ Review Cleanups"))
    markup.row(KeyboardButton("✅ Approve Token Purchase"), KeyboardButton("💌 Broadcast Message"))
    markup.row(KeyboardButton("🏹‍⚠️ Run Daily Lottery"), KeyboardButton("㊗️ Run Weekly Raffle"))
    markup.row(KeyboardButton("📈 User Stats"), KeyboardButton("⬅️ Back to User Menu"))
    return markup

# --- Bot Webhook ---
@app.route('/webhook', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return ''
    else:
        abort(403)

@app.route('/webhook/nowpayments', methods=['POST'])
def nowpayments_webhook():
    if request.headers.get('content-type') == 'application/json':
        data = request.get_json()
        logger.info(f"Received NOWPayments webhook: {data}")

        payment_status = data.get('payment_status')
        order_id = data.get('order_id')

        if payment_status == 'finished' and order_id and order_id.startswith('learnearnafrica_'):
            try:
                parts = order_id.split('_')
                user_id = int(parts[1])
                price_usd = float(data.get('price_amount'))
                
                # Calculate tokens from USD price
                # 1 token = 0.4 GHS
                # A simpler way: 1 token = 0.4 GHS = 0.4 / 11.8 USD ~= $0.0339
                # tokens_to_add = price_usd / (0.4 / USD_TO_CEDIS_RATE)
                tokens_to_add = round((price_usd * USD_TO_CEDIS_RATE) / 0.4)

                user = get_user_data(user_id)
                if user:
                    update_user_tokens_points(user_id, float(user['Tokens']) + tokens_to_add, float(user['Points']))
                    log_token_purchase(user_id, data.get('payment_id'), tokens_to_add, "NOWPayments_USDT")
                    bot.send_message(user_id, f"✅ Your payment was successful! {tokens_to_add} tokens have been added to your account.")
            except Exception as e:
                logger.error(f"Error processing NOWPayments webhook: {e}")
        return ''
    else:
        abort(403)

# --- Cleanup Submission Review Handlers (for Admins) ---

def process_cleanup_approval(call, row_index, user_id, points_to_award=50):
    """Helper function to process a cleanup submission approval."""
    admin_id = call.from_user.id
    approve_cleanup_submission(row_index, admin_id, points_to_award)

    user = get_user_data(user_id)
    if user:
        update_user_tokens_points(user_id, user['Tokens'], float(user['Points']) + points_to_award)
        bot.send_message(user_id, f"✅ Your community cleanup submission has been approved! You've been awarded {points_to_award} points.")

    bot.answer_callback_query(call.id, "Submission Approved.")
    # Edit the original admin message to show it's been processed
    new_caption = call.message.caption + "\n\n<b>✅ Approved by you.</b>"
    bot.edit_message_caption(caption=new_caption, chat_id=call.message.chat.id, message_id=call.message.message_id, parse_mode='HTML')

def process_cleanup_rejection(call, row_index, user_id):
    """Helper function to process a cleanup submission rejection."""
    admin_id = call.from_user.id
    reject_cleanup_submission(row_index, admin_id)

    bot.send_message(user_id, "❌ Your community cleanup submission has been rejected. Please ensure your submission follows the guidelines and try again.")
    bot.answer_callback_query(call.id, "Submission Rejected.")
    # Edit the original admin message
    new_caption = call.message.caption + "\n\n<b>❌ Rejected by you.</b>"
    bot.edit_message_caption(caption=new_caption, chat_id=call.message.chat.id, message_id=call.message.message_id, parse_mode='HTML')

@bot.message_handler(func=lambda message: message.text == "♻️ Review Cleanups" and is_admin(message.chat.id))
def review_cleanups_handler(message):
    chat_id = message.chat.id
    bot.send_message(chat_id, "Fetching pending cleanup submissions...")
    
    pending_submissions = get_pending_cleanup_submissions()
    
    if not pending_submissions:
        bot.send_message(chat_id, "No pending submissions to review.")
        return
        
    bot.send_message(chat_id, f"Found {len(pending_submissions)} pending submissions. Displaying now:")
    
    for sub in pending_submissions:
        user_id = sub['UserID']
        row_index = sub['row_index']
        
        caption = (
            f"🗑️ <b>Review Cleanup Submission</b>\n\n"
            f"<b>User:</b> {sub['Name']} (@{sub.get('Username', 'N/A')})\n"
            f"<b>ID:</b> <code>{user_id}</code>\n"
            f"<b>Location:</b> {sub['Location']}\n"
            f"<b>Submitted:</b> {sub['Timestamp']}"
        )
                  
        markup = InlineKeyboardMarkup()
        markup.add(
            InlineKeyboardButton("✅ Approve (50 pts)", callback_data=f"cleanup_review_approve:{row_index}:{user_id}"),
            InlineKeyboardButton("❌ Reject", callback_data=f"cleanup_review_reject:{row_index}:{user_id}")
        )
        
        media_id = sub['MediaURL']
        media_type = sub.get('MediaType', 'photo') # Default to photo if not specified

        try:
            if media_type == 'photo':
                bot.send_photo(chat_id, media_id, caption=caption, reply_markup=markup, parse_mode='HTML')
            elif media_type == 'video':
                bot.send_video(chat_id, media_id, caption=caption, reply_markup=markup, parse_mode='HTML')
        except Exception as e:
            bot.send_message(chat_id, f"Could not display media for submission from user {user_id}.\nError: {e}\n\n{caption}", reply_markup=markup, parse_mode='HTML')

@bot.callback_query_handler(func=lambda call: call.data.startswith("cleanup_approve:"))
def approve_cleanup_callback(call):
    """Handles real-time approval from admin notification."""
    try:
        _, user_id, timestamp = call.data.split(":", 2)
        user_id = int(user_id)
        row_index = find_cleanup_submission(user_id, timestamp)
        if row_index:
            process_cleanup_approval(call, row_index, user_id)
        else:
            bot.answer_callback_query(call.id, "⚠️ Submission already processed or not found.")
            bot.edit_message_caption(caption=call.message.caption + "\n\n<b>⚠️ Already processed.</b>", chat_id=call.message.chat.id, message_id=call.message.message_id, parse_mode='HTML')
    except Exception as e:
        logger.error(f"Error in cleanup_approve callback: {e}")
        bot.answer_callback_query(call.id, "An error occurred.")

@bot.callback_query_handler(func=lambda call: call.data.startswith("cleanup_reject:"))
def reject_cleanup_callback(call):
    """Handles real-time rejection from admin notification."""
    try:
        _, user_id, timestamp = call.data.split(":", 2)
        user_id = int(user_id)
        row_index = find_cleanup_submission(user_id, timestamp)
        if row_index:
            process_cleanup_rejection(call, row_index, user_id)
        else:
            bot.answer_callback_query(call.id, "⚠️ Submission already processed or not found.")
            bot.edit_message_caption(caption=call.message.caption + "\n\n<b>⚠️ Already processed.</b>", chat_id=call.message.chat.id, message_id=call.message.message_id, parse_mode='HTML')
    except Exception as e:
        logger.error(f"Error in cleanup_reject callback: {e}")
        bot.answer_callback_query(call.id, "An error occurred.")

@bot.callback_query_handler(func=lambda call: call.data.startswith("cleanup_review_approve:"))
def approve_cleanup_review_callback(call):
    """Handles approval from the batch review list."""
    _, row_index, user_id = call.data.split(":")
    process_cleanup_approval(call, int(row_index), int(user_id))

@bot.callback_query_handler(func=lambda call: call.data.startswith("cleanup_review_reject:"))
def reject_cleanup_review_callback(call):
    """Handles rejection from the batch review list."""
    _, row_index, user_id = call.data.split(":")
    process_cleanup_rejection(call, int(row_index), int(user_id))

# --- Marketplace Handlers ---
@bot.message_handler(func=lambda message: message.text == "🛒 Marketplace")
def marketplace_menu_handler(message):
    logger.info("Marketplace handler called")
    chat_id = message.chat.id
    marketplace_message = (
        "\U0001f6d2 <b>Welcome to the Marketplace!</b> (Coming Soon)\n\n"
        "This is where your points turn into real-world value! In the future, you'll be able to:\n\n"
        "• <b>Browse a catalog of products:</b> Use your points to claim exclusive items like branded merchandise, digital goods, and more.\n"
        "• <b>Enter special raffles:</b> Participate in exclusive raffles for high-value prizes.\n"
        "• <b>Support community projects:</b> Donate your points to support educational and environmental initiatives.\n\n"
        "Stay tuned for updates! We're working hard to bring you an exciting marketplace experience."
    )
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🔔 Notify Me When Available", callback_data="notify_me_marketplace"))
    bot.send_message(chat_id, marketplace_message, reply_markup=markup, parse_mode='HTML')


@bot.callback_query_handler(func=lambda call: call.data == "notify_me_marketplace")
def notify_me_marketplace_handler(call):
    chat_id = call.message.chat.id
    user = get_user_data(chat_id)
    bot.answer_callback_query(call.id, "✅ You will be notified when the marketplace is live!")
    bot.send_message(chat_id, "Thanks for your interest! We'll let you know as soon as the Marketplace is open.")
    
    # Notify admin
    if user:
        admin_message = f"\u2709\ufe0f User @{user.get('Username', user.get('Name', chat_id))} is interested in the Marketplace feature."
        for admin_id in ADMIN_CHAT_IDS:
            try:
                bot.send_message(admin_id, admin_message)
            except Exception as e:
                logger.error(f"Failed to send marketplace interest notification to admin {admin_id}: {e}")

@bot.callback_query_handler(func=lambda call: call.data == "notify_admin_purchase")
def notify_admin_purchase_handler(call):
    chat_id = call.message.chat.id
    user = get_user_data(chat_id)
    for admin_id in ADMIN_CHAT_IDS:
        bot.send_message(admin_id, f"User @{user.get('Username', chat_id)} has requested admin attention for a token purchase.")
    bot.send_message(chat_id, "✅ Admin has been notified. Please wait for approval.")

if __name__ == "__main__":
    # Register handlers from other modules
    register_cleanup_handlers(bot, ADMIN_CHAT_IDS, logger)
    app.run(host="0.0.0.0", port=int(os.environ.get('PORT', 8080)))
