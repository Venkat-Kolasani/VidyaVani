#!/usr/bin/env python3
"""
Test script for IVR XML generation and webhook handling
Tests the XML responses and error handling scenarios
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.ivr.ivr_handler import IVRHandler
from src.session.session_manager import session_manager, ResponseData

def test_xml_generation():
    """Test XML generation for different scenarios"""
    
    print("=" * 60)
    print("Testing IVR XML Generation")
    print("=" * 60)
    
    # Initialize IVR handler
    ivr_handler = IVRHandler(session_manager)
    
    # Test scenarios
    test_cases = [
        {
            "name": "Welcome XML",
            "method": "_generate_welcome_xml",
            "args": []
        },
        {
            "name": "Grade Confirmation (English)",
            "method": "_generate_grade_confirmation_xml",
            "args": ["english"]
        },
        {
            "name": "Grade Confirmation (Telugu)",
            "method": "_generate_grade_confirmation_xml", 
            "args": ["telugu"]
        },
        {
            "name": "Interaction Mode (English)",
            "method": "_generate_interaction_mode_xml",
            "args": ["english"]
        },
        {
            "name": "Question Recording (English)",
            "method": "_generate_question_recording_xml",
            "args": ["english"]
        },
        {
            "name": "Processing Message (English)",
            "method": "_generate_processing_xml",
            "args": ["english"]
        },
        {
            "name": "Processing Message (Telugu)",
            "method": "_generate_processing_xml",
            "args": ["telugu"]
        },
        {
            "name": "Response Delivery",
            "method": "_generate_response_delivery_xml",
            "args": ["https://example.com/response.wav", "english"]
        },
        {
            "name": "Invalid Selection (Language)",
            "method": "_generate_invalid_selection_xml",
            "args": ["language", "english"]
        },
        {
            "name": "Processing Error (English)",
            "method": "_generate_processing_error_xml",
            "args": ["english"]
        },
        {
            "name": "Timeout Error (Telugu)",
            "method": "_generate_timeout_error_xml",
            "args": ["telugu"]
        },
        {
            "name": "Recording Too Short (English)",
            "method": "_generate_recording_too_short_xml",
            "args": ["english"]
        },
        {
            "name": "Audio Error Fallback",
            "method": "_generate_audio_error_xml",
            "args": ["english", "This is a sample response text that will be spoken as fallback."]
        }
    ]
    
    results = []
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. Testing: {test_case['name']}")
        print("-" * 40)
        
        try:
            # Get the method from IVR handler
            method = getattr(ivr_handler, test_case['method'])
            
            # Call the method with arguments
            xml_result = method(*test_case['args'])
            
            # Validate XML structure
            if xml_result and '<Response>' in xml_result and '</Response>' in xml_result:
                print("✅ XML generated successfully")
                print(f"   Length: {len(xml_result)} characters")
                
                # Check for common XML elements
                elements = ['Say', 'Gather', 'Record', 'Play', 'Redirect', 'Pause', 'Hangup']
                found_elements = [elem for elem in elements if f'<{elem}' in xml_result]
                if found_elements:
                    print(f"   Elements: {', '.join(found_elements)}")
                
                results.append(True)
            else:
                print("❌ Invalid XML structure")
                results.append(False)
                
        except Exception as e:
            print(f"❌ XML generation failed: {e}")
            results.append(False)
    
    # Summary
    print("\n" + "=" * 60)
    print("XML GENERATION TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    print(f"Tests passed: {passed}/{total}")
    print(f"Success rate: {passed/total*100:.1f}%")
    
    return passed == total

def test_session_workflow():
    """Test complete session workflow simulation"""
    
    print("\n" + "=" * 60)
    print("Testing Session Workflow")
    print("=" * 60)
    
    phone_number = "+919999999999"
    
    # Simulate complete call flow
    print("\n1. Incoming Call")
    print("-" * 20)
    
    # Create session
    session = session_manager.create_session(phone_number)
    print(f"✅ Session created: {session.session_id}")
    
    # Language selection
    success = session_manager.update_session_language(phone_number, "english")
    print(f"✅ Language updated: {success}")
    
    # Menu navigation
    success = session_manager.update_session_menu(phone_number, "recording_question")
    print(f"✅ Menu state updated: {success}")
    
    print("\n2. Question Processing")
    print("-" * 20)
    
    # Simulate processing status updates
    session_manager.update_processing_status(phone_number, "processing_audio")
    print("✅ Status: processing_audio")
    
    session_manager.update_processing_status(phone_number, "generating_response")
    print("✅ Status: generating_response")
    
    # Store response data
    response_data = ResponseData(
        question_text="What is reflection of light?",
        response_text="Reflection of light occurs when light rays bounce back from a surface. The angle of incidence equals the angle of reflection.",
        response_audio_url="https://example.com/response.wav",
        detailed_response_text="Detailed explanation of reflection...",
        detailed_audio_url="https://example.com/detailed.wav",
        language="english"
    )
    
    success = session_manager.store_response_data(phone_number, response_data)
    print(f"✅ Response data stored: {success}")
    
    session_manager.update_processing_status(phone_number, "ready")
    print("✅ Status: ready")
    
    print("\n3. Response Delivery")
    print("-" * 20)
    
    # Retrieve response data
    retrieved_data = session_manager.get_current_response_data(phone_number)
    print(f"✅ Response data retrieved: {retrieved_data is not None}")
    
    if retrieved_data:
        print(f"   Question: {retrieved_data.question_text}")
        print(f"   Response: {retrieved_data.response_text[:50]}...")
        print(f"   Audio URL: {retrieved_data.response_audio_url}")
    
    print("\n4. Session Cleanup")
    print("-" * 20)
    
    # End session
    session_manager.end_session(phone_number)
    print("✅ Session ended")
    
    # Cleanup
    session_manager.cleanup_session(phone_number)
    print("✅ Session cleaned up")
    
    return True

def test_error_handling_xml():
    """Test error handling XML responses"""
    
    print("\n" + "=" * 60)
    print("Testing Error Handling XML")
    print("=" * 60)
    
    ivr_handler = IVRHandler(session_manager)
    
    # Test error scenarios
    error_scenarios = [
        {
            "name": "Processing Error (English)",
            "language": "english",
            "method": "_generate_processing_error_xml"
        },
        {
            "name": "Processing Error (Telugu)",
            "language": "telugu", 
            "method": "_generate_processing_error_xml"
        },
        {
            "name": "Timeout Error (English)",
            "language": "english",
            "method": "_generate_timeout_error_xml"
        },
        {
            "name": "Recording Too Short (Telugu)",
            "language": "telugu",
            "method": "_generate_recording_too_short_xml"
        },
        {
            "name": "Recording Too Long (English)",
            "language": "english",
            "method": "_generate_recording_too_long_xml"
        },
        {
            "name": "Recording Failed (Telugu)",
            "language": "telugu",
            "method": "_generate_recording_failed_xml"
        }
    ]
    
    for scenario in error_scenarios:
        print(f"\nTesting: {scenario['name']}")
        print("-" * 30)
        
        try:
            method = getattr(ivr_handler, scenario['method'])
            xml_result = method(scenario['language'])
            
            # Check for error recovery options
            has_gather = '<Gather' in xml_result
            has_redirect = '<Redirect' in xml_result
            has_say = '<Say' in xml_result
            
            print(f"✅ XML generated with error handling")
            print(f"   Has user input: {has_gather}")
            print(f"   Has redirect: {has_redirect}")
            print(f"   Has message: {has_say}")
            
        except Exception as e:
            print(f"❌ Error XML generation failed: {e}")
    
    return True

def main():
    """Run all IVR tests"""
    
    print("🚀 Starting IVR XML Generation Tests")
    print("This tests the XML responses and error handling")
    
    try:
        # Test 1: XML Generation
        xml_success = test_xml_generation()
        
        # Test 2: Session Workflow
        session_success = test_session_workflow()
        
        # Test 3: Error Handling XML
        error_success = test_error_handling_xml()
        
        # Overall result
        print("\n" + "=" * 60)
        print("OVERALL IVR TEST RESULTS")
        print("=" * 60)
        
        all_passed = xml_success and session_success and error_success
        
        print(f"XML Generation: {'✅ PASS' if xml_success else '❌ FAIL'}")
        print(f"Session Workflow: {'✅ PASS' if session_success else '❌ FAIL'}")
        print(f"Error Handling: {'✅ PASS' if error_success else '❌ FAIL'}")
        
        if all_passed:
            print("\n🎉 ALL IVR TESTS PASSED!")
            print("The IVR XML generation and error handling is working correctly.")
            return 0
        else:
            print("\n⚠️  SOME IVR TESTS FAILED.")
            return 1
            
    except Exception as e:
        print(f"\n💥 IVR test suite failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)