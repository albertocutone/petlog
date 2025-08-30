// PetLog Dashboard JavaScript

// Initialize the dashboard when the page loads
document.addEventListener('DOMContentLoaded', function() {
    console.log('PetLog Dashboard loaded');
    initializeApp();
});

function initializeApp() {
    console.log('Initializing PetLog Dashboard...');

    // Initialize all components
    initializeVideoStream();
    checkStreamStatus();

    console.log('Dashboard initialized successfully');
}

// Video streaming functions
function initializeVideoStream() {
    const videoElement = document.getElementById('live-video');
    const placeholder = document.getElementById('video-placeholder');
    const refreshBtn = document.getElementById('refresh-video');
    const fullscreenBtn = document.getElementById('fullscreen-video');

    // Add start/stop stream buttons
    const videoControls = document.querySelector('.video-controls');

    if (!videoControls) {
        console.error('Video controls container not found');
        return;
    }

    // Check if buttons already exist to avoid duplicates
    if (document.getElementById('start-stream')) {
        console.log('Stream control buttons already exist');
        return;
    }

    const startBtn = document.createElement('button');
    startBtn.id = 'start-stream';
    startBtn.className = 'btn btn-primary';
    startBtn.innerHTML = '▶️ Start Stream';
    startBtn.type = 'button';
    startBtn.addEventListener('click', function(e) {
        e.preventDefault();
        startVideoStream();
    });

    const stopBtn = document.createElement('button');
    stopBtn.id = 'stop-stream';
    stopBtn.className = 'btn btn-secondary';
    stopBtn.innerHTML = '⏹️ Stop Stream';
    stopBtn.type = 'button';
    stopBtn.addEventListener('click', function(e) {
        e.preventDefault();
        stopVideoStream();
    });
    stopBtn.style.display = 'none';

    const recordBtn = document.createElement('button');
    recordBtn.id = 'record-stream';
    recordBtn.className = 'btn btn-accent';
    recordBtn.innerHTML = '🔴 Record';
    recordBtn.type = 'button';
    recordBtn.addEventListener('click', function(e) {
        e.preventDefault();
        toggleRecording();
    });
    recordBtn.style.display = 'none';

    // Insert buttons in the correct order
    videoControls.insertBefore(startBtn, refreshBtn);
    videoControls.insertBefore(stopBtn, refreshBtn);
    videoControls.insertBefore(recordBtn, refreshBtn);

    // Update existing button handlers
    refreshBtn.onclick = refreshVideoStream;
    fullscreenBtn.onclick = toggleFullscreen;

    console.log('Video stream controls initialized');
    console.log('Start button:', startBtn);
    console.log('Stop button:', stopBtn);
    console.log('Record button:', recordBtn);
}

async function startVideoStream() {
    try {
        console.log('Starting video stream...');
        showVideoLoading(true);

        const response = await fetch('/live/start', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
        });

        if (!response.ok) {
            throw new Error(`Failed to start stream: ${response.status} ${response.statusText}`);
        }

        const result = await response.json();
        console.log('Stream started:', result);

        // Start displaying the stream
        displayVideoStream();
        updateStreamControls(true);
        showSuccess('Video stream started successfully');

    } catch (error) {
        console.error('Error starting stream:', error);
        showError('Failed to start video stream: ' + error.message);
    } finally {
        showVideoLoading(false);
    }
}

async function stopVideoStream() {
    try {
        console.log('Stopping video stream...');

        const response = await fetch('/live/stop', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });

        if (!response.ok) {
            throw new Error(`Failed to stop stream: ${response.statusText}`);
        }

        const result = await response.json();
        console.log('Stream stopped:', result);

        hideVideoStream();
        updateStreamControls(false);
        showSuccess('Video stream stopped');

    } catch (error) {
        console.error('Error stopping stream:', error);
        showError('Failed to stop video stream: ' + error.message);
    }
}

function displayVideoStream() {
    const videoElement = document.getElementById('live-video');
    const placeholder = document.getElementById('video-placeholder');

    // For MJPEG, we use an img element instead of video
    let imgElement = document.getElementById('live-stream-img');
    if (!imgElement) {
        imgElement = document.createElement('img');
        imgElement.id = 'live-stream-img';
        imgElement.className = 'video-stream';
        imgElement.style.width = '100%';
        imgElement.style.height = 'auto';
        imgElement.style.borderRadius = '8px';
        imgElement.style.background = '#000';
        videoElement.parentNode.insertBefore(imgElement, videoElement);
    }

    // Set the stream source with cache busting
    imgElement.src = '/live/stream?t=' + Date.now();

    // Show stream, hide placeholder and video element
    placeholder.style.display = 'none';
    videoElement.style.display = 'none';
    imgElement.style.display = 'block';

    // Handle stream errors
    imgElement.onerror = function() {
        console.error('Video stream error');
        hideVideoStream();
        showError('Video stream connection lost');
    };

    console.log('Video stream display started');
}

function hideVideoStream() {
    const placeholder = document.getElementById('video-placeholder');
    const imgElement = document.getElementById('live-stream-img');

    if (imgElement) {
        imgElement.src = '';
        imgElement.style.display = 'none';
    }
    placeholder.style.display = 'flex';

    console.log('Video stream display stopped');
}

