// Network Monitoring and Metrics Tracking
// Tracks API calls and performance metrics

const networkState = {
    calls: [],
    metrics: {
        totalRequests: 0,
        successfulRequests: 0,
        failedRequests: 0,
        totalResponseTime: 0,
        aiRequests: 0,
    },
    responseTimes: [],
};

// Track Network Call
function trackNetworkCall(method, endpoint, status, responseTime) {
    const call = {
        id: Date.now() + Math.random(),
        method,
        endpoint,
        status,
        responseTime,
        timestamp: new Date().toLocaleTimeString('en-US', { hour12: false }),
        success: status >= 200 && status < 300,
    };
    
    networkState.calls.unshift(call);
    
    // Keep only last 50 calls
    if (networkState.calls.length > 50) {
        networkState.calls.pop();
    }
    
    // Update metrics
    networkState.metrics.totalRequests++;
    if (call.success) {
        networkState.metrics.successfulRequests++;
    } else {
        networkState.metrics.failedRequests++;
    }
    networkState.metrics.totalResponseTime += responseTime;
    
    // Track AI requests
    if (endpoint.includes('/demo/response') || endpoint.includes('/process-question')) {
        networkState.metrics.aiRequests++;
    }
    
    // Track response times for chart
    networkState.responseTimes.push({
        time: call.timestamp,
        value: responseTime,
    });
    if (networkState.responseTimes.length > 20) {
        networkState.responseTimes.shift();
    }
    
    // Update UI
    addNetworkItem(call);
    updateMetrics();
}

// Add Network Item to UI
function addNetworkItem(call) {
    const networkList = document.getElementById('network-list');
    
    // Remove empty state if present
    const emptyState = networkList.querySelector('.empty-state');
    if (emptyState) {
        emptyState.remove();
    }
    
    const item = document.createElement('div');
    item.className = `network-item ${call.success ? 'success' : 'error'}`;
    
    item.innerHTML = `
        <div>
            <span class="network-method">${call.method}</span>
            <span class="network-url">${call.endpoint}</span>
        </div>
        <div class="network-details">
            <span class="network-status ${call.success ? 'success' : 'error'}">
                ${call.status} ${call.success ? '✓' : '✗'}
            </span>
            <span>${call.responseTime}ms</span>
            <span>${call.timestamp}</span>
        </div>
    `;
    
    networkList.insertBefore(item, networkList.firstChild);
    
    // Keep only last 20 items in UI
    while (networkList.children.length > 20) {
        networkList.removeChild(networkList.lastChild);
    }
}

// Update Metrics Display
function updateMetrics() {
    const { totalRequests, successfulRequests, totalResponseTime, aiRequests } = networkState.metrics;
    
    // Update metric cards
    document.getElementById('total-requests').textContent = totalRequests;
    document.getElementById('ai-requests').textContent = aiRequests;
    
    // Calculate average response time
    const avgResponseTime = totalRequests > 0 
        ? Math.round(totalResponseTime / totalRequests) 
        : 0;
    document.getElementById('avg-response-time').textContent = `${avgResponseTime}ms`;
    
    // Calculate success rate
    const successRate = totalRequests > 0 
        ? Math.round((successfulRequests / totalRequests) * 100) 
        : 100;
    document.getElementById('success-rate').textContent = `${successRate}%`;
    
    // Update chart
    updateResponseChart();
}

