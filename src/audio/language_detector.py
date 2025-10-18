"""
Language detection and accent handling for Indian dialects
"""

import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from google.cloud import speech
from google.api_core import exceptions as google_exceptions

from .language_types import Language


@dataclass
class LanguageDetectionResult:
    """Result of language detection operation"""
    detected_language: Language
    confidence: float
    alternative_languages: List[Tuple[Language, float]]
    accent_info: Optional[str] = None


class AccentType(Enum):
    """Common Indian accent types for better recognition"""
    STANDARD_INDIAN = "standard_indian"
    SOUTH_INDIAN = "south_indian"
    NORTH_INDIAN = "north_indian"
    TELUGU_NATIVE = "telugu_native"
    ENGLISH_NATIVE = "english_native"


class LanguageDetector:
    """
    Advanced language detection with Indian accent handling
    """
    
    def __init__(self, stt_client: speech.SpeechClient):
        """Initialize language detector with STT client"""
        self.stt_client = stt_client
        self.logger = logging.getLogger(__name__)
        
        # Language detection configurations
        self.detection_configs = {
            Language.ENGLISH: [
                speech.RecognitionConfig(
                    encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
                    sample_rate_hertz=16000,
                    language_code="en-IN",
                    alternative_language_codes=["en-US", "en-GB"],
                    enable_automatic_punctuation=False,
                    use_enhanced=True,
                    model="phone_call",
                ),
                speech.RecognitionConfig(
                    encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
                    sample_rate_hertz=16000,
                    language_code="en-US",
                    alternative_language_codes=["en-IN"],
                    enable_automatic_punctuation=False,
                    use_enhanced=True,
                    model="phone_call",
                )
            ],
            Language.TELUGU: [
                speech.RecognitionConfig(
                    encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
                    sample_rate_hertz=16000,
                    language_code="te-IN",
                    enable_automatic_punctuation=False,
                    use_enhanced=True,
                    model="phone_call",
                )
            ]
        }
        
        # Common English words that indicate English speech
        self.english_indicators = {
            "hello", "hi", "question", "what", "how", "why", "when", "where",
            "science", "physics", "chemistry", "biology", "explain", "tell",
            "about", "chapter", "lesson", "study", "learn", "understand"
        }
        
        # Common Telugu words that indicate Telugu speech
        self.telugu_indicators = {
            "నమస్కారం", "హలో", "ప్రశ్న", "ఏమిటి", "ఎలా", "ఎందుకు", "ఎప్పుడు", "ఎక్కడ",
            "సైన్స్", "భౌతిక", "రసాయన", "జీవ", "వివరించు", "చెప్పు",
            "గురించి", "అధ్యాయం", "పాఠం", "చదువు", "నేర్చుకో", "అర్థం"
        }

    def detect_language_advanced(self, audio_data: bytes) -> LanguageDetectionResult:
        """
        Advanced language detection with confidence scoring
        
        Args:
            audio_data: Raw audio data
            
        Returns:
            LanguageDetectionResult with detected language and confidence
        """
        try:
            audio = speech.RecognitionAudio(content=audio_data)
            results = {}
            
            # Test each language configuration
            for language, configs in self.detection_configs.items():
                best_confidence = 0.0
                best_transcript = ""
                
                for config in configs:
                    try:
                        response = self.stt_client.recognize(config=config, audio=audio)
                        
                        if response.results:
                            result = response.results[0]
                            transcript = result.alternatives[0].transcript
                            confidence = result.alternatives[0].confidence
                            
                            if confidence > best_confidence:
                                best_confidence = confidence
                                best_transcript = transcript
                                
                    except Exception as e:
                        self.logger.warning(f"Language detection failed for {language.value}: {e}")
                        continue
                
                if best_confidence > 0:
                    results[language] = (best_confidence, best_transcript)
            
            # Analyze results and apply heuristics
            return self._analyze_detection_results(results)
            
        except Exception as e:
            self.logger.error(f"Advanced language detection failed: {e}")
            return LanguageDetectionResult(
                detected_language=Language.ENGLISH,
                confidence=0.5,
                alternative_languages=[]
            )

    def _analyze_detection_results(self, results: Dict[Language, Tuple[float, str]]) -> LanguageDetectionResult:
        """
        Analyze detection results and apply linguistic heuristics
        
        Args:
            results: Dictionary of language -> (confidence, transcript) pairs
            
        Returns:
            LanguageDetectionResult with best language choice
        """
        if not results:
            return LanguageDetectionResult(
                detected_language=Language.ENGLISH,
                confidence=0.3,
                alternative_languages=[]
            )
        
        # Apply content-based heuristics
        enhanced_results = {}
        
        for language, (confidence, transcript) in results.items():
            enhanced_confidence = confidence
            
            # Boost confidence based on language-specific words
            if language == Language.ENGLISH:
                english_words = self._count_language_indicators(transcript.lower(), self.english_indicators)
                if english_words > 0:
                    enhanced_confidence = min(1.0, confidence + (english_words * 0.1))
            
            elif language == Language.TELUGU:
                telugu_words = self._count_language_indicators(transcript, self.telugu_indicators)
                if telugu_words > 0:
                    enhanced_confidence = min(1.0, confidence + (telugu_words * 0.15))
            
            enhanced_results[language] = enhanced_confidence
        
        # Sort by enhanced confidence
        sorted_results = sorted(enhanced_results.items(), key=lambda x: x[1], reverse=True)
        
        # Get best language
        best_language, best_confidence = sorted_results[0]
        
        # Create alternative languages list
        alternatives = [(lang, conf) for lang, conf in sorted_results[1:]]
        
        # Detect accent type
        accent_info = self._detect_accent_type(best_language, results.get(best_language, (0, ""))[1])
        
        return LanguageDetectionResult(
            detected_language=best_language,
            confidence=best_confidence,
            alternative_languages=alternatives,
            accent_info=accent_info
        )

    def _count_language_indicators(self, text: str, indicators: set) -> int:
        """Count language-specific indicator words in text"""
        words = text.split()
        count = 0
        
        for word in words:
            # Remove punctuation for matching
            clean_word = word.strip(".,!?;:")
            if clean_word in indicators:
                count += 1
        
        return count

    def _detect_accent_type(self, language: Language, transcript: str) -> str:
        """
        Detect accent type based on language and transcript characteristics
        
        Args:
            language: Detected language
            transcript: Transcribed text
            
        Returns:
            Accent type description
        """
        try:
            if language == Language.ENGLISH:
                # Simple heuristics for English accent detection
                if any(word in transcript.lower() for word in ["sir", "madam", "kindly", "please"]):
                    return AccentType.STANDARD_INDIAN.value
                else:
                    return AccentType.STANDARD_INDIAN.value  # Default for Indian context
            
            elif language == Language.TELUGU:
                return AccentType.TELUGU_NATIVE.value
            
            return "unknown"
            
        except Exception as e:
            self.logger.error(f"Accent detection failed: {e}")
            return "unknown"

    def quick_language_detection(self, audio_data: bytes) -> Language:
        """
        Quick language detection for real-time processing
        
        Args:
            audio_data: Raw audio data
            
        Returns:
            Detected Language enum
        """
        try:
            # Use simpler detection for speed
            audio = speech.RecognitionAudio(content=audio_data)
            
            # Try English first (more common in educational context)
            english_config = self.detection_configs[Language.ENGLISH][0]
            
            try:
                response = self.stt_client.recognize(config=english_config, audio=audio)
                if response.results and response.results[0].alternatives[0].confidence > 0.6:
                    return Language.ENGLISH
            except:
                pass
            
            # Try Telugu
            telugu_config = self.detection_configs[Language.TELUGU][0]
            
            try:
                response = self.stt_client.recognize(config=telugu_config, audio=audio)
                if response.results and response.results[0].alternatives[0].confidence > 0.6:
                    return Language.TELUGU
            except:
                pass
            
            # Default to English
            return Language.ENGLISH
            
        except Exception as e:
            self.logger.error(f"Quick language detection failed: {e}")
            return Language.ENGLISH

    def validate_language_choice(self, audio_data: bytes, expected_language: Language) -> bool:
        """
        Validate if audio matches expected language
        
        Args:
            audio_data: Raw audio data
            expected_language: Expected language
            
        Returns:
            True if audio matches expected language
        """
        try:
            detected = self.quick_language_detection(audio_data)
            return detected == expected_language
            
        except Exception as e:
            self.logger.error(f"Language validation failed: {e}")
            return True  # Assume valid if detection fails


