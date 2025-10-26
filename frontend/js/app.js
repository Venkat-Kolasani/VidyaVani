// VidyaVani Frontend Application
// Main application logic

// Configuration
const CONFIG = {
    // Auto-detect environment
    API_BASE: window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
        ? `http://${window.location.hostname}:${window.location.port || 5001}`
        : 'https://vidyavani.onrender.com',
};

// Application State
const state = {
    sessionId: null,
    phoneNumber: null,
    isActive: false,
    currentLanguage: 'english',
    messages: [],
    startTime: null,
    timerInterval: null,
    isMuted: false,
    isSpeakerOn: true,
};

// Initialize application
document.addEventListener('DOMContentLoaded', () => {
    initializeApp();
    updateTime();
    setInterval(updateTime, 1000);
});

async function initializeApp() {
    log('info', 'Initializing VidyaVani application...');
    
    // Check backend health
    await checkBackendHealth();
    
    // Load demo questions
    await loadDemoQuestions();
    
    // Initialize voice recognition
    initializeVoiceRecognition();
    
    log('success', 'Application initialized successfully');
}

// Backend Health Check
async function checkBackendHealth() {
    try {
        showToast('Connecting to backend...', 'info');
        
        const response = await fetchWithTimeout(`${CONFIG.API_BASE}/health`, {
            method: 'GET',
        }, 5000);
        
        const data = await response.json();
        
        if (data.status === 'healthy') {
            document.getElementById('backend-status').textContent = '🟢 Online';
            document.getElementById('backend-status').classList.add('online');
            showToast('Backend connected successfully', 'success');
            log('success', 'Backend health check passed');
            return true;
        } else {
            throw new Error('Backend unhealthy');
        }
    } catch (error) {
        console.error('Backend health check failed:', error);
        document.getElementById('backend-status').textContent = '🔴 Offline';
        document.getElementById('backend-status').classList.add('offline');
        showToast('Backend connection failed. Using demo mode.', 'warning');
        log('error', `Backend health check failed: ${error.message}`);
        return false;
    }
}

// Fetch with timeout
function fetchWithTimeout(url, options = {}, timeout = 10000) {
    return Promise.race([
        fetch(url, options),
        new Promise((_, reject) =>
            setTimeout(() => reject(new Error('Request timeout')), timeout)
        )
    ]);
}

// Start Learning Session
async function startSession() {
    try {
        log('info', 'Starting new learning session...');
        showToast('Starting session...', 'info');
        
        // Generate phone number
        state.phoneNumber = '+91' + Math.floor(Math.random() * 9000000000 + 1000000000);
        
        // Create session with backend
        const response = await fetchWithTimeout(`${CONFIG.API_BASE}/api/session/create`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                phone_number: state.phoneNumber,
                source: 'web_frontend'
            })
        }, 10000);
        
        if (response.ok) {
            const data = await response.json();
            state.sessionId = data.session_id;
            state.isActive = true;
            state.startTime = Date.now();
            
            // Update UI
            document.getElementById('session-id').textContent = state.sessionId.substring(0, 8) + '...';
            document.getElementById('welcome-screen').classList.add('hidden');
            document.getElementById('ivr-menu-screen').classList.remove('hidden');
            document.getElementById('end-btn').classList.remove('hidden');
            
            updateStatus('active', 'Session Active');
            startTimer();
            
            // Initialize IVR flow
            ivr.showIVRMenu('welcome');
            pipeline.reset();
            pipeline.updateStep('ivr', 'active', 'IVR System Ready');
            
            showToast('Session started successfully!', 'success');
            log('success', `Session created: ${state.sessionId}`);
            
            // Track in network
            trackNetworkCall('POST', '/api/session/create', 200, Date.now() - performance.now());
        } else {
            throw new Error('Failed to create session');
        }
    } catch (error) {
        console.error('Failed to start session:', error);
        showToast('Failed to start session. Please try again.', 'error');
        log('error', `Session start failed: ${error.message}`);
    }
}

// End Session
async function endSession() {
    if (!state.isActive) return;
    
    try {
        log('info', 'Ending session...');
        
        // End session with backend
        if (state.sessionId && state.phoneNumber) {
            await fetchWithTimeout(`${CONFIG.API_BASE}/api/session/${encodeURIComponent(state.phoneNumber)}/end`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            }, 5000);
        }
        
        // Reset state
        state.isActive = false;
        state.sessionId = null;
        state.phoneNumber = null;
        state.messages = [];
        stopTimer();
        
        // Reset UI
        document.getElementById('conversation-screen').classList.add('hidden');
        document.getElementById('ivr-menu-screen').classList.add('hidden');
        document.getElementById('welcome-screen').classList.remove('hidden');
        document.getElementById('end-btn').classList.add('hidden');
        document.getElementById('messages').innerHTML = '';
        document.getElementById('session-id').textContent = 'Not Started';
        
        // Reset pipeline
        pipeline.reset();
        
        updateStatus('', 'Ready to Start');
        
        showToast('Session ended', 'info');
        log('info', 'Session ended successfully');
    } catch (error) {
        console.error('Failed to end session:', error);
        log('error', `Session end failed: ${error.message}`);
    }
}

