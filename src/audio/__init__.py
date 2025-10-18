# Audio Processing Module

from .audio_processor import (
    AudioProcessor,
    VoiceGender,
    AudioProcessingResult,
    TTSConfig
)
from .language_types import Language
from .audio_utils import (
    AudioCodec,
    AudioQualityChecker,
    AudioFormat,
    create_test_audio_file
)
from .language_detector import (
    LanguageDetector,
    LanguageDetectionResult,
    AccentType,
    AccentHandler
)

__all__ = [
    'AudioProcessor',
    'Language',
    'VoiceGender',
    'AudioProcessingResult',
    'TTSConfig',
    'AudioCodec',
    'AudioQualityChecker',
    'AudioFormat',
    'LanguageDetector',
    'LanguageDetectionResult',
    'AccentType',
    'AccentHandler',
    'create_test_audio_file'
]