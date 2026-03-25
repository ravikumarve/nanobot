// nanobot Dashboard JavaScript

class Dashboard {
    constructor() {
        this.ws = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000;
        
        this.initializeWebSocket();
        this.updateStats();
    }
    
    initializeWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws`;
        
        this.ws = new WebSocket(wsUrl);
        
        this.ws.onopen = () => {
            console.log('WebSocket connected');
            this.reconnectAttempts = 0;
            this.updateStatus('connected', 'Connected');
            
            // Subscribe to default channels
            this.sendMessage({
                type: 'subscribe',
                channels: ['messages', 'sessions', 'agents']
            });
        };
        
        this.ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                this.handleMessage(data);
            } catch (error) {
                console.error('Error parsing WebSocket message:', error);
            }
        };
        
        this.ws.onclose = () => {
            console.log('WebSocket disconnected');
            this.updateStatus('disconnected', 'Disconnected');
            this.attemptReconnect();
        };
        
        this.ws.onerror = (error) => {
            console.error('WebSocket error:', error);
            this.updateStatus('error', 'Connection Error');
        };
    }
    
    handleMessage(data) {
        switch (data.type) {
            case 'initial_state':
                this.updateStats(data);
                break;
                
            case 'message_processed':
                this.addActivityMessage(data);
                this.updateStats({
                    messages_processed: data.messages_processed
                });
                break;
                
            case 'session_created':
                this.updateStats({
                    sessions: data.sessions
                });
                break;
                
            case 'agent_status':
                this.updateStats({
                    agents: data.agents
                });
                break;
                
            default:
                console.log('Received message:', data);
        }
    }
    
    sendMessage(message) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(message));
        }
    }
    
    updateStats(stats = {}) {
        if (stats.agents !== undefined) {
            document.getElementById('agent-count').textContent = stats.agents;
        }
        
        if (stats.sessions !== undefined) {
            document.getElementById('session-count').textContent = stats.sessions;
        }
        
        if (stats.messages_processed !== undefined) {
            document.getElementById('message-count').textContent = stats.messages_processed.toLocaleString();
        }
        
        if (stats.response_time !== undefined) {
            document.getElementById('response-time').textContent = `${stats.response_time}ms`;
        }
    }
    
    addActivityMessage(data) {
        const activityLog = document.getElementById('activity-log');
        const messageDiv = document.createElement('div');
        messageDiv.className = `activity-message ${data.level || 'info'}`;
        
        const timestamp = new Date().toLocaleTimeString();
        const content = data.content || 'Activity occurred';
        
        messageDiv.innerHTML = `
            <div class="timestamp">${timestamp}</div>
            <div class="message-content">${this.escapeHtml(content)}</div>
        `;
        
        activityLog.prepend(messageDiv);
        
        // Keep only last 50 messages
        const messages = activityLog.querySelectorAll('.activity-message');
        if (messages.length > 50) {
            messages[messages.length - 1].remove();
        }
        
        // Auto-scroll to top
        activityLog.scrollTop = 0;
    }
    
    updateStatus(status, text) {
        const indicator = document.getElementById('status-indicator');
        const statusText = document.getElementById('status-text');
        
        indicator.className = 'status-indicator';
        indicator.classList.add(status);
        statusText.textContent = text;
    }
    
    attemptReconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            this.reconnectDelay *= 2; // Exponential backoff
            
            setTimeout(() => {
                console.log(`Attempting reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`);
                this.initializeWebSocket();
            }, this.reconnectDelay);
        }
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Initialize dashboard when page loads
document.addEventListener('DOMContentLoaded', () => {
    new Dashboard();
});