function updateStreamControls(streaming) {
    const startBtn = document.getElementById('start-stream');
    const stopBtn = document.getElementById('stop-stream');
    const recordBtn = document.getElementById('record-stream');

    if (streaming) {
        startBtn.style.display = 'none';
        stopBtn.style.display = 'inline-block';
        recordBtn.style.display = 'inline-block';
    } else {
        startBtn.style.display = 'inline-block';
        stopBtn.style.display = 'none';
        recordBtn.style.display = 'none';

        // Reset record button if it was recording
        recordBtn.innerHTML = '🔴 Record';
        recordBtn.classList.remove('recording');
    }

    console.log('Stream controls updated, streaming:', streaming);
}

async function toggleRecording() {
    const recordBtn = document.getElementById('record-stream');
    const isRecording = recordBtn.classList.contains('recording');

    try {
        if (isRecording) {
            // Stop streaming (which will also stop recording)
            const response = await fetch('/live/stop', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });

            if (!response.ok) {
                throw new Error('Failed to stop recording');
            }

            const result = await response.json();
            console.log('Stream and recording stopped:', result);

            // Update UI
            hideVideoStream();
            updateStreamControls(false);

            if (result.recording_stopped) {
                showSuccess(`Recording saved: ${result.recording_path}`);
            }

        } else {
            // Prompt for recording duration
            const duration = prompt('Enter recording duration in seconds (or leave empty for manual stop):');
            let recordDuration = null;

            if (duration && duration.trim() !== '') {
                recordDuration = parseInt(duration);
                if (isNaN(recordDuration) || recordDuration <= 0) {
                    showError('Invalid duration. Please enter a positive number.');
                    return;
                }
            }

            // Start streaming with recording
            const params = new URLSearchParams();
            if (recordDuration) {
                params.append('record_duration', recordDuration.toString());
            }

            const response = await fetch(`/live/start?${params}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });

            if (!response.ok) {
                throw new Error('Failed to start recording');
            }

            const result = await response.json();
            console.log('Stream started with recording:', result);

            // Update UI
            displayVideoStream();
            updateStreamControls(true);

            if (result.recording) {
                recordBtn.innerHTML = '⏺️ Stop Recording';
                recordBtn.classList.add('recording');

                const durationText = recordDuration ? ` for ${recordDuration}s` : '';
                showSuccess(`Recording started${durationText}`);
            }
        }

    } catch (error) {
        console.error('Error toggling recording:', error);
        showError('Recording error: ' + error.message);
    }
}

async function checkStreamStatus() {
    try {
        console.log('Checking stream status...');
        const response = await fetch('/live/status');
        if (!response.ok) {
            console.log('Stream status check failed:', response.status);
            return;
        }

        const status = await response.json();
        console.log('Stream status:', status);

        if (status.streaming) {
            displayVideoStream();
            updateStreamControls(true);

            if (status.recording) {
                const recordBtn = document.getElementById('record-stream');
                recordBtn.innerHTML = '⏺️ Stop Recording';
                recordBtn.classList.add('recording');
            }
        }

        // Update camera status display
        const cameraStatus = document.getElementById('camera-status');
        if (cameraStatus) {
            cameraStatus.textContent = status.streaming ? 'Streaming' :
                                     status.initialized ? 'Ready' : 'Checking...';
        }

    } catch (error) {
        console.error('Error checking stream status:', error);
        const cameraStatus = document.getElementById('camera-status');
        if (cameraStatus) {
            cameraStatus.textContent = 'Error';
        }
    }
}

function refreshVideoStream() {
    const imgElement = document.getElementById('live-stream-img');
    if (imgElement && imgElement.src) {
        // Force refresh by adding timestamp
        const currentSrc = imgElement.src.split('?')[0];
        imgElement.src = currentSrc + '?t=' + Date.now();
        console.log('Video stream refreshed');
    }
}

function toggleFullscreen() {
    const imgElement = document.getElementById('live-stream-img');

    if (!imgElement || imgElement.style.display === 'none') {
        showError('Start video stream first');
        return;
    }

    if (!document.fullscreenElement) {
        imgElement.requestFullscreen().catch(err => {
            console.error('Error entering fullscreen:', err);
        });
    } else {
        document.exitFullscreen();
    }
}

function showVideoLoading(show) {
    const placeholder = document.getElementById('video-placeholder');
    const content = placeholder.querySelector('.placeholder-content');

    if (show) {
        content.innerHTML = `
            <div class="spinner"></div>
            <p>Starting video stream...</p>
        `;
    } else {
        content.innerHTML = `
            <div class="camera-icon">📹</div>
            <p>Live video stream will appear here</p>
            <small>Camera status: <span id="camera-status">Ready</span></small>
        `;
    }
}

// Utility functions for notifications
function showSuccess(message) {
    console.log('Success:', message);
    createToast(message, 'success');
}

function showError(message) {
    console.error('Error:', message);
    createToast(message, 'error');
}

function createToast(message, type) {
    // Remove existing toasts
    const existingToasts = document.querySelectorAll('.toast');
    existingToasts.forEach(toast => toast.remove());

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    toast.style.cssText = `
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

    toast.style.backgroundColor = colors[type] || colors.info;

    document.body.appendChild(toast);

    setTimeout(() => {
        toast.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => {
            if (toast.parentNode) {
                toast.remove();
            }
        }, 300);
    }, type === 'error' ? 5000 : 3000);
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

    .btn-accent {
        background-color: #dc2626;
        color: white;
    }

    .btn-accent:hover:not(:disabled) {
        background-color: #b91c1c;
    }

    .btn-accent.recording {
        background-color: #059669;
    }

    .btn-accent.recording:hover:not(:disabled) {
        background-color: #047857;
    }
`;
document.head.appendChild(style);

console.log('PetLog Dashboard JavaScript loaded');
