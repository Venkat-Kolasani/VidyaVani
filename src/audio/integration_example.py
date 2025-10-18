"""
Integration example showing how to use the audio processing pipeline
in the VidyaVani IVR system
"""

import logging
from typing import Optional

from .audio_processor import AudioProcessor, Language, AudioProcessingResult
from .language_detector import LanguageDetector
from .audio_utils import AudioQualityChecker

logger = logging.getLogger(__name__)


class IVRAudioHandler:
    """
    High-level audio handler for IVR integration
    Combines all audio processing components for easy use
    """
    
    def __init__(self, config):
        """Initialize IVR audio handler"""
        self.config = config
        self.audio_processor = AudioProcessor(config)
        self.language_detector = LanguageDetector(self.audio_processor.stt_client)
        self.quality_checker = AudioQualityChecker()
        
        logger.info("IVR Audio Handler initialized successfully")

    def process_student_question(self, audio_data: bytes, preferred_language: Optional[str] = None) -> dict:
        """
        Complete pipeline to process student question from IVR
        
        Args:
            audio_data: Raw audio from Exotel recording
            preferred_language: User's preferred language ('english' or 'telugu')
            
        Returns:
            Dictionary with processing results
        """
        try:
            # Convert string language to enum
            target_language = None
            if preferred_language:
                if preferred_language.lower() == 'english':
                    target_language = Language.ENGLISH
                elif preferred_language.lower() == 'telugu':
                    target_language = Language.TELUGU
            
            # Check audio quality first
            if not self.quality_checker.is_suitable_for_ivr(audio_data):
                logger.warning("Audio quality not suitable for processing")
                return {
                    'success': False,
                    'error_type': 'poor_quality',
                    'message': self.audio_processor.get_fallback_message(
                        'noise_error', 
                        target_language or Language.ENGLISH
                    )
                }
            
            # Process the question
            result = self.audio_processor.process_question_audio(audio_data, target_language)
            
            if result.success:
                return {
                    'success': True,
                    'question_text': result.content,
                    'confidence': result.confidence,
                    'detected_language': result.detected_language,
                    'language_enum': target_language or Language.ENGLISH
                }
            else:
                return {
                    'success': False,
                    'error_type': 'processing_failed',
                    'message': result.error_message
                }
                
        except Exception as e:
            logger.error(f"Student question processing failed: {e}")
            return {
                'success': False,
                'error_type': 'system_error',
                'message': self.audio_processor.get_fallback_message(
                    'processing_error',
                    target_language or Language.ENGLISH
                )
            }

    def generate_response_audio(self, response_text: str, language: str) -> dict:
        """
        Generate audio response for IVR delivery
        
        Args:
            response_text: AI-generated response text
            language: Target language ('english' or 'telugu')
            
        Returns:
            Dictionary with audio generation results
        """
        try:
            # Convert string to enum
            if language.lower() == 'english':
                target_language = Language.ENGLISH
            elif language.lower() == 'telugu':
                target_language = Language.TELUGU
            else:
                target_language = Language.ENGLISH  # Default
            
            # Generate audio response
            result = self.audio_processor.generate_response_audio(response_text, target_language)
            
            if result.success:
                return {
                    'success': True,
                    'audio_data': result.audio_data,
                    'language': language
                }
            else:
                return {
                    'success': False,
                    'error_message': result.error_message
                }
                
        except Exception as e:
            logger.error(f"Response audio generation failed: {e}")
            return {
                'success': False,
                'error_message': f"Failed to generate audio response: {str(e)}"
            }

    def get_language_selection_audio(self, language: str) -> dict:
        """
        Generate audio for language selection menu
        
        Args:
            language: Target language for menu
            
        Returns:
            Dictionary with menu audio data
        """
        try:
            if language.lower() == 'english':
                menu_text = "Welcome to VidyaVani. Press 1 for English or 2 for Telugu."
                target_language = Language.ENGLISH
            else:
                menu_text = "విద్యావాణికి స్వాగతం. ఇంగ్లీష్ కోసం 1 లేదా తెలుగు కోసం 2 నొక్కండి."
                target_language = Language.TELUGU
            
            result = self.audio_processor.text_to_speech(menu_text, target_language)
            
            if result.success:
                return {
                    'success': True,
                    'audio_data': result.audio_data,
                    'menu_text': menu_text
                }
            else:
                return {
                    'success': False,
                    'error_message': result.error_message
                }
                
        except Exception as e:
            logger.error(f"Menu audio generation failed: {e}")
            return {
                'success': False,
                'error_message': f"Failed to generate menu audio: {str(e)}"
            }

    def get_error_response_audio(self, error_type: str, language: str) -> dict:
        """
        Generate audio for error responses
        
        Args:
            error_type: Type of error (noise_error, unclear_speech, processing_error)
            language: Target language
            
        Returns:
            Dictionary with error audio data
        """
        try:
            # Convert string to enum
            if language.lower() == 'english':
                target_language = Language.ENGLISH
            elif language.lower() == 'telugu':
                target_language = Language.TELUGU
            else:
                target_language = Language.ENGLISH
            
            # Get error message
            error_message = self.audio_processor.get_fallback_message(error_type, target_language)
            
            # Generate audio
            result = self.audio_processor.text_to_speech(error_message, target_language)
            
            if result.success:
                return {
                    'success': True,
                    'audio_data': result.audio_data,
                    'error_message': error_message
                }
            else:
                return {
                    'success': False,
                    'error_message': f"Failed to generate error audio: {result.error_message}"
                }
                
        except Exception as e:
            logger.error(f"Error audio generation failed: {e}")
            return {
                'success': False,
                'error_message': f"Failed to generate error audio: {str(e)}"
            }


# Example usage for Flask integration
def create_audio_handler(config):
    """Factory function to create audio handler"""
    return IVRAudioHandler(config)


# Example Flask route integration (pseudo-code)
"""
from flask import Flask, request, jsonify
from src.audio.integration_example import create_audio_handler
from config import Config

app = Flask(__name__)
config = Config()
audio_handler = create_audio_handler(config)

@app.route('/webhook/process-question', methods=['POST'])
def process_question():
    try:
        # Get audio data from Exotel webhook
        audio_url = request.form.get('RecordingUrl')
        language = request.form.get('Language', 'english')
        
        # Download audio data (implementation needed)
        audio_data = download_audio_from_url(audio_url)
        
        # Process question
        result = audio_handler.process_student_question(audio_data, language)
        
        if result['success']:
            # Continue with RAG processing...
            return jsonify({
                'status': 'success',
                'question': result['question_text'],
                'confidence': result['confidence']
            })
        else:
            # Return error audio
            error_audio = audio_handler.get_error_response_audio(
                result['error_type'], 
                language
            )
            return jsonify({
                'status': 'error',
                'message': result['message'],
                'audio_data': error_audio.get('audio_data')
            })
            
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/webhook/generate-response', methods=['POST'])
def generate_response():
    try:
        response_text = request.json.get('response_text')
        language = request.json.get('language', 'english')
        
        # Generate audio response
        result = audio_handler.generate_response_audio(response_text, language)
        
        if result['success']:
            return jsonify({
                'status': 'success',
                'audio_data': result['audio_data']
            })
        else:
            return jsonify({
                'status': 'error',
                'message': result['error_message']
            }), 500
            
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
"""