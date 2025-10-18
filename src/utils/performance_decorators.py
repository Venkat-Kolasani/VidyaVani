"""
Performance Monitoring Decorators for VidyaVani IVR Learning System

This module provides decorators to easily add performance tracking to functions
and methods throughout the system.
"""

import functools
import time
import logging
from typing import Callable, Any, Optional

from .performance_tracker import performance_tracker
from .logging_config import performance_logger

logger = logging.getLogger(__name__)

def track_performance(component_name: str, track_api_usage: bool = False, 
                     service_name: str = None, estimate_cost: bool = False):
    """
    Decorator to track performance metrics for a function or method
    
    Args:
        component_name: Name of the component being tracked
        track_api_usage: Whether to track this as an API usage
        service_name: Service name for API tracking (required if track_api_usage=True)
        estimate_cost: Whether to estimate API costs
    
    Usage:
        @track_performance("STT_Processing")
        def speech_to_text(self, audio_data):
            # Function implementation
            pass
        
        @track_performance("OpenAI_GPT", track_api_usage=True, service_name="openai_gpt", estimate_cost=True)
        def generate_response(self, prompt):
            # API call implementation
            pass
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # Start timing
            timing_id = performance_tracker.start_component_timing(component_name)
            start_time = time.time()
            
            success = False
            error_message = None
            tokens_used = 0
            estimated_cost = 0.0
            
            try:
                # Execute the function
                result = func(*args, **kwargs)
                success = True
                
                # Extract metrics from result if it's a structured response
                if hasattr(result, 'success'):
                    success = result.success
                    if hasattr(result, 'error_message'):
                        error_message = result.error_message
                
                # Extract token usage for API calls
                if track_api_usage and hasattr(result, 'tokens_used'):
                    tokens_used = result.tokens_used
                
                return result
                
            except Exception as e:
                success = False
                error_message = str(e)
                logger.error(f"Performance tracking caught error in {component_name}: {e}")
                raise
                
            finally:
                # End timing and record metrics
                duration = time.time() - start_time
                performance_tracker.end_component_timing(timing_id, success, error_message)
                
                # Track API usage if requested
                if track_api_usage and service_name:
                    # Estimate cost for OpenAI services
                    if estimate_cost and service_name.startswith('openai'):
                        estimated_cost = _estimate_openai_cost(service_name, tokens_used)
                    
                    performance_tracker.track_api_usage(
                        service=service_name,
                        success=success,
                        tokens_used=tokens_used,
                        estimated_cost=estimated_cost
                    )
                
                # Log performance details
                performance_logger.log_response_time(component_name, duration)
                
                if track_api_usage:
                    performance_logger.log_api_call(
                        service=service_name or component_name,
                        endpoint=func.__name__,
                        duration=duration,
                        status="SUCCESS" if success else "FAILED",
                        tokens_used=tokens_used,
                        estimated_cost=estimated_cost
                    )
        
        return wrapper
    return decorator

def track_cache_usage(cache_name: str):
    """
    Decorator to track cache hit/miss rates
    
    Args:
        cache_name: Name of the cache being tracked
    
    Usage:
        @track_cache_usage("response_cache")
        def get_cached_response(self, key):
            # Returns (result, hit) tuple or result with .cache_hit attribute
            pass
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            result = func(*args, **kwargs)
            
            # Determine if it was a cache hit
            cache_hit = False
            
            if isinstance(result, tuple) and len(result) == 2:
                # Assume (result, hit) tuple format
                actual_result, cache_hit = result
            elif hasattr(result, 'cache_hit'):
                # Result object with cache_hit attribute
                cache_hit = result.cache_hit
                actual_result = result
            elif result is not None:
                # Non-None result assumed to be cache hit
                cache_hit = True
                actual_result = result
            else:
                # None result assumed to be cache miss
                cache_hit = False
                actual_result = result
            
            # Track cache usage
            performance_tracker.track_cache_usage(cache_name, cache_hit)
            performance_logger.log_cache_hit(cache_name, str(hash(str(args) + str(kwargs)))[:8], cache_hit)
            
            return actual_result
        
        return wrapper
    return decorator

