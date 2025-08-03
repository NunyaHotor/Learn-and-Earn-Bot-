
"""
Learn4Cash Quiz Bot - A Telegram bot for educational quizzes with token system.
"""

import random
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from datetime import datetime
import time
import logging
import threading
import json
import os

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
    update_last_claim_date,
    get_sheet_manager
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Bot configuration
API_KEY = "8470972230:AAFs4wYw94DOiXk2TLpyM0iKlfXLL78JdBE"
bot = telebot.TeleBot(API_KEY, parse_mode='HTML')

# Enhanced quiz data with 65 African-centered questions
quizzes = [
    # Ghana Questions
    {"q": "Who was Ghana's first president?", "a": "Kwame Nkrumah", "choices": ["Kwame Nkrumah", "Rawlings", "Mahama", "Busia"]},
    {"q": "When did Ghana gain independence?", "a": "1957", "choices": ["1945", "1957", "1960", "1966"]},
    {"q": "What is the capital of Ghana?", "a": "Accra", "choices": ["Kumasi", "Tamale", "Accra", "Ho"]},
    {"q": "Which region is Lake Volta in?", "a": "Volta", "choices": ["Ashanti", "Volta", "Northern", "Bono"]},
    {"q": "Who led the 1948 Accra Riots?", "a": "The Big Six", "choices": ["Yaa Asantewaa", "The Big Six", "Danquah", "Rawlings"]},
    
    # General African Questions
    {"q": "What is the largest country in Africa by land area?", "a": "Algeria", "choices": ["Nigeria", "Algeria", "Egypt", "South Africa"]},
    {"q": "Which African country has the most pyramids?", "a": "Sudan", "choices": ["Egypt", "Sudan", "Ethiopia", "Libya"]},
    {"q": "What is the official language of Angola?", "a": "Portuguese", "choices": ["French", "Portuguese", "English", "Spanish"]},
    {"q": "Which African river is the longest?", "a": "Nile", "choices": ["Congo", "Niger", "Zambezi", "Nile"]},
    {"q": "Which African country is known as the Rainbow Nation?", "a": "South Africa", "choices": ["Ghana", "South Africa", "Kenya", "Tanzania"]},
    {"q": "Which African island nation lies off the southeast coast of Africa?", "a": "Madagascar", "choices": ["Seychelles", "Mauritius", "Madagascar", "Comoros"]},
    {"q": "What is the largest desert in Africa?", "a": "Sahara", "choices": ["Namib", "Sahara", "Kalahari", "Gobi"]},
    {"q": "Which African country was never colonized?", "a": "Ethiopia", "choices": ["Ghana", "Liberia", "Ethiopia", "Morocco"]},
    {"q": "Which African country produces the most cocoa?", "a": "Côte d'Ivoire", "choices": ["Ghana", "Nigeria", "Cameroon", "Côte d'Ivoire"]},
    {"q": "What is the currency of Nigeria?", "a": "Naira", "choices": ["Cedi", "Shilling", "Rand", "Naira"]},
    
    # Historical Questions
    {"q": "Who was the Ethiopian emperor who defeated Italy at Adwa in 1896?", "a": "Menelik II", "choices": ["Haile Selassie", "Menelik II", "Tewodros II", "Yohannes IV"]},
    {"q": "Which ancient African kingdom was known for its gold trade?", "a": "Mali Empire", "choices": ["Songhai", "Mali Empire", "Ghana Empire", "Kanem"]},
    {"q": "Who was the first woman to win a Nobel Peace Prize from Africa?", "a": "Wangari Maathai", "choices": ["Ellen Johnson Sirleaf", "Wangari Maathai", "Leymah Gbowee", "Tawakkol Karman"]},
    {"q": "Which African city is known as the 'Mother City'?", "a": "Cape Town", "choices": ["Lagos", "Cairo", "Cape Town", "Nairobi"]},
    {"q": "What was the ancient name of Ethiopia?", "a": "Abyssinia", "choices": ["Nubia", "Kush", "Abyssinia", "Axum"]},
    {"q": "Which African leader coined the term 'African Socialism'?", "a": "Julius Nyerere", "choices": ["Kwame Nkrumah", "Julius Nyerere", "Kenneth Kaunda", "Jomo Kenyatta"]},
    {"q": "The Great Rift Valley runs through which part of Africa?", "a": "East Africa", "choices": ["West Africa", "North Africa", "East Africa", "Central Africa"]},
    {"q": "Which African country was formerly known as Southern Rhodesia?", "a": "Zimbabwe", "choices": ["Zambia", "Zimbabwe", "Botswana", "Malawi"]},
    {"q": "Who was known as the 'Father of African Nationalism'?", "a": "Marcus Garvey", "choices": ["W.E.B. Du Bois", "Marcus Garvey", "Kwame Nkrumah", "Nelson Mandela"]},
    {"q": "Which African queen fought against Roman expansion?", "a": "Queen Nzinga", "choices": ["Queen Nefertiti", "Queen Nzinga", "Queen Candace", "Queen Amina"]},
    {"q": "What is the highest mountain in Africa?", "a": "Mount Kilimanjaro", "choices": ["Mount Kenya", "Mount Kilimanjaro", "Ras Dashen", "Mount Elgon"]},
    {"q": "Which African empire controlled the salt and gold trade routes?", "a": "Songhai Empire", "choices": ["Mali Empire", "Ghana Empire", "Songhai Empire", "Kanem Empire"]},
    {"q": "Who was the last Pharaoh of Egypt?", "a": "Cleopatra VII", "choices": ["Nefertiti", "Hatshepsut", "Cleopatra VII", "Ankhesenamun"]},
    {"q": "Which African country has the most official languages?", "a": "South Africa", "choices": ["Nigeria", "South Africa", "Kenya", "Tanzania"]},
    {"q": "What was the original name of Ghana before independence?", "a": "Gold Coast", "choices": ["Gold Coast", "Ivory Coast", "Slave Coast", "Grain Coast"]},
    {"q": "Which African kingdom was famous for its terracotta sculptures?", "a": "Nok", "choices": ["Benin", "Nok", "Ife", "Oyo"]},
    {"q": "Who wrote the novel 'Things Fall Apart'?", "a": "Chinua Achebe", "choices": ["Wole Soyinka", "Chinua Achebe", "Ngugi wa Thiong'o", "Ama Ata Aidoo"]},
    {"q": "Which lake is shared by Kenya, Tanzania, and Uganda?", "a": "Lake Victoria", "choices": ["Lake Tanganyika", "Lake Victoria", "Lake Malawi", "Lake Chad"]},
    {"q": "What does 'Ubuntu' mean in African philosophy?", "a": "I am because we are", "choices": ["Unity in diversity", "I am because we are", "Strength in numbers", "Peace and harmony"]},
    {"q": "Which African country was the first to gain independence?", "a": "Libya", "choices": ["Ghana", "Nigeria", "Libya", "Morocco"]},
    {"q": "Who was the founder of the Kingdom of Zulu?", "a": "Shaka Zulu", "choices": ["Shaka Zulu", "Cetshwayo", "Dingane", "Mpande"]},
    
    # NEW 30 AFRICAN-CENTERED QUESTIONS
    
    # Geography Questions
    {"q": "Which African country is landlocked and bordered by 7 countries?", "a": "Chad", "choices": ["Mali", "Niger", "Chad", "Burkina Faso"]},
    {"q": "What is the largest lake in Africa?", "a": "Lake Victoria", "choices": ["Lake Tanganyika", "Lake Victoria", "Lake Malawi", "Lake Chad"]},
    {"q": "Which African country has both Atlantic and Indian Ocean coastlines?", "a": "South Africa", "choices": ["Somalia", "South Africa", "Morocco", "Egypt"]},
    {"q": "What is the lowest point in Africa?", "a": "Lake Assal", "choices": ["Dead Sea", "Lake Assal", "Qattara Depression", "Danakil Depression"]},
    {"q": "Which African mountain range is located in Morocco?", "a": "Atlas Mountains", "choices": ["Atlas Mountains", "Drakensberg", "Ethiopian Highlands", "Ahaggar Mountains"]},
    
    # Currency Questions
    {"q": "What is the currency of Kenya?", "a": "Shilling", "choices": ["Rand", "Shilling", "Birr", "Dinar"]},
    {"q": "Which African country uses the Franc CFA?", "a": "Senegal", "choices": ["Ghana", "Nigeria", "Senegal", "Ethiopia"]},
    {"q": "What is the currency of Egypt?", "a": "Pound", "choices": ["Dinar", "Dirham", "Pound", "Birr"]},
    {"q": "Which currency is used in Morocco?", "a": "Dirham", "choices": ["Dinar", "Dirham", "Franc", "Pound"]},
    {"q": "What is the currency of Ethiopia?", "a": "Birr", "choices": ["Birr", "Shilling", "Rand", "Naira"]},
    
    # Commerce & Economics
    {"q": "Which African country is the largest producer of diamonds?", "a": "Botswana", "choices": ["South Africa", "Botswana", "Angola", "Congo"]},
    {"q": "What is Africa's largest stock exchange?", "a": "Johannesburg Stock Exchange", "choices": ["Nigerian Stock Exchange", "Johannesburg Stock Exchange", "Egyptian Exchange", "Nairobi Securities Exchange"]},
    {"q": "Which African country exports the most oil?", "a": "Nigeria", "choices": ["Angola", "Nigeria", "Algeria", "Libya"]},
    {"q": "What is the main export of Zambia?", "a": "Copper", "choices": ["Gold", "Copper", "Diamonds", "Coffee"]},
    {"q": "Which African country is the largest producer of coffee?", "a": "Ethiopia", "choices": ["Kenya", "Ethiopia", "Uganda", "Tanzania"]},
    
    # Politics & Government
    {"q": "Who was the first black president of South Africa?", "a": "Nelson Mandela", "choices": ["Nelson Mandela", "Thabo Mbeki", "Jacob Zuma", "Desmond Tutu"]},
    {"q": "Which African organization promotes continental unity?", "a": "African Union", "choices": ["ECOWAS", "African Union", "SADC", "EAC"]},
    {"q": "Who was Libya's leader for 42 years?", "a": "Muammar Gaddafi", "choices": ["Hosni Mubarak", "Muammar Gaddafi", "Idi Amin", "Robert Mugabe"]},
    {"q": "Which African country had apartheid?", "a": "South Africa", "choices": ["Zimbabwe", "South Africa", "Namibia", "Angola"]},
    {"q": "Who founded the African National Congress (ANC)?", "a": "John Dube", "choices": ["Nelson Mandela", "Oliver Tambo", "John Dube", "Walter Sisulu"]},
    
    # Religion & Culture
    {"q": "What is the predominant religion in Ethiopia?", "a": "Christianity", "choices": ["Islam", "Christianity", "Judaism", "Traditional"]},
    {"q": "Which city is considered holy in Ethiopian Christianity?", "a": "Lalibela", "choices": ["Addis Ababa", "Lalibela", "Gondar", "Axum"]},
    {"q": "What is the main religion in Morocco?", "a": "Islam", "choices": ["Christianity", "Islam", "Judaism", "Traditional"]},
    {"q": "Which African country has the most Christians?", "a": "Nigeria", "choices": ["Ethiopia", "Nigeria", "Congo", "Kenya"]},
    {"q": "What is the holy month in Islam called?", "a": "Ramadan", "choices": ["Hajj", "Ramadan", "Eid", "Zakat"]},
    
    # Additional History Questions
    {"q": "Which ancient African civilization built the pyramids at Meroë?", "a": "Kingdom of Kush", "choices": ["Ancient Egypt", "Kingdom of Kush", "Axum", "Nubia"]},
    {"q": "Who was the famous warrior queen of the Zulu?", "a": "Queen Nandi", "choices": ["Queen Nzinga", "Queen Nandi", "Queen Amina", "Queen Kandake"]},
    {"q": "Which African country was colonized by Belgium?", "a": "Congo", "choices": ["Rwanda", "Congo", "Burundi", "All of these"]},
    {"q": "What year did African Union replace OAU?", "a": "2001", "choices": ["1999", "2000", "2001", "2002"]},
    {"q": "Which African leader wrote 'How Europe Underdeveloped Africa'?", "a": "Walter Rodney", "choices": ["Kwame Nkrumah", "Walter Rodney", "Julius Nyerere", "Frantz Fanon"]}
]

