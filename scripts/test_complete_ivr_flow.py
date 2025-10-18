#!/usr/bin/env python3
"""
Complete IVR flow test for VidyaVani
Tests the entire call flow from start to finish
"""

import requests
import xml.etree.ElementTree as ET
import time

def test_complete_flow():
    """Test complete IVR call flow"""
    
    base_url = "http://localhost:5001"
    test_phone = "+919876543213"
    
    print("🧪 Testing Complete IVR Call Flow")
    print("=" * 50)
    
    # Step 1: Incoming call
    print("\n📞 Step 1: Incoming Call")
    response = requests.post(f"{base_url}/webhook/incoming-call", data={
        'CallSid': 'complete_test_123',
        'From': test_phone,
        'To': '+911234567890'
    })
    
    assert response.status_code == 200, f"Incoming call failed: {response.status_code}"
    assert 'Welcome to VidyaVani' in response.text, "Welcome message not found"
    print("✅ Call initiated successfully")
    
    # Validate XML structure
    root = ET.fromstring(response.text)
    assert root.tag == 'Response', "Invalid XML root element"
    assert len(root.findall('.//Say')) > 0, "No Say elements found"
    assert len(root.findall('.//Gather')) > 0, "No Gather elements found"
    print("✅ XML structure valid")
    
    # Step 2: Language Selection (English)
    print("\n🌐 Step 2: Language Selection (English)")
    response = requests.post(f"{base_url}/webhook/language-selection", data={
        'From': test_phone,
        'Digits': '1'  # English
    })
    
    assert response.status_code == 200, f"Language selection failed: {response.status_code}"
    assert 'English' in response.text, "English confirmation not found"
    print("✅ English language selected")
    
    # Step 3: Grade Confirmation
    print("\n🎓 Step 3: Grade Confirmation")
    response = requests.post(f"{base_url}/webhook/grade-confirmation", data={
        'From': test_phone,
        'Digits': '1'
    })
    
    assert response.status_code == 200, f"Grade confirmation failed: {response.status_code}"
    print("✅ Grade confirmed")
    
    # Step 4: Interaction Mode Selection
    print("\n💬 Step 4: Interaction Mode Selection")
    response = requests.post(f"{base_url}/webhook/interaction-mode-selection", data={
        'From': test_phone,
        'Digits': '2'  # Ask question directly
    })
    
    assert response.status_code == 200, f"Interaction mode failed: {response.status_code}"
    assert 'question' in response.text.lower(), "Question prompt not found"
    print("✅ Question mode selected")
    
    # Validate recording XML
    root = ET.fromstring(response.text)
    record_elements = root.findall('.//Record')
    assert len(record_elements) > 0, "No Record elements found"
    
    record_elem = record_elements[0]
    assert record_elem.get('maxLength') == '15', "Recording duration not set correctly"
    assert record_elem.get('action') == '/webhook/question-recording', "Recording action not set"
    print("✅ Recording configuration valid")
    
    # Step 5: Question Recording
    print("\n🎤 Step 5: Question Recording")
    response = requests.post(f"{base_url}/webhook/question-recording", data={
        'From': test_phone,
        'RecordingUrl': 'https://example.com/test_question.wav',
        'RecordingDuration': '12'
    })
    
    assert response.status_code == 200, f"Question recording failed: {response.status_code}"
    assert 'processing' in response.text.lower() or 'wait' in response.text.lower(), "Processing message not found"
    print("✅ Question recorded and processing started")
    
    # Step 6: Session State Validation
    print("\n📊 Step 6: Session State Validation")
    response = requests.get(f"{base_url}/api/session/{test_phone}")
    
    assert response.status_code == 200, f"Session API failed: {response.status_code}"
    session_data = response.json()
    
    assert session_data['language'] == 'english', f"Language not set correctly: {session_data['language']}"
    assert session_data['call_active'] == True, "Call not marked as active"
    assert session_data['current_menu'] == 'processing_question', f"Menu state incorrect: {session_data['current_menu']}"
    print("✅ Session state valid")
    print(f"   Language: {session_data['language']}")
    print(f"   Menu: {session_data['current_menu']}")
    print(f"   Call Active: {session_data['call_active']}")
    
    # Step 7: Response Delivery (simulated)
    print("\n📢 Step 7: Response Delivery")
    response = requests.post(f"{base_url}/webhook/response-delivery", data={
        'From': test_phone,
        'ResponseAudioUrl': 'https://example.com/ai_response.wav'
    })
    
    assert response.status_code == 200, f"Response delivery failed: {response.status_code}"
    print("✅ Response delivered")
    
    # Validate follow-up menu XML
    root = ET.fromstring(response.text)
    gather_elements = root.findall('.//Gather')
    assert len(gather_elements) > 0, "No follow-up menu found"
    
    gather_elem = gather_elements[0]
    assert gather_elem.get('action') == '/webhook/follow-up-menu', "Follow-up action not set"
    print("✅ Follow-up menu configured")
    
    # Step 8: Follow-up Menu Navigation
    print("\n🔄 Step 8: Follow-up Menu Navigation")
    
    # Test new question option
    response = requests.post(f"{base_url}/webhook/follow-up-menu", data={
        'From': test_phone,
        'Digits': '3'  # New question
    })
    
    assert response.status_code == 200, f"Follow-up menu failed: {response.status_code}"
    assert 'question' in response.text.lower(), "New question prompt not found"
    print("✅ New question option working")
    
    # Test main menu option
    response = requests.post(f"{base_url}/webhook/follow-up-menu", data={
        'From': test_phone,
        'Digits': '9'  # Main menu
    })
    
    assert response.status_code == 200, f"Main menu failed: {response.status_code}"
    print("✅ Main menu option working")
    
    # Step 9: Invalid Input Handling
    print("\n❌ Step 9: Invalid Input Handling")
    response = requests.post(f"{base_url}/webhook/language-selection", data={
        'From': test_phone,
        'Digits': '5'  # Invalid option
    })
    
    assert response.status_code == 200, f"Invalid input handling failed: {response.status_code}"
    assert 'Invalid' in response.text or 'invalid' in response.text, "Invalid selection message not found"
    print("✅ Invalid input handled gracefully")
    
    # Step 10: Call End
    print("\n📴 Step 10: Call End")
    response = requests.post(f"{base_url}/webhook/call-end", data={
        'From': test_phone,
        'CallSid': 'complete_test_123'
    })
    
    assert response.status_code == 200, f"Call end failed: {response.status_code}"
    print("✅ Call ended successfully")
    
    # Verify session is marked as ended
    response = requests.get(f"{base_url}/api/session/{test_phone}")
    if response.status_code == 200:
        session_data = response.json()
        assert session_data['call_active'] == False, "Call not marked as ended"
        print("✅ Session marked as ended")
    
    print("\n" + "=" * 50)
    print("🎉 Complete IVR flow test PASSED!")
    print("✅ All webhook endpoints working")
    print("✅ XML responses valid")
    print("✅ Session management working")
    print("✅ Language selection working")
    print("✅ Menu navigation working")
    print("✅ Error handling working")

