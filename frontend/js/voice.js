// Voice Recognition and Speech Synthesis
// Handles voice input and audio output

let recognition = null;
let synthesis = window.speechSynthesis;
let isListening = false;
let currentUtterance = null;

// Initialize Voice Recognition
function initializeVoiceRecognition() {
    // Check for browser support
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    
    if (!SpeechRecognition) {
        console.warn('Speech recognition not supported in this browser');
        app.log('warning', 'Speech recognition not supported in this browser');
        app.showToast('Voice input not supported in this browser', 'warning');
        return;
    }
    
    recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = true;
    recognition.lang = 'en-IN'; // Indian English
    recognition.maxAlternatives = 1;
    
    recognition.onstart = () => {
        isListening = true;
        updateVoiceUI(true);
        app.log('info', 'Voice recognition started');
    };
    
    recognition.onresult = (event) => {
        const transcript = Array.from(event.results)
            .map(result => result[0])
            .map(result => result.transcript)
            .join('');
        
        console.log('Speech recognition result:', transcript, 'isFinal:', event.results[0].isFinal);
        
        // Show interim results in UI
        if (!event.results[0].isFinal) {
            // Show interim transcript
            app.log('info', `Listening: ${transcript}`);
        } else {
            // Final result - process it
            console.log('Final transcript:', transcript);
            handleVoiceInput(transcript);
        }
    };
    
    recognition.onerror = (event) => {
        console.error('Speech recognition error:', event.error);
        isListening = false;
        updateVoiceUI(false);
        
        let errorMessage = 'Voice recognition error';
        switch (event.error) {
            case 'no-speech':
                errorMessage = 'No speech detected. Please try again.';
                break;
            case 'audio-capture':
                errorMessage = 'Microphone not accessible. Please check permissions.';
                break;
            case 'not-allowed':
                errorMessage = 'Microphone permission denied. Please allow microphone access.';
                break;
            default:
                errorMessage = `Voice recognition error: ${event.error}`;
        }
        
        app.showToast(errorMessage, 'error');
        app.log('error', errorMessage);
    };
    
    recognition.onend = () => {
        isListening = false;
        updateVoiceUI(false);
        app.log('info', 'Voice recognition ended');
    };
    
    app.log('success', 'Voice recognition initialized');
}

// Toggle Voice Input
function toggleVoiceInput() {
    if (!app.state.isActive) {
        app.showToast('Please start a session first', 'warning');
        return;
    }
    
    if (app.state.isMuted) {
        app.showToast('Please unmute microphone first', 'warning');
        return;
    }
    
    if (!recognition) {
        app.showToast('Voice recognition not available', 'error');
        return;
    }
    
    if (isListening) {
        stopListening();
    } else {
        startListening();
    }
}

// Start Listening
function startListening() {
    try {
        recognition.start();
        app.showToast('Listening... Speak your question', 'info');
    } catch (error) {
        console.error('Failed to start recognition:', error);
        app.showToast('Failed to start voice recognition', 'error');
    }
}

// Stop Listening
function stopListening() {
    try {
        recognition.stop();
    } catch (error) {
        console.error('Failed to stop recognition:', error);
    }
}

// Handle Voice Input
function handleVoiceInput(transcript) {
    if (!transcript || transcript.trim().length === 0) {
        app.showToast('No speech detected. Please try again.', 'warning');
        app.log('warning', 'Empty transcript received');
        return;
    }
    
    const cleanTranscript = transcript.trim();
    console.log('Processing voice input:', cleanTranscript);
    
    app.log('success', `Voice input received: ${cleanTranscript}`);
    app.showToast('Processing your question...', 'info');
    
    // Process the question
    app.askQuestion(cleanTranscript);
}

// Update Voice UI
function updateVoiceUI(listening) {
    const voiceBtn = document.getElementById('voice-btn');
    const visualizer = document.getElementById('voice-visualizer');
    const listeningIndicator = document.getElementById('listening-indicator');
    
    if (listening) {
        voiceBtn.classList.add('listening');
        voiceBtn.querySelector('.btn-text').textContent = 'Listening... Speak now!';
        visualizer.classList.add('active');
        listeningIndicator.classList.remove('hidden');
        
        // Change mic icon color when listening
        const micSvg = voiceBtn.querySelector('.mic-icon svg');
        if (micSvg) {
            micSvg.style.stroke = '#fff';
        }
    } else {
        voiceBtn.classList.remove('listening');
        voiceBtn.querySelector('.btn-text').textContent = 'Tap to Speak';
        visualizer.classList.remove('active');
        listeningIndicator.classList.add('hidden');
        
        // Reset mic icon color
        const micSvg = voiceBtn.querySelector('.mic-icon svg');
        if (micSvg) {
            micSvg.style.stroke = '#fff';
        }
    }
}

// Text-to-Speech
function speakText(text, lang = 'en-IN') {
    // Stop any ongoing speech
    if (synthesis.speaking) {
        synthesis.cancel();
    }
    
    if (!text || text.trim().length === 0) {
        return;
    }
    
    // Create utterance
    currentUtterance = new SpeechSynthesisUtterance(text);
    currentUtterance.lang = lang;
    currentUtterance.rate = 0.9; // Slightly slower for clarity
    currentUtterance.pitch = 1.0;
    currentUtterance.volume = 1.0;
    
    // Get available voices
    const voices = synthesis.getVoices();
    
    // Try to find Indian English voice
    const indianVoice = voices.find(voice => 
        voice.lang === 'en-IN' || 
        voice.lang.startsWith('en-') && voice.name.includes('India')
    );
    
    if (indianVoice) {
        currentUtterance.voice = indianVoice;
    }
    
    currentUtterance.onstart = () => {
        app.log('info', 'Speech synthesis started');
    };
    
    currentUtterance.onend = () => {
        app.log('info', 'Speech synthesis completed');
        currentUtterance = null;
    };
    
    currentUtterance.onerror = (event) => {
        console.error('Speech synthesis error:', event);
        app.log('error', `Speech synthesis error: ${event.error}`);
        currentUtterance = null;
    };
    
    // Speak
    synthesis.speak(currentUtterance);
    app.log('info', 'Speaking response...');
}

// Stop Speaking
function stopSpeaking() {
    if (synthesis.speaking) {
        synthesis.cancel();
        app.log('info', 'Speech synthesis stopped');
    }
}

// Change Language
function changeLanguage(lang) {
    if (recognition) {
        recognition.lang = lang === 'telugu' ? 'te-IN' : 'en-IN';
        app.state.currentLanguage = lang;
        app.log('info', `Language changed to ${lang}`);
    }
}

// Load voices (some browsers need this)
if (synthesis.onvoiceschanged !== undefined) {
    synthesis.onvoiceschanged = () => {
        const voices = synthesis.getVoices();
        if (window.app && window.app.log) {
            window.app.log('info', `Loaded ${voices.length} voices`);
        }
    };
}

// Export functions
window.voice = {
    toggleVoiceInput,
    speakText,
    stopSpeaking,
    changeLanguage,
    isListening: () => isListening,
};