# Global state
current_question = {}
custom_token_requests = {}
player_progress = {}
skipped_questions = {}
paused_games = {}
pending_token_purchases = {}  # Track pending purchases for verification
user_question_pools = {}  # Track used questions per user
all_users = set()  # Track all registered users

# Motivational messages
MOTIVATIONAL_MESSAGES = [
    "🌟 Believe in yourself! Every question you answer makes you smarter!",
    "🚀 Success is a journey, not a destination. Keep learning!",
    "💪 Your potential is limitless! Keep pushing forward!",
    "🎯 Focus on progress, not perfection. You're doing great!",
    "🌈 Every expert was once a beginner. Keep going!",
    "✨ Knowledge is power, and you're gaining it every day!",
    "🔥 Champions are made in practice. Keep quizzing!",
    "🎉 You're amazing! Every effort counts towards your success!",
    "💡 Smart minds ask great questions. You're on the right track!",
    "🏆 Winners never quit, and quitters never win. You've got this!",
    "🌱 Growth happens outside your comfort zone. Keep learning!",
    "⭐ You're not just earning tokens, you're building knowledge!",
    "🎪 Make learning fun! Every quiz is a step forward!",
    "🦋 Transform your mind one question at a time!",
    "🎊 Celebrate small wins! They lead to big victories!"
]

# Configuration constants
ADMIN_CHAT_ID = None  # Set admin chat ID for notifications
ADMIN_CHAT_IDS = []  # Multiple admin chat IDs
USD_TO_CEDIS_RATE = 15.8
PAYSTACK_LINK = "https://paystack.shop/pay/6yjmo6ykwr"

TOKEN_PRICING = {
    "5 tokens": {"amount": 5, "price_cedis": 2, "price_usd": round(2/USD_TO_CEDIS_RATE, 2)},
    "12 tokens": {"amount": 12, "price_cedis": 5, "price_usd": round(5/USD_TO_CEDIS_RATE, 2)},
    "30 tokens": {"amount": 30, "price_cedis": 10, "price_usd": round(10/USD_TO_CEDIS_RATE, 2)}
}

