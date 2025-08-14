# Pet Camera Monitoring System Design

## Project Summary

The Pet Camera Monitoring System is a scalable, AI-powered solution for monitoring pets in real time using a Raspberry Pi 4 and camera module. The system detects and classifies pet-specific events (using face recognition for identification), records video for dynamic activities, and logs all events with metadata. Users can access live video, event logs, and recordings remotely via a simple client interface. The system is designed for reliability, security, and future extensibility, with local storage management and configurable alerts for inactivity. Its modular architecture allows for easy adaptation to new hardware, additional features, and scaling to multiple devices or users.

---

## System Requirements

### Functional Requirements

- Monitor pets using Raspberry Pi 4 and Camera Module V2.
- Detect and classify pet-specific events using real-time AI video processing (face recognition for pet identification).
- Record video for dynamic events.
- Log each event with metadata and link to its recording.
- Allow remote client access to live video, event logs, and recordings.
- Catalog events per pet for easy review.
- Alert user if no events are detected for a configurable period.
- Store recordings locally; overwrite oldest files when disk usage exceeds 80%.
- Server and client implementations are independent and scalable.

### Non-Functional Requirements

- Real-time detection with minimal latency.
- System recovers from crashes and continues monitoring.
- Secure remote access (HTTPS, authentication).
- Intuitive, simple client interface.
- Modular, scalable architecture for future expansion.
- Strong authentication and encrypted connections for remote access.
- Data retention policies and user consent for video/audio recording.

---

## Capacity Estimation

- **Number of pets:** 2 (scalable to more)
- **Number of cameras:** 1 (scalable to more)
- **Event frequency:** 10–50 events per pet per day
- **Video storage:** 720p video, ~1GB/hour; storage managed to keep usage below 80% of available disk space
- **Concurrent users:** 1 (owner), scalable to more clients
- **Database size:** Small (event logs, metadata), grows with number of events

---

## API Design

**Endpoints:**

- `GET /live` — Live video stream
- `GET /events` — List all events (filter by pet, type, date)
- `GET /events/{id}` — Get event details and associated media
- `GET /recordings` — List all recordings
- `POST /alerts/config` — Configure alert preferences

---

## Data Model

### Database Design (SQLite)

- **Event Log Table**
  - `event_id` (PK)
  - `timestamp`
  - `pet_id`
  - `event_type`
  - `media_path` (link to recording)
  - `duration` (if applicable)

- **Pet Table**
  - `pet_id` (PK)
  - `name`
  - `face_embedding` (for recognition)

- **Alert Config Table**
  - `config_id` (PK)
  - `user_id`
  - `no_event_threshold` (time in minutes/hours)

---

## High-Level Design

### Block Diagram

flowchart TD
    subgraph Hardware
        CameraModule[Raspberry Pi Camera Module V2]
        RaspberryPi[Raspberry Pi 4]
    end
    subgraph Software
        EventDetection[Event Detection Module]
        VideoRecorder[Video Recorder]
        EventLogger[Event Logger]
        AlertSystem[Alert System]
        WebServer[Python API Server]
    end
    Client[Client Interface]

    CameraModule --> RaspberryPi
    RaspberryPi --> EventDetection
    EventDetection -->|Event Detected| VideoRecorder
    EventDetection -->|Event Metadata| EventLogger
    VideoRecorder -->|Recording Info| EventLogger
    EventLogger --> AlertSystem
    RaspberryPi --> WebServer
    WebServer --> Client
    AlertSystem -->|Alert Notification| Client

#### Diagram Explanation

- **Hardware Layer:**
  The camera module captures video and sends it to the Raspberry Pi, which acts as the central processing unit.

- **Software Layer:**
  The Event Detection Module analyzes the video stream in real time, identifying pets and classifying their activities.
  When an event is detected, the Video Recorder saves the relevant footage and the Event Logger stores metadata about the event, including a link to the recording in the SQLite database.
  The Alert System monitors the event log for inactivity or other alert conditions and notifies the user as needed.

