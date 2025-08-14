#```python
import os
import random
import time
import logging
import threading
from datetime import datetime, timezone
from dotenv import load_dotenv
from telebot import TeleBot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from googletrans import Translator
import json
import schedule
import traceback
import requests  # Added to handle potential ReadTimeout exceptions in polling

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
    get_sheet_manager,
    find_user_by_referral_code,
    update_transaction_status
)

# --- Setup ---
load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

API_KEY = os.getenv("TELEGRAM_API_KEY") or "YOUR_FALLBACK_API_KEY"
bot = TeleBot(API_KEY, parse_mode='HTML')
ADMIN_CHAT_IDS = [2145372547]
translator = Translator()

USD_TO_CEDIS_RATE = 11.8
PAYSTACK_LINK = "https://paystack.shop/pay/6yjmo6ykwr"

def fetch_exchange_rate():
    """Fetch the latest USD to GHS exchange rate from API."""
    try:
        import requests
        response = requests.get("https://api.exchangerate-api.com/v4/latest/USD")
        data = response.json()
        rate = data['rates']['GHS']
        logger.info(f"Updated exchange rate: 1 USD = {rate} GHS")
        return rate
    except Exception as e:
        logger.error(f"Error fetching exchange rate: {e}")
        return USD_TO_CEDIS_RATE  # Fallback to current rate

def update_exchange_rate():
    """Update the global exchange rate."""
    global USD_TO_CEDIS_RATE
    new_rate = fetch_exchange_rate()
    if new_rate != USD_TO_CEDIS_RATE:
        USD_TO_CEDIS_RATE = new_rate
        # Update pricing with new rate
        for package in TOKEN_PRICING.values():
            package['price_usd'] = round(package['price_cedis']/USD_TO_CEDIS_RATE, 2)
        logger.info("Exchange rate updated successfully")

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

# --- Quiz Data ---
GENERAL_QUIZZES = [
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
    {"q": "Who wrote the novel 'Things Fall Apart'?", "a": "Chinua Achebe", "choices": ["Wole Soyinka", "Chinua Achebe", "Ngugi wa Thiong'o", "Ama Ata Aidoo"]},
    {"q": "Which lake is shared by Kenya, Tanzania, and Uganda?", "a": "Lake Victoria", "choices": ["Lake Tanganyika", "Lake Victoria", "Lake Malawi", "Lake Chad"]},
    {"q": "What does 'Ubuntu' mean in African philosophy?", "a": "I am because we are", "choices": ["Unity in diversity", "I am because we are", "Strength in numbers", "Peace and harmony"]},
    {"q": "Which African country was the first to gain independence?", "a": "Libya", "choices": ["Ghana", "Nigeria", "Libya", "Morocco"]},
    {"q": "Who was the founder of the Kingdom of Zulu?", "a": "Shaka Zulu", "choices": ["Shaka Zulu", "Cetshwayo", "Dingane", "Mpande"]},
    {"q": "Which African country is landlocked and bordered by 7 countries?", "a": "Chad", "choices": ["Mali", "Niger", "Chad", "Burkina Faso"]},
    {"q": "What is the largest lake in Africa?", "a": "Lake Victoria", "choices": ["Lake Tanganyika", "Lake Victoria", "Lake Malawi", "Lake Chad"]},
    {"q": "Which African country has both Atlantic and Indian Ocean coastlines?", "a": "South Africa", "choices": ["Somalia", "South Africa", "Morocco", "Egypt"]},
    {"q": "What is the lowest point in Africa?", "a": "Lake Assal", "choices": ["Dead Sea", "Lake Assal", "Qattara Depression", "Danakil Depression"]},
    {"q": "Which African mountain range is located in Morocco?", "a": "Atlas Mountains", "choices": ["Atlas Mountains", "Drakensberg", "Ethiopian Highlands", "Ahaggar Mountains"]},
    {"q": "What is the currency of Kenya?", "a": "Shilling", "choices": ["Rand", "Shilling", "Birr", "Dinar"]},
    {"q": "Which African country uses the Franc CFA?", "a": "Senegal", "choices": ["Ghana", "Nigeria", "Senegal", "Ethiopia"]},
    {"q": "What is the currency of Egypt?", "a": "Pound", "choices": ["Dinar", "Dirham", "Pound", "Birr"]},
    {"q": "Which currency is used in Morocco?", "a": "Dirham", "choices": ["Dinar", "Dirham", "Franc", "Pound"]},
    {"q": "What is the currency of Ethiopia?", "a": "Birr", "choices": ["Birr", "Shilling", "Rand", "Naira"]},
    {"q": "Which African country is the largest producer of diamonds?", "a": "Botswana", "choices": ["South Africa", "Botswana", "Angola", "Congo"]},
    {"q": "What is Africa's largest stock exchange?", "a": "Johannesburg Stock Exchange", "choices": ["Nigerian Stock Exchange", "Johannesburg Stock Exchange", "Egyptian Exchange", "Nairobi Securities Exchange"]},
    {"q": "Which African country exports the most oil?", "a": "Nigeria", "choices": ["Angola", "Nigeria", "Algeria", "Libya"]},
    {"q": "What is the main export of Zambia?", "a": "Copper", "choices": ["Gold", "Copper", "Diamonds", "Coffee"]},
    {"q": "Which African country is the largest producer of coffee?", "a": "Ethiopia", "choices": ["Kenya", "Ethiopia", "Uganda", "Tanzania"]},
    {"q": "Who was the first black president of South Africa?", "a": "Nelson Mandela", "choices": ["Nelson Mandela", "Thabo Mbeki", "Jacob Zuma", "Desmond Tutu"]},
    {"q": "Which African organization promotes continental unity?", "a": "African Union", "choices": ["ECOWAS", "African Union", "SADC", "EAC"]},
    {"q": "Who was Libya's leader for 42 years?", "a": "Muammar Gaddafi", "choices": ["Hosni Mubarak", "Muammar Gaddafi", "Idi Amin", "Robert Mugabe"]},
    {"q": "Which African country had apartheid?", "a": "South Africa", "choices": ["Zimbabwe", "South Africa", "Namibia", "Angola"]},
    {"q": "Who founded the African National Congress (ANC)?", "a": "John Dube", "choices": ["Nelson Mandela", "Oliver Tambo", "John Dube", "Walter Sisulu"]},
    {"q": "What is the predominant religion in Ethiopia?", "a": "Christianity", "choices": ["Islam", "Christianity", "Judaism", "Traditional"]},
    {"q": "Which city is considered holy in Ethiopian Christianity?", "a": "Lalibela", "choices": ["Addis Ababa", "Lalibela", "Gondar", "Axum"]},
    {"q": "What is the main religion in Morocco?", "a": "Islam", "choices": ["Christianity", "Islam", "Judaism", "Traditional"]},
    {"q": "Which African country has the most Christians?", "a": "Nigeria", "choices": ["Ethiopia", "Nigeria", "Congo", "Kenya"]},
    {"q": "What is the holy month in Islam called?", "a": "Ramadan", "choices": ["Hajj", "Ramadan", "Eid", "Zakat"]},
    {"q": "Which ancient African civilization built the pyramids at Meroë?", "a": "Kingdom of Kush", "choices": ["Ancient Egypt", "Kingdom of Kush", "Axum", "Nubia"]},
    {"q": "Who was the famous warrior queen of the Zulu?", "a": "Queen Nandi", "choices": ["Queen Nzinga", "Queen Nandi", "Queen Amina", "Queen Kandake"]},
    {"q": "Which African country was colonized by Belgium?", "a": "Congo", "choices": ["Rwanda", "Congo", "Burundi", "All of these"]},
    {"q": "What year did African Union replace OAU?", "a": "2001", "choices": ["1999", "2000", "2001", "2002"]},
    {"q": "Which African leader wrote 'How Europe Underdeveloped Africa'?", "a": "Walter Rodney", "choices": ["Kwame Nkrumah", "Walter Rodney", "Julius Nyerere", "Frantz Fanon"]}
]