# Updated reward system: 1 token = 20 points
REDEEM_OPTIONS = {
    "1 Token": {"points": 20, "reward": "+1 Token", "cedis": 0.4, "usd": round(0.4/USD_TO_CEDIS_RATE, 2)},
    "3 Tokens": {"points": 60, "reward": "+3 Tokens", "cedis": 1.2, "usd": round(1.2/USD_TO_CEDIS_RATE, 2)},
    "5 Tokens": {"points": 100, "reward": "+5 Tokens", "cedis": 2.0, "usd": round(2.0/USD_TO_CEDIS_RATE, 2)},
    "GHS 2 Airtime": {"points": 150, "reward": "GHS 2 Airtime", "cedis": 2, "usd": round(2/USD_TO_CEDIS_RATE, 2)},
    "GHS 5 Airtime": {"points": 300, "reward": "GHS 5 Airtime", "cedis": 5, "usd": round(5/USD_TO_CEDIS_RATE, 2)},
    "GHS 10 Airtime": {"points": 500, "reward": "GHS 10 Airtime", "cedis": 10, "usd": round(10/USD_TO_CEDIS_RATE, 2)},
    "500MB Data": {"points": 200, "reward": "500MB Internet Data", "cedis": 3, "usd": round(3/USD_TO_CEDIS_RATE, 2)},
    "1GB Data": {"points": 400, "reward": "1GB Internet Data", "cedis": 5, "usd": round(5/USD_TO_CEDIS_RATE, 2)},
    "GHS 5 MoMo": {"points": 300, "reward": "GHS 5 MoMo", "cedis": 5, "usd": round(5/USD_TO_CEDIS_RATE, 2)},
    "GHS 10 MoMo": {"points": 600, "reward": "GHS 10 MoMo", "cedis": 10, "usd": round(10/USD_TO_CEDIS_RATE, 2)},
    "Samsung Phone": {"points": 15000, "reward": "Samsung Galaxy A15", "cedis": 1200, "usd": round(1200/USD_TO_CEDIS_RATE, 2)},
    "iPhone": {"points": 25000, "reward": "iPhone 13", "cedis": 3500, "usd": round(3500/USD_TO_CEDIS_RATE, 2)},
    "Budget Laptop": {"points": 20000, "reward": "HP Laptop 14", "cedis": 2800, "usd": round(2800/USD_TO_CEDIS_RATE, 2)},
    "Gaming Laptop": {"points": 35000, "reward": "Gaming Laptop", "cedis": 5500, "usd": round(5500/USD_TO_CEDIS_RATE, 2)}
}

PAYMENT_INFO = """
💸 <b>Payment Instructions</b>

📲 <b>MTN MoMo</b>: 
• Merchant: <b>474994</b>
• Name: <b>Sufex Technology</b>
• Direct Payment: <a href="https://paystack.shop/pay/6yjmo6ykwr">Pay with Paystack</a>

💰 <b>Crypto (USDT TRC20)</b>: 
• Address: <code>TVd2gJT5Q1ncXqdPmsCFYaiizvgaWbLSGn</code>

📬 Send payment screenshot to @Learn4CashAdmin for verification.
⚡ Tokens are added manually after payment confirmation!
"""

# About Us section
ABOUT_US = """
🎓 <b>About Learn4Cash</b>

We are a revolutionary educational platform that combines learning with earning. Our mission is to make African history and culture accessible while rewarding knowledge seekers.

🌍 <b>Our Vision:</b>
To create a generation of well-informed Africans who are proud of their heritage and financially empowered through education.

🎯 <b>What We Do:</b>
• Interactive African-centered quizzes
• Real rewards for learning achievements
• Fair competition system
• Community building through knowledge

💡 <b>Founded:</b> 2024
📍 <b>Based:</b> Ghana, West Africa
🌟 <b>Mission:</b> Education + Earning = Empowerment
"""

WELCOME_MESSAGE = """
🎓 <b>Welcome to Learn4Cash Quiz Bot!</b>

Hello {name}! Ready to earn while you learn African history and culture?

{about_us}

🎮 <b>How to Play:</b>
• Answer quiz questions to earn points
• Use tokens to play (1 token per question)
• Earn 10 points per correct answer
• Get streak bonuses for consecutive correct answers!

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

🎯 <b>Special Features:</b>
• Skip questions (once per question)
• Pause and resume games
• Track your progress
• Compete on leaderboards

🏆 <b>Fair Play:</b>
• Daily, weekly, monthly winners announced
• Transparent lottery system
• Equal chances for all players

{motivation}

Ready to start your learning journey? 🚀
"""


def create_main_menu():
    """Create the main menu keyboard.""" 
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        KeyboardButton("🎮 Play Quiz"),
        KeyboardButton("💰 Buy Tokens"),
        KeyboardButton("🎁 Redeem Rewards"),
        KeyboardButton("🎁 Daily Reward"),
        KeyboardButton("📊 My Stats"),
        KeyboardButton("📈 Progress"),
        KeyboardButton("👥 Referrals"),
        KeyboardButton("🏆 Leaderboard"),
        KeyboardButton("ℹ️ Help"),
        KeyboardButton("📢 Notify Admin")
    )
    return markup


def create_admin_menu():
    """Create the admin menu keyboard."""
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        KeyboardButton("📊 Admin Dashboard"),
        KeyboardButton("🎯 Run Daily Lottery"),
        KeyboardButton("🎰 Run Weekly Raffle"),
        KeyboardButton("📋 View Pending Tokens"),
        KeyboardButton("✅ Approve Token Purchase"),
        KeyboardButton("📈 User Stats"),
        KeyboardButton("📢 Broadcast Message"),
        KeyboardButton("🔙 Back to User Menu")
    )
    return markup


def is_admin(user_id):
    """Check if user is an admin."""
    return user_id in ADMIN_CHAT_IDS


def notify_admin_token_purchase(user_id, package_info, payment_method):
    """Notify admin about token purchase."""
    try:
        user_data = get_user_data(user_id)
        if not user_data:
            return
        
        message = f"""
🔔 <b>NEW TOKEN PURCHASE NOTIFICATION</b>

👤 <b>User:</b> {user_data['Name']} (ID: {user_id})
📦 <b>Package:</b> {package_info.get('amount', 'Custom')} tokens
💰 <b>Price:</b> ₵{package_info.get('price_cedis', 'N/A')} / ${package_info.get('price_usd', 'N/A')}
💳 <b>Payment Method:</b> {payment_method}
⏰ <b>Time:</b> {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC

📱 <b>User Contact:</b> @{user_data.get('Username', 'No username')}

⚡ Use Admin Dashboard to approve purchase
        """
        
        for admin_id in ADMIN_CHAT_IDS:
            try:
                bot.send_message(admin_id, message)
            except Exception as e:
                logger.error(f"Failed to notify admin {admin_id}: {e}")
                
    except Exception as e:
        logger.error(f"Error notifying admin: {e}")


def log_token_transaction(user_id, transaction_type, amount, details, payment_method=None):
    """Enhanced logging for token transactions."""
    try:
        timestamp = datetime.utcnow().isoformat()
        log_entry = f"{timestamp} | {transaction_type} | User: {user_id} | Amount: {amount} | Details: {details}"
        if payment_method:
            log_entry += f" | Payment: {payment_method}"
        
        logger.info(f"Token Transaction: {log_entry}")
        
        # Log to sheet
        if transaction_type in ["BUY", "REDEEM"]:
            log_token_purchase(user_id, f"{transaction_type}_{details}", amount)
            
    except Exception as e:
        logger.error(f"Error logging token transaction: {e}")