class AccentHandler:
    """Handle different Indian accents for better recognition"""
    
    def __init__(self):
        """Initialize accent handler"""
        self.logger = logging.getLogger(__name__)
        
        # Accent-specific recognition tips
        self.accent_configs = {
            AccentType.SOUTH_INDIAN: {
                "boost_words": ["very", "good", "nice", "what", "how"],
                "common_substitutions": {
                    "v": "w",  # "very" -> "wery"
                    "th": "d",  # "the" -> "de"
                }
            },
            AccentType.TELUGU_NATIVE: {
                "boost_words": ["physics", "chemistry", "biology", "science"],
                "common_substitutions": {}
            }
        }

    def enhance_recognition_for_accent(self, transcript: str, accent_type: str) -> str:
        """
        Enhance transcript based on detected accent patterns
        
        Args:
            transcript: Original transcript
            accent_type: Detected accent type
            
        Returns:
            Enhanced transcript with accent corrections
        """
        try:
            enhanced = transcript
            
            # Apply accent-specific enhancements
            if accent_type in [AccentType.SOUTH_INDIAN.value, AccentType.STANDARD_INDIAN.value]:
                # Common Indian English patterns
                enhanced = enhanced.replace(" wery ", " very ")
                enhanced = enhanced.replace(" wat ", " what ")
                enhanced = enhanced.replace(" wen ", " when ")
                enhanced = enhanced.replace(" were ", " where ")
            
            return enhanced
            
        except Exception as e:
            self.logger.error(f"Accent enhancement failed: {e}")
            return transcript

    def get_accent_specific_tips(self, accent_type: str) -> List[str]:
        """
        Get tips for handling specific accent types
        
        Args:
            accent_type: Accent type identifier
            
        Returns:
            List of handling tips
        """
        tips = {
            AccentType.SOUTH_INDIAN.value: [
                "Expect 'v' and 'w' sound confusion",
                "Listen for retroflex consonants",
                "Account for different 'th' pronunciation"
            ],
            AccentType.TELUGU_NATIVE.value: [
                "Expect Telugu phonetic influence",
                "Listen for aspirated consonants",
                "Account for vowel length differences"
            ],
            AccentType.STANDARD_INDIAN.value: [
                "Standard Indian English patterns",
                "Clear consonant pronunciation",
                "Formal speech patterns"
            ]
        }
        
        return tips.get(accent_type, ["Standard processing"])