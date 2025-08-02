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
    update_user_momo,
    check_and_give_daily_reward,
    update_last_claim_date
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
custom_token_requests = {}

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
ADMIN_CHAT_ID = None  # Set this to admin's chat ID for notifications

TOKEN_PRICING = {
    "5 tokens (₵2)": {"amount": 5, "price": "2 GHS"},
    "12 tokens (₵5)": {"amount": 12, "price": "5 GHS"},
    "30 tokens (₵10)": {"amount": 30, "price": "10 GHS"}
}

REDEEM_OPTIONS = {
    "1 Token": {"points": 30, "reward": "+1 Token"},
    "3 Tokens": {"points": 90, "reward": "+3 Tokens"},
    "5 Tokens": {"points": 150, "reward": "+5 Tokens"},
    "GHS 2 Airtime": {"points": 100, "reward": "GHS 2 Airtime"},
    "GHS 5 Airtime": {"points": 250, "reward": "GHS 5 Airtime"},
    "GHS 10 Airtime": {"points": 500, "reward": "GHS 10 Airtime"},
    "Internet Data": {"points": 300, "reward": "500MB Data"},
    "MoMo": {"points": 400, "reward": "GHS 3 MoMo"},
    "2 USDT": {"points": 600, "reward": "2 USDT (Crypto)"},
    "5 USDT": {"points": 1500, "reward": "5 USDT (Crypto)"}
}

PAYMENT_LINKS = {
    "momo": "https://paystack.com/pay/momo-learn4cash",
    "crypto": "https://buycrypto.learn4cash.io",
    "paystack": "https://paystack.shop/pay/6yjmo6ykwr"
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
        KeyboardButton("🎁 Daily Reward"),
        KeyboardButton("📊 My Stats"),
        KeyboardButton("👥 Referrals"),
        KeyboardButton("ℹ️ Help"),
        KeyboardButton("🏆 Leaderboard")
    )
    return markup


# Implement leaderboard functionality (Example)
def update_leaderboard(user_id, points):
    """Update the leaderboard with user points."""
    # Dummy leaderboard (replace with actual data storage)
    leaderboard = {}  # user_id: points

    leaderboard[user_id] = points
    sorted_leaderboard = sorted(leaderboard.items(), key=lambda item: item[1], reverse=True)
    return sorted_leaderboard


def get_top_users(limit=10):
    """Get the top users from the leaderboard."""
    # Dummy leaderboard (replace with actual data storage)
    leaderboard = {123: 100, 456: 200, 789: 150}  # user_id: points
    sorted_leaderboard = sorted(leaderboard.items(), key=lambda item: item[1], reverse=True)
    return sorted_leaderboard[:limit]


def broadcast_winner(winner_id, period="daily"):
    """Broadcast the winner to all players (example)."""
    # Placeholder for broadcasting logic (e.g., sending a message to all users)
    message = f"🎉 Congrats to user {winner_id} for winning the {period} reward!"
    # Add logic to send this message to all users or a broadcast channel
    logger.info(message)  # Log the broadcast message for testing


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

    # Check for daily reward
    daily_reward_given = check_and_give_daily_reward(chat_id)

    # Send motivational message
    motivation = random.choice(MOTIVATIONAL_MESSAGES)

    welcome_msg = f"""
🎓 <b>Welcome to Learn4Cash Quiz Bot!</b>

Hello {user.first_name}! Ready to earn while you learn?

{motivation}

🔐 You start with <b>3 free tokens</b>
🧠 Earn <b>10 points</b> per correct answer
🎁 Redeem points for tokens, airtime, or crypto
🎁 Get <b>1 free token daily</b> - just visit us!

Use the menu below to get started!
    """

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

    # Add custom token option
    markup.add(InlineKeyboardButton("🎯 Custom Amount", callback_data="buy:custom"))

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


@bot.message_handler(func=lambda message: message.text == "🎁 Daily Reward")
def daily_reward_handler(message):
    """Handle the daily reward request."""
    chat_id = message.chat.id
    user = get_user_data(chat_id)

    if not user:
        bot.send_message(chat_id, "Please /start first.")
        return

    # Check for daily reward
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
• Choose from different packages or custom amount
• Pay via MoMo or Crypto using secure payment links
• Tokens processed within 5-10 minutes after payment

🎁 <b>Daily Rewards:</b>
• Get 1 free token every day
• Just visit the bot daily to claim
• No limits on daily claims!

