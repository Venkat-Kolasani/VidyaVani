# VidyaVani API Endpoints Documentation

**Base URL**: `https://vidyavani.onrender.com`

## 📋 **Complete API Endpoints List**

### 🏠 **Core System Endpoints**

| Method | Endpoint | Purpose | Response Type |
|--------|----------|---------|---------------|
| `GET` | `/` | System information and endpoint directory | JSON |
| `GET` | `/health` | Basic system health check | JSON |
| `GET` | `/api/health` | Detailed health check with component status | JSON |
| `GET` | `/health/detailed` | Comprehensive health diagnostics | JSON |
| `GET` | `/health/history` | Health check history and trends | JSON |
| `POST` | `/health/restart` | Manual system restart (admin only) | JSON |

### 📞 **IVR Webhook Endpoints (Exotel Integration)**

| Method | Endpoint | Purpose | Response Type |
|--------|----------|---------|---------------|
| `POST` | `/webhook/incoming-call` | Handle incoming call initiation | XML (TwiML) |
| `POST` | `/webhook/language-selection` | Process language choice (English/Telugu) | XML (TwiML) |
| `POST` | `/webhook/grade-confirmation` | Confirm Class 10 grade selection | XML (TwiML) |
| `POST` | `/webhook/interaction-mode` | Redirect to interaction mode selection | XML (TwiML) |
| `POST` | `/webhook/interaction-mode-selection` | Handle browse/ask mode selection | XML (TwiML) |
| `POST` | `/webhook/question-recording` | Process voice question recording | XML (TwiML) |
| `POST` | `/webhook/recording-status` | Handle recording completion callback | JSON |
| `POST` | `/webhook/response-delivery` | Deliver AI-generated response | XML (TwiML) |
| `POST` | `/webhook/follow-up-menu` | Handle follow-up menu selections | XML (TwiML) |
| `POST` | `/webhook/error-recovery` | Handle error recovery options | XML (TwiML) |
| `POST` | `/webhook/call-end` | Process call termination | JSON |

### 👤 **Session Management API**

| Method | Endpoint | Purpose | Response Type |
|--------|----------|---------|---------------|
| `POST` | `/api/session/create` | Create new user session | JSON |
| `GET` | `/api/session/<phone_number>` | Get session details by phone number | JSON |
| `PUT` | `/api/session/<phone_number>/language` | Update session language preference | JSON |
| `PUT` | `/api/session/<phone_number>/menu` | Update current menu state | JSON |
| `POST` | `/api/session/<phone_number>/question` | Add question to session history | JSON |
| `POST` | `/api/session/<phone_number>/response` | Add AI response to session | JSON |
| `GET` | `/api/session/<phone_number>/context` | Get conversation context for RAG | JSON |
| `POST` | `/api/session/<phone_number>/end` | End user session | JSON |
| `DELETE` | `/api/session/<phone_number>/cleanup` | Remove session from memory | JSON |
| `GET` | `/api/session/stats` | Get session statistics and analytics | JSON |

### 🤖 **AI Question Processing API**

| Method | Endpoint | Purpose | Response Type |
|--------|----------|---------|---------------|
| `POST` | `/api/process-question` | Process question with full AI pipeline | JSON |
| `GET` | `/api/processing-status/<phone_number>` | Get current processing status | JSON |
| `GET` | `/api/demo/questions` | Get curated demo questions list | JSON |
| `POST` | `/api/demo/response` | Get AI response for demo questions | JSON |
| `GET` | `/api/demo/recordings` | Get demo call recordings | JSON |
| `GET` | `/api/demo/summary` | Get demo session summaries | JSON |

### 📊 **Performance Monitoring API**

| Method | Endpoint | Purpose | Response Type |
|--------|----------|---------|---------------|
| `GET` | `/api/performance/metrics` | Comprehensive performance metrics | JSON |
| `GET` | `/api/performance/components` | Component-specific performance data | JSON |
| `GET` | `/api/performance/api-usage` | API usage and cost tracking | JSON |
| `GET` | `/api/performance/cache` | Cache performance metrics | JSON |
| `GET` | `/api/performance/alerts` | Recent performance alerts | JSON |
| `GET` | `/api/performance/dashboard` | Performance dashboard data | JSON |
| `POST` | `/api/performance/export` | Export performance metrics | JSON |
| `POST` | `/api/performance/reset` | Reset performance metrics (testing) | JSON |

### 🔧 **Error Handling & Debugging API**

| Method | Endpoint | Purpose | Response Type |
|--------|----------|---------|---------------|
| `GET` | `/api/errors/summary` | Error summary and statistics | JSON |
| `GET` | `/api/errors/debugging-report` | Detailed debugging information | JSON |
| `GET` | `/api/docs` | API documentation | HTML/JSON |

### 🎵 **Audio Storage API**

| Method | Endpoint | Purpose | Response Type |
|--------|----------|---------|---------------|
| `GET` | `/audio/<filename>` | Serve audio files for playback | Audio File |
| `GET` | `/audio-storage/stats` | Audio storage statistics | JSON |
| `POST` | `/audio-storage/test` | Test audio storage functionality | JSON |