def get_random_quiz(user_id):
    """Get a random quiz that hasn't been used by this user recently."""
    if user_id not in user_question_pools:
        user_question_pools[user_id] = []
    
    used_questions = user_question_pools[user_id]
    available_questions = [q for q in quizzes if q['q'] not in used_questions]
    
    # If all questions used, reset pool
    if not available_questions:
        user_question_pools[user_id] = []
        available_questions = quizzes
    
    selected_quiz = random.choice(available_questions)
    user_question_pools[user_id].append(selected_quiz['q'])
    
    return selected_quiz


def init_player_progress(user_id):
    """Initialize player progress tracking."""
    if user_id not in player_progress:
        player_progress[user_id] = {
            'current_streak': 0,
            'best_streak': 0,
            'total_correct': 0,
            'total_questions': 0,
            'questions_until_bonus': 10,
            'skips_used': 0,
            'games_paused': 0
        }


def update_player_progress(user_id, correct=True):
    """Update player progress after answering a question."""
    if user_id not in player_progress:
        init_player_progress(user_id)
    
    progress = player_progress[user_id]
    progress['total_questions'] += 1
    
    if correct:
        progress['current_streak'] += 1
        progress['total_correct'] += 1
        progress['best_streak'] = max(progress['best_streak'], progress['current_streak'])
        
        if progress['current_streak'] == 10:
            progress['questions_until_bonus'] = 10
            progress['current_streak'] = 0
            return True
    else:
        progress['current_streak'] = 0
    
    return False


def get_leaderboard():
    """Get leaderboard data from all users."""
    try:
        sheet_manager = get_sheet_manager()
        all_records = sheet_manager.main_sheet.get_all_records()
        
        # Sort by points descending
        leaderboard = sorted(all_records, key=lambda x: int(x.get('Points', 0)), reverse=True)
        return leaderboard[:10]  # Top 10
    except Exception as e:
        logger.error(f"Error getting leaderboard: {e}")
        return []


def broadcast_to_all_users(message):
    """Broadcast a message to all registered users."""
    try:
        sheet_manager = get_sheet_manager()
        all_records = sheet_manager.main_sheet.get_all_records()
        
        for record in all_records:
            user_id = record.get('UserID')
            if user_id:
                try:
                    bot.send_message(int(user_id), message)
                    time.sleep(0.1)  # Avoid rate limiting
                except Exception as e:
                    logger.error(f"Failed to send message to {user_id}: {e}")
    except Exception as e:
        logger.error(f"Error broadcasting message: {e}")


def conduct_daily_lottery():
    """Conduct daily lottery and announce winner."""
    try:
        sheet_manager = get_sheet_manager()
        all_records = sheet_manager.main_sheet.get_all_records()
        
        if not all_records:
            return
        
        # Select random winner
        winner = random.choice(all_records)
        winner_id = winner.get('UserID')
        winner_name = winner.get('Name', 'Player')
        
        # Add 5 bonus tokens to winner
        current_tokens = int(winner.get('Tokens', 0))
        current_points = int(winner.get('Points', 0))
        update_user_tokens_points(int(winner_id), current_tokens + 5, current_points)
        
        # Announce to all users
        announcement = f"""
🏆 <b>DAILY WINNER ANNOUNCEMENT!</b>

🎉 Congratulations to our daily winner!
👤 Winner: {winner_name} (ID: {winner_id})
🎁 Prize: 5 bonus tokens!

🔥 <b>Keep playing to be tomorrow's winner!</b>
💪 Every question you answer increases your chances!

🎮 Ready to play? Use the menu below!
        """
        
        broadcast_to_all_users(announcement)
        logger.info(f"Daily winner: {winner_id} ({winner_name})")
        
    except Exception as e:
        logger.error(f"Error conducting daily lottery: {e}")


def conduct_weekly_raffle():
    """Conduct weekly raffle with bigger prizes."""
    try:
        sheet_manager = get_sheet_manager()
        all_records = sheet_manager.main_sheet.get_all_records()
        
        if not all_records:
            return
        
        # Select random winner
        winner = random.choice(all_records)
        winner_id = winner.get('UserID')
        winner_name = winner.get('Name', 'Player')
        
        # Add bigger prize (20 tokens + 500 points)
        current_tokens = int(winner.get('Tokens', 0))
        current_points = int(winner.get('Points', 0))
        update_user_tokens_points(int(winner_id), current_tokens + 20, current_points + 500)
        
        # Announce to all users
        announcement = f"""
🎊 <b>WEEKLY RAFFLE WINNER!</b>

🏆 Congratulations to our weekly raffle winner!
👤 Winner: {winner_name} (ID: {winner_id})
🎁 Grand Prize: 20 tokens + 500 points!

🌟 <b>Weekly raffles every Sunday!</b>
📈 Keep playing to increase your chances!

🎮 Join the action now!
        """
        
        broadcast_to_all_users(announcement)
        logger.info(f"Weekly winner: {winner_id} ({winner_name})")
        
    except Exception as e:
        logger.error(f"Error conducting weekly raffle: {e}")


@bot.message_handler(commands=['start'])
def start_handler(message):
    """Handle the /start command."""
    chat_id = message.chat.id
    user = message.from_user
    all_users.add(chat_id)

    # Parse referral code if present
    referrer_id = None
    if len(message.text.split()) > 1:
        try:
            referrer_id = int(message.text.split()[1])
        except ValueError:
            pass

    # Register user
    success = register_user(
        user_id=chat_id,
        name=user.first_name or "User",
        username=user.username or "",
        referrer_id=referrer_id
    )

    # Process referral rewards (2 tokens instead of 1)
    if success and referrer_id:
        referrer_data = get_user_data(referrer_id)
        if referrer_data:
            new_tokens = referrer_data['Tokens'] + 2
            update_user_tokens_points(referrer_id, new_tokens, referrer_data['Points'])
            increment_referral_count(referrer_id)
            bot.send_message(referrer_id, "🎉 <b>New Referral!</b>\n\n✅ +2 tokens added to your account!\n💰 Thanks for spreading the word! 🚀")

    # Initialize progress tracking
    init_player_progress(chat_id)

    # Check for daily reward
    daily_reward_given = check_and_give_daily_reward(chat_id)

    # Send motivational message
    motivation = random.choice(MOTIVATIONAL_MESSAGES)

    welcome_msg = WELCOME_MESSAGE.format(
        name=user.first_name,
        about_us=ABOUT_US,
        motivation=motivation
    )

    if daily_reward_given:
        welcome_msg += "\n\n🎉 <b>Daily Bonus:</b> +1 free token added to your account!"

    bot.send_message(chat_id, welcome_msg, reply_markup=create_main_menu())


@bot.message_handler(func=lambda message: message.text == "🎮 Play Quiz")
def play_handler(message):
    """Handle the play quiz request."""
    chat_id = message.chat.id
    user = get_user_data(chat_id)

    if not user:
        bot.send_message(chat_id, "Please /start first.")
        return

    if user['Tokens'] <= 0:
        bot.send_message(chat_id, "⚠️ You don't have any tokens! Use '💰 Buy Tokens' to continue playing.")
        return

    # Check if user has a paused game
    if chat_id in paused_games:
        markup = InlineKeyboardMarkup()
        markup.add(
            InlineKeyboardButton("▶️ Resume Game", callback_data="resume_game"),
            InlineKeyboardButton("🆕 New Game", callback_data="new_game")
        )
        bot.send_message(chat_id, "You have a paused game. What would you like to do?", reply_markup=markup)
        return

    # If there's an active question, continue with it instead of blocking
    if chat_id in current_question:
        question_data = current_question[chat_id]
        answer_markup = InlineKeyboardMarkup()
        for choice in question_data['choices']:
            answer_markup.add(InlineKeyboardButton(choice, callback_data=f"answer:{choice}"))
        
        control_buttons = [InlineKeyboardButton("⏸️ Pause", callback_data="pause_game")]
        answer_markup.add(control_buttons[0])
        
        bot.send_message(
            chat_id,
            f"🧠 <b>Continue your current question:</b>\n{question_data['question']}",
            reply_markup=answer_markup
        )
        return

    start_new_quiz(chat_id)


