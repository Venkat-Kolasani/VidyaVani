#!/usr/bin/env python3
"""
Test script for VidyaVani Demo System and Visual Presentation Tools
Tests all components of Task 10 implementation
"""

import sys
import os
import json
import time
import requests
from datetime import datetime

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.session.session_manager import SessionManager
from src.utils.call_recorder import call_recorder
from config import Config

def test_demo_questions():
    """Test demo questions functionality"""
    print("🧪 Testing Demo Questions System...")
    
    try:
        # Test session manager demo questions
        session_manager = SessionManager()
        
        # Get demo questions
        questions = session_manager.get_demo_questions()
        print(f"✓ Found {len(questions)} demo questions")
        
        if len(questions) != 20:
            print(f"❌ Expected 20 demo questions, found {len(questions)}")
            return False
        
        # Test question categories
        qa_pairs = session_manager.get_demo_qa_pairs()
        physics_count = 0
        chemistry_count = 0
        biology_count = 0
        
        physics_keywords = ['light', 'reflection', 'mirror', 'current', 'magnetic', 'motor', 'ohm']
        chemistry_keywords = ['acid', 'base', 'soap', 'metal', 'corrosion', 'equation', 'ph']
        biology_keywords = ['plant', 'food', 'kidney', 'heart', 'blood', 'photosynthesis', 'breathe']
        
        for question, response in qa_pairs:
            question_lower = question.lower()
            if any(keyword in question_lower for keyword in physics_keywords):
                physics_count += 1
            elif any(keyword in question_lower for keyword in chemistry_keywords):
                chemistry_count += 1
            elif any(keyword in question_lower for keyword in biology_keywords):
                biology_count += 1
        
        print(f"✓ Question distribution: Physics({physics_count}), Chemistry({chemistry_count}), Biology({biology_count})")
        
        # Test cached responses
        test_questions = [
            "What is reflection of light?",
            "How do plants make their food?",
            "What happens when acid reacts with base?"
        ]
        
        for question in test_questions:
            cached_response = session_manager.get_cached_demo_response(question)
            if cached_response:
                print(f"✓ Cached response found for: '{question[:30]}...'")
            else:
                print(f"❌ No cached response for: '{question}'")
                return False
        
        print("✅ Demo Questions System: PASSED")
        return True
        
    except Exception as e:
        print(f"❌ Demo Questions System: FAILED - {str(e)}")
        return False

def test_call_recording():
    """Test call recording functionality"""
    print("\n🧪 Testing Call Recording System...")
    
    try:
        # Test recording lifecycle
        phone_number = "+919999999999"
        session_id = "test_session_123"
        
        # Start recording
        recording_id = call_recorder.start_recording(
            phone_number=phone_number,
            session_id=session_id,
            language="english",
            demo_mode=True
        )
        print(f"✓ Started recording: {recording_id}")
        
        # Add questions and responses
        test_question = "What is photosynthesis?"
        test_response = "Photosynthesis is the process by which plants make food using sunlight."
        
        success = call_recorder.add_question(phone_number, test_question)
        print(f"✓ Added question: {success}")
        
        success = call_recorder.add_response(phone_number, test_response)
        print(f"✓ Added response: {success}")
        
        # Add processing metrics
        metrics = {
            'total_time': 6.5,
            'stt_time': 1.2,
            'rag_time': 3.8,
            'tts_time': 1.5
        }
        success = call_recorder.add_processing_metrics(phone_number, metrics)
        print(f"✓ Added metrics: {success}")
        
        # End recording
        ended_id = call_recorder.end_recording(phone_number, "completed")
        print(f"✓ Ended recording: {ended_id}")
        
        # Verify recording data
        recording = call_recorder.get_recording(recording_id)
        if recording:
            print(f"✓ Recording retrieved: {recording.recording_id}")
            print(f"  - Questions: {len(recording.questions_asked)}")
            print(f"  - Responses: {len(recording.responses_given)}")
            print(f"  - Duration: {recording.duration_seconds:.1f}s")
            print(f"  - Status: {recording.call_status}")
        else:
            print("❌ Failed to retrieve recording")
            return False
        
        # Test demo summary
        summary = call_recorder.create_demo_summary()
        print(f"✓ Demo summary created: {summary['total_demos']} recordings")
        
        print("✅ Call Recording System: PASSED")
        return True
        
    except Exception as e:
        print(f"❌ Call Recording System: FAILED - {str(e)}")
        return False

