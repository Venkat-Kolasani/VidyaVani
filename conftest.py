"""
Pytest configuration for VidyaVani test suite.
Provides fixtures and configuration for all tests.
"""

import pytest
import requests
import time


def pytest_configure(config):
    """Register custom markers"""
    config.addinivalue_line(
        "markers", "integration: mark test as integration test requiring live server"
    )
    config.addinivalue_line(
        "markers", "requires_server: mark test as requiring Flask server on port 5001"
    )


def is_server_running(port=5001, max_attempts=1):
    """Check if the Flask server is running on the specified port"""
    for attempt in range(max_attempts):
        try:
            response = requests.get(f"http://localhost:{port}/", timeout=1)
            return True
        except (requests.ConnectionError, requests.Timeout):
            if attempt < max_attempts - 1:
                time.sleep(0.5)
    return False


def pytest_collection_modifyitems(config, items):
    """
    Automatically skip integration tests if server is not running.
    Only checks once per test session for efficiency.
    """
    # Integration test file patterns that require a running server
    integration_patterns = [
        'audio_storage_integration',
        'complete_ivr_flow',
        'complete_fixed_flow',
        'production_readiness',
        'telugu_flow',
        'ivr_pipeline_integration',
        'follow_up_menu_fixes',
        'end_to_end_integration',
        'workflow_simulation',
        'single_source_demo',
        'ivr_endpoints',
        'google_cloud_integration',
        'ivr_xml_generation',
        'content_processing'
    ]
    
    # Check server status once
    server_running = is_server_running()
    
    skip_marker = pytest.mark.skip(
        reason=(
            "\n\n⚠️  Flask server is not running on port 5001!\n"
            "This test requires a running server.\n\n"
            "To start the server, run in a separate terminal:\n"
            "  ./run_test_server.sh\n"
            "OR:\n"
            "  PORT=5001 python app.py\n\n"
            "To run only unit tests (no server needed):\n"
            "  pytest scripts/test_error_handling.py\n"
            "  pytest scripts/test_performance_tracking.py\n"
            "  pytest scripts/test_rag_engine.py\n"
            "  pytest scripts/test_session_management.py\n"
            "  pytest scripts/test_session_utils.py\n"
        )
    )
    
    for item in items:
        # Check if test file matches integration patterns
        test_file = item.nodeid.lower()
        is_integration_test = any(pattern in test_file for pattern in integration_patterns)
        
        # Skip integration tests if server is not running
        if is_integration_test and not server_running:
            item.add_marker(skip_marker)
