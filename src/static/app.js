// PetLog Dashboard JavaScript
class PetLogDashboard {
    constructor() {
        this.isStreaming = false;
        this.isRecording = false;
        this.currentPage = 1;
        this.pageSize = 20;
        this.totalEvents = 0;
        this.eventRefreshInterval = null;
        this.statusRefreshInterval = null;
        this.lastEventId = null; // For detecting new events

        this.initializeEventListeners();
        this.loadInitialData();
        this.startPeriodicUpdates();
    }

    initializeEventListeners() {
        // Stream controls
        document.getElementById('start-stream').addEventListener('click', () => this.startStream());
        document.getElementById('stop-stream').addEventListener('click', () => this.stopStream());
        document.getElementById('refresh-stream').addEventListener('click', () => this.refreshStream());
        document.getElementById('toggle-recording').addEventListener('click', () => this.toggleRecording());

        // Event controls
        document.getElementById('refresh-events').addEventListener('click', () => this.loadEvents());
        document.getElementById('event-type-filter').addEventListener('change', () => this.loadEvents());
        document.getElementById('start-date-filter').addEventListener('change', () => this.loadEvents());
        document.getElementById('end-date-filter').addEventListener('change', () => this.loadEvents());

        // Pagination controls
        document.getElementById('prev-page').addEventListener('click', () => this.previousPage());
        document.getElementById('next-page').addEventListener('click', () => this.nextPage());

        // Modal controls
        document.getElementById('close-modal').addEventListener('click', () => this.closeModal());

        // Close modal when clicking outside
        document.getElementById('event-modal').addEventListener('click', (e) => {
            if (e.target.id === 'event-modal') {
                this.closeModal();
            }
        });
    }

    async loadInitialData() {
        await this.loadApiInfo();
        await this.loadEvents();
        await this.loadSystemStatus();
        await this.loadStreamStatus();
    }

    startPeriodicUpdates() {
        // Check for new events every 5 seconds
        this.eventRefreshInterval = setInterval(() => {
            this.checkForNewEvents();
        }, 5000);

        // Refresh system status every 30 seconds
        this.statusRefreshInterval = setInterval(() => {
            this.loadSystemStatus();
            this.loadStreamStatus();
        }, 30000);
    }

    async loadApiInfo() {
        try {
            const response = await fetch('/api');
            const data = await response.json();
            document.getElementById('api-version').textContent = data.version || 'Unknown';
            document.getElementById('api-status').textContent = 'Connected';
        } catch (error) {
            console.error('Error loading API info:', error);
            document.getElementById('api-version').textContent = 'Error';
            document.getElementById('api-status').textContent = 'Disconnected';
        }
    }

    async startStream() {
        try {
            const response = await fetch('/live/start', { method: 'POST' });
            const data = await response.json();

            if (response.ok) {
                this.isStreaming = true;
                this.updateStreamUI();
                this.showNotification('Stream started successfully', 'success');
            } else {
                throw new Error(data.detail || 'Failed to start stream');
            }
        } catch (error) {
            console.error('Error starting stream:', error);
            this.showNotification('Failed to start stream: ' + error.message, 'error');
        }
    }

    async stopStream() {
        try {
            const response = await fetch('/live/stop', { method: 'POST' });
            const data = await response.json();

            if (response.ok) {
                this.isStreaming = false;
                this.isRecording = false;
                this.updateStreamUI();
                this.showNotification('Stream stopped successfully', 'success');
            } else {
                throw new Error(data.detail || 'Failed to stop stream');
            }
        } catch (error) {
            console.error('Error stopping stream:', error);
            this.showNotification('Failed to stop stream: ' + error.message, 'error');
        }
    }

    async toggleRecording() {
        // This is a placeholder - recording toggle functionality would need to be implemented
        this.showNotification('Recording toggle not yet implemented', 'info');
    }

    refreshStream() {
        if (this.isStreaming) {
            const streamImg = document.getElementById('live-stream');
            const timestamp = new Date().getTime();
            streamImg.src = `/live/stream?t=${timestamp}`;
            this.showNotification('Stream refreshed', 'success');
        } else {
            this.showNotification('Stream is not active', 'warning');
        }
    }

