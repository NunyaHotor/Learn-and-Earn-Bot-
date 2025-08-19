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
from telebot import TeleBot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

from sheet_manager_fix import (
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
from ui_enhancer_fixed import ui_enhancer
from user_preference_service import user_preference_service

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
bot = TeleBot(API_KEY, parse_mode='HTML')
translator = Translator()

USD_TO_CEDIS_RATE = 11.8
PAYSTACK_LINK = "https://paystack.shop/pay/6yjmo6ykwr"

TOKEN_PRICING = {
    "5 tokens": {"amount": 5, "price_cedis": 2, "price_usd": round(2/USD_TO_CEDIS_RATE, 2)},
    "15 tokens": {"amount": 15, "price_cedis": 5, "price_usd": round(5/USD_TO_CEDIS_RATE, 2)},
    "40 tokens": {"amount": 40, "price_cedis": 10, "price_usd": round(10/USD_TO_CEDIS_RATE, 2)}
}

REDEEM_OPTIONS = {
    "1 Token": {"points": 10, "reward": "+1 Token", "cedis": 0.4, "usd": round(0.4/USD_TO_CEDIS_RATE, 2), "tier": 1, "amount": 1},
    "3 Tokens": {"points": 60, "reward": "+3 Tokens", "cedis": 1.2, "usd": round(1.2/USD_TO_CEDIS_RATE, 2), "tier": 1, "amount": 3},
    "7 Tokens": {"points": 140, "reward": "+7 Tokens", "cedis": 2.8, "usd": round(2.8/USD_TO_CEDIS_RATE, 2), "tier": 1, "amount": 7},
    "GHS 2 Airtime": {"points": 160, "reward": "GHS 2 Airtime", "cedis": 2, "usd": round(2/USD_TO_CEDIS_RATE, 2), "tier": 2},
    "GHS 5 Airtime": {"points": 300, "reward": "GHS 5 Airtime", "cedis": 5, "usd": round(5/USD_TO_CEDIS_RATE, 2), "tier": 2},
    "500MB Data": {"points": 200, "reward": "500MB Internet Data", "cedis": 3, "usd": round(3/USD_TO_CEDIS_RATE, 2), "tier": 2},
    "1GB Data": {"points": 400, "reward": "1GB Internet Data", "cedis": 5, "usd": round(5/USD_TO_CEDIS_RATE, 2), "tier": 2},
    "2GB Data": {"points": 700, "reward": "2GB Internet Data", "cedis": 8, "usd": round(8/USD_TO_CEDIS_RATE, 2), "tier": 2},
    "15 Tokens": {"points": 300, "reward": "+15 Tokens", "cedis": 6.0, "usd": round(6.0/USD_TO_CEDIS_RATE, 2), "tier": 2, "amount": 15},
    "25 Tokens": {"points": 500, "reward": "+25 Tokens", "cedis": 10.0, "usd": round(10.0/USD_TO_CEDIS_RATE, 2), "tier": 2, "amount": 25},
    "GHS 10 Airtime": {"points": 1000, "reward": "GHS 10 Airtime", "cedis": 10, "usd": round(10/USD_TO_CEDIS_RATE, 2), "tier": 3},
    "GHS 20 Airtime": {"points": 1800, "reward": "GHS 20 Airtime", "cedis": 20, "usd": round(20/USD_TO_CEDIS_RATE, 2), "tier": 3},
    "5GB Data": {"points": 1200, "reward": "5GB Internet Data", "cedis": 15, "usd": round(15/USD_TO_CEDIS_RATE, 2), "tier": 3},
    "10GB Data": {"points": 2000, "reward": "10GB Internet Data", "cedis": 25, "usd": round(25/USD_TO_CEDIS_RATE, 2), "tier": 3},
    "GHS 10 MoMo": {"points": 1100, "reward": "GHS 10 MoMo", "cedis": 10, "usd": round(10/USD_TO_CEDIS_RATE, 2), "tier": 3},
    "GHS 20 MoMo": {"points": 2100, "reward": "GHS 20 MoMo", "cedis": 20, "usd": round(20/USD_TO_CEDIS_RATE, 2), "tier": 3},
    "GHS 50 MoMo": {"points": 5000, "reward": "GHS 50 MoMo", "cedis": 50, "usd": round(50/USD_TO_CEDIS_RATE, 2), "tier": 3},
    "Basic Phone": {"points": 8000, "reward": "Basic Smartphone", "cedis": 400, "usd": round(400/USD_TO_CEDIS_RATE, 2), "tier": 3},
    "50 Tokens": {"points": 1000, "reward": "+50 Tokens", "cedis": 20.0, "usd": round(20.0/USD_TO_CEDIS_RATE, 2), "tier": 3, "amount": 50},
    "Samsung Phone": {"points": 15000, "reward": "Samsung Galaxy A15", "cedis": 1200, "usd": round(1200/USD_TO_CEDIS_RATE, 2), "tier": 4},
    "iPhone": {"points": 35000, "reward": "iPhone 13", "cedis": 3500, "usd": round(3500/USD_TO_CEDIS_RATE, 2), "tier": 4},
    "Budget Laptop": {"points": 25000, "reward": "HP Laptop 14", "cedis": 2800, "usd": round(2800/USD_TO_CEDIS_RATE, 2), "tier": 4},
    "Gaming Laptop": {"points": 45000, "reward": "Gaming Laptop", "cedis": 5500, "usd": round(5500/USD_TO_CEDIS_RATE, 2), "tier": 4},
    "GHS 100 MoMo": {"points": 10000, "reward": "GHS 100 MoMo", "cedis": 100, "usd": round(100/USD_TO_CEDIS_RATE, 2), "tier": 4},
    "GHS 200 MoMo": {"points": 20000, "reward": "GHS 200 MoMo", "cedis": 200, "usd": round(200/USD_TO_CEDIS_RATE, 2), "tier": 4},
    "100 Tokens": {"points": 2000, "reward": "+100 Tokens", "cedis": 40.0, "usd": round(40.0/USD_TO_CEDIS_RATE, 2), "tier": 4, "amount": 100}
}

PAYMENT_INFO = """
💸 <b>Payment Instructions</b>

📲 <b>MTN MoMo Payment:</b>
• Make payment to MTN merchant ID: <b>474994</b>
• Name: <b>Sufex Technology</b>
• Direct Payment: <a href="https://paystack.shop/pay/6yjmo6ykwr">Pay with Paystack</a>

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

📬 Send payment screenshot to @Learn4CashAdmin for verification.
⚡ Tokens are added manually after payment confirmation!
"""

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

# --- Unified Quiz Data ---
ALL_QUIZZES = {
    "General": [
        {"q": "Who was Ghana's first president?", "a": "Kwame Nkrumah", "choices": ["Kwame Nkrumah", "Rawlings", "Mahama", "Busia"]},
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
        {"q": "What is the currency of Nigeria?", "a": "Naira", "choices": ["Cedi", "Shilling", "Rand", "Naira"]},
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
        {"q": "Who wrote the novel 'Things Fall Apart'?", "a": "Chinua Achebe", "choices": ["Wole Soyinka", "Chinua Achebe", "Ngugi wa Thiong'o", "Ama Ata Aidoo
