"""
Enhanced Error Handler for VidyaVani IVR Learning System

This module provides comprehensive error handling, retry logic, and fallback responses
specifically designed for demo reliability and graceful degradation.
"""

import logging
import time
import functools
from typing import Dict, Any, Optional, Callable, List, Tuple
from dataclasses import dataclass
from enum import Enum
import traceback

from .error_tracker import error_tracker

logger = logging.getLogger(__name__)


class ErrorType(Enum):
    """Categories of errors for appropriate handling"""
    API_TIMEOUT = "api_timeout"
    API_RATE_LIMIT = "api_rate_limit"
    AUDIO_PROCESSING = "audio_processing"
    CONTENT_NOT_FOUND = "content_not_found"
    UNCLEAR_SPEECH = "unclear_speech"
    RECORDING_ISSUE = "recording_issue"
    PROCESSING_TIMEOUT = "processing_timeout"
    NETWORK_ERROR = "network_error"
    SYSTEM_ERROR = "system_error"
    INVALID_INPUT = "invalid_input"


@dataclass
class ErrorResponse:
    """Structured error response with multilingual support"""
    error_type: ErrorType
    english_message: str
    telugu_message: str
    recovery_action: str
    retry_allowed: bool = True
    redirect_to_menu: bool = False


class ErrorResponseTemplates:
    """Centralized error response templates for English and Telugu"""
    
    TEMPLATES = {
        ErrorType.API_TIMEOUT: ErrorResponse(
            error_type=ErrorType.API_TIMEOUT,
            english_message="I'm taking a bit longer than usual to process your question. Please wait a moment while I try again.",
            telugu_message="మీ ప్రశ్నను ప్రాసెస్ చేయడానికి సాధారణం కంటే ఎక్కువ సమయం పడుతోంది. నేను మళ్లీ ప్రయత్నిస్తున్నప్పుడు దయచేసి కాసేపు వేచి ఉండండి.",
            recovery_action="Retry with exponential backoff",
            retry_allowed=True
        ),
        
        ErrorType.API_RATE_LIMIT: ErrorResponse(
            error_type=ErrorType.API_RATE_LIMIT,
            english_message="I'm currently handling many questions. Please wait a moment and I'll process your question shortly.",
            telugu_message="నేను ప్రస్తుతం చాలా ప్రశ్నలను హ్యాండిల్ చేస్తున్నాను. దయచేసి కాసేపు వేచి ఉండండి, నేను మీ ప్రశ్నను త్వరలో ప్రాసెస్ చేస్తాను.",
            recovery_action="Queue request and retry after delay",
            retry_allowed=True
        ),
        
        ErrorType.AUDIO_PROCESSING: ErrorResponse(
            error_type=ErrorType.AUDIO_PROCESSING,
            english_message="I'm having trouble with the audio. Please speak clearly and try asking your question again.",
            telugu_message="ఆడియోతో నాకు సమస్య ఉంది. దయచేసి స్పష్టంగా మాట్లాడి మీ ప్రశ్నను మళ్లీ అడగండి.",
            recovery_action="Request new recording with clearer instructions",
            retry_allowed=True,
            redirect_to_menu=True
        ),
        
        ErrorType.CONTENT_NOT_FOUND: ErrorResponse(
            error_type=ErrorType.CONTENT_NOT_FOUND,
            english_message="I don't have information about that topic in our Class 10 Science curriculum. Please ask about Physics, Chemistry, or Biology topics.",
            telugu_message="మా క్లాస్ 10 సైన్స్ పాఠ్యక్రమంలో ఆ విషయం గురించి నాకు సమాచారం లేదు. దయచేసి భౌతిక శాస్త్రం, రసాయన శాస్త్రం లేదా జీవ శాస్త్రం గురించి అడగండి.",
            recovery_action="Suggest alternative topics from curriculum",
            retry_allowed=True,
            redirect_to_menu=True
        ),
        
        ErrorType.UNCLEAR_SPEECH: ErrorResponse(
            error_type=ErrorType.UNCLEAR_SPEECH,
            english_message="I couldn't understand your question clearly. Please speak slowly and clearly, then ask your question again.",
            telugu_message="మీ ప్రశ్న స్పష్టంగా అర్థం కాలేదు. దయచేసి నెమ్మదిగా మరియు స్పష్టంగా మాట్లాడి మీ ప్రశ్నను మళ్లీ అడగండి.",
            recovery_action="Request clearer speech with instructions",
            retry_allowed=True,
            redirect_to_menu=True
        ),
        
        ErrorType.RECORDING_ISSUE: ErrorResponse(
            error_type=ErrorType.RECORDING_ISSUE,
            english_message="There was a problem with your recording. Please make sure you're in a quiet place and try recording your question again.",
            telugu_message="మీ రికార్డింగ్‌లో సమస్య ఉంది. దయచేసి మీరు నిశ్శబ్ద ప్రదేశంలో ఉన్నారని నిర్ధారించుకుని మీ ప్రశ్నను మళ్లీ రికార్డ్ చేయండి.",
            recovery_action="Guide user to better recording conditions",
            retry_allowed=True,
            redirect_to_menu=True
        ),
        
        ErrorType.PROCESSING_TIMEOUT: ErrorResponse(
            error_type=ErrorType.PROCESSING_TIMEOUT,
            english_message="I'm taking longer than expected to answer your question. Let me try with a simpler approach. Please ask a more specific question.",
            telugu_message="మీ ప్రశ్నకు సమాధానం ఇవ్వడానికి ఊహించిన దానికంటే ఎక్కువ సమయం పడుతోంది. నేను సరళమైన విధానంతో ప్రయత్నిస్తాను. దయచేసి మరింత నిర్దిష్టమైన ప్రశ్న అడగండి.",
            recovery_action="Suggest simpler question format",
            retry_allowed=True,
            redirect_to_menu=True
        ),
        
        ErrorType.NETWORK_ERROR: ErrorResponse(
            error_type=ErrorType.NETWORK_ERROR,
            english_message="I'm having connectivity issues. Please wait a moment while I reconnect, then try again.",
            telugu_message="నాకు కనెక్టివిటీ సమస్యలు ఉన్నాయి. నేను మళ్లీ కనెక్ట్ అవుతున్నప్పుడు దయచేసి కాసేపు వేచి ఉండి, ఆపై మళ్లీ ప్రయత్నించండి.",
            recovery_action="Retry after network recovery",
            retry_allowed=True
        ),
        
        ErrorType.SYSTEM_ERROR: ErrorResponse(
            error_type=ErrorType.SYSTEM_ERROR,
            english_message="I'm experiencing a technical issue. Please try asking your question again, or call back in a few minutes.",
            telugu_message="నాకు సాంకేతిక సమస్య ఉంది. దయచేసి మీ ప్రశ్నను మళ్లీ అడగండి లేదా కొన్ని నిమిషాల తర్వాత మళ్లీ కాల్ చేయండి.",
            recovery_action="System restart or fallback to cached responses",
            retry_allowed=False,
            redirect_to_menu=True
        ),
        
        ErrorType.INVALID_INPUT: ErrorResponse(
            error_type=ErrorType.INVALID_INPUT,
            english_message="I can only help with Class 10 Science questions. Please ask about topics like light, acids and bases, or life processes.",
            telugu_message="నేను క్లాస్ 10 సైన్స్ ప్రశ్నలతో మాత్రమే సహాయం చేయగలను. దయచేసి వెలుతురు, ఆమ్లాలు మరియు క్షారాలు లేదా జీవ ప్రక్రియలు వంటి విషయాల గురించి అడగండి.",
            recovery_action="Guide user to appropriate topics",
            retry_allowed=True,
            redirect_to_menu=True
        )
    }
    
    @classmethod
    def get_response(cls, error_type: ErrorType) -> ErrorResponse:
        """Get error response template for given error type"""
        return cls.TEMPLATES.get(error_type, cls.TEMPLATES[ErrorType.SYSTEM_ERROR])
    
    @classmethod
    def get_message(cls, error_type: ErrorType, language: str) -> str:
        """Get error message in specified language"""
        response = cls.get_response(error_type)
        if language.lower() == 'telugu':
            return response.telugu_message
        return response.english_message


