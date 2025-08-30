# Petlog - Pet Camera Monitoring System

A scalable, AI-powered pet monitoring system built for Raspberry Pi that detects and classifies pet activities using real-time video analysis and face recognition.

## Overview

Petlog is designed to monitor pets using a Raspberry Pi 4 and camera module, providing:

- **Real-time pet detection** with face recognition for identification
- **Event classification** (playing, sleeping, eating, etc.)
- **Automatic video recording** for dynamic activities
- **Remote access** via web dashboard
- **Smart alerts** for inactivity periods
- **Local storage management** with automatic cleanup

## Quick Start

### Prerequisites

- Raspberry Pi 4 with Camera Module V2
- Python 3.8+
- Git

### Installation

1. **Clone the repository**

   ```bash
   git clone https://github.com/albertocutone/petlog.git
   cd petlog
   ```

2. **Install dependencies**

   **For Host Development (macOS/Linux):**

   ```bash
   # Install runtime dependencies (system-wide)
   pip3 install -r requirements.txt

   # Note: Development tools (black, flake8, mypy) are installed globally
   # Note: picamera2 is NOT installed via pip - it's system-level on Raspberry Pi
   ```

   **For Raspberry Pi Deployment:**

   ```bash
   # First-time setup (only needed once)
   python scripts/deploy.py --first-setup

   # Regular deployments (after first setup)
   python scripts/deploy.py
   ```

   **Important Note about picamera2:**
   The `picamera2` library is installed system-wide on Raspberry Pi using:

   ```bash
   sudo apt install python3-picamera2
   ```

   It is NOT installed via pip because it doesn't work properly with pip installations. The deploy script handles this automatically during first-time setup with the `--first-setup` flag.

3. **Verify installation (Raspberry Pi only)**

   ```bash
   # Test camera hardware
   python tests/HW/test_camera.py
   ```

4. **Run the FastAPI server**

   **Local Development:**

   ```bash
   python src/main.py
   ```

### Current Features (v0.1.0)

- ✅ **MJPEG Live Streaming**: Real-time camera feed via web browser
- ✅ **Stream Controls**: Start/stop streaming with web interface
- ✅ **Recording Controls**: Start/stop recording with optional storage
- ✅ **Mock Camera Support**: Development mode without actual hardware
- ✅ **Responsive Dashboard**: Works on desktop and mobile devices
- ✅ **System Status**: Real-time monitoring of camera and system health

### Planned Features

- **AI-Powered Detection**: Uses YoloV11 for pet identification
- **Event Logging**: SQLite database for storing event metadata
- **Remote Access**: Secure HTTPS access with authentication
- **Storage Management**: Automatic cleanup when storage exceeds 80%

## API Endpoints

### Live Streaming

- `GET /live/stream` - MJPEG video stream
- `POST /live/start` - Start camera streaming
- `POST /live/stop` - Stop camera streaming
- `GET /live/status` - Get streaming status

### Recording

- `POST /live/record/start` - Start recording (requires storage enabled)
- `POST /live/record/stop` - Stop recording
- `GET /recordings` - List all recordings (coming soon)

### System

- `GET /health` - System health check
- `GET /camera/status` - Camera status
- `GET /` - Web dashboard

   # Or just deploy without starting server
   python scripts/deploy.py
   ```

   The server will be available at:
   - **Local**: http://localhost:8000
   - **Raspberry Pi**: http://192.168.1.74:8000
   - **API Documentation**: /docs (Swagger UI)
   - **Alternative Docs**: /redoc (ReDoc)
   - **Health Check**: /health

## Testing

### Manual Testing

1. **Start the server**

   ```bash
   python src/main.py
   ```

2. **Test API endpoints**

   ```bash
   # Test root endpoint
   curl http://localhost:8000/

   # Test health check
   curl http://localhost:8000/health

   # Test event creation
   curl -X POST http://localhost:8000/event \
     -H "Content-Type: application/json" \
     -d '{"pet_id": 1, "event_type": "playing", "duration": 30.5}'

   # View interactive API documentation
   open http://localhost:8000/docs
   ```

### Automated Testing

Run the test suite to verify API functionality:

```bash
# Install test dependencies
pip install pytest httpx

