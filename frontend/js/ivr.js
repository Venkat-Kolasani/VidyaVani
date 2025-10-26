// IVR Flow Management
// Handles the phone keypad experience and IVR menu navigation

const ivrState = {
    currentMenu: 'welcome',
    language: null,
    grade: null,
    interactionMode: null,
};

// IVR Menu States
const IVR_MENUS = {
    welcome: {
        prompt: 'Welcome to VidyaVani! Your AI-powered learning assistant for Class 10 Science.',
        instruction: 'Please select your language:',
        options: [
            { key: '1', text: 'English' },
            { key: '2', text: 'Telugu (తెలుగు)' }
        ]
    },
    gradeConfirmation: {
        prompt: 'You are calling for Class 10 Science learning assistance.',
        instruction: 'Please select an option:',
        options: [
            { key: '1', text: 'Confirm Class 10' },
            { key: '2', text: 'Change Grade' }
        ]
    },
    interactionMode: {
        prompt: 'How would you like to interact?',
        instruction: 'Please select an option:',
        options: [
            { key: '1', text: 'Browse Topics' },
            { key: '2', text: 'Ask Question Directly' }
        ]
    },
    topicBrowsing: {
        prompt: 'Class 10 Science Topics:',
        instruction: 'Select a topic:',
        options: [
            { key: '1', text: 'Physics (Light, Electricity)' },
            { key: '2', text: 'Chemistry (Acids, Metals)' },
            { key: '3', text: 'Biology (Life Processes)' },
            { key: '9', text: 'Ask Question Instead' }
        ]
    }
};

// Handle Keypad Press
function handleKeypadPress(key) {
    if (!app.state.isActive) {
        app.showToast('Please start a session first', 'warning');
        return;
    }
    
    console.log('Keypad pressed:', key);
    app.log('info', `Keypad: ${key} pressed`);
    
    // Show visual feedback
    showKeypadFeedback(key);
    
    // Update pipeline
    updatePipelineStep('ivr', 'active', `Processing input: ${key}`);
    
    // Handle based on current menu
    setTimeout(() => {
        handleMenuSelection(key);
    }, 300);
}

// Show Keypad Feedback
function showKeypadFeedback(key) {
    // Create a visual feedback element
    const feedback = document.createElement('div');
    feedback.className = 'keypad-feedback';
    feedback.textContent = key;
    feedback.style.cssText = `
        position: fixed;
        top: 50%;
        left: 25%;
        transform: translate(-50%, -50%);
        background: rgba(99, 102, 241, 0.9);
        color: white;
        padding: 20px 30px;
        border-radius: 15px;
        font-size: 2rem;
        font-weight: 700;
        z-index: 10000;
        animation: fadeInOut 0.5s ease;
    `;
    
    document.body.appendChild(feedback);
    
    setTimeout(() => {
        feedback.remove();
    }, 500);
}

// Handle Menu Selection
function handleMenuSelection(key) {
    const currentMenu = IVR_MENUS[ivrState.currentMenu];
    
    if (!currentMenu) {
        app.log('error', `Invalid menu state: ${ivrState.currentMenu}`);
        return;
    }
    
    // Find the selected option
    const selectedOption = currentMenu.options.find(opt => opt.key === key);
    
    if (!selectedOption) {
        app.showToast('Invalid selection. Please try again.', 'warning');
        updatePipelineStep('ivr', 'completed', 'Invalid input');
        return;
    }
    
    app.log('success', `Selected: ${selectedOption.text}`);
    
    // Handle based on current menu
    switch (ivrState.currentMenu) {
        case 'welcome':
            handleLanguageSelection(key);
            break;
        case 'gradeConfirmation':
            handleGradeConfirmation(key);
            break;
        case 'interactionMode':
            handleInteractionMode(key);
            break;
        case 'topicBrowsing':
            handleTopicSelection(key);
            break;
    }
}