### 🖥️ **Web Interface Endpoints**

| Method | Endpoint | Purpose | Response Type |
|--------|----------|---------|---------------|
| `GET` | `/demo/simulator` | Interactive phone simulator interface | HTML |
| `GET` | `/demo/processing-dashboard` | Processing pipeline dashboard | HTML |
| `GET` | `/demo/xml-responses` | Demo XML response examples | HTML |
| `GET` | `/dashboard` | Performance dashboard page | HTML |

## 📝 **Detailed Endpoint Descriptions**

### **Core System Health**

#### `GET /health`
**Purpose**: Quick system health check
**Response**: 
```json
{
  "service": "VidyaVani IVR Learning System",
  "status": "healthy",
  "timestamp": "2025-10-21T15:42:47.617377"
}
```

#### `GET /api/health`
**Purpose**: Detailed health check with component status
**Response**:
```json
{
  "components": {
    "critical": 2,
    "healthy": 1,
    "warning": 2
  },
  "deployment": {
    "environment": "production",
    "log_level": "INFO",
    "max_requests": 1000,
    "platform": "render"
  },
  "status": "critical",
  "timestamp": "2025-10-21T15:42:47.617377"
}
```

### **IVR Webhook Integration**

#### `POST /webhook/incoming-call`
**Purpose**: Handle incoming phone calls from Exotel/Twilio
**Expected Input**:
```
From: +919876543210
To: +918012345678
CallSid: unique_call_id
```
**Response**: XML (TwiML) for IVR flow
```xml
<Response>
  <Say voice="alice" language="en-IN">Welcome to VidyaVani...</Say>
  <Gather numDigits="1" timeout="10" action="/webhook/language-selection">
    <Say>Press 1 for English or Press 2 for Telugu</Say>
  </Gather>
</Response>
```

### **AI Question Processing**

#### `POST /api/demo/response`
**Purpose**: Get AI response for demo questions
**Input**:
```json
{
  "question": "What is reflection of light?"
}
```
**Response**:
```json
{
  "response": "Reflection of light is the bouncing back of light rays when they hit a surface...",
  "processing_time": 1.23,
  "confidence": 0.95
}
```

#### `GET /api/demo/questions`
**Purpose**: Get curated demo questions
**Response**:
```json
{
  "count": 20,
  "demo_questions": [
    "What is reflection of light?",
    "How does a concave mirror work?",
    "What is the difference between AC and DC current?",
    "Explain Ohm's law"
  ]
}
```

### **Performance Monitoring**

#### `GET /api/performance/metrics`
**Purpose**: Get comprehensive system performance data
**Response**:
```json
{
  "api_metrics": {
    "exotel": {
      "total_requests": 0,
      "success_rate": 0.0,
      "rate_limit_hits": 0
    },
    "google_stt": {
      "total_requests": 0,
      "success_rate": 0.0,
      "total_tokens_used": 0
    }
  },
  "system_metrics": {
    "cpu_usage": 45.2,
    "memory_usage": 67.8,
    "disk_usage": 23.1
  }
}
```

## 🔐 **Authentication & Security**

- **Public Endpoints**: All demo and health endpoints are publicly accessible
- **Webhook Endpoints**: Designed for Exotel/Twilio integration (validate request signatures in production)
- **Admin Endpoints**: `/health/restart` requires admin authentication
- **Rate Limiting**: Implemented on processing endpoints to prevent abuse

## 🌐 **CORS & Integration**

- **CORS Enabled**: All API endpoints support cross-origin requests
- **Content Types**: 
  - JSON APIs: `application/json`
  - Webhooks: `application/x-www-form-urlencoded`
  - Audio: `audio/wav`, `audio/mp3`
  - Web Pages: `text/html`

## 📱 **Mobile & Browser Support**

- **Responsive**: All web interfaces work on mobile devices
- **Voice Support**: Browser-based speech recognition and synthesis
- **Progressive Web App**: Offline capability for demo interfaces

## 🚀 **Production Ready Features**

- **Health Monitoring**: Comprehensive health checks and alerts
- **Performance Tracking**: Real-time metrics and analytics
- **Error Handling**: Robust error recovery and logging
- **Session Management**: Complete user state tracking
- **Audio Processing**: Google Cloud STT/TTS integration
- **AI Integration**: Gemini 2.5 Flash for intelligent responses
- **Bilingual Support**: English and Telugu language processing

## 🔗 **Integration Examples**

### **Frontend Integration**
```javascript
// Get system health
const health = await fetch('https://vidyavani.onrender.com/health');

// Process a question
const response = await fetch('https://vidyavani.onrender.com/api/demo/response', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ question: 'What is photosynthesis?' })
});
```

### **Phone Service Integration**
```bash
# Configure webhook URL in Exotel/Twilio
WEBHOOK_URL="https://vidyavani.onrender.com/webhook/incoming-call"
METHOD="POST"
CONTENT_TYPE="application/x-www-form-urlencoded"
```

This comprehensive API provides everything needed for a complete AI-powered phone tutoring system! 🎓📞