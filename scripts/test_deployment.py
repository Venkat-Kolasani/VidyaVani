#!/usr/bin/env python3
"""
Test script to verify VidyaVani deployment on Render
"""

import requests
import json
import time

BASE_URL = "https://vidyavani.onrender.com"

def test_endpoint(endpoint, description):
    """Test a single endpoint"""
    url = f"{BASE_URL}{endpoint}"
    print(f"\n🔍 Testing {description}")
    print(f"URL: {url}")
    
    try:
        response = requests.get(url, timeout=30)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ SUCCESS")
            if response.headers.get('content-type', '').startswith('application/json'):
                try:
                    data = response.json()
                    print(f"Response: {json.dumps(data, indent=2)[:200]}...")
                except:
                    print(f"Response: {response.text[:200]}...")
            else:
                print(f"Response: {response.text[:200]}...")
        else:
            print(f"❌ FAILED: {response.status_code}")
            print(f"Error: {response.text[:200]}...")
            
    except requests.exceptions.Timeout:
        print("⏰ TIMEOUT (30s)")
    except requests.exceptions.ConnectionError:
        print("🔌 CONNECTION ERROR")
    except Exception as e:
        print(f"❌ ERROR: {e}")

def main():
    """Run all tests"""
    print("🚀 Testing VidyaVani Deployment")
    print("=" * 50)
    
    # Test endpoints
    endpoints = [
        ("/api/health", "Health Check"),
        ("/demo-simulator", "Demo Simulator Page"),
        ("/demo/processing-dashboard", "Processing Dashboard"),
        ("/api/demo/questions", "Demo Questions API"),
        ("/api/performance/metrics", "Performance Metrics"),
        ("/api/session/stats", "Session Stats"),
    ]
    
    for endpoint, description in endpoints:
        test_endpoint(endpoint, description)
        time.sleep(1)  # Small delay between requests
    
    print("\n" + "=" * 50)
    print("🎉 Testing completed!")
    print("\n📞 Next steps:")
    print("1. If health check passes, the app is running")
    print("2. Configure Exotel webhook URL: https://vidyavani.onrender.com/webhook/incoming-call")
    print("3. Test phone calls!")

if __name__ == "__main__":
    main()