// Update Response Time Chart
function updateResponseChart() {
    const canvas = document.getElementById('response-chart');
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    const width = canvas.width = canvas.offsetWidth;
    const height = canvas.height = 200;
    
    // Clear canvas
    ctx.clearRect(0, 0, width, height);
    
    if (networkState.responseTimes.length === 0) {
        // Show empty state
        ctx.fillStyle = '#94a3b8';
        ctx.font = '14px Inter';
        ctx.textAlign = 'center';
        ctx.fillText('No data yet', width / 2, height / 2);
        return;
    }
    
    // Draw chart
    const data = networkState.responseTimes;
    const maxValue = Math.max(...data.map(d => d.value), 100);
    const padding = 40;
    const chartWidth = width - padding * 2;
    const chartHeight = height - padding * 2;
    
    // Draw axes
    ctx.strokeStyle = '#475569';
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(padding, padding);
    ctx.lineTo(padding, height - padding);
    ctx.lineTo(width - padding, height - padding);
    ctx.stroke();
    
    // Draw grid lines
    ctx.strokeStyle = '#334155';
    ctx.lineWidth = 0.5;
    for (let i = 0; i <= 4; i++) {
        const y = padding + (chartHeight / 4) * i;
        ctx.beginPath();
        ctx.moveTo(padding, y);
        ctx.lineTo(width - padding, y);
        ctx.stroke();
    }
    
    // Draw line
    if (data.length > 1) {
        ctx.strokeStyle = '#6366f1';
        ctx.lineWidth = 2;
        ctx.beginPath();
        
        data.forEach((point, index) => {
            const x = padding + (chartWidth / (data.length - 1)) * index;
            const y = height - padding - (point.value / maxValue) * chartHeight;
            
            if (index === 0) {
                ctx.moveTo(x, y);
            } else {
                ctx.lineTo(x, y);
            }
        });
        
        ctx.stroke();
        
        // Draw points
        ctx.fillStyle = '#6366f1';
        data.forEach((point, index) => {
            const x = padding + (chartWidth / (data.length - 1)) * index;
            const y = height - padding - (point.value / maxValue) * chartHeight;
            
            ctx.beginPath();
            ctx.arc(x, y, 3, 0, Math.PI * 2);
            ctx.fill();
        });
    }
    
    // Draw labels
    ctx.fillStyle = '#94a3b8';
    ctx.font = '11px Inter';
    ctx.textAlign = 'right';
    
    // Y-axis labels
    for (let i = 0; i <= 4; i++) {
        const value = Math.round((maxValue / 4) * (4 - i));
        const y = padding + (chartHeight / 4) * i;
        ctx.fillText(`${value}ms`, padding - 10, y + 4);
    }
}

// Monitor Backend Health
async function monitorBackendHealth() {
    try {
        const startTime = performance.now();
        const response = await fetch(`${app.CONFIG.API_BASE}/health`);
        const responseTime = Math.round(performance.now() - startTime);
        
        if (response.ok) {
            trackNetworkCall('GET', '/health', 200, responseTime);
            return true;
        } else {
            trackNetworkCall('GET', '/health', response.status, responseTime);
            return false;
        }
    } catch (error) {
        trackNetworkCall('GET', '/health', 0, 0);
        return false;
    }
}

// Start periodic health monitoring
setInterval(() => {
    if (app.state.isActive) {
        monitorBackendHealth();
    }
}, 30000); // Every 30 seconds

// Performance Observer (if supported)
if ('PerformanceObserver' in window) {
    try {
        const observer = new PerformanceObserver((list) => {
            for (const entry of list.getEntries()) {
                if (entry.entryType === 'resource' && entry.name.includes(app.CONFIG.API_BASE)) {
                    const url = new URL(entry.name);
                    const endpoint = url.pathname;
                    const responseTime = Math.round(entry.duration);
                    
                    // Only track if not already tracked
                    const recentCall = networkState.calls.find(call => 
                        call.endpoint === endpoint && 
                        Math.abs(call.responseTime - responseTime) < 10
                    );
                    
                    if (!recentCall) {
                        trackNetworkCall('GET', endpoint, 200, responseTime);
                    }
                }
            }
        });
        
        observer.observe({ entryTypes: ['resource'] });
    } catch (error) {
        console.warn('Performance Observer not supported:', error);
    }
}

// Export functions
window.network = {
    trackNetworkCall,
    updateMetrics,
    monitorBackendHealth,
    getMetrics: () => networkState.metrics,
    getCalls: () => networkState.calls,
};
