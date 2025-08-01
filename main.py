# modern_quiz_bot.py
import random
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from datetime import datetime
import time

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

    if label == "1 Token":
        update_user_tokens_points(chat_id, user['Tokens'] + 1, new_points)
        bot.send_message(chat_id, "🎉 Your token has been credited. Enjoy!")
        time.sleep(2)  # short delay before auto play
        from types import SimpleNamespace
        play_handler(SimpleNamespace(chat=SimpleNamespace(id=chat_id)))


@bot.callback_query_handler(func=lambda call: True)
def answer_handler(call):
    chat_id = call.message.chat.id
    user = get_user_data(chat_id)
    if not user or chat_id not in current_question:
        return

    answer = call.data
    correct = current_question[chat_id]['correct']

    tokens = user['Tokens']
    points = user['Points']

    if answer == correct:
        points += 10
        bot.answer_callback_query(call.id, "✅ Correct!")
        bot.send_message(chat_id, "🎉 You earned <b>10 points</b>!")
    else:
        bot.answer_callback_query(call.id, "❌ Wrong.")
        bot.send_message(chat_id, f"The correct answer was: <b>{correct}</b>")

    update_user_tokens_points(chat_id, tokens, points)
    bot.send_message(chat_id, f"Balance: 🔐 <b>{tokens} tokens</b> | 🧠 <b>{points} points</b>")
    del current_question[chat_id]

    if tokens > 0:
        time.sleep(2)  # cooldown before next question
        from types import SimpleNamespace
        play_handler(SimpleNamespace(chat=SimpleNamespace(id=chat_id)))
    else:
        bot.send_message(chat_id, "🔚 You’ve run out of tokens. Use /buytokens to top up.")
        from types import SimpleNamespace
        buytokens_handler(SimpleNamespace(chat=SimpleNamespace(id=chat_id)))