ZONE_QUIZZES = {
    "West Africa": [
        {"q": "Which country is the largest exporter of cocoa beans in West Africa?", "a": "Ivory Coast", "choices": ["Ivory Coast", "Ghana", "Nigeria", "Togo"]},
        {"q": "Who founded the Ashanti Empire in present-day Ghana?", "a": "Osei Tutu", "choices": ["Osei Tutu", "Yaa Asantewaa", "Kwame Nkrumah", "Opoku Ware"]},
        {"q": "Which ruler led the Mali Empire to its peak in the 14th century?", "a": "Mansa Musa", "choices": ["Sundiata Keita", "Mansa Musa", "Askia Muhammad", "Sonni Ali"]},
        {"q": "Which West African country was the first to gain independence in 1957?", "a": "Ghana", "choices": ["Nigeria", "Ghana", "Senegal", "Liberia"]},
        {"q": "Who led the Biafra secession attempt in Nigeria during the 1960s?", "a": "Odumegwu Ojukwu", "choices": ["Odumegwu Ojukwu", "Nnamdi Azikiwe", "Ahmadu Bello", "Tafawa Balewa"]},
        {"q": "Which ancient Yoruba city-state is known for its bronze artworks?", "a": "Ife", "choices": ["Oyo", "Ife", "Benin", "Lagos"]},
        {"q": "What was the primary commodity traded across the Trans-Saharan routes in West Africa?", "a": "Gold", "choices": ["Salt", "Gold", "Ivory", "Spices"]},
        {"q": "Who is the president of Nigeria as of 2025?", "a": "Bola Tinubu", "choices": ["Bola Tinubu", "Muhammadu Buhari", "Goodluck Jonathan", "Yemi Osinbajo"]},
        {"q": "Where is the headquarters of the Economic Community of West African States (ECOWAS)?", "a": "Abuja", "choices": ["Lagos", "Abuja", "Accra", "Dakar"]},
        {"q": "Who was the first president of Senegal from 1960 to 1980?", "a": "Léopold Sédar Senghor", "choices": ["Léopold Sédar Senghor", "Abdou Diouf", "Macky Sall", "Abdoulaye Wade"]},
        {"q": "What is the capital city of Burkina Faso?", "a": "Ouagadougou", "choices": ["Bamako", "Ouagadougou", "Niamey", "Yamoussoukro"]},
        {"q": "Which West African country elected Africa's first female president in 2006?", "a": "Liberia", "choices": ["Ghana", "Liberia", "Nigeria", "Sierra Leone"]},
        {"q": "In which year did Ghana adopt its Fourth Republic constitution?", "a": "1992", "choices": ["1981", "1992", "2000", "1960"]},
        {"q": "Which Yoruba deity is associated with thunder and lightning?", "a": "Shango", "choices": ["Ogun", "Shango", "Obatala", "Yemoja"]},
        {"q": "Which West African country is known for originating Kente cloth?", "a": "Ghana", "choices": ["Nigeria", "Ghana", "Mali", "Senegal"]},
        {"q": "Which dish is central to a cultural rivalry between Nigeria and Ghana?", "a": "Jollof Rice", "choices": ["Fufu", "Jollof Rice", "Egusi Soup", "Pounded Yam"]},
        {"q": "What music genre was pioneered by Nigerian musician Fela Kuti?", "a": "Afrobeat", "choices": ["Highlife", "Afrobeat", "Juju", "Apala"]},
        {"q": "Which West African ethnic group is known for its cosmological masks?", "a": "Dogon", "choices": ["Dogon", "Yoruba", "Ashanti", "Fulani"]},
        {"q": "Which festival in Benin celebrates the Vodun religion?", "a": "Vodun Festival", "choices": ["Fetu Afahye", "Vodun Festival", "Durbar", "Homowo"]},
        {"q": "Which Nigerian city is the hub of the country's oil industry?", "a": "Port Harcourt", "choices": ["Lagos", "Port Harcourt", "Abuja", "Kano"]},
        {"q": "What is the official currency of Ghana?", "a": "Cedi", "choices": ["Naira", "Cedi", "CFA Franc", "Dalasi"]},
        {"q": "Which Nigerian billionaire is known for his cement manufacturing empire?", "a": "Aliko Dangote", "choices": ["Aliko Dangote", "Femi Otedola", "Mike Adenuga", "Tony Elumelu"]},
        {"q": "Which West African port is the largest by cargo volume?", "a": "Lagos", "choices": ["Lagos", "Tema", "Dakar", "Abidjan"]},
        {"q": "Which Nigerian fintech company became a unicorn in 2021?", "a": "Flutterwave", "choices": ["Paystack", "Flutterwave", "Interswitch", "Opay"]},
        {"q": "Which West African country is the largest producer of gold?", "a": "Ghana", "choices": ["Mali", "Ghana", "Nigeria", "Burkina Faso"]}
    ],
    "East Africa": [
        {"q": "Which country is famous for its coffee exports?", "a": "Ethiopia", "choices": ["Ethiopia", "Kenya", "Uganda", "Tanzania"]},
        {"q": "What is the main currency used in Kenya?", "a": "Shilling", "choices": ["Shilling", "Franc", "Birr", "Dollar"]},
        {"q": "Which country is a major exporter of tea?", "a": "Kenya", "choices": ["Kenya", "Uganda", "Tanzania", "Rwanda"]},
        {"q": "Which country is known for its flower industry?", "a": "Kenya", "choices": ["Kenya", "Ethiopia", "Uganda", "Tanzania"]},
        {"q": "What is the currency of Tanzania?", "a": "Shilling", "choices": ["Shilling", "Franc", "Birr", "Dollar"]},
        {"q": "Who was the first president of Tanzania?", "a": "Julius Nyerere", "choices": ["Julius Nyerere", "John Magufuli", "Uhuru Kenyatta", "Yoweri Museveni"]},
        {"q": "Which country gained independence from Britain in 1962?", "a": "Uganda", "choices": ["Uganda", "Kenya", "Tanzania", "Rwanda"]},
        {"q": "Who is the current president of Kenya (2025)?", "a": "William Ruto", "choices": ["William Ruto", "Uhuru Kenyatta", "Jomo Kenyatta", "Daniel arap Moi"]},
        {"q": "Which country has the capital city of Kigali?", "a": "Rwanda", "choices": ["Rwanda", "Burundi", "Uganda", "Kenya"]},
        {"q": "Which country was formerly known as Tanganyika?", "a": "Tanzania", "choices": ["Tanzania", "Kenya", "Uganda", "Rwanda"]},
        {"q": "The ancient city of Axum is located in which country?", "a": "Ethiopia", "choices": ["Ethiopia", "Kenya", "Uganda", "Tanzania"]},
        {"q": "Which country was home to the Buganda Kingdom?", "a": "Uganda", "choices": ["Uganda", "Kenya", "Tanzania", "Rwanda"]},
        {"q": "Who was the famous queen of Sheba?", "a": "Ethiopia", "choices": ["Ethiopia", "Kenya", "Uganda", "Tanzania"]},
        {"q": "Which country is known for the ancient city of Lalibela?", "a": "Ethiopia", "choices": ["Ethiopia", "Kenya", "Uganda", "Tanzania"]},
        {"q": "Which country was the site of the 1994 genocide?", "a": "Rwanda", "choices": ["Rwanda", "Burundi", "Uganda", "Kenya"]},
        {"q": "What is the capital of Burundi?", "a": "Gitega", "choices": ["Gitega", "Bujumbura", "Kigali", "Nairobi"]},
        {"q": "Which country is famous for the Serengeti National Park?", "a": "Tanzania", "choices": ["Tanzania", "Kenya", "Uganda", "Rwanda"]},
        {"q": "What is the official language of Uganda?", "a": "English", "choices": ["English", "Swahili", "French", "Arabic"]},
        {"q": "Which country is famous for the city of Djibouti?", "a": "Djibouti", "choices": ["Djibouti", "Eritrea", "Somalia", "Ethiopia"]},
        {"q": "What is the capital of Eritrea?", "a": "Asmara", "choices": ["Asmara", "Addis Ababa", "Djibouti", "Nairobi"]},
        {"q": "Which country is famous for the city of Mombasa?", "a": "Kenya", "choices": ["Kenya", "Tanzania", "Uganda", "Ethiopia"]},
        {"q": "Which country is famous for the city of Juba?", "a": "South Sudan", "choices": ["South Sudan", "Sudan", "Uganda", "Kenya"]},
        {"q": "Which country is famous for the city of Arusha?", "a": "Tanzania", "choices": ["Tanzania", "Kenya", "Uganda", "Ethiopia"]},
        {"q": "Which country is famous for the city of Bujumbura?", "a": "Burundi", "choices": ["Burundi", "Rwanda", "Uganda", "Kenya"]},
        {"q": "Which country is famous for the city of Jinja?", "a": "Uganda", "choices": ["Uganda", "Kenya", "Tanzania", "Rwanda"]}
    ],
    "North Africa": [
        {"q": "Which country is the largest exporter of phosphates in North Africa?", "a": "Morocco", "choices": ["Morocco", "Egypt", "Algeria", "Tunisia"]},
        {"q": "What is the main currency used in Egypt?", "a": "Pound", "choices": ["Pound", "Dinar", "Dirham", "Franc"]},
        {"q": "Which country is famous for its oil industry?", "a": "Libya", "choices": ["Libya", "Tunisia", "Algeria", "Morocco"]},
        {"q": "Which country is a major exporter of dates?", "a": "Algeria", "choices": ["Algeria", "Morocco", "Egypt", "Tunisia"]},
        {"q": "What is the currency of Tunisia?", "a": "Dinar", "choices": ["Dinar", "Dirham", "Pound", "Franc"]},
        {"q": "Who was the president of Egypt during the Arab Spring in 2011?", "a": "Hosni Mubarak", "choices": ["Hosni Mubarak", "Anwar Sadat", "Gamal Abdel Nasser", "Mohamed Morsi"]},
        {"q": "Which country was ruled by Muammar Gaddafi?", "a": "Libya", "choices": ["Libya", "Tunisia", "Algeria", "Morocco"]},
        {"q": "Who is the current king of Morocco (2025)?", "a": "Mohammed VI", "choices": ["Mohammed VI", "Hassan II", "Mohammed V", "Abdallah"]},
        {"q": "Which country has the capital city of Algiers?", "a": "Algeria", "choices": ["Algeria", "Morocco", "Tunisia", "Libya"]},
        {"q": "Which country was formerly known as Numidia?", "a": "Algeria", "choices": ["Algeria", "Morocco", "Tunisia", "Libya"]},
        {"q": "The ancient city of Carthage was located in which present-day country?", "a": "Tunisia", "choices": ["Tunisia", "Libya", "Morocco", "Egypt"]},
        {"q": "Which country was home to the Pharaohs?", "a": "Egypt", "choices": ["Egypt", "Libya", "Morocco", "Tunisia"]},
        {"q": "Who was the famous queen of Egypt?", "a": "Cleopatra", "choices": ["Cleopatra", "Nefertiti", "Hatshepsut", "Ankhesenamun"]},
        {"q": "Which country is known for the ancient city of Marrakech?", "a": "Morocco", "choices": ["Morocco", "Algeria", "Tunisia", "Libya"]},
        {"q": "Which country was the site of the Battle of El Alamein?", "a": "Egypt", "choices": ["Egypt", "Libya", "Morocco", "Tunisia"]},
        {"q": "What is the capital of Sudan?", "a": "Khartoum", "choices": ["Khartoum", "Juba", "Cairo", "Tripoli"]},
        {"q": "Which country is famous for the city of Casablanca?", "a": "Morocco", "choices": ["Morocco", "Algeria", "Tunisia", "Libya"]},
        {"q": "What is the official language of Libya?", "a": "Arabic", "choices": ["Arabic", "French", "Berber", "English"]},
        {"q": "Which country is famous for the city of Benghazi?", "a": "Libya", "choices": ["Libya", "Egypt", "Morocco", "Tunisia"]},
        {"q": "Which country is famous for the city of Tunis?", "a": "Tunisia", "choices": ["Tunisia", "Algeria", "Libya", "Egypt"]},
        {"q": "Which country is famous for the city of Oran?", "a": "Algeria", "choices": ["Algeria", "Morocco", "Tunisia", "Libya"]},
        {"q": "Which country is famous for the city of Sfax?", "a": "Tunisia", "choices": ["Tunisia", "Algeria", "Libya", "Egypt"]},
        {"q": "Which country is famous for the city of Giza?", "a": "Egypt", "choices": ["Egypt", "Libya", "Morocco", "Tunisia"]},
        {"q": "Which country is famous for the city of Fez?", "a": "Morocco", "choices": ["Morocco", "Algeria", "Tunisia", "Libya"]},
        {"q": "Which country is famous for the city of Aswan?", "a": "Egypt", "choices": ["Egypt", "Libya", "Morocco", "Tunisia"]}
    ],
    "Central Africa": [
        {"q": "Which country is the largest producer of crude oil in Central Africa?", "a": "Equatorial Guinea", "choices": ["Equatorial Guinea", "Gabon", "Cameroon", "Chad"]},
        {"q": "What is the main currency used in Cameroon?", "a": "Franc CFA", "choices": ["Franc CFA", "Naira", "Dollar", "Euro"]},
        {"q": "Which country is a major exporter of timber?", "a": "Gabon", "choices": ["Gabon", "Cameroon", "Congo", "Chad"]},
        {"q": "Which country is famous for its diamond mines?", "a": "DR Congo", "choices": ["DR Congo", "Congo", "Gabon", "Cameroon"]},
        {"q": "What is the currency of Chad?", "a": "Franc CFA", "choices": ["Franc CFA", "Naira", "Dollar", "Euro"]},
        {"q": "Who is the long-serving president of Cameroon?", "a": "Paul Biya", "choices": ["Paul Biya", "Ali Bongo", "Denis Sassou Nguesso", "Idriss Déby"]},
        {"q": "Which country has Brazzaville as its capital?", "a": "Congo", "choices": ["Congo", "DR Congo", "Gabon", "Chad"]},
        {"q": "Who is the president of Gabon (2025)?", "a": "Brice Oligui Nguema", "choices": ["Brice Oligui Nguema", "Ali Bongo", "Paul Biya", "Denis Sassou Nguesso"]},
        {"q": "Which country is a member of CEMAC?", "a": "Cameroon", "choices": ["Cameroon", "Gabon", "Congo", "Chad"]},
        {"q": "Which country was formerly known as Zaire?", "a": "DR Congo", "choices": ["DR Congo", "Congo", "Gabon", "Cameroon"]},
        {"q": "The Kingdom of Kongo was located in which present-day country?", "a": "DR Congo", "choices": ["DR Congo", "Congo", "Gabon", "Cameroon"]},
        {"q": "Which country was home to the Kanem-Bornu Empire?", "a": "Chad", "choices": ["Chad", "Cameroon", "Gabon", "Congo"]},
        {"q": "Who was the famous explorer of the Congo River?", "a": "Henry Morton Stanley", "choices": ["Henry Morton Stanley", "David Livingstone", "Mungo Park", "John Speke"]},
        {"q": "Which country was colonized by Belgium?", "a": "DR Congo", "choices": ["DR Congo", "Congo", "Gabon", "Cameroon"]},
        {"q": "Which country was home to the Bantu migrations?", "a": "Cameroon", "choices": ["Cameroon", "Gabon", "Congo", "Chad"]},
        {"q": "What is the capital of Chad?", "a": "N'Djamena", "choices": ["N'Djamena", "Yaoundé", "Brazzaville", "Kinshasa"]},
        {"q": "Which country is famous for the city of Libreville?", "a": "Gabon", "choices": ["Gabon", "Cameroon", "Congo", "Chad"]},
        {"q": "Which country is famous for the city of Bangui?", "a": "Central African Republic", "choices": ["Central African Republic", "Cameroon", "Gabon", "Congo"]},
        {"q": "Which country is famous for the city of Malabo?", "a": "Equatorial Guinea", "choices": ["Equatorial Guinea", "Gabon", "Cameroon", "Chad"]},
        {"q": "Which country is famous for the city of Kinshasa?", "a": "DR Congo", "choices": ["DR Congo", "Congo", "Gabon", "Chad"]},
        {"q": "Which country is famous for the city of Douala?", "a": "Cameroon", "choices": ["Cameroon", "Gabon", "Congo", "Chad"]},
        {"q": "Which country is famous for the city of Brazzaville?", "a": "Congo", "choices": ["Congo", "DR Congo", "Gabon", "Cameroon"]},
        {"q": "Which country is famous for the city of Pointe-Noire?", "a": "Congo", "choices": ["Congo", "DR Congo", "Gabon", "Cameroon"]},
        {"q": "Which country is famous for the city of Bertoua?", "a": "Cameroon", "choices": ["Cameroon", "Gabon", "Congo", "Chad"]},
        {"q": "Which country is famous for the city of Bangui?", "a": "Central African Republic", "choices": ["Central African Republic", "Cameroon", "Gabon", "Congo"]}
    ],
    "Southern Africa": [
        {"q": "Which country is the world's largest producer of platinum?", "a": "South Africa", "choices": ["South Africa", "Botswana", "Namibia", "Zimbabwe"]},
        {"q": "What is the main currency used in Zimbabwe?", "a": "Dollar", "choices": ["Dollar", "Rand", "Kwacha", "Pula"]},
        {"q": "Which country is famous for its diamond mines?", "a": "Botswana", "choices": ["Botswana", "South Africa", "Namibia", "Zimbabwe"]},
        {"q": "Which country is a major exporter of copper?", "a": "Zambia", "choices": ["Zambia", "Zimbabwe", "Botswana", "South Africa"]},
        {"q": "What is the currency of Namibia?", "a": "Namibian Dollar", "choices": ["Namibian Dollar", "Rand", "Kwacha", "Pula"]},
        {"q": "Who was the first black president of South Africa?", "a": "Nelson Mandela", "choices": ["Nelson Mandela", "Thabo Mbeki", "Jacob Zuma", "Cyril Ramaphosa"]},
        {"q": "Which country was formerly known as Rhodesia?", "a": "Zimbabwe", "choices": ["Zimbabwe", "Zambia", "Botswana", "Namibia"]},
        {"q": "Who is the current president of Zambia (2025)?", "a": "Hakainde Hichilema", "choices": ["Hakainde Hichilema", "Edgar Lungu", "Levy Mwanawasa", "Kenneth Kaunda"]},
        {"q": "Which country has the capital city of Gaborone?", "a": "Botswana", "choices": ["Botswana", "Namibia", "Zimbabwe", "South Africa"]},
        {"q": "Which country was formerly known as South West Africa?", "a": "Namibia", "choices": ["Namibia", "Botswana", "Zimbabwe", "Angola"]},
        {"q": "The Great Zimbabwe ruins are located in which country?", "a": "Zimbabwe", "choices": ["Zimbabwe", "South Africa", "Botswana", "Namibia"]},
        {"q": "Which country was home to the Zulu Kingdom?", "a": "South Africa", "choices": ["South Africa", "Botswana", "Namibia", "Zimbabwe"]},
        {"q": "Who was the famous king of the Zulu?", "a": "Shaka Zulu", "choices": ["Shaka Zulu", "Cetshwayo", "Dingane", "Mpande"]},
        {"q": "Which country was colonized by Portugal?", "a": "Mozambique", "choices": ["Mozambique", "Angola", "Namibia", "Botswana"]},
        {"q": "Which country was home to the Lozi Kingdom?", "a": "Zambia", "choices": ["Zambia", "Zimbabwe", "Botswana", "South Africa"]},
        {"q": "What is the capital of Lesotho?", "a": "Maseru", "choices": ["Maseru", "Lusaka", "Harare", "Pretoria"]},
        {"q": "Which country is famous for the city of Windhoek?", "a": "Namibia", "choices": ["Namibia", "Botswana", "Zimbabwe", "South Africa"]},
        {"q": "Which country is famous for the city of Lusaka?", "a": "Zambia", "choices": ["Zambia", "Zimbabwe", "Botswana", "South Africa"]},
        {"q": "Which country is famous for the city of Antananarivo?", "a": "Madagascar", "choices": ["Madagascar", "Mozambique", "South Africa", "Angola"]},
        {"q": "Which country is famous for the city of Blantyre?", "a": "Malawi", "choices": ["Malawi", "Zambia", "Zimbabwe", "Botswana"]},
        {"q": "Which country is famous for the city of Bulawayo?", "a": "Zimbabwe", "choices": ["Zimbabwe", "Zambia", "Botswana", "South Africa"]},
        {"q": "Which country is famous for the city of Port Louis?", "a": "Mauritius", "choices": ["Mauritius", "Madagascar", "Mozambique", "Angola"]},
        {"q": "Which country is famous for the city of Francistown?", "a": "Botswana", "choices": ["Botswana", "Namibia", "Zimbabwe", "South Africa"]},
        {"q": "Which country is famous for the city of Toliara?", "a": "Madagascar", "choices": ["Madagascar", "Mozambique", "South Africa", "Angola"]},
        {"q": "Which country is famous for the city of Livingstone?", "a": "Zambia", "choices": ["Zambia", "Zimbabwe", "Botswana", "South Africa"]}
    ]
}

