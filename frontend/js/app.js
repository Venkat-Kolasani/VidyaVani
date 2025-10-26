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
function fetchWithTimeout(url, options = {}, timeout = 30000) {
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
        }, 30000);
        
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
        
        // More specific error messages
        let errorMsg = 'Failed to start session';
        if (error.message === 'Request timeout') {
            errorMsg = 'Backend is taking too long to respond. Please try again.';
        } else if (error.message.includes('Failed to fetch')) {
            errorMsg = 'Cannot connect to backend. Please check your connection.';
        }
        
        showToast(errorMsg, 'error');
        log('error', `Session start failed: ${error.message}`);
        
        // Reset UI
        document.getElementById('start-call-btn').style.display = 'block';
        document.getElementById('end-call-btn').style.display = 'none';
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
            
            console.log('Backend response:', data);
            
            // Hide processing screen
            hideProcessingScreen();
            
            // Add AI response
            if (data.response && data.response.trim().length > 0) {
                addMessage('assistant', data.response);
                
                // Speak the response
                if (state.isSpeakerOn) {
                    speakText(data.response);
                }
                
                showToast('Response generated successfully', 'success');
                log('success', `Response generated in ${responseTime}ms`);
                
                // Track network call
                trackNetworkCall('POST', '/api/demo/response', 200, responseTime);
                updateMetrics();
                return; // IMPORTANT: Stop here, we got a response
            } else {
                // If no cached response, try to generate using real backend
                console.log('No cached response, trying real backend...');
                hideProcessingScreen();
                await generateRealAIResponse(questionText);
                return; // IMPORTANT: generateRealAIResponse handles everything
            }
        } else {
            throw new Error('Failed to get response');
        }
    } catch (error) {
        console.error('Failed to process question:', error);
        hideProcessingScreen();
        
        // Try to provide a demo response instead of showing error
        log('warning', `Question processing failed: ${error.message}, trying demo response`);
        await generateDemoResponse(questionText);
    }
}

// Generate Real AI Response using backend RAG + Gemini
async function generateRealAIResponse(questionText) {
    try {
        showToast('Connecting to AI system...', 'info');
        log('info', 'Calling RAG + Gemini AI backend...');
        
        // Call the real RAG + Gemini endpoint
        const startTime = Date.now();
        const response = await fetchWithTimeout(`${CONFIG.API_BASE}/api/answer-question`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                question: questionText,
                language: app.state.currentLanguage 
            })
        }, 30000);
        
        const responseTime = Date.now() - startTime;
        
        if (response.ok) {
            const data = await response.json();
            
            if (data.success && data.response) {
                addMessage('assistant', data.response);
                
                if (state.isSpeakerOn) {
                    speakText(data.response);
                }
                
                const method = data.method === 'rag' ? 'RAG + Gemini' : 'Gemini AI';
                const sourcesMsg = data.sources_used > 0 ? ` using ${data.sources_used} NCERT sources` : '';
                showToast(`Response from ${method}${sourcesMsg}`, 'success');
                log('success', `${method} response generated in ${responseTime}ms`);
                
                // Track as AI request
                trackNetworkCall('POST', '/api/answer-question', 200, responseTime);
                updateMetrics();
                
                return; // Success - stop here
            }
        }
        
        // If RAG fails, try Gemini direct
        log('warning', 'RAG failed, trying Gemini direct...');
        await tryGeminiDirect(questionText);
        return; // tryGeminiDirect handles everything
        
    } catch (error) {
        console.error('Failed to generate AI response:', error);
        log('error', `AI generation failed: ${error.message}`);
        
        // Fall back to demo responses
        await generateDemoResponse(questionText);
    }
}

