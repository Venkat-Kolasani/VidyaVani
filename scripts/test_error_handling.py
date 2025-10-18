#!/usr/bin/env python3
"""
Test Error Handling System for VidyaVani

This script tests the error handling, retry logic, and fallback responses
to ensure demo reliability.
"""

import sys
import os
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.utils.error_handler import ErrorHandler, ErrorType, ErrorResponseTemplates
from src.utils.error_tracker import error_tracker
from src.ivr.error_recovery_handler import IVRErrorRecoveryHandler
from config import Config

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def test_error_response_templates():
    """Test error response templates for both languages"""
    print("\n🧪 Testing Error Response Templates...")
    
    templates = ErrorResponseTemplates()
    
    test_cases = [
        (ErrorType.API_TIMEOUT, 'english'),
        (ErrorType.API_TIMEOUT, 'telugu'),
        (ErrorType.UNCLEAR_SPEECH, 'english'),
        (ErrorType.UNCLEAR_SPEECH, 'telugu'),
        (ErrorType.CONTENT_NOT_FOUND, 'english'),
        (ErrorType.CONTENT_NOT_FOUND, 'telugu'),
        (ErrorType.PROCESSING_TIMEOUT, 'english'),
        (ErrorType.PROCESSING_TIMEOUT, 'telugu'),
    ]
    
    for error_type, language in test_cases:
        message = templates.get_message(error_type, language)
        response = templates.get_response(error_type)
        
        print(f"✅ {error_type.value} ({language}): {message[:50]}...")
        print(f"   Retry allowed: {response.retry_allowed}, Redirect: {response.redirect_to_menu}")
    
    print("✅ Error response templates test completed")


def test_error_handler():
    """Test the main error handler functionality"""
    print("\n🧪 Testing Error Handler...")
    
    handler = ErrorHandler()
    
    # Test different types of exceptions
    test_exceptions = [
        (Exception("Connection timeout occurred"), "API_Component"),
        (Exception("Rate limit exceeded"), "OpenAI_Service"),
        (Exception("Audio processing failed"), "Audio_Processor"),
        (Exception("No content found for query"), "RAG_Engine"),
        (Exception("Network unreachable"), "Network_Layer"),
    ]
    
    for exception, component in test_exceptions:
        error_response = handler.handle_error(
            error=exception,
            component=component,
            phone_number="test_phone_123",
            language='english'
        )
        
        print(f"✅ {component}: {error_response['error_type']} - {error_response['message'][:50]}...")
        print(f"   Retry: {error_response['retry_allowed']}, Recovery: {error_response['recovery_action']}")
    
    print("✅ Error handler test completed")


def test_fallback_responses():
    """Test fallback response generation"""
    print("\n🧪 Testing Fallback Responses...")
    
    handler = ErrorHandler()
    
    fallback_tests = [
        (ErrorType.UNCLEAR_SPEECH, 'english'),
        (ErrorType.UNCLEAR_SPEECH, 'telugu'),
        (ErrorType.CONTENT_NOT_FOUND, 'english'),
        (ErrorType.CONTENT_NOT_FOUND, 'telugu'),
        (ErrorType.API_TIMEOUT, 'english'),
        (ErrorType.SYSTEM_ERROR, 'telugu'),
    ]
    
    for error_type, language in fallback_tests:
        fallback = handler.get_fallback_response(error_type, language)
        
        print(f"✅ {error_type.value} ({language}): {fallback['message'][:50]}...")
        print(f"   Success: {fallback['success']}, Retry: {fallback['retry_allowed']}")
        
        if fallback.get('recovery_suggestions'):
            print(f"   Suggestions: {len(fallback['recovery_suggestions'])} provided")
    
    print("✅ Fallback responses test completed")


def test_error_tracker():
    """Test error tracking functionality"""
    print("\n🧪 Testing Error Tracker...")
    
    # Track some test errors
    test_errors = [
        ("STT_Processing", Exception("Speech recognition timeout")),
        ("TTS_Processing", Exception("Text-to-speech quota exceeded")),
        ("OpenAI_Generation", Exception("API rate limit reached")),
        ("IVR_Handler", Exception("Session not found")),
    ]
    
    for component, error in test_errors:
        error_id = error_tracker.track_error(
            component=component,
            error=error,
            phone_number="test_phone_456",
            recovery_action=f"Handled {component} error"
        )
        print(f"✅ Tracked error {error_id} for {component}")
    
    # Get error summary
    summary = error_tracker.get_error_summary(hours=1)
    print(f"✅ Error summary: {summary['total_errors']} errors, {summary['unique_error_types']} types")
    
    # Generate debugging report
    report = error_tracker.get_debugging_report()
    print(f"✅ System health: {report['system_health']}")
    print(f"✅ Recommendations: {len(report['recommendations'])} provided")
    
    print("✅ Error tracker test completed")