// Handle Language Selection
function handleLanguageSelection(key) {
    if (key === '1') {
        ivrState.language = 'english';
        app.state.currentLanguage = 'english';
        app.showToast('English selected', 'success');
    } else if (key === '2') {
        ivrState.language = 'telugu';
        app.state.currentLanguage = 'telugu';
        app.showToast('Telugu selected (తెలుగు ఎంచుకోబడింది)', 'success');
    }
    
    updatePipelineStep('ivr', 'completed', `Language: ${ivrState.language}`);
    
    // Move to grade confirmation
    setTimeout(() => {
        ivrState.currentMenu = 'gradeConfirmation';
        showIVRMenu('gradeConfirmation');
    }, 1000);
}

// Handle Grade Confirmation
function handleGradeConfirmation(key) {
    if (key === '1') {
        ivrState.grade = 'class10';
        app.showToast('Class 10 confirmed', 'success');
        updatePipelineStep('ivr', 'completed', 'Grade: Class 10');
        
        // Move to interaction mode
        setTimeout(() => {
            ivrState.currentMenu = 'interactionMode';
            showIVRMenu('interactionMode');
        }, 1000);
    } else if (key === '2') {
        app.showToast('Grade change not available in demo', 'info');
    }
}

// Handle Interaction Mode
function handleInteractionMode(key) {
    if (key === '1') {
        ivrState.interactionMode = 'browse';
        app.showToast('Browse topics selected', 'success');
        updatePipelineStep('ivr', 'completed', 'Mode: Browse Topics');
        
        // Move to topic browsing
        setTimeout(() => {
            ivrState.currentMenu = 'topicBrowsing';
            showIVRMenu('topicBrowsing');
        }, 1000);
    } else if (key === '2') {
        ivrState.interactionMode = 'ask';
        app.showToast('Ask question mode selected', 'success');
        updatePipelineStep('ivr', 'completed', 'Mode: Ask Question');
        
        // Switch to conversation screen
        setTimeout(() => {
            switchToConversationMode();
        }, 1000);
    }
}

// Handle Topic Selection
function handleTopicSelection(key) {
    const topics = {
        '1': 'Physics - Light and Electricity',
        '2': 'Chemistry - Acids and Metals',
        '3': 'Biology - Life Processes'
    };
    
    if (key === '9') {
        // Switch to ask question mode
        ivrState.interactionMode = 'ask';
        switchToConversationMode();
    } else if (topics[key]) {
        app.showToast(`Selected: ${topics[key]}`, 'success');
        updatePipelineStep('ivr', 'completed', `Topic: ${topics[key]}`);
        
        // Switch to conversation mode with topic context
        setTimeout(() => {
            switchToConversationMode();
            app.addMessage('assistant', `Great! You've selected ${topics[key]}. What would you like to learn about this topic?`);
        }, 1000);
    }
}

// Show IVR Menu
function showIVRMenu(menuName) {
    const menu = IVR_MENUS[menuName];
    if (!menu) return;
    
    const promptEl = document.querySelector('.ivr-prompt');
    const optionsEl = document.querySelector('.ivr-options');
    
    // Update prompt
    promptEl.innerHTML = `
        <p class="ivr-text">${menu.prompt}</p>
        <p class="ivr-instruction">${menu.instruction}</p>
    `;
    
    // Update options
    optionsEl.innerHTML = '';
    menu.options.forEach(option => {
        const optionDiv = document.createElement('div');
        optionDiv.className = 'ivr-option';
        optionDiv.onclick = () => handleKeypadPress(option.key);
        optionDiv.innerHTML = `
            <span class="option-key">${option.key}</span>
            <span class="option-text">${option.text}</span>
        `;
        optionsEl.appendChild(optionDiv);
    });
    
    updatePipelineStep('ivr', 'active', `Menu: ${menuName}`);
}

// Switch to Conversation Mode
function switchToConversationMode() {
    document.getElementById('ivr-menu-screen').classList.add('hidden');
    document.getElementById('conversation-screen').classList.remove('hidden');
    
    updatePipelineStep('ivr', 'completed', 'IVR flow completed');
    
    app.log('success', 'Switched to conversation mode');
    app.showToast('You can now ask questions!', 'success');
}

// Export functions
window.ivr = {
    handleKeypadPress,
    showIVRMenu,
    state: ivrState,
};