# --- Global State ---
current_question = {}
custom_token_requests = {}
player_progress = {}
skipped_questions = {}
paused_games = {}
pending_token_purchases = {}
user_question_pools = {}
all_users = set()
user_feedback_mode = {}
user_momo_pending = {}
user_selected_zone = {}
user_selected_language = {}
user_quiz_index = {}
user_quiz_mode = {}
zone_question_pools = {}

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

# --- Menus ---
def create_main_menu(chat_id):
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    buttons = [
        KeyboardButton("🎮 General Quiz"),
        KeyboardButton("🌍 Zone Quiz"),
        KeyboardButton("💰 Buy Tokens"),
        KeyboardButton("🎁 Redeem Rewards"),
        KeyboardButton("🎁 Daily Reward"),
        KeyboardButton("📊 My Stats"),
        KeyboardButton("📈 Progress"),
        KeyboardButton("👥 Referrals"),
        KeyboardButton("🏆 Leaderboard"),
        KeyboardButton("ℹ️ Help"),
        KeyboardButton("💬 Send Feedback")
    ]
    if is_admin(chat_id):
        buttons.append(KeyboardButton("🔧 Admin Menu"))
    markup.add(*buttons)
    return markup

def create_admin_menu():
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

def send_zone_menu(chat_id):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    for zone in ZONE_QUIZZES.keys():
        markup.add(KeyboardButton(zone))
    bot.send_message(chat_id, "🌍 Choose an African zone to learn about:", reply_markup=markup)

