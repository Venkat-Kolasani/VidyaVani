"""
Performance Tracking and Metrics Collection for VidyaVani IVR Learning System

This module provides comprehensive performance tracking for all system components
including response times, API usage, cache performance, and error rates.
"""

import logging
import time
import threading
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict, deque
import json
import os

logger = logging.getLogger(__name__)

@dataclass
class ComponentMetrics:
    """Metrics for individual system components"""
    component_name: str
    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    total_response_time: float = 0.0
    min_response_time: float = float('inf')
    max_response_time: float = 0.0
    recent_response_times: deque = field(default_factory=lambda: deque(maxlen=100))
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage"""
        if self.total_calls == 0:
            return 0.0
        return (self.successful_calls / self.total_calls) * 100
    
    @property
    def average_response_time(self) -> float:
        """Calculate average response time"""
        if self.successful_calls == 0:
            return 0.0
        return self.total_response_time / self.successful_calls
    
    @property
    def recent_average_response_time(self) -> float:
        """Calculate average of recent response times"""
        if not self.recent_response_times:
            return 0.0
        return sum(self.recent_response_times) / len(self.recent_response_times)

@dataclass
class APIUsageMetrics:
    """Track API usage and costs"""
    service_name: str
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_tokens_used: int = 0
    estimated_cost: float = 0.0
    rate_limit_hits: int = 0
    last_request_time: Optional[datetime] = None
    
    @property
    def success_rate(self) -> float:
        """Calculate API success rate"""
        if self.total_requests == 0:
            return 0.0
        return (self.successful_requests / self.total_requests) * 100

@dataclass
class CacheMetrics:
    """Track cache performance"""
    cache_name: str
    total_requests: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    
    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate percentage"""
        if self.total_requests == 0:
            return 0.0
        return (self.cache_hits / self.total_requests) * 100

@dataclass
class SessionMetrics:
    """Track session-level metrics"""
    session_id: str
    phone_number: str
    start_time: datetime
    end_time: Optional[datetime] = None
    language: str = "english"
    total_questions: int = 0
    successful_responses: int = 0
    failed_responses: int = 0
    total_processing_time: float = 0.0
    
    @property
    def session_duration(self) -> float:
        """Calculate session duration in seconds"""
        end = self.end_time or datetime.now()
        return (end - self.start_time).total_seconds()
    
    @property
    def success_rate(self) -> float:
        """Calculate session success rate"""
        if self.total_questions == 0:
            return 0.0
        return (self.successful_responses / self.total_questions) * 100

