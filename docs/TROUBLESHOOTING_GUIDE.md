# VidyaVani Troubleshooting Guide

## Table of Contents
1. [Quick Diagnostics](#quick-diagnostics)
2. [Common Issues](#common-issues)
3. [Performance Problems](#performance-problems)
4. [API Integration Issues](#api-integration-issues)
5. [Audio Processing Problems](#audio-processing-problems)
6. [Content Retrieval Issues](#content-retrieval-issues)
7. [System Recovery Procedures](#system-recovery-procedures)
8. [Monitoring & Alerts](#monitoring--alerts)

## Quick Diagnostics

### System Health Check
```bash
# Run comprehensive system validation
python scripts/validate_setup.py

# Check API connectivity
python scripts/test_google_cloud_integration.py

# Verify FAISS index integrity
python scripts/verify_rag_implementation.py

# Test end-to-end flow
python scripts/test_complete_ivr_flow.py
```

### Health Check Endpoint
```bash
# Check system status
curl -f http://localhost:5000/api/health

# Expected response:
{
  "status": "healthy",
  "services": {
    "openai": "connected",
    "google_cloud": "connected",
    "faiss_index": "loaded",
    "cache": "active"
  },
  "performance": {
    "avg_response_time": 6.7,
    "cache_hit_rate": 0.45,
    "active_sessions": 3
  }
}
```

### Log Analysis Commands
```bash
# Check recent errors
tail -n 100 logs/app.log | grep ERROR

# Monitor performance
tail -f logs/performance.log

# Check API usage
grep "api_call" logs/app.log | tail -20

# Find slow responses
grep "response_time.*[1-9][0-9]" logs/performance.log
```

## Common Issues

### Issue 1: High Response Times (> 10 seconds)

#### Symptoms
- Students complaining about long waits
- Timeout errors in logs
- Poor user experience ratings

#### Diagnosis
```bash
# Check component performance
curl http://localhost:5000/api/metrics

# Monitor real-time performance
python scripts/test_performance_tracking.py

# Check system resources
top -p $(pgrep -f "python app.py")
```

#### Root Causes & Solutions

**1. API Rate Limiting**
```python
# Check OpenAI usage
import openai
usage = openai.Usage.retrieve()
if usage.total_usage > usage.hard_limit * 0.8:
    print("Approaching OpenAI rate limit")
    # Solution: Enable aggressive caching
```

**2. FAISS Index Issues**
```bash
# Check index file integrity
ls -la data/ncert/vector_db/faiss_index.bin

# Rebuild if corrupted
python scripts/add_ncert_pdf.py --rebuild-index
```

**3. Memory Pressure**
```bash
# Check memory usage
free -h
ps aux --sort=-%mem | head -10

# Solution: Restart application or increase memory
```

**4. Network Latency**
```bash
# Test API latency
ping -c 5 api.openai.com
ping -c 5 speech.googleapis.com

# Solution: Use regional endpoints or CDN
```

### Issue 2: Audio Quality Problems

#### Symptoms
- Poor STT accuracy (< 85%)
- Unclear TTS output
- Student complaints about audio

#### Diagnosis
```bash
# Test audio processing pipeline
python scripts/test_audio_processing.py

# Check codec compatibility
python scripts/validate_audio_formats.py

# Test with sample audio files
python -c "
from src.audio.audio_processor import AudioProcessor
processor = AudioProcessor()
result = processor.speech_to_text('test_audio.wav', 'english')
print(f'STT Result: {result}')
"
```

#### Solutions

**1. STT Configuration Optimization**
```python
# Adjust STT settings in config.py
STT_CONFIG = {
    'language_code': 'en-IN',
    'alternative_language_codes': ['te-IN'],
    'enable_automatic_punctuation': True,
    'enable_noise_reduction': True,
    'model': 'latest_long',
    'use_enhanced': True,
    'boost_adaptation': 20
}
```

**2. TTS Quality Enhancement**
```python
# Optimize TTS configuration
TTS_CONFIG = {
    'voice_name': 'en-IN-Wavenet-A',
    'language_code': 'en-IN',
    'speaking_rate': 0.9,
    'pitch': 0.0,
    'volume_gain_db': 2.0,
    'audio_encoding': 'LINEAR16',
    'sample_rate_hertz': 16000
}
```

**3. Audio Format Issues**
```bash
# Convert audio to supported format
ffmpeg -i input.wav -ar 16000 -ac 1 -f wav output.wav

# Check audio file properties
ffprobe input.wav
```

### Issue 3: Content Retrieval Failures

#### Symptoms
- "Content not found" responses
- Irrelevant answers to questions
- Low RAG accuracy (< 90%)

#### Diagnosis
```bash
# Test RAG engine
python scripts/test_rag_engine.py

# Check FAISS index status
python -c "
import faiss
index = faiss.read_index('data/ncert/vector_db/faiss_index.bin')
print(f'Index size: {index.ntotal} vectors')
"

# Verify content chunks
python scripts/verify_pdf_content.py
```

#### Solutions

**1. Rebuild Content Index**
```bash
# Full rebuild of FAISS index
python scripts/add_ncert_pdf.py --rebuild-index

# Verify rebuild success
python scripts/verify_rag_implementation.py
```

**2. Adjust Search Parameters**
```python
# Tune semantic search in src/rag/semantic_search.py
SEARCH_CONFIG = {
    'top_k': 5,  # Increase from 3
    'similarity_threshold': 0.65,  # Lower threshold
    'max_content_length': 600,  # Increase context
    'enable_reranking': True
}
```

**3. Content Quality Issues**
```bash
# Check content processing
python -c "
from src.content.content_processor import ContentProcessor
processor = ContentProcessor()
chunks = processor.get_content_stats()
print(f'Total chunks: {len(chunks)}')
print(f'Average length: {sum(len(c.content) for c in chunks) / len(chunks)}')
"
```

### Issue 4: API Integration Failures

#### Symptoms
- Authentication errors
- Service unavailable responses
- Quota exceeded messages

#### Diagnosis
```bash
# Test API connections
python scripts/test_google_cloud_integration.py

# Check environment variables
echo "OpenAI Key: ${OPENAI_API_KEY:0:10}..."
echo "GCP Project: $GOOGLE_CLOUD_PROJECT"

# Verify credentials
python -c "
import openai
import os
openai.api_key = os.getenv('OPENAI_API_KEY')
try:
    models = openai.Model.list()
    print('OpenAI connection: OK')
except Exception as e:
    print(f'OpenAI error: {e}')
"
```

#### Solutions

**1. API Key Issues**
```bash
# Verify API keys are set correctly
env | grep -E "(OPENAI|GOOGLE|EXOTEL)"

# Test OpenAI key
curl -H "Authorization: Bearer $OPENAI_API_KEY" \
     https://api.openai.com/v1/models

# Test Google Cloud authentication
gcloud auth application-default print-access-token
```

**2. Quota Management**
```python
# Monitor API usage
def check_api_quotas():
    # OpenAI usage check
    import openai
    usage = openai.Usage.retrieve()
    
    # Google Cloud quota check
    from google.cloud import monitoring_v3
    client = monitoring_v3.MetricServiceClient()
    
    return {
        'openai_remaining': usage.hard_limit - usage.total_usage,
        'gcp_quota_used': get_gcp_quota_usage()
    }
```

**3. Rate Limiting Implementation**
```python
# Add rate limiting to API calls
import time
from functools import wraps

def rate_limit(calls_per_minute=60):
    def decorator(func):
        last_called = [0.0]
        @wraps(func)
        def wrapper(*args, **kwargs):
            elapsed = time.time() - last_called[0]
            left_to_wait = 60.0 / calls_per_minute - elapsed
            if left_to_wait > 0:
                time.sleep(left_to_wait)
            ret = func(*args, **kwargs)
            last_called[0] = time.time()
            return ret
        return wrapper
    return decorator
```

## Performance Problems

### Slow Response Times

#### Investigation Steps
```bash
# 1. Check component timing
grep "component_times" logs/performance.log | tail -10

# 2. Monitor system resources
htop

# 3. Check network connectivity
ping -c 5 api.openai.com
traceroute api.openai.com

# 4. Test individual components
python -c "
import time
from src.audio.audio_processor import AudioProcessor
from src.rag.rag_engine import RAGEngine

# Test STT
start = time.time()
processor = AudioProcessor()
# ... test STT
print(f'STT time: {time.time() - start}s')

# Test RAG
start = time.time()
rag = RAGEngine()
# ... test RAG
print(f'RAG time: {time.time() - start}s')
"
```

#### Optimization Strategies

**1. Enable Parallel Processing**
```python
# In src/ivr/processing_pipeline.py
import asyncio

async def process_question_parallel(audio_data, session):
    # Start STT and content prep simultaneously
    stt_task = asyncio.create_task(speech_to_text(audio_data))
    prep_task = asyncio.create_task(prepare_content_retrieval())
    
    question_text = await stt_task
    retrieval_ready = await prep_task
    
    # Continue with RAG processing
    response = await generate_response(question_text)
    return response
```

**2. Implement Aggressive Caching**
```python
# Cache configuration
CACHE_CONFIG = {
    'response_ttl': 3600,  # 1 hour
    'audio_ttl': 86400,    # 24 hours
    'session_ttl': 1800,   # 30 minutes
    'preload_common': True
}
```

**3. Optimize FAISS Queries**
```python
# Tune FAISS parameters
index.nprobe = 8  # Reduce from 10 for speed
search_params = faiss.SearchParametersIVF()
search_params.nprobe = 8
search_params.max_codes = 1000
```

### Memory Issues

#### Symptoms
- Out of memory errors
- Slow garbage collection
- System becoming unresponsive

#### Solutions
```python
# Memory optimization in app.py
import gc
import psutil

def monitor_memory():
    process = psutil.Process()
    memory_mb = process.memory_info().rss / 1024 / 1024
    if memory_mb > 800:  # 800MB threshold
        gc.collect()
        print(f"Memory usage: {memory_mb:.1f}MB - GC triggered")

# Session cleanup
def cleanup_old_sessions():
    current_time = time.time()
    for session_id in list(active_sessions.keys()):
        if current_time - active_sessions[session_id].last_activity > 1800:
            del active_sessions[session_id]
```

## API Integration Issues

### OpenAI API Problems

#### Common Error Codes
```python
# Handle OpenAI errors gracefully
import openai

def safe_openai_call(prompt, **kwargs):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            **kwargs
        )
        return response.choices[0].message.content
    except openai.error.RateLimitError:
        print("Rate limit exceeded - using cached response")
        return get_cached_response(prompt)
    except openai.error.APIError as e:
        print(f"OpenAI API error: {e}")
        return "I'm having trouble processing your question. Please try again."
    except openai.error.Timeout:
        print("OpenAI timeout - retrying with shorter prompt")
        return safe_openai_call(prompt[:500], **kwargs)
```

### Google Cloud API Problems

#### Authentication Issues
```bash
# Check service account key
export GOOGLE_APPLICATION_CREDENTIALS="path/to/service-account.json"
gcloud auth activate-service-account --key-file=$GOOGLE_APPLICATION_CREDENTIALS

# Test authentication
gcloud auth list
gcloud projects list
```

#### STT/TTS Errors
```python
# Handle Google Cloud errors
from google.cloud import speech, texttospeech
from google.api_core import exceptions

def safe_stt_call(audio_data, language='en-IN'):
    client = speech.SpeechClient()
    try:
        response = client.recognize(config=config, audio=audio)
        return response.results[0].alternatives[0].transcript
    except exceptions.DeadlineExceeded:
        print("STT timeout - using shorter audio segment")
        return safe_stt_call(audio_data[:10000], language)
    except exceptions.InvalidArgument as e:
        print(f"Invalid audio format: {e}")
        return "Please speak more clearly and try again."
    except exceptions.ResourceExhausted:
        print("STT quota exceeded - using fallback")
        return "I'm having trouble hearing you. Please try again later."
```

### Exotel Integration Issues

#### Webhook Problems
```python
# Debug webhook calls
from flask import request
import json

@app.route('/webhook/debug', methods=['POST'])
def debug_webhook():
    print("Webhook received:")
    print(f"Headers: {dict(request.headers)}")
    print(f"Form data: {dict(request.form)}")
    print(f"JSON data: {request.get_json()}")
    return "OK"
```

#### XML Response Issues
```python
# Validate XML responses
from xml.etree.ElementTree import Element, SubElement, tostring

def create_exotel_response(message, next_action=None):
    response = Element('Response')
    say = SubElement(response, 'Say')
    say.set('voice', 'woman')
    say.set('language', 'en')
    say.text = message
    
    if next_action:
        redirect = SubElement(response, 'Redirect')
        redirect.text = next_action
    
    xml_str = tostring(response, encoding='unicode')
    print(f"Generated XML: {xml_str}")  # Debug output
    return xml_str
```

## Audio Processing Problems

### STT Accuracy Issues

#### Diagnosis
```python
# Test STT with known audio samples
def test_stt_accuracy():
    test_cases = [
        ("test_audio_clear.wav", "Why does light bend in water?"),
        ("test_audio_noisy.wav", "What is photosynthesis?"),
        ("test_audio_telugu.wav", "వెలుగు ఎందుకు వంగుతుంది?")
    ]
    
    for audio_file, expected in test_cases:
        result = speech_to_text(audio_file)
        accuracy = calculate_similarity(result, expected)
        print(f"{audio_file}: {accuracy:.2f}% accuracy")
```

#### Solutions
```python
# Improve STT configuration
STT_CONFIG = {
    'language_code': 'en-IN',
    'alternative_language_codes': ['te-IN', 'hi-IN'],
    'enable_automatic_punctuation': True,
    'enable_noise_reduction': True,
    'model': 'latest_long',
    'use_enhanced': True,
    'boost_adaptation': 20,
    'filter_profanity': False,
    'enable_word_confidence': True,
    'enable_word_time_offsets': True
}
```

### TTS Quality Issues

#### Common Problems
1. **Robotic voice**: Use Wavenet voices instead of standard
2. **Wrong pronunciation**: Adjust SSML markup
3. **Poor audio quality**: Check encoding settings

#### Solutions
```python
# Enhanced TTS configuration
def generate_speech(text, language='en-IN'):
    client = texttospeech.TextToSpeechClient()
    
    # Use SSML for better control
    ssml_text = f"""
    <speak>
        <prosody rate="0.9" pitch="0st" volume="loud">
            {text}
        </prosody>
    </speak>
    """
    
    synthesis_input = texttospeech.SynthesisInput(ssml=ssml_text)
    
    voice = texttospeech.VoiceSelectionParams(
        language_code=language,
        name='en-IN-Wavenet-A' if language == 'en-IN' else 'te-IN-Standard-A',
        ssml_gender=texttospeech.SsmlVoiceGender.FEMALE
    )
    
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.LINEAR16,
        sample_rate_hertz=16000,
        speaking_rate=0.9,
        pitch=0.0,
        volume_gain_db=2.0
    )
    
    response = client.synthesize_speech(
        input=synthesis_input,
        voice=voice,
        audio_config=audio_config
    )
    
    return response.audio_content
```

## System Recovery Procedures

### Emergency Recovery Steps

#### 1. Service Down Recovery
```bash
# Check if service is running
curl -f http://localhost:5000/api/health

# If down, check process
ps aux | grep "python app.py"

# Restart service
pkill -f "python app.py"
nohup python app.py > logs/app.log 2>&1 &

# Verify restart
sleep 5
curl -f http://localhost:5000/api/health
```

#### 2. Database Corruption Recovery
```bash
# Backup current state
cp -r data/ncert/vector_db data/ncert/vector_db.backup.$(date +%Y%m%d_%H%M%S)

# Rebuild FAISS index
python scripts/add_ncert_pdf.py --rebuild-index

# Verify integrity
python scripts/verify_rag_implementation.py
```

#### 3. Cache Corruption Recovery
```bash
# Clear all caches
redis-cli FLUSHALL  # If using Redis
# Or for in-memory cache, restart application

# Warm up cache with common questions
python scripts/preload_cache.py
```

### Rollback Procedures

#### Code Rollback
```bash
# Rollback to previous version
git log --oneline -10
git checkout <previous_commit_hash>

# Restart service
pkill -f "python app.py"
python app.py
```

#### Data Rollback
```bash
# Restore from backup
cp data/ncert/vector_db.backup.YYYYMMDD_HHMMSS/* data/ncert/vector_db/

# Verify restoration
python scripts/verify_rag_implementation.py
```

### Disaster Recovery

#### Full System Recovery
```bash
# 1. Clone fresh repository
git clone https://github.com/your-org/vidyavani.git vidyavani-recovery
cd vidyavani-recovery

# 2. Restore environment
cp ../vidyavani/.env .env
cp -r ../vidyavani/data/ncert/vector_db data/ncert/

# 3. Install dependencies
pip install -r requirements.txt

# 4. Verify setup
python scripts/validate_setup.py

# 5. Start service
python app.py
```

## Monitoring & Alerts

### Log Monitoring

#### Critical Error Patterns
```bash
# Monitor for critical errors
tail -f logs/app.log | grep -E "(CRITICAL|ERROR|FATAL)"

# API failure patterns
grep -E "(timeout|rate.limit|quota.exceeded)" logs/app.log

# Performance degradation
grep "response_time.*[1-9][0-9]" logs/performance.log
```

#### Automated Monitoring Script
```python
#!/usr/bin/env python3
# monitor.py - Continuous system monitoring

import time
import requests
import json
from datetime import datetime

def check_system_health():
    try:
        response = requests.get('http://localhost:5000/api/health', timeout=5)
        health_data = response.json()
        
        # Check response time
        if health_data['performance']['avg_response_time'] > 10:
            send_alert("High response time detected")
        
        # Check success rate
        if health_data['performance'].get('success_rate', 0) < 0.9:
            send_alert("Low success rate detected")
        
        # Check service status
        for service, status in health_data['services'].items():
            if status != 'connected' and status != 'loaded' and status != 'active':
                send_alert(f"Service {service} is {status}")
                
    except Exception as e:
        send_alert(f"Health check failed: {e}")

def send_alert(message):
    timestamp = datetime.now().isoformat()
    alert = {
        'timestamp': timestamp,
        'message': message,
        'severity': 'high'
    }
    print(f"ALERT: {json.dumps(alert)}")
    # Add webhook notification here

if __name__ == "__main__":
    while True:
        check_system_health()
        time.sleep(60)  # Check every minute
```

### Performance Alerts

#### Response Time Monitoring
```python
# Add to app.py
import time
from functools import wraps

def monitor_performance(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        duration = time.time() - start_time
        
        if duration > 10:  # Alert if > 10 seconds
            log_performance_alert(func.__name__, duration)
        
        return result
    return wrapper

def log_performance_alert(function_name, duration):
    alert = {
        'type': 'performance_alert',
        'function': function_name,
        'duration': duration,
        'timestamp': time.time()
    }
    print(f"PERFORMANCE ALERT: {json.dumps(alert)}")
```

### Health Check Automation

#### Continuous Health Monitoring
```bash
#!/bin/bash
# health_monitor.sh - Run every 5 minutes via cron

HEALTH_URL="http://localhost:5000/api/health"
LOG_FILE="logs/health_monitor.log"

# Check if service is responding
if curl -f -s $HEALTH_URL > /dev/null; then
    echo "$(date): Service healthy" >> $LOG_FILE
else
    echo "$(date): Service down - attempting restart" >> $LOG_FILE
    pkill -f "python app.py"
    sleep 5
    nohup python app.py > logs/app.log 2>&1 &
    echo "$(date): Service restarted" >> $LOG_FILE
fi
```

#### Cron Job Setup
```bash
# Add to crontab (crontab -e)
*/5 * * * * /path/to/vidyavani/health_monitor.sh
0 */6 * * * /path/to/vidyavani/cleanup_logs.sh
0 2 * * * /path/to/vidyavani/backup_data.sh
```

This comprehensive troubleshooting guide provides systematic approaches to diagnosing and resolving issues in the VidyaVani system, ensuring reliable operation and quick recovery from problems.