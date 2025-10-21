#!/usr/bin/env python3
"""
Direct test of Gemini 2.5 Flash
"""

import os
import google.generativeai as genai

def test_gemini_direct():
    api_key = os.getenv('GOOGLE_GEMINI_API_KEY')
    if not api_key:
        print("❌ GOOGLE_GEMINI_API_KEY not found")
        return
    
    genai.configure(api_key=api_key)
    
    # Test Gemini 2.5 Flash directly
    model = genai.GenerativeModel('models/gemini-2.5-flash')
    
    prompt = "You are a helpful science tutor. What is photosynthesis?"
    
    print("🧪 Testing Gemini 2.5 Flash directly...")
    
    try:
        response = model.generate_content(prompt)
        print(f"✅ Response type: {type(response)}")
        print(f"✅ Candidates: {len(response.candidates) if response.candidates else 0}")
        
        if response.candidates:
            candidate = response.candidates[0]
            print(f"✅ Content parts: {len(candidate.content.parts) if candidate.content.parts else 0}")
            
            if candidate.content.parts:
                content = candidate.content.parts[0].text
                print(f"✅ Response: {content[:200]}...")
            else:
                print("❌ No content parts")
        else:
            print("❌ No candidates")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_gemini_direct()