- **Web Server:**
  The Python API server (using FastAPI) exposes endpoints for live video, event logs, recordings, and alert configuration.

- **Client Interface:**
  Users access the system remotely via a web dashboard or other client, viewing live feeds, browsing events, and receiving alerts.

This modular architecture ensures that each component can be developed, tested, and scaled independently, supporting future enhancements and hardware changes.

---

## Request Flows

sequenceDiagram
    participant Camera as Camera Module
    participant Pi as Raspberry Pi
    participant Detector as Event Detection Module
    participant Recorder as Video Recorder
    participant Logger as Event Logger (SQLite DB)
    participant Server as API Server
    participant Client as Client Interface
    participant Alert as Alert System

    Camera->>Pi: Capture video stream
    Pi->>Detector: Analyze frames for pet events
    Detector->>Recorder: Trigger recording on event
    Detector->>Logger: Log event metadata
    Recorder->>Logger: Link recording to event
    Pi->>Server: Serve live stream and API requests
    Client->>Server: Request live feed, events, recordings
    Logger->>Alert: Monitor event frequency for alerts
    Alert->>Client: Send alert notifications

## Class Diagram

https://www.internalfb.com/mermaid/MM10850

## Detailed Component Design

### Event Detection Module

- Uses AI models for real-time video analysis.
- Identifies pets by face recognition.
- Classifies events (see event list below).
- Triggers recording based on event type.
- [Pet recognition + event detection](https://www.internalfb.com/metamate/message/10238445186778155)

### Event Logger

- Stores event metadata in a SQLite database.
- Links each event to its corresponding media file.
- Supports efficient querying and filtering.

### Video Recorder

- Records video for dynamic events (e.g., playing, moving).
- Stores media files in a root folder; manages disk usage.

### Alert System

- Monitors event log for absence of activity.
- Sends alerts to client if no events detected for a configurable period.
- Designed to support future alert types.

### Web/API Server

- Serves live video stream.
- Provides API endpoints for event logs, recordings, and alert configuration.
- Handles authentication and secure remote access.

### Client Interface

- Fastest and simplest implementation (e.g., web dashboard).
- Allows user to view live feed, browse events, and configure alerts.
- Designed to be independent and scalable.

---

## Technical Decisions & Architecture

### Technology Stack & Architecture

#### Programming Language & Runtime
- **Python 3.8+**: Chosen for its extensive ecosystem of AI/ML libraries, excellent hardware support on Raspberry Pi, and rapid development capabilities
- **Virtual environment**: Isolated Python environment to manage dependencies and avoid conflicts
- **pip for package management**: Standard Python package manager with requirements.txt for reproducible builds

#### Backend Framework
- **FastAPI**: Selected over Flask/Django for:
  - High performance with async support
  - Automatic API documentation generation
  - Built-in type validation and serialization
  - Modern Python syntax with type hints
  - Easy WebSocket support for live video streaming

#### Database
- **SQLite**: Chosen for local storage because:
  - Zero-configuration, serverless database
  - Perfect for single-device embedded systems
  - ACID compliance and reliability
  - Easy migration path to PostgreSQL if scaling is needed
  - Minimal resource footprint on Raspberry Pi

#### AI/Computer Vision Stack
- **OpenCV**: Industry standard for computer vision tasks
- **face_recognition library**: Simplified face detection and recognition built on dlib
- **NumPy**: Efficient array operations for image processing
- **Hardware acceleration**: Leverage Raspberry Pi GPU when available

#### Client Interface
- **Web-based dashboard**:
  - Cross-platform compatibility (desktop, mobile, tablet)
  - No app store dependencies
  - Easy to update and maintain
  - Progressive Web App (PWA) capabilities for mobile-like experience

### Infrastructure & Hardware

#### Hardware Platform
- **Raspberry Pi 4**: Chosen for:
  - Sufficient processing power for real-time video analysis
  - Excellent camera module integration
  - GPIO pins for future sensor expansion
  - Strong community support and documentation
  - Cost-effective solution
- **Camera Module V2**: Official Raspberry Pi camera for reliable integration

#### Storage Strategy
- **Local storage with automatic cleanup**:
  - Recordings stored locally on SD card/USB drive
  - Automatic deletion when storage exceeds 80% capacity
  - Oldest files deleted first (FIFO approach)
- **Future cloud backup capability**: Architecture designed to support cloud sync

### Security & Operations

#### Security & Access Control
- **HTTPS for remote access**: SSL/TLS encryption for all client communications
- **Token-based authentication**: JWT or similar for stateless authentication
- **Local network first**: Primary operation on local network with secure remote access as secondary

#### Deployment & Operations
- **Systemd service**: Run as system service on Raspberry Pi for automatic startup and restart
- **Log rotation**: Prevent log files from consuming excessive storage
- **Health monitoring**: Built-in health checks and system monitoring
- **Graceful degradation**: System continues basic operation even if some components fail

### Architecture Principles

#### Scalability
- **Horizontal scaling ready**: Architecture supports multiple cameras and devices
- **Database migration path**: Easy transition from SQLite to PostgreSQL for multi-device deployments
- **Stateless API design**: Enables load balancing and clustering if needed

#### Reliability
- **Fault tolerance**: System recovers from component failures
- **Data persistence**: Critical event data survives system restarts
- **Backup strategies**: Regular database backups and configuration snapshots

#### Maintainability
- **Clear separation of concerns**: Each module has a single responsibility
- **Comprehensive logging**: Detailed logs for debugging and monitoring
- **Documentation**: Code comments, API docs, and setup instructions
- **Type hints**: Python type annotations for better code clarity and IDE support

#### Performance
- **Async processing**: Non-blocking I/O for concurrent operations
- **Efficient video processing**: Optimized frame processing to minimize CPU usage
- **Smart recording**: Only record during events to save storage and processing
- **Configurable quality settings**: Adjustable video quality based on storage constraints

### Development Environment

#### Local Setup
- **macOS development machine**: Primary development on Apple Silicon Mac
- **VS Code**: Primary IDE with Python extensions
- **Virtual environment**: Isolated Python environment for development
- **Git hooks**: Pre-commit hooks for code formatting and linting

#### Raspberry Pi Deployment
- **Raspberry Pi OS**: Official operating system for optimal hardware support
- **SSH access**: Remote development and deployment capabilities
- **Automated deployment script**: `scripts/deploy.py` for streamlined deployments

#### Development Architecture
- **Modular architecture**: Each component (detection, recording, logging, alerts) developed as separate modules
- **API-first design**: Backend exposes RESTful API that can support multiple client types
- **Local development**: Code developed on macOS, deployed to Raspberry Pi
- **Configuration management**: Environment variables and config files for different deployment environments

### Future Considerations

#### Technology Evolution
- **Container deployment**: Docker support for easier deployment and scaling
- **Edge AI acceleration**: Support for AI accelerator hardware (Coral TPU, etc.)
- **Cloud integration**: AWS/Azure/GCP integration for backup and remote processing
- **Mobile apps**: Native iOS/Android applications for enhanced user experience

#### Feature Expansion
- **Multi-pet support**: Enhanced AI models for multiple pet recognition
- **Behavioral analytics**: Long-term behavior pattern analysis
- **Integration APIs**: Support for smart home platforms (Home Assistant, etc.)
- **Advanced alerts**: Machine learning-based anomaly detection

### Decision Log

#### Major Technical Decisions
1. **2024-01**: Chose FastAPI over Flask for better async support and automatic documentation
2. **2024-01**: Selected SQLite over PostgreSQL for initial implementation due to simplicity and embedded nature
3. **2024-01**: Decided on local-first storage with cloud backup as future enhancement
4. **2024-01**: Chose web-based client over native apps for faster development and cross-platform support
5. **2024-01**: Selected Raspberry Pi 4 over alternatives for optimal price/performance ratio

#### Trade-offs Made
- **Simplicity vs. Scalability**: Chose simpler solutions (SQLite, single-device) with clear migration paths
- **Performance vs. Cost**: Raspberry Pi provides adequate performance at low cost, with upgrade path available
- **Development Speed vs. Optimization**: Prioritized rapid development with Python, optimization can be added later
- **Local vs. Cloud**: Local-first approach for privacy and reliability, cloud features as enhancements

---

## Failure Scenarios / Bottlenecks

- **Camera/Hardware Failure:**
  System should detect and alert if camera or Pi is offline.
- **AI Model Failure:**
  Fallback to basic motion detection if face recognition fails.
- **Storage Full:**
  Automatic deletion of oldest recordings when disk usage >80%.
- **Network Issues:**
  Graceful degradation; local logging continues, remote access resumes when network is restored.
- **High Event Rate:**
  System may skip non-critical events or batch logs to avoid overload.
- **Database Corruption:**
  Regular backups and integrity checks.
- **Single Point of Failure:**
  The Raspberry Pi is a single point of failure; if it fails, monitoring stops. Mitigation: add redundancy or health checks.
- **Local Storage Limitations:**
  If the device is offline for long periods, local storage may fill up and overwrite important events. Mitigation: cloud sync or user notifications.
- **AI Model Accuracy:**
  False positives/negatives in event detection may reduce reliability. Mitigation: continuous model improvement and user feedback.
- **Scalability:**
  While the design is modular, scaling to many devices or users will require moving to a more robust backend (e.g., PostgreSQL, distributed storage).

---

## Possible Pet Events

- Passing by / Moving through camera view
- Sleeping / Resting
- Playing (active movement, chasing toys)
- Eating / Drinking
- Grooming (licking, scratching)
- Jumping / Climbing
- Sitting / Lying down
- Interacting with another pet
- Vocalizing (meowing, barking)
- Entering or leaving a designated area
- Abnormal behavior (e.g., pacing, distress)
- Absence of movement (for alerting)

---

## Future Improvements

- **Multi-camera support:**
  Expand system to monitor multiple rooms or areas.
- **Cloud backup:**
  Sync event logs and recordings to cloud storage for durability and remote access.
- **Advanced analytics:**
  Activity heatmaps, health monitoring, and behavior trends.
- **Alert enhancements:**
  Add more alert types (e.g., abnormal behavior, excessive vocalization).
- **Mobile app client:**
  Develop dedicated mobile applications for better user experience.
- **Failure mitigation:**
  - Add hardware watchdogs and redundant sensors.
  - Implement database replication and automated recovery.
  - Use cloud-based storage for critical data.
  - Monitor system health and send proactive alerts.



Revised Actionable Steps:
1. Flash Raspberry Pi OS onto SD card and set up Raspberry Pi 4 with camera module.
2. Set up Git and initialize a new GitHub project in /Users/albertocutone/local/projects.
3. Install required system dependencies on Raspberry Pi (Python, pip, camera drivers, etc.).
4. Set up Python virtual environment for the project.
5. Install core Python libraries (FastAPI, OpenCV, face recognition, SQLite, etc.).
6. Connect and test the camera module with a basic video capture script (hardware validation).
7. Design and implement the FastAPI backend server with all required API endpoints (live video, events, recordings, alerts).
8. Develop a simple client interface (web dashboard) for live video, event logs, and alerts.
9. Design and implement the SQLite database schema (event log, pet, alert config tables).
10. Develop the Event Detection Module (real-time video analysis, face recognition, event classification).
11. Implement the Video Recorder module (triggered recording, file management, storage limits).
12. Build the Event Logger to store event metadata and link to recordings.
13. Develop the Alert System (monitor inactivity, send notifications).
14. Integrate each module with the FastAPI backend and client interface, testing endpoints as features are added.
15. Set up authentication and HTTPS for secure remote access.
16. Test end-to-end system functionality (event detection, recording, logging, alerts, remote access).
17. Set up automated backups and health checks for reliability.
18. Document setup, usage, and future improvement steps in the project README.