def send_language_menu(chat_id):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    for lang in ["English", "French", "Swahili", "Arabic"]:
        markup.add(KeyboardButton(lang))
    bot.send_message(chat_id, "🌐 Choose your language:", reply_markup=markup)

# --- Utility Functions ---
def is_admin(user_id):
    return user_id in ADMIN_CHAT_IDS

def notify_admin_token_purchase(user_id, package_info, payment_method):
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
⏰ <b>Time:</b> {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC

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
    try:
        timestamp = datetime.now(timezone.utc).isoformat()
        readable_time = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
        log_entry = f"{readable_time} | {transaction_type} | User: {user_id} | Amount: {amount} | Details: {details}"
        if payment_method:
            log_entry += f" | Payment: {payment_method}"
        logger.info(f"Token Transaction: {log_entry}")
        if transaction_type in ["BUY", "REDEEM", "STREAK_BONUS", "DAILY_REWARD"]:
            log_token_purchase(user_id, f"{transaction_type}_{details}_{readable_time}", amount, payment_method)
    except Exception as e:
        logger.error(f"Error logging token transaction: {e}")

def init_player_progress(user_id):
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

def update_player_progress(user_id, is_correct):
    init_player_progress(user_id)
    progress = player_progress[user_id]
    progress['total_questions'] += 1
    if is_correct:
        progress['current_streak'] += 1
        progress['total_correct'] += 1
        progress['questions_until_bonus'] -= 1
        if progress['questions_until_bonus'] == 0:
            progress['questions_until_bonus'] = 10
            return True
    else:
        progress['current_streak'] = 0
        progress['questions_until_bonus'] = 10
    progress['best_streak'] = max(progress['best_streak'], progress['current_streak'])
    return False

def get_random_general_quiz(user_id):
    if user_id not in user_question_pools:
        user_question_pools[user_id] = []
    used_questions = user_question_pools[user_id]
    available_questions = [q for q in GENERAL_QUIZZES if q['q'] not in used_questions]
    if not available_questions:
        user_question_pools[user_id] = []
        available_questions = GENERAL_QUIZZES
    selected_quiz = random.choice(available_questions)
    user_question_pools[user_id].append(selected_quiz['q'])
    return selected_quiz

def get_random_zone_quiz(user_id, zone):
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

def translate_text(text, lang_code):
    try:
        return translator.translate(text, dest=lang_code).text
    except Exception as e:
        logger.error(f"Translation error: {e}")
        return text

def send_feedback_to_admin(user_id, feedback_text):
    try:
        user_data = get_user_data(user_id)
        if not user_data:
            return
        feedback_message = f"""
💬 <b>USER FEEDBACK RECEIVED</b>

👤 <b>From:</b> {user_data['Name']} (ID: {user_id})
📱 <b>Username:</b> @{user_data.get('Username', 'No username')}
⏰ <b>Time:</b> {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC

📝 <b>Message:</b>
{feedback_text}

📊 <b>User Stats:</b>
• Tokens: {user_data['Tokens']}
• Points: {user_data['Points']}
• Referrals: {int(user_data.get('ReferralEarnings', 0))}
        """
        for admin_id in ADMIN_CHAT_IDS:
            try:
                bot.send_message(admin_id, feedback_message)
            except Exception as e:
                logger.error(f"Failed to send feedback to admin {admin_id}: {e}")
    except Exception as e:
        logger.error(f"Error sending feedback to admin: {e}")

# --- Registration & MoMo ---
@bot.message_handler(commands=['start'])
def start_handler(message):
    chat_id = message.chat.id
    args = message.text.split()
    referrer_id = None
    if len(args) > 1 and args[1].startswith("REF"):
        referrer_code = args[1]
        referrer_id = find_user_by_referral_code(referrer_code)
    
    user = get_user_data(chat_id)
    if not user:
        register_user(chat_id, message.from_user.first_name, message.from_user.username, referrer_id)
        user = get_user_data(chat_id)
        update_user_tokens_points(chat_id, user['Tokens'] + 3, user['Points'])
        if referrer_id:
            reward_referrer(int(referrer_id), 2)
            increment_referral_count(int(referrer_id), chat_id)
    if not user.get("MoMoNumber"):
        bot.send_message(chat_id, "📱 Please enter your MoMo number to continue:")
        user_momo_pending[chat_id] = "awaiting_momo"
        return
    motivation = random.choice(MOTIVATIONAL_MESSAGES)
    bot.send_message(
        chat_id,
        WELCOME_MESSAGE.format(
            name=user.get('Name', message.from_user.first_name),
            about_us=ABOUT_US,
            motivation=motivation
        ),
        reply_markup=create_main_menu(chat_id)
    )

@bot.message_handler(func=lambda message: message.chat.id in user_momo_pending)
def momo_number_handler(message):
    chat_id = message.chat.id
    if user_momo_pending[chat_id] == "awaiting_momo":
        momo_number = message.text.strip()
        import re
        if not re.match(r'^\+?\d{10,12}$', momo_number):
            bot.send_message(chat_id, "❌ Invalid MoMo number. Please enter a valid 10-12 digit phone number.")
            return
        update_user_momo(chat_id, momo_number)
        bot.send_message(chat_id, f"✅ MoMo number {momo_number} recorded!")
        del user_momo_pending[chat_id]
        motivation = random.choice(MOTIVATIONAL_MESSAGES)
        bot.send_message(
            chat_id,
            WELCOME_MESSAGE.format(
                name=message.from_user.first_name,
                about_us=ABOUT_US,
                motivation=motivation
            ),
            reply_markup=create_main_menu(chat_id)
        )

# --- Quiz Mode Selection ---
@bot.message_handler(func=lambda message: message.text == "🎮 General Quiz")
def general_quiz_handler(message):
    chat_id = message.chat.id
    user_quiz_mode[chat_id] = "general"
    start_new_quiz(chat_id, "general")

@bot.message_handler(func=lambda message: message.text == "🌍 Zone Quiz")
def zone_quiz_handler(message):
    chat_id = message.chat.id
    user_quiz_mode[chat_id] = "zone"
    send_zone_menu(chat_id)

@bot.message_handler(func=lambda message: message.text in ZONE_QUIZZES.keys())
def zone_selection_handler(message):
    chat_id = message.chat.id
    user_selected_zone[chat_id] = message.text
    send_language_menu(chat_id)

@bot.message_handler(func=lambda message: message.text in ["English", "French", "Swahili", "Arabic"])
def language_selection_handler(message):
    chat_id = message.chat.id
    user_selected_language[chat_id] = message.text
    start_new_quiz(chat_id, "zone")

# --- Unified Quiz Logic ---
def start_new_quiz(chat_id, mode):
    user = get_user_data(chat_id)
    if not user:
        bot.send_message(chat_id, "Please /start first.")
        return
    if user['Tokens'] <= 0:
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
    quiz = None
    if mode == "general":
        quiz = get_random_general_quiz(chat_id)
    elif mode == "zone":
        zone = user_selected_zone.get(chat_id, "West Africa")
        quiz = get_random_zone_quiz(chat_id, zone)
    if not quiz:
        bot.send_message(chat_id, "❌ Error loading quiz. Please try again.")
        return
    lang = user_selected_language.get(chat_id, "English")
    lang_code = {"English": "en", "French": "fr", "Swahili": "sw", "Arabic": "ar"}[lang]
    question = translate_text(quiz['q'], lang_code)
    choices = [translate_text(c, lang_code) for c in quiz['choices']]
    correct = translate_text(quiz['a'], lang_code)
    current_question[chat_id] = {
        'correct': correct,
        'question': question,
        'choices': choices,
        'skipped': False,
        'mode': mode,
        'original_answer': quiz['a']
    }
    answer_markup = InlineKeyboardMarkup()
    for choice in choices:
        answer_markup.add(InlineKeyboardButton(choice, callback_data=f"answer:{choice}"))
    answer_markup.add(InlineKeyboardButton("⏭️ Skip", callback_data="skip_question"), InlineKeyboardButton("⏸️ Pause", callback_data="pause_game"))
    bot.send_message(chat_id, f"🧠 <b>{'General' if mode == 'general' else user_selected_zone[chat_id]} Quiz:</b>\n{question}", reply_markup=answer_markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("answer:"))
def answer_handler(call):
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
        tokens -= 1
        if bonus_earned:
            tokens += 3
            log_token_transaction(chat_id, "STREAK_BONUS", 3, "10_correct_answers")
        update_user_tokens_points(chat_id, tokens, points)
        bot.answer_callback_query(call.id, "✅ Correct! +10 points")
        message = f"🎉 Correct answer! You earned <b>10 points</b>!"
        if bonus_earned:
            message += f"\n\n🔥 <b>STREAK BONUS!</b>\n✅ +3 tokens for 10 correct answers in a row!\n💰 Total tokens: {tokens}"
        bot.send_message(chat_id, message)
    else:
        tokens -= 1
        update_user_tokens_points(chat_id, tokens, points)
        bot.answer_callback_query(call.id, "❌ Wrong answer!")
        bot.send_message(chat_id, f"❌ Wrong! The correct answer was: <b>{correct}</b>")
    bot.send_message(chat_id, f"💰 Balance: {tokens} tokens | {points} points\n🔥 Current Streak: {player_progress[chat_id]['current_streak']}")
    del current_question[chat_id]
    if tokens > 0:
        time.sleep(2)
        start_new_quiz(chat_id, user_quiz_mode.get(chat_id, "general"))
    else:
        bot.send_message(chat_id, "🔚 You've run out of tokens. Use '💰 Buy Tokens' to continue playing!", reply_markup=create_main_menu(chat_id))

# --- Token Purchase Handler ---
@bot.message_handler(func=lambda message: message.text == "💰 Buy Tokens")
def buy_tokens_handler(message):
    chat_id = message.chat.id
    markup = InlineKeyboardMarkup()
    for label, data in TOKEN_PRICING.items():
        price_text = f"{label} (₵{data['price_cedis']} / ${data['price_usd']})"
        markup.add(InlineKeyboardButton(price_text, callback_data=f"buy:{label}"))
    markup.add(InlineKeyboardButton("Custom Amount", callback_data="buy:custom"))
    bot.send_message(chat_id, f"💰 Choose a token package:\n\n{PAYMENT_INFO}", reply_markup=markup)

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
    bot.send_message(chat_id, f"To buy {amount} tokens for GHS {price}, send payment via MTN MoMo or USDT. Your Transaction ID is `{transaction_id}`. An admin will approve it shortly.", parse_mode="Markdown")
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
    for reward, info in REDEEM_OPTIONS.items():
        if points >= info['points']:
            markup.add(InlineKeyboardButton(f"{reward} ({info['points']} pts)", callback_data=f"redeem:{reward}"))
    bot.send_message(chat_id, f"🎁 You have {points} points. Choose a reward to redeem:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("redeem:"))
def redeem_callback_handler(call):
    chat_id = call.message.chat.id
    label = call.data.split("redeem:")[1]
    reward = REDEEM_OPTIONS.get(label)
    user = get_user_data(chat_id)
    if not reward or not user:
        bot.answer_callback_query(call.id, "Invalid reward or user.")
        return
    if user['Points'] < reward['points']:
        bot.answer_callback_query(call.id, "Not enough points.")
        return
    tokens_to_add = reward.get('amount', 0)
    update_user_tokens_points(chat_id, user['Tokens'] + tokens_to_add, user['Points'] - reward['points'])
    log_point_redemption(chat_id, label)
    bot.send_message(chat_id, f"🎉 You redeemed: {reward['reward']}!\nOur team will contact you for delivery if applicable.")
    bot.answer_callback_query(call.id)

# --- Skip and Pause Handlers ---
@bot.callback_query_handler(func=lambda call: call.data == "skip_question")
def skip_question_handler(call):
    chat_id = call.message.chat.id
    if chat_id in current_question and not current_question[chat_id]['skipped']:
        current_question[chat_id]['skipped'] = True
        bot.send_message(chat_id, "⏭️ Question skipped! No tokens deducted.")
        mode = current_question[chat_id]['mode']
        del current_question[chat_id]
        start_new_quiz(chat_id, mode)
    else:
        bot.send_message(chat_id, "❌ You can only skip once per question.")

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
        log_token_transaction(chat_id, "DAILY_REWARD", 1, "Daily_Claim")
    else:
        bot.send_message(chat_id, "⏳ You've already claimed your daily reward today. Come back tomorrow!")
    bot.send_message(chat_id, "Back to main menu:", reply_markup=create_main_menu(chat_id))

# --- Stats Handler ---
@bot.message_handler(func=lambda message: message.text == "📊 My Stats")
def stats_handler(message):
    chat_id = message.chat.id
    user = get_user_data(chat_id)
    if not user:
        bot.send_message(chat_id, "Please /start first.")
        return
    init_player_progress(chat_id)
    progress = player_progress[chat_id]
    stats_message = f"""
📊 <b>Your Stats</b>

👤 <b>Name:</b> {user['Name']}
📱 <b>Username:</b> @{user.get('Username', 'None')}
💰 <b>Tokens:</b> {user['Tokens']}
🎯 <b>Points:</b> {user['Points']}
👥 <b>Referrals:</b> {int(user.get('ReferralEarnings', 0))}
🔥 <b>Current Streak:</b> {progress['current_streak']}
🏆 <b>Best Streak:</b> {progress['best_streak']}
✅ <b>Total Correct:</b> {progress['total_correct']}
❓ <b>Total Questions:</b> {progress['total_questions']}
⏭️ <b>Skips Used:</b> {progress['skips_used']}
⏸️ <b>Games Paused:</b> {progress['games_paused']}
    """
    bot.send_message(chat_id, stats_message, reply_markup=create_main_menu(chat_id))

# --- Progress Handler ---
@bot.message_handler(func=lambda message: message.text == "📈 Progress")
def progress_handler(message):
    chat_id = message.chat.id
    init_player_progress(chat_id)
    progress = player_progress[chat_id]
    accuracy = (progress['total_correct'] / progress['total_questions'] * 100) if progress['total_questions'] > 0 else 0
    progress_message = f"""
📈 <b>Your Progress</b>

🔥 <b>Current Streak:</b> {progress['current_streak']} correct
🏆 <b>Best Streak:</b> {progress['best_streak']} correct
✅ <b>Accuracy:</b> {accuracy:.2f}%
❓ <b>Questions Answered:</b> {progress['total_questions']}
✅ <b>Correct Answers:</b> {progress['total_correct']}
⏭️ <b>Questions Until Bonus:</b> {progress['questions_until_bonus']}
    """
    bot.send_message(chat_id, progress_message, reply_markup=create_main_menu(chat_id))

# --- Referrals Handler ---
@bot.message_handler(func=lambda message: message.text == "👥 Referrals")
def referrals_handler(message):
    chat_id = message.chat.id
    user = get_user_data(chat_id)
    if not user:
        bot.send_message(chat_id, "Please /start first.")
        return
    referral_code = user.get("referral_code", f"REF{str(chat_id)[-6:]}")
    referral_message = f"""
👥 <b>Referrals</b>

Invite friends to Learn4Cash and earn <b>2 tokens</b> per referral!
📲 Your referral code: <b>{referral_code}</b>
🔗 Share this link: <code>https://t.me/Learn4CashBot?start={referral_code}</code>
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

🎮 <b>How to Play:</b>
• Select 'General Quiz' or 'Zone Quiz' to start
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
• Contact @Learn4CashAdmin for payment or reward queries

{ABOUT_US}
    """
    bot.send_message(chat_id, help_message, reply_markup=create_main_menu(chat_id))

# --- Feedback Handler ---
@bot.message_handler(func=lambda message: message.text == "💬 Send Feedback")
def feedback_handler(message):
    chat_id = message.chat.id
    user_feedback_mode[chat_id] = True
    bot.send_message(chat_id, "📝 Please type your feedback or suggestions:", reply_markup=ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton("🔙 Cancel")))

@bot.message_handler(func=lambda message: message.chat.id in user_feedback_mode and user_feedback_mode[message.chat.id])
def feedback_input_handler(message):
    chat_id = message.chat.id
    if message.text == "🔙 Cancel":
        del user_feedback_mode[chat_id]
        bot.send_message(chat_id, "Feedback cancelled.", reply_markup=create_main_menu(chat_id))
        return
    send_feedback_to_admin(chat_id, message.text)
    del user_feedback_mode[chat_id]
    bot.send_message(chat_id, "✅ Thank you for your feedback! Our team will review it.", reply_markup=create_main_menu(chat_id))

# --- Admin Menu Handler ---
@bot.message_handler(func=lambda message: message.text == "🔧 Admin Menu" and is_admin(message.chat.id))
def admin_menu_handler(message):
    chat_id = message.chat.id
    bot.send_message(chat_id, "🔧 Admin Menu", reply_markup=create_admin_menu())

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
🎯 Total Points Earned: {total_points}
👥 Total Referrals: {total_referrals}
📋 Pending Token Purchases: {len(pending_transactions)}
    """
    bot.send_message(chat_id, dashboard_message, reply_markup=create_admin_menu())

# --- Run Daily Lottery Handler ---
@bot.message_handler(func=lambda message: message.text == "🎯 Run Daily Lottery" and is_admin(message.chat.id))
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
    log_token_transaction(winner_id, "LOTTERY_WIN", 5, "Daily_Lottery")
    bot.send_message(winner_id, "🎉 Congratulations! You won 5 tokens in the daily lottery!")
    bot.send_message(chat_id, f"🎯 Daily Lottery Winner: {winner['Name']} (@{winner.get('Username', 'None')}) - 5 tokens awarded.", reply_markup=create_admin_menu())

# --- Run Weekly Raffle Handler ---
@bot.message_handler(func=lambda message: message.text == "🎰 Run Weekly Raffle" and is_admin(message.chat.id))
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
    log_token_transaction(winner_id, "RAFFLE_WIN", 10, "Weekly_Raffle")
    bot.send_message(winner_id, "🎰 Congratulations! You won 10 tokens in the weekly raffle!")
    bot.send_message(chat_id, f"🎰 Weekly Raffle Winner: {winner['Name']} (@{winner.get('Username', 'None')}) - 10 tokens awarded.", reply_markup=create_admin_menu())

# --- View Pending Tokens Handler ---
@bot.message_handler(func=lambda message: message.text == "📋 View Pending Tokens" and is_admin(message.chat.id))
def view_pending_tokens_handler(message):
    chat_id = message.chat.id
    sheet_manager = get_sheet_manager()
    pending_transactions = sheet_manager.get_pending_transactions()
    if not pending_transactions:
        bot.send_message(chat_id, "No pending token purchases.", reply_markup=create_admin_menu())
        return
    pending_message = "📋 <b>Pending Token Purchases</b>\n\n"
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
@bot.message_handler(func=lambda message: message.text == "📢 Broadcast Message" and is_admin(message.chat.id))
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
        user_id = user['user_id']
        try:
            bot.send_message(user_id, f"📢 <b>Announcement</b>\n\n{broadcast_text}")
        except Exception as e:
            logger.error(f"Failed to send broadcast to {user_id}: {e}")
    bot.send_message(chat_id, f"📢 Broadcast sent to {len(users)} users.", reply_markup=create_admin_menu())

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
    init_player_progress(user_id)
    progress = player_progress[user_id]
    stats_message = f"""
📈 <b>User Stats for {user['Name']}</b>

👤 <b>User ID:</b> {user_id}
📱 <b>Username:</b> @{user.get('Username', 'None')}
💰 <b>Tokens:</b> {user['Tokens']}
🎯 <b>Points:</b> {user['Points']}
👥 <b>Referrals:</b> {int(user.get('ReferralEarnings', 0))}
🔥 <b>Current Streak:</b> {progress['current_streak']}
🏆 <b>Best Streak:</b> {progress['best_streak']}
✅ <b>Total Correct:</b> {progress['total_correct']}
❓ <b>Total Questions:</b> {progress['total_questions']}
⏭️ <b>Skips Used:</b> {progress['skips_used']}
⏸️ <b>Games Paused:</b> {progress['games_paused']}
    """
    bot.send_message(chat_id, stats_message, reply_markup=create_admin_menu())

# --- Back to User Menu ---
@bot.message_handler(func=lambda message: message.text == "🔙 Back to User Menu" and is_admin(message.chat.id))
def back_to_user_menu_handler(message):
    chat_id = message.chat.id
    bot.send_message(chat_id, "Returning to user menu...", reply_markup=create_main_menu(chat_id))

# --- Pause and Resume Handlers ---
@bot.callback_query_handler(func=lambda call: call.data == "pause_game")
def pause_game_handler(call):
    chat_id = call.message.chat.id
    if chat_id in current_question:
        paused_games[chat_id] = current_question[chat_id]
        init_player_progress(chat_id)
        player_progress[chat_id]['games_paused'] += 1
        del current_question[chat_id]
        bot.send_message(chat_id, "⏸️ Game paused. Use 'General Quiz' or 'Zone Quiz' to resume.", reply_markup=create_main_menu(chat_id))
        bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data == "resume_game")
def resume_game_handler(call):
    chat_id = call.message.chat.id
    if chat_id in paused_games:
        current_question[chat_id] = paused_games[chat_id]
        question = current_question[chat_id]['question']
        choices = current_question[chat_id]['choices']
        answer_markup = InlineKeyboardMarkup()
        for choice in choices:
            answer_markup.add(InlineKeyboardButton(choice, callback_data=f"answer:{choice}"))
        answer_markup.add(InlineKeyboardButton("⏭️ Skip", callback_data="skip_question"), InlineKeyboardButton("⏸️ Pause", callback_data="pause_game"))
        bot.send_message(chat_id, f"▶️ Resuming game:\n🧠 <b>{current_question[chat_id]['mode'].title()} Quiz:</b>\n{question}", reply_markup=answer_markup)
        del paused_games[chat_id]
        bot.answer_callback_query(call.id)
    else:
        bot.send_message(chat_id, "No paused game found.", reply_markup=create_main_menu(chat_id))
        bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data == "new_game")
def new_game_handler(call):
    chat_id = call.message.chat.id
    if chat_id in paused_games:
        del paused_games[chat_id]
    mode = user_quiz_mode.get(chat_id, "general")
    start_new_quiz(chat_id, mode)
    bot.answer_callback_query(call.id)

# --- Bot Polling ---
def schedule_daily_lottery():
    schedule.every().day.at("00:00").do(run_daily_lottery)

def run_daily_lottery():
    sheet_manager = get_sheet_manager()
    users = sheet_manager.get_all_users()
    eligible_users = [user for user in users if float(user.get('Tokens', 0)) > 0]
    if eligible_users:
        winner = random.choice(eligible_users)
        winner_id = winner['UserID']
        current_tokens = float(winner.get('Tokens', 0))
        sheet_manager.update_user_tokens_points(winner_id, current_tokens + 5, winner.get('Points', 0))
        log_token_transaction(winner_id, "LOTTERY_WIN", 5, "Daily_Lottery")
        bot.send_message(winner_id, "🎉 Congratulations! You won 5 tokens in the daily lottery!")
        for admin_id in ADMIN_CHAT_IDS:
            bot.send_message(admin_id, f"🎯 Daily Lottery Winner: {winner['Name']} (@{winner.get('Username', 'None')}) - 5 tokens awarded.")

def run_scheduler():
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    threading.Thread(target=run_scheduler, daemon=True).start()
    
    # Delete webhook before starting polling to prevent 409 conflict
    try:
        bot.delete_webhook()
        logger.info("Webhook deleted successfully. Starting polling...")
    except Exception as e:
        logger.warning(f"Could not delete webhook: {e}")
    
    retry_count = 0
    max_retries = 5
    while retry_count < max_retries:
        try:
            bot.polling(none_stop=True, timeout=60, long_polling_timeout=60)  # Increased timeout
            break  # Exit loop if polling starts successfully
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
