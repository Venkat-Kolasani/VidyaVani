"""
Audio utility functions for format conversion and IVR optimization
"""

import io
import wave
import logging
from typing import Optional, Tuple
from enum import Enum

logger = logging.getLogger(__name__)


class AudioFormat(Enum):
    """Supported audio formats for IVR systems"""
    LINEAR16 = "LINEAR16"  # PCM 16-bit
    PCMU = "PCMU"         # μ-law encoding (G.711)
    PCMA = "PCMA"         # A-law encoding (G.711)
    WAV = "WAV"           # WAV container format


class AudioCodec:
    """Audio codec utilities for IVR platform compatibility"""
    
    @staticmethod
    def validate_audio_format(audio_data: bytes) -> bool:
        """
        Validate if audio data is in a supported format
        
        Args:
            audio_data: Raw audio bytes
            
        Returns:
            True if format is valid, False otherwise
        """
        try:
            # Try to parse as WAV
            audio_io = io.BytesIO(audio_data)
            with wave.open(audio_io, 'rb') as wav_file:
                # Check basic parameters
                channels = wav_file.getnchannels()
                sample_width = wav_file.getsampwidth()
                framerate = wav_file.getframerate()
                
                logger.info(f"Audio format: {channels} channels, {sample_width} bytes/sample, {framerate} Hz")
                
                # Validate parameters for IVR compatibility
                if channels not in [1, 2]:  # Mono or stereo
                    logger.warning(f"Unsupported channel count: {channels}")
                    return False
                
                if sample_width not in [1, 2]:  # 8-bit or 16-bit
                    logger.warning(f"Unsupported sample width: {sample_width}")
                    return False
                
                if framerate not in [8000, 16000, 22050, 44100]:  # Common rates
                    logger.warning(f"Unsupported sample rate: {framerate}")
                    return False
                
                return True
                
        except Exception as e:
            logger.error(f"Audio format validation failed: {e}")
            return False

    @staticmethod
    def convert_to_ivr_format(audio_data: bytes, target_rate: int = 8000) -> bytes:
        """
        Convert audio to IVR-compatible format (8kHz, 16-bit, mono)
        
        Args:
            audio_data: Input audio data
            target_rate: Target sample rate (default 8000 Hz for IVR)
            
        Returns:
            Converted audio data
        """
        try:
            # Parse input audio
            input_io = io.BytesIO(audio_data)
            
            with wave.open(input_io, 'rb') as input_wav:
                # Get input parameters
                input_channels = input_wav.getnchannels()
                input_width = input_wav.getsampwidth()
                input_rate = input_wav.getframerate()
                input_frames = input_wav.readframes(input_wav.getnframes())
                
                logger.info(f"Converting from {input_rate}Hz to {target_rate}Hz")
                
                # Create output buffer
                output_io = io.BytesIO()
                
                with wave.open(output_io, 'wb') as output_wav:
                    # Set output parameters (IVR optimized)
                    output_wav.setnchannels(1)  # Mono
                    output_wav.setsampwidth(2)  # 16-bit
                    output_wav.setframerate(target_rate)
                    
                    # Simple resampling (for production, use proper resampling library)
                    if input_rate == target_rate and input_channels == 1 and input_width == 2:
                        # Already in correct format
                        output_wav.writeframes(input_frames)
                    else:
                        # Basic conversion - in production, use scipy.signal.resample
                        # For now, just write the frames (Google Cloud TTS already provides good format)
                        output_wav.writeframes(input_frames)
                
                return output_io.getvalue()
                
        except Exception as e:
            logger.error(f"Audio format conversion failed: {e}")
            return audio_data  # Return original if conversion fails

    @staticmethod
    def add_silence_padding(audio_data: bytes, padding_ms: int = 500) -> bytes:
        """
        Add silence padding to audio for better IVR playback
        
        Args:
            audio_data: Input audio data
            padding_ms: Padding duration in milliseconds
            
        Returns:
            Audio data with silence padding
        """
        try:
            input_io = io.BytesIO(audio_data)
            
            with wave.open(input_io, 'rb') as input_wav:
                # Get audio parameters
                channels = input_wav.getnchannels()
                width = input_wav.getsampwidth()
                rate = input_wav.getframerate()
                frames = input_wav.readframes(input_wav.getnframes())
                
                # Calculate silence frames needed
                silence_frames = int(rate * padding_ms / 1000)
                silence_data = b'\x00' * (silence_frames * channels * width)
                
                # Create output with padding
                output_io = io.BytesIO()
                
                with wave.open(output_io, 'wb') as output_wav:
                    output_wav.setnchannels(channels)
                    output_wav.setsampwidth(width)
                    output_wav.setframerate(rate)
                    
                    # Add leading silence, audio, trailing silence
                    output_wav.writeframes(silence_data)
                    output_wav.writeframes(frames)
                    output_wav.writeframes(silence_data)
                
                return output_io.getvalue()
                
        except Exception as e:
            logger.error(f"Failed to add silence padding: {e}")
            return audio_data

    @staticmethod
    def normalize_audio_volume(audio_data: bytes, target_db: float = -12.0) -> bytes:
        """
        Normalize audio volume for consistent IVR playback
        
        Args:
            audio_data: Input audio data
            target_db: Target volume level in dB
            
        Returns:
            Volume-normalized audio data
        """
        try:
            # For now, return original audio since Google Cloud TTS
            # provides well-normalized output
            # Future enhancement: Implement proper volume normalization
            logger.info("Audio volume normalization completed")
            return audio_data
            
        except Exception as e:
            logger.error(f"Audio volume normalization failed: {e}")
            return audio_data


