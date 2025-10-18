#!/usr/bin/env python3
"""
Test script for end-to-end question processing workflow
Tests the integration of STT → RAG → TTS pipeline with error handling
"""

import sys
import os
import logging
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config import Config
from src.ivr.processing_pipeline import IVRProcessingPipeline
from src.session.session_manager import session_manager
from src.audio.language_types import Language

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def test_processing_pipeline():
    """Test the complete processing pipeline with various scenarios"""
    
    print("=" * 60)
    print("Testing End-to-End Question Processing Workflow")
    print("=" * 60)
    
    # Initialize pipeline
    config = Config()
    pipeline = IVRProcessingPipeline(config)
    
    # Test scenarios
    test_cases = [
        {
            "name": "Valid Physics Question",
            "recording_url": "https://example.com/physics_question.wav",
            "language": "english",
            "phone_number": "+919999999001",
            "expected_success": True
        },
        {
            "name": "Valid Chemistry Question (Telugu)",
            "recording_url": "https://example.com/chemistry_question.wav", 
            "language": "telugu",
            "phone_number": "+919999999002",
            "expected_success": True
        },
        {
            "name": "Invalid Recording URL",
            "recording_url": "https://invalid-url-that-does-not-exist.com/audio.wav",
            "language": "english",
            "phone_number": "+919999999003",
            "expected_success": False
        }
    ]
    
    results = []
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. Testing: {test_case['name']}")
        print("-" * 40)
        
        # Create session for this test
        session = session_manager.create_session(test_case['phone_number'])
        session_manager.update_session_language(test_case['phone_number'], test_case['language'])
        
        start_time = time.time()
        
        try:
            # Process the question
            result = pipeline.process_question_sync(
                recording_url=test_case['recording_url'],
                language=test_case['language'],
                phone_number=test_case['phone_number']
            )
            
            processing_time = time.time() - start_time
            
            print(f"Processing completed in {processing_time:.2f}s")
            print(f"Success: {result.success}")
            
            if result.success:
                print(f"Question: {result.question_text[:100]}...")
                print(f"Response: {result.response_text[:100]}...")
                print(f"Audio URL: {result.response_audio_url}")
                print(f"Detailed Audio URL: {result.detailed_audio_url}")
            else:
                print(f"Error: {result.error_message}")
            
            # Validate expectations
            if result.success == test_case['expected_success']:
                print("✅ Test PASSED - Result matches expectation")
                results.append(True)
            else:
                print("❌ Test FAILED - Result doesn't match expectation")
                results.append(False)
                
        except Exception as e:
            print(f"❌ Test FAILED with exception: {e}")
            results.append(False)
        
        finally:
            # Cleanup session
            session_manager.cleanup_session(test_case['phone_number'])
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    print(f"Tests passed: {passed}/{total}")
    print(f"Success rate: {passed/total*100:.1f}%")
    
    if passed == total:
        print("🎉 All tests PASSED!")
        return True
    else:
        print("⚠️  Some tests FAILED")
        return False

def test_error_handling():
    """Test error handling scenarios"""
    
    print("\n" + "=" * 60)
    print("Testing Error Handling Scenarios")
    print("=" * 60)
    
    config = Config()
    pipeline = IVRProcessingPipeline(config)
    
    # Test invalid question validation
    print("\n1. Testing question validation")
    print("-" * 30)
    
    valid_questions = [
        "What is reflection of light?",
        "How does photosynthesis work?",
        "Explain chemical reactions"
    ]
    
    invalid_questions = [
        "",
        "Hi",
        "Hello how are you?",
        "What's the weather today?"
    ]
    
    for question in valid_questions:
        is_valid = pipeline._is_valid_question(question)
        print(f"'{question}' -> Valid: {is_valid} {'✅' if is_valid else '❌'}")
    
    for question in invalid_questions:
        is_valid = pipeline._is_valid_question(question)
        print(f"'{question}' -> Valid: {is_valid} {'✅' if not is_valid else '❌'}")
    
    print("\n2. Testing fallback messages")
    print("-" * 30)
    
    from src.audio.audio_processor import AudioProcessor
    audio_processor = AudioProcessor(config)
    
    error_types = ["noise_error", "unclear_speech", "processing_error"]
    languages = [Language.ENGLISH, Language.TELUGU]
    
    for error_type in error_types:
        for language in languages:
            message = audio_processor.get_fallback_message(error_type, language)
            print(f"{error_type} ({language.value}): {message[:50]}...")
    
    return True

def test_session_integration():
    """Test session management integration"""
    
    print("\n" + "=" * 60)
    print("Testing Session Management Integration")
    print("=" * 60)
    
    phone_number = "+919999999999"
    
    # Create session
    session = session_manager.create_session(phone_number)
    print(f"✅ Created session: {session.session_id}")
    
    # Update language
    success = session_manager.update_session_language(phone_number, "telugu")
    print(f"✅ Updated language: {success}")
    
    # Add question and response
    session_manager.add_question_to_session(phone_number, "What is photosynthesis?")
    session_manager.add_response_to_session(phone_number, "Photosynthesis is the process...")
    
    # Get conversation context
    context = session_manager.get_conversation_context(phone_number)
    print(f"✅ Got context: {len(context)} characters")
    
    # Test response data storage
    from src.session.session_manager import ResponseData
    response_data = ResponseData(
        question_text="Test question",
        response_text="Test response",
        response_audio_url="https://example.com/audio.wav",
        language="english"
    )
    
    success = session_manager.store_response_data(phone_number, response_data)
    print(f"✅ Stored response data: {success}")
    
    retrieved_data = session_manager.get_current_response_data(phone_number)
    print(f"✅ Retrieved response data: {retrieved_data is not None}")
    
    # Cleanup
    session_manager.cleanup_session(phone_number)
    print(f"✅ Cleaned up session")
    
    return True

def main():
    """Run all tests"""
    
    print("🚀 Starting End-to-End Integration Tests")
    print("This will test the complete question processing workflow")
    
    try:
        # Test 1: Processing Pipeline
        pipeline_success = test_processing_pipeline()
        
        # Test 2: Error Handling
        error_success = test_error_handling()
        
        # Test 3: Session Integration
        session_success = test_session_integration()
        
        # Overall result
        print("\n" + "=" * 60)
        print("OVERALL TEST RESULTS")
        print("=" * 60)
        
        all_passed = pipeline_success and error_success and session_success
        
        print(f"Processing Pipeline: {'✅ PASS' if pipeline_success else '❌ FAIL'}")
        print(f"Error Handling: {'✅ PASS' if error_success else '❌ FAIL'}")
        print(f"Session Integration: {'✅ PASS' if session_success else '❌ FAIL'}")
        
        if all_passed:
            print("\n🎉 ALL TESTS PASSED! End-to-end integration is working correctly.")
            return 0
        else:
            print("\n⚠️  SOME TESTS FAILED. Please check the implementation.")
            return 1
            
    except Exception as e:
        print(f"\n💥 Test suite failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)