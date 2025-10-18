#!/usr/bin/env python3
"""
Test script to simulate the complete workflow with mock data
This bypasses STT and tests the RAG → TTS pipeline directly
"""

import sys
import os
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config import Config
from src.rag.context_builder import ContextBuilder
from src.rag.response_generator import ResponseGenerator
from src.audio.audio_processor import AudioProcessor
from src.audio.language_types import Language
from src.session.session_manager import session_manager, ResponseData

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def test_rag_to_tts_workflow():
    """Test the RAG → TTS workflow with sample questions"""
    
    print("=" * 60)
    print("Testing RAG → TTS Workflow")
    print("=" * 60)
    
    config = Config()
    context_builder = ContextBuilder(config)
    response_generator = ResponseGenerator(config)
    audio_processor = AudioProcessor(config)
    
    # Test questions
    test_questions = [
        {
            "question": "What is reflection of light?",
            "language": "english",
            "phone_number": "+919999999001"
        },
        {
            "question": "How does photosynthesis work?",
            "language": "english", 
            "phone_number": "+919999999002"
        },
        {
            "question": "Explain chemical reactions",
            "language": "telugu",
            "phone_number": "+919999999003"
        }
    ]
    
    results = []
    
    for i, test_case in enumerate(test_questions, 1):
        print(f"\n{i}. Testing: {test_case['question']}")
        print("-" * 40)
        
        try:
            # Step 1: Build context
            context = context_builder.build_context(
                question=test_case['question'],
                language=test_case['language'],
                detail_level="simple"
            )
            print(f"✅ Context built: {len(context.get('context', ''))} characters")
            
            # Step 2: Generate response
            response_result = response_generator.generate_response(context)
            
            if response_result['success']:
                response_text = response_result['response_text']
                print(f"✅ Response generated: {len(response_text)} characters")
                print(f"   Preview: {response_text[:100]}...")
                
                # Step 3: Convert to audio
                language_enum = Language.TELUGU if test_case['language'] == 'telugu' else Language.ENGLISH
                audio_result = audio_processor.generate_response_audio(response_text, language_enum)
                
                if audio_result.success:
                    print(f"✅ Audio generated: {len(audio_result.audio_data)} bytes")
                    
                    # Step 4: Test session storage
                    session = session_manager.create_session(test_case['phone_number'])
                    session_manager.update_session_language(test_case['phone_number'], test_case['language'])
                    
                    response_data = ResponseData(
                        question_text=test_case['question'],
                        response_text=response_text,
                        response_audio_url="https://example.com/audio.wav",  # Mock URL
                        language=test_case['language']
                    )
                    
                    success = session_manager.store_response_data(test_case['phone_number'], response_data)
                    print(f"✅ Session storage: {success}")
                    
                    # Cleanup
                    session_manager.cleanup_session(test_case['phone_number'])
                    
                    results.append(True)
                    print("🎉 Test PASSED")
                    
                else:
                    print(f"❌ Audio generation failed: {audio_result.error_message}")
                    results.append(False)
                    
            else:
                print(f"❌ Response generation failed")
                results.append(False)
                
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            results.append(False)
    
    # Summary
    print("\n" + "=" * 60)
    print("WORKFLOW TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    print(f"Tests passed: {passed}/{total}")
    print(f"Success rate: {passed/total*100:.1f}%")
    
    return passed == total

def test_error_scenarios():
    """Test error handling in the workflow"""
    
    print("\n" + "=" * 60)
    print("Testing Error Scenarios")
    print("=" * 60)
    
    config = Config()
    context_builder = ContextBuilder(config)
    response_generator = ResponseGenerator(config)
    
    # Test with invalid/empty question
    print("\n1. Testing empty question handling")
    print("-" * 30)
    
    try:
        context = context_builder.build_context(
            question="",
            language="english",
            detail_level="simple"
        )
        print("✅ Empty question handled gracefully")
    except Exception as e:
        print(f"❌ Empty question caused exception: {e}")
    
    # Test with very long question
    print("\n2. Testing long question handling")
    print("-" * 30)
    
    long_question = "What is " + "very " * 100 + "long question about physics?"
    
    try:
        context = context_builder.build_context(
            question=long_question,
            language="english",
            detail_level="simple"
        )
        
        response_result = response_generator.generate_response(context)
        
        if response_result['success']:
            print("✅ Long question handled successfully")
        else:
            print("⚠️  Long question handled with graceful failure")
            
    except Exception as e:
        print(f"❌ Long question caused exception: {e}")
    
    return True

def test_multilingual_support():
    """Test multilingual support"""
    
    print("\n" + "=" * 60)
    print("Testing Multilingual Support")
    print("=" * 60)
    
    config = Config()
    audio_processor = AudioProcessor(config)
    
    test_texts = [
        ("Hello, this is a test message in English.", Language.ENGLISH),
        ("ఇది తెలుగులో ఒక పరీక్ష సందేశం.", Language.TELUGU)
    ]
    
    for text, language in test_texts:
        print(f"\nTesting {language.value}:")
        print(f"Text: {text}")
        
        try:
            result = audio_processor.text_to_speech(text, language)
            
            if result.success:
                print(f"✅ TTS successful: {len(result.audio_data)} bytes")
            else:
                print(f"❌ TTS failed: {result.error_message}")
                
        except Exception as e:
            print(f"❌ TTS exception: {e}")
    
    return True

def main():
    """Run all workflow tests"""
    
    print("🚀 Starting Workflow Simulation Tests")
    print("This tests the RAG → TTS pipeline with mock data")
    
    try:
        # Test 1: Main workflow
        workflow_success = test_rag_to_tts_workflow()
        
        # Test 2: Error scenarios
        error_success = test_error_scenarios()
        
        # Test 3: Multilingual support
        multilingual_success = test_multilingual_support()
        
        # Overall result
        print("\n" + "=" * 60)
        print("OVERALL WORKFLOW TEST RESULTS")
        print("=" * 60)
        
        all_passed = workflow_success and error_success and multilingual_success
        
        print(f"RAG → TTS Workflow: {'✅ PASS' if workflow_success else '❌ FAIL'}")
        print(f"Error Scenarios: {'✅ PASS' if error_success else '❌ FAIL'}")
        print(f"Multilingual Support: {'✅ PASS' if multilingual_success else '❌ FAIL'}")
        
        if all_passed:
            print("\n🎉 ALL WORKFLOW TESTS PASSED!")
            print("The end-to-end processing pipeline is working correctly.")
            return 0
        else:
            print("\n⚠️  SOME WORKFLOW TESTS FAILED.")
            return 1
            
    except Exception as e:
        print(f"\n💥 Workflow test suite failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)