class PerformanceTracker:
    """
    Comprehensive performance tracking system for VidyaVani
    
    Tracks response times, API usage, cache performance, and system metrics
    with thread-safe operations and configurable retention policies.
    """
    
    def __init__(self, config=None):
        """Initialize performance tracker"""
        self.config = config
        self._lock = threading.Lock()
        
        # Component metrics
        self.component_metrics: Dict[str, ComponentMetrics] = {}
        
        # API usage tracking
        self.api_metrics: Dict[str, APIUsageMetrics] = {
            'openai_gpt': APIUsageMetrics('OpenAI GPT'),
            'openai_embeddings': APIUsageMetrics('OpenAI Embeddings'),
            'google_stt': APIUsageMetrics('Google Speech-to-Text'),
            'google_tts': APIUsageMetrics('Google Text-to-Speech'),
            'exotel': APIUsageMetrics('Exotel IVR')
        }
        
        # Cache performance tracking
        self.cache_metrics: Dict[str, CacheMetrics] = {
            'response_cache': CacheMetrics('Response Cache'),
            'audio_cache': CacheMetrics('Audio Cache'),
            'session_cache': CacheMetrics('Session Cache'),
            'demo_cache': CacheMetrics('Demo Cache')
        }
        
        # Session tracking
        self.session_metrics: Dict[str, SessionMetrics] = {}
        
        # System-wide metrics
        self.system_metrics = {
            'total_calls': 0,
            'concurrent_calls': 0,
            'max_concurrent_calls': 0,
            'total_processing_time': 0.0,
            'system_start_time': datetime.now(),
            'last_activity_time': datetime.now()
        }
        
        # Performance alerts
        self.performance_alerts = []
        self.alert_thresholds = {
            'response_time_warning': 8.0,  # seconds
            'response_time_critical': 12.0,  # seconds
            'success_rate_warning': 90.0,  # percentage
            'success_rate_critical': 80.0,  # percentage
            'api_usage_warning': 80.0,  # percentage of limit
            'api_usage_critical': 95.0  # percentage of limit
        }
        
        logger.info("Performance tracker initialized")
    
    def start_component_timing(self, component_name: str) -> str:
        """
        Start timing for a component operation
        
        Args:
            component_name: Name of the component being timed
            
        Returns:
            Timing ID for use with end_component_timing
        """
        timing_id = f"{component_name}_{int(time.time() * 1000000)}"
        
        with self._lock:
            if component_name not in self.component_metrics:
                self.component_metrics[component_name] = ComponentMetrics(component_name)
            
            # Store start time
            if not hasattr(self, '_active_timings'):
                self._active_timings = {}
            self._active_timings[timing_id] = {
                'component': component_name,
                'start_time': time.time()
            }
        
        return timing_id
    
    def end_component_timing(self, timing_id: str, success: bool = True, error_message: str = None):
        """
        End timing for a component operation
        
        Args:
            timing_id: Timing ID from start_component_timing
            success: Whether the operation was successful
            error_message: Optional error message if operation failed
        """
        end_time = time.time()
        
        with self._lock:
            if not hasattr(self, '_active_timings') or timing_id not in self._active_timings:
                logger.warning(f"No active timing found for ID: {timing_id}")
                return
            
            timing_info = self._active_timings.pop(timing_id)
            component_name = timing_info['component']
            start_time = timing_info['start_time']
            duration = end_time - start_time
            
            metrics = self.component_metrics[component_name]
            metrics.total_calls += 1
            
            if success:
                metrics.successful_calls += 1
                metrics.total_response_time += duration
                metrics.min_response_time = min(metrics.min_response_time, duration)
                metrics.max_response_time = max(metrics.max_response_time, duration)
                metrics.recent_response_times.append(duration)
                
                # Log performance info
                logger.info(f"PERF - {component_name}: {duration:.3f}s - SUCCESS")
                
                # Check for performance alerts
                self._check_performance_alerts(component_name, duration, success)
            else:
                metrics.failed_calls += 1
                logger.warning(f"PERF - {component_name}: {duration:.3f}s - FAILED: {error_message}")
                
                # Check for performance alerts
                self._check_performance_alerts(component_name, duration, success)
    
    def track_api_usage(self, service: str, success: bool, tokens_used: int = 0, 
                       estimated_cost: float = 0.0, rate_limited: bool = False):
        """
        Track API usage metrics
        
        Args:
            service: API service name (openai_gpt, google_stt, etc.)
            success: Whether the API call was successful
            tokens_used: Number of tokens used (for OpenAI)
            estimated_cost: Estimated cost of the API call
            rate_limited: Whether the call hit rate limits
        """
        with self._lock:
            if service not in self.api_metrics:
                self.api_metrics[service] = APIUsageMetrics(service)
            
            metrics = self.api_metrics[service]
            metrics.total_requests += 1
            metrics.last_request_time = datetime.now()
            
            if success:
                metrics.successful_requests += 1
            else:
                metrics.failed_requests += 1
            
            if tokens_used > 0:
                metrics.total_tokens_used += tokens_used
            
            if estimated_cost > 0:
                metrics.estimated_cost += estimated_cost
            
            if rate_limited:
                metrics.rate_limit_hits += 1
            
            logger.info(f"API - {service}: {'SUCCESS' if success else 'FAILED'} - "
                       f"Tokens: {tokens_used}, Cost: ${estimated_cost:.4f}")
    
    def track_cache_usage(self, cache_name: str, hit: bool):
        """
        Track cache hit/miss metrics
        
        Args:
            cache_name: Name of the cache
            hit: Whether it was a cache hit (True) or miss (False)
        """
        with self._lock:
            if cache_name not in self.cache_metrics:
                self.cache_metrics[cache_name] = CacheMetrics(cache_name)
            
            metrics = self.cache_metrics[cache_name]
            metrics.total_requests += 1
            
            if hit:
                metrics.cache_hits += 1
            else:
                metrics.cache_misses += 1
            
            logger.info(f"CACHE - {cache_name}: {'HIT' if hit else 'MISS'} - "
                       f"Hit rate: {metrics.hit_rate:.1f}%")
    
    def start_session_tracking(self, session_id: str, phone_number: str, language: str = "english"):
        """
        Start tracking metrics for a session
        
        Args:
            session_id: Unique session identifier
            phone_number: Phone number for the session
            language: Session language
        """
        with self._lock:
            self.session_metrics[session_id] = SessionMetrics(
                session_id=session_id,
                phone_number=phone_number,
                start_time=datetime.now(),
                language=language
            )
            
            # Update system metrics
            self.system_metrics['total_calls'] += 1
            self.system_metrics['concurrent_calls'] += 1
            self.system_metrics['max_concurrent_calls'] = max(
                self.system_metrics['max_concurrent_calls'],
                self.system_metrics['concurrent_calls']
            )
            self.system_metrics['last_activity_time'] = datetime.now()
        
        logger.info(f"SESSION - Started tracking: {session_id} ({phone_number})")
    
    def end_session_tracking(self, session_id: str):
        """
        End tracking for a session
        
        Args:
            session_id: Session identifier to end tracking for
        """
        with self._lock:
            if session_id in self.session_metrics:
                session = self.session_metrics[session_id]
                session.end_time = datetime.now()
                
                # Update system metrics
                self.system_metrics['concurrent_calls'] = max(0, 
                    self.system_metrics['concurrent_calls'] - 1)
                self.system_metrics['total_processing_time'] += session.total_processing_time
                
                logger.info(f"SESSION - Ended tracking: {session_id} - "
                           f"Duration: {session.session_duration:.1f}s, "
                           f"Questions: {session.total_questions}, "
                           f"Success rate: {session.success_rate:.1f}%")
    
    def track_question_processing(self, session_id: str, success: bool, processing_time: float):
        """
        Track question processing metrics for a session
        
        Args:
            session_id: Session identifier
            success: Whether processing was successful
            processing_time: Time taken to process the question
        """
        with self._lock:
            if session_id in self.session_metrics:
                session = self.session_metrics[session_id]
                session.total_questions += 1
                session.total_processing_time += processing_time
                
                if success:
                    session.successful_responses += 1
                else:
                    session.failed_responses += 1
                
                logger.info(f"QUESTION - {session_id}: {processing_time:.3f}s - "
                           f"{'SUCCESS' if success else 'FAILED'}")
    
    def _check_performance_alerts(self, component_name: str, duration: float, success: bool):
        """
        Check for performance alerts and log warnings
        
        Args:
            component_name: Name of the component
            duration: Response time duration
            success: Whether the operation was successful
        """
        # Response time alerts
        if duration > self.alert_thresholds['response_time_critical']:
            alert = {
                'type': 'response_time_critical',
                'component': component_name,
                'duration': duration,
                'threshold': self.alert_thresholds['response_time_critical'],
                'timestamp': datetime.now()
            }
            self.performance_alerts.append(alert)
            logger.critical(f"ALERT - Critical response time: {component_name} took {duration:.3f}s")
            
        elif duration > self.alert_thresholds['response_time_warning']:
            alert = {
                'type': 'response_time_warning',
                'component': component_name,
                'duration': duration,
                'threshold': self.alert_thresholds['response_time_warning'],
                'timestamp': datetime.now()
            }
            self.performance_alerts.append(alert)
            logger.warning(f"ALERT - Slow response time: {component_name} took {duration:.3f}s")
        
        # Success rate alerts
        if component_name in self.component_metrics:
            metrics = self.component_metrics[component_name]
            success_rate = metrics.success_rate
            
            if success_rate < self.alert_thresholds['success_rate_critical']:
                alert = {
                    'type': 'success_rate_critical',
                    'component': component_name,
                    'success_rate': success_rate,
                    'threshold': self.alert_thresholds['success_rate_critical'],
                    'timestamp': datetime.now()
                }
                self.performance_alerts.append(alert)
                logger.critical(f"ALERT - Critical success rate: {component_name} at {success_rate:.1f}%")
                
            elif success_rate < self.alert_thresholds['success_rate_warning']:
                alert = {
                    'type': 'success_rate_warning',
                    'component': component_name,
                    'success_rate': success_rate,
                    'threshold': self.alert_thresholds['success_rate_warning'],
                    'timestamp': datetime.now()
                }
                self.performance_alerts.append(alert)
                logger.warning(f"ALERT - Low success rate: {component_name} at {success_rate:.1f}%")
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """
        Get comprehensive performance summary
        
        Returns:
            Dictionary containing all performance metrics
        """
        with self._lock:
            # Component metrics summary
            component_summary = {}
            for name, metrics in self.component_metrics.items():
                component_summary[name] = {
                    'total_calls': metrics.total_calls,
                    'success_rate': metrics.success_rate,
                    'average_response_time': metrics.average_response_time,
                    'recent_average_response_time': metrics.recent_average_response_time,
                    'min_response_time': metrics.min_response_time if metrics.min_response_time != float('inf') else 0,
                    'max_response_time': metrics.max_response_time
                }
            
            # API metrics summary
            api_summary = {}
            for name, metrics in self.api_metrics.items():
                api_summary[name] = {
                    'total_requests': metrics.total_requests,
                    'success_rate': metrics.success_rate,
                    'total_tokens_used': metrics.total_tokens_used,
                    'estimated_cost': metrics.estimated_cost,
                    'rate_limit_hits': metrics.rate_limit_hits
                }
            
            # Cache metrics summary
            cache_summary = {}
            for name, metrics in self.cache_metrics.items():
                cache_summary[name] = {
                    'total_requests': metrics.total_requests,
                    'hit_rate': metrics.hit_rate,
                    'cache_hits': metrics.cache_hits,
                    'cache_misses': metrics.cache_misses
                }
            
            # Active sessions summary
            active_sessions = len([s for s in self.session_metrics.values() if s.end_time is None])
            
            # Recent alerts (last 24 hours)
            recent_alerts = [
                alert for alert in self.performance_alerts
                if alert['timestamp'] > datetime.now() - timedelta(hours=24)
            ]
            
            return {
                'system_metrics': self.system_metrics.copy(),
                'component_metrics': component_summary,
                'api_metrics': api_summary,
                'cache_metrics': cache_summary,
                'session_summary': {
                    'total_sessions': len(self.session_metrics),
                    'active_sessions': active_sessions,
                    'concurrent_calls': self.system_metrics['concurrent_calls']
                },
                'recent_alerts': recent_alerts,
                'uptime_seconds': (datetime.now() - self.system_metrics['system_start_time']).total_seconds()
            }
    
    def export_metrics_to_file(self, filepath: str = None):
        """
        Export metrics to JSON file
        
        Args:
            filepath: Optional file path, defaults to logs/performance_metrics.json
        """
        if filepath is None:
            os.makedirs('logs', exist_ok=True)
            filepath = f"logs/performance_metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        try:
            summary = self.get_performance_summary()
            
            # Convert datetime objects to strings for JSON serialization
            def convert_datetime(obj):
                if isinstance(obj, datetime):
                    return obj.isoformat()
                elif isinstance(obj, dict):
                    return {k: convert_datetime(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [convert_datetime(item) for item in obj]
                return obj
            
            summary = convert_datetime(summary)
            
            with open(filepath, 'w') as f:
                json.dump(summary, f, indent=2)
            
            logger.info(f"Performance metrics exported to: {filepath}")
            
        except Exception as e:
            logger.error(f"Failed to export metrics: {e}")
    
    def reset_metrics(self):
        """Reset all metrics (useful for testing)"""
        with self._lock:
            self.component_metrics.clear()
            for metrics in self.api_metrics.values():
                metrics.total_requests = 0
                metrics.successful_requests = 0
                metrics.failed_requests = 0
                metrics.total_tokens_used = 0
                metrics.estimated_cost = 0.0
                metrics.rate_limit_hits = 0
            
            for metrics in self.cache_metrics.values():
                metrics.total_requests = 0
                metrics.cache_hits = 0
                metrics.cache_misses = 0
            
            self.session_metrics.clear()
            self.performance_alerts.clear()
            
            self.system_metrics.update({
                'total_calls': 0,
                'concurrent_calls': 0,
                'max_concurrent_calls': 0,
                'total_processing_time': 0.0,
                'system_start_time': datetime.now(),
                'last_activity_time': datetime.now()
            })
        
        logger.info("All performance metrics reset")

# Global performance tracker instance
performance_tracker = PerformanceTracker()