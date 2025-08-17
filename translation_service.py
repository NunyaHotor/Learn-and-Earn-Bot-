import logging
from googletrans import Translator

logger = logging.getLogger(__name__)

class TranslationService:
    def __init__(self):
        self.translator = Translator()

    def translate_text(self, text, lang_code):
        try:
            return self.translator.translate(text, dest=lang_code).text
        except Exception as e:
            logger.error(f"Translation error: {e}")
            return text

translation_service = TranslationService()
