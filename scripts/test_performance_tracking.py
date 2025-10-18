#!/usr/bin/env python3
"""
Performance Tracking Test Script for VidyaVani IVR Learning System

This script tests the performance tracking functionality and generates
sample metrics for demonstration purposes.
"""

import sys
import os
import time
import requests
import json
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.utils.performance_tracker import performance_tracker
from src.utils.performance_decorators import track_performance, PipelineTracker
from config import Config

def simulate_component_operations():
    """Simulate various component operations to generate performance data"""
    print("🔄 Simulating component operations...")
    
    # Simulate STT processing
    @track_performance("STT_Processing", track_api_usage=True, service_name="google_stt")
    def simulate_stt():
        time.sleep(0.5)  # Simulate processing time
        return {"success": True, "content": "What is reflection of light?"}
    
    # Simulate RAG processing
    @track_performance("RAG_Processing")
    def simulate_rag():
        time.sleep(1.2)  # Simulate processing time
        return {"success": True, "response": "Light reflection occurs when..."}
    
    # Simulate TTS processing
    @track_performance("TTS_Processing", track_api_usage=True, service_name="google_tts")
    def simulate_tts():
        time.sleep(0.8)  # Simulate processing time
        return {"success": True, "audio_data": b"fake_audio_data"}
    
    # Simulate OpenAI API calls
    @track_performance("OpenAI_Response_Generation", track_api_usage=True, 
                      service_name="openai_gpt", estimate_cost=True)
    def simulate_openai():
        time.sleep(2.1)  # Simulate API call time
        return {"success": True, "tokens_used": 150, "response": "Generated response"}
    
    # Run simulations multiple times
    for i in range(5):
        print(f"  Simulation round {i+1}/5")
        
        # Simulate complete pipeline
        with PipelineTracker("question_processing", f"+91999999999{i}") as tracker:
            tracker.start_stage("stt")
            stt_result = simulate_stt()
            tracker.end_stage("stt", stt_result["success"])
            
            tracker.start_stage("rag")
            rag_result = simulate_rag()
            tracker.end_stage("rag", rag_result["success"])
            
            tracker.start_stage("openai")
            openai_result = simulate_openai()
            tracker.end_stage("openai", openai_result["success"])
            
            tracker.start_stage("tts")
            tts_result = simulate_tts()
            tracker.end_stage("tts", tts_result["success"])
        
        # Simulate some cache operations
        performance_tracker.track_cache_usage("response_cache", i % 3 == 0)  # 33% hit rate
        performance_tracker.track_cache_usage("audio_cache", i % 2 == 0)     # 50% hit rate
        
        # Simulate session tracking
        session_id = f"session_{i}"
        performance_tracker.start_session_tracking(session_id, f"+91999999999{i}", "english")
        performance_tracker.track_question_processing(session_id, True, 2.5 + i * 0.3)
        performance_tracker.end_session_tracking(session_id)
        
        time.sleep(0.1)  # Brief pause between rounds

def simulate_error_scenarios():
    """Simulate error scenarios to test error tracking"""
    print("⚠️  Simulating error scenarios...")
    
    @track_performance("STT_Processing_Error", track_api_usage=True, service_name="google_stt")
    def simulate_stt_error():
        time.sleep(0.3)
        return {"success": False, "error_message": "Audio quality too poor"}
    
    @track_performance("Slow_Component")
    def simulate_slow_component():
        time.sleep(10.0)  # Simulate slow response (should trigger alert)
        return {"success": True}
    
    # Simulate some failures
    for i in range(3):
        try:
            result = simulate_stt_error()
        except:
            pass
        
        # Simulate API rate limiting
        performance_tracker.track_api_usage("openai_gpt", False, rate_limited=True)
    
    # Simulate one slow component (should trigger performance alert)
    print("  Simulating slow component (will trigger alert)...")
    simulate_slow_component()

def test_performance_api_endpoints():
    """Test performance monitoring API endpoints"""
    print("🌐 Testing performance API endpoints...")
    
    base_url = "http://localhost:5000"
    endpoints = [
        "/api/performance/metrics",
        "/api/performance/components", 
        "/api/performance/api-usage",
        "/api/performance/cache",
        "/api/performance/alerts",
        "/api/performance/dashboard"
    ]
    
    for endpoint in endpoints:
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=5)
            if response.status_code == 200:
                print(f"  ✅ {endpoint} - OK")
            else:
                print(f"  ❌ {endpoint} - Status: {response.status_code}")
        except requests.exceptions.ConnectionError:
            print(f"  ⚠️  {endpoint} - Server not running (expected if testing standalone)")
        except Exception as e:
            print(f"  ❌ {endpoint} - Error: {e}")