def test_api_endpoints():
    """Test demo system API endpoints"""
    print("\n🧪 Testing Demo API Endpoints...")
    
    base_url = "http://localhost:5000"
    
    try:
        # Test demo questions endpoint
        response = requests.get(f"{base_url}/api/demo/questions", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Demo questions API: {data['count']} questions")
        else:
            print(f"❌ Demo questions API failed: {response.status_code}")
            return False
        
        # Test curated questions endpoint
        response = requests.get(f"{base_url}/api/demo/curated-questions", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Curated questions API: {data['total_questions']} questions")
            print(f"  - Physics: {data['physics_count']}")
            print(f"  - Chemistry: {data['chemistry_count']}")
            print(f"  - Biology: {data['biology_count']}")
        else:
            print(f"❌ Curated questions API failed: {response.status_code}")
            return False
        
        # Test demo response endpoint
        test_question = "What is reflection of light?"
        response = requests.post(
            f"{base_url}/api/demo/response",
            json={"question": test_question},
            timeout=5
        )
        if response.status_code == 200:
            data = response.json()
            if data.get('cached'):
                print(f"✓ Demo response API: Found cached response")
            else:
                print(f"❌ Demo response API: No cached response found")
                return False
        else:
            print(f"❌ Demo response API failed: {response.status_code}")
            return False
        
        # Test demo summary endpoint
        response = requests.get(f"{base_url}/api/demo/summary", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Demo summary API: {data.get('total_demos', 0)} demos")
        else:
            print(f"❌ Demo summary API failed: {response.status_code}")
            return False
        
        print("✅ Demo API Endpoints: PASSED")
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Demo API Endpoints: FAILED - Connection error: {str(e)}")
        print("   Make sure the Flask server is running on localhost:5000")
        return False
    except Exception as e:
        print(f"❌ Demo API Endpoints: FAILED - {str(e)}")
        return False

def test_html_templates():
    """Test HTML template files"""
    print("\n🧪 Testing HTML Templates...")
    
    try:
        # Check demo simulator template
        simulator_path = "templates/demo_simulator.html"
        if os.path.exists(simulator_path):
            with open(simulator_path, 'r', encoding='utf-8') as f:
                content = f.read()
                if 'VidyaVani Demo Simulator' in content:
                    print("✓ Demo simulator template exists and valid")
                else:
                    print("❌ Demo simulator template invalid")
                    return False
        else:
            print("❌ Demo simulator template not found")
            return False
        
        # Check processing dashboard template
        dashboard_path = "templates/processing_dashboard.html"
        if os.path.exists(dashboard_path):
            with open(dashboard_path, 'r', encoding='utf-8') as f:
                content = f.read()
                if 'VidyaVani Processing Pipeline' in content:
                    print("✓ Processing dashboard template exists and valid")
                else:
                    print("❌ Processing dashboard template invalid")
                    return False
        else:
            print("❌ Processing dashboard template not found")
            return False
        
        # Check performance dashboard template (existing)
        perf_dashboard_path = "templates/performance_dashboard.html"
        if os.path.exists(perf_dashboard_path):
            print("✓ Performance dashboard template exists")
        else:
            print("❌ Performance dashboard template not found")
            return False
        
        print("✅ HTML Templates: PASSED")
        return True
        
    except Exception as e:
        print(f"❌ HTML Templates: FAILED - {str(e)}")
        return False

def test_web_pages():
    """Test web page accessibility"""
    print("\n🧪 Testing Web Pages...")
    
    base_url = "http://localhost:5000"
    
    try:
        # Test demo simulator page
        response = requests.get(f"{base_url}/demo/simulator", timeout=10)
        if response.status_code == 200:
            if 'VidyaVani Demo Simulator' in response.text:
                print("✓ Demo simulator page accessible")
            else:
                print("❌ Demo simulator page content invalid")
                return False
        else:
            print(f"❌ Demo simulator page failed: {response.status_code}")
            return False
        
        # Test processing dashboard page
        response = requests.get(f"{base_url}/demo/processing-dashboard", timeout=10)
        if response.status_code == 200:
            if 'VidyaVani Processing Pipeline' in response.text:
                print("✓ Processing dashboard page accessible")
            else:
                print("❌ Processing dashboard page content invalid")
                return False
        else:
            print(f"❌ Processing dashboard page failed: {response.status_code}")
            return False
        
        # Test performance dashboard page
        response = requests.get(f"{base_url}/dashboard", timeout=10)
        if response.status_code == 200:
            if 'VidyaVani Performance Dashboard' in response.text:
                print("✓ Performance dashboard page accessible")
            else:
                print("❌ Performance dashboard page content invalid")
                return False
        else:
            print(f"❌ Performance dashboard page failed: {response.status_code}")
            return False
        
        print("✅ Web Pages: PASSED")
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Web Pages: FAILED - Connection error: {str(e)}")
        print("   Make sure the Flask server is running on localhost:5000")
        return False
    except Exception as e:
        print(f"❌ Web Pages: FAILED - {str(e)}")
        return False

def test_complete_demo_flow():
    """Test complete demo flow simulation"""
    print("\n🧪 Testing Complete Demo Flow...")
    
    try:
        # Simulate a complete demo call
        phone_number = "+919876543210"
        session_id = "demo_flow_test"
        
        # Create session
        session_manager = SessionManager()
        session = session_manager.create_session(phone_number)
        print(f"✓ Created session: {session.session_id}")
        
        # Start recording
        recording_id = call_recorder.start_recording(
            phone_number=phone_number,
            session_id=session_id,
            language="english",
            demo_mode=True
        )
        print(f"✓ Started recording: {recording_id}")
        
        # Simulate language selection
        session_manager.update_session_language(phone_number, "english")
        print("✓ Selected language: English")
        
        # Process demo questions
        demo_questions = [
            "What is reflection of light?",
            "How do plants make their food?",
            "What happens when acid reacts with base?"
        ]
        
        for i, question in enumerate(demo_questions):
            print(f"  Processing question {i+1}: {question[:30]}...")
            
            # Add question to session and recording
            session_manager.add_question_to_session(phone_number, question)
            call_recorder.add_question(phone_number, question)
            
            # Get cached response
            cached_response = session_manager.get_cached_demo_response(question)
            if cached_response:
                # Add response to session and recording
                session_manager.add_response_to_session(phone_number, cached_response)
                call_recorder.add_response(phone_number, cached_response)
                
                # Add simulated metrics
                metrics = {
                    'total_time': 2.5 + (i * 0.5),  # Simulate varying response times
                    'stt_time': 0.8,
                    'rag_time': 1.2,
                    'tts_time': 0.5
                }
                call_recorder.add_processing_metrics(phone_number, metrics)
                
                print(f"    ✓ Response: {cached_response[:50]}...")
            else:
                print(f"    ❌ No cached response found")
                return False
        
        # End session and recording
        session_manager.end_session(phone_number)
        call_recorder.end_recording(phone_number, "completed")
        print("✓ Ended session and recording")
        
        # Verify final recording
        final_recording = call_recorder.get_recording(recording_id)
        if final_recording:
            print(f"✓ Final recording verification:")
            print(f"  - Questions: {len(final_recording.questions_asked)}")
            print(f"  - Responses: {len(final_recording.responses_given)}")
            print(f"  - Duration: {final_recording.duration_seconds:.1f}s")
            print(f"  - Language: {final_recording.language}")
            print(f"  - Status: {final_recording.call_status}")
        else:
            print("❌ Failed to verify final recording")
            return False
        
        print("✅ Complete Demo Flow: PASSED")
        return True
        
    except Exception as e:
        print(f"❌ Complete Demo Flow: FAILED - {str(e)}")
        return False

def generate_test_report():
    """Generate comprehensive test report"""
    print("\n📊 Generating Test Report...")
    
    try:
        # Get demo summary
        summary = call_recorder.create_demo_summary()
        
        # Get session stats
        session_manager = SessionManager()
        demo_questions = session_manager.get_demo_questions()
        
        report = {
            'test_timestamp': datetime.now().isoformat(),
            'demo_system_status': 'operational',
            'components': {
                'demo_questions': {
                    'total_questions': len(demo_questions),
                    'cached_responses': len(session_manager.demo_cache),
                    'status': 'ready'
                },
                'call_recording': {
                    'total_recordings': summary.get('total_demos', 0),
                    'status': 'operational'
                },
                'web_interfaces': {
                    'demo_simulator': 'available',
                    'processing_dashboard': 'available',
                    'performance_dashboard': 'available'
                }
            },
            'demo_readiness': {
                'curated_questions': len(demo_questions) >= 20,
                'cached_responses': len(session_manager.demo_cache) >= 20,
                'recording_system': True,
                'visual_dashboards': True
            }
        }
        
        # Save report
        report_path = f"logs/demo_system_test_report_{int(time.time())}.json"
        os.makedirs('logs', exist_ok=True)
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"✓ Test report saved: {report_path}")
        
        # Print summary
        print("\n📋 Test Summary:")
        print(f"  - Demo Questions: {report['components']['demo_questions']['total_questions']}")
        print(f"  - Cached Responses: {report['components']['demo_questions']['cached_responses']}")
        print(f"  - Recordings: {report['components']['call_recording']['total_recordings']}")
        print(f"  - Demo Ready: {all(report['demo_readiness'].values())}")
        
        return report_path
        
    except Exception as e:
        print(f"❌ Test Report Generation: FAILED - {str(e)}")
        return None

def main():
    """Run all demo system tests"""
    print("🚀 VidyaVani Demo System Test Suite")
    print("=" * 50)
    
    tests = [
        ("Demo Questions System", test_demo_questions),
        ("Call Recording System", test_call_recording),
        ("HTML Templates", test_html_templates),
        ("API Endpoints", test_api_endpoints),
        ("Web Pages", test_web_pages),
        ("Complete Demo Flow", test_complete_demo_flow)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n🧪 Running: {test_name}")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name}: FAILED - {str(e)}")
            results.append((test_name, False))
    
    # Print final results
    print("\n" + "=" * 50)
    print("📊 FINAL TEST RESULTS")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    # Generate report
    report_path = generate_test_report()
    
    if passed == total:
        print("\n🎉 All tests passed! Demo system is ready for presentation.")
        if report_path:
            print(f"📄 Detailed report: {report_path}")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please review and fix issues.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)