def start_new_quiz(chat_id):
    """Start a new quiz question."""
    user = get_user_data(chat_id)
    
    # Deduct token
    new_tokens = user['Tokens'] - 1
    update_user_tokens_points(chat_id, new_tokens, user['Points'])

    # Select random quiz using improved randomization
    quiz = get_random_quiz(chat_id)
    current_question[chat_id] = {
        'correct': quiz['a'],
        'question': quiz['q'],
        'choices': quiz['choices'],
        'skipped': False
    }

    # Initialize progress if needed
    init_player_progress(chat_id)

    # Check if user can skip
    can_skip = not skipped_questions.get(chat_id, {}).get(quiz['q'], False)

    # Create answer buttons
    answer_markup = InlineKeyboardMarkup()
    for choice in quiz['choices']:
        answer_markup.add(InlineKeyboardButton(choice, callback_data=f"answer:{choice}"))
    
    # Add control buttons
    control_buttons = []
    if can_skip:
        control_buttons.append(InlineKeyboardButton("⏭️ Skip", callback_data="skip_question"))
    control_buttons.append(InlineKeyboardButton("⏸️ Pause", callback_data="pause_game"))
    
    if control_buttons:
        if len(control_buttons) == 2:
            answer_markup.add(control_buttons[0], control_buttons[1])
        else:
            answer_markup.add(control_buttons[0])

    progress = player_progress[chat_id]
    streak_info = f"\n🔥 Current Streak: {progress['current_streak']}"
    bonus_info = f"\n🎁 Streak Bonus: {10 - progress['current_streak']} more for 3 tokens!"

    bot.send_message(
        chat_id, 
        f"🧠 <b>Question:</b>\n{quiz['q']}\n\n💰 Tokens: {new_tokens}{streak_info}{bonus_info}", 
        reply_markup=answer_markup
    )


@bot.message_handler(func=lambda message: message.text == "💰 Buy Tokens")
def buytokens_handler(message):
    """Handle the buy tokens request."""
    chat_id = message.chat.id
    user = get_user_data(chat_id)

    if not user:
        bot.send_message(chat_id, "Please /start first.")
        return

    markup = InlineKeyboardMarkup()
    for label, data in TOKEN_PRICING.items():
        price_text = f"{label} (₵{data['price_cedis']} / ${data['price_usd']})"
        markup.add(InlineKeyboardButton(price_text, callback_data=f"buy:{label}"))

    markup.add(InlineKeyboardButton("🎯 Custom Amount (No Limit)", callback_data="buy:custom"))

    bot.send_message(
        chat_id,
        f"💰 <b>Choose a token package:</b>\n\n{PAYMENT_INFO}\n\n💱 <b>Exchange Rate:</b> $1 = ₵{USD_TO_CEDIS_RATE}",
        reply_markup=markup
    )


@bot.message_handler(func=lambda message: message.text == "🎁 Redeem Rewards")
def redeem_handler(message):
    """Handle the redeem rewards request."""
    chat_id = message.chat.id
    user = get_user_data(chat_id)

    if not user:
        bot.send_message(chat_id, "Please /start first.")
        return

    points = user['Points']
    markup = InlineKeyboardMarkup()

    # Show rewards based on point requirements
    for label, reward in REDEEM_OPTIONS.items():
        if points >= reward['points']:
            price_text = f"{label} ({reward['points']} pts) - ₵{reward['cedis']} / ${reward['usd']}"
            markup.add(InlineKeyboardButton(
                text=price_text, 
                callback_data=f"redeem:{label}"
            ))

    if markup.keyboard:
        bot.send_message(
            chat_id, 
            f"🏆 <b>Available Rewards:</b>\n\nYour Points: {points}\n💱 Exchange Rate: $1 = ₵{USD_TO_CEDIS_RATE}\n\n🎁 <b>NEW:</b> 1 token = 20 points\n💯 Points above 100 unlock premium rewards!\n\nChoose a reward to redeem:", 
            reply_markup=markup
        )
    else:
        bot.send_message(chat_id, f"⚠️ You need more points to redeem rewards.\n\n💰 Your Points: {points}\n🎯 Minimum: 20 points for 1 token\n💎 Premium rewards: 100+ points")


@bot.message_handler(func=lambda message: message.text == "🏆 Leaderboard")
def leaderboard_handler(message):
    """Handle the leaderboard request."""
    chat_id = message.chat.id
    
    leaderboard = get_leaderboard()
    
    if not leaderboard:
        bot.send_message(chat_id, "🏆 <b>Leaderboard</b>\n\nNo data available yet. Start playing to see rankings!")
        return
    
    leaderboard_text = "🏆 <b>Top 10 Players</b>\n\n"
    
    for i, player in enumerate(leaderboard, 1):
        name = player.get('Name', 'Unknown')
        points = player.get('Points', 0)
        tokens = player.get('Tokens', 0)
        
        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
        leaderboard_text += f"{medal} <b>{name}</b>\n   💎 {points} points | 🪙 {tokens} tokens\n\n"
    
    leaderboard_text += "🎮 Keep playing to climb the ranks!"
    
    bot.send_message(chat_id, leaderboard_text)


@bot.message_handler(func=lambda message: message.text.isdigit() and message.chat.id in custom_token_requests)
def custom_token_handler(message):
    """Handle custom token amount input."""
    chat_id = message.chat.id
    amount = int(message.text)
    
    if amount < 1:
        bot.send_message(chat_id, "❌ Please enter a valid number of tokens (minimum 1).")
        return
    
    price_cedis = round(amount * 0.4, 2)
    price_usd = round(price_cedis / USD_TO_CEDIS_RATE, 2)
    
    # Store in pending purchases
    pending_token_purchases[chat_id] = {
        'package': 'Custom',
        'amount': amount,
        'price_cedis': price_cedis,
        'price_usd': price_usd
    }
    
    # Clear custom request
    if chat_id in custom_token_requests:
        del custom_token_requests[chat_id]
    
    # Log custom purchase attempt
    log_token_transaction(chat_id, "CUSTOM_BUY_ATTEMPT", amount, f"Custom_{amount}_tokens")
    
    payment_markup = InlineKeyboardMarkup()
    payment_markup.add(
        InlineKeyboardButton("📱 Pay via MTN MoMo", callback_data="pay_momo"),
        InlineKeyboardButton("₿ Pay via USDT", callback_data="pay_crypto")
    )
    
    bot.send_message(
        chat_id,
        f"💰 <b>Custom Order:</b> {amount} tokens\n"
        f"💸 Price: ₵{price_cedis} / ${price_usd}\n\n"
        f"{PAYMENT_INFO}\n"
        "⚠️ <b>Important:</b> Tokens will be added after payment verification.\n\n"
        "Choose your payment method:",
        reply_markup=payment_markup
    )