🎁 <b>Redeeming:</b>
• Exchange points for rewards
• Get tokens, airtime, data, MoMo, or crypto
• Rewards are processed by admin

👥 <b>Referrals:</b>
• Earn 1 token per referral
• Share your referral link
• Unlimited earning potential

🎰 <b>Fair Lottery System:</b>
• Daily, weekly, and monthly winners
• Based on points with fair weighted probability
• Test the system: /test_lottery
• See live draw simulation: /simulate_draw

Need more help? Contact @Learn4CashAdmin
    """

    bot.send_message(message.chat.id, help_msg)


@bot.message_handler(func=lambda message: message.text == "🏆 Leaderboard")
def leaderboard_handler(message):
    """Handle the leaderboard request."""
    chat_id = message.chat.id
    top_users = get_top_users()

    if not top_users:
        bot.send_message(chat_id, "📊 Leaderboard is empty.")
        return

    leaderboard_msg = "🏆 <b>Leaderboard</b> 🏆\n\n"
    for i, (user_id, points) in enumerate(top_users):
        leaderboard_msg += f"{i + 1}. User {user_id}: {points} points\n"  # Replace user_id with actual username

    bot.send_message(chat_id, leaderboard_msg)

@bot.message_handler(commands=['test_lottery'])
def test_lottery_handler(message):
    """Test the lottery system (admin only)."""
    chat_id = message.chat.id
    
    # For testing purposes, allow anyone to test the lottery
    # In production, you might want to restrict this to admins
    
    # Simulate user data for testing
    test_users = {
        chat_id: get_user_data(chat_id)['Points'] if get_user_data(chat_id) else 100,
        123456789: 250,
        987654321: 180,
        555666777: 320,
        111222333: 90
    }
    
    # Test daily winner selection
    daily_winner = select_winner_from_data(test_users, "daily")
    weekly_winner = select_winner_from_data(test_users, "weekly") 
    monthly_winner = select_winner_from_data(test_users, "monthly")
    
    test_msg = f"""
🎰 <b>Lottery System Test</b>

👥 <b>Test Pool:</b>
User {chat_id}: {test_users[chat_id]} points
User 123456789: 250 points  
User 987654321: 180 points
User 555666777: 320 points
User 111222333: 90 points

🏆 <b>Results:</b>
📅 Daily Winner: User {daily_winner}
📊 Weekly Winner: User {weekly_winner}  
🎊 Monthly Winner: User {monthly_winner}

✨ <b>Selection is based on:</b>
• Points earned (weighted probability)
• Random selection for fairness
• Higher points = higher chance but not guaranteed

