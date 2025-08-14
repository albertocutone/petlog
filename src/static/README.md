# PetLog Web Dashboard

This directory contains the web dashboard client interface for the PetLog pet monitoring system.

## Files

- `index.html` - Main dashboard HTML page
- `styles.css` - CSS styles for the dashboard
- `app.js` - JavaScript application logic

## Features

The web dashboard provides:

### 🎥 Live Video Feed
- Real-time video stream from the pet camera
- Fullscreen viewing capability
- Camera status monitoring

### 📊 Event Monitoring
- Real-time event log display
- Event filtering by pet and event type
- Detailed event information with confidence scores
- Pagination for large event lists
- Event icons for easy identification

### 🔔 Alert Configuration
- Configure inactivity alert thresholds
- Enable/disable alert notifications
- User-specific alert settings

### 📈 System Status
- API server health monitoring
- Camera connection status
- Database operational status
- Storage usage tracking
- Real-time status updates

## Usage

### 1. Deploy to Raspberry Pi

From your Mac, deploy the project to the Raspberry Pi:

```bash
cd /Users/albertocutone/local/projects/petlog
python scripts/deploy.py
```

### 2. Start the Web Dashboard Server on Raspberry Pi

SSH to your Raspberry Pi and start the server:

```bash
ssh metal@192.168.1.74
cd /home/metal/projects/petlog/
python3 -m uvicorn src.api:app --host 192.168.1.74 --port 8000 --reload
```

### 3. Access the Dashboard

Open your web browser and navigate to:
```
http://192.168.1.74:8000
```

Replace `192.168.1.74` with your Pi's actual IP address.

### 4. Dashboard Sections
- **Live Video**: View real-time camera feed
- **Recent Events**: Browse and filter pet activity events
- **Alert Configuration**: Set up inactivity alerts
- **System Status**: Monitor system health

## API Integration

The dashboard communicates with the FastAPI backend through these endpoints:

- `GET /` - Serves the dashboard
- `GET /health` - System health status
- `GET /events` - Event listing with filtering
- `GET /events/{id}` - Event details
- `GET /pets` - Pet information
- `POST /alerts/config` - Alert configuration
- `GET /alerts/config/{user_id}` - Get alert settings
- `GET /live` - Live video stream info

## Browser Compatibility

The dashboard is compatible with modern web browsers including:
- Chrome 80+
- Firefox 75+
- Safari 13+
- Edge 80+

## Mobile Support

The dashboard is responsive and works on mobile devices with:
- Touch-friendly interface
- Adaptive layout for small screens
- Mobile-optimized controls

## Development Workflow

For ongoing development:

1. **Make changes** on your Mac in `/Users/albertocutone/local/projects/petlog/src/static/`
2. **Deploy changes** using `python scripts/deploy.py`
3. **Restart server** on Pi (if using `--reload`, changes are automatic)
4. **Refresh browser** to see updates

## Running as a Service (Optional)

To run the dashboard automatically on boot, create a systemd service on the Pi:

### 1. Create Service File

```bash
sudo nano /etc/systemd/system/petlog-dashboard.service
```

Add the following content:

```ini
[Unit]
Description=PetLog Web Dashboard
After=network.target

[Service]
Type=simple
User=metal
WorkingDirectory=/home/metal/projects/petlog
ExecStart=/usr/bin/python3 -m uvicorn src.api:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

### 2. Enable and Start Service

```bash
sudo systemctl daemon-reload
sudo systemctl enable petlog-dashboard.service
sudo systemctl start petlog-dashboard.service
```

### 3. Check Service Status

```bash
sudo systemctl status petlog-dashboard.service
```

## Troubleshooting

### Port Already in Use
If port 8000 is busy, use a different port:
```bash
python3 -m uvicorn src.api:app --host 0.0.0.0 --port 8001 --reload
```

### Permission Issues
Ensure static files have proper permissions:
```bash
chmod -R 644 /home/metal/projects/petlog/src/static/*
```

### Import Errors
Make sure you're in the project directory:
```bash
cd /home/metal/projects/petlog
```

### Network Access
Ensure the Pi's firewall allows connections on port 8000:
```bash
sudo ufw allow 8000
```

## Next Steps

Once the dashboard is running:

1. Implement actual camera integration
2. Set up the event detection system
3. Configure the database for event logging
4. Test alert functionality
5. Set up HTTPS for secure remote access

The web dashboard is now ready to serve as the client interface for your PetLog pet monitoring system running on the Raspberry Pi!
