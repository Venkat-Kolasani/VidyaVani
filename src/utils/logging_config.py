"""
Logging configuration for VidyaVani IVR Learning System
"""

import logging
import logging.config
import os
from datetime import datetime

def setup_logging():
    """Configure logging for the application"""
    
    # Ensure logs directory exists
    os.makedirs('logs', exist_ok=True)
    
    # Create log filename with date
    log_filename = f"logs/vidyavani_{datetime.now().strftime('%Y%m%d')}.log"
    
    logging_config = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'detailed': {
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
            },
            'simple': {
                'format': '%(asctime)s - %(levelname)s - %(message)s'
            },
            'performance': {
                'format': '%(asctime)s - PERF - %(message)s'
            }
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'level': 'INFO',
                'formatter': 'simple',
                'stream': 'ext://sys.stdout'
            },
            'file': {
                'class': 'logging.FileHandler',
                'level': 'DEBUG',
                'formatter': 'detailed',
                'filename': log_filename,
                'mode': 'a'
            },
            'performance': {
                'class': 'logging.FileHandler',
                'level': 'INFO',
                'formatter': 'performance',
                'filename': 'logs/performance.log',
                'mode': 'a'
            }
        },
        'loggers': {
            '': {  # root logger
                'handlers': ['console', 'file'],
                'level': 'DEBUG',
                'propagate': False
            },
            'performance': {
                'handlers': ['performance'],
                'level': 'INFO',
                'propagate': False
            },
            'werkzeug': {  # Flask's built-in server
                'handlers': ['console'],
                'level': 'WARNING',
                'propagate': False
            }
        }
    }
    
    logging.config.dictConfig(logging_config)
    
    # Create performance logger
    perf_logger = logging.getLogger('performance')
    
    return perf_logger

class PerformanceLogger:
    """Performance monitoring logger with enhanced tracking"""
    
    def __init__(self):
        self.logger = logging.getLogger('performance')
    
    def log_response_time(self, component: str, duration: float, session_id: str = None):
        """Log component response time"""
        session_info = f" - Session: {session_id}" if session_id else ""
        self.logger.info(f"{component}: {duration:.3f}s{session_info}")
    
    def log_api_call(self, service: str, endpoint: str, duration: float, status: str, 
                    tokens_used: int = 0, estimated_cost: float = 0.0):
        """Log external API call performance with usage tracking"""
        cost_info = f", Cost: ${estimated_cost:.4f}" if estimated_cost > 0 else ""
        token_info = f", Tokens: {tokens_used}" if tokens_used > 0 else ""
        self.logger.info(f"API - {service}.{endpoint}: {duration:.3f}s - {status}{token_info}{cost_info}")
    
    def log_cache_hit(self, cache_type: str, key_hash: str, hit: bool):
        """Log cache hit/miss"""
        status = "HIT" if hit else "MISS"
        self.logger.info(f"CACHE - {cache_type}.{key_hash[:8]}: {status}")
    
    def log_concurrent_users(self, count: int):
        """Log concurrent user count"""
        self.logger.info(f"CONCURRENT_USERS: {count}")
    
    def log_processing_pipeline(self, phone_number: str, stage: str, duration: float, success: bool):
        """Log processing pipeline stage performance"""
        status = "SUCCESS" if success else "FAILED"
        self.logger.info(f"PIPELINE - {phone_number} - {stage}: {duration:.3f}s - {status}")
    
    def log_error_recovery(self, component: str, error_type: str, recovery_action: str):
        """Log error recovery actions"""
        self.logger.info(f"ERROR_RECOVERY - {component}: {error_type} -> {recovery_action}")

# Initialize performance logger instance
performance_logger = PerformanceLogger()