    updateStreamUI() {
        const startBtn = document.getElementById('start-stream');
        const stopBtn = document.getElementById('stop-stream');
        const refreshBtn = document.getElementById('refresh-stream');
        const recordBtn = document.getElementById('toggle-recording');
        const streamImg = document.getElementById('live-stream');
        const placeholder = document.getElementById('stream-placeholder');
        const statusIndicator = document.querySelector('.status-indicator');
        const statusText = document.querySelector('#stream-status span:last-child');

        if (this.isStreaming) {
            startBtn.disabled = true;
            stopBtn.disabled = false;
            refreshBtn.disabled = false;
            recordBtn.disabled = false;

            // Add cache-busting parameter to force stream refresh
            const timestamp = new Date().getTime();
            streamImg.src = `/live/stream?t=${timestamp}`;

            streamImg.style.display = 'block';
            placeholder.style.display = 'none';
            statusIndicator.className = 'status-indicator online';
            statusText.textContent = 'Stream: Online';
        } else {
            startBtn.disabled = false;
            stopBtn.disabled = true;
            refreshBtn.disabled = true;
            recordBtn.disabled = true;
            streamImg.style.display = 'none';
            placeholder.style.display = 'block';
            statusIndicator.className = 'status-indicator offline';
            statusText.textContent = 'Stream: Offline';
        }

        // Update recording button text
        recordBtn.textContent = this.isRecording ? 'Stop Recording' : 'Start Recording';
    }

    async loadEvents(page = 1) {
        try {
            this.currentPage = page;

            // Get filter values
            const eventType = document.getElementById('event-type-filter').value;
            const startDate = document.getElementById('start-date-filter').value;
            const endDate = document.getElementById('end-date-filter').value;

            // Build query parameters
            const params = new URLSearchParams({
                page: page.toString(),
                page_size: this.pageSize.toString()
            });

            if (eventType) params.append('event_type', eventType);
            if (startDate) params.append('start_date', startDate + 'T00:00:00');
            if (endDate) params.append('end_date', endDate + 'T23:59:59');

            const response = await fetch(`/events?${params}`);
            const data = await response.json();

            if (response.ok) {
                this.displayEvents(data.events || []);
                this.updatePagination(data.total_count, data.page, data.page_size);
                this.updateEventStatistics(data.events || []);

                // Update last event ID for new event detection
                if (data.events && data.events.length > 0) {
                    this.lastEventId = data.events[0].event_id;
                }
            } else {
                throw new Error(data.detail || 'Failed to load events');
            }

        } catch (error) {
            console.error('Error loading events:', error);
            this.displayEvents([]);
            this.showNotification('Failed to load events: ' + error.message, 'error');
        }
    }

    async checkForNewEvents() {
        try {
            // Get the most recent event to check for new ones
            const params = new URLSearchParams({
                page: '1',
                page_size: '1'
            });

            const response = await fetch(`/events?${params}`);
            const data = await response.json();

            if (response.ok && data.events && data.events.length > 0) {
                const latestEvent = data.events[0];

                // If we have a new event (different ID than last known)
                if (this.lastEventId && latestEvent.event_id !== this.lastEventId) {
                    // New event detected - refresh the events list
                    this.loadEvents(this.currentPage);

                    // Show notification for new event
                    const eventIcon = latestEvent.event_type === 'entering_area' ? '🔵' : '🔴';
                    const eventName = this.formatEventType(latestEvent.event_type);
                    const className = latestEvent.metadata?.class_name || 'object';

                    this.showNotification(
                        `${eventIcon} New Event: ${eventName} - ${className}`,
                        'info'
                    );
                }
            }
        } catch (error) {
            console.error('Error checking for new events:', error);
        }
    }

    displayEvents(events) {
        const eventsList = document.getElementById('events-list');

        if (!events || events.length === 0) {
            eventsList.innerHTML = '<p class="no-events">No events found</p>';
            return;
        }

        const eventsHTML = events.map(event => {
            const timestamp = new Date(event.timestamp).toLocaleString();
            const eventTypeClass = event.event_type.replace('_', '-');
            const eventIcon = event.event_type === 'entering_area' ? '🔵' : '🔴';

            let metadataInfo = '';
            if (event.metadata) {
                const meta = event.metadata;
                if (meta.class_name) {
                    metadataInfo += `<span class="object-class">${meta.class_name}</span>`;
                }
                if (meta.tracking_duration) {
                    metadataInfo += `<span class="tracking-duration">Duration: ${meta.tracking_duration.toFixed(1)}s</span>`;
                }
            }

            return `
                <div class="event-item ${eventTypeClass}" onclick="dashboard.showEventDetails(${event.event_id})">
                    <div class="event-header">
                        <span class="event-icon">${eventIcon}</span>
                        <span class="event-type">${this.formatEventType(event.event_type)}</span>
                        <span class="event-time">${timestamp}</span>
                    </div>
                    <div class="event-details">
                        ${event.confidence ? `<span class="confidence">Confidence: ${(event.confidence * 100).toFixed(1)}%</span>` : ''}
                        ${metadataInfo}
                    </div>
                </div>
            `;
        }).join('');

        eventsList.innerHTML = eventsHTML;
    }