// Add Message to Conversation
function addMessage(role, text, audioUrl = null) {
    const messagesContainer = document.getElementById('messages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;
    
    const time = new Date().toLocaleTimeString('en-US', { 
        hour: '2-digit', 
        minute: '2-digit' 
    });
    
    let audioHtml = '';
    if (audioUrl) {
        audioHtml = `
            <div class="message-audio">
                <button class="play-audio-btn" onclick="playAudio('${audioUrl}')">
                    🔊 Play Audio
                </button>
            </div>
        `;
    }
    
    messageDiv.innerHTML = `
        <div class="message-bubble">
            ${text}
            ${audioHtml}
        </div>
        <span class="message-time">${time}</span>
    `;
    
    messagesContainer.appendChild(messageDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
    
    state.messages.push({ role, text, time, audioUrl });
}

// Play Audio Response
function playAudio(url) {
    const audio = new Audio(url);
    audio.play().catch(error => {
        console.error('Failed to play audio:', error);
        showToast('Failed to play audio', 'error');
    });
}

// Load Demo Questions
async function loadDemoQuestions() {
    try {
        const response = await fetchWithTimeout(`${CONFIG.API_BASE}/api/demo/questions`, {}, 5000);
        const data = await response.json();
        
        const chipsContainer = document.getElementById('question-chips');
        chipsContainer.innerHTML = '';
        
        // Show first 6 questions
        data.demo_questions.slice(0, 6).forEach(question => {
            const chip = document.createElement('button');
            chip.className = 'question-chip';
            chip.textContent = question;
            chip.onclick = () => askQuestion(question);
            chipsContainer.appendChild(chip);
        });
        
        log('success', `Loaded ${data.count} demo questions`);
    } catch (error) {
        console.error('Failed to load demo questions:', error);
        log('warning', 'Failed to load demo questions');
    }
}

// Ask Question (Text or Voice)
async function askQuestion(questionText) {
    if (!state.isActive) {
        showToast('Please start a session first', 'warning');
        return;
    }
    
    try {
        log('info', `Processing question: ${questionText}`);
        
        // Add user message
        addMessage('user', questionText);
        
        // Show processing screen
        showProcessingScreen();
        
        // Simulate pipeline flow
        pipeline.simulate(questionText);
        
        // Send to backend for processing
        const startTime = Date.now();
        const response = await fetchWithTimeout(`${CONFIG.API_BASE}/api/demo/response`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ question: questionText })
        }, 30000);
        
        const responseTime = Date.now() - startTime;
        
        if (response.ok) {
            const data = await response.json();
            
            // Hide processing screen
            hideProcessingScreen();
            
            // Add AI response
            if (data.response) {
                addMessage('assistant', data.response);
                
                // Speak the response
                if (state.isSpeakerOn) {
                    speakText(data.response);
                }
                
                showToast('Response generated successfully', 'success');
                log('success', `Response generated in ${responseTime}ms`);
            } else {
                // If no cached response, generate new one
                await generateAIResponse(questionText);
            }
            
            // Track network call
            trackNetworkCall('POST', '/api/demo/response', 200, responseTime);
            updateMetrics();
        } else {
            throw new Error('Failed to get response');
        }
    } catch (error) {
        console.error('Failed to process question:', error);
        hideProcessingScreen();
        addMessage('assistant', 'I apologize, but I encountered an error processing your question. Please try again.');
        showToast('Failed to process question', 'error');
        log('error', `Question processing failed: ${error.message}`);
    }
}

// Generate AI Response (fallback)
async function generateAIResponse(questionText) {
    try {
        // This would call the full processing pipeline
        // For now, we'll use a simple response
        const response = `I understand you're asking about "${questionText}". Let me help you with that. This is a demonstration of the AI-powered response system. In production, this would connect to the full RAG pipeline with NCERT content and Gemini AI.`;
        
        addMessage('assistant', response);
        
        if (state.isSpeakerOn) {
            speakText(response);
        }
    } catch (error) {
        console.error('Failed to generate AI response:', error);
    }
}

// Show/Hide Processing Screen
function showProcessingScreen() {
    document.getElementById('conversation-screen').classList.add('hidden');
    document.getElementById('processing-screen').classList.remove('hidden');
    updateStatus('processing', 'Processing...');
    
    // Animate processing steps
    const steps = document.querySelectorAll('.step');
    steps.forEach((step, index) => {
        setTimeout(() => {
            step.classList.add('active');
        }, index * 800);
    });
}

function hideProcessingScreen() {
    document.getElementById('processing-screen').classList.add('hidden');
    document.getElementById('conversation-screen').classList.remove('hidden');
    updateStatus('active', 'Session Active');
    
    // Reset steps
    document.querySelectorAll('.step').forEach(step => {
        step.classList.remove('active');
    });
}

// Update Status
function updateStatus(type, text) {
    const statusDot = document.getElementById('status-dot');
    const statusText = document.getElementById('status-text');
    
    statusDot.className = 'status-dot';
    if (type) statusDot.classList.add(type);
    statusText.textContent = text;
}