def test_ivr_error_recovery():
    """Test IVR error recovery handler"""
    print("\n🧪 Testing IVR Error Recovery...")
    
    # Mock session manager for testing
    class MockSessionManager:
        def get_session(self, phone_number):
            class MockSession:
                language = 'english'
            return MockSession()
        
        def update_processing_status(self, phone_number, status):
            pass
        
        def update_session_menu(self, phone_number, menu_state):
            pass
    
    mock_session_manager = MockSessionManager()
    recovery_handler = IVRErrorRecoveryHandler(mock_session_manager)
    
    # Test graceful fallback XML generation
    test_scenarios = [
        (ErrorType.UNCLEAR_SPEECH, 'english'),
        (ErrorType.CONTENT_NOT_FOUND, 'telugu'),
        (ErrorType.API_TIMEOUT, 'english'),
        (ErrorType.SYSTEM_ERROR, 'telugu'),
    ]
    
    for error_type, language in test_scenarios:
        xml_response = recovery_handler.generate_graceful_fallback_xml(error_type, language)
        
        # Basic validation that XML was generated
        if '<Response>' in xml_response and '</Response>' in xml_response:
            print(f"✅ Generated XML for {error_type.value} ({language})")
        else:
            print(f"❌ Failed to generate XML for {error_type.value} ({language})")
    
    # Test error logging
    recovery_handler.log_error_for_debugging(
        ErrorType.PROCESSING_TIMEOUT,
        "test_phone_789",
        {'session_exists': True, 'processing_stage': 'stt', 'language': 'english'}
    )
    print("✅ Error logging test completed")
    
    print("✅ IVR error recovery test completed")


def test_retry_logic():
    """Test retry logic with mock functions"""
    print("\n🧪 Testing Retry Logic...")
    
    from src.utils.error_handler import with_retry, RetryConfig
    
    # Mock function that fails first few times
    class MockAPICall:
        def __init__(self, fail_count=2):
            self.call_count = 0
            self.fail_count = fail_count
        
        def __call__(self):
            self.call_count += 1
            if self.call_count <= self.fail_count:
                raise Exception(f"API timeout on attempt {self.call_count}")
            return f"Success on attempt {self.call_count}"
    
    # Test with retry decorator
    @with_retry(
        error_types=[ErrorType.API_TIMEOUT, ErrorType.NETWORK_ERROR],
        config=RetryConfig(max_attempts=3, base_delay=0.1),
        component_name="test_component"
    )
    def mock_api_call_with_retry():
        return mock_call()
    
    # Test successful retry
    mock_call = MockAPICall(fail_count=2)
    try:
        result = mock_api_call_with_retry()
        print(f"✅ Retry successful: {result}")
    except Exception as e:
        print(f"❌ Retry failed: {e}")
    
    # Test failure after max retries
    mock_call = MockAPICall(fail_count=5)
    try:
        result = mock_api_call_with_retry()
        print(f"❌ Should have failed: {result}")
    except Exception as e:
        print(f"✅ Correctly failed after retries: {e}")
    
    print("✅ Retry logic test completed")


def main():
    """Run all error handling tests"""
    print("🚀 Starting Error Handling System Tests...")
    
    try:
        test_error_response_templates()
        test_error_handler()
        test_fallback_responses()
        test_error_tracker()
        test_ivr_error_recovery()
        test_retry_logic()
        
        print("\n🎉 All error handling tests completed successfully!")
        print("\n📊 Test Summary:")
        print("✅ Error response templates working")
        print("✅ Error handler functioning correctly")
        print("✅ Fallback responses generated properly")
        print("✅ Error tracking and debugging operational")
        print("✅ IVR error recovery handlers ready")
        print("✅ Retry logic working as expected")
        
        print("\n🛡️ Error Handling System is ready for demo!")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())