def track_session_activity(session_id_param: str = 'session_id', phone_param: str = 'phone_number'):
    """
    Decorator to track session-level activity
    
    Args:
        session_id_param: Name of the session ID parameter
        phone_param: Name of the phone number parameter
    
    Usage:
        @track_session_activity()
        def process_question(self, session_id, phone_number, question):
            # Processing implementation
            pass
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # Extract session information
            session_id = kwargs.get(session_id_param)
            phone_number = kwargs.get(phone_param)
            
            # If not in kwargs, try to extract from args based on function signature
            if not session_id or not phone_number:
                try:
                    import inspect
                    sig = inspect.signature(func)
                    bound_args = sig.bind(*args, **kwargs)
                    bound_args.apply_defaults()
                    
                    session_id = session_id or bound_args.arguments.get(session_id_param)
                    phone_number = phone_number or bound_args.arguments.get(phone_param)
                except Exception:
                    pass
            
            start_time = time.time()
            success = False
            
            try:
                result = func(*args, **kwargs)
                success = True
                
                # Check if result indicates success/failure
                if hasattr(result, 'success'):
                    success = result.success
                
                return result
                
            except Exception as e:
                success = False
                raise
                
            finally:
                # Track question processing if we have session info
                if session_id:
                    processing_time = time.time() - start_time
                    performance_tracker.track_question_processing(session_id, success, processing_time)
                    
                    if phone_number:
                        performance_logger.log_processing_pipeline(
                            phone_number, func.__name__, processing_time, success
                        )
        
        return wrapper
    return decorator

def _estimate_openai_cost(service_name: str, tokens_used: int) -> float:
    """
    Estimate cost for OpenAI API calls
    
    Args:
        service_name: OpenAI service name
        tokens_used: Number of tokens used
        
    Returns:
        Estimated cost in USD
    """
    # Pricing as of 2024 (approximate, for tracking purposes)
    pricing = {
        'openai_gpt': {
            'gpt-4o-mini': {'input': 0.00015, 'output': 0.0006},  # per 1K tokens
            'gpt-5-nano': {'input': 0.0001, 'output': 0.0004}     # estimated pricing
        },
        'openai_embeddings': {
            'text-embedding-3-small': 0.00002  # per 1K tokens
        }
    }
    
    if service_name == 'openai_gpt':
        # Assume roughly 50/50 input/output split for simplicity
        model_pricing = pricing['openai_gpt'].get('gpt-5-nano', pricing['openai_gpt']['gpt-4o-mini'])
        input_cost = (tokens_used * 0.5 / 1000) * model_pricing['input']
        output_cost = (tokens_used * 0.5 / 1000) * model_pricing['output']
        return input_cost + output_cost
        
    elif service_name == 'openai_embeddings':
        return (tokens_used / 1000) * pricing['openai_embeddings']['text-embedding-3-small']
    
    return 0.0

# Context manager for tracking processing pipelines
class PipelineTracker:
    """
    Context manager for tracking multi-stage processing pipelines
    
    Usage:
        with PipelineTracker("question_processing", phone_number) as tracker:
            # STT stage
            tracker.start_stage("stt")
            stt_result = process_speech_to_text(audio)
            tracker.end_stage("stt", stt_result.success)
            
            # RAG stage
            tracker.start_stage("rag")
            rag_result = generate_response(question)
            tracker.end_stage("rag", rag_result.success)
            
            # TTS stage
            tracker.start_stage("tts")
            tts_result = text_to_speech(response)
            tracker.end_stage("tts", tts_result.success)
    """
    
    def __init__(self, pipeline_name: str, phone_number: str = None):
        self.pipeline_name = pipeline_name
        self.phone_number = phone_number
        self.stages = {}
        self.current_stage = None
        self.pipeline_start_time = None
    
    def __enter__(self):
        self.pipeline_start_time = time.time()
        logger.info(f"Starting pipeline tracking: {self.pipeline_name}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        total_time = time.time() - self.pipeline_start_time
        success = exc_type is None
        
        logger.info(f"Pipeline {self.pipeline_name} completed in {total_time:.3f}s - "
                   f"{'SUCCESS' if success else 'FAILED'}")
        
        # Log stage breakdown
        for stage_name, stage_info in self.stages.items():
            performance_logger.log_processing_pipeline(
                self.phone_number or "unknown",
                f"{self.pipeline_name}_{stage_name}",
                stage_info['duration'],
                stage_info['success']
            )
    
    def start_stage(self, stage_name: str):
        """Start timing a pipeline stage"""
        if self.current_stage:
            logger.warning(f"Starting stage {stage_name} while {self.current_stage} is still active")
        
        self.current_stage = stage_name
        self.stages[stage_name] = {
            'start_time': time.time(),
            'duration': 0.0,
            'success': False
        }
        
        logger.debug(f"Pipeline stage started: {stage_name}")
    
    def end_stage(self, stage_name: str, success: bool = True):
        """End timing a pipeline stage"""
        if stage_name not in self.stages:
            logger.warning(f"Ending stage {stage_name} that was never started")
            return
        
        stage_info = self.stages[stage_name]
        stage_info['duration'] = time.time() - stage_info['start_time']
        stage_info['success'] = success
        
        if self.current_stage == stage_name:
            self.current_stage = None
        
        logger.debug(f"Pipeline stage completed: {stage_name} - {stage_info['duration']:.3f}s - "
                    f"{'SUCCESS' if success else 'FAILED'}")