    updateEventStatistics(events) {
        // Count events by type
        let enteringCount = 0;
        let leavingCount = 0;
        let recentCount = 0;

        const now = new Date();
        const oneDayAgo = new Date(now.getTime() - 24 * 60 * 60 * 1000);

        events.forEach(event => {
            if (event.event_type === 'entering_area') enteringCount++;
            if (event.event_type === 'leaving_area') leavingCount++;

            const eventTime = new Date(event.timestamp);
            if (eventTime > oneDayAgo) recentCount++;
        });

        document.getElementById('entering-events').textContent = enteringCount;
        document.getElementById('leaving-events').textContent = leavingCount;
        document.getElementById('total-events').textContent = events.length;
        document.getElementById('recent-events').textContent = recentCount;

        // Update last event time
        if (events.length > 0) {
            const lastEventTime = new Date(events[0].timestamp).toLocaleString();
            document.getElementById('last-event-time').textContent = lastEventTime;
        }
    }

    updatePagination(totalCount, currentPage, pageSize) {
        this.totalEvents = totalCount;
        const totalPages = Math.ceil(totalCount / pageSize);

        document.getElementById('page-info').textContent = `Page ${currentPage} of ${totalPages}`;
        document.getElementById('prev-page').disabled = currentPage <= 1;
        document.getElementById('next-page').disabled = currentPage >= totalPages;
    }

    previousPage() {
        if (this.currentPage > 1) {
            this.loadEvents(this.currentPage - 1);
        }
    }

    nextPage() {
        const totalPages = Math.ceil(this.totalEvents / this.pageSize);
        if (this.currentPage < totalPages) {
            this.loadEvents(this.currentPage + 1);
        }
    }

    async showEventDetails(eventId) {
        try {
            const response = await fetch(`/events/${eventId}`);
            const event = await response.json();

            if (response.ok) {
                const timestamp = new Date(event.timestamp).toLocaleString();
                const eventIcon = event.event_type === 'entering_area' ? '🔵' : '🔴';

                let detailsHTML = `
                    <div class="event-detail-item">
                        <strong>Event ID:</strong> ${event.event_id}
                    </div>
                    <div class="event-detail-item">
                        <strong>Type:</strong> ${eventIcon} ${this.formatEventType(event.event_type)}
                    </div>
                    <div class="event-detail-item">
                        <strong>Timestamp:</strong> ${timestamp}
                    </div>
                `;

                if (event.confidence) {
                    detailsHTML += `
                        <div class="event-detail-item">
                            <strong>Confidence:</strong> ${(event.confidence * 100).toFixed(1)}%
                        </div>
                    `;
                }

                if (event.metadata) {
                    detailsHTML += `
                        <div class="event-detail-item">
                            <strong>Object Class:</strong> ${event.metadata.class_name || 'Unknown'}
                        </div>
                    `;

                    if (event.metadata.tracking_duration) {
                        detailsHTML += `
                            <div class="event-detail-item">
                                <strong>Tracking Duration:</strong> ${event.metadata.tracking_duration.toFixed(1)}s
                            </div>
                        `;
                    }
                }

                if (event.media_path) {
                    detailsHTML += `
                        <div class="event-detail-item">
                            <strong>Media:</strong> <a href="${event.media_path}" target="_blank">View Recording</a>
                        </div>
                    `;
                }

                document.getElementById('event-details').innerHTML = detailsHTML;
                document.getElementById('event-modal').style.display = 'block';
            } else {
                throw new Error('Failed to load event details');
            }
        } catch (error) {
            console.error('Error loading event details:', error);
            this.showNotification('Failed to load event details: ' + error.message, 'error');
        }
    }

    closeModal() {
        document.getElementById('event-modal').style.display = 'none';
    }

    formatEventType(eventType) {
        return eventType.split('_').map(word =>
            word.charAt(0).toUpperCase() + word.slice(1)
        ).join(' ');
    }