@bot.callback_query_handler(func=lambda call: call.data.startswith("buy:"))
def buy_callback_handler(call):
    """Handle token purchase callbacks."""
    chat_id = call.message.chat.id
    package_label = call.data.split("buy:")[1]

    bot.answer_callback_query(call.id)

    if package_label == "custom":
        custom_token_requests[chat_id] = {'waiting_for_amount': True}
        bot.send_message(
            chat_id,
            "🎯 <b>Custom Token Purchase</b>\n\n"
            "Please enter the number of tokens you want (no limit):\n\n"
            f"💡 <i>Rate: ₵0.40 per token (${round(0.4/USD_TO_CEDIS_RATE, 3)} USD)</i>"
        )
        return

    package_info = TOKEN_PRICING[package_label]
    
    # Store pending purchase for verification
    pending_token_purchases[chat_id] = {
        'package': package_label,
        'amount': package_info['amount'],
        'price_cedis': package_info['price_cedis'],
        'price_usd': package_info['price_usd']
    }
    
    # Log purchase attempt
    log_token_transaction(chat_id, "BUY_ATTEMPT", package_info['amount'], package_label)
    
    payment_markup = InlineKeyboardMarkup()
    payment_markup.add(
        InlineKeyboardButton("📱 Pay via MTN MoMo", callback_data=f"pay_momo:{package_label}"),
        InlineKeyboardButton("₿ Pay via USDT", callback_data=f"pay_crypto:{package_label}")
    )

    bot.send_message(
        chat_id,
        f"💰 <b>Selected:</b> {package_label}\n"
        f"💸 Price: ₵{package_info['price_cedis']} / ${package_info['price_usd']}\n\n"
        f"{PAYMENT_INFO}\n"
        "⚠️ <b>Important:</b> Tokens will be added after payment verification by admin.\n\n"
        "Choose your payment method:",
        reply_markup=payment_markup
    )


@bot.callback_query_handler(func=lambda call: call.data.startswith("pay_"))
def payment_method_handler(call):
    """Handle payment method selection."""
    chat_id = call.message.chat.id
    bot.answer_callback_query(call.id)
    
    # Determine payment method
    payment_method = "MTN MoMo" if "momo" in call.data else "USDT Crypto"
    
    # Log payment method selection
    if chat_id in pending_token_purchases:
        purchase_info = pending_token_purchases[chat_id]
        log_token_transaction(chat_id, "PAYMENT_METHOD", purchase_info['amount'], purchase_info['package'], payment_method)
        
        # Notify admin
        notify_admin_token_purchase(chat_id, purchase_info, payment_method)
    
    if "momo" in call.data:
        bot.send_message(
            chat_id,
            f"📱 <b>MTN MoMo Payment</b>\n\n"
            f"• Send to merchant: <b>474994</b>\n"
            f"• Name: <b>Sufex Technology</b>\n"
            f"• Direct Payment: <a href='{PAYSTACK_LINK}'>Pay with Paystack</a>\n\n"
            f"📸 Send payment screenshot to @Learn4CashAdmin\n"
            f"📢 Use '📢 Notify Admin' button to alert admin\n"
            f"⏳ Tokens will be added after verification!"
        )
    elif "crypto" in call.data:
        bot.send_message(
            chat_id,
            "₿ <b>USDT Payment (TRC20)</b>\n\n"
            "• Address: <code>TVd2gJT5Q1ncXqdPmsCFYaiizvgaWbLSGn</code>\n\n"
            "📸 Send transaction screenshot to @Learn4CashAdmin\n"
            "📢 Use '📢 Notify Admin' button to alert admin\n"
            "⏳ Tokens will be added after verification!"
        )


@bot.message_handler(func=lambda message: message.text == "📊 My Stats")
def stats_handler(message):
    """Handle the stats request."""
    chat_id = message.chat.id
    user = get_user_data(chat_id)

    if not user:
        bot.send_message(chat_id, "Please /start first.")
        return

    init_player_progress(chat_id)
    progress = player_progress[chat_id]
    
    accuracy = (progress['total_correct'] / progress['total_questions'] * 100) if progress['total_questions'] > 0 else 0

    stats_msg = f"""
📊 <b>Your Stats</b>

👤 Name: {user['Name']}
🔐 Tokens: {user['Tokens']}
🧠 Points: {user['Points']} (1 token = 20 points)
👥 Referrals: {int(user['ReferralEarnings'])}

🎯 <b>Performance:</b>
• Accuracy: {accuracy:.1f}%
• Current Streak: {progress['current_streak']}
• Best Streak: {progress['best_streak']}

💰 MoMo: Not needed for payments
    """

    bot.send_message(chat_id, stats_msg)


@bot.message_handler(func=lambda message: message.text == "📈 Progress")
def progress_handler(message):
    """Handle the progress request."""
    chat_id = message.chat.id
    user = get_user_data(chat_id)

    if not user:
        bot.send_message(chat_id, "Please /start first.")
        return

    init_player_progress(chat_id)
    progress = player_progress[chat_id]
    
    accuracy = (progress['total_correct'] / progress['total_questions'] * 100) if progress['total_questions'] > 0 else 0

    progress_msg = f"""
📈 <b>Your Progress Report</b>

🎯 <b>Performance:</b>
• Accuracy: {accuracy:.1f}%
• Total Questions: {progress['total_questions']}
• Correct Answers: {progress['total_correct']}

🔥 <b>Streaks:</b>
• Current Streak: {progress['current_streak']}
• Best Streak: {progress['best_streak']}
• Next Bonus: {10 - progress['current_streak']} correct answers

🎮 <b>Game Stats:</b>
• Questions Skipped: {progress['skips_used']}
• Games Paused: {progress['games_paused']}

🏆 <b>Streak Bonus:</b>
Get 10 correct answers in a row to earn 3 bonus tokens!
    """

    bot.send_message(chat_id, progress_msg)


@bot.message_handler(func=lambda message: message.text == "👥 Referrals")
def referrals_handler(message):
    """Handle the referrals request."""
    chat_id = message.chat.id
    user = get_user_data(chat_id)

    if not user:
        bot.send_message(chat_id, "Please /start first.")
        return

    referral_link = f"https://t.me/Learn4CashBot?start={chat_id}"
    referral_msg = f"""
👥 <b>Referral Program</b>

🎁 Earn 2 TOKENS for each friend you refer!
📊 Total referrals: {int(user['ReferralEarnings'])}

🔗 Your referral link:
<code>{referral_link}</code>

💡 <b>How it works:</b>
• Share your link with friends
• They click and start the bot
• You automatically get 2 tokens!
• No limits on referrals!

Share this link with friends to earn rewards! 🚀
    """

    bot.send_message(chat_id, referral_msg)


@bot.message_handler(func=lambda message: message.text == "🎁 Daily Reward")
def daily_reward_handler(message):
    """Handle the daily reward request."""
    chat_id = message.chat.id
    user = get_user_data(chat_id)

    if not user:
        bot.send_message(chat_id, "Please /start first.")
        return

    daily_reward_given = check_and_give_daily_reward(chat_id)
    motivation = random.choice(MOTIVATIONAL_MESSAGES)

    if daily_reward_given:
        updated_user = get_user_data(chat_id)
        bot.send_message(
            chat_id,
            f"🎉 <b>Daily Reward Claimed!</b>\n\n"
            f"✅ +1 free token added to your account!\n"
            f"💰 Total tokens: {updated_user['Tokens']}\n\n"
            f"{motivation}"
        )
    else:
        bot.send_message(
            chat_id,
            f"⏰ <b>Daily Reward Already Claimed!</b>\n\n"
            f"Come back tomorrow for your next free token!\n"
            f"💰 Current tokens: {user['Tokens']}\n\n"
            f"{motivation}"
        )


