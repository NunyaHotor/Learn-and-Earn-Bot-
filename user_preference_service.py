import logging
from typing import Dict, Optional
from ui_enhancer import ui_enhancer

logger = logging.getLogger(__name__)

# Admin check function
def is_admin(chat_id: int) -> bool:
    """Check if user is an admin"""
    import os
    admin_chat_ids_str = os.getenv("ADMIN_CHAT_IDS", "")
    admin_chat_ids = [int(cid.strip()) for cid in admin_chat_ids_str.split(",") if cid.strip().isdigit()]
    return chat_id in admin_chat_ids

class UserPreferenceService:
    def __init__(self):
        self.supported_languages = {
            'en': {'name': 'English', 'flag': '🇺🇸'},
            'fr': {'name': 'French', 'flag': '🇫🇷'},
            'sw': {'name': 'Swahili', 'flag': '🇰🇪'},
            'ar': {'name': 'Arabic', 'flag': '🇸🇦'},
            'pt': {'name': 'Portuguese', 'flag': '🇵🇹'},
            'es': {'name': 'Spanish', 'flag': '🇪🇸'},
            'de': {'name': 'German', 'flag': '🇩🇪'},
            'it': {'name': 'Italian', 'flag': '🇮🇹'},
            'zh': {'name': 'Chinese', 'flag': '🇨🇳'},
            'ja': {'name': 'Japanese', 'flag': '🇯🇵'},
            'ko': {'name': 'Korean', 'flag': '🇰🇷'},
            'ru': {'name': 'Russian', 'flag': '🇷🇺'},
            'hi': {'name': 'Hindi', 'flag': '🇮🇳'},
            'nl': {'name': 'Dutch', 'flag': '🇳🇱'},
            'tr': {'name': 'Turkish', 'flag': '🇹🇷'},
            'vi': {'name': 'Vietnamese', 'flag': '🇻🇳'},
            'th': {'name': 'Thai', 'flag': '🇹🇭'},
            'id': {'name': 'Indonesian', 'flag': '🇮🇩'},
            'ms': {'name': 'Malay', 'flag': '🇲🇾'},
            'tl': {'name': 'Filipino', 'flag': '🇵🇭'}
        }
        
        self.african_zones = {
            'West Africa': {
                'countries': ['Ghana', 'Nigeria', 'Senegal', 'Ivory Coast', 'Liberia', 'Sierra Leone', 'Guinea', 'Guinea-Bissau', 'Gambia', 'Cape Verde', 'Mali', 'Burkina Faso', 'Togo', 'Benin'],
                'flag': '🌍',
                'description': 'Rich in gold, cocoa, and vibrant cultures'
            },
            'East Africa': {
                'countries': ['Kenya', 'Tanzania', 'Uganda', 'Ethiopia', 'Rwanda', 'Burundi', 'South Sudan', 'Djibouti', 'Eritrea', 'Somalia', 'Madagascar', 'Comoros', 'Seychelles', 'Mauritius'],
                'flag': '🌍',
                'description': 'Home to the Great Rift Valley and coffee'
            },
            'North Africa': {
                'countries': ['Egypt', 'Libya', 'Tunisia', 'Algeria', 'Morocco', 'Sudan', 'South Sudan'],
                'flag': '🌍',
                'description': 'Ancient civilizations and Sahara Desert'
            },
            'Central Africa': {
                'countries': ['Cameroon', 'Chad', 'Central African Republic', 'Equatorial Guinea', 'Gabon', 'Congo', 'DR Congo', 'São Tomé and Príncipe'],
                'flag': '🌍',
                'description': 'Rich in minerals and rainforests'
            },
            'Southern Africa': {
                'countries': ['South Africa', 'Zimbabwe', 'Zambia', 'Botswana', 'Namibia', 'Angola', 'Mozambique', 'Malawi', 'Lesotho', 'Swaziland', 'Madagascar'],
                'flag': '🌍',
                'description': 'Diamond mines and diverse wildlife'
            }
        }
        
    def get_language_choices(self):
        """Get available language choices"""
        return self.supported_languages
        
    def get_zone_choices(self):
        """Get available zone choices"""
        return self.african_zones
        
    def validate_language(self, lang_code):
        """Validate language code"""
        return lang_code in self.supported_languages
        
    def validate_zone(self, zone):
        """Validate zone"""
        return zone in self.african_zones
        
    def get_zone_info(self, zone):
        """Get detailed zone information"""
        return self.african_zones.get(zone, {})

user_preference_service = UserPreferenceService()
