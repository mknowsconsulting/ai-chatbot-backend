"""
Language Detection Service
Automatically detect language (Indonesian/English) from user message
"""

from langdetect import detect, LangDetectException
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class LanguageDetector:
    """
    Detect language from text
    Supported: Indonesian (id), English (en)
    """
    
    def __init__(self):
        self.default_language = "id"  # Default to Indonesian
        self.supported_languages = ["id", "en"]
    
    def detect_language(self, text: str) -> str:
        """
        Detect language from text
        
        Args:
            text: Input text
            
        Returns:
            Language code ('id' or 'en')
            
        Example:
            lang = detector.detect_language("Berapa biaya kuliah?")
            # Returns: 'id'
            
            lang = detector.detect_language("How much is tuition?")
            # Returns: 'en'
        """
        
        # Handle empty or very short text
        if not text or len(text.strip()) < 3:
            logger.debug(f"Text too short, using default language: {self.default_language}")
            return self.default_language
        
        try:
            # Detect language
            detected = detect(text)
            
            # Map to supported languages
            if detected == "id":
                return "id"
            elif detected == "en":
                return "en"
            else:
                # If detected language not supported, default to Indonesian
                logger.debug(f"Detected {detected}, using default: {self.default_language}")
                return self.default_language
                
        except LangDetectException as e:
            logger.warning(f"Language detection failed: {e}, using default: {self.default_language}")
            return self.default_language
        except Exception as e:
            logger.error(f"Language detection error: {e}, using default: {self.default_language}")
            return self.default_language
    
    def is_indonesian(self, text: str) -> bool:
        """Check if text is Indonesian"""
        return self.detect_language(text) == "id"
    
    def is_english(self, text: str) -> bool:
        """Check if text is English"""
        return self.detect_language(text) == "en"
    
    def detect_with_confidence(self, text: str) -> dict:
        """
        Detect language with confidence score
        
        Args:
            text: Input text
            
        Returns:
            Dictionary with language and confidence
            
        Example:
            result = detector.detect_with_confidence("Hello")
            # Returns: {'language': 'en', 'confidence': 0.95}
        """
        from langdetect import detect_langs
        
        try:
            if not text or len(text.strip()) < 3:
                return {
                    "language": self.default_language,
                    "confidence": 0.5
                }
            
            # Get probabilities
            langs = detect_langs(text)
            
            # Find ID or EN
            for lang_prob in langs:
                if lang_prob.lang in self.supported_languages:
                    return {
                        "language": lang_prob.lang,
                        "confidence": lang_prob.prob
                    }
            
            # Default
            return {
                "language": self.default_language,
                "confidence": 0.5
            }
            
        except Exception as e:
            logger.error(f"Language detection with confidence failed: {e}")
            return {
                "language": self.default_language,
                "confidence": 0.5
            }


# ============================================
# Global Language Detector Instance
# ============================================

language_detector = LanguageDetector()
