"""
Audio Processing Pipeline for VidyaVani IVR Learning System

This module handles speech-to-text and text-to-speech conversion using Google Cloud APIs
with support for English and Telugu languages, optimized for IVR platform compatibility.
"""

import logging
from typing import Optional
from dataclasses import dataclass
from enum import Enum

from google.cloud import speech
from google.cloud import texttospeech
from google.api_core import exceptions as google_exceptions

import sys
from pathlib import Path

# Add project root to path for config import
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from config import Config

# Add src to path for utils import
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.logging_config import setup_logging
from utils.performance_decorators import track_performance, track_cache_usage
from utils.error_tracker import error_tracker
from .language_detector import LanguageDetector
from .language_types import Language


_LOGGING_CONFIGURED = False


class VoiceGender(Enum):
    """Voice gender options for TTS"""
    MALE = texttospeech.SsmlVoiceGender.MALE
    FEMALE = texttospeech.SsmlVoiceGender.FEMALE
    NEUTRAL = texttospeech.SsmlVoiceGender.NEUTRAL


@dataclass
class AudioProcessingResult:
    """Result of audio processing operation"""
    success: bool
    content: Optional[str] = None
    audio_data: Optional[bytes] = None
    error_message: Optional[str] = None
    confidence: Optional[float] = None
    detected_language: Optional[str] = None


@dataclass
class TTSConfig:
    """Configuration for Text-to-Speech conversion"""
    language_code: str
    voice_name: Optional[str] = None
    gender: VoiceGender = VoiceGender.FEMALE
    speaking_rate: float = 1.0
    pitch: float = 0.0
    volume_gain_db: float = 0.0