    async loadSystemStatus() {
        try {
            const [healthResponse, cameraResponse, detectionResponse] = await Promise.all([
                fetch('/health'),
                fetch('/camera/status'),
                fetch('/detection/status')
            ]);

            const healthData = await healthResponse.json();
            const cameraData = await cameraResponse.json();
            const detectionData = await detectionResponse.json();

            // Update system status
            document.getElementById('camera-status').textContent = cameraData.status || 'Unknown';
            document.getElementById('database-status').textContent = healthData.database_status || 'Unknown';

            // Update detection status
            const detectionStatusElement = document.getElementById('detection-status');
            if (detectionStatusElement) {
                detectionStatusElement.textContent = detectionData.running ? 'Running' : 'Stopped';
            }

        } catch (error) {
            console.error('Error loading system status:', error);
            document.getElementById('camera-status').textContent = 'Error';
            document.getElementById('database-status').textContent = 'Error';

            const detectionStatusElement = document.getElementById('detection-status');
            if (detectionStatusElement) {
                detectionStatusElement.textContent = 'Error';
            }
        }
    }

    async loadStreamStatus() {
        try {
            const response = await fetch('/live/status');
            const data = await response.json();

            this.isStreaming = data.streaming || false;
            this.isRecording = data.recording || false;
            this.updateStreamUI();

        } catch (error) {
            console.error('Error loading stream status:', error);
        }
    }

    showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.textContent = message;

        // Style the notification
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 12px 20px;
            border-radius: 8px;
            color: white;
            font-weight: 500;
            z-index: 10000;
            max-width: 300px;
            word-wrap: break-word;
            animation: slideIn 0.3s ease;
        `;

        const colors = {
            success: '#10b981',
            error: '#ef4444',
            warning: '#f59e0b',
            info: '#2563eb'
        };

        notification.style.backgroundColor = colors[type] || colors.info;

        // Add to page
        document.body.appendChild(notification);

        // Auto-remove after 5 seconds
        setTimeout(() => {
            notification.style.animation = 'slideOut 0.3s ease';
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
            }, 300);
        }, type === 'error' ? 5000 : 3000);

        console.log(`[${type.toUpperCase()}] ${message}`);
    }

    // Cleanup method
    destroy() {
        if (this.eventRefreshInterval) {
            clearInterval(this.eventRefreshInterval);
        }
        if (this.statusRefreshInterval) {
            clearInterval(this.statusRefreshInterval);
        }
    }
}

// Add notification animations and styles
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }

    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(100%);
            opacity: 0;
        }
    }

    .event-item {
        border: 1px solid #e5e7eb;
        border-radius: 8px;
        padding: 12px;
        margin-bottom: 8px;
        background: white;
        cursor: pointer;
        transition: background-color 0.2s;
    }

    .event-item:hover {
        background-color: #f9fafb;
    }

    .event-item.entering-area {
        border-left: 4px solid #3b82f6;
    }

    .event-item.leaving-area {
        border-left: 4px solid #ef4444;
    }

    .event-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 8px;
    }

    .event-icon {
        font-size: 16px;
        margin-right: 8px;
    }

    .event-type {
        font-weight: 600;
        color: #374151;
    }

    .event-time {
        font-size: 12px;
        color: #6b7280;
    }

    .event-details {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        font-size: 12px;
    }

    .event-details span {
        background: #f3f4f6;
        padding: 2px 6px;
        border-radius: 4px;
        color: #374151;
    }

    .no-events {
        text-align: center;
        color: #6b7280;
        font-style: italic;
        padding: 20px;
    }

    .modal {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background-color: rgba(0, 0, 0, 0.5);
        z-index: 1000;
    }

    .modal-content {
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        background: white;
        border-radius: 8px;
        padding: 20px;
        max-width: 500px;
        width: 90%;
        max-height: 80%;
        overflow-y: auto;
    }

    .modal-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 20px;
        border-bottom: 1px solid #e5e7eb;
        padding-bottom: 10px;
    }

    .close-btn {
        background: none;
        border: none;
        font-size: 24px;
        cursor: pointer;
        color: #6b7280;
    }

    .close-btn:hover {
        color: #374151;
    }

    .event-detail-item {
        margin-bottom: 10px;
        padding: 8px;
        background: #f9fafb;
        border-radius: 4px;
    }

    .event-detail-item strong {
        color: #374151;
    }
`;
document.head.appendChild(style);

// Initialize dashboard when page loads
document.addEventListener('DOMContentLoaded', () => {
    window.dashboard = new PetLogDashboard();
});

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    if (window.dashboard) {
        window.dashboard.destroy();
    }
});

console.log('PetLog Dashboard JavaScript loaded - Clean workflow implementation');