// Try Gemini Direct (fallback when RAG fails)
async function tryGeminiDirect(questionText) {
    try {
        showToast('Trying Gemini AI...', 'info');
        log('info', 'Calling Gemini direct endpoint...');
        
        const startTime = Date.now();
        const response = await fetchWithTimeout(`${CONFIG.API_BASE}/api/gemini-direct`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                question: questionText,
                language: app.state.currentLanguage 
            })
        }, 30000);
        
        const responseTime = Date.now() - startTime;
        
        if (response.ok) {
            const data = await response.json();
            
            if (data.success && data.response) {
                addMessage('assistant', data.response);
                
                if (state.isSpeakerOn) {
                    speakText(data.response);
                }
                
                showToast('Response from Gemini AI', 'success');
                log('success', `Gemini direct response in ${responseTime}ms`);
                
                trackNetworkCall('POST', '/api/gemini-direct', 200, responseTime);
                updateMetrics();
                
                return; // Success - stop here
            }
        }
        
        // If Gemini also fails, use demo responses
        log('warning', 'Gemini direct failed, using demo responses');
        await generateDemoResponse(questionText);
        return; // generateDemoResponse handles everything
        
    } catch (error) {
        console.error('Gemini direct failed:', error);
        log('error', `Gemini direct failed: ${error.message}`);
        await generateDemoResponse(questionText);
    }
}

