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
            KeyboardButton("💬 Feedback"),
            KeyboardButton("🌐 Current Affairs"),
            KeyboardButton("🎁 Tiered Rewards"),
            KeyboardButton("🌍 African Countries"),
            KeyboardButton("🛒 Marketplace")
        ]
        
        if is_admin:
            game_buttons.append(KeyboardButton("🔧 Admin"))
            
        markup.add(*game_buttons)
        return markup
        
    def create_language_menu(self):
        """Create language selection menu"""
        markup = ReplyKeyboardMarkup(resize_keyboard=True)
        from user_preference_service import user_preference_service
        
        for lang_code, info in user_preference_service.supported_languages.items():
            markup.add(KeyboardButton(f"{info['flag']} {info['name']}"))
        return markup
        
    def create_zone_menu(self):
        """Create zone selection menu"""
        markup = ReplyKeyboardMarkup(resize_keyboard=True)
        from user_preference_service import user_preference_service
        
        for zone, info in user_preference_service.african_zones.items():
            markup.add(KeyboardButton(f"{info['flag']} {zone}"))
        return markup
        
    def create_tier_menu(self):
        """Create tier-based reward menu"""
        markup = InlineKeyboardMarkup(row_width=2)
        
        tiers = [
            ("🥉 Bronze", "bronze", "0-1000 points"),
            ("🥈 Silver", "silver", "1001-5000 points"),
            ("🥇 Gold", "gold", "5001-10000 points"),
            ("💎 Platinum", "platinum", "10000+ points")
        ]
        
        for tier_name, tier_id, description in tiers:
            markup.add(
                InlineKeyboardButton(
                    f"{tier_name} {description}",
                    callback_data=f"tier:{tier_id}"
                )
            )
        return markup
        
        
    def create_notification_button(self, text, callback_data, emoji="🔔"):
        """Create notification button"""
        return InlineKeyboardButton(f"{emoji} {text}", callback_data=callback_data)
        
    def create_return_button(self):
        """Create return to main menu button"""
        return InlineKeyboardButton("🏠 Return to Main Menu", callback_data="return_main")
        
    def create_crypto_payment_menu(self):
        """Create crypto payment menu"""
        markup = InlineKeyboardMarkup(row_width=1)

        crypto_options = [
            ("Bitcoin (BTC)", "btc"),
            ("Ethereum (ETH)", "eth"),
            ("USDT (TRC20)", "usdt_trc20"),
            ("USDT (ERC20)", "usdt_erc20"),
            ("BNB (BSC)", "bnb"),
            ("Solana (SOL)", "sol")
        ]

        for name, crypto in crypto_options:
            markup.add(
                InlineKeyboardButton(
                    f"💎 {name}",
                    callback_data=f"crypto:{crypto}"
                )
            )
        return markup

