# PetLog Web Dashboard Deployment Guide

This guide explains how to deploy the PetLog web dashboard to your Raspberry Pi.

## Prerequisites

1. Raspberry Pi 4 with Raspberry Pi OS installed
2. Python 3.8+ installed on the Pi
3. SSH access configured between your Mac and Pi
4. Network connectivity between your devices

## Deployment Steps

### 1. Deploy Project to Raspberry Pi

Use the existing deployment script to sync all files including the web dashboard:

```bash
cd /Users/albertocutone/local/projects/petlog
python scripts/deploy.py
```

This will:
- Sync all project files to the Pi at `/home/metal/projects/petlog/`
- Include the `src/static/` directory with the web dashboard files
- Set proper file permissions

### 2. Install Dependencies on Pi

SSH to your Raspberry Pi and install the required dependencies:

```bash
ssh metal@192.168.1.74
cd /home/metal/projects/petlog/

# Install dependencies using system Python (no virtual environment)
python3 -m pip install --user fastapi uvicorn python-multipart
```

### 3. Start the Web Dashboard Server

Start the FastAPI server with the web dashboard:

```bash
# On the Pi, in the project directory
python3 -m uvicorn src.api:app --host 0.0.0.0 --port 8000 --reload
```

### 5. Access the Dashboard

Open a web browser and navigate to:
```
http://192.168.1.74:8000
```

Replace `192.168.1.74` with your Pi's actual IP address.

## Dashboard Features

The web dashboard provides:

- **Live Video Feed**: Real-time camera stream (placeholder for now)
- **Event Monitoring**: Browse and filter pet activity events
- **Alert Configuration**: Set up inactivity alerts
- **System Status**: Monitor API, camera, database, and storage

## Running as a Service (Optional)

To run the dashboard automatically on boot, create a systemd service:

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
uvicorn src.api:app --host 0.0.0.0 --port 8001 --reload
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

## Development Workflow

For ongoing development:

1. **Make changes** on your Mac in `/Users/albertocutone/local/projects/petlog/src/static/`
2. **Deploy changes** using `python scripts/deploy.py`
3. **Restart server** on Pi (if using `--reload`, changes are automatic)
4. **Refresh browser** to see updates

## API Endpoints

The dashboard uses these API endpoints:

- `GET /` - Serves the dashboard HTML
- `GET /health` - System health status
- `GET /events` - Event listing with filtering
- `GET /pets` - Pet information
- `POST /alerts/config` - Alert configuration
- `GET /live` - Live video stream info

## Next Steps

Once the dashboard is running:

1. Implement actual camera integration
2. Set up the event detection system
3. Configure the database for event logging
4. Test alert functionality
5. Set up HTTPS for secure remote access

The web dashboard is now ready to serve as the client interface for your PetLog pet monitoring system!
