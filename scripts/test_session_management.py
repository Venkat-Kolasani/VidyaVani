#!/usr/bin/env python3
"""
Test script for VidyaVani Session Management
Tests session creation, management, and demo question caching
"""

import sys
import os
import requests
import json
import time

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.session import session_manager

def test_session_manager_direct():
    """Test session manager directly (without Flask)"""
    print("=== Testing Session Manager Directly ===")
    
    # Test session creation
    phone_number = "+919876543210"
    session = session_manager.create_session(phone_number)
    print(f"✓ Created session: {session.session_id}")
    
    # Test language update
    success = session_manager.update_session_language(phone_number, "telugu")
    print(f"✓ Updated language: {success}")
    
    # Test menu update
    success = session_manager.update_session_menu(phone_number, "question_recording")
    print(f"✓ Updated menu state: {success}")
    
    # Test adding questions and responses
    questions = [
        "What is reflection of light?",
        "How does photosynthesis work?",
        "What is Ohm's law?"
    ]
    
    for i, question in enumerate(questions):
        session_manager.add_question_to_session(phone_number, question)
        
        # Check if it's a demo question
        demo_response = session_manager.get_cached_demo_response(question)
        if demo_response:
            print(f"✓ Found cached demo response for: {question[:30]}...")
            session_manager.add_response_to_session(phone_number, demo_response)
        else:
            mock_response = f"This is a mock response to question {i+1}"
            session_manager.add_response_to_session(phone_number, mock_response)
    
    # Test conversation context
    context = session_manager.get_conversation_context(phone_number)
    print(f"✓ Conversation context length: {len(context)} characters")
    
    # Test session stats
    stats = session_manager.get_session_stats()
    print(f"✓ Session stats: {stats}")
    
    # Test demo questions
    demo_questions = session_manager.get_demo_questions()
    print(f"✓ Demo questions count: {len(demo_questions)}")
    
    # Test session cleanup
    session_manager.end_session(phone_number)
    session_manager.cleanup_session(phone_number)
    print("✓ Session ended and cleaned up")
    
    print("=== Direct Session Manager Tests Completed ===\n")

def test_flask_api_endpoints():
    """Test session management via Flask API endpoints"""
    print("=== Testing Flask API Endpoints ===")
    
    base_url = "http://localhost:5000"
    phone_number = "+919876543211"
    
    try:
        # Test session creation
        response = requests.post(f"{base_url}/api/session/create", 
                               json={"phone_number": phone_number})
        if response.status_code == 200:
            print("✓ Session creation API works")
        else:
            print(f"✗ Session creation failed: {response.status_code}")
            return
        
        # Test getting session
        response = requests.get(f"{base_url}/api/session/{phone_number}")
        if response.status_code == 200:
            print("✓ Get session API works")
        else:
            print(f"✗ Get session failed: {response.status_code}")
        
        # Test language update
        response = requests.put(f"{base_url}/api/session/{phone_number}/language",
                              json={"language": "telugu"})
        if response.status_code == 200:
            print("✓ Language update API works")
        else:
            print(f"✗ Language update failed: {response.status_code}")
        
        # Test adding question
        response = requests.post(f"{base_url}/api/session/{phone_number}/question",
                               json={"question": "What is reflection of light?"})
        if response.status_code == 200:
            print("✓ Add question API works")
        else:
            print(f"✗ Add question failed: {response.status_code}")
        
        # Test demo questions
        response = requests.get(f"{base_url}/api/demo/questions")
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Demo questions API works: {data['count']} questions")
        else:
            print(f"✗ Demo questions failed: {response.status_code}")
        
        # Test demo response
        response = requests.post(f"{base_url}/api/demo/response",
                               json={"question": "What is reflection of light?"})
        if response.status_code == 200:
            data = response.json()
            if data['cached']:
                print("✓ Demo response cache works")
            else:
                print("✗ Demo response not cached")
        else:
            print(f"✗ Demo response failed: {response.status_code}")
        
        # Test session stats
        response = requests.get(f"{base_url}/api/session/stats")
        if response.status_code == 200:
            print("✓ Session stats API works")
        else:
            print(f"✗ Session stats failed: {response.status_code}")
        
        # Cleanup
        requests.post(f"{base_url}/api/session/{phone_number}/end")
        requests.delete(f"{base_url}/api/session/{phone_number}/cleanup")
        print("✓ Session cleanup completed")
        
    except requests.exceptions.ConnectionError:
        print("✗ Flask server not running. Start with: python app.py")
        return
    
    print("=== Flask API Tests Completed ===\n")

def test_demo_question_coverage():
    """Test demo question cache coverage"""
    print("=== Testing Demo Question Coverage ===")
    
    demo_questions = session_manager.get_demo_questions()
    
    # Test each demo question
    physics_count = 0
    chemistry_count = 0
    biology_count = 0
    
    for question in demo_questions:
        response = session_manager.get_cached_demo_response(question)
        if response:
            # Categorize by subject based on keywords
            if any(word in question.lower() for word in ['light', 'mirror', 'current', 'ohm', 'magnetic', 'motor', 'refraction']):
                physics_count += 1
            elif any(word in question.lower() for word in ['acid', 'base', 'soap', 'metal', 'corrosion', 'equation', 'carbon dioxide', 'ph']):
                chemistry_count += 1
            elif any(word in question.lower() for word in ['plants', 'kidney', 'heart', 'photosynthesis', 'breathe', 'reproduction']):
                biology_count += 1
    
    print(f"✓ Physics questions: {physics_count}")
    print(f"✓ Chemistry questions: {chemistry_count}")
    print(f"✓ Biology questions: {biology_count}")
    print(f"✓ Total cached questions: {len(demo_questions)}")
    
    # Test some specific questions
    test_questions = [
        "What is reflection of light?",
        "How does photosynthesis work?",  # This should NOT be cached (different wording)
        "What happens when acid reacts with base?",
        "Random question that should not be cached"
    ]
    
    for question in test_questions:
        response = session_manager.get_cached_demo_response(question)
        if response:
            print(f"✓ Cached: {question[:40]}...")
        else:
            print(f"✗ Not cached: {question[:40]}...")
    
    print("=== Demo Question Coverage Tests Completed ===\n")

def main():
    """Run all tests"""
    print("VidyaVani Session Management Test Suite")
    print("=" * 50)
    
    # Test direct session manager
    test_session_manager_direct()
    
    # Test demo question coverage
    test_demo_question_coverage()
    
    # Test Flask API (only if server is running)
    print("Note: To test Flask API endpoints, run 'python app.py' in another terminal")
    test_flask_api_endpoints()
    
    print("All tests completed!")

if __name__ == "__main__":
    main()