#!/usr/bin/env python3
"""
Production setup script for VidyaVani IVR Learning System
Handles environment-specific configuration and initialization
"""

import os
import sys
import json
import logging
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import Config

def setup_logging():
    """Setup production logging configuration"""
    logging.basicConfig(
        level=getattr(logging, Config.LOG_LEVEL),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s' if Config.LOG_FORMAT == 'console' 
               else '{"timestamp": "%(asctime)s", "logger": "%(name)s", "level": "%(levelname)s", "message": "%(message)s"}'
    )
    return logging.getLogger(__name__)

def create_directories():
    """Create necessary directories for production"""
    directories = [
        'logs',
        'data/ncert/vector_db',
        'audio_storage',
        'call_recordings/audio',
        'call_recordings/metadata'
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"✓ Created directory: {directory}")

def validate_environment():
    """Validate production environment configuration"""
    logger = logging.getLogger(__name__)
    
    try:
        # Validate required environment variables
        Config.validate_required_keys()
        logger.info("✓ All required environment variables are set")
        
        # Setup Google Cloud credentials
        credentials_path = Config.setup_google_credentials()
        if credentials_path:
            logger.info(f"✓ Google Cloud credentials configured: {credentials_path}")
        else:
            logger.warning("⚠ Google Cloud credentials not found - STT/TTS may not work")
        
        # Validate deployment platform
        platform = Config.DEPLOYMENT_PLATFORM
        logger.info(f"✓ Deployment platform: {platform}")
        
        # Check Redis availability in production
        if Config.IS_PRODUCTION and Config.USE_REDIS:
            try:
                import redis
                r = redis.from_url(Config.REDIS_URL)
                r.ping()
                logger.info("✓ Redis connection successful")
            except Exception as e:
                logger.warning(f"⚠ Redis connection failed: {e}")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Environment validation failed: {e}")
        return False

def initialize_vector_database():
    """Initialize FAISS vector database if needed"""
    logger = logging.getLogger(__name__)
    
    vector_db_path = Path('data/ncert/vector_db')
    
    # Check if vector database exists
    if not (vector_db_path / 'faiss_index.bin').exists():
        logger.info("Vector database not found - will be created on first content processing")
    else:
        logger.info("✓ Vector database found")
    
    return True

def setup_performance_monitoring():
    """Setup production performance monitoring"""
    logger = logging.getLogger(__name__)
    
    # Create performance metrics directory
    os.makedirs('logs/metrics', exist_ok=True)
    
    # Initialize performance tracking
    try:
        from src.utils.performance_tracker import performance_tracker
        performance_tracker.reset_metrics()
        logger.info("✓ Performance monitoring initialized")
    except Exception as e:
        logger.warning(f"⚠ Performance monitoring setup failed: {e}")
    
    return True

def print_deployment_summary():
    """Print deployment configuration summary"""
    config = Config.get_environment_config()
    deployment_info = Config.get_deployment_info()
    
    print("\n" + "="*60)
    print("VidyaVani IVR Learning System - Production Setup")
    print("="*60)
    print(f"Environment: {config['environment']}")
    print(f"Platform: {deployment_info['platform']}")
    print(f"Workers: {deployment_info['workers']}")
    print(f"Timeout: {deployment_info['timeout']}s")
    print(f"Redis: {'Enabled' if config['use_redis'] else 'Disabled'}")
    print(f"Log Level: {config['log_level']}")
    print(f"Max Concurrent Calls: {config['max_concurrent_calls']}")
    print(f"Response Timeout: {config['response_timeout']}s")
    print("="*60)

def main():
    """Main setup function"""
    print("Starting VidyaVani production setup...")
    
    # Setup logging first
    logger = setup_logging()
    logger.info("Production setup started")
    
    success = True
    
    # Create necessary directories
    try:
        create_directories()
        logger.info("✓ Directory structure created")
    except Exception as e:
        logger.error(f"✗ Directory creation failed: {e}")
        success = False
    
    # Validate environment
    if not validate_environment():
        success = False
    
    # Initialize vector database
    if not initialize_vector_database():
        success = False
    
    # Setup performance monitoring
    if not setup_performance_monitoring():
        success = False
    
    # Print summary
    print_deployment_summary()
    
    if success:
        logger.info("✓ Production setup completed successfully")
        print("\n✓ Production setup completed successfully!")
        return 0
    else:
        logger.error("✗ Production setup failed")
        print("\n✗ Production setup failed - check logs for details")
        return 1

if __name__ == '__main__':
    sys.exit(main())