class RetryConfig:
    """Configuration for retry logic"""
    
    def __init__(self, max_attempts: int = 3, base_delay: float = 1.0, 
                 max_delay: float = 10.0, exponential_base: float = 2.0):
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
    
    def get_delay(self, attempt: int) -> float:
        """Calculate delay for given attempt number"""
        delay = self.base_delay * (self.exponential_base ** attempt)
        return min(delay, self.max_delay)


def with_retry(error_types: List[ErrorType] = None, 
               config: RetryConfig = None,
               component_name: str = "unknown"):
    """
    Decorator to add retry logic to functions
    
    Args:
        error_types: List of error types that should trigger retries
        config: Retry configuration
        component_name: Name of component for logging
    """
    if error_types is None:
        error_types = [ErrorType.API_TIMEOUT, ErrorType.NETWORK_ERROR]
    
    if config is None:
        config = RetryConfig()
    
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(config.max_attempts):
                try:
                    result = func(*args, **kwargs)
                    
                    # If function returns a result object with success field
                    if hasattr(result, 'success') and not result.success:
                        # Check if error type allows retry
                        error_type = getattr(result, 'error_type', None)
                        if error_type in error_types and attempt < config.max_attempts - 1:
                            delay = config.get_delay(attempt)
                            logger.warning(f"Attempt {attempt + 1} failed for {component_name}, retrying in {delay}s")
                            time.sleep(delay)
                            continue
                    
                    return result
                    
                except Exception as e:
                    last_exception = e
                    
                    # Determine if this exception should trigger retry
                    should_retry = False
                    for error_type in error_types:
                        if _exception_matches_error_type(e, error_type):
                            should_retry = True
                            break
                    
                    if should_retry and attempt < config.max_attempts - 1:
                        delay = config.get_delay(attempt)
                        logger.warning(f"Attempt {attempt + 1} failed for {component_name}: {e}, retrying in {delay}s")
                        time.sleep(delay)
                        continue
                    else:
                        # Track error and re-raise
                        error_tracker.track_error(component_name, e, 
                                                recovery_action=f"Failed after {attempt + 1} attempts")
                        raise
            
            # All attempts failed
            if last_exception:
                raise last_exception
                
        return wrapper
    return decorator