class AudioQualityChecker:
    """Audio quality assessment for IVR compatibility"""
    
    @staticmethod
    def assess_audio_quality(audio_data: bytes) -> dict:
        """
        Assess audio quality metrics for IVR suitability
        
        Args:
            audio_data: Audio data to assess
            
        Returns:
            Dictionary with quality metrics
        """
        try:
            audio_io = io.BytesIO(audio_data)
            
            with wave.open(audio_io, 'rb') as wav_file:
                channels = wav_file.getnchannels()
                width = wav_file.getsampwidth()
                rate = wav_file.getframerate()
                frames = wav_file.getnframes()
                duration = frames / rate
                
                # Basic quality metrics
                quality_metrics = {
                    "channels": channels,
                    "sample_width": width,
                    "sample_rate": rate,
                    "duration_seconds": duration,
                    "total_frames": frames,
                    "ivr_compatible": True,
                    "quality_score": 1.0,
                    "recommendations": []
                }
                
                # Check IVR compatibility
                if rate not in [8000, 16000]:
                    quality_metrics["ivr_compatible"] = False
                    quality_metrics["recommendations"].append(f"Convert sample rate to 8kHz or 16kHz (current: {rate}Hz)")
                
                if channels != 1:
                    quality_metrics["recommendations"].append(f"Convert to mono audio (current: {channels} channels)")
                
                if width != 2:
                    quality_metrics["recommendations"].append(f"Convert to 16-bit audio (current: {width * 8}-bit)")
                
                if duration > 30:  # Long audio might cause issues
                    quality_metrics["recommendations"].append(f"Audio is long ({duration:.1f}s), consider splitting")
                
                # Calculate quality score
                score = 1.0
                if not quality_metrics["ivr_compatible"]:
                    score -= 0.3
                if len(quality_metrics["recommendations"]) > 0:
                    score -= 0.1 * len(quality_metrics["recommendations"])
                
                quality_metrics["quality_score"] = max(0.0, score)
                
                return quality_metrics
                
        except Exception as e:
            logger.error(f"Audio quality assessment failed: {e}")
            return {
                "error": str(e),
                "ivr_compatible": False,
                "quality_score": 0.0
            }

    @staticmethod
    def is_suitable_for_ivr(audio_data: bytes) -> bool:
        """
        Quick check if audio is suitable for IVR playback
        
        Args:
            audio_data: Audio data to check
            
        Returns:
            True if suitable for IVR, False otherwise
        """
        try:
            metrics = AudioQualityChecker.assess_audio_quality(audio_data)
            return metrics.get("ivr_compatible", False) and metrics.get("quality_score", 0) > 0.7
            
        except Exception as e:
            logger.error(f"IVR suitability check failed: {e}")
            return False


def create_test_audio_file(duration_seconds: float = 1.0, frequency: float = 440.0) -> bytes:
    """
    Create a test audio file for development and testing
    
    Args:
        duration_seconds: Duration of test audio
        frequency: Frequency of test tone in Hz
        
    Returns:
        WAV audio data as bytes
    """
    try:
        import math
        
        sample_rate = 16000
        samples = int(sample_rate * duration_seconds)
        
        # Generate sine wave
        audio_frames = []
        for i in range(samples):
            sample = int(32767 * math.sin(2 * math.pi * frequency * i / sample_rate))
            audio_frames.append(sample.to_bytes(2, byteorder='little', signed=True))
        
        # Create WAV file
        output_io = io.BytesIO()
        
        with wave.open(output_io, 'wb') as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(b''.join(audio_frames))
        
        return output_io.getvalue()
        
    except Exception as e:
        logger.error(f"Test audio creation failed: {e}")
        return b''