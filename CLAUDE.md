---
oncalls: ["albertocutone"]
---

# Petlog Devmate Context File

## Project Overview

Petlog is a scalable, AI-powered pet monitoring system built for Raspberry Pi that detects and classifies pet activities using real-time video analysis and face recognition. The system provides real-time pet detection with face recognition for identification, event classification (playing, sleeping, eating, etc.), automatic video recording for dynamic activities, remote access via web dashboard, smart alerts for inactivity periods, and local storage management with automatic cleanup.

## Codebase Structure

- `src/`: Core application source code
- `src/api.py`: FastAPI backend with REST endpoints
- `src/camera_streaming.py`: MJPEG streaming and camera management
- `src/detection.py`: AI-powered pet detection and classification
- `src/database.py`: SQLite database operations for event logging
- `src/models.py`: Pydantic data models and schemas
- `src/static/`: Web dashboard frontend (HTML, CSS, JavaScript)
- `tests/`: Test suite including hardware and API tests
- `scripts/deploy.py`: Raspberry Pi deployment automation
- `docs/`: Technical documentation and system design

## Key Files and Components

- `src/main.py`: Application entry point with uvicorn server
- `src/api.py`: FastAPI application with live streaming and recording endpoints
- `src/camera_streaming.py`: Camera abstraction with mock support for development
- `src/detection.py`: OpenCV and face recognition integration
- `src/database.py`: SQLite database with event and pet management
- `src/static/index.html`: Responsive web dashboard
- `tests/HW/test_camera.py`: Hardware-specific camera tests
- `scripts/deploy.py`: Automated deployment to Raspberry Pi

## Development Guidelines

1. **Use Type Hints and Clear Naming:**
   All Python functions must include type annotations. Use self-documenting variable and function names to minimize the need for comments.

2. **Follow SOLID Principles:**
   Apply Single Responsibility Principle and modular design. Break functionality into small, reusable components following Object-Oriented Design principles.

3. **Configuration Over Hardcoding:**
   Use environment variables and config files for settings. No magic numbers - use named constants with descriptive names.

4. **Conventional Commits Required:**
   Use [conventional commit format](https://www.conventionalcommits.org/en/v1.0.0/#summary) for GitHub Actions compatibility:
   - `feat(scope): description` for new features
   - `fix(scope): description` for bug fixes
   - `docs: description` for documentation changes
   - `test(scope): description` for test additions

5. **Test-Driven Development:**
   Write unit tests for all new functionality. Use pytest framework with tests in `tests/` directory mirroring source structure. Mock external dependencies (camera, hardware).

6. **Incremental Development:**
   Break work into small, atomic tasks completable in 0.5 hours. Each commit should build and run successfully.
   Do not add functionality outside of the prompt, just propose them as next steps.

7. **Error Handling and Logging:**
   Implement graceful degradation - system should continue operating when non-critical components fail. Use structured logging with appropriate levels (DEBUG, INFO, WARNING, ERROR, CRITICAL).

8. **Raspberry Pi Optimization:**
   Monitor memory usage especially for video processing. Use hardware acceleration when available. Implement automatic cleanup for old recordings.

9. **Remote Development:**
   Modify the source code on your Mac host, then sync changes to the Raspberry Pi using the deploy script. All test commands should be executed on the Raspberry Pi.

## Common Commands

- `python src/main.py`: Start the FastAPI server locally
- `python scripts/deploy.py --first-setup`: First-time Raspberry Pi setup
- `python scripts/deploy.py`: Regular deployment to Raspberry Pi
- `pytest tests/`: Run all tests
- `pytest tests/test_api.py -v`: Run API tests with verbose output
- `python tests/HW/test_camera.py`: Test camera hardware (Raspberry Pi only)
- `curl http://localhost:8000/health`: Health check endpoint
- `curl http://localhost:8000/live/status`: Check streaming status

Additional:

- Start streaming: `curl -X POST http://localhost:8000/live/start`
- Stop streaming: `curl -X POST http://localhost:8000/live/stop`
- Start recording: `curl -X POST http://localhost:8000/live/record/start`
- Stop recording: `curl -X POST http://localhost:8000/live/record/stop`
- View dashboard: `http://localhost:8000` (or `http://192.168.1.74:8000` on Pi)
- API documentation: `http://localhost:8000/docs` (Swagger UI)
- Alternative docs: `http://localhost:8000/redoc` (ReDoc)

## Known Issues

- `picamera2` library must be installed system-wide on Raspberry Pi using `sudo apt install python3-picamera2` - it doesn't work with pip installations
- Mock camera is automatically used on non-Raspberry Pi systems for development
- Memory usage can be high during video processing - monitor and optimize accordingly
- Storage management requires manual configuration of cleanup thresholds

## Additional Resources

- [Development Guidelines (context.md)](context.md) - Complete development rules and practices
- [Technical Decisions (docs/technical-decisions.md)](docs/technical-decisions.md) - Architecture and technology choices
- [System Design (docs/design/petlog.md)](docs/design/petlog.md) - Detailed system specification
- [Streaming Documentation (docs/STREAMING.md)](docs/STREAMING.md) - Video streaming implementation details
- [Event System Design (docs/design/events.md)](docs/design/events.md) - Event classification and logging
- [Deployment Guide (DEPLOYMENT.md)](DEPLOYMENT.md) - Raspberry Pi deployment instructions