def _exception_matches_error_type(exception: Exception, error_type: ErrorType) -> bool:
    """Check if exception matches the given error type"""
    error_str = str(exception).lower()
    
    if error_type == ErrorType.API_TIMEOUT:
        return any(keyword in error_str for keyword in ['timeout', 'deadline', 'timed out'])
    elif error_type == ErrorType.API_RATE_LIMIT:
        return any(keyword in error_str for keyword in ['rate limit', 'quota', 'too many requests'])
    elif error_type == ErrorType.NETWORK_ERROR:
        return any(keyword in error_str for keyword in ['connection', 'network', 'unreachable'])
    elif error_type == ErrorType.AUDIO_PROCESSING:
        return any(keyword in error_str for keyword in ['audio', 'speech', 'recording'])
    
    return False


class ErrorHandler:
    """Main error handler class for coordinating error responses"""
    
    def __init__(self):
        self.templates = ErrorResponseTemplates()
        self.retry_configs = {
            'api_calls': RetryConfig(max_attempts=3, base_delay=1.0),
            'audio_processing': RetryConfig(max_attempts=2, base_delay=0.5),
            'content_retrieval': RetryConfig(max_attempts=2, base_delay=0.3)
        }
    
    def handle_error(self, error: Exception, component: str, 
                    session_id: str = None, phone_number: str = None,
                    language: str = 'english') -> Dict[str, Any]:
        """
        Handle error and return appropriate response
        
        Args:
            error: The exception that occurred
            component: Component where error occurred
            session_id: Optional session ID
            phone_number: Optional phone number
            language: User's language preference
            
        Returns:
            Dictionary with error response details
        """
        # Categorize the error
        error_type = self._categorize_error(error)
        
        # Get appropriate response template
        response_template = self.templates.get_response(error_type)
        
        # Track the error
        error_id = error_tracker.track_error(
            component=component,
            error=error,
            session_id=session_id,
            phone_number=phone_number,
            recovery_action=response_template.recovery_action
        )
        
        # Log error with context
        logger.error(f"Error handled - {component} - {error_type.value}: {str(error)}")
        if phone_number:
            logger.error(f"  Phone: {phone_number}")
        if session_id:
            logger.error(f"  Session: {session_id}")
        
        return {
            'error_id': error_id,
            'error_type': error_type.value,
            'message': self.templates.get_message(error_type, language),
            'recovery_action': response_template.recovery_action,
            'retry_allowed': response_template.retry_allowed,
            'redirect_to_menu': response_template.redirect_to_menu,
            'component': component
        }
    
    def _categorize_error(self, error: Exception) -> ErrorType:
        """Categorize error based on exception details"""
        error_str = str(error).lower()
        
        # Check for specific error patterns
        if any(keyword in error_str for keyword in ['timeout', 'deadline exceeded']):
            return ErrorType.API_TIMEOUT
        elif any(keyword in error_str for keyword in ['rate limit', 'quota exceeded']):
            return ErrorType.API_RATE_LIMIT
        elif any(keyword in error_str for keyword in ['audio', 'speech', 'recording']):
            return ErrorType.AUDIO_PROCESSING
        elif any(keyword in error_str for keyword in ['no content', 'not found', 'no results']):
            return ErrorType.CONTENT_NOT_FOUND
        elif any(keyword in error_str for keyword in ['unclear', 'confidence', 'understand']):
            return ErrorType.UNCLEAR_SPEECH
        elif any(keyword in error_str for keyword in ['connection', 'network', 'unreachable']):
            return ErrorType.NETWORK_ERROR
        else:
            return ErrorType.SYSTEM_ERROR
    
    def get_fallback_response(self, error_type: ErrorType, language: str, 
                            context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Get fallback response for specific error type
        
        Args:
            error_type: Type of error
            language: User's language
            context: Additional context for response
            
        Returns:
            Fallback response dictionary
        """
        response_template = self.templates.get_response(error_type)
        
        return {
            'success': False,
            'error_type': error_type.value,
            'message': self.templates.get_message(error_type, language),
            'recovery_suggestions': self._get_recovery_suggestions(error_type, language),
            'retry_allowed': response_template.retry_allowed,
            'redirect_to_menu': response_template.redirect_to_menu
        }
    
    def _get_recovery_suggestions(self, error_type: ErrorType, language: str) -> List[str]:
        """Get recovery suggestions for error type"""
        suggestions = {
            ErrorType.UNCLEAR_SPEECH: {
                'english': [
                    "Speak slowly and clearly",
                    "Find a quieter place to call from",
                    "Hold the phone closer to your mouth"
                ],
                'telugu': [
                    "నెమ్మదిగా మరియు స్పష్టంగా మాట్లాడండి",
                    "కాల్ చేయడానికి నిశ్శబ్ద ప్రదేశాన్ని కనుగొనండి",
                    "ఫోన్‌ను మీ నోటికి దగ్గరగా పట్టుకోండి"
                ]
            },
            ErrorType.CONTENT_NOT_FOUND: {
                'english': [
                    "Ask about Physics topics like light and electricity",
                    "Try Chemistry questions about acids and metals",
                    "Ask Biology questions about plants and animals"
                ],
                'telugu': [
                    "వెలుతురు మరియు విద్యుత్ వంటి భౌతిక శాస్త్ర విషయాల గురించి అడగండి",
                    "ఆమ్లాలు మరియు లోహాల గురించి రసాయన శాస్త్ర ప్రశ్నలు ప్రయత్నించండి",
                    "మొక్కలు మరియు జంతువుల గురించి జీవ శాస్త్ర ప్రశ్నలు అడగండి"
                ]
            }
        }
        
        lang_key = 'telugu' if language.lower() == 'telugu' else 'english'
        return suggestions.get(error_type, {}).get(lang_key, [])


# Global error handler instance
error_handler = ErrorHandler()


def handle_error(error: Exception, component: str, **kwargs) -> Dict[str, Any]:
    """
    Convenience function to handle errors
    
    Args:
        error: Exception that occurred
        component: Component name
        **kwargs: Additional context (session_id, phone_number, language)
        
    Returns:
        Error response dictionary
    """
    return error_handler.handle_error(error, component, **kwargs)


def get_fallback_response(error_type: ErrorType, language: str = 'english', 
                         context: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Convenience function to get fallback responses
    
    Args:
        error_type: Type of error
        language: User's language
        context: Additional context
        
    Returns:
        Fallback response dictionary
    """
    return error_handler.get_fallback_response(error_type, language, context)