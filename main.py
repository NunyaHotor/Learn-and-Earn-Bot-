
"""
Learn4Cash Quiz Bot - A Telegram bot for educational quizzes with token system.
"""

import random
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from datetime import datetime
import time
import logging

from sheet_manager import (
    register_user,
    get_user_data,
    update_user_tokens_points,
    reward_referrer,
    log_token_purchase,
    increment_referral_count,
    log_point_redemption,
    update_user_momo
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Bot configuration
API_KEY = "8470972230:AAFs4wYw94DOiXk2TLpyM0iKlfXLL78JdBE"
bot = telebot.TeleBot(API_KEY, parse_mode='HTML')

# Quiz data
quizzes = [
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
    {"q": "What is the currency of Nigeria?", "a": "Naira", "choices": ["Cedi", "Shilling", "Rand", "Naira"]}
]

# Global state
pending_momo = {}
current_question = {}

# Configuration constants
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


def create_main_menu():
    """Create the main menu keyboard."""
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        KeyboardButton("🎮 Play Quiz"),
        KeyboardButton("💰 Buy Tokens"),
        KeyboardButton("🎁 Redeem Rewards"),
        KeyboardButton("📊 My Stats"),
        KeyboardButton("👥 Referrals"),
        KeyboardButton("ℹ️ Help")
    )
    return markup


