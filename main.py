
# modern_quiz_bot.py
import random
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from datetime import datetime
import os

from sheet_manager import (
    register_user,
    get_user_data,
    update_user_tokens_points,
    reward_referrer,
    log_token_purchase,
    increment_referral_count,
    log_point_redemption
)

# Use environment variable for API key (more secure)
API_KEY = os.getenv("TELEGRAM_BOT_TOKEN", "8470972230:AAFs4wYw94DOiXk2TLpyM0iKlfXLL78JdBE")
bot = telebot.TeleBot(API_KEY, parse_mode='HTML')

quizzes = [
    {"q": "Who was Ghana's first president?", "a": "Kwame Nkrumah", "choices": ["Kwame Nkrumah", "Rawlings", "Mahama", "Busia"]},
    {"q": "When did Ghana gain independence?", "a": "1957", "choices": ["1945", "1957", "1960", "1966"]},
    {"q": "What is the capital of Ghana?", "a": "Accra", "choices": ["Kumasi", "Tamale", "Accra", "Ho"]},
    {"q": "Which region is Lake Volta in?", "a": "Volta", "choices": ["Ashanti", "Volta", "Northern", "Bono"]},
    {"q": "Who led the 1948 Accra Riots?", "a": "The Big Six", "choices": ["Yaa Asantewaa", "The Big Six", "Danquah", "Rawlings"]}
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


@bot.message_handler(commands=['start'])
def start_handler(message):
    chat_id = message.chat.id
    user_name = message.from_user.first_name or "User"
    username = message.from_user.username or ""
    
    # Handle referral
    referrer_id = None
    if len(message.text.split()) > 1:
        try:
            referrer_id = int(message.text.split()[1])
        except ValueError:
            pass
    
    try:
        register_user(chat_id, user_name, username, referrer_id)
        if referrer_id:
            reward_referrer(referrer_id)
            increment_referral_count(referrer_id)
    except Exception as e:
        print(f"[ERROR] Registration failed: {e}")
    
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton("🧠 Start Quiz"), KeyboardButton("💰 Buy Tokens"))
    markup.add(KeyboardButton("👤 Profile"), KeyboardButton("🏆 Redeem"))
    
    welcome_msg = f"""
🎉 <b>Welcome to Learn4Cash, {user_name}!</b>

📚 Test your knowledge and earn rewards!
🎯 Answer quizzes to earn points
💎 Buy tokens for more attempts
🏆 Redeem points for amazing rewards

Choose an option below to get started! 👇
"""
    bot.send_message(chat_id, welcome_msg, reply_markup=markup)


@bot.message_handler(func=lambda message: message.text == "🧠 Start Quiz")
def quiz_handler(message):
    chat_id = message.chat.id
    user = get_user_data(chat_id)
    
    if not user:
        bot.send_message(chat_id, "Please /start first.")
        return
    
    if user['Tokens'] <= 0:
        bot.send_message(chat_id, "⚠️ No tokens left! Buy more tokens to continue playing.")
        return
    
    quiz = random.choice(quizzes)
    current_question[chat_id] = quiz
    
    markup = InlineKeyboardMarkup()
    for choice in quiz['choices']:
        markup.add(InlineKeyboardButton(text=choice, callback_data=f"answer:{choice}"))
    
    bot.send_message(chat_id, f"🧠 <b>Question:</b>\n{quiz['q']}", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith("answer:"))
def answer_handler(call):
    chat_id = call.message.chat.id
    answer = call.data.split("answer:")[1]
    
    if chat_id not in current_question:
        bot.answer_callback_query(call.id, "Quiz expired! Start a new one.")
        return
    
    quiz = current_question[chat_id]
    user = get_user_data(chat_id)
    
    if not user:
        bot.answer_callback_query(call.id, "User not found!")
        return
    
    # Deduct token
    new_tokens = max(0, user['Tokens'] - 1)
    
    if answer == quiz['a']:
        new_points = user['Points'] + 10
        bot.answer_callback_query(call.id, "Correct! +10 points")
        response = "✅ <b>Correct!</b> You earned 10 points!"
    else:
        new_points = user['Points']
        bot.answer_callback_query(call.id, "Wrong answer!")
        response = f"❌ <b>Wrong!</b> The correct answer was: <b>{quiz['a']}</b>"
    
    try:
        update_user_tokens_points(chat_id, new_tokens, new_points)
    except Exception as e:
        print(f"[ERROR] Failed to update user data: {e}")
    
    bot.send_message(chat_id, response)
    del current_question[chat_id]


