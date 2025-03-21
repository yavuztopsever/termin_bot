// Dashboard state
let charts = new Map();
let ws = null;

// Initialize WebSocket connection
function initWebSocket() {
    ws = new WebSocket(`ws://${window.location.host}/ws`);
    
    ws.onopen = () => {
        console.log('WebSocket connected');
    };
    
    ws.onclose = () => {
        console.log('WebSocket disconnected');
        // Attempt to reconnect after 5 seconds
        setTimeout(initWebSocket, 5000);
    };
    
    ws.onerror = (error) => {
        console.error('WebSocket error:', error);
    };
    
    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.type === 'update') {
            updateDashboard(data.data);
        }
    };
}

// Update dashboard with new data
function updateDashboard(data) {
    updateHealthStatus(data.health);
    updateMetrics(data.metrics);
    updateAlerts(data.alerts);
}

// Update health status section
function updateHealthStatus(health) {
    const container = document.getElementById('health-status');
    container.innerHTML = '';
    
    // Overall status
    const overallStatus = document.createElement('div');
    overallStatus.className = 'col-span-full bg-white p-4 rounded-lg shadow';
    overallStatus.innerHTML = `
        <div class="flex items-center">
            <div class="flex-shrink-0">
                <i class="fas fa-circle ${health.status === 'healthy' ? 'text-green-500' : 'text-red-500'}"></i>
            </div>
            <div class="ml-3">
                <h3 class="text-lg font-medium text-gray-900">Overall Status</h3>
                <p class="text-sm text-gray-500">${health.status}</p>
            </div>
        </div>
    `;
    container.appendChild(overallStatus);
    
    // Component status
    Object.entries(health.components).forEach(([name, status]) => {
        const template = document.getElementById('health-component-template');
        const clone = template.content.cloneNode(true);
        
        const icon = clone.querySelector('.fa-circle');
        icon.className = `fas fa-circle ${status.healthy ? 'text-green-500' : 'text-red-500'}`;
        
        const title = clone.querySelector('h3');
        title.textContent = name;
        
        const description = clone.querySelector('p');
        description.textContent = status.message || (status.healthy ? 'Healthy' : 'Unhealthy');
        
        container.appendChild(clone);
    });
}

// Update metrics section
function updateMetrics(metrics) {
    const container = document.getElementById('metrics-charts');
    container.innerHTML = '';
    
    // API Requests Chart
    createMetricChart('api-requests', 'API Requests', metrics.api_requests, {
        type: 'line',
        labels: metrics.api_requests.labels,
        datasets: [{
            label: 'Requests',
            data: metrics.api_requests.values,
            borderColor: 'rgb(59, 130, 246)',
            tension: 0.1
        }]
    });
    
    // Response Times Chart
    createMetricChart('response-times', 'Response Times', metrics.response_times, {
        type: 'line',
        labels: metrics.response_times.labels,
        datasets: [{
            label: 'Time (ms)',
            data: metrics.response_times.values,
            borderColor: 'rgb(16, 185, 129)',
            tension: 0.1
        }]
    });
    
    // Error Rates Chart
    createMetricChart('error-rates', 'Error Rates', metrics.error_rates, {
        type: 'bar',
        labels: metrics.error_rates.labels,
        datasets: [{
            label: 'Errors',
            data: metrics.error_rates.values,
            backgroundColor: 'rgb(239, 68, 68)'
        }]
    });
}

// Create or update metric chart
function createMetricChart(id, title, data, config) {
    const template = document.getElementById('chart-template');
    const clone = template.content.cloneNode(true);
    
    const chartTitle = clone.querySelector('h3');
    chartTitle.textContent = title;
    
    const canvas = clone.querySelector('canvas');
    canvas.id = `chart-${id}`;
    
    document.getElementById('metrics-charts').appendChild(clone);
    
    if (charts.has(id)) {
        charts.get(id).destroy();
    }
    
    const chart = new Chart(canvas, {
        ...config,
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });
    
    charts.set(id, chart);
}

// Update alerts section
function updateAlerts(alerts) {
    const container = document.getElementById('alerts-list');
    container.innerHTML = '';
    
    if (alerts.active_alerts.length === 0) {
        container.innerHTML = '<p class="text-gray-500">No active alerts</p>';
        return;
    }
    
    alerts.active_alerts.forEach(alert => {
        const template = document.getElementById('alert-template');
        const clone = template.content.cloneNode(true);
        
        const icon = clone.querySelector('.fa-exclamation-circle');
        icon.className = `fas fa-exclamation-circle ${
            alert.level === 'critical' ? 'text-red-500' :
            alert.level === 'warning' ? 'text-yellow-500' :
            'text-blue-500'
        }`;
        
        const title = clone.querySelector('h3');
        title.textContent = `${alert.component} - ${alert.level.toUpperCase()}`;
        
        const message = clone.querySelector('div');
        message.textContent = alert.message;
        
        container.appendChild(clone);
    });
}

// Initialize dashboard
document.addEventListener('DOMContentLoaded', () => {
    initWebSocket();
    
    // Initial data fetch
    Promise.all([
        fetch('/api/health').then(r => r.json()),
        fetch('/api/metrics').then(r => r.json()),
        fetch('/api/alerts').then(r => r.json())
    ]).then(([health, metrics, alerts]) => {
        updateDashboard({ health, metrics, alerts });
    }).catch(error => {
        console.error('Failed to fetch initial data:', error);
    });
}); 