// Timer Functions
function startTimer() {
    state.timerInterval = setInterval(() => {
        const elapsed = Math.floor((Date.now() - state.startTime) / 1000);
        const minutes = Math.floor(elapsed / 60);
        const seconds = elapsed % 60;
        document.getElementById('call-timer').textContent = 
            `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
    }, 1000);
}

function stopTimer() {
    if (state.timerInterval) {
        clearInterval(state.timerInterval);
        state.timerInterval = null;
    }
    document.getElementById('call-timer').textContent = '00:00';
}

// Update Current Time
function updateTime() {
    const now = new Date();
    const hours = now.getHours();
    const minutes = now.getMinutes();
    document.getElementById('current-time').textContent = 
        `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}`;
}

// Control Functions
function toggleMute() {
    state.isMuted = !state.isMuted;
    const btn = document.getElementById('mute-btn');
    
    if (state.isMuted) {
        btn.classList.add('muted');
        // Change to muted mic icon
        btn.innerHTML = `
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <line x1="1" y1="1" x2="23" y2="23"></line>
                <path d="M9 9v3a3 3 0 0 0 5.12 2.12M15 9.34V4a3 3 0 0 0-5.94-.6"></path>
                <path d="M17 16.95A7 7 0 0 1 5 12v-2m14 0v2a7 7 0 0 1-.11 1.23"></path>
                <line x1="12" y1="19" x2="12" y2="23"></line>
                <line x1="8" y1="23" x2="16" y2="23"></line>
            </svg>
        `;
    } else {
        btn.classList.remove('muted');
        // Change to normal mic icon
        btn.innerHTML = `
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"></path>
                <path d="M19 10v2a7 7 0 0 1-14 0v-2"></path>
                <line x1="12" y1="19" x2="12" y2="23"></line>
                <line x1="8" y1="23" x2="16" y2="23"></line>
            </svg>
        `;
    }
    
    showToast(state.isMuted ? 'Microphone muted' : 'Microphone unmuted', 'info');
}

function toggleSpeaker() {
    state.isSpeakerOn = !state.isSpeakerOn;
    const btn = document.getElementById('speaker-btn');
    
    if (!state.isSpeakerOn) {
        btn.classList.add('off');
        // Change to speaker off icon
        btn.innerHTML = `
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"></polygon>
                <line x1="23" y1="9" x2="17" y2="15"></line>
                <line x1="17" y1="9" x2="23" y2="15"></line>
            </svg>
        `;
    } else {
        btn.classList.remove('off');
        // Change to speaker on icon
        btn.innerHTML = `
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"></polygon>
                <path d="M19.07 4.93a10 10 0 0 1 0 14.14"></path>
                <path d="M15.54 8.46a5 5 0 0 1 0 7.07"></path>
            </svg>
        `;
    }
    
    showToast(state.isSpeakerOn ? 'Speaker on' : 'Speaker off', 'info');
}

// Toast Notifications
function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;
    
    container.appendChild(toast);
    
    setTimeout(() => {
        toast.style.animation = 'slideInRight 0.3s ease reverse';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// Logging
function log(type, message) {
    const logsContainer = document.getElementById('logs-list');
    const logEntry = document.createElement('div');
    logEntry.className = `log-entry ${type}`;
    
    const time = new Date().toLocaleTimeString('en-US', { 
        hour12: false 
    });
    
    logEntry.innerHTML = `
        <span class="log-time">${time}</span>
        <span class="log-message">${message}</span>
    `;
    
    logsContainer.insertBefore(logEntry, logsContainer.firstChild);
    
    // Keep only last 50 logs
    while (logsContainer.children.length > 50) {
        logsContainer.removeChild(logsContainer.lastChild);
    }
}

// Developer Panel Functions
function toggleDeveloperPanel() {
    const panel = document.querySelector('.developer-panel');
    const btn = document.querySelector('.toggle-btn');
    
    if (panel.style.display === 'none') {
        panel.style.display = 'flex';
        btn.textContent = '−';
    } else {
        panel.style.display = 'none';
        btn.textContent = '+';
    }
}

function switchTab(tabName) {
    // Update tab buttons
    document.querySelectorAll('.tab').forEach(tab => {
        tab.classList.remove('active');
    });
    event.target.classList.add('active');
    
    // Update tab content
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
    });
    document.getElementById(`${tabName}-tab`).classList.add('active');
}

function clearNetwork() {
    document.getElementById('network-list').innerHTML = '<div class="empty-state">No network activity yet</div>';
    showToast('Network log cleared', 'info');
}

function clearLogs() {
    document.getElementById('logs-list').innerHTML = `
        <div class="log-entry info">
            <span class="log-time">${new Date().toLocaleTimeString('en-US', { hour12: false })}</span>
            <span class="log-message">Logs cleared</span>
        </div>
    `;
    showToast('Logs cleared', 'info');
}

// Export functions for use in other files
window.app = {
    state,
    CONFIG,
    startSession,
    endSession,
    askQuestion,
    showToast,
    log,
    addMessage,
    updateStatus,
};