def test_telugu_complete_flow():
    """Test complete flow in Telugu"""
    
    base_url = "http://localhost:5001"
    test_phone = "+919876543214"
    
    print("\n\n🧪 Testing Complete Telugu Flow")
    print("=" * 40)
    
    # Incoming call
    response = requests.post(f"{base_url}/webhook/incoming-call", data={
        'CallSid': 'telugu_complete_123',
        'From': test_phone,
        'To': '+911234567890'
    })
    assert response.status_code == 200
    
    # Select Telugu
    response = requests.post(f"{base_url}/webhook/language-selection", data={
        'From': test_phone,
        'Digits': '2'  # Telugu
    })
    assert response.status_code == 200
    assert 'తెలుగు' in response.text
    
    # Grade confirmation
    response = requests.post(f"{base_url}/webhook/grade-confirmation", data={
        'From': test_phone,
        'Digits': '1'
    })
    assert response.status_code == 200
    
    # Ask question
    response = requests.post(f"{base_url}/webhook/interaction-mode-selection", data={
        'From': test_phone,
        'Digits': '2'
    })
    assert response.status_code == 200
    assert 'ప్రశ్న' in response.text or 'సెకన్లు' in response.text
    
    # Record question
    response = requests.post(f"{base_url}/webhook/question-recording", data={
        'From': test_phone,
        'RecordingUrl': 'https://example.com/telugu_q.wav',
        'RecordingDuration': '8'
    })
    assert response.status_code == 200
    
    # Check session language
    response = requests.get(f"{base_url}/api/session/{test_phone}")
    assert response.status_code == 200
    session_data = response.json()
    assert session_data['language'] == 'telugu'
    
    print("✅ Telugu complete flow working")

if __name__ == "__main__":
    try:
        test_complete_flow()
        test_telugu_complete_flow()
        print("\n🏆 ALL TESTS PASSED! IVR system is ready for integration.")
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
    except Exception as e:
        print(f"\n💥 ERROR: {e}")