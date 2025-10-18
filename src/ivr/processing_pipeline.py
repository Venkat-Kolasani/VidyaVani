"""
IVR Processing Pipeline for VidyaVani
Integrates STT → RAG → TTS pipeline for question processing
"""

import logging
import asyncio
import requests
from typing import Optional, Dict, Any
from dataclasses import dataclass
import tempfile
import os

from src.audio.audio_processor import AudioProcessor, Language
from src.rag.context_builder import ContextBuilder
from src.rag.response_generator import ResponseGenerator
from src.session.session_manager import ResponseData
from config import Config

logger = logging.getLogger(__name__)

@dataclass
class ProcessingResult:
    """Result of the complete processing pipeline"""
    success: bool
    question_text: str = ""
    response_text: str = ""
    response_audio_url: str = ""
    detailed_response_text: str = ""
    detailed_audio_url: str = ""
    error_message: str = ""
    processing_time: float = 0.0

class IVRProcessingPipeline:
    """Complete processing pipeline for IVR questions"""
    
    def __init__(self, config: Config):
        self.config = config
        self.audio_processor = AudioProcessor(config)
        self.context_builder = ContextBuilder(config)
        self.response_generator = ResponseGenerator(config)
        
        # Create temp directory for audio files
        self.temp_dir = tempfile.mkdtemp(prefix="vidyavani_audio_")
        logger.info(f"Processing pipeline initialized with temp dir: {self.temp_dir}")
    
    def _language_str_to_enum(self, language_str: str) -> Language:
        """Convert language string to Language enum"""
        if language_str.lower() == 'telugu':
            return Language.TELUGU
        return Language.ENGLISH
    
    def _download_audio_from_url(self, audio_url: str) -> Optional[bytes]:
        """Download audio data from URL with better error handling"""
        try:
            logger.info(f"Downloading audio from: {audio_url}")
            
            # Check if it's a placeholder/example URL
            if 'example.com' in audio_url or 'placeholder' in audio_url.lower():
                logger.warning(f"Placeholder URL detected: {audio_url}")
                # Return demo audio data for testing
                return self._get_demo_audio_data()
            
            response = requests.get(audio_url, timeout=30)
            response.raise_for_status()
            
            # Validate content type
            content_type = response.headers.get('content-type', '')
            if not any(audio_type in content_type.lower() for audio_type in ['audio', 'wav', 'mp3', 'ogg']):
                logger.warning(f"Unexpected content type: {content_type}")
            
            logger.info(f"Downloaded {len(response.content)} bytes of audio data")
            return response.content
            
        except requests.exceptions.Timeout:
            logger.error(f"Timeout downloading audio from {audio_url}")
            return self._get_demo_audio_data()
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed for {audio_url}: {e}")
            return self._get_demo_audio_data()
        except Exception as e:
            logger.error(f"Unexpected error downloading audio from {audio_url}: {e}")
            return None
    
    def _get_demo_audio_data(self) -> bytes:
        """
        Generate demo audio data for testing when real recording is not available
        Returns a small WAV file with silence
        """
        try:
            # Generate 2 seconds of silence in WAV format (16-bit, 16kHz, mono)
            sample_rate = 16000
            duration = 2.0
            num_samples = int(sample_rate * duration)
            
            # WAV header for 16-bit mono audio
            wav_header = bytearray([
                0x52, 0x49, 0x46, 0x46,  # "RIFF"
                0x00, 0x00, 0x00, 0x00,  # File size (will be filled)
                0x57, 0x41, 0x56, 0x45,  # "WAVE"
                0x66, 0x6D, 0x74, 0x20,  # "fmt "
                0x10, 0x00, 0x00, 0x00,  # Subchunk1Size (16)
                0x01, 0x00,              # AudioFormat (PCM)
                0x01, 0x00,              # NumChannels (1)
                0x80, 0x3E, 0x00, 0x00,  # SampleRate (16000)
                0x00, 0x7D, 0x00, 0x00,  # ByteRate (32000)
                0x02, 0x00,              # BlockAlign (2)
                0x10, 0x00,              # BitsPerSample (16)
                0x64, 0x61, 0x74, 0x61,  # "data"
                0x00, 0x00, 0x00, 0x00   # Subchunk2Size (will be filled)
            ])
            
            # Generate silence (zeros)
            audio_data = bytearray(num_samples * 2)  # 2 bytes per sample (16-bit)
            
            # Fill in sizes
            data_size = len(audio_data)
            file_size = len(wav_header) + data_size - 8
            
            # Update header with correct sizes
            wav_header[4:8] = file_size.to_bytes(4, 'little')
            wav_header[40:44] = data_size.to_bytes(4, 'little')
            
            demo_wav = bytes(wav_header + audio_data)
            logger.info(f"Generated demo audio data: {len(demo_wav)} bytes")
            return demo_wav
            
        except Exception as e:
            logger.error(f"Failed to generate demo audio data: {e}")
            return b''  # Return empty bytes as last resort
    
    def _save_audio_to_temp_file(self, audio_data: bytes, prefix: str = "audio") -> str:
        """Save audio data to temporary file and return file path"""
        try:
            temp_file = tempfile.NamedTemporaryFile(
                delete=False, 
                suffix=".wav", 
                prefix=f"{prefix}_",
                dir=self.temp_dir
            )
            
            temp_file.write(audio_data)
            temp_file.close()
            
            logger.info(f"Saved audio to temp file: {temp_file.name}")
            return temp_file.name
            
        except Exception as e:
            logger.error(f"Failed to save audio to temp file: {e}")
            return ""
    
    def _upload_audio_for_ivr(self, audio_data: bytes, filename: str) -> str:
        """
        Upload audio data and return URL for IVR playback
        Uses the audio storage service for real file serving
        """
        try:
            from src.storage.audio_storage import audio_storage
            
            # Store audio and get public URL
            public_url = audio_storage.store_audio(audio_data, filename)
            
            if public_url:
                logger.info(f"Audio uploaded successfully: {public_url}")
                return public_url
            else:
                logger.error("Failed to upload audio to storage service")
                return ""
            
        except Exception as e:
            logger.error(f"Failed to upload audio: {e}")
            return ""
    
    async def process_question_async(self, recording_url: str, language: str, phone_number: str) -> ProcessingResult:
        """
        Asynchronously process question through complete pipeline
        
        Args:
            recording_url: URL of the recorded question
            language: User's language preference
            phone_number: Phone number for session tracking
            
        Returns:
            ProcessingResult with generated response
        """
        import time
        start_time = time.time()
        
        try:
            logger.info(f"Starting async processing for {phone_number}")
            
            # Step 1: Download audio from recording URL
            audio_data = self._download_audio_from_url(recording_url)
            if not audio_data:
                return ProcessingResult(
                    success=False,
                    error_message="Failed to download audio recording"
                )
            
            # Step 2: Convert speech to text
            language_enum = self._language_str_to_enum(language)
            stt_result = self.audio_processor.process_question_audio(audio_data, language_enum)
            
            if not stt_result.success:
                return ProcessingResult(
                    success=False,
                    error_message=stt_result.error_message or "Failed to process audio"
                )
            
            question_text = stt_result.content
            logger.info(f"STT successful: '{question_text}'")
            
            # Step 3: Build context using RAG
            context = self.context_builder.build_context(
                question=question_text,
                language=language,
                detail_level="simple"
            )
            
            # Step 4: Generate simple response
            response_result = self.response_generator.generate_response(context)
            
            if not response_result['success']:
                return ProcessingResult(
                    success=False,
                    question_text=question_text,
                    error_message="Failed to generate response"
                )
            
            response_text = response_result['response_text']
            logger.info(f"Response generated: {len(response_text)} characters")
            
            # Step 5: Generate detailed response for option 1
            detailed_context = self.context_builder.build_context(
                question=question_text,
                language=language,
                detail_level="detailed"
            )
            
            detailed_result = self.response_generator.generate_response(detailed_context)
            detailed_response_text = detailed_result['response_text'] if detailed_result['success'] else response_text
            
            # Step 6: Convert responses to speech
            response_audio_result = self.audio_processor.generate_response_audio(response_text, language_enum)
            detailed_audio_result = self.audio_processor.generate_response_audio(detailed_response_text, language_enum)
            
            if not response_audio_result.success:
                return ProcessingResult(
                    success=False,
                    question_text=question_text,
                    response_text=response_text,
                    error_message="Failed to generate response audio"
                )
            
            # Step 7: Upload audio files for IVR access
            response_audio_url = self._upload_audio_for_ivr(
                response_audio_result.audio_data, 
                f"response_{phone_number}_{int(start_time)}"
            )
            
            detailed_audio_url = ""
            if detailed_audio_result.success:
                detailed_audio_url = self._upload_audio_for_ivr(
                    detailed_audio_result.audio_data,
                    f"detailed_{phone_number}_{int(start_time)}"
                )
            
            processing_time = time.time() - start_time
            
            logger.info(f"Processing completed in {processing_time:.2f}s for {phone_number}")
            
            return ProcessingResult(
                success=True,
                question_text=question_text,
                response_text=response_text,
                response_audio_url=response_audio_url,
                detailed_response_text=detailed_response_text,
                detailed_audio_url=detailed_audio_url,
                processing_time=processing_time
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"Processing pipeline failed after {processing_time:.2f}s: {e}")
            
            return ProcessingResult(
                success=False,
                error_message=f"Processing failed: {str(e)}",
                processing_time=processing_time
            )
    
    def process_question_sync(self, recording_url: str, language: str, phone_number: str) -> ProcessingResult:
        """
        Synchronously process question (wrapper for async method)
        
        Args:
            recording_url: URL of the recorded question
            language: User's language preference  
            phone_number: Phone number for session tracking
            
        Returns:
            ProcessingResult with generated response
        """
        try:
            # Run async method in event loop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(
                self.process_question_async(recording_url, language, phone_number)
            )
            loop.close()
            return result
            
        except Exception as e:
            logger.error(f"Sync processing wrapper failed: {e}")
            return ProcessingResult(
                success=False,
                error_message=f"Processing wrapper failed: {str(e)}"
            )
    
    def cleanup(self):
        """Clean up temporary files"""
        try:
            import shutil
            if os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
                logger.info(f"Cleaned up temp directory: {self.temp_dir}")
        except Exception as e:
            logger.error(f"Failed to cleanup temp directory: {e}")
    
    def __del__(self):
        """Cleanup on destruction"""
        self.cleanup()