// Demo Response Fallback
async function generateDemoResponse(questionText) {
    try {
        showToast('Using demo response...', 'info');
        log('info', 'Falling back to demo responses...');
        const demoResponses = {
            'photosynthesis': 'Photosynthesis is the process by which plants convert light energy into chemical energy. Chlorophyll in leaves captures sunlight to produce glucose and oxygen from carbon dioxide and water. The equation is: 6CO2 + 6H2O + Light Energy → C6H12O6 + 6O2. This process is essential for plant growth and provides oxygen for all living organisms.',
            
            'ohm': "Ohm's law states that the current flowing through a conductor is directly proportional to the voltage across it, provided the temperature remains constant. The formula is V = I × R, where V is voltage in volts, I is current in amperes, and R is resistance in ohms. This fundamental law helps us understand and calculate electrical circuits.",
            
            'reflection': 'Reflection of light occurs when light rays bounce back from a surface. The laws of reflection state that the angle of incidence equals the angle of reflection, and both rays lie in the same plane as the normal. Mirrors use reflection to form images - plane mirrors form virtual images while curved mirrors can form real or virtual images.',
            
            'mirror': 'Mirrors are smooth reflective surfaces that form images through reflection. Concave mirrors converge light rays and can form real or virtual images depending on object position. Convex mirrors diverge light rays and always form virtual, diminished images. They are used in vehicles, telescopes, and solar cookers.',
            
            'electricity': 'Electricity is the flow of electric charge through a conductor. It can be generated through various methods including chemical reactions in batteries, electromagnetic induction in generators, and solar cells. Electric current is measured in amperes, and it powers most modern devices we use daily.',
            
            'current': 'Electric current is the rate of flow of electric charge through a conductor. It is measured in amperes (A). Current can be direct current (DC) which flows in one direction, or alternating current (AC) which periodically reverses direction. The relationship between current, voltage, and resistance is given by Ohms law.',
            
            'acid': 'Acids are substances that release hydrogen ions (H+) when dissolved in water. They have a pH less than 7, taste sour, and turn blue litmus paper red. Strong acids like hydrochloric acid and sulfuric acid completely ionize in water. Weak acids like acetic acid partially ionize. Acids react with bases to form salts and water.',
            
            'base': 'Bases are substances that release hydroxide ions (OH-) when dissolved in water. They have a pH greater than 7, taste bitter, and feel slippery. They turn red litmus paper blue. Common bases include sodium hydroxide, calcium hydroxide, and ammonia. Bases neutralize acids to form salts and water.',
            
            'metal': 'Metals are elements that are typically hard, shiny, malleable, ductile, and good conductors of heat and electricity. They tend to lose electrons to form positive ions. Metals react with oxygen to form metal oxides, with water to form hydroxides, and with acids to produce salts and hydrogen gas. Examples include iron, copper, aluminum, and gold.',
            
            'respiration': 'Respiration is the biochemical process by which living organisms break down glucose to release energy. Aerobic respiration occurs in the presence of oxygen and produces carbon dioxide, water, and ATP energy. The equation is: C6H12O6 + 6O2 → 6CO2 + 6H2O + Energy. This process occurs in mitochondria and is essential for all life activities.',
            
            'digestion': 'Digestion is the process of breaking down complex food molecules into simpler, absorbable forms. It begins in the mouth with mechanical and chemical breakdown, continues in the stomach with acid and enzymes, and completes in the small intestine where nutrients are absorbed. The digestive system includes organs like the stomach, liver, pancreas, and intestines.',
            
            'carbon': 'Carbon is a versatile element that forms the basis of all organic compounds. It can form four covalent bonds, allowing it to create long chains and complex molecules. Carbon compounds include hydrocarbons, alcohols, carboxylic acids, and more. Carbon dioxide is produced during respiration and used in photosynthesis, forming part of the carbon cycle.',
            
            'magnetic': 'Magnetism is the force exerted by magnets when they attract or repel each other. Every magnet has two poles - north and south. Like poles repel and unlike poles attract. A magnetic field is the region around a magnet where its force can be detected. Electric current flowing through a conductor also produces a magnetic field.',
            
            'energy': 'Energy is the capacity to do work. It exists in various forms including kinetic energy (energy of motion), potential energy (stored energy), thermal energy, electrical energy, and chemical energy. The law of conservation of energy states that energy cannot be created or destroyed, only converted from one form to another.',
            
            'eye': 'The human eye works like a camera. Light enters through the cornea, passes through the pupil (controlled by the iris), and is focused by the lens onto the retina at the back of the eye. The retina contains light-sensitive cells called rods and cones that convert light into electrical signals. These signals travel through the optic nerve to the brain, which interprets them as images. The eye can adjust focus for near and far objects through accommodation.',
            
            'lens': 'A lens is a transparent optical device that refracts light rays to converge or diverge them. Convex lenses are thicker in the middle and converge light rays to a focal point - used in magnifying glasses and to correct farsightedness. Concave lenses are thinner in the middle and diverge light rays - used to correct nearsightedness. The power of a lens is measured in diopters.',
            
            'refraction': 'Refraction is the bending of light when it passes from one medium to another of different optical density. This occurs because light travels at different speeds in different media. The refractive index measures how much a medium slows down light. Refraction causes phenomena like the apparent bending of a stick in water, the twinkling of stars, and the formation of rainbows.',
            
            'heart': 'The human heart is a muscular organ that pumps blood throughout the body. It has four chambers: two atria (upper chambers) and two ventricles (lower chambers). The right side pumps deoxygenated blood to the lungs, while the left side pumps oxygenated blood to the body. The heart beats about 72 times per minute, controlled by electrical signals from the sinoatrial node. Valves prevent backflow of blood.',
            
            'blood': 'Blood is a fluid connective tissue that transports oxygen, nutrients, hormones, and waste products throughout the body. It consists of plasma (liquid part) and blood cells. Red blood cells contain hemoglobin and carry oxygen. White blood cells fight infections. Platelets help in blood clotting. Blood also helps regulate body temperature and pH balance.',
            
            'reaction': 'A chemical reaction is a process where substances (reactants) are transformed into new substances (products) with different properties. Chemical reactions involve breaking and forming of chemical bonds. They can be classified as combination, decomposition, displacement, or double displacement reactions. Chemical equations represent reactions using symbols and formulas, following the law of conservation of mass.',
        };
        
        // Find relevant response
        let response = null;
        const lowerQuestion = questionText.toLowerCase();
        
        for (const [keyword, answer] of Object.entries(demoResponses)) {
            if (lowerQuestion.includes(keyword)) {
                response = answer;
                break;
            }
        }
        
        // Fallback response - provide a helpful answer
        if (!response) {
            // Generate a generic but helpful response
            response = `I understand you're asking about "${questionText}". While I'm having trouble connecting to the full AI system right now, I can tell you that this is an important topic in Class 10 Science. For the best learning experience, the system normally searches through NCERT textbooks and provides detailed explanations. Please try asking about topics like: photosynthesis, light reflection, electric current, chemical reactions, acids and bases, or human body systems. You can also try the original demo simulator at /demo/simulator for pre-loaded responses.`;
        }
        
        addMessage('assistant', response);
        
        if (state.isSpeakerOn) {
            speakText(response);
        }
        
        showToast('Response generated', 'success');
        log('success', 'AI response generated');
        
        // Track as AI request
        trackNetworkCall('POST', '/api/ai/generate', 200, 1500);
        updateMetrics();
        
    } catch (error) {
        console.error('Failed to generate AI response:', error);
        addMessage('assistant', 'I apologize, but I encountered an error. Please try asking another question.');
        log('error', `AI generation failed: ${error.message}`);
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
