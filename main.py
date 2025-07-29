# modern_quiz_bot.py
import random
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

from sheet_manager import register_user, get_user_data, update_user_tokens_points, reward_referrer

API_KEY = "8470972230:AAFs4wYw94DOiXk2TLpyM0iKlfXLL78JdBE"
bot = telebot.TeleBot(API_KEY, parse_mode='HTML')

# In-memory user and referral data (for production, use persistent storage)
users = {}
referrals = {}

quizzes = [
    {"q": "Who was Ghana’s first president?", "a": "Kwame Nkrumah", "choices": ["Kwame Nkrumah", "Rawlings", "Mahama", "Busia"]},
    {"q": "When did Ghana gain independence?", "a": "1957", "choices": ["1945", "1957", "1960", "1966"]},
    {"q": "What is the capital of Ghana?", "a": "Accra", "choices": ["Kumasi", "Tamale", "Accra", "Ho"]},
    {"q": "Which region is Lake Volta in?", "a": "Volta", "choices": ["Ashanti", "Volta", "Northern", "Bono"]},
    {"q": "Who led the 1948 Accra Riots?", "a": "The Big Six", "choices": ["Yaa Asantewaa", "The Big Six", "Danquah", "Rawlings"]}
]

def get_user(chat_id):
    return users.get(chat_id)

def ensure_user(chat_id, ref_code=None):
    if chat_id not in users:
        users[chat_id] = {"tokens": 3, "points": 0, "ref": ref_code}
        if ref_code:
            referrals.setdefault(ref_code, []).append(chat_id)
        return True
    return False

@bot.message_handler(commands=['start'])
def start_handler(message):
    chat_id = message.chat.id
    parts = message.text.split()
    ref_code = parts[1] if len(parts) > 1 else None

    is_new = ensure_user(chat_id, ref_code)
    if is_new:
        bot.send_message(chat_id, "🎉 Welcome to <b>Learn4Cash</b>! You have <b>3</b> free tokens.")
    else:
        bot.send_message(chat_id, "Welcome back!")

@bot.message_handler(commands=['balance'])
def balance_handler(message):
    chat_id = message.chat.id
    user = get_user(chat_id)
    if user:
        bot.send_message(chat_id, f"🔐 Tokens: <b>{user['tokens']}</b> | 🧠 Points: <b>{user['points']}</b>")
    else:
        bot.send_message(chat_id, "Type /start to register.")

@bot.message_handler(commands=['refer'])
def refer_handler(message):
    chat_id = message.chat.id
    if chat_id in users:
        ref_link = f"https://t.me/YOUR_BOT_USERNAME?start={chat_id}"
        bot.send_message(chat_id, f"📢 Share this to earn tokens:
<b>{ref_link}</b>")
    else:
        bot.send_message(chat_id, "Please /start first.")

@bot.message_handler(commands=['play'])
def play_handler(message):
    chat_id = message.chat.id
    user = get_user(chat_id)

    if not user:
        bot.send_message(chat_id, "Please /start first.")
        return

    if user['tokens'] < 1:
        bot.send_message(chat_id, "🚫 You don’t have enough tokens. Use /buytokens.")
        return

    user['tokens'] -= 1
    quiz = random.choice(quizzes)
    question, correct, options = quiz['q'], quiz['a'], quiz['choices'][:]
    random.shuffle(options)

    user['current_question'] = {"question": question, "correct": correct}

    markup = InlineKeyboardMarkup()
    for opt in options:
        markup.add(InlineKeyboardButton(text=opt, callback_data=opt))

    bot.send_message(chat_id, f"❓ <b>{question}</b>", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def answer_handler(call):
    chat_id = call.message.chat.id
    user = get_user(chat_id)
    if not user or 'current_question' not in user:
        return

    answer = call.data
    correct = user['current_question']['correct']
    del user['current_question']

    if answer == correct:
        user['points'] += 10
        bot.answer_callback_query(call.id, "✅ Correct!")
        bot.send_message(chat_id, "🎉 You earned <b>10 points</b>!")
    else:
        bot.answer_callback_query(call.id, "❌ Wrong.")
        bot.send_message(chat_id, f"The correct answer was: <b>{correct}</b>")

    bot.send_message(chat_id, f"Balance: 🔐 <b>{user['tokens']} tokens</b> | 🧠 <b>{user['points']} points</b>")

if __name__ == '__main__':
    print("Bot is running...")
    bot.infinity_polling()