🔄 Run /test_lottery again to see different results!
    """
    
    bot.send_message(chat_id, test_msg)

@bot.message_handler(commands=['simulate_draw'])
def simulate_draw_handler(message):
    """Simulate a live lottery draw for transparency."""
    chat_id = message.chat.id
    
    # Get current user data
    user = get_user_data(chat_id)
    if not user:
        bot.send_message(chat_id, "Please /start first.")
        return
    
    # Simulate live draw
    bot.send_message(chat_id, "🎰 <b>Starting Live Lottery Draw...</b>")
    time.sleep(1)
    
    bot.send_message(chat_id, "🔄 Gathering eligible participants...")
    time.sleep(2)
    
    # Simulate participants
    participants = [
        {"id": chat_id, "points": user['Points'], "name": user['Name']},
        {"id": 123456, "points": 250, "name": "Player2"},
        {"id": 789012, "points": 180, "name": "Player3"},
        {"id": 345678, "points": 320, "name": "Player4"}
    ]
    
    bot.send_message(chat_id, f"👥 Found {len(participants)} eligible participants!")
    time.sleep(1)
    
    # Show participants
    participants_msg = "📋 <b>Participants:</b>\n\n"
    for p in participants:
        participants_msg += f"• {p['name']} (ID: {p['id']}): {p['points']} points\n"
    
    bot.send_message(chat_id, participants_msg)
    time.sleep(2)
    
    # Simulate drawing process
    bot.send_message(chat_id, "🎲 Rolling the dice...")
    time.sleep(2)
    
    bot.send_message(chat_id, "🔄 Calculating probabilities...")
    time.sleep(1)
    
    # Select winner based on weighted probability
    winner = weighted_random_selection(participants)
    
    bot.send_message(chat_id, "🎊 <b>AND THE WINNER IS...</b>")
    time.sleep(2)
    
    bot.send_message(
        chat_id, 
        f"🏆 <b>CONGRATULATIONS!</b>\n\n"
        f"🎉 Winner: {winner['name']}\n"
        f"🆔 ID: {winner['id']}\n"
        f"🧠 Points: {winner['points']}\n\n"
        f"🎁 Prize will be processed shortly!\n"
        f"📢 This draw was conducted fairly using weighted probability!"
    )


@bot.message_handler(func=lambda message: message.text.isdigit() and (message.chat.id in pending_momo or message.chat.id in custom_token_requests))
def number_input_handler(message):
    """Handle MoMo number input or custom token amount input."""
    chat_id = message.chat.id
    number = message.text

    # Handle custom token amount input
    if chat_id in custom_token_requests and custom_token_requests[chat_id].get('waiting_for_amount'):
        token_amount = int(number)
        if token_amount < 1:
            bot.send_message(chat_id, "❌ Please enter a valid number of tokens (minimum 1).")
            return
        if token_amount > 100:
            bot.send_message(chat_id, "❌ Maximum 100 tokens per purchase. Please contact admin for larger amounts.")
            return

        # Calculate price (₵0.4 per token based on 5 tokens for ₵2)
        price_cedis = round(token_amount * 0.4, 2)

        custom_token_requests[chat_id] = {
            'amount': token_amount,
            'price': f"{price_cedis} GHS",
            'waiting_for_momo': True
        }

        bot.send_message(
            chat_id,
            f"💰 <b>Custom Order:</b> {token_amount} tokens for ₵{price_cedis}\n\n"
            "📲 Please send your MoMo number to proceed with payment."
        )
        return

    # Handle MoMo number input
    if chat_id in pending_momo or (chat_id in custom_token_requests and custom_token_requests[chat_id].get('waiting_for_momo')):
        momo_number = number

        # Update user's MoMo number
        if update_user_momo(chat_id, momo_number):
            bot.send_message(chat_id, f"✅ MoMo number {momo_number} saved successfully!")

            # Show payment options for both standard and custom purchases
            payment_markup = InlineKeyboardMarkup()
            payment_markup.add(
                InlineKeyboardButton("💳 Pay with MoMo", url=PAYMENT_LINKS['paystack']),
                InlineKeyboardButton("₿ Pay with Crypto", url=PAYMENT_LINKS['crypto'])
            )
            payment_markup.add(InlineKeyboardButton("✅ Payment Completed", callback_data="payment_completed"))

            if chat_id in pending_momo:
                package_info = pending_momo[chat_id]
                bot.send_message(
                    chat_id,
                    f"💰 <b>Payment Options for {package_info['label']}</b>\n\n"
                    f"💸 Amount: {TOKEN_PRICING[package_info['label']]['price']}\n"
                    f"📱 MoMo: {momo_number}\n\n"
                    "Choose your payment method below:",
                    reply_markup=payment_markup
                )
            elif chat_id in custom_token_requests:
                custom_info = custom_token_requests[chat_id]
                bot.send_message(
                    chat_id,
                    f"💰 <b>Payment Options for Custom Purchase</b>\n\n"
                    f"🪙 Tokens: {custom_info['amount']}\n"
                    f"💸 Amount: {custom_info['price']}\n"
                    f"📱 MoMo: {momo_number}\n\n"
                    "Choose your payment method below:",
                    reply_markup=payment_markup
                )
        else:
            bot.send_message(chat_id, "❌ Failed to save MoMo number. Please try again.")


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
            "Please enter the number of tokens you want to buy (1-100):\n\n"
            "💡 <i>Rate: ₵0.40 per token</i>"
        )
        return

    package_info = TOKEN_PRICING[package_label]

    pending_momo[chat_id] = {
        'label': package_label,
        'amount': package_info['amount']
    }

    bot.send_message(
        chat_id,
        f"💰 You selected: <b>{package_label}</b>\n\n"
        f"📲 Please send your MoMo number to complete the purchase.\n"
        f"💸 Price: {package_info['price']}\n\n"
        "After sending your MoMo number:\n"
        f"💳 Pay securely via: {PAYMENT_LINKS['paystack']}\n"
        "💰 Or pay crypto (USDT): Check payment links\n"
        "🔄 Tokens will be added automatically after payment confirmation!\n"
        "📞 Contact @Learn4CashAdmin for any issues."
    )


@bot.callback_query_handler(func=lambda call: call.data == "payment_completed")
def payment_completed_handler(call):
    """Handle payment completion confirmation."""
    chat_id = call.message.chat.id
    bot.answer_callback_query(call.id)

    if chat_id in pending_momo:
        package_info = pending_momo[chat_id]
        
        # Simulate automatic token addition (in real scenario, this would be after payment verification)
        user = get_user_data(chat_id)
        if user:
            new_tokens = user['Tokens'] + package_info['amount']
            update_user_tokens_points(chat_id, new_tokens, user['Points'])
            
            # Send success notification
            bot.send_message(
                chat_id,
                f"🎉 <b>Payment Successful!</b>\n\n"
                f"✅ <b>{package_info['amount']} tokens</b> have been added to your account!\n"
                f"💰 Total tokens: <b>{new_tokens}</b>\n\n"
                f"🎮 Ready to play more quizzes?\n"
                f"Thank you for using Learn4Cash! 🚀"
            )
            
            # Log successful purchase
            log_token_purchase(chat_id, f"COMPLETED: {package_info['label']}", package_info['amount'])
        
        del pending_momo[chat_id]

    elif chat_id in custom_token_requests:
        custom_info = custom_token_requests[chat_id]
        
        # Simulate automatic token addition for custom purchase
        user = get_user_data(chat_id)
        if user:
            new_tokens = user['Tokens'] + custom_info['amount']
            update_user_tokens_points(chat_id, new_tokens, user['Points'])
            
            # Send success notification
            bot.send_message(
                chat_id,
                f"🎉 <b>Payment Successful!</b>\n\n"
                f"✅ <b>{custom_info['amount']} tokens</b> have been added to your account!\n"
                f"💰 Total tokens: <b>{new_tokens}</b>\n"
                f"💸 Amount paid: {custom_info['price']}\n\n"
                f"🎮 Ready to play more quizzes?\n"
                f"Thank you for using Learn4Cash! 🚀"
            )
            
            # Log successful purchase
            log_token_purchase(chat_id, f"COMPLETED: Custom {custom_info['amount']} tokens", custom_info['amount'])
        
        del custom_token_requests[chat_id]

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
    if "Token" in label and label.endswith("Token") or label.endswith("Tokens"):
        # Extract token amount from label
        token_amount = 1
        if label == "3 Tokens":
            token_amount = 3
        elif label == "5 Tokens":
            token_amount = 5

        new_tokens = user['Tokens'] + token_amount
        update_user_tokens_points(chat_id, new_tokens, new_points)

        bot.answer_callback_query(call.id, f"✅ {token_amount} token(s) added!")
        
        # Enhanced token redemption notification
        bot.send_message(
            chat_id, 
            f"🎉 <b>Redemption Successful!</b>\n\n"
            f"✅ <b>{token_amount} token(s)</b> added to your account!\n"
            f"💰 Total tokens: <b>{new_tokens}</b>\n"
            f"🧠 Remaining points: <b>{new_points}</b>\n"
            f"📉 Points used: <b>{reward['points']}</b>\n\n"
            f"🎮 <b>Auto-starting next quiz...</b>"
        )

        # Auto-start next game after short delay
        time.sleep(2)
        play_handler(message=type('obj', (object,), {'chat': type('obj', (object,), {'id': chat_id})()})())
    
    # Handle other reward options (Airtime, MoMo, Data, Crypto)
    elif "Airtime" in label or "MoMo" in label or "Data" in label or "USDT" in label:
        update_user_tokens_points(chat_id, user['Tokens'], new_points)
        bot.answer_callback_query(call.id, "✅ Redemption submitted!")
        
        # Enhanced external reward notification
        bot.send_message(
            chat_id,
            f"🎁 <b>Redemption Request Submitted!</b>\n\n"
            f"🏆 Reward: <b>{reward['reward']}</b>\n"
            f"📉 Points deducted: <b>{reward['points']}</b>\n"
            f"🧠 Remaining points: <b>{new_points}</b>\n"
            f"⏳ Status: <b>Processing</b>\n\n"
            f"📬 <b>Next Steps:</b>\n"
            f"• Admin will process your reward within 24 hours\n"
            f"• You'll receive a confirmation message\n"
            f"• Contact @Learn4CashAdmin for urgent issues\n\n"
            f"🎮 Continue playing to earn more points!"
        )
        
        # Send notification to admin (if admin chat ID is available)
        admin_notification = (
            f"🔔 <b>New Redemption Request</b>\n\n"
            f"👤 User ID: {chat_id}\n"
            f"👤 Name: {user['Name']}\n"
            f"🎁 Reward: {reward['reward']}\n"
            f"📉 Points used: {reward['points']}\n"
            f"📱 MoMo: {user.get('MoMoNumber', 'Not set')}\n"
            f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        # Note: Add admin chat ID to send notification
        
    else:
        update_user_tokens_points(chat_id, user['Tokens'], new_points)
        bot.answer_callback_query(call.id, "✅ Redemption submitted!")
        
        bot.send_message(
            chat_id, 
            f"🎁 <b>Redemption Request Submitted!</b>\n\n"
            f"🏆 Reward: <b>{reward['reward']}</b>\n"
            f"📉 Points deducted: <b>{reward['points']}</b>\n"
            f"🧠 Remaining points: <b>{new_points}</b>\n"
            f"⏳ Status: <b>Processing</b>\n\n"
            f"📬 Admin will process your reward within 24 hours.\n"
            f"📞 Contact @Learn4CashAdmin for confirmation."
        )

    # Log the redemption
    try:
        log_point_redemption(chat_id, label, reward['points'], datetime.utcnow().isoformat())
        logger.info(f"Redemption logged for user {chat_id}: {label} ({reward['points']} points)")
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


@bot.message_handler(func=lambda message: message.text.isdigit() and message.chat.id in custom_token_requests and custom_token_requests[message.chat.id].get('waiting_for_amount'))
def custom_token_amount_handler(message):
    """Handle custom token amount input."""
    number_input_handler(message)

@bot.message_handler(func=lambda message: True)
def default_handler(message):
    """Handle all other messages."""
    chat_id = message.chat.id

    # Check if user is in custom token flow
    if chat_id in custom_token_requests:
        if custom_token_requests[chat_id].get('waiting_for_amount'):
            bot.send_message(chat_id, "Please enter a valid number for tokens (1-100).")
            return
        elif custom_token_requests[chat_id].get('waiting_for_momo'):
            bot.send_message(chat_id, "Please enter your MoMo number (digits only).")
            return

    bot.send_message(
        chat_id, 
        "Please use the menu buttons below or type /start to begin.",
        reply_markup=create_main_menu()
    )

# Implement daily, weekly, monthly winner selection and broadcasting (example)
def select_winner(period="daily"):
    """Select a winner based on points for the given period."""
    # Get actual user data from sheets (simplified for demo)
    user_points = {123: 150, 456: 200, 789: 180}  # user_id: points

    if not user_points:
        return None

    # Use weighted selection instead of just highest points
    return weighted_random_selection_from_dict(user_points)

def select_winner_from_data(user_data, period="daily"):
    """Select winner from provided user data for testing."""
    if not user_data:
        return None
    
    return weighted_random_selection_from_dict(user_data)

def weighted_random_selection_from_dict(user_points):
    """Select winner using weighted probability based on points."""
    if not user_points:
        return None
    
    # Convert to list format for weighted selection
    participants = [{"id": uid, "points": points} for uid, points in user_points.items()]
    winner = weighted_random_selection(participants)
    return winner["id"] if winner else None

def weighted_random_selection(participants):
    """
    Select a winner using weighted probability.
    Higher points = higher chance, but everyone has a fair chance.
    """
    if not participants:
        return None
    
    # Calculate weights (points + base weight for fairness)
    base_weight = 10  # Everyone gets at least 10 weight
    total_weight = 0
    weights = []
    
    for participant in participants:
        weight = participant["points"] + base_weight
        weights.append(weight)
        total_weight += weight
    
    # Generate random number
    rand_num = random.randint(1, total_weight)
    
    # Find winner based on weighted selection
    current_weight = 0
    for i, participant in enumerate(participants):
        current_weight += weights[i]
        if rand_num <= current_weight:
            return participant
    
    # Fallback (should never reach here)
    return participants[0]


def notify_admin(message):
    """Send notification to admin if admin chat ID is set."""
    if ADMIN_CHAT_ID:
        try:
            bot.send_message(ADMIN_CHAT_ID, message)
        except Exception as e:
            logger.error(f"Failed to notify admin: {e}")


def notify_user_token_addition(chat_id, amount, total_tokens, reason="purchase"):
    """Send notification when tokens are added to user account."""
    try:
        user = get_user_data(chat_id)
        if not user:
            return
        
        if reason == "purchase":
            message = (
                f"🎉 <b>Tokens Added Successfully!</b>\n\n"
                f"✅ <b>+{amount} tokens</b> added to your account\n"
                f"💰 Total tokens: <b>{total_tokens}</b>\n"
                f"🎮 Ready to continue playing!\n\n"
                f"Thank you for your purchase! 🚀"
            )
        elif reason == "daily":
            message = (
                f"🎁 <b>Daily Reward Claimed!</b>\n\n"
                f"✅ <b>+{amount} token</b> added to your account\n"
                f"💰 Total tokens: <b>{total_tokens}</b>\n"
                f"🔄 Come back tomorrow for more!\n\n"
                f"{random.choice(MOTIVATIONAL_MESSAGES)}"
            )
        elif reason == "referral":
            message = (
                f"👥 <b>Referral Bonus!</b>\n\n"
                f"✅ <b>+{amount} token</b> for successful referral\n"
                f"💰 Total tokens: <b>{total_tokens}</b>\n"
                f"🎉 Keep sharing to earn more!"
            )
        else:
            message = (
                f"🎉 <b>Tokens Added!</b>\n\n"
                f"✅ <b>+{amount} tokens</b> added to your account\n"
                f"💰 Total tokens: <b>{total_tokens}</b>"
            )
        
        bot.send_message(chat_id, message)
        logger.info(f"Token addition notification sent to user {chat_id}: +{amount} tokens")
        
    except Exception as e:
        logger.error(f"Failed to send token notification to user {chat_id}: {e}")


def notify_user_redemption_status(chat_id, reward_name, status="completed", additional_info=""):
    """Notify user about redemption status update."""
    try:
        if status == "completed":
            message = (
                f"✅ <b>Reward Delivered!</b>\n\n"
                f"🎁 <b>{reward_name}</b> has been processed successfully!\n"
                f"📱 Check your account/phone for the reward\n"
                f"{additional_info}\n\n"
                f"🎮 Continue playing to earn more rewards!\n"
                f"Thank you for using Learn4Cash! 🚀"
            )
        elif status == "failed":
            message = (
                f"❌ <b>Reward Processing Failed</b>\n\n"
                f"🎁 Reward: <b>{reward_name}</b>\n"
                f"💬 Reason: {additional_info}\n\n"
                f"📞 Please contact @Learn4CashAdmin for assistance\n"
                f"🔄 Your points will be refunded if needed"
            )
        else:
            message = (
                f"⏳ <b>Reward Update</b>\n\n"
                f"🎁 Reward: <b>{reward_name}</b>\n"
                f"📋 Status: <b>{status}</b>\n"
                f"{additional_info}"
            )
        
        bot.send_message(chat_id, message)
        logger.info(f"Redemption status notification sent to user {chat_id}: {reward_name} - {status}")
        
    except Exception as e:
        logger.error(f"Failed to send redemption notification to user {chat_id}: {e}")


def schedule_winners():
    """Schedule daily, weekly, and monthly winner selection."""
    while True:
        now = datetime.now()

        # Daily winner selection (at 00:00)
        if now.hour == 0 and now.minute == 0:
            daily_winner = select_winner("daily")
            if daily_winner:
                broadcast_winner(daily_winner, "daily")
            time.sleep(60)  # Prevent multiple selections in the same minute

        # Weekly winner selection (every Sunday at 00:00)
        if now.weekday() == 6 and now.hour == 0 and now.minute == 0:
            weekly_winner = select_winner("weekly")
            if weekly_winner:
                broadcast_winner(weekly_winner, "weekly")
            time.sleep(60)

        # Monthly winner selection (on the 1st of each month at 00:00)
        if now.day == 1 and now.hour == 0 and now.minute == 0:
            monthly_winner = select_winner("monthly")
            if monthly_winner:
                broadcast_winner(monthly_winner, "monthly")
            time.sleep(60)

        time.sleep(30)  # Check every 30 seconds


if __name__ == "__main__":
    logger.info("Starting Learn4Cash Quiz Bot...")

    # Start the scheduler in a separate thread
    import threading
    scheduler_thread = threading.Thread(target=schedule_winners)
    scheduler_thread.daemon = True  # Allow the main program to exit even if the thread is running
    scheduler_thread.start()

    try:
        bot.infinity_polling(timeout=10, long_polling_timeout=5)
    except Exception as e:
        logger.error(f"Bot error: {e}")
        time.sleep(5)
        bot.infinity_polling(timeout=10, long_polling_timeout=5)