#!/usr/bin/env python3
"""
Test Telugu language flow for VidyaVani IVR
"""

import requests
import xml.etree.ElementTree as ET

def test_telugu_flow():
    """Test complete Telugu language flow"""
    
    base_url = "http://localhost:5001"
    test_phone = "+919876543212"
    
    print("🧪 Testing Telugu Language Flow")
    print("=" * 40)
    
    # Step 1: Incoming call
    print("\n1. Incoming call...")
    response = requests.post(f"{base_url}/webhook/incoming-call", data={
        'CallSid': 'telugu_test_123',
        'From': test_phone,
        'To': '+911234567890'
    })
    
    if response.status_code == 200:
        print("✅ Call initiated")
    
    # Step 2: Select Telugu (option 2)
    print("\n2. Selecting Telugu language...")
    response = requests.post(f"{base_url}/webhook/language-selection", data={
        'From': test_phone,
        'Digits': '2'  # Telugu
    })
    
    if response.status_code == 200:
        print("✅ Telugu selected")
        # Check for Telugu text in response
        if 'తెలుగు' in response.text:
            print("✅ Telugu text found in response")
        else:
            print("❌ Telugu text not found")
    
    # Step 3: Grade confirmation
    print("\n3. Grade confirmation...")
    response = requests.post(f"{base_url}/webhook/grade-confirmation", data={
        'From': test_phone,
        'Digits': '1'
    })
    
    if response.status_code == 200:
        print("✅ Grade confirmed")
    
    # Step 4: Select ask question (option 2)
    print("\n4. Selecting ask question...")
    response = requests.post(f"{base_url}/webhook/interaction-mode-selection", data={
        'From': test_phone,
        'Digits': '2'
    })
    
    if response.status_code == 200:
        print("✅ Question mode selected")
        if 'ప్రశ్న' in response.text or 'సెకన్లు' in response.text:
            print("✅ Telugu question prompt found")
        else:
            print("❌ Telugu question prompt not found")
    
    # Step 5: Record question
    print("\n5. Recording question...")
    response = requests.post(f"{base_url}/webhook/question-recording", data={
        'From': test_phone,
        'RecordingUrl': 'https://example.com/telugu_question.wav',
        'RecordingDuration': '10'
    })
    
    if response.status_code == 200:
        print("✅ Question recorded")
        if 'ప్రాసెస్' in response.text or 'వేచి' in response.text:
            print("✅ Telugu processing message found")
        else:
            print("❌ Telugu processing message not found")
    
    # Step 6: Check session state
    print("\n6. Checking session state...")
    response = requests.get(f"{base_url}/api/session/{test_phone}")
    
    if response.status_code == 200:
        session_data = response.json()
        print(f"✅ Session language: {session_data.get('language')}")
        print(f"✅ Current menu: {session_data.get('current_menu')}")
        
        if session_data.get('language') == 'telugu':
            print("✅ Telugu language correctly set in session")
        else:
            print("❌ Language not set correctly")
    
    # Step 7: Test follow-up menu in Telugu
    print("\n7. Testing follow-up menu...")
    response = requests.post(f"{base_url}/webhook/follow-up-menu", data={
        'From': test_phone,
        'Digits': '9'  # Main menu
    })
    
    if response.status_code == 200:
        print("✅ Follow-up menu working")
        if 'టాపిక్స్' in response.text or 'ప్రశ్న' in response.text:
            print("✅ Telugu menu options found")
        else:
            print("❌ Telugu menu options not found")
    
    print("\n" + "=" * 40)
    print("🏁 Telugu flow testing completed")

if __name__ == "__main__":
    test_telugu_flow()