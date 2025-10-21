"""
Load balancing and concurrency management for VidyaVani IVR Learning System
"""

import os
import time
import threading
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from collections import deque
import asyncio
from concurrent.futures import ThreadPoolExecutor, as_completed

@dataclass
class RequestInfo:
    """Request information for load balancing"""
    request_id: str
    phone_number: str
    endpoint: str
    start_time: datetime
    priority: int = 1  # 1=normal, 2=high, 3=critical
    estimated_duration: float = 8.0  # seconds

@dataclass
class WorkerInfo:
    """Worker process information"""
    worker_id: str
    pid: int
    status: str  # idle, busy, overloaded, error
    current_requests: int
    total_requests: int
    last_activity: datetime
    cpu_usage: float = 0.0
    memory_usage: float = 0.0

class LoadBalancer:
    """Load balancing and request management"""
    
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Concurrency limits
        self.max_concurrent_requests = config.MAX_CONCURRENT_CALLS
        self.max_requests_per_worker = 2
        self.request_timeout = config.RESPONSE_TIMEOUT
        
        # Request tracking
        self.active_requests: Dict[str, RequestInfo] = {}
        self.request_queue: deque = deque()
        self.completed_requests: deque = deque(maxlen=1000)
        
        # Worker management
        self.workers: Dict[str, WorkerInfo] = {}
        self.worker_pool = ThreadPoolExecutor(
            max_workers=config.GUNICORN_WORKERS,
            thread_name_prefix="vidyavani_worker"
        )
        
        # Rate limiting
        self.rate_limit_window = 60  # seconds
        self.max_requests_per_minute = 30
        self.request_history: deque = deque(maxlen=100)
        
        # Circuit breaker
        self.circuit_breaker_enabled = True
        self.failure_threshold = 5
        self.recovery_timeout = 300  # 5 minutes
        self.circuit_state = 'closed'  # closed, open, half-open
        self.failure_count = 0
        self.last_failure_time = None
        
        # Load balancing metrics
        self.metrics = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'queued_requests': 0,
            'rejected_requests': 0,
            'average_response_time': 0.0,
            'peak_concurrent_requests': 0
        }
        
        # Monitoring thread
        self.monitoring_active = False
        self.monitoring_thread = None
        
    def start_monitoring(self):
        """Start load balancing monitoring"""
        if self.monitoring_active:
            return
        
        self.monitoring_active = True
        self.logger.info("Starting load balancer monitoring")
        
        def monitor_loop():
            while self.monitoring_active:
                try:
                    self._update_worker_status()
                    self._process_request_queue()
                    self._cleanup_completed_requests()
                    self._update_circuit_breaker()
                    self._update_metrics()
                    
                    time.sleep(1)  # Monitor every second
                    
                except Exception as e:
                    self.logger.error(f"Load balancer monitoring error: {str(e)}")
                    time.sleep(5)
        
        self.monitoring_thread = threading.Thread(target=monitor_loop, daemon=True)
        self.monitoring_thread.start()
    
    def stop_monitoring(self):
        """Stop load balancing monitoring"""
        self.monitoring_active = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
        self.logger.info("Load balancer monitoring stopped")
    
    def can_accept_request(self, phone_number: str) -> tuple[bool, str]:
        """Check if system can accept new request"""
        # Check circuit breaker
        if self.circuit_state == 'open':
            return False, "System temporarily unavailable (circuit breaker open)"
        
        # Check concurrent request limit
        if len(self.active_requests) >= self.max_concurrent_requests:
            return False, f"Maximum concurrent requests reached ({self.max_concurrent_requests})"
        
        # Check rate limiting
        if not self._check_rate_limit(phone_number):
            return False, "Rate limit exceeded"
        
        # Check if phone number already has active request
        for request in self.active_requests.values():
            if request.phone_number == phone_number:
                return False, "Request already in progress for this phone number"
        
        return True, "OK"
    
    def submit_request(self, request_info: RequestInfo) -> bool:
        """Submit request for processing"""
        try:
            # Check if request can be accepted
            can_accept, reason = self.can_accept_request(request_info.phone_number)
            
            if not can_accept:
                self.logger.warning(f"Request rejected: {reason}")
                self.metrics['rejected_requests'] += 1
                return False
            
            # Add to active requests
            self.active_requests[request_info.request_id] = request_info
            self.metrics['total_requests'] += 1
            
            # Update peak concurrent requests
            current_concurrent = len(self.active_requests)
            if current_concurrent > self.metrics['peak_concurrent_requests']:
                self.metrics['peak_concurrent_requests'] = current_concurrent
            
            # Add to request history for rate limiting
            self.request_history.append({
                'phone_number': request_info.phone_number,
                'timestamp': datetime.now()
            })
            
            self.logger.info(f"Request accepted: {request_info.request_id} ({current_concurrent}/{self.max_concurrent_requests})")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to submit request: {str(e)}")
            return False
    
    def complete_request(self, request_id: str, success: bool, response_time: float):
        """Mark request as completed"""
        try:
            if request_id not in self.active_requests:
                self.logger.warning(f"Request not found in active requests: {request_id}")
                return
            
            request_info = self.active_requests.pop(request_id)
            
            # Update metrics
            if success:
                self.metrics['successful_requests'] += 1
                self.failure_count = 0  # Reset failure count on success
            else:
                self.metrics['failed_requests'] += 1
                self.failure_count += 1
                self.last_failure_time = datetime.now()
            
            # Update average response time
            total_successful = self.metrics['successful_requests']
            if total_successful > 0:
                current_avg = self.metrics['average_response_time']
                self.metrics['average_response_time'] = (
                    (current_avg * (total_successful - 1) + response_time) / total_successful
                )
            
            # Add to completed requests
            self.completed_requests.append({
                'request_id': request_id,
                'phone_number': request_info.phone_number,
                'endpoint': request_info.endpoint,
                'start_time': request_info.start_time,
                'end_time': datetime.now(),
                'response_time': response_time,
                'success': success
            })
            
            self.logger.info(f"Request completed: {request_id} (success: {success}, time: {response_time:.2f}s)")
            
        except Exception as e:
            self.logger.error(f"Failed to complete request: {str(e)}")
    
    def _check_rate_limit(self, phone_number: str) -> bool:
        """Check rate limiting for phone number"""
        now = datetime.now()
        cutoff_time = now - timedelta(seconds=self.rate_limit_window)
        
        # Count recent requests from this phone number
        recent_requests = sum(
            1 for req in self.request_history
            if req['phone_number'] == phone_number and req['timestamp'] > cutoff_time
        )
        
        return recent_requests < self.max_requests_per_minute
    
    def _update_worker_status(self):
        """Update worker status information"""
        try:
            import psutil
            
            # Get current process info
            current_process = psutil.Process()
            
            # Update main worker info
            worker_id = f"worker_{current_process.pid}"
            
            if worker_id not in self.workers:
                self.workers[worker_id] = WorkerInfo(
                    worker_id=worker_id,
                    pid=current_process.pid,
                    status='idle',
                    current_requests=0,
                    total_requests=0,
                    last_activity=datetime.now()
                )
            
            worker = self.workers[worker_id]
            worker.current_requests = len(self.active_requests)
            worker.last_activity = datetime.now()
            worker.cpu_usage = current_process.cpu_percent()
            worker.memory_usage = current_process.memory_percent()
            
            # Determine worker status
            if worker.current_requests == 0:
                worker.status = 'idle'
            elif worker.current_requests <= self.max_requests_per_worker:
                worker.status = 'busy'
            else:
                worker.status = 'overloaded'
            
        except Exception as e:
            self.logger.debug(f"Worker status update failed: {str(e)}")
    
    def _process_request_queue(self):
        """Process queued requests"""
        # For now, we handle requests synchronously
        # In a more complex setup, this would distribute requests to available workers
        pass
    
    def _cleanup_completed_requests(self):
        """Clean up old completed requests"""
        # Completed requests are automatically limited by deque maxlen
        pass
    
    def _update_circuit_breaker(self):
        """Update circuit breaker state"""
        if not self.circuit_breaker_enabled:
            return
        
        now = datetime.now()
        
        if self.circuit_state == 'closed':
            # Check if we should open the circuit
            if self.failure_count >= self.failure_threshold:
                self.circuit_state = 'open'
                self.logger.warning(f"Circuit breaker opened due to {self.failure_count} failures")
        
        elif self.circuit_state == 'open':
            # Check if we should try half-open
            if (self.last_failure_time and 
                now - self.last_failure_time > timedelta(seconds=self.recovery_timeout)):
                self.circuit_state = 'half-open'
                self.logger.info("Circuit breaker moved to half-open state")
        
        elif self.circuit_state == 'half-open':
            # Check if we should close or re-open
            if self.failure_count == 0:
                self.circuit_state = 'closed'
                self.logger.info("Circuit breaker closed - system recovered")
            elif self.failure_count >= 1:
                self.circuit_state = 'open'
                self.logger.warning("Circuit breaker re-opened due to continued failures")
    
    def _update_metrics(self):
        """Update load balancing metrics"""
        self.metrics['queued_requests'] = len(self.request_queue)
    
    def get_load_status(self) -> Dict[str, Any]:
        """Get current load balancing status"""
        return {
            'active_requests': len(self.active_requests),
            'max_concurrent_requests': self.max_concurrent_requests,
            'queue_length': len(self.request_queue),
            'circuit_state': self.circuit_state,
            'failure_count': self.failure_count,
            'workers': {
                worker_id: {
                    'status': worker.status,
                    'current_requests': worker.current_requests,
                    'cpu_usage': worker.cpu_usage,
                    'memory_usage': worker.memory_usage
                }
                for worker_id, worker in self.workers.items()
            },
            'metrics': self.metrics.copy()
        }
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for monitoring"""
        total_requests = self.metrics['total_requests']
        
        return {
            'load_balancer': {
                'total_requests': total_requests,
                'success_rate': (
                    (self.metrics['successful_requests'] / max(1, total_requests)) * 100
                ),
                'average_response_time': self.metrics['average_response_time'],
                'concurrent_requests': len(self.active_requests),
                'peak_concurrent_requests': self.metrics['peak_concurrent_requests'],
                'rejected_requests': self.metrics['rejected_requests'],
                'circuit_breaker_state': self.circuit_state
            }
        }

class RequestMiddleware:
    """Flask middleware for load balancing"""
    
    def __init__(self, app, load_balancer):
        self.app = app
        self.load_balancer = load_balancer
        self.setup_middleware()
    
    def setup_middleware(self):
        """Setup Flask middleware for load balancing"""
        
        @self.app.before_request
        def before_request():
            from flask import g, request
            import uuid
            
            # Skip load balancing for health checks and static resources
            if request.endpoint in ['health_check', 'detailed_health_check']:
                return
            
            # Generate request info
            request_id = getattr(g, 'request_id', str(uuid.uuid4()))
            
            # Safely extract phone number
            phone_number = 'unknown'
            try:
                phone_number = (
                    request.form.get('From') or 
                    request.form.get('phone_number') or 
                    'unknown'
                )
                
                # Try JSON data if available and content-type is correct
                if request.is_json and request.json:
                    phone_number = request.json.get('phone_number') or phone_number
            except Exception:
                phone_number = 'unknown'
            
            # Determine priority
            priority = 1  # normal
            if request.endpoint and 'webhook' in request.endpoint:
                priority = 2  # high priority for IVR webhooks
            elif request.endpoint == 'process_question':
                priority = 3  # critical for question processing
            
            # Create request info
            request_info = RequestInfo(
                request_id=request_id,
                phone_number=phone_number,
                endpoint=request.endpoint or request.path,
                start_time=datetime.now(),
                priority=priority
            )
            
            # Submit request to load balancer
            if not self.load_balancer.submit_request(request_info):
                from flask import jsonify
                return jsonify({
                    'error': 'System overloaded',
                    'message': 'Please try again in a few moments',
                    'retry_after': 30
                }), 503
            
            # Store request info in Flask context
            g.load_balancer_request = request_info
        
        @self.app.after_request
        def after_request(response):
            from flask import g
            
            # Complete request in load balancer
            if hasattr(g, 'load_balancer_request'):
                request_info = g.load_balancer_request
                
                # Calculate response time
                response_time = (datetime.now() - request_info.start_time).total_seconds()
                
                # Determine success
                success = 200 <= response.status_code < 400
                
                # Complete request
                self.load_balancer.complete_request(
                    request_info.request_id,
                    success,
                    response_time
                )
            
            return response

# Global load balancer instance
load_balancer = None

def get_load_balancer(config):
    """Get or create global load balancer instance"""
    global load_balancer
    if load_balancer is None:
        load_balancer = LoadBalancer(config)
    return load_balancer

def setup_load_balancing(app, config):
    """Setup load balancing for Flask app"""
    lb = get_load_balancer(config)
    RequestMiddleware(app, lb)
    lb.start_monitoring()
    return lb