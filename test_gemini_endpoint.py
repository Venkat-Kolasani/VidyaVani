#!/usr/bin/env python3
"""
Test script to verify Gemini API endpoint is working
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_gemini_direct():
    """Test Gemini API directly"""
    print("🧪 Testing Gemini API Direct Connection...")
    print("=" * 60)
    
    try:
        import google.generativeai as genai
        
        # Get API key
        api_key = os.getenv('GOOGLE_GEMINI_API_KEY')
        if not api_key:
            print("❌ GOOGLE_GEMINI_API_KEY not found in environment")
            return False
        
        print(f"✅ API Key found: {api_key[:10]}...{api_key[-5:]}")
        
        # Configure Gemini
        genai.configure(api_key=api_key)
        
        # Test with gemini-2.5-flash
        print("\n📡 Testing gemini-2.5-flash model...")
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        # Test question
        test_question = "What is potential difference in simple terms?"
        print(f"❓ Question: {test_question}")
        
        # Generate response
        response = model.generate_content(test_question)
        response_text = response.text if response and response.text else None
        
        if response_text:
            print(f"\n✅ Response received ({len(response_text)} chars):")
            print("-" * 60)
            print(response_text)
            print("-" * 60)
            return True
        else:
            print("❌ No response text received")
            return False
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_gemini_endpoint_locally():
    """Test the Flask endpoint locally"""
    print("\n\n🧪 Testing Flask /api/gemini-direct Endpoint...")
    print("=" * 60)
    
    try:
        import requests
        
        # Test endpoint
        url = "http://localhost:5000/api/gemini-direct"
        payload = {
            "question": "What is photosynthesis?",
            "language": "english"
        }
        
        print(f"📡 POST {url}")
        print(f"📦 Payload: {payload}")
        
        response = requests.post(url, json=payload, timeout=30)
        
        print(f"\n📊 Status Code: {response.status_code}")
        
        if response.ok:
            data = response.json()
            print(f"✅ Success: {data.get('success')}")
            print(f"📝 Response ({len(data.get('response', ''))} chars):")
            print("-" * 60)
            print(data.get('response', 'No response'))
            print("-" * 60)
            print(f"🔧 Method: {data.get('method')}")
            print(f"🌐 Language: {data.get('language')}")
            return True
        else:
            print(f"❌ Error: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("⚠️  Flask server not running on localhost:5000")
        print("   Start it with: python app.py")
        return None
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("🚀 VidyaVani Gemini API Test Suite")
    print("=" * 60)
    
    # Test 1: Direct Gemini API
    test1_result = test_gemini_direct()
    
    # Test 2: Flask endpoint (if server is running)
    test2_result = test_gemini_endpoint_locally()
    
    # Summary
    print("\n\n" + "=" * 60)
    print("📊 Test Summary")
    print("=" * 60)
    print(f"Direct Gemini API:     {'✅ PASS' if test1_result else '❌ FAIL'}")
    if test2_result is not None:
        print(f"Flask Endpoint:        {'✅ PASS' if test2_result else '❌ FAIL'}")
    else:
        print(f"Flask Endpoint:        ⏭️  SKIPPED (server not running)")
    
    print("\n💡 To test the deployed version:")
    print("   curl https://vidyavani.onrender.com/api/test-gemini")
    print("=" * 60 + "\n")
    
    sys.exit(0 if test1_result else 1)