# Run all tests
pytest tests/

# Run API tests specifically
pytest tests/test_api.py

# Run tests with verbose output
pytest tests/test_api.py -v
```

### Development Setup

For development work, please read the [development guidelines](context.md) first.

1. **Create a feature branch**

   ```bash
   git checkout -b feat/your-feature-name
   ```

2. **Follow [conventional commit format](https://www.conventionalcommits.org/en/v1.0.0/)**

   ```bash
   git commit -m "feat(scope): description of changes"
   ```

3. **Run tests before committing**

   ```bash
   pytest tests/
   ```

## Project Structure

```
petlog/
├── docs/                    # Documentation
│   ├── design/             # System design and specifications
│   └── technical-decisions.md
├── src/                     # Source code (coming soon)
├── tests/                   # Test files (coming soon)
├── scripts/                 # Deployment scripts
├── context.md              # Development guidelines
└── main.py                 # Application entry point
```

## Key Features

- **AI-Powered Detection**: Uses OpenCV and face recognition for pet identification
- **Event Logging**: SQLite database for storing event metadata
- **Web API**: FastAPI backend with live video streaming
- **Remote Access**: Secure HTTPS access with authentication
- **Storage Management**: Automatic cleanup when storage exceeds 80%
- **Modular Architecture**: Scalable design supporting multiple cameras/pets

## Documentation

- **[Development Guidelines](context.md)** - Rules and practices for contributors
- **[Technical Decisions](docs/technical-decisions.md)** - Architecture and technology choices
- **[System Design](docs/design/petlog.md)** - Detailed system specification

## Contributing

1. Read the [development context](context.md) for coding standards
2. Create a feature branch following the naming convention
3. Use conventional commit messages for GitHub Actions compatibility
4. Ensure all tests pass before submitting PR
5. Include UML diagrams in `architectures/` folder for complex features

## Hardware Requirements

- **Raspberry Pi 4** (recommended) or compatible single-board computer
- **Camera Module V2** or USB camera
- **MicroSD card** (32GB+ recommended)
- **Stable internet connection** for remote access

## License

This project is licensed under the terms specified in the [LICENSE](LICENSE) file.

## Usage

### Starting the Application

1. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

2. **Run the server**

   ```bash
   python -m src.main
   ```

3. **Access the dashboard**
   Open your browser to `http://localhost:8000`

### Camera Configuration

The camera streaming can be configured in `src/camera_service.py`:

```python
camera_config = CameraConfig(
    resolution=(1280, 720),    # Video resolution
    frame_rate=15,             # FPS (lower = better performance)
    quality=85,                # JPEG quality (1-100)
    enable_storage=False       # Enable/disable recording capability
)
```

### Development Mode

The system automatically detects if you're running on a Raspberry Pi. On other systems, it runs in development mode with a mock camera that generates test patterns.

### Recording Videos

To enable video recording:

1. Set `enable_storage=True` in camera configuration
2. Recordings are saved to the `recordings/` directory
3. Use the web interface or API endpoints to start/stop recording

## Database Management

### SQLite Web Client Setup

To view and manage the SQLite database through a web interface, install and use `sqlite_web`:

```bash
pip install sqlite_web

sqlite_web /home/metal/projects/petlog/petlog.db -H 192.168.1.74 -p 8080
```

Access the database web interface at:
- **Raspberry Pi**: http://192.168.1.74:8080

## Monitoring Setup

For comprehensive system monitoring, install Netdata for real-time dashboard:

```bash
# Install Netdata (one-line setup)
wget -O /tmp/netdata-kickstart.sh https://my-netdata.io/kickstart.sh && sh /tmp/netdata-kickstart.sh
```

Access monitoring dashboard at:
- **Raspberry Pi**: http://YOUR_PI_IP:19999 (e.g., http://192.168.1.74:19999)


## Status

🚧 **In Development** - This project is currently in active development. Core features are being implemented following the system design specifications.

**Latest Update**: MJPEG live streaming functionality has been implemented with web dashboard controls.