@bot.message_handler(func=lambda message: message.text == "📢 Notify Admin")
def notify_admin_handler(message):
    """Handle admin notification requests."""
    chat_id = message.chat.id
    user = get_user_data(chat_id)
    
    if not user:
        bot.send_message(chat_id, "Please /start first.")
        return
    
    # Check if user has pending token purchase
    if chat_id in pending_token_purchases:
        purchase_info = pending_token_purchases[chat_id]
        notify_admin_token_purchase(chat_id, purchase_info, "User Request")
        bot.send_message(
            chat_id,
            "✅ <b>Admin Notified!</b>\n\n"
            "Your token purchase notification has been sent to the admin.\n"
            "You will receive your tokens after payment verification.\n\n"
            "📬 Make sure you've sent payment proof to @Learn4CashAdmin"
        )
    else:
        bot.send_message(
            chat_id,
            "📢 <b>Contact Admin</b>\n\n"
            "No pending token purchase found.\n"
            "For general inquiries, contact @Learn4CashAdmin directly."
        )


@bot.message_handler(func=lambda message: message.text == "📊 Admin Dashboard" and is_admin(message.chat.id))
def admin_dashboard_handler(message):
    """Handle admin dashboard request."""
    chat_id = message.chat.id
    
    try:
        sheet_manager = get_sheet_manager()
        all_users = sheet_manager.get_all_users()
        
        total_users = len(all_users)
        total_tokens = sum(int(user.get('Tokens', 0)) for user in all_users)
        total_points = sum(int(user.get('Points', 0)) for user in all_users)
        pending_purchases = len(pending_token_purchases)
        
        dashboard_msg = f"""
📊 <b>ADMIN DASHBOARD</b>

👥 <b>User Statistics:</b>
• Total Users: {total_users}
• Total Tokens in System: {total_tokens}
• Total Points in System: {total_points}
• Pending Token Purchases: {pending_purchases}

🎯 <b>Quick Actions:</b>
• Run Daily Lottery
• Run Weekly Raffle  
• View Pending Purchases
• Approve Token Purchases
• Broadcast Messages

📈 <b>System Status:</b> ✅ Online
⏰ <b>Last Update:</b> {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC
        """
        
        bot.send_message(chat_id, dashboard_msg, reply_markup=create_admin_menu())
        
    except Exception as e:
        bot.send_message(chat_id, f"❌ Dashboard Error: {str(e)}")


@bot.message_handler(func=lambda message: message.text == "🎯 Run Daily Lottery" and is_admin(message.chat.id))
def admin_run_daily_lottery(message):
    """Admin run daily lottery manually."""
    chat_id = message.chat.id
    
    try:
        conduct_daily_lottery()
        bot.send_message(chat_id, "✅ Daily lottery conducted successfully!")
    except Exception as e:
        bot.send_message(chat_id, f"❌ Error conducting lottery: {str(e)}")


@bot.message_handler(func=lambda message: message.text == "🎰 Run Weekly Raffle" and is_admin(message.chat.id))
def admin_run_weekly_raffle(message):
    """Admin run weekly raffle manually."""
    chat_id = message.chat.id
    
    try:
        conduct_weekly_raffle()
        bot.send_message(chat_id, "✅ Weekly raffle conducted successfully!")
    except Exception as e:
        bot.send_message(chat_id, f"❌ Error conducting raffle: {str(e)}")


@bot.message_handler(func=lambda message: message.text == "📋 View Pending Tokens" and is_admin(message.chat.id))
def admin_view_pending_tokens(message):
    """View pending token purchases."""
    chat_id = message.chat.id
    
    if not pending_token_purchases:
        bot.send_message(chat_id, "✅ No pending token purchases.")
        return
    
    pending_msg = "📋 <b>PENDING TOKEN PURCHASES</b>\n\n"
    
    for user_id, purchase_info in pending_token_purchases.items():
        user_data = get_user_data(user_id)
        user_name = user_data['Name'] if user_data else 'Unknown'
        
        pending_msg += f"👤 <b>{user_name}</b> (ID: {user_id})\n"
        pending_msg += f"📦 {purchase_info.get('amount', 'Custom')} tokens\n"
        pending_msg += f"💰 ₵{purchase_info.get('price_cedis', 'N/A')}\n\n"
    
    bot.send_message(chat_id, pending_msg)


@bot.message_handler(func=lambda message: message.text == "🔙 Back to User Menu" and is_admin(message.chat.id))
def admin_back_to_user_menu(message):
    """Return to user menu from admin menu."""
    chat_id = message.chat.id
    bot.send_message(chat_id, "🔙 Returned to user menu", reply_markup=create_main_menu())


@bot.message_handler(func=lambda message: message.text == "ℹ️ Help")
def help_handler(message):
    """Handle the help request."""
    help_msg = """
ℹ️ <b>How to Use Learn4Cash Bot</b>

🎮 <b>Playing:</b>
• Use tokens to answer quiz questions
• Earn 10 points per correct answer
• You start with 3 free tokens
• Skip questions once per question
• Pause and resume games anytime

🔥 <b>Streak Bonuses:</b>
• Get 10 correct answers in a row
• Earn 3 bonus tokens automatically
• Track your progress in stats

💰 <b>Buying Tokens:</b>
• Choose from packages or custom amount
• No limit on custom purchases
• Pay via MTN MoMo or USDT crypto
• Manual verification by admin required

🎁 <b>Daily Rewards:</b>
• Get 1 free token every day
• Just visit the bot daily to claim

🎁 <b>Redeeming:</b>
• Exchange points for rewards (1 token = 20 points)
• Tokens, airtime, data, MoMo, phones, laptops
• See values in both Cedis and USD

👥 <b>Referrals:</b>
• Earn 2 tokens per referral (auto-processed)
• Share your referral link
• Unlimited earning potential

🏆 <b>Competitions:</b>
• Daily winners announced to all
• Weekly random raffles
• Fair lottery system

📈 <b>Progress Tracking:</b>
• Monitor accuracy and streaks
• See detailed statistics
• Track your improvement

📢 <b>Admin Contact:</b>
• Use "📢 Notify Admin" for token purchase issues
• Contact @Learn4CashAdmin for other support

Need help? Contact @Learn4CashAdmin
    """

    # Show admin menu if user is admin
    if is_admin(message.chat.id):
        markup = create_admin_menu()
    else:
        markup = create_main_menu()
    
    bot.send_message(message.chat.id, help_msg, reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data == "skip_question")
def skip_question_handler(call):
    """Handle question skipping."""
    chat_id = call.message.chat.id
    bot.answer_callback_query(call.id)

    if chat_id not in current_question:
        return

    question = current_question[chat_id]['question']
    
    if chat_id not in skipped_questions:
        skipped_questions[chat_id] = {}
    skipped_questions[chat_id][question] = True

    init_player_progress(chat_id)
    player_progress[chat_id]['skips_used'] += 1

    bot.send_message(chat_id, "⏭️ Question skipped! Starting new question...")
    
    del current_question[chat_id]
    time.sleep(1)
    start_new_quiz(chat_id)


@bot.callback_query_handler(func=lambda call: call.data == "pause_game")
def pause_game_handler(call):
    """Handle game pausing."""
    chat_id = call.message.chat.id
    bot.answer_callback_query(call.id)

    if chat_id not in current_question:
        return

    paused_games[chat_id] = current_question[chat_id]
    del current_question[chat_id]

    init_player_progress(chat_id)
    player_progress[chat_id]['games_paused'] += 1

    bot.send_message(
        chat_id, 
        "⏸️ <b>Game Paused</b>\n\nYour question has been saved. Use '🎮 Play Quiz' to resume or start a new game.",
        reply_markup=create_main_menu()
    )


