import logging
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

logger = logging.getLogger(__name__)

class UIEnhancer:
    def __init__(self):
        self.colors = {
            'primary': '#0088cc',
            'secondary': '#ff6b6b',
            'success': '#28a745',
            'warning': '#ffc107',
            'danger': '#dc3545',
            'info': '#17a2b8'
        }
        
    def create_main_menu(self, is_admin=False):
        """Create enhanced main menu"""
        markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        
        # Main game buttons
        game_buttons = [
            KeyboardButton("🎮 Start Quiz"),
            KeyboardButton("🌍 Zone Quiz"),
            KeyboardButton("💰 Buy Tokens"),
            KeyboardButton("🎁 Redeem Rewards"),
            KeyboardButton("🎁 Daily Reward"),
            KeyboardButton("📊 My Stats"),
            KeyboardButton("📈 Progress"),
            KeyboardButton("👥 Referrals"),
            KeyboardButton("🏆 Leaderboard"),
            KeyboardButton("ℹ️ Help"),
            KeyboardButton("💬 Send Feedback"),
            KeyboardButton("🌐 Current Affairs"),
            KeyboardButton("🎁 Tiered Rewards"),
            KeyboardButton("🌍 African Countries"),
            KeyboardButton("🛒 Marketplace")
        ]
        
        if is_admin:
            game_buttons.append(KeyboardButton("🔧 Admin Menu"))
            
        markup.add(*game_buttons)
        return markup
        
    def create_language_menu(self):
        """Create language selection menu"""
        markup = ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(
            KeyboardButton("🇺🇸 English"),
            KeyboardButton("🇫🇷 French"),
            KeyboardButton("🇸🇪 Swedish"),
            KeyboardButton("🇸🇦 Arabic")
        )
        return markup
        
    def create_zone_menu(self):
        """Create zone selection menu"""
        markup = ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(
            KeyboardButton("🇺🇸 English"),
            KeyboardButton("🇫🇷 French"),
            KeyboardButton("🇸🇪 Swedish"),
            KeyboardButton("🇸🇦 Arabic")
        )
        return markup
        
    def create_tier_menu(self):
        """Create tier-based reward menu"""
        markup = InlineKeyboardMarkup(row_width=2)
        markup.add(
            InlineKeyboardButton("🥉 Bronze", callback_data="tier:bronze"),
            InlineKeyboardButton("🥈 Silver", callback_data="tier:silver"),
            InlineKeyboardButton("🥇 Gold", callback_data="tier:gold"),
            InlineKeyboardButton("🏆 Platinum", callback_data="tier:platinum"),
        )
        return markup
        
    def create_admin_menu(self):
        """Create admin menu"""
        markup = ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(
            KeyboardButton("📊 Admin Dashboard"),
            KeyboardButton("📋 View Pending Tokens"),
            KeyboardButton("✅ Approve Token Purchase"),
            KeyboardButton("📢 Broadcast Message"),
            KeyboardButton("📈 User Stats"),
            KeyboardButton("🎯 Run Daily Lottery"),
            KeyboardButton("🎰 Run Weekly Raffle"),
            KeyboardButton("🔙 Back to User Menu")
        )
        return markup

ui_enhancer = UIEnhancer()
