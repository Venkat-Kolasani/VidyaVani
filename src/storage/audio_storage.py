"""
Audio Storage Service for VidyaVani IVR
Handles uploading and serving audio files for Exotel integration
"""

import io
import logging
import os
import hashlib
import threading
import time
import wave
from datetime import datetime, timedelta
from typing import Optional

from flask import Flask, abort, send_file

from config import Config

logger = logging.getLogger(__name__)

class AudioStorageService:
    """
    Audio storage service that provides publicly accessible URLs for Exotel
    Uses local file storage with HTTP serving for development/demo
    Can be extended to use S3/GCS for production
    """
    
    def __init__(
        self,
        base_url: str = "http://localhost:5001",
        storage_dir: str = "audio_storage",
        sample_rate: int = 8000,
    ):
        self.base_url = base_url.rstrip('/')
        self.storage_dir = storage_dir
        self.sample_rate = sample_rate
        self.audio_files = {}  # filename -> metadata
        self._lock = threading.Lock()

        # Create storage directory
        os.makedirs(self.storage_dir, exist_ok=True)

        # Start cleanup thread
        self.cleanup_thread = threading.Thread(target=self._cleanup_old_files, daemon=True)
        self.cleanup_thread.start()

        logger.info(f"Audio storage initialized: {self.storage_dir} (base URL: {self.base_url})")
    
    def store_audio(self, audio_data: bytes, filename_prefix: str = "audio") -> str:
        """
        Store audio data and return publicly accessible URL
        
        Args:
            audio_data: Raw audio data
            filename_prefix: Prefix for the generated filename
            
        Returns:
            Public URL for the audio file
        """
        try:
            processed_audio = self._ensure_wav_format(audio_data)

            # Generate unique filename
            timestamp = int(time.time())
            content_hash = hashlib.md5(processed_audio).hexdigest()[:8]
            filename = f"{filename_prefix}_{timestamp}_{content_hash}.wav"
            
            # Save to storage directory
            file_path = os.path.join(self.storage_dir, filename)
            
            with open(file_path, 'wb') as f:
                f.write(processed_audio)
            
            # Store metadata
            with self._lock:
                self.audio_files[filename] = {
                    'created_at': datetime.now(),
                    'size': len(processed_audio),
                    'path': file_path,
                }
            
            # Generate public URL
            public_url = f"{self.base_url}/audio/{filename}"
            
            logger.info(
                "Audio stored: %s (%d bytes raw -> %d bytes wav) -> %s",
                filename,
                len(audio_data),
                len(processed_audio),
                public_url,
            )
            return public_url
            
        except Exception as e:
            logger.error(f"Failed to store audio: {e}")
            return ""
    
    def get_audio_file_path(self, filename: str) -> Optional[str]:
        """
        Get local file path for serving
        
        Args:
            filename: Audio filename
            
        Returns:
            Local file path or None if not found
        """
        with self._lock:
            metadata = self.audio_files.get(filename)
        if metadata:
            file_path = metadata['path']
            if os.path.exists(file_path):
                return file_path
        
        return None
    
    def cleanup_file(self, filename: str) -> bool:
        """
        Remove audio file from storage
        
        Args:
            filename: Audio filename to remove
            
        Returns:
            True if removed successfully
        """
        try:
            with self._lock:
                metadata = self.audio_files.get(filename)
                if not metadata:
                    return False
                file_path = metadata['path']
                if os.path.exists(file_path):
                    os.remove(file_path)
                del self.audio_files[filename]
            logger.info(f"Cleaned up audio file: {filename}")
            return True
        except Exception as e:
            logger.error(f"Failed to cleanup audio file {filename}: {e}")
        
        return False
    
    def _cleanup_old_files(self):
        """
        Background thread to cleanup old audio files
        Removes files older than 1 hour
        """
        while True:
            try:
                cutoff_time = datetime.now() - timedelta(hours=1)
                with self._lock:
                    files_to_remove = [
                        filename
                        for filename, metadata in self.audio_files.items()
                        if metadata['created_at'] < cutoff_time
                    ]
                
                for filename in files_to_remove:
                    self.cleanup_file(filename)
                
                if files_to_remove:
                    logger.info(f"Cleaned up {len(files_to_remove)} old audio files")
                
            except Exception as e:
                logger.error(f"Error in audio cleanup thread: {e}")
            
            # Sleep for 10 minutes before next cleanup
            time.sleep(600)
    
    def get_storage_stats(self) -> dict:
        """Get storage statistics"""
        with self._lock:
            total_files = len(self.audio_files)
            total_size = sum(metadata['size'] for metadata in self.audio_files.values())
        
        return {
            'total_files': total_files,
            'total_size_bytes': total_size,
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'storage_directory': self.storage_dir
        }

    def _ensure_wav_format(self, audio_data: bytes) -> bytes:
        """
        Ensure audio data is wrapped in a WAV container.

        Exotel expects a valid WAV file. Google TTS returns raw PCM when
        requesting LINEAR16, so we inject the minimal header when needed.
        """

        if not audio_data:
            return audio_data

        if audio_data[:4] == b"RIFF":
            return audio_data

        # PCM16 requires even number of bytes; fall back to original on mismatch
        if len(audio_data) % 2 != 0:
            logger.warning("PCM payload length not 16-bit aligned; storing raw bytes")
            return audio_data

        try:
            buffer = io.BytesIO()
            with wave.open(buffer, 'wb') as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(self.sample_rate)
                wav_file.writeframes(audio_data)
            return buffer.getvalue()
        except Exception as exc:
            logger.error(f"Failed to wrap audio in WAV container: {exc}")
            return audio_data

