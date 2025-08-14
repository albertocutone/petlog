// PetLog Dashboard JavaScript

class PetLogDashboard {
    constructor() {
        this.apiBaseUrl = window.location.origin;
        this.currentPage = 1;
        this.pageSize = 10;
        this.isConnected = false;
        this.refreshInterval = null;

        this.init();
    }

    async init() {
        this.setupEventListeners();
        await this.checkConnection();
        await this.loadInitialData();
        this.startAutoRefresh();
    }

    setupEventListeners() {
        // Connection and refresh controls
        document.getElementById('refresh-video')?.addEventListener('click', () => this.refreshVideo());
        document.getElementById('fullscreen-video')?.addEventListener('click', () => this.toggleFullscreen());
        document.getElementById('refresh-events')?.addEventListener('click', () => this.loadEvents());
        document.getElementById('refresh-status')?.addEventListener('click', () => this.loadSystemStatus());

        // Event filters
        document.getElementById('pet-filter')?.addEventListener('change', () => this.loadEvents());
        document.getElementById('event-type-filter')?.addEventListener('change', () => this.loadEvents());

        // Pagination
        document.getElementById('prev-page')?.addEventListener('click', () => this.previousPage());
        document.getElementById('next-page')?.addEventListener('click', () => this.nextPage());

        // Alert configuration
        document.getElementById('save-alerts')?.addEventListener('click', () => this.saveAlertConfig());

        // Modal controls
        document.getElementById('close-modal')?.addEventListener('click', () => this.closeModal());
        document.getElementById('event-modal')?.addEventListener('click', (e) => {
            if (e.target.id === 'event-modal') this.closeModal();
        });

        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') this.closeModal();
        });
    }

    async checkConnection() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/health`);
            if (response.ok) {
                this.setConnectionStatus(true, 'Connected');
                this.isConnected = true;
            } else {
                throw new Error('API not responding');
            }
        } catch (error) {
            this.setConnectionStatus(false, 'Disconnected');
            this.isConnected = false;
            console.error('Connection check failed:', error);
        }
    }

    setConnectionStatus(connected, message) {
        const statusDot = document.getElementById('connection-status');
        const statusText = document.getElementById('connection-text');

        if (statusDot && statusText) {
            statusDot.className = `status-dot ${connected ? 'online' : 'offline'}`;
            statusText.textContent = message;
        }
    }

    async loadInitialData() {
        await Promise.all([
            this.loadPets(),
            this.loadEvents(),
            this.loadSystemStatus(),
            this.loadAlertConfig(),
            this.setupVideoStream()
        ]);
    }

    async loadPets() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/pets`);
            if (response.ok) {
                const pets = await response.json();
                this.populatePetFilter(pets);
            }
        } catch (error) {
            console.error('Failed to load pets:', error);
        }
    }

    populatePetFilter(pets) {
        const petFilter = document.getElementById('pet-filter');
        if (petFilter) {
            // Clear existing options except "All Pets"
            petFilter.innerHTML = '<option value="">All Pets</option>';

            pets.forEach(pet => {
                const option = document.createElement('option');
                option.value = pet.pet_id;
                option.textContent = pet.name;
                petFilter.appendChild(option);
            });
        }
    }

    async loadEvents() {
        const eventsList = document.getElementById('events-list');
        if (!eventsList) return;

        // Show loading state
        eventsList.innerHTML = `
            <div class="loading-placeholder">
                <div class="spinner"></div>
                <p>Loading events...</p>
            </div>
        `;

        try {
            const petId = document.getElementById('pet-filter')?.value || '';
            const eventType = document.getElementById('event-type-filter')?.value || '';

            const params = new URLSearchParams({
                page: this.currentPage.toString(),
                page_size: this.pageSize.toString()
            });

            if (petId) params.append('pet_id', petId);
            if (eventType) params.append('event_type', eventType);

            const response = await fetch(`${this.apiBaseUrl}/events?${params}`);
            if (response.ok) {
                const data = await response.json();
                this.displayEvents(data.events);
                this.updatePagination(data.page, data.total_count, data.page_size);
            } else {
                throw new Error('Failed to load events');
            }
        } catch (error) {
            console.error('Failed to load events:', error);
            eventsList.innerHTML = `
                <div class="loading-placeholder">
                    <p>Failed to load events. Please try again.</p>
                </div>
            `;
        }
    }

    displayEvents(events) {
        const eventsList = document.getElementById('events-list');
        if (!eventsList) return;

        if (events.length === 0) {
            eventsList.innerHTML = `
                <div class="loading-placeholder">
                    <p>No events found.</p>
                </div>
            `;
            return;
        }

        eventsList.innerHTML = events.map(event => `
            <div class="event-item" onclick="petlogDashboard.showEventDetails(${event.event_id})">
                <div class="event-icon">${this.getEventIcon(event.event_type)}</div>
                <div class="event-content">
                    <div class="event-title">${this.formatEventType(event.event_type)}</div>
                    <div class="event-meta">
                        Pet ID: ${event.pet_id}
                        ${event.duration ? ` • Duration: ${event.duration}s` : ''}
                        ${event.confidence ? ` • Confidence: ${Math.round(event.confidence * 100)}%` : ''}
                    </div>
                </div>
                <div class="event-time">${this.formatDateTime(event.timestamp)}</div>
            </div>
        `).join('');
    }

    getEventIcon(eventType) {
        const icons = {
            playing: '🎾',
            eating: '🍽️',
            drinking: '💧',
            sleeping: '😴',
            grooming: '🧼',
            sitting: '🪑',
            jumping: '🦘',
            passing_by: '🚶',
            vocalizing: '🔊',
            interacting: '🤝',
            entering_area: '🚪',
            leaving_area: '🚪',
            abnormal_behavior: '⚠️',
            no_movement: '⏸️'
        };
        return icons[eventType] || '📝';
    }

    formatEventType(eventType) {
        return eventType.split('_').map(word =>
            word.charAt(0).toUpperCase() + word.slice(1)
        ).join(' ');
    }

    formatDateTime(timestamp) {
        const date = new Date(timestamp);
        const now = new Date();
        const diffMs = now - date;
        const diffMins = Math.floor(diffMs / 60000);
        const diffHours = Math.floor(diffMins / 60);
        const diffDays = Math.floor(diffHours / 24);

        if (diffMins < 1) return 'Just now';
        if (diffMins < 60) return `${diffMins}m ago`;
        if (diffHours < 24) return `${diffHours}h ago`;
        if (diffDays < 7) return `${diffDays}d ago`;

        return date.toLocaleDateString();
    }

    updatePagination(currentPage, totalCount, pageSize) {
        const totalPages = Math.ceil(totalCount / pageSize);

        const prevBtn = document.getElementById('prev-page');
        const nextBtn = document.getElementById('next-page');
        const pageInfo = document.getElementById('page-info');

        if (prevBtn) prevBtn.disabled = currentPage <= 1;
        if (nextBtn) nextBtn.disabled = currentPage >= totalPages;
        if (pageInfo) pageInfo.textContent = `Page ${currentPage} of ${totalPages}`;
    }

    previousPage() {
        if (this.currentPage > 1) {
            this.currentPage--;
            this.loadEvents();
        }
    }

    nextPage() {
        this.currentPage++;
        this.loadEvents();
    }

    async showEventDetails(eventId) {
        try {
            const response = await fetch(`${this.apiBaseUrl}/events/${eventId}`);
            if (response.ok) {
                const event = await response.json();
                this.displayEventModal(event);
            } else {
                throw new Error('Event not found');
            }
        } catch (error) {
            console.error('Failed to load event details:', error);
            this.displayEventModal({
                event_id: eventId,
                error: 'Failed to load event details'
            });
        }
    }

    displayEventModal(event) {
        const modal = document.getElementById('event-modal');
        const eventDetails = document.getElementById('event-details');

        if (!modal || !eventDetails) return;

        if (event.error) {
            eventDetails.innerHTML = `<p class="text-error">${event.error}</p>`;
        } else {
            eventDetails.innerHTML = `
                <div class="event-detail-content">
                    <div class="detail-row">
                        <strong>Event ID:</strong> ${event.event_id}
                    </div>
                    <div class="detail-row">
                        <strong>Type:</strong> ${this.getEventIcon(event.event_type)} ${this.formatEventType(event.event_type)}
                    </div>
                    <div class="detail-row">
                        <strong>Pet ID:</strong> ${event.pet_id}
                    </div>
                    <div class="detail-row">
                        <strong>Timestamp:</strong> ${new Date(event.timestamp).toLocaleString()}
                    </div>
                    ${event.duration ? `
                        <div class="detail-row">
                            <strong>Duration:</strong> ${event.duration} seconds
                        </div>
                    ` : ''}
                    ${event.confidence ? `
                        <div class="detail-row">
                            <strong>Confidence:</strong> ${Math.round(event.confidence * 100)}%
                        </div>
                    ` : ''}
                    ${event.media_path ? `
                        <div class="detail-row">
                            <strong>Recording:</strong>
                            <a href="${event.media_path}" target="_blank">View Recording</a>
                        </div>
                    ` : ''}
                    ${event.metadata ? `
                        <div class="detail-row">
                            <strong>Metadata:</strong>
                            <pre>${JSON.stringify(event.metadata, null, 2)}</pre>
                        </div>
                    ` : ''}
                </div>
            `;
        }

        modal.style.display = 'flex';
    }

    closeModal() {
        const modal = document.getElementById('event-modal');
        if (modal) {
            modal.style.display = 'none';
        }
    }

    async loadSystemStatus() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/health`);
            if (response.ok) {
                const status = await response.json();
                this.displaySystemStatus(status);
            } else {
                throw new Error('Failed to load system status');
            }
        } catch (error) {
            console.error('Failed to load system status:', error);
            this.displaySystemStatus({
                status: 'error',
                camera_status: 'unknown',
                database_status: 'unknown',
                storage_usage: 0
            });
        }
    }

    displaySystemStatus(status) {
        const apiStatus = document.getElementById('api-status');
        const cameraStatus = document.getElementById('camera-status-detail');
        const databaseStatus = document.getElementById('database-status');
        const storageUsage = document.getElementById('storage-usage');
        const lastUpdated = document.getElementById('last-updated-time');

        if (apiStatus) {
            apiStatus.textContent = status.status || 'Unknown';
            apiStatus.className = `status-value ${this.getStatusClass(status.status)}`;
        }

        if (cameraStatus) {
            cameraStatus.textContent = status.camera_status || 'Unknown';
            cameraStatus.className = `status-value ${this.getStatusClass(status.camera_status)}`;
        }

        if (databaseStatus) {
            databaseStatus.textContent = status.database_status || 'Unknown';
            databaseStatus.className = `status-value ${this.getStatusClass(status.database_status)}`;
        }

        if (storageUsage) {
            const usage = Math.round((status.storage_usage || 0) * 100);
            storageUsage.textContent = `${usage}%`;
            storageUsage.className = `status-value ${usage > 80 ? 'error' : usage > 60 ? 'warning' : 'healthy'}`;
        }

        if (lastUpdated) {
            lastUpdated.textContent = new Date().toLocaleTimeString();
        }

        // Update camera status in video section
        const cameraStatusSpan = document.getElementById('camera-status');
        if (cameraStatusSpan) {
            cameraStatusSpan.textContent = status.camera_status || 'Unknown';
        }
    }

    getStatusClass(status) {
        const statusMap = {
            'healthy': 'healthy',
            'connected': 'healthy',
            'operational': 'healthy',
            'running': 'healthy',
            'warning': 'warning',
            'error': 'error',
            'disconnected': 'error',
            'offline': 'error'
        };
        return statusMap[status] || 'warning';
    }

    async loadAlertConfig() {
        try {
            const userId = document.getElementById('user-id')?.value || 1;
            const response = await fetch(`${this.apiBaseUrl}/alerts/config/${userId}`);
            if (response.ok) {
                const config = await response.json();
                this.displayAlertConfig(config);
            }
        } catch (error) {
            console.error('Failed to load alert config:', error);
        }
    }

    displayAlertConfig(config) {
        const enabledCheckbox = document.getElementById('alert-enabled');
        const thresholdInput = document.getElementById('alert-threshold');
        const userIdInput = document.getElementById('user-id');
        const statusInfo = document.getElementById('alert-status-info');

        if (enabledCheckbox) enabledCheckbox.checked = config.enabled;
        if (thresholdInput) thresholdInput.value = config.no_event_threshold;
        if (userIdInput) userIdInput.value = config.user_id;

        if (statusInfo) {
            statusInfo.innerHTML = `
                <p><strong>Status:</strong> ${config.enabled ? 'Enabled' : 'Disabled'}</p>
                <p><strong>Threshold:</strong> ${config.no_event_threshold} minutes</p>
                <p><strong>User ID:</strong> ${config.user_id}</p>
            `;
        }
    }

    async saveAlertConfig() {
        const enabled = document.getElementById('alert-enabled')?.checked || false;
        const threshold = parseInt(document.getElementById('alert-threshold')?.value) || 60;
        const userId = parseInt(document.getElementById('user-id')?.value) || 1;

        const config = {
            user_id: userId,
            no_event_threshold: threshold,
            enabled: enabled
        };

        try {
            const response = await fetch(`${this.apiBaseUrl}/alerts/config`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(config)
            });

            if (response.ok) {
                this.showNotification('Alert configuration saved successfully', 'success');
                await this.loadAlertConfig();
            } else {
                throw new Error('Failed to save configuration');
            }
        } catch (error) {
            console.error('Failed to save alert config:', error);
            this.showNotification('Failed to save alert configuration', 'error');
        }
    }

    async setupVideoStream() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/live`);
            if (response.ok) {
                const data = await response.json();
                // For now, just show the placeholder since video streaming isn't implemented yet
                console.log('Video stream info:', data);
            }
        } catch (error) {
            console.error('Failed to setup video stream:', error);
        }
    }

    refreshVideo() {
        // Placeholder for video refresh functionality
        this.showNotification('Video refresh requested', 'info');
    }

    toggleFullscreen() {
        const videoContainer = document.querySelector('.video-container');
        if (!videoContainer) return;

        if (!document.fullscreenElement) {
            videoContainer.requestFullscreen().catch(err => {
                console.error('Failed to enter fullscreen:', err);
            });
        } else {
            document.exitFullscreen();
        }
    }

    showNotification(message, type = 'info') {
        // Create a simple notification system
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.textContent = message;
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 12px 20px;
            border-radius: 8px;
            color: white;
            font-weight: 500;
            z-index: 10000;
            animation: slideIn 0.3s ease;
        `;

        const colors = {
            success: '#10b981',
            error: '#ef4444',
            warning: '#f59e0b',
            info: '#2563eb'
        };

        notification.style.backgroundColor = colors[type] || colors.info;

        document.body.appendChild(notification);

        setTimeout(() => {
            notification.style.animation = 'slideOut 0.3s ease';
            setTimeout(() => {
                document.body.removeChild(notification);
            }, 300);
        }, 3000);
    }

    startAutoRefresh() {
        // Refresh data every 30 seconds
        this.refreshInterval = setInterval(async () => {
            if (this.isConnected) {
                await this.loadEvents();
                await this.loadSystemStatus();
            } else {
                await this.checkConnection();
            }
        }, 30000);
    }

    stopAutoRefresh() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
            this.refreshInterval = null;
        }
    }
}

// Add notification animations
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

    .detail-row {
        margin-bottom: 12px;
        padding: 8px 0;
        border-bottom: 1px solid var(--border-color);
    }

    .detail-row:last-child {
        border-bottom: none;
    }

    .detail-row pre {
        background-color: var(--background-color);
        padding: 8px;
        border-radius: 4px;
        font-size: 0.8rem;
        margin-top: 4px;
        overflow-x: auto;
    }
`;
document.head.appendChild(style);

// Initialize the dashboard when the page loads
let petlogDashboard;
document.addEventListener('DOMContentLoaded', () => {
    petlogDashboard = new PetLogDashboard();
});

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    if (petlogDashboard) {
        petlogDashboard.stopAutoRefresh();
    }
});