@bot.message_handler(commands=['start'])
def start_handler(message):
    """Handle the /start command."""
    chat_id = message.chat.id
    user = message.from_user
    
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
    
    if success and referrer_id:
        # Reward referrer
        reward_referrer(referrer_id)
        increment_referral_count(referrer_id)
        bot.send_message(referrer_id, "🎉 You got a new referral! +1 token added to your account.")
    
    welcome_msg = f"""
🎓 <b>Welcome to Learn4Cash Quiz Bot!</b>

Hello {user.first_name}! Ready to earn while you learn?

🔐 You start with <b>3 free tokens</b>
🧠 Earn <b>10 points</b> per correct answer
🎁 Redeem points for tokens, airtime, or crypto

Use the menu below to get started!
    """
    
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
    
    if chat_id in current_question:
        bot.send_message(chat_id, "You already have an active question. Please answer it first.")
        return
    
    # Deduct token
    new_tokens = user['Tokens'] - 1
    update_user_tokens_points(chat_id, new_tokens, user['Points'])
    
    # Select random quiz
    quiz = random.choice(quizzes)
    current_question[chat_id] = {'correct': quiz['a']}
    
    # Create inline keyboard
    markup = InlineKeyboardMarkup()
    for choice in quiz['choices']:
        markup.add(InlineKeyboardButton(choice, callback_data=choice))
    
    bot.send_message(
        chat_id, 
        f"🧠 <b>Question:</b>\n{quiz['q']}\n\n💰 Remaining tokens: {new_tokens}", 
        reply_markup=markup
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
        markup.add(InlineKeyboardButton(label, callback_data=f"buy:{label}"))
    
    bot.send_message(
        chat_id,
        "💰 <b>Choose a token package:</b>\n\n" + PAYMENT_INFO,
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
    
    for label, reward in REDEEM_OPTIONS.items():
        if points >= reward['points']:
            markup.add(InlineKeyboardButton(
                text=f"{label} ({reward['points']} pts)", 
                callback_data=f"redeem:{label}"
            ))
    
    if markup.keyboard:
        bot.send_message(
            chat_id, 
            f"🏆 <b>Available Rewards:</b>\n\nYour Points: {points}\n\nChoose a reward to redeem:", 
            reply_markup=markup
        )
    else:
        bot.send_message(chat_id, "⚠️ You don't have enough points to redeem any rewards yet.")


@bot.message_handler(func=lambda message: message.text == "📊 My Stats")
def stats_handler(message):
    """Handle the stats request."""
    chat_id = message.chat.id
    user = get_user_data(chat_id)
    
    if not user:
        bot.send_message(chat_id, "Please /start first.")
        return
    
    stats_msg = f"""
📊 <b>Your Stats</b>

👤 Name: {user['Name']}
🔐 Tokens: {user['Tokens']}
🧠 Points: {user['Points']}
👥 Referrals: {int(user['ReferralEarnings'])}
💰 MoMo: {user['MoMoNumber'] or 'Not set'}
    """
    
    bot.send_message(chat_id, stats_msg)


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

🎁 Earn 1 token for each friend you refer!
📊 Total referrals: {int(user['ReferralEarnings'])}

🔗 Your referral link:
<code>{referral_link}</code>

Share this link with friends to earn rewards!
    """
    
    bot.send_message(chat_id, referral_msg)


@bot.message_handler(func=lambda message: message.text == "ℹ️ Help")
def help_handler(message):
    """Handle the help request."""
    help_msg = """
ℹ️ <b>How to Use Learn4Cash Bot</b>

🎮 <b>Playing:</b>
• Use tokens to answer quiz questions
• Earn 10 points per correct answer
• You start with 3 free tokens

💰 <b>Buying Tokens:</b>
• Choose from different packages
• Pay via MoMo or Crypto
• Send payment proof to @Learn4CashAdmin

🎁 <b>Redeeming:</b>
• Exchange points for rewards
• Get tokens, airtime, or crypto
• Rewards are processed by admin

👥 <b>Referrals:</b>
• Earn 1 token per referral
• Share your referral link
• Unlimited earning potential

Need more help? Contact @Learn4CashAdmin
    """
    
    bot.send_message(message.chat.id, help_msg)


@bot.message_handler(func=lambda message: message.text.isdigit() and message.chat.id in pending_momo)
def momo_number_handler(message):
    """Handle MoMo number input."""
    chat_id = message.chat.id
    momo_number = message.text
    
    # Update user's MoMo number
    if update_user_momo(chat_id, momo_number):
        bot.send_message(chat_id, f"✅ MoMo number {momo_number} saved successfully!")
        
        # Process the pending purchase
        if chat_id in pending_momo:
            package_info = pending_momo[chat_id]
            user = get_user_data(chat_id)
            
            # Add tokens to user account
            new_tokens = user['Tokens'] + package_info['amount']
            update_user_tokens_points(chat_id, new_tokens, user['Points'])
            
            # Log the purchase
            log_token_purchase(chat_id, package_info['label'], package_info['amount'])
            
            bot.send_message(
                chat_id, 
                f"🎉 {package_info['amount']} tokens added to your account!\nTotal tokens: {new_tokens}"
            )
            
            del pending_momo[chat_id]
    else:
        bot.send_message(chat_id, "❌ Failed to save MoMo number. Please try again.")


@bot.callback_query_handler(func=lambda call: call.data.startswith("buy:"))
def buy_callback_handler(call):
    """Handle token purchase callbacks."""
    chat_id = call.message.chat.id
    package_label = call.data.split("buy:")[1]
    package_info = TOKEN_PRICING[package_label]
    
    pending_momo[chat_id] = {
        'label': package_label,
        'amount': package_info['amount']
    }
    
    bot.answer_callback_query(call.id)
    bot.send_message(
        chat_id,
        f"💰 You selected: <b>{package_label}</b>\n\n"
        f"📲 Please send your MoMo number to complete the purchase.\n"
        f"💸 Price: {package_info['price']}\n\n"
        "After sending your MoMo number, make the payment and send proof to @Learn4CashAdmin."
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
    
    # Handle special case for token redemption
    if label == "1 Token":
        new_tokens = user['Tokens'] + 1
        update_user_tokens_points(chat_id, new_tokens, new_points)
        
        bot.answer_callback_query(call.id, "✅ Token added!")
        bot.send_message(chat_id, "🎉 Your token has been credited immediately!")
        
        # Auto-start next game after short delay
        time.sleep(2)
        play_handler(message=type('obj', (object,), {'chat': type('obj', (object,), {'id': chat_id})()})())
    else:
        update_user_tokens_points(chat_id, user['Tokens'], new_points)
        
        bot.answer_callback_query(call.id, "✅ Redemption submitted!")
        bot.send_message(
            chat_id, 
            f"✅ You've redeemed <b>{label}</b>. Admin will process your reward soon.\n"
            "📬 Contact @Learn4CashAdmin for confirmation."
        )

    # Log the redemption
    try:
        log_point_redemption(chat_id, label, reward['points'], datetime.utcnow().isoformat())
    except Exception as e:
        logger.error(f"Failed to log redemption: {e}")


@bot.callback_query_handler(func=lambda call: True)
def answer_handler(call):
    """Handle quiz answer callbacks."""
    chat_id = call.message.chat.id
    user = get_user_data(chat_id)
    
    if not user or chat_id not in current_question:
        bot.answer_callback_query(call.id, "❌ Invalid question!")
        return

    answer = call.data
    correct = current_question[chat_id]['correct']
    tokens = user['Tokens']
    points = user['Points']

    if answer == correct:
        points += 10
        bot.answer_callback_query(call.id, "✅ Correct! +10 points")
        bot.send_message(chat_id, "🎉 Correct answer! You earned <b>10 points</b>!")
    else:
        bot.answer_callback_query(call.id, "❌ Wrong answer!")
        bot.send_message(chat_id, f"❌ Wrong! The correct answer was: <b>{correct}</b>")

    # Update user data
    update_user_tokens_points(chat_id, tokens, points)
    bot.send_message(chat_id, f"💰 Balance: {tokens} tokens | {points} points")
    
    # Clean up current question
    del current_question[chat_id]

    # Auto-continue if user has tokens
    if tokens > 0:
        time.sleep(2)
        play_handler(message=type('obj', (object,), {'chat': type('obj', (object,), {'id': chat_id})()})())
    else:
        bot.send_message(
            chat_id, 
            "🔚 You've run out of tokens. Use '💰 Buy Tokens' to continue playing!",
            reply_markup=create_main_menu()
        )


@bot.message_handler(func=lambda message: True)
def default_handler(message):
    """Handle all other messages."""
    bot.send_message(
        message.chat.id, 
        "Please use the menu buttons below or type /start to begin.",
        reply_markup=create_main_menu()
    )


if __name__ == "__main__":
    logger.info("Starting Learn4Cash Quiz Bot...")
    try:
        bot.infinity_polling(timeout=10, long_polling_timeout=5)
    except Exception as e:
        logger.error(f"Bot error: {e}")
        time.sleep(5)
        bot.infinity_polling(timeout=10, long_polling_timeout=5)
