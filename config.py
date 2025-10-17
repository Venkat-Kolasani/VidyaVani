"""
Configuration settings for VidyaVani IVR Learning System
"""

import os
from dataclasses import dataclass

@dataclass
class Config:
    """Application configuration class"""
    
    # Flask Configuration
    SECRET_KEY: str = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    FLASK_ENV: str = os.getenv('FLASK_ENV', 'development')
    
    # Exotel Configuration
    EXOTEL_ACCOUNT_SID: str = os.getenv('EXOTEL_ACCOUNT_SID', '')
    EXOTEL_API_KEY: str = os.getenv('EXOTEL_API_KEY', '')
    EXOTEL_API_TOKEN: str = os.getenv('EXOTEL_API_TOKEN', '')
    EXOTEL_PHONE_NUMBER: str = os.getenv('EXOTEL_PHONE_NUMBER', '')
    EXOTEL_APP_ID: str = os.getenv('EXOTEL_APP_ID', '')
    
    # OpenAI Configuration
    OPENAI_API_KEY: str = os.getenv('OPENAI_API_KEY', '')
    OPENAI_MODEL: str = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')  # Cheapest model available
    OPENAI_MAX_TOKENS: int = int(os.getenv('OPENAI_MAX_TOKENS', '150'))
    OPENAI_TEMPERATURE: float = float(os.getenv('OPENAI_TEMPERATURE', '0.3'))
    
    # Google Cloud Configuration
    GOOGLE_CLOUD_PROJECT: str = os.getenv('GOOGLE_CLOUD_PROJECT', '')
    GOOGLE_APPLICATION_CREDENTIALS: str = os.getenv('GOOGLE_APPLICATION_CREDENTIALS', '')
    
    # Performance Configuration
    MAX_CONCURRENT_CALLS: int = int(os.getenv('MAX_CONCURRENT_CALLS', '5'))
    RESPONSE_TIMEOUT: int = int(os.getenv('RESPONSE_TIMEOUT', '8'))
    CACHE_TTL: int = int(os.getenv('CACHE_TTL', '3600'))
    
    # Audio Configuration
    MAX_RECORDING_DURATION: int = int(os.getenv('MAX_RECORDING_DURATION', '15'))
    AUDIO_SAMPLE_RATE: int = int(os.getenv('AUDIO_SAMPLE_RATE', '16000'))
    
    # Content Configuration
    CONTENT_CHUNK_SIZE: int = int(os.getenv('CONTENT_CHUNK_SIZE', '300'))
    CONTENT_OVERLAP: int = int(os.getenv('CONTENT_OVERLAP', '50'))
    TOP_K_RETRIEVAL: int = int(os.getenv('TOP_K_RETRIEVAL', '3'))
    
    @classmethod
    def validate_required_keys(cls):
        """Validate that required environment variables are set"""
        required_keys = [
            'EXOTEL_ACCOUNT_SID',
            'EXOTEL_API_KEY',
            'EXOTEL_API_TOKEN',
            'OPENAI_API_KEY'
        ]
        
        missing_keys = []
        for key in required_keys:
            if not os.getenv(key):
                missing_keys.append(key)
        
        if missing_keys:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_keys)}")
        
        return True