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
    ],
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
        {"q": "Which country is famous for its pyramids?", "a": "Egypt", "choices": ["Egypt", "Morocco", "Algeria", "Tunisia"]}, coffee exports?", "a": "Ethiopia", "choices": ["Ethiopia", "Kenya", "Uganda", "Tanzania"]},
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
        {"q": "Which country is famous for its pyramids?", "a": "Egypt", "choices": ["Egypt", "Morocco", "Algeria", "Tunisia"]},