@bot.callback_query_handler(func=lambda call: call.data == "resume_game")
def resume_game_handler(call):
    """Handle game resuming."""
    chat_id = call.message.chat.id
    bot.answer_callback_query(call.id)

    if chat_id not in paused_games:
        bot.send_message(chat_id, "❌ No paused game found.")
        return

    current_question[chat_id] = paused_games[chat_id]
    del paused_games[chat_id]

    question_data = current_question[chat_id]
    
    answer_markup = InlineKeyboardMarkup()
    for choice in question_data['choices']:
        answer_markup.add(InlineKeyboardButton(choice, callback_data=f"answer:{choice}"))
    
    control_buttons = [InlineKeyboardButton("⏸️ Pause", callback_data="pause_game")]
    answer_markup.add(control_buttons[0])

    bot.send_message(
        chat_id,
        f"▶️ <b>Game Resumed</b>\n\n🧠 <b>Question:</b>\n{question_data['question']}",
        reply_markup=answer_markup
    )


@bot.callback_query_handler(func=lambda call: call.data == "new_game")
def new_game_handler(call):
    """Handle starting a new game."""
    chat_id = call.message.chat.id
    bot.answer_callback_query(call.id)

    if chat_id in paused_games:
        del paused_games[chat_id]

    start_new_quiz(chat_id)


@bot.callback_query_handler(func=lambda call: call.data.startswith("answer:"))
def answer_handler(call):
    """Handle quiz answer callbacks."""
    chat_id = call.message.chat.id
    user = get_user_data(chat_id)

    if not user or chat_id not in current_question:
        bot.answer_callback_query(call.id, "❌ Invalid question!")
        return

    answer = call.data.split("answer:")[1]
    correct = current_question[chat_id]['correct']
    tokens = user['Tokens']
    points = user['Points']

    bonus_earned = update_player_progress(chat_id, answer == correct)

    if answer == correct:
        points += 10
        bot.answer_callback_query(call.id, "✅ Correct! +10 points")
        
        message = "🎉 Correct answer! You earned <b>10 points</b>!"
        
        if bonus_earned:
            tokens += 3
            update_user_tokens_points(chat_id, tokens, points)
            message += f"\n\n🔥 <b>STREAK BONUS!</b>\n✅ +3 tokens for 10 correct answers in a row!\n💰 Total tokens: {tokens}"
            log_token_purchase(chat_id, "STREAK_BONUS", 3)
        else:
            update_user_tokens_points(chat_id, tokens, points)
            
        bot.send_message(chat_id, message)
    else:
        bot.answer_callback_query(call.id, "❌ Wrong answer!")
        bot.send_message(chat_id, f"❌ Wrong! The correct answer was: <b>{correct}</b>")
        update_user_tokens_points(chat_id, tokens, points)

    progress = player_progress[chat_id]
    bot.send_message(chat_id, f"💰 Balance: {tokens} tokens | {points} points\n🔥 Current Streak: {progress['current_streak']}")

    del current_question[chat_id]

    if tokens > 0:
        time.sleep(2)
        start_new_quiz(chat_id)
    else:
        bot.send_message(
            chat_id, 
            "🔚 You've run out of tokens. Use '💰 Buy Tokens' to continue playing!",
            reply_markup=create_main_menu()
        )


@bot.callback_query_handler(func=lambda call: call.data.startswith("redeem:"))
def redeem_callback_handler(call):
    """Handle redemption callbacks."""
    chat_id = call.message.chat.id
    label = call.data.split("redeem:")[1]
    reward = REDEEM_OPTIONS[label]
    user = get_user_data(chat_id)

    if user['Points'] < reward['points']:
        bot.answer_callback_query(call.id, "❌ Not enough points!")
        return

    new_points = user['Points'] - reward['points']

    if "Token" in label:
        token_amount = int(label.split()[0])
        new_tokens = user['Tokens'] + token_amount
        update_user_tokens_points(chat_id, new_tokens, new_points)

        # Log token redemption
        log_token_transaction(chat_id, "REDEEM", token_amount, f"Redeemed_{label}")

        bot.answer_callback_query(call.id, f"✅ {token_amount} token(s) added!")
        
        bot.send_message(
            chat_id, 
            f"🎉 <b>Redemption Successful!</b>\n\n"
            f"✅ <b>+{token_amount} token(s)</b> added!\n"
            f"💰 Total tokens: <b>{new_tokens}</b>\n"
            f"🧠 Points remaining: <b>{new_points}</b>\n"
            f"💱 Value: ₵{reward['cedis']} / ${reward['usd']}"
        )
    else:
        update_user_tokens_points(chat_id, user['Tokens'], new_points)
        
        # Log non-token redemption
        log_token_transaction(chat_id, "REDEEM", 0, f"Redeemed_{label}_for_{reward['points']}_points")
        
        bot.answer_callback_query(call.id, "✅ Redemption submitted!")
        
        bot.send_message(
            chat_id,
            f"🎁 <b>Redemption Request Submitted!</b>\n\n"
            f"🏆 Reward: <b>{reward['reward']}</b>\n"
            f"💱 Value: ₵{reward['cedis']} / ${reward['usd']}\n"
            f"📉 Points used: <b>{reward['points']}</b>\n"
            f"🧠 Remaining: <b>{new_points}</b>\n\n"
            f"📬 Admin will process within 24 hours.\n"
            f"📞 Contact @Learn4CashAdmin for updates."
        )

    log_point_redemption(chat_id, label, reward['points'], datetime.utcnow().isoformat())


@bot.message_handler(func=lambda message: True)
def default_handler(message):
    """Handle all other messages."""
    chat_id = message.chat.id

    if chat_id in custom_token_requests and custom_token_requests[chat_id].get('waiting_for_amount'):
        if message.text.isdigit():
            custom_token_handler(message)
        else:
            bot.send_message(chat_id, "Please enter a valid number for tokens.")
        return

    bot.send_message(
        chat_id, 
        "Please use the menu buttons below or type /start to begin.",
        reply_markup=create_main_menu()
    )


def schedule_events():
    """Schedule daily announcements and weekly raffles."""
    import schedule
    
    schedule.every().day.at("20:00").do(conduct_daily_lottery)
    schedule.every().sunday.at("21:00").do(conduct_weekly_raffle)
    
    while True:
        schedule.run_pending()
        time.sleep(60)


if __name__ == "__main__":
    logger.info("Starting Learn4Cash Quiz Bot...")

    # Set admin chat IDs (replace with actual admin user IDs)
    # Example: ADMIN_CHAT_IDS = [123456789, 987654321]
    # For now, leave empty - add your admin IDs here
    ADMIN_CHAT_IDS = []  # Add admin user IDs here

    # Start event scheduler in a separate thread
    scheduler_thread = threading.Thread(target=schedule_events)
    scheduler_thread.daemon = True
    scheduler_thread.start()

    logger.info(f"Admin system initialized. Admins: {len(ADMIN_CHAT_IDS)}")

    try:
        bot.infinity_polling(timeout=10, long_polling_timeout=5)
    except Exception as e:
        logger.error(f"Bot error: {e}")
        time.sleep(5)
        bot.infinity_polling(timeout=10, long_polling_timeout=5)