class AudioProcessor:
    """
    Main audio processing class handling STT and TTS operations
    with multilingual support and IVR optimization
    """
    
    def __init__(self, config: Config):
        """Initialize audio processor with Google Cloud clients"""
        self.config = config

        global _LOGGING_CONFIGURED
        if not _LOGGING_CONFIGURED:
            setup_logging()
            _LOGGING_CONFIGURED = True

        self.logger = logging.getLogger(__name__)
        self.language_detector: Optional[LanguageDetector] = None
        
        # Initialize Google Cloud clients
        try:
            self.stt_client = speech.SpeechClient()
            self.tts_client = texttospeech.TextToSpeechClient()
            self.logger.info("Google Cloud audio clients initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize Google Cloud clients: {e}")
            raise

        try:
            self.language_detector = LanguageDetector(self.stt_client)
            self.logger.debug("Language detector initialized")
        except Exception as detector_error:
            self.language_detector = None
            self.logger.warning(
                "Advanced language detection unavailable, falling back to basic detection: %s",
                detector_error,
            )
        
        # Language configurations for STT
        self.stt_configs = {
            Language.ENGLISH: speech.RecognitionConfig(
                encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
                sample_rate_hertz=self.config.AUDIO_SAMPLE_RATE,
                language_code=Language.ENGLISH.value,
                enable_automatic_punctuation=True,
                use_enhanced=True,  # Enhanced model for better accuracy
                # model="phone_call",  # Not supported for en-IN, use default
            ),
            Language.TELUGU: speech.RecognitionConfig(
                encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
                sample_rate_hertz=self.config.AUDIO_SAMPLE_RATE,
                language_code=Language.TELUGU.value,
                enable_automatic_punctuation=True,
                use_enhanced=True,
                # model="phone_call",  # Not supported for te-IN, use default
            )
        }
        
        # TTS voice configurations
        self.tts_configs = {
            Language.ENGLISH: TTSConfig(
                language_code=Language.ENGLISH.value,
                voice_name="en-IN-Wavenet-A",  # Indian English female voice
                gender=VoiceGender.FEMALE,
                speaking_rate=0.9,  # Slightly slower for clarity
            ),
            Language.TELUGU: TTSConfig(
                language_code=Language.TELUGU.value,
                voice_name="te-IN-Standard-A",  # Telugu female voice
                gender=VoiceGender.FEMALE,
                speaking_rate=0.9,
            )
        }
        
        # Fallback messages for different scenarios
        self.fallback_messages = {
            "noise_error": {
                Language.ENGLISH: "I'm sorry, there was too much background noise. Could you try asking again?",
                Language.TELUGU: "క్షమించండి, చాలా నేపథ్య శబ్దం ఉంది. దయచేసి మళ్లీ ప్రయత్నించగలరా?"
            },
            "unclear_speech": {
                Language.ENGLISH: "I couldn't understand your question clearly. Please speak slowly and try again.",
                Language.TELUGU: "మీ ప్రశ్న స్పష్టంగా అర్థం కాలేదు. దయచేసి నెమ్మదిగా మాట్లాడి మళ్లీ ప్రయత్నించండి."
            },
            "processing_error": {
                Language.ENGLISH: "I'm having trouble processing your audio. Please try again.",
                Language.TELUGU: "మీ ఆడియో ప్రాసెస్ చేయడంలో సమస్య ఉంది. దయచేసి మళ్లీ ప్రయత్నించండి."
            }
        }

    @track_performance("STT_Processing", track_api_usage=True, service_name="google_stt")
    def speech_to_text(self, audio_data: bytes, language: Language = Language.ENGLISH) -> AudioProcessingResult:
        """
        Convert speech audio to text using Google Cloud Speech-to-Text API
        
        Args:
            audio_data: Raw audio data in bytes
            language: Target language for recognition
            
        Returns:
            AudioProcessingResult with transcribed text or error information
        """
        try:
            # Prepare audio for Google Cloud STT
            audio = speech.RecognitionAudio(content=audio_data)
            config = self.stt_configs[language]
            
            self.logger.info(f"Starting STT processing for {language.value}")
            
            # Perform speech recognition
            response = self.stt_client.recognize(config=config, audio=audio)
            
            if not response.results:
                self.logger.warning("No speech detected in audio")
                return AudioProcessingResult(
                    success=False,
                    error_message=self.fallback_messages["unclear_speech"][language]
                )
            
            # Get the best transcription result
            result = response.results[0]
            transcript = result.alternatives[0].transcript
            confidence = result.alternatives[0].confidence
            
            self.logger.info(f"STT successful: confidence={confidence:.2f}")
            
            # Check confidence threshold
            if confidence < 0.6:  # Low confidence threshold
                self.logger.warning(f"Low confidence transcription: {confidence:.2f}")
                return AudioProcessingResult(
                    success=False,
                    error_message=self.fallback_messages["unclear_speech"][language]
                )
            
            return AudioProcessingResult(
                success=True,
                content=transcript.strip(),
                confidence=confidence,
                detected_language=language.value
            )
            
        except google_exceptions.InvalidArgument as e:
            self.logger.error(f"Invalid audio format: {e}")
            return AudioProcessingResult(
                success=False,
                error_message=self.fallback_messages["processing_error"][language]
            )
        except google_exceptions.DeadlineExceeded as e:
            self.logger.error(f"STT timeout: {e}")
            return AudioProcessingResult(
                success=False,
                error_message=self.fallback_messages["processing_error"][language]
            )
        except Exception as e:
            self.logger.error(f"STT processing failed: {e}")
            error_tracker.track_error('Google_STT', e, recovery_action='Returned fallback error message')
            return AudioProcessingResult(
                success=False,
                error_message=self.fallback_messages["processing_error"][language]
            )

    @track_performance("TTS_Processing", track_api_usage=True, service_name="google_tts")
    def text_to_speech(self, text: str, language: Language = Language.ENGLISH) -> AudioProcessingResult:
        """
        Convert text to speech using Google Cloud Text-to-Speech API
        
        Args:
            text: Text to convert to speech
            language: Target language for synthesis
            
        Returns:
            AudioProcessingResult with audio data or error information
        """
        try:
            # Get TTS configuration for language
            tts_config = self.tts_configs[language]
            
            # Prepare synthesis input
            synthesis_input = texttospeech.SynthesisInput(text=text)
            
            # Configure voice parameters
            voice = texttospeech.VoiceSelectionParams(
                language_code=tts_config.language_code,
                name=tts_config.voice_name,
                ssml_gender=tts_config.gender.value
            )
            
            # Configure audio output optimized for IVR
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.LINEAR16,  # PCM format for IVR
                sample_rate_hertz=self.config.AUDIO_IVR_SAMPLE_RATE,
                speaking_rate=tts_config.speaking_rate,
                pitch=tts_config.pitch,
                volume_gain_db=tts_config.volume_gain_db
            )
            
            self.logger.info(f"Starting TTS processing for {language.value}")
            
            # Perform text-to-speech synthesis
            response = self.tts_client.synthesize_speech(
                input=synthesis_input,
                voice=voice,
                audio_config=audio_config
            )
            
            self.logger.info("TTS synthesis completed successfully")
            
            return AudioProcessingResult(
                success=True,
                audio_data=response.audio_content
            )
            
        except google_exceptions.InvalidArgument as e:
            self.logger.error(f"Invalid TTS parameters: {e}")
            return AudioProcessingResult(
                success=False,
                error_message=f"Text-to-speech conversion failed: {str(e)}"
            )
        except google_exceptions.DeadlineExceeded as e:
            self.logger.error(f"TTS timeout: {e}")
            return AudioProcessingResult(
                success=False,
                error_message="Text-to-speech conversion timed out"
            )
        except Exception as e:
            self.logger.error(f"TTS processing failed: {e}")
            error_tracker.track_error('Google_TTS', e, recovery_action='Returned TTS error response')
            return AudioProcessingResult(
                success=False,
                error_message=f"Text-to-speech conversion failed: {str(e)}"
            )

    @track_performance("Language_Detection")
    def detect_language(self, audio_data: bytes) -> Language:
        """
        Detect language from audio data by trying both supported languages
        
        Args:
            audio_data: Raw audio data in bytes
            
        Returns:
            Detected Language enum value
        """
        try:
            if self.language_detector:
                try:
                    detection = self.language_detector.detect_language_advanced(audio_data)
                except Exception as detection_error:
                    self.logger.warning(
                        "Advanced language detection failed, using fallback: %s",
                        detection_error,
                    )
                else:
                    self.logger.info(
                        "Language detection result: %s (confidence %.2f)",
                        detection.detected_language.value,
                        detection.confidence,
                    )
                    if detection.accent_info:
                        self.logger.debug("Detected accent: %s", detection.accent_info)

                    if detection.confidence < 0.5 and detection.alternative_languages:
                        alt_language, alt_confidence = detection.alternative_languages[0]
                        self.logger.info(
                            "Using alternative language %s (confidence %.2f)",
                            alt_language.value,
                            alt_confidence,
                        )
                        return alt_language

                    return detection.detected_language

            # Fallback to basic detection if detector unavailable or failed
            english_result = self.speech_to_text(audio_data, Language.ENGLISH)
            if english_result.success and english_result.confidence and english_result.confidence > 0.7:
                return Language.ENGLISH

            telugu_result = self.speech_to_text(audio_data, Language.TELUGU)
            if telugu_result.success and telugu_result.confidence and telugu_result.confidence > 0.7:
                return Language.TELUGU

            self.logger.warning("Language detection inconclusive, defaulting to English")
            return Language.ENGLISH

        except Exception as e:
            self.logger.error(f"Language detection failed: {e}")
            return Language.ENGLISH

    def optimize_audio_for_ivr(self, audio_data: bytes) -> bytes:
        """
        Optimize audio data for IVR platform compatibility
        
        Args:
            audio_data: Raw audio data
            
        Returns:
            Optimized audio data for IVR platforms
        """
        try:
            # For now, return the audio as-is since Google Cloud TTS
            # already provides optimized output for telephony
            # Future enhancement: Add codec conversion (PCMU/PCMA) if needed
            
            self.logger.info("Audio optimization completed")
            return audio_data
            
        except Exception as e:
            self.logger.error(f"Audio optimization failed: {e}")
            return audio_data

    def get_fallback_message(self, error_type: str, language: Language) -> str:
        """
        Get appropriate fallback message for error scenarios
        
        Args:
            error_type: Type of error (noise_error, unclear_speech, processing_error)
            language: Target language for message
            
        Returns:
            Localized error message
        """
        return self.fallback_messages.get(error_type, {}).get(
            language, 
            self.fallback_messages["processing_error"][Language.ENGLISH]
        )

    def process_question_audio(self, audio_data: bytes, preferred_language: Optional[Language] = None) -> AudioProcessingResult:
        """
        Complete pipeline to process question audio with language detection and fallbacks
        
        Args:
            audio_data: Raw audio data from IVR
            preferred_language: User's preferred language if known
            
        Returns:
            AudioProcessingResult with transcribed question text
        """
        try:
            # Use preferred language or detect from audio
            if preferred_language:
                target_language = preferred_language
            else:
                target_language = self.detect_language(audio_data)
            
            # Process speech to text
            result = self.speech_to_text(audio_data, target_language)
            
            if result.success:
                self.logger.info(f"Question processed successfully in {target_language.value}")
                return result
            else:
                # Try alternative language if detection was used
                if not preferred_language:
                    alt_language = Language.TELUGU if target_language == Language.ENGLISH else Language.ENGLISH
                    alt_result = self.speech_to_text(audio_data, alt_language)
                    
                    if alt_result.success and alt_result.confidence > 0.6:
                        self.logger.info(f"Question processed with alternative language {alt_language.value}")
                        return alt_result
                
                return result
                
        except Exception as e:
            self.logger.error(f"Question audio processing failed: {e}")
            return AudioProcessingResult(
                success=False,
                error_message=self.get_fallback_message("processing_error", Language.ENGLISH)
            )

    def generate_response_audio(self, response_text: str, language: Language) -> AudioProcessingResult:
        """
        Generate audio response optimized for IVR delivery
        
        Args:
            response_text: Text response to convert to speech
            language: Target language for synthesis
            
        Returns:
            AudioProcessingResult with optimized audio data
        """
        try:
            # Convert text to speech
            tts_result = self.text_to_speech(response_text, language)
            
            if tts_result.success:
                # Optimize audio for IVR platform
                optimized_audio = self.optimize_audio_for_ivr(tts_result.audio_data)
                
                return AudioProcessingResult(
                    success=True,
                    audio_data=optimized_audio
                )
            else:
                return tts_result
                
        except Exception as e:
            self.logger.error(f"Response audio generation failed: {e}")
            return AudioProcessingResult(
                success=False,
                error_message=f"Failed to generate audio response: {str(e)}"
            )