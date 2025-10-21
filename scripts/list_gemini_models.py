#!/usr/bin/env python3
"""
List available Gemini models
"""

import os
import google.generativeai as genai

def list_models():
    api_key = os.getenv('GOOGLE_GEMINI_API_KEY')
    if not api_key:
        print("❌ GOOGLE_GEMINI_API_KEY not found")
        return
    
    genai.configure(api_key=api_key)
    
    print("🔍 Available Gemini models:")
    print("=" * 50)
    
    for model in genai.list_models():
        if 'generateContent' in model.supported_generation_methods:
            print(f"✅ {model.name}")
            print(f"   Display name: {model.display_name}")
            print(f"   Description: {model.description}")
            print()

if __name__ == "__main__":
    list_models()