# Global audio storage instance
_config = Config()
audio_storage = AudioStorageService(
    base_url=_config.AUDIO_STORAGE_BASE_URL,
    storage_dir=_config.AUDIO_STORAGE_DIR,
    sample_rate=_config.AUDIO_IVR_SAMPLE_RATE,
)

def register_audio_routes(app: Flask):
    """
    Register audio serving routes with Flask app
    
    Args:
        app: Flask application instance
    """
    
    @app.route('/audio/<filename>')
    def serve_audio(filename):
        """Serve audio files for Exotel"""
        file_path = audio_storage.get_audio_file_path(filename)
        
        if file_path and os.path.exists(file_path):
            logger.info(f"Serving audio file: {filename}")
            try:
                return send_file(
                    file_path,
                    mimetype='audio/wav',
                    as_attachment=False,
                    download_name=filename
                )
            except Exception as e:
                logger.error(f"Error serving audio file {filename}: {e}")
                abort(500)
        else:
            logger.warning(f"Audio file not found: {filename}")
            abort(404)
    
    @app.route('/audio-storage/stats')
    def audio_storage_stats():
        """Get audio storage statistics"""
        try:
            stats = audio_storage.get_storage_stats()
            return stats
        except Exception as e:
            logger.error(f"Error getting storage stats: {e}")
            return {'error': 'Failed to get storage stats'}, 500
    
    @app.route('/audio-storage/test', methods=['POST'])
    def test_audio_storage():
        """Test endpoint to store and retrieve audio"""
        try:
            # Create test audio data
            test_audio = b"RIFF test audio data for endpoint validation"
            
            # Store audio
            audio_url = audio_storage.store_audio(test_audio, "endpoint_test")
            
            if audio_url:
                return {
                    'success': True,
                    'audio_url': audio_url,
                    'message': 'Audio stored successfully'
                }
            else:
                return {
                    'success': False,
                    'message': 'Failed to store audio'
                }, 500
                
        except Exception as e:
            logger.error(f"Error in test audio storage: {e}")
            return {
                'success': False,
                'error': str(e)
            }, 500
    
    logger.info("Audio serving routes registered")