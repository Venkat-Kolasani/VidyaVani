#!/usr/bin/env python3
"""
Test script to verify frontend is working
"""

import os
import sys

def test_frontend_files():
    """Test that all frontend files exist"""
    print("🔍 Testing frontend files...")
    
    required_files = [
        'frontend/index.html',
        'frontend/css/styles.css',
        'frontend/js/app.js',
        'frontend/js/voice.js',
        'frontend/js/network.js',
        'frontend/README.md',
    ]
    
    all_exist = True
    for file_path in required_files:
        if os.path.exists(file_path):
            size = os.path.getsize(file_path)
            print(f"  ✅ {file_path} ({size:,} bytes)")
        else:
            print(f"  ❌ {file_path} - NOT FOUND")
            all_exist = False
    
    return all_exist

def test_html_structure():
    """Test HTML file structure"""
    print("\n🔍 Testing HTML structure...")
    
    with open('frontend/index.html', 'r') as f:
        html_content = f.read()
    
    required_elements = [
        'phone-device',
        'developer-panel',
        'voice-btn',
        'network-list',
        'metrics-grid',
        'logs-list',
    ]
    
    all_found = True
    for element in required_elements:
        if element in html_content:
            print(f"  ✅ Found element: {element}")
        else:
            print(f"  ❌ Missing element: {element}")
            all_found = False
    
    return all_found

def test_javascript_functions():
    """Test JavaScript file structure"""
    print("\n🔍 Testing JavaScript functions...")
    
    js_files = {
        'frontend/js/app.js': [
            'startSession',
            'endSession',
            'askQuestion',
            'showToast',
            'checkBackendHealth',
        ],
        'frontend/js/voice.js': [
            'initializeVoiceRecognition',
            'toggleVoiceInput',
            'speakText',
        ],
        'frontend/js/network.js': [
            'trackNetworkCall',
            'updateMetrics',
            'monitorBackendHealth',
        ],
    }
    
    all_found = True
    for file_path, functions in js_files.items():
        print(f"\n  📄 {file_path}")
        with open(file_path, 'r') as f:
            content = f.read()
        
        for func in functions:
            if f'function {func}' in content or f'{func} =' in content:
                print(f"    ✅ {func}")
            else:
                print(f"    ❌ {func} - NOT FOUND")
                all_found = False
    
    return all_found

def test_css_styles():
    """Test CSS file"""
    print("\n🔍 Testing CSS styles...")
    
    with open('frontend/css/styles.css', 'r') as f:
        css_content = f.read()
    
    required_classes = [
        '.phone-device',
        '.developer-panel',
        '.voice-btn',
        '.network-item',
        '.metric-card',
        '.toast',
    ]
    
    all_found = True
    for css_class in required_classes:
        if css_class in css_content:
            print(f"  ✅ {css_class}")
        else:
            print(f"  ❌ {css_class} - NOT FOUND")
            all_found = False
    
    return all_found

def main():
    """Run all tests"""
    print("=" * 60)
    print("🚀 VidyaVani Frontend Test Suite")
    print("=" * 60)
    
    tests = [
        ("Frontend Files", test_frontend_files),
        ("HTML Structure", test_html_structure),
        ("JavaScript Functions", test_javascript_functions),
        ("CSS Styles", test_css_styles),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ Error in {test_name}: {str(e)}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Summary")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status} - {test_name}")
    
    print(f"\n  Total: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Frontend is ready to deploy.")
        return 0
    else:
        print("\n⚠️  Some tests failed. Please review the output above.")
        return 1

if __name__ == '__main__':
    sys.exit(main())
