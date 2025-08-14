import logging
from googletrans import Translator
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class TranslationService:
    def __init__(self):
        self.translator = Translator()
        self.supported_languages = {
            'en': 'English',
            'fr': 'French',
            'sw': 'Swahili',
            'ar': 'Arabic',
            'pt': 'Portuguese',
            'es': 'Spanish',
            'de': 'German',
            'it': 'Italian',
            'zh': 'Chinese',
            'ja': 'Japanese',
            'ko': 'Korean',
            'ru': 'Russian',
            'hi': 'Hindi',
            'nl': 'Dutch',
            'tr': 'Turkish',
            'vi': 'Vietnamese',
            'th': 'Thai',
            'id': 'Indonesian',
            'ms': 'Malay',
            'tl': 'Filipino'
        }
        
    def translate_text(self, text: str, target_lang: str) -> str:
        """Translate text to target language"""
        try:
            if target_lang not in self.supported_languages:
                return text
            result = self.translator.translate(text, dest=target_lang)
            return result.text
        except Exception as e:
            logger.error(f"Translation error: {e}")
            return text
            
    def detect_language(self, text: str) -> str:
        """Detect the language of the text"""
        try:
            result = self.translator.detect(text)
            return result.lang
        except Exception as e:
            logger.error(f"Language detection error: {e}")
            return 'en'
            
    def get_supported_languages(self) -> Dict[str, str]:
        """Get all supported languages"""
        return self.supported_languages

translation_service = TranslationService()
