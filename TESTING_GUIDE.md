# VidyaVani Testing Guide

## Overview

The VidyaVani test suite includes both **unit tests** and **integration tests**:

- **Unit Tests**: Test individual components in isolation (35 tests)
- **Integration Tests**: Test end-to-end workflows requiring a live Flask server (13 tests)

## Quick Start

### Running All Tests

```bash
# Run complete test suite (requires server for integration tests)
pytest
```

### Running Only Unit Tests

```bash
# Run tests that don't require a server
pytest -k "not (integration or ivr or telugu or complete)"
```

## Integration Test Requirements

**Integration tests require a Flask server running on port 5001.**

### Option 1: Using the Test Server Script (Recommended)

Open a **new terminal** and run:

```bash
./run_test_server.sh
```

This will start the Flask server on port 5001. Leave it running while you execute tests in another terminal.

### Option 2: Manual Server Start

Open a **new terminal** and run:

```bash
PORT=5001 python app.py
```

Or:

```bash
PORT=5001 FLASK_ENV=development python app.py
```

### Option 3: Using Flask CLI

```bash
FLASK_APP=app.py FLASK_ENV=development flask run --port 5001
```

## Running Tests with Server

Once the server is running (you should see output like `* Running on http://0.0.0.0:5001`):

1. **In a new terminal**, navigate to the project directory
2. Run the full test suite:

```bash
pytest
```

Or run specific integration tests:

```bash
# Audio storage integration
pytest scripts/test_audio_storage_integration.py -v

# Complete IVR flow
pytest scripts/test_complete_ivr_flow.py -v

# Telugu language flow
pytest scripts/test_telugu_flow.py -v

# Production readiness
pytest scripts/test_production_readiness.py -v

# All IVR pipeline tests
pytest scripts/test_ivr_pipeline_integration.py -v
```

## Test Categories

### Unit Tests (✅ Pass without server)
- `scripts/test_audio_processing.py` - Audio STT/TTS unit tests
- `scripts/test_rag_engine.py` - RAG engine unit tests
- `scripts/test_session_management.py` - Session management
- `scripts/test_error_handling.py` - Error handling logic
- `scripts/test_performance_tracking.py` - Performance metrics

### Integration Tests (🌐 Require server on port 5001)
- `scripts/test_audio_storage_integration.py` - Audio storage and serving
- `scripts/test_complete_ivr_flow.py` - Full IVR workflows
- `scripts/test_complete_fixed_flow.py` - Fixed workflow validation
- `scripts/test_telugu_flow.py` - Telugu language integration
- `scripts/test_production_readiness.py` - Production validation
- `scripts/test_ivr_pipeline_integration.py` - IVR pipeline tests
- `scripts/test_follow_up_menu_fixes.py` - Menu navigation tests

## Troubleshooting

### "Connection refused" errors

**Problem**: Tests fail with `ConnectionError: [Errno 61] Connection refused`

**Solution**: 
1. Check if the Flask server is running:
   ```bash
   curl http://localhost:5001/
   ```
2. If not running, start it using one of the options above

### Port already in use

**Problem**: Server shows `Address already in use` error

**Solution**:
```bash
# Kill processes on port 5001
lsof -ti tcp:5001 | xargs kill -9

# Then restart the server
./run_test_server.sh
```

### Google Cloud credentials missing

**Problem**: Tests skip with "Google Cloud credentials not available"

**Solution**: This is normal if you haven't configured Google Cloud. Audio processing tests will skip gracefully.

## Test Results Summary

### Expected Results (with server running):

```
================================ test session ==============================
35 passed, 0 failed, 1 skipped, 13 integration tests passed
```

### Expected Results (without server):

```
================================ test session ==============================
35 passed, 13 failed (connection errors), 1 skipped
```

**Note**: The 13 "failed" tests are actually just connection errors from missing server - the code itself is fine!

## CI/CD Considerations

For automated testing in CI/CD pipelines:

1. Start the Flask server as a background process before running tests
2. Use pytest markers to separate unit and integration tests
3. Example GitHub Actions:

```yaml
- name: Start Flask Server
  run: |
    PORT=5001 python app.py &
    sleep 10  # Wait for server to start

- name: Run Unit Tests
  run: pytest -k "not integration"

- name: Run Integration Tests
  run: pytest -k "integration"

- name: Stop Flask Server
  run: kill $(lsof -ti tcp:5001)
```

## Test Coverage

Current test coverage:

- ✅ Audio Processing (STT/TTS)
- ✅ RAG Engine (Semantic Search, Response Generation)
- ✅ Session Management
- ✅ Error Handling & Recovery
- ✅ Performance Tracking
- ✅ IVR Workflows (English & Telugu)
- ✅ Audio Storage & Serving
- ✅ Production Readiness Checks

## Quick Reference

```bash
# Run all tests (server required)
pytest

# Run unit tests only (no server needed)
pytest -k "not (integration or ivr or telugu or complete)"

# Run specific test file
pytest scripts/test_audio_processing.py -v

# Run with verbose output
pytest -vv

# Run with output capture disabled (see print statements)
pytest -s

# Start test server
./run_test_server.sh

# Check server status
curl http://localhost:5001/
```

## Task 9 Validation

To validate Task 9 (Error Handling) implementation:

```bash
# 1. Start the server
./run_test_server.sh

# 2. In another terminal, run error handling tests
pytest scripts/test_error_handling.py -v

# 3. Check integration error scenarios
pytest scripts/test_production_readiness.py -v
```

All tests should pass when the server is running!
