// AI Processing Pipeline Visualization
// Shows real-time progress through the AI pipeline

const pipelineSteps = {
    ivr: { name: 'IVR System', status: 'idle', time: 0 },
    stt: { name: 'Speech-to-Text', status: 'waiting', time: 0 },
    rag: { name: 'RAG System', status: 'waiting', time: 0 },
    gemini: { name: 'Gemini AI', status: 'waiting', time: 0 },
    tts: { name: 'Text-to-Speech', status: 'waiting', time: 0 },
    response: { name: 'Response Delivered', status: 'waiting', time: 0 },
};

// Update Pipeline Step
function updatePipelineStep(stepId, status, message = '', time = 0) {
    const step = document.getElementById(`step-${stepId}`);
    if (!step) return;
    
    const statusEl = step.querySelector('.step-status');
    const timeEl = step.querySelector('.step-time');
    
    // Update status
    pipelineSteps[stepId].status = status;
    pipelineSteps[stepId].time = time;
    
    // Remove all status classes
    step.classList.remove('active', 'completed', 'error');
    
    // Add new status class
    if (status === 'active' || status === 'processing') {
        step.classList.add('active');
        statusEl.textContent = message || 'Processing...';
        statusEl.style.color = 'var(--primary-color)';
    } else if (status === 'completed' || status === 'success') {
        step.classList.add('completed');
        statusEl.textContent = message || 'Completed';
        statusEl.style.color = 'var(--success-color)';
        
        if (time > 0) {
            timeEl.textContent = `${time}ms`;
        }
    } else if (status === 'error' || status === 'failed') {
        step.classList.add('error');
        statusEl.textContent = message || 'Error';
        statusEl.style.color = 'var(--danger-color)';
    } else {
        statusEl.textContent = message || 'Waiting';
        statusEl.style.color = 'var(--text-secondary)';
    }
    
    // Log to console
    console.log(`Pipeline [${stepId}]: ${status} - ${message}`);
}

// Reset Pipeline
function resetPipeline() {
    Object.keys(pipelineSteps).forEach(stepId => {
        updatePipelineStep(stepId, 'waiting', '');
        const timeEl = document.getElementById(`step-${stepId}`).querySelector('.step-time');
        timeEl.textContent = '';
    });
    
    updatePipelineStep('ivr', 'idle', 'Ready');
}

// Simulate Full Pipeline Flow
async function simulatePipelineFlow(questionText) {
    const startTime = Date.now();
    
    try {
        // Step 1: IVR System
        updatePipelineStep('ivr', 'active', 'Receiving input');
        await sleep(300);
        updatePipelineStep('ivr', 'completed', 'Input received', 300);
        
        // Step 2: Speech-to-Text
        updatePipelineStep('stt', 'active', 'Converting speech...');
        await sleep(800);
        updatePipelineStep('stt', 'completed', `Transcribed: "${questionText.substring(0, 30)}..."`, 800);
        
        // Step 3: RAG System
        updatePipelineStep('rag', 'active', 'Searching NCERT content...');
        await sleep(1200);
        updatePipelineStep('rag', 'completed', 'Found 5 relevant passages', 1200);
        
        // Step 4: Gemini AI
        updatePipelineStep('gemini', 'active', 'Generating response...');
        await sleep(1500);
        updatePipelineStep('gemini', 'completed', 'Response generated', 1500);
        
        // Step 5: Text-to-Speech
        updatePipelineStep('tts', 'active', 'Converting to speech...');
        await sleep(600);
        updatePipelineStep('tts', 'completed', 'Audio generated', 600);
        
        // Step 6: Response Delivered
        updatePipelineStep('response', 'active', 'Delivering response...');
        await sleep(200);
        const totalTime = Date.now() - startTime;
        updatePipelineStep('response', 'completed', 'Response delivered', totalTime);
        
        app.log('success', `Pipeline completed in ${totalTime}ms`);
        
        return true;
    } catch (error) {
        console.error('Pipeline error:', error);
        app.log('error', `Pipeline failed: ${error.message}`);
        return false;
    }
}

// Helper function
function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

// Export functions
window.pipeline = {
    updateStep: updatePipelineStep,
    reset: resetPipeline,
    simulate: simulatePipelineFlow,
};
