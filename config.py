"""
Configuration settings for VidyaVani IVR Learning System
"""

import os
import json
from dataclasses import dataclass
from typing import Dict, Any

@dataclass
class Config:
    """Application configuration class"""
    
    # Environment Detection
    FLASK_ENV: str = os.getenv('FLASK_ENV', 'development')
    IS_PRODUCTION: bool = FLASK_ENV == 'production'
    IS_DEVELOPMENT: bool = FLASK_ENV == 'development'
    
    # Flask Configuration
    SECRET_KEY: str = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # Production Security Settings
    if IS_PRODUCTION:
        # Force HTTPS in production
        PREFERRED_URL_SCHEME: str = 'https'
        SESSION_COOKIE_SECURE: bool = True
        SESSION_COOKIE_HTTPONLY: bool = True
        SESSION_COOKIE_SAMESITE: str = 'Lax'
    
    # Exotel Configuration
    EXOTEL_ACCOUNT_SID: str = os.getenv('EXOTEL_ACCOUNT_SID', '')
    EXOTEL_API_KEY: str = os.getenv('EXOTEL_API_KEY', '')
    EXOTEL_API_TOKEN: str = os.getenv('EXOTEL_API_TOKEN', '')
    EXOTEL_PHONE_NUMBER: str = os.getenv('EXOTEL_PHONE_NUMBER', '')
    EXOTEL_APP_ID: str = os.getenv('EXOTEL_APP_ID', '')
    
    # AI Configuration (supports OpenAI, OpenRouter, and Gemini)
    OPENAI_API_KEY: str = os.getenv('OPENAI_API_KEY', '')
    OPENAI_BASE_URL: str = os.getenv('OPENAI_BASE_URL', '')  # For OpenRouter or other providers
    OPENAI_MODEL: str = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')  # Default model
    OPENAI_MAX_TOKENS: int = int(os.getenv('OPENAI_MAX_TOKENS', '150'))
    OPENAI_TEMPERATURE: float = float(os.getenv('OPENAI_TEMPERATURE', '0.3'))
    
    # Google Gemini Configuration (alternative to OpenAI)
    GOOGLE_GEMINI_API_KEY: str = os.getenv('GOOGLE_GEMINI_API_KEY', '')
    GEMINI_MODEL: str = os.getenv('GEMINI_MODEL', 'gemini-2.5-flash')
    GEMINI_MAX_TOKENS: int = int(os.getenv('GEMINI_MAX_TOKENS', '500'))
    GEMINI_TEMPERATURE: float = float(os.getenv('GEMINI_TEMPERATURE', '0.7'))
    
    # AI Provider Selection (auto-detect based on available keys)
    USE_GEMINI: bool = bool(GOOGLE_GEMINI_API_KEY and (not OPENAI_API_KEY or OPENAI_API_KEY.strip() == ''))
    
    # LLM Configuration
    LLM_MODEL = os.getenv('LLM_MODEL', 'gpt-5-nano')  # Changed from gpt-4o-mini
    LLM_TEMPERATURE = float(os.getenv('LLM_TEMPERATURE', '0.7'))
    LLM_MAX_TOKENS = int(os.getenv('LLM_MAX_TOKENS', '500'))
    
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
    AUDIO_IVR_SAMPLE_RATE: int = int(os.getenv('AUDIO_IVR_SAMPLE_RATE', '8000'))
    AUDIO_STORAGE_BASE_URL: str = os.getenv('AUDIO_STORAGE_BASE_URL', 'http://localhost:5001')
    AUDIO_STORAGE_DIR: str = os.getenv('AUDIO_STORAGE_DIR', os.path.join(os.getcwd(), 'audio_storage'))
    
    # Content Configuration
    CONTENT_CHUNK_SIZE: int = int(os.getenv('CONTENT_CHUNK_SIZE', '300'))
    CONTENT_OVERLAP: int = int(os.getenv('CONTENT_OVERLAP', '50'))
    TOP_K_RETRIEVAL: int = int(os.getenv('TOP_K_RETRIEVAL', '3'))
    
    # Deployment Configuration
    DEPLOYMENT_PLATFORM: str = os.getenv('DEPLOYMENT_PLATFORM', 'local')  # render, railway, docker, local
    
    # Load Balancing Configuration
    GUNICORN_WORKERS: int = int(os.getenv('GUNICORN_WORKERS', '2' if IS_PRODUCTION else '1'))
    GUNICORN_TIMEOUT: int = int(os.getenv('GUNICORN_TIMEOUT', '120'))
    GUNICORN_MAX_REQUESTS: int = int(os.getenv('GUNICORN_MAX_REQUESTS', '1000'))
    GUNICORN_MAX_REQUESTS_JITTER: int = int(os.getenv('GUNICORN_MAX_REQUESTS_JITTER', '100'))
    
    # Redis Configuration (Production)
    REDIS_URL: str = os.getenv('REDIS_URL', 'redis://localhost:6379/0' if IS_PRODUCTION else '')
    USE_REDIS: bool = bool(REDIS_URL and IS_PRODUCTION)
    
    # Logging Configuration
    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO' if IS_PRODUCTION else 'DEBUG')
    LOG_FORMAT: str = os.getenv('LOG_FORMAT', 'json' if IS_PRODUCTION else 'console')
    
    # Health Check Configuration
    HEALTH_CHECK_TIMEOUT: int = int(os.getenv('HEALTH_CHECK_TIMEOUT', '10'))
    HEALTH_CHECK_INTERVAL: int = int(os.getenv('HEALTH_CHECK_INTERVAL', '30'))
    
    @classmethod
    def get_environment_config(cls) -> Dict[str, Any]:
        """Get environment-specific configuration"""
        config = {
            'environment': cls.FLASK_ENV,
            'is_production': cls.IS_PRODUCTION,
            'deployment_platform': cls.DEPLOYMENT_PLATFORM,
            'workers': cls.GUNICORN_WORKERS,
            'use_redis': cls.USE_REDIS,
            'log_level': cls.LOG_LEVEL,
            'max_concurrent_calls': cls.MAX_CONCURRENT_CALLS,
            'response_timeout': cls.RESPONSE_TIMEOUT
        }
        return config
    
    @classmethod
    def validate_required_keys(cls):
        """Validate that required environment variables are set"""
        required_keys = [
            'EXOTEL_ACCOUNT_SID',
            'EXOTEL_API_KEY', 
            'EXOTEL_API_TOKEN'
        ]
        
        # Require either OpenAI or Gemini API key
        has_openai = bool(os.getenv('OPENAI_API_KEY', '').strip())
        has_gemini = bool(os.getenv('GOOGLE_GEMINI_API_KEY', '').strip())
        
        if not has_openai and not has_gemini:
            required_keys.append('OPENAI_API_KEY or GOOGLE_GEMINI_API_KEY')
        
        # Additional production requirements
        if cls.IS_PRODUCTION:
            required_keys.extend([
                'SECRET_KEY',
                'GOOGLE_CLOUD_PROJECT'
            ])
        
        missing_keys = []
        for key in required_keys:
            if not os.getenv(key):
                missing_keys.append(key)
        
        if missing_keys:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_keys)}")
        
        return True
    
    @classmethod
    def setup_google_credentials(cls):
        """Setup Google Cloud credentials from environment"""
        # Handle Google Cloud credentials JSON from environment variable
        credentials_json = os.getenv('GOOGLE_APPLICATION_CREDENTIALS_JSON')
        if credentials_json and not os.getenv('GOOGLE_APPLICATION_CREDENTIALS'):
            # Write credentials to temporary file for Google Cloud SDK
            import tempfile
            import json
            try:
                # Validate JSON format
                json.loads(credentials_json)
                with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                    f.write(credentials_json)
                    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = f.name
                    print(f"Google Cloud credentials written to: {f.name}")
            except json.JSONDecodeError as e:
                print(f"Invalid JSON in GOOGLE_APPLICATION_CREDENTIALS_JSON: {e}")
        
        return os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
    
    @classmethod
    def get_deployment_info(cls) -> Dict[str, Any]:
        """Get deployment information for monitoring"""
        return {
            'platform': cls.DEPLOYMENT_PLATFORM,
            'environment': cls.FLASK_ENV,
            'workers': cls.GUNICORN_WORKERS,
            'timeout': cls.GUNICORN_TIMEOUT,
            'max_requests': cls.GUNICORN_MAX_REQUESTS,
            'redis_enabled': cls.USE_REDIS,
            'log_level': cls.LOG_LEVEL
        }