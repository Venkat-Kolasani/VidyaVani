# VidyaVani Frontend - AI-Powered Voice Learning Assistant

## Overview

This is the production-ready web frontend for VidyaVani, an AI-powered voice learning assistant for Class 10 Science students. The frontend provides an immersive, voice-first learning experience that connects to the deployed backend API.

## Features

### 🎤 Voice-First Interaction
- **Real-time Speech Recognition**: Speak your questions naturally using browser's Web Speech API
- **Text-to-Speech Responses**: AI responses are automatically spoken back to you
- **Hands-free Learning**: No typing required - just speak and listen

### 🎨 Beautiful UI/UX
- **Modern Design**: Clean, professional interface with smooth animations
- **Phone Simulator**: Realistic phone interface showing the IVR experience
- **Dark Theme**: Easy on the eyes with a professional dark color scheme
- **Responsive**: Works on desktop, tablet, and mobile devices

### 🔧 Developer Console
- **Network Monitoring**: See all API calls in real-time
- **Performance Metrics**: Track response times, success rates, and AI requests
- **System Logs**: Monitor application events and errors
- **Live Charts**: Visualize response time trends

### 🚀 Real Backend Integration
- **Live API Calls**: Connects to deployed backend at vidyavani.onrender.com
- **Session Management**: Full session tracking with backend
- **Demo Questions**: Pre-loaded questions with cached responses
- **Error Handling**: Graceful fallbacks and error recovery

## Technology Stack

- **HTML5**: Semantic markup with accessibility features
- **CSS3**: Modern styling with animations and gradients
- **Vanilla JavaScript**: No frameworks - pure, performant JS
- **Web Speech API**: Browser-native speech recognition and synthesis
- **Fetch API**: Modern HTTP requests with timeout handling
- **Canvas API**: Real-time charts and visualizations

## File Structure

```
frontend/
├── index.html          # Main HTML structure
├── css/
│   └── styles.css      # Complete styling and animations
├── js/
│   ├── app.js          # Main application logic
│   ├── voice.js        # Voice recognition and TTS
│   └── network.js      # Network monitoring and metrics
└── README.md           # This file
```

## Usage

### Starting a Session

1. Click the "Start Learning Session" button
2. The system creates a session with the backend
3. You're now ready to ask questions!

### Asking Questions

**Voice Input (Recommended):**
1. Click the "Tap to Speak" button (microphone icon)
2. Speak your question clearly
3. The system will process and respond with voice

**Quick Questions:**
- Click any of the pre-loaded question chips
- Instant responses from cached data

### Features During Session

- **Mute/Unmute**: Control microphone access
- **Speaker On/Off**: Toggle audio responses
- **End Session**: Cleanly terminate the learning session

### Developer Console

Switch between tabs to view:
- **Network**: All API calls with status and timing
- **Metrics**: Performance statistics and charts
- **Logs**: System events and debugging info

## API Integration

The frontend connects to these backend endpoints:

- `GET /health` - System health check
- `POST /api/session/create` - Create new session
- `POST /api/session/{phone}/end` - End session
- `GET /api/demo/questions` - Load demo questions
- `POST /api/demo/response` - Get AI responses

## Browser Compatibility

### Fully Supported
- Chrome 80+ (Desktop & Mobile)
- Edge 80+
- Safari 14.1+
- Firefox 90+

### Voice Features Require
- Microphone permission
- HTTPS connection (or localhost)
- Web Speech API support

## Configuration

Edit `js/app.js` to change the API base URL:

```javascript
const CONFIG = {
    API_BASE: 'https://vidyavani.onrender.com',
    // For local development:
    // API_BASE: 'http://localhost:5000',
};
```

## Performance

- **Initial Load**: < 2 seconds
- **Voice Recognition**: Real-time (< 100ms latency)
- **API Response**: 1-3 seconds (depends on backend)
- **TTS Playback**: Instant start

## Accessibility

- Semantic HTML5 elements
- ARIA labels for screen readers
- Keyboard navigation support
- High contrast color scheme
- Clear visual feedback

## Demo Mode

If backend is unavailable:
- System automatically falls back to demo mode
- Shows cached responses for demo questions
- All UI features remain functional
- Network monitoring shows connection status

## Deployment

### Option 1: Serve from Flask Backend
The backend already serves this frontend at `/app`

### Option 2: Static Hosting
Deploy to Vercel, Netlify, or any static host:
```bash
# Build command: none (pure HTML/CSS/JS)
# Publish directory: frontend/
```

### Option 3: CDN
Upload to S3, CloudFlare Pages, or similar

## Development

### Local Testing
1. Open `index.html` directly in browser, OR
2. Use Python's HTTP server:
   ```bash
   cd frontend
   python -m http.server 8000
   ```
3. Visit `http://localhost:8000`

### Debugging
- Open browser DevTools (F12)
- Check Console for errors
- Use Network tab to monitor API calls
- The built-in Developer Console shows app-specific logs

## Future Enhancements

- [ ] Multi-language support (Telugu UI)
- [ ] Offline mode with service workers
- [ ] Voice activity detection
- [ ] Conversation history export
- [ ] Custom voice selection
- [ ] Dark/Light theme toggle
- [ ] Advanced analytics dashboard

## Support

For issues or questions:
- Check browser console for errors
- Verify microphone permissions
- Ensure backend is online (check /health endpoint)
- Review network tab in developer console

## License

Part of the VidyaVani AI-Powered IVR Learning System
