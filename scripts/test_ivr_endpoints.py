#!/usr/bin/env python3
"""
Test script for VidyaVani IVR endpoints
Tests the webhook endpoints and XML response generation
"""

import requests
import json
import sys
import os

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

def test_ivr_endpoints():
    """Test IVR webhook endpoints"""
    
    base_url = "http://localhost:5001"
    test_phone = "+919876543210"
    
    print("🧪 Testing VidyaVani IVR Endpoints")
    print("=" * 50)
    
    # Test 1: Incoming call
    print("\n1. Testing incoming call webhook...")
    try:
        response = requests.post(f"{base_url}/webhook/incoming-call", data={
            'CallSid': 'test_call_123',
            'From': test_phone,
            'To': '+911234567890'
        })
        
        if response.status_code == 200:
            print("✅ Incoming call webhook working")
            print(f"Response content type: {response.headers.get('content-type')}")
            print(f"Response length: {len(response.text)} characters")
            if 'Welcome to VidyaVani' in response.text:
                print("✅ Welcome message found in response")
            else:
                print("❌ Welcome message not found")
        else:
            print(f"❌ Incoming call failed: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"❌ Error testing incoming call: {e}")
    
    # Test 2: Language selection
    print("\n2. Testing language selection webhook...")
    try:
        response = requests.post(f"{base_url}/webhook/language-selection", data={
            'From': test_phone,
            'Digits': '1'  # English
        })
        
        if response.status_code == 200:
            print("✅ Language selection webhook working")
            if 'English' in response.text or 'Class 10' in response.text:
                print("✅ English confirmation found")
            else:
                print("❌ Language confirmation not found")
        else:
            print(f"❌ Language selection failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Error testing language selection: {e}")
    
    # Test 3: Interaction mode selection
    print("\n3. Testing interaction mode selection...")
    try:
        response = requests.post(f"{base_url}/webhook/interaction-mode-selection", data={
            'From': test_phone,
            'Digits': '2'  # Ask question directly
        })
        
        if response.status_code == 200:
            print("✅ Interaction mode selection working")
            if 'question' in response.text.lower() or 'record' in response.text.lower():
                print("✅ Question recording prompt found")
            else:
                print("❌ Question recording prompt not found")
        else:
            print(f"❌ Interaction mode selection failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Error testing interaction mode: {e}")
    
    # Test 4: Question recording
    print("\n4. Testing question recording webhook...")
    try:
        response = requests.post(f"{base_url}/webhook/question-recording", data={
            'From': test_phone,
            'RecordingUrl': 'https://example.com/recording.wav',
            'RecordingDuration': '8'
        })
        
        if response.status_code == 200:
            print("✅ Question recording webhook working")
            if 'processing' in response.text.lower() or 'wait' in response.text.lower():
                print("✅ Processing message found")
            else:
                print("❌ Processing message not found")
        else:
            print(f"❌ Question recording failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Error testing question recording: {e}")
    
    # Test 5: Follow-up menu
    print("\n5. Testing follow-up menu...")
    try:
        response = requests.post(f"{base_url}/webhook/follow-up-menu", data={
            'From': test_phone,
            'Digits': '3'  # New question
        })
        
        if response.status_code == 200:
            print("✅ Follow-up menu webhook working")
            if 'question' in response.text.lower():
                print("✅ New question prompt found")
            else:
                print("❌ New question prompt not found")
        else:
            print(f"❌ Follow-up menu failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Error testing follow-up menu: {e}")
    
    # Test 6: Session API integration
    print("\n6. Testing session API integration...")
    try:
        # Check if session was created
        response = requests.get(f"{base_url}/api/session/{test_phone}")
        
        if response.status_code == 200:
            session_data = response.json()
            print("✅ Session API working")
            print(f"Session language: {session_data.get('language')}")
            print(f"Current menu: {session_data.get('current_menu')}")
            print(f"Call active: {session_data.get('call_active')}")
        else:
            print(f"❌ Session API failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Error testing session API: {e}")
    
    # Test 7: XML validation
    print("\n7. Testing XML response validation...")
    try:
        import xml.etree.ElementTree as ET
        
        response = requests.post(f"{base_url}/webhook/incoming-call", data={
            'CallSid': 'test_call_456',
            'From': '+919876543211',
            'To': '+911234567890'
        })
        
        if response.status_code == 200:
            # Try to parse XML
            try:
                root = ET.fromstring(response.text)
                print("✅ XML response is valid")
                
                # Check for required elements
                say_elements = root.findall('.//Say')
                gather_elements = root.findall('.//Gather')
                
                print(f"Say elements found: {len(say_elements)}")
                print(f"Gather elements found: {len(gather_elements)}")
                
                if say_elements and gather_elements:
                    print("✅ Required XML elements present")
                else:
                    print("❌ Missing required XML elements")
                    
            except ET.ParseError as e:
                print(f"❌ Invalid XML response: {e}")
        else:
            print(f"❌ XML validation failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Error validating XML: {e}")
    
    print("\n" + "=" * 50)
    print("🏁 IVR endpoint testing completed")

if __name__ == "__main__":
    test_ivr_endpoints()