@bot.message_handler(func=lambda message: message.text == "👤 Profile")
def profile_handler(message):
    chat_id = message.chat.id
    user = get_user_data(chat_id)
    
    if not user:
        bot.send_message(chat_id, "Please /start first.")
        return
    
    profile_msg = f"""
👤 <b>Your Profile</b>

🆔 Name: {user['Name']}
📱 Username: @{user['Username'] or 'Not set'}
💎 Tokens: {user['Tokens']}
🏆 Points: {user['Points']}
💰 Referral Earnings: {user['ReferralEarnings']}
📞 MoMo: {user['MoMoNumber'] or 'Not set'}

🔗 Your referral link:
<code>https://t.me/YourBotUsername?start={chat_id}</code>
"""
    bot.send_message(chat_id, profile_msg)


@bot.message_handler(func=lambda message: message.text == "💰 Buy Tokens")
def buy_tokens_handler(message):
    chat_id = message.chat.id
    
    markup = InlineKeyboardMarkup()
    for label, info in TOKEN_PRICING.items():
        markup.add(InlineKeyboardButton(text=label, callback_data=f"buy:{label}"))
    
    bot.send_message(chat_id, "💰 <b>Choose token package:</b>", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith("buy:"))
def buy_callback_handler(call):
    chat_id = call.message.chat.id
    label = call.data.split("buy:")[1]
    
    if label not in TOKEN_PRICING:
        bot.answer_callback_query(call.id, "Invalid selection!")
        return
    
    info = TOKEN_PRICING[label]
    pending_momo[chat_id] = {"label": label, "amount": info["amount"]}
    
    msg = f"""
💰 <b>Purchase: {label}</b>
💵 Price: {info['price']}

{PAYMENT_INFO}

⏰ You have 15 minutes to complete payment.
"""
    bot.answer_callback_query(call.id)
    bot.send_message(chat_id, msg, disable_web_page_preview=True)


@bot.message_handler(func=lambda message: message.text == "🏆 Redeem")
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
        bot.send_message(message.chat.id, "🏆 Choose a reward to redeem:", reply_markup=markup)
    else:
        bot.send_message(message.chat.id, "⚠️ You don't have enough points to redeem any rewards yet.")


@bot.callback_query_handler(func=lambda call: call.data.startswith("redeem:"))
def redeem_callback_handler(call):
    chat_id = call.message.chat.id
    label = call.data.split("redeem:")[1]
    
    if label not in REDEEM_OPTIONS:
        bot.answer_callback_query(call.id, "Invalid selection!")
        return
    
    reward = REDEEM_OPTIONS[label]
    user = get_user_data(chat_id)
    
    if not user or user['Points'] < reward['points']:
        bot.answer_callback_query(call.id, "❌ Not enough points!")
        return

    new_points = user['Points'] - reward['points']
    
    try:
        update_user_tokens_points(chat_id, user['Tokens'], new_points)
        log_point_redemption(chat_id, label, reward['points'], datetime.utcnow().isoformat())
    except Exception as e:
        print(f"[ERROR] Failed to process redemption: {e}")
        bot.answer_callback_query(call.id, "❌ Error processing redemption!")
        return

    bot.answer_callback_query(call.id, "✅ Redemption successful!")
    bot.send_message(chat_id, f"✅ You've redeemed <b>{label}</b>. Admin will process your reward soon.")
    bot.send_message(chat_id, "📬 Please send your details/screenshot to @Learn4CashAdmin for confirmation.")


@bot.message_handler(commands=['admin'])
def admin_handler(message):
    # Add admin functionality here
    bot.send_message(message.chat.id, "🔧 Admin panel (implement admin features)")


@bot.message_handler(func=lambda message: True)
def default_handler(message):
    bot.send_message(message.chat.id, "🤔 I didn't understand that. Use the menu buttons below!")


if __name__ == "__main__":
    print("🤖 Bot is starting...")
    try:
        bot.polling(none_stop=True, interval=1)
    except Exception as e:
        print(f"[ERROR] Bot crashed: {e}")
