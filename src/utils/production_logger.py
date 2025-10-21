"""
Production logging configuration for VidyaVani IVR Learning System
"""

import os
import json
import logging
import logging.handlers
from datetime import datetime
from typing import Dict, Any
from pathlib import Path

class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging in production"""
    
    def format(self, record):
        log_entry = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
        
        # Add extra fields if present
        if hasattr(record, 'extra_fields'):
            log_entry.update(record.extra_fields)
        
        # Add performance metrics if present
        if hasattr(record, 'performance_metrics'):
            log_entry['performance'] = record.performance_metrics
        
        # Add request context if present
        if hasattr(record, 'request_id'):
            log_entry['request_id'] = record.request_id
        
        if hasattr(record, 'session_id'):
            log_entry['session_id'] = record.session_id
        
        if hasattr(record, 'phone_number'):
            # Hash phone number for privacy
            import hashlib
            log_entry['phone_hash'] = hashlib.sha256(record.phone_number.encode()).hexdigest()[:8]
        
        return json.dumps(log_entry)

class ProductionLogger:
    """Production logging manager"""
    
    def __init__(self, config):
        self.config = config
        self.setup_logging()
    
    def setup_logging(self):
        """Setup production logging configuration"""
        # Create logs directory
        log_dir = Path('logs')
        log_dir.mkdir(exist_ok=True)
        
        # Root logger configuration
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, self.config.LOG_LEVEL))
        
        # Clear existing handlers
        root_logger.handlers.clear()
        
        # Console handler
        console_handler = logging.StreamHandler()
        
        if self.config.LOG_FORMAT == 'json':
            console_handler.setFormatter(JSONFormatter())
        else:
            console_handler.setFormatter(logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            ))
        
        root_logger.addHandler(console_handler)
        
        # File handlers for production
        if self.config.IS_PRODUCTION:
            # Application log file (rotating)
            app_handler = logging.handlers.RotatingFileHandler(
                log_dir / 'app.log',
                maxBytes=10*1024*1024,  # 10MB
                backupCount=5
            )
            app_handler.setFormatter(JSONFormatter())
            app_handler.setLevel(logging.INFO)
            root_logger.addHandler(app_handler)
            
            # Error log file (rotating)
            error_handler = logging.handlers.RotatingFileHandler(
                log_dir / 'error.log',
                maxBytes=10*1024*1024,  # 10MB
                backupCount=5
            )
            error_handler.setFormatter(JSONFormatter())
            error_handler.setLevel(logging.ERROR)
            root_logger.addHandler(error_handler)
            
            # Performance log file
            perf_handler = logging.handlers.RotatingFileHandler(
                log_dir / 'performance.log',
                maxBytes=10*1024*1024,  # 10MB
                backupCount=3
            )
            perf_handler.setFormatter(JSONFormatter())
            perf_handler.addFilter(self._performance_filter)
            root_logger.addHandler(perf_handler)
    
    def _performance_filter(self, record):
        """Filter for performance-related log entries"""
        return hasattr(record, 'performance_metrics') or 'performance' in record.getMessage().lower()
    
    def log_request(self, request_id: str, endpoint: str, method: str, 
                   session_id: str = None, phone_number: str = None):
        """Log incoming request"""
        logger = logging.getLogger('request')
        
        extra = {
            'extra_fields': {
                'request_id': request_id,
                'endpoint': endpoint,
                'method': method,
                'event_type': 'request_start'
            }
        }
        
        if session_id:
            extra['session_id'] = session_id
        if phone_number:
            extra['phone_number'] = phone_number
        
        logger.info(f"Request started: {method} {endpoint}", extra=extra)
    
    def log_response(self, request_id: str, status_code: int, response_time: float,
                    session_id: str = None):
        """Log response completion"""
        logger = logging.getLogger('request')
        
        extra = {
            'extra_fields': {
                'request_id': request_id,
                'status_code': status_code,
                'response_time': response_time,
                'event_type': 'request_complete'
            }
        }
        
        if session_id:
            extra['session_id'] = session_id
        
        logger.info(f"Request completed: {status_code} ({response_time:.3f}s)", extra=extra)
    
    def log_performance(self, component: str, metrics: Dict[str, Any], 
                       session_id: str = None):
        """Log performance metrics"""
        logger = logging.getLogger('performance')
        
        extra = {
            'performance_metrics': {
                'component': component,
                **metrics
            }
        }
        
        if session_id:
            extra['session_id'] = session_id
        
        logger.info(f"Performance metrics for {component}", extra=extra)
    
    def log_error(self, error: Exception, context: Dict[str, Any] = None,
                 session_id: str = None, phone_number: str = None):
        """Log error with context"""
        logger = logging.getLogger('error')
        
        extra = {
            'extra_fields': {
                'error_type': type(error).__name__,
                'event_type': 'error'
            }
        }
        
        if context:
            extra['extra_fields']['context'] = context
        
        if session_id:
            extra['session_id'] = session_id
        if phone_number:
            extra['phone_number'] = phone_number
        
        logger.error(f"Error occurred: {str(error)}", exc_info=error, extra=extra)
    
    def log_api_call(self, api_name: str, endpoint: str, response_time: float,
                    success: bool, cost: float = None, session_id: str = None):
        """Log external API call"""
        logger = logging.getLogger('api')
        
        extra = {
            'extra_fields': {
                'api_name': api_name,
                'endpoint': endpoint,
                'response_time': response_time,
                'success': success,
                'event_type': 'api_call'
            }
        }
        
        if cost is not None:
            extra['extra_fields']['estimated_cost'] = cost
        
        if session_id:
            extra['session_id'] = session_id
        
        status = "successful" if success else "failed"
        logger.info(f"API call {status}: {api_name} ({response_time:.3f}s)", extra=extra)
    
    def log_cache_operation(self, operation: str, cache_type: str, key: str,
                          hit: bool = None, session_id: str = None):
        """Log cache operations"""
        logger = logging.getLogger('cache')
        
        extra = {
            'extra_fields': {
                'operation': operation,
                'cache_type': cache_type,
                'cache_key_hash': hash(key) % 10000,  # Hash for privacy
                'event_type': 'cache_operation'
            }
        }
        
        if hit is not None:
            extra['extra_fields']['cache_hit'] = hit
        
        if session_id:
            extra['session_id'] = session_id
        
        logger.debug(f"Cache {operation}: {cache_type}", extra=extra)

class RequestLogger:
    """Request logging middleware"""
    
    def __init__(self, app, production_logger):
        self.app = app
        self.production_logger = production_logger
        self.setup_middleware()
    
    def setup_middleware(self):
        """Setup Flask request logging middleware"""
        
        @self.app.before_request
        def before_request():
            import uuid
            from flask import g, request
            
            # Generate request ID
            g.request_id = str(uuid.uuid4())
            g.start_time = datetime.utcnow()
            
            # Extract session info safely
            session_id = None
            phone_number = None
            
            try:
                # Try form data first
                session_id = request.form.get('session_id')
                phone_number = request.form.get('From') or request.form.get('phone_number')
                
                # Try JSON data if available and content-type is correct
                if request.is_json and request.json:
                    session_id = session_id or request.json.get('session_id')
                    phone_number = phone_number or request.json.get('phone_number')
            except Exception:
                # Ignore errors in session extraction
                pass
            
            # Log request start
            self.production_logger.log_request(
                request_id=g.request_id,
                endpoint=request.endpoint or request.path,
                method=request.method,
                session_id=session_id,
                phone_number=phone_number
            )
        
        @self.app.after_request
        def after_request(response):
            from flask import g
            
            # Calculate response time
            if hasattr(g, 'start_time'):
                response_time = (datetime.utcnow() - g.start_time).total_seconds()
                
                # Log response
                self.production_logger.log_response(
                    request_id=getattr(g, 'request_id', 'unknown'),
                    status_code=response.status_code,
                    response_time=response_time
                )
            
            return response

# Global production logger instance
production_logger = None

def get_production_logger(config):
    """Get or create global production logger instance"""
    global production_logger
    if production_logger is None:
        production_logger = ProductionLogger(config)
    return production_logger

def setup_request_logging(app, config):
    """Setup request logging for Flask app"""
    prod_logger = get_production_logger(config)
    RequestLogger(app, prod_logger)
    return prod_logger