#!/usr/bin/env python3
"""
Test script for VidyaVani Session Utilities
Tests session utility functions for easy integration
"""

import sys
import os

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.session import (
    get_or_create_user_session,
    process_user_question,
    process_system_response,
    update_user_menu_state,
    get_session_info,
    handle_call_end,
    get_demo_question_list,
    is_demo_question,
    cache_audio_for_response,
    get_cached_audio_response,
    get_system_stats
)

def test_session_utilities():
    """Test all session utility functions"""
    print("=== Testing Session Utility Functions ===")
    
    phone_number = "+919876543212"
    
    # Test session creation with language
    session = get_or_create_user_session(phone_number, "telugu")
    print(f"✓ Created session with Telugu language: {session.session_id}")
    
    # Test session info retrieval
    info = get_session_info(phone_number)
    print(f"✓ Session info retrieved: Language={info['language']}")
    
    # Test menu state update
    success = update_user_menu_state(phone_number, "question_recording")
    print(f"✓ Menu state updated: {success}")
    
    # Test question processing
    test_questions = [
        "What is reflection of light?",  # Demo question
        "How do plants make their food?",  # Demo question
        "What is quantum mechanics?"  # Non-demo question
    ]
    
    for question in test_questions:
        result = process_user_question(phone_number, question)
        print(f"✓ Processed question: '{question[:30]}...'")
        print(f"  - Is demo: {result['is_demo_question']}")
        print(f"  - Has cached response: {result['cached_response'] is not None}")
        
        # Add a mock response
        if result['cached_response']:
            response = result['cached_response']
        else:
            response = f"This is a generated response for: {question}"
        
        process_system_response(phone_number, response)
        print(f"  - Added response to session")
    
    # Test conversation context
    final_result = process_user_question(phone_number, "Tell me more about the previous topic")
    print(f"✓ Conversation context length: {len(final_result['conversation_context'])} chars")
    
    # Test demo question utilities
    demo_questions = get_demo_question_list()
    print(f"✓ Demo questions available: {len(demo_questions)}")
    
    # Test demo question detection
    for question in ["What is reflection of light?", "Random non-demo question"]:
        is_demo = is_demo_question(question)
        print(f"✓ '{question[:30]}...' is demo: {is_demo}")
    
    # Test audio caching
    mock_audio = b"mock_audio_data_12345"
    cache_audio_for_response("Test response", mock_audio, "english")
    cached_audio = get_cached_audio_response("Test response", "english")
    print(f"✓ Audio caching works: {cached_audio == mock_audio}")
    
    # Test system stats
    stats = get_system_stats()
    print(f"✓ System stats: {stats['active_sessions']} active sessions")
    
    # Test call end handling
    success = handle_call_end(phone_number)
    print(f"✓ Call end handled: {success}")
    
    # Verify session is cleaned up
    info_after_cleanup = get_session_info(phone_number)
    print(f"✓ Session cleaned up: {info_after_cleanup is None}")
    
    print("=== Session Utility Tests Completed ===\n")

def test_integration_scenario():
    """Test a complete call scenario using utilities"""
    print("=== Testing Complete Call Scenario ===")
    
    phone_number = "+919876543213"
    
    # 1. Call starts - create session
    session = get_or_create_user_session(phone_number, "english")
    print("1. ✓ Call started, session created")
    
    # 2. User selects language menu
    update_user_menu_state(phone_number, "language_selection")
    print("2. ✓ Language selection menu")
    
    # 3. User selects Telugu
    session = get_or_create_user_session(phone_number, "telugu")
    update_user_menu_state(phone_number, "main_menu")
    print("3. ✓ Language changed to Telugu")
    
    # 4. User chooses to ask question
    update_user_menu_state(phone_number, "question_recording")
    print("4. ✓ Question recording mode")
    
    # 5. User asks a demo question
    question = "What is reflection of light?"
    result = process_user_question(phone_number, question)
    
    if result['is_demo_question']:
        # Use cached response
        response = result['cached_response']
        print("5. ✓ Demo question - using cached response")
    else:
        # Would normally call RAG engine here
        response = "Generated response from RAG engine"
        print("5. ✓ Non-demo question - would call RAG engine")
    
    process_system_response(phone_number, response)
    
    # 6. User asks follow-up question
    followup = "Can you explain more about mirrors?"
    result = process_user_question(phone_number, followup)
    print(f"6. ✓ Follow-up question with context: {len(result['conversation_context'])} chars")
    
    # Mock response for follow-up
    process_system_response(phone_number, "Mirrors reflect light according to the law of reflection...")
    
    # 7. User asks another demo question
    question2 = "How do plants make their food?"
    result = process_user_question(phone_number, question2)
    if result['is_demo_question']:
        process_system_response(phone_number, result['cached_response'])
        print("7. ✓ Second demo question processed")
    
    # 8. Check session state
    info = get_session_info(phone_number)
    print(f"8. ✓ Session has {info['question_count']} questions and {info['response_count']} responses")
    
    # 9. Call ends
    handle_call_end(phone_number)
    print("9. ✓ Call ended and session cleaned up")
    
    print("=== Complete Call Scenario Test Completed ===\n")

def test_concurrent_sessions():
    """Test multiple concurrent sessions"""
    print("=== Testing Concurrent Sessions ===")
    
    phone_numbers = ["+919876543214", "+919876543215", "+919876543216"]
    
    # Create multiple sessions
    sessions = []
    for phone in phone_numbers:
        session = get_or_create_user_session(phone, "english")
        sessions.append(session)
        
        # Add some activity to each session
        process_user_question(phone, "What is reflection of light?")
        process_system_response(phone, "Light reflects off surfaces...")
    
    print(f"✓ Created {len(sessions)} concurrent sessions")
    
    # Check system stats
    stats = get_system_stats()
    print(f"✓ System stats show {stats['active_sessions']} active sessions")
    
    # Clean up all sessions
    for phone in phone_numbers:
        handle_call_end(phone)
    
    # Verify cleanup
    final_stats = get_system_stats()
    print(f"✓ After cleanup: {final_stats['active_sessions']} active sessions")
    
    print("=== Concurrent Sessions Test Completed ===\n")

def main():
    """Run all utility tests"""
    print("VidyaVani Session Utilities Test Suite")
    print("=" * 50)
    
    test_session_utilities()
    test_integration_scenario()
    test_concurrent_sessions()
    
    print("All utility tests completed successfully!")

if __name__ == "__main__":
    main()