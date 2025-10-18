"""
Error Tracking and Recovery for VidyaVani IVR Learning System

This module provides enhanced error tracking, categorization, and recovery
suggestions for debugging during demo preparation.
"""

import logging
import traceback
import hashlib
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from collections import defaultdict, deque
import json
import os

logger = logging.getLogger(__name__)

@dataclass
class ErrorEvent:
    """Represents an error event with context"""
    timestamp: datetime
    component: str
    error_type: str
    error_message: str
    stack_trace: Optional[str] = None
    session_id: Optional[str] = None
    phone_number: Optional[str] = None
    recovery_action: Optional[str] = None
    resolved: bool = False

class ErrorTracker:
    """
    Comprehensive error tracking system for debugging and monitoring
    """
    
    def __init__(self):
        self.error_events: List[ErrorEvent] = []
        self.error_counts = defaultdict(int)
        self.component_errors = defaultdict(list)
        self.recent_errors = deque(maxlen=100)  # Keep last 100 errors
        
        # Error categorization patterns
        self.error_patterns = {
            'api_timeout': ['timeout', 'deadline exceeded', 'connection timeout'],
            'api_rate_limit': ['rate limit', 'quota exceeded', 'too many requests'],
            'audio_processing': ['audio', 'speech', 'tts', 'stt', 'recording'],
            'openai_error': ['openai', 'gpt', 'completion', 'embedding'],
            'google_cloud_error': ['google', 'cloud', 'speech', 'texttospeech'],
            'exotel_error': ['exotel', 'webhook', 'ivr', 'call'],
            'session_error': ['session', 'phone_number', 'user'],
            'content_error': ['content', 'rag', 'retrieval', 'context'],
            'storage_error': ['storage', 'file', 'audio_storage', 'upload']
        }
        
        # Recovery suggestions for common error types
        self.recovery_suggestions = {
            'api_timeout': [
                'Check network connectivity',
                'Verify API service status',
                'Increase timeout values',
                'Implement retry logic with exponential backoff'
            ],
            'api_rate_limit': [
                'Implement request queuing',
                'Add rate limiting to prevent hitting limits',
                'Use caching to reduce API calls',
                'Consider upgrading API plan'
            ],
            'audio_processing': [
                'Check audio format and quality',
                'Verify Google Cloud credentials',
                'Test with sample audio files',
                'Check audio codec compatibility'
            ],
            'openai_error': [
                'Verify OpenAI API key',
                'Check API usage limits',
                'Validate request format',
                'Test with simpler prompts'
            ],
            'google_cloud_error': [
                'Verify Google Cloud credentials',
                'Check service account permissions',
                'Validate audio format for STT/TTS',
                'Test with Google Cloud console'
            ],
            'exotel_error': [
                'Verify Exotel webhook URLs',
                'Check Exotel account credentials',
                'Validate XML response format',
                'Test webhook endpoints manually'
            ],
            'session_error': [
                'Check session creation logic',
                'Verify phone number format',
                'Clear session cache if corrupted',
                'Check session timeout settings'
            ],
            'content_error': [
                'Verify NCERT content is loaded',
                'Check FAISS index integrity',
                'Test semantic search functionality',
                'Validate content chunk format'
            ],
            'storage_error': [
                'Check file system permissions',
                'Verify storage directory exists',
                'Test audio file upload/download',
                'Check disk space availability'
            ]
        }
    
    def track_error(self, component: str, error: Exception, 
                   session_id: str = None, phone_number: str = None,
                   recovery_action: str = None) -> str:
        """
        Track an error event with full context
        
        Args:
            component: Component where error occurred
            error: The exception object
            session_id: Optional session identifier
            phone_number: Optional phone number
            recovery_action: Optional recovery action taken
            
        Returns:
            Error ID for tracking
        """
        error_type = self._categorize_error(str(error))
        
        error_event = ErrorEvent(
            timestamp=datetime.now(),
            component=component,
            error_type=error_type,
            error_message=str(error),
            stack_trace=traceback.format_exc(),
            session_id=session_id,
            phone_number=phone_number,
            recovery_action=recovery_action
        )
        
        # Store error
        self.error_events.append(error_event)
        self.recent_errors.append(error_event)
        self.error_counts[error_type] += 1
        self.component_errors[component].append(error_event)
        
        # Log error with context (anonymizing phone number for privacy)
        logger.error(f"ERROR_TRACKED - {component} - {error_type}: {str(error)}")
        if session_id:
            logger.error(f"  Session: {session_id}")
        if phone_number:
            # Hash phone number for privacy compliance
            phone_hash = hashlib.sha256(phone_number.encode()).hexdigest()[:8]
            logger.error(f"  Phone: {phone_hash}")
        if recovery_action:
            logger.info(f"  Recovery: {recovery_action}")
        
        return f"{component}_{error_type}_{int(error_event.timestamp.timestamp())}"
    
    def _categorize_error(self, error_message: str) -> str:
        """
        Categorize error based on message content
        
        Args:
            error_message: Error message to categorize
            
        Returns:
            Error category string
        """
        error_lower = error_message.lower()
        
        for category, patterns in self.error_patterns.items():
            if any(pattern in error_lower for pattern in patterns):
                return category
        
        return 'unknown_error'
    
    def get_recovery_suggestions(self, error_type: str) -> List[str]:
        """
        Get recovery suggestions for an error type
        
        Args:
            error_type: Type of error
            
        Returns:
            List of recovery suggestions
        """
        return self.recovery_suggestions.get(error_type, [
            'Check system logs for more details',
            'Verify all configuration settings',
            'Test individual components',
            'Contact support if issue persists'
        ])
    
    def get_error_summary(self, hours: int = 24) -> Dict[str, Any]:
        """
        Get error summary for the specified time period
        
        Args:
            hours: Number of hours to look back
            
        Returns:
            Error summary dictionary
        """
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_errors = [
            error for error in self.error_events 
            if error.timestamp > cutoff_time
        ]
        
        # Count errors by type
        error_type_counts = defaultdict(int)
        component_counts = defaultdict(int)
        
        for error in recent_errors:
            error_type_counts[error.error_type] += 1
            component_counts[error.component] += 1
        
        # Find most problematic components
        top_error_types = sorted(
            error_type_counts.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:5]
        
        top_components = sorted(
            component_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]
        
        return {
            'time_period_hours': hours,
            'total_errors': len(recent_errors),
            'unique_error_types': len(error_type_counts),
            'top_error_types': top_error_types,
            'top_problematic_components': top_components,
            'recent_errors': [
                {
                    'timestamp': error.timestamp.isoformat(),
                    'component': error.component,
                    'error_type': error.error_type,
                    'message': error.error_message[:100] + '...' if len(error.error_message) > 100 else error.error_message,
                    'session_id': error.session_id,
                    'phone_hash': hashlib.sha256(error.phone_number.encode()).hexdigest()[:8] if error.phone_number else None,
                    'recovery_action': error.recovery_action
                }
                for error in recent_errors[-10:]  # Last 10 errors
            ]
        }
    
    def get_debugging_report(self) -> Dict[str, Any]:
        """
        Generate comprehensive debugging report
        
        Returns:
            Debugging report with error analysis and suggestions
        """
        summary = self.get_error_summary(24)
        
        # Generate specific recommendations
        recommendations = []
        
        for error_type, count in summary['top_error_types']:
            suggestions = self.get_recovery_suggestions(error_type)
            recommendations.append({
                'error_type': error_type,
                'occurrence_count': count,
                'priority': 'high' if count > 5 else 'medium' if count > 2 else 'low',
                'suggestions': suggestions[:3]  # Top 3 suggestions
            })
        
        # System health assessment
        total_errors = summary['total_errors']
        if total_errors == 0:
            health_status = 'excellent'
        elif total_errors < 5:
            health_status = 'good'
        elif total_errors < 15:
            health_status = 'fair'
        else:
            health_status = 'poor'
        
        return {
            'report_timestamp': datetime.now().isoformat(),
            'system_health': health_status,
            'error_summary': summary,
            'recommendations': recommendations,
            'next_steps': self._get_next_steps(health_status, summary)
        }
    
    def _get_next_steps(self, health_status: str, summary: Dict[str, Any]) -> List[str]:
        """
        Get recommended next steps based on system health
        
        Args:
            health_status: Current system health status
            summary: Error summary
            
        Returns:
            List of recommended next steps
        """
        if health_status == 'excellent':
            return [
                'System is running smoothly',
                'Continue monitoring for any new issues',
                'Consider performance optimizations'
            ]
        elif health_status == 'good':
            return [
                'Address minor issues to prevent escalation',
                'Review error patterns for optimization opportunities',
                'Test error recovery mechanisms'
            ]
        elif health_status == 'fair':
            return [
                'Investigate top error types immediately',
                'Implement additional error handling',
                'Consider increasing monitoring frequency',
                'Review system configuration'
            ]
        else:  # poor
            return [
                'URGENT: Address critical errors immediately',
                'Check all external service connections',
                'Verify all configuration settings',
                'Consider rolling back recent changes',
                'Implement emergency fallback procedures'
            ]
    
    def export_error_report(self, filepath: str = None) -> str:
        """
        Export comprehensive error report to file
        
        Args:
            filepath: Optional file path for export
            
        Returns:
            Path to exported file
        """
        if filepath is None:
            os.makedirs('logs', exist_ok=True)
            filepath = f"logs/error_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        report = self.get_debugging_report()
        
        try:
            with open(filepath, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            
            logger.info(f"Error report exported to: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Failed to export error report: {e}")
            raise
    
    def clear_old_errors(self, days: int = 7):
        """
        Clear errors older than specified days
        
        Args:
            days: Number of days to retain errors
        """
        cutoff_time = datetime.now() - timedelta(days=days)
        
        original_count = len(self.error_events)
        self.error_events = [
            error for error in self.error_events 
            if error.timestamp > cutoff_time
        ]
        
        cleared_count = original_count - len(self.error_events)
        if cleared_count > 0:
            logger.info(f"Cleared {cleared_count} old error events")

# Global error tracker instance
error_tracker = ErrorTracker()

def track_error(component: str, error: Exception, **kwargs) -> str:
    """
    Convenience function to track errors
    
    Args:
        component: Component name where error occurred
        error: Exception object
        **kwargs: Additional context (session_id, phone_number, recovery_action)
        
    Returns:
        Error tracking ID
    """
    return error_tracker.track_error(component, error, **kwargs)