def display_performance_summary():
    """Display comprehensive performance summary"""
    print("\n📊 Performance Summary")
    print("=" * 50)
    
    summary = performance_tracker.get_performance_summary()
    
    # System metrics
    system = summary['system_metrics']
    print(f"System Uptime: {summary['uptime_seconds']:.1f} seconds")
    print(f"Total Calls: {system['total_calls']}")
    print(f"Concurrent Calls: {system['concurrent_calls']}")
    print(f"Max Concurrent: {system['max_concurrent_calls']}")
    
    # Component performance
    print(f"\n🔧 Component Performance:")
    for name, metrics in summary['component_metrics'].items():
        print(f"  {name}:")
        print(f"    Calls: {metrics['total_calls']}")
        print(f"    Success Rate: {metrics['success_rate']:.1f}%")
        print(f"    Avg Response Time: {metrics['average_response_time']:.3f}s")
        print(f"    Recent Avg: {metrics['recent_average_response_time']:.3f}s")
    
    # API usage
    print(f"\n🌐 API Usage:")
    total_cost = 0
    for name, metrics in summary['api_metrics'].items():
        if metrics['total_requests'] > 0:
            print(f"  {name}:")
            print(f"    Requests: {metrics['total_requests']}")
            print(f"    Success Rate: {metrics['success_rate']:.1f}%")
            print(f"    Tokens Used: {metrics['total_tokens_used']}")
            print(f"    Estimated Cost: ${metrics['estimated_cost']:.4f}")
            total_cost += metrics['estimated_cost']
    
    print(f"\n💰 Total Estimated Cost: ${total_cost:.4f}")
    
    # Cache performance
    print(f"\n🗄️  Cache Performance:")
    for name, metrics in summary['cache_metrics'].items():
        if metrics['total_requests'] > 0:
            print(f"  {name}:")
            print(f"    Requests: {metrics['total_requests']}")
            print(f"    Hit Rate: {metrics['hit_rate']:.1f}%")
    
    # Recent alerts
    if summary['recent_alerts']:
        print(f"\n⚠️  Recent Alerts ({len(summary['recent_alerts'])}):")
        for alert in summary['recent_alerts'][-5:]:  # Show last 5 alerts
            print(f"  {alert['type']}: {alert.get('component', 'system')} - {alert['timestamp']}")
    else:
        print(f"\n✅ No Recent Alerts")
    
    # Session summary
    session_summary = summary['session_summary']
    print(f"\n👥 Session Summary:")
    print(f"  Total Sessions: {session_summary['total_sessions']}")
    print(f"  Active Sessions: {session_summary['active_sessions']}")

def export_metrics_for_demo():
    """Export metrics to file for demo purposes"""
    print("\n💾 Exporting metrics for demo...")
    
    try:
        performance_tracker.export_metrics_to_file()
        print("  ✅ Metrics exported successfully")
        
        # Also create a simplified demo file
        summary = performance_tracker.get_performance_summary()
        
        demo_data = {
            'demo_timestamp': datetime.now().isoformat(),
            'system_health': 'healthy' if len(summary['recent_alerts']) == 0 else 'warning',
            'total_calls_processed': summary['system_metrics']['total_calls'],
            'average_response_times': {
                name: metrics['average_response_time'] 
                for name, metrics in summary['component_metrics'].items()
            },
            'api_cost_summary': {
                'total_estimated_cost': sum(
                    api['estimated_cost'] for api in summary['api_metrics'].values()
                ),
                'total_tokens_used': sum(
                    api['total_tokens_used'] for api in summary['api_metrics'].values()
                )
            },
            'cache_efficiency': {
                name: metrics['hit_rate'] 
                for name, metrics in summary['cache_metrics'].items()
                if metrics['total_requests'] > 0
            }
        }
        
        with open('logs/demo_performance_summary.json', 'w') as f:
            json.dump(demo_data, f, indent=2)
        
        print("  ✅ Demo summary exported to logs/demo_performance_summary.json")
        
    except Exception as e:
        print(f"  ❌ Export failed: {e}")

def main():
    """Main test function"""
    print("🚀 VidyaVani Performance Tracking Test")
    print("=" * 50)
    
    # Ensure logs directory exists
    os.makedirs('logs', exist_ok=True)
    
    # Reset metrics for clean test
    performance_tracker.reset_metrics()
    print("📊 Performance metrics reset for clean test")
    
    # Run simulations
    simulate_component_operations()
    simulate_error_scenarios()
    
    # Test API endpoints (if server is running)
    test_performance_api_endpoints()
    
    # Display comprehensive summary
    display_performance_summary()
    
    # Export metrics for demo
    export_metrics_for_demo()
    
    print(f"\n✅ Performance tracking test completed!")
    print(f"📁 Check logs/ directory for exported metrics")
    print(f"🌐 Start the Flask app and visit /api/performance/dashboard for live metrics")

if __name__ == "__main__":
    main()