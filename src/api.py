# petlog/src/api.py
import os
import logging
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .version import VERSION
from .camera_streaming import camera_manager, mjpeg_streamer, CameraConfig

# Configure logging - console only
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="PetLog API",
    description="A FastAPI backend for pet activity logging and monitoring",
    version=VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Mount static files for the web dashboard
static_path = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_path):
    app.mount("/static", StaticFiles(directory=static_path), name="static")


# Pydantic Models for Data Validation


class EventType(str, Enum):
    """Enumeration of possible pet events."""

    ABNORMAL_BEHAVIOR = "abnormal_behavior"
    DRINKING = "drinking"
    EATING = "eating"
    ENTERING_AREA = "entering_area"
    GROOMING = "grooming"
    INTERACTING = "interacting"
    JUMPING = "jumping"
    LEAVING_AREA = "leaving_area"
    NO_MOVEMENT = "no_movement"
    PASSING_BY = "passing_by"
    PLAYING = "playing"
    SITTING = "sitting"
    SLEEPING = "sleeping"
    VOCALIZING = "vocalizing"


class Pet(BaseModel):
    """Pet model for database representation."""

    pet_id: int
    name: str
    face_embedding: Optional[str] = None


class EventCreate(BaseModel):
    """Model for creating new events."""

    pet_id: int = Field(..., description="ID of the pet involved in the event")
    event_type: EventType = Field(..., description="Type of event detected")
    duration: Optional[float] = Field(None, description="Duration of event in seconds")
    confidence: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="AI confidence score"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        None, description="Additional event metadata"
    )


class Event(BaseModel):
    """Model for event responses."""

    event_id: int
    timestamp: datetime
    pet_id: int
    event_type: EventType
    media_path: Optional[str] = None
    duration: Optional[float] = None
    confidence: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None


class EventsResponse(BaseModel):
    """Response model for events listing."""

    events: List[Event]
    total_count: int
    page: int
    page_size: int


class Recording(BaseModel):
    """Model for recording responses."""

    recording_id: int
    timestamp: datetime
    file_path: str
    file_size: int
    duration: float
    event_ids: List[int]


class AlertConfig(BaseModel):
    """Model for alert configuration."""

    user_id: int
    no_event_threshold: int = Field(
        ..., description="Threshold in minutes for no-event alerts"
    )
    enabled: bool = True


class HealthStatus(BaseModel):
    """Model for health check response."""

    status: str
    timestamp: datetime
    service: str
    camera_status: str
    database_status: str
    storage_usage: float


# API Endpoints


@app.get("/", response_class=FileResponse)
async def dashboard():
    """Serve the main dashboard page."""
    static_path = os.path.join(os.path.dirname(__file__), "static")
    index_path = os.path.join(static_path, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    else:
        return JSONResponse(
            {
                "message": "Welcome to PetLog API",
                "version": VERSION,
                "status": "running",
                "documentation": "/docs",
                "dashboard": "Dashboard files not found",
            }
        )


@app.get("/api", response_model=Dict[str, str])
async def api_info() -> Dict[str, str]:
    """API information endpoint."""
    return {
        "message": "Welcome to PetLog API",
        "version": VERSION,
        "status": "running",
        "documentation": "/docs",
    }


@app.get("/health", response_model=HealthStatus)
async def health_check() -> HealthStatus:
    """Health check endpoint for monitoring system status."""
    # TODO: Implement actual health checks for camera, database, storage
    return HealthStatus(
        status="healthy",
        timestamp=datetime.now(),
        service="petlog-api",
        camera_status="connected",
        database_status="operational",
        storage_usage=0.45,  # 45% usage
    )


@app.get("/live/stream")
async def live_video_stream(request: Request):
    """Live MJPEG video stream endpoint."""
    client_ip = request.client.host
    logger.info(f"MJPEG stream requested from {client_ip}")
    
    try:
        if not camera_manager.camera:
            logger.info("Camera not initialized, initializing now...")
            if not camera_manager.initialize():
                logger.error("Failed to initialize camera for streaming")
                raise HTTPException(status_code=500, detail="Failed to initialize camera")
        
        if not camera_manager.is_streaming:
            logger.info("Camera not streaming, starting stream...")
            camera_manager.start_streaming()
        
        logger.info(f"Serving MJPEG stream to {client_ip}")
        return mjpeg_streamer.create_response()
        
    except Exception as e:
        logger.error(f"Error serving MJPEG stream to {client_ip}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/live/start")
async def start_live_stream(
    request: Request,
    record_duration: Optional[int] = None,
    filename: Optional[str] = None
) -> Dict[str, Any]:
    """Start the live video stream with optional recording.
    
    Args:
        record_duration: Duration in seconds to record (optional)
        filename: Custom filename for recording (optional)
    """
    client_ip = request.client.host
    logger.info(f"Stream start requested from {client_ip} - duration: {record_duration}, filename: {filename}")
    
    try:
        if not camera_manager.camera:
            logger.info("Camera not initialized, initializing now...")
            if not camera_manager.initialize():
                logger.error("Failed to initialize camera")
                raise HTTPException(status_code=500, detail="Failed to initialize camera")
        
        logger.info("Starting camera streaming...")
        camera_manager.start_streaming()
        
        response = {
            "message": "Live stream started successfully",
            "status": "streaming",
            "stream_url": "/live/stream",
            "active_streams": mjpeg_streamer.get_stream_count()
        }
        
        # Start recording if duration is specified
        if record_duration is not None:
            if record_duration <= 0:
                logger.warning(f"Invalid recording duration: {record_duration}")
                raise HTTPException(status_code=400, detail="Recording duration must be positive")
            
            logger.info(f"Starting recording for {record_duration} seconds...")
            recording_path = camera_manager.start_recording(filename, record_duration)
            response.update({
                "recording": True,
                "recording_path": recording_path,
                "recording_duration": record_duration
            })
            logger.info(f"Recording started: {recording_path}")
        
        logger.info(f"Stream started successfully for {client_ip}")
        return response
        
    except Exception as e:
        logger.error(f"Error starting stream for {client_ip}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/live/stop")
async def stop_live_stream(request: Request) -> Dict[str, Any]:
    """Stop the live video stream and any active recording."""
    client_ip = request.client.host
    logger.info(f"Stream stop requested from {client_ip}")
    
    try:
        recording_path = None
        if camera_manager.is_recording:
            logger.info("Stopping active recording...")
            recording_path = camera_manager.stop_recording()
            logger.info(f"Recording stopped: {recording_path}")
        
        logger.info("Stopping camera streaming...")
        camera_manager.stop_streaming()
        
        response = {
            "message": "Live stream stopped successfully",
            "status": "stopped"
        }
        
        if recording_path:
            response["recording_stopped"] = True
            response["recording_path"] = recording_path
        
        logger.info(f"Stream stopped successfully for {client_ip}")
        return response
        
    except Exception as e:
        logger.error(f"Error stopping stream for {client_ip}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/live/status")
async def get_live_status(request: Request) -> Dict[str, Any]:
    """Get current live stream status."""
    client_ip = request.client.host
    logger.debug(f"Stream status requested from {client_ip}")
    
    try:
        status = camera_manager.get_status()
        status["active_streams"] = mjpeg_streamer.get_stream_count()
        logger.debug(f"Stream status: {status}")
        return status
        
    except Exception as e:
        logger.error(f"Error getting stream status for {client_ip}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/events", response_model=EventsResponse)
async def get_events(
    pet_id: Optional[int] = Query(None, description="Filter by pet ID"),
    event_type: Optional[EventType] = Query(None, description="Filter by event type"),
    start_date: Optional[datetime] = Query(
        None, description="Filter events after this date"
    ),
    end_date: Optional[datetime] = Query(
        None, description="Filter events before this date"
    ),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=1000, description="Number of events per page"),
) -> EventsResponse:
    """Get all events with optional filtering."""
    # TODO: Implement actual database query with filters
    return EventsResponse(events=[], total_count=0, page=page, page_size=page_size)


@app.get("/events/{event_id}", response_model=Event)
async def get_event_details(event_id: int) -> Event:
    """Get event details and associated media."""
    # TODO: Implement actual database query
    raise HTTPException(status_code=404, detail="Event not found")


@app.post("/event", response_model=Dict[str, Any])
async def create_event(event: EventCreate) -> Dict[str, Any]:
    """Log a new pet event."""
    # TODO: Implement actual event logging to database
    return {
        "message": "Event logged successfully",
        "event_id": 12345,  # Placeholder
        "timestamp": datetime.now().isoformat(),
        "event_type": event.event_type,
        "pet_id": event.pet_id,
    }


@app.get("/recordings", response_model=List[Recording])
async def get_recordings(
    start_date: Optional[datetime] = Query(
        None, description="Filter recordings after this date"
    ),
    end_date: Optional[datetime] = Query(
        None, description="Filter recordings before this date"
    ),
    event_id: Optional[int] = Query(None, description="Filter by associated event ID"),
) -> List[Recording]:
    """Get all recordings with optional filtering."""
    # TODO: Implement actual database query for recordings
    return []


@app.get("/recordings/{recording_id}")
async def get_recording_file(recording_id: int):
    """Download or stream a specific recording file."""
    # TODO: Implement actual file serving
    raise HTTPException(status_code=404, detail="Recording not found")


@app.post("/alerts/config", response_model=Dict[str, str])
async def configure_alerts(config: AlertConfig) -> Dict[str, str]:
    """Configure alert preferences."""
    # TODO: Implement actual alert configuration storage
    return {
        "message": "Alert configuration updated successfully",
        "user_id": str(config.user_id),
        "threshold": f"{config.no_event_threshold} minutes",
    }


@app.get("/alerts/config/{user_id}", response_model=AlertConfig)
async def get_alert_config(user_id: int) -> AlertConfig:
    """Get current alert configuration for a user."""
    # TODO: Implement actual configuration retrieval
    return AlertConfig(
        user_id=user_id, no_event_threshold=60, enabled=True  # Default 1 hour
    )


# Additional utility endpoints


@app.get("/pets", response_model=List[Pet])
async def get_pets() -> List[Pet]:
    """Get all registered pets."""
    # TODO: Implement actual database query
    return []


@app.post("/pet", response_model=Dict[str, Any])
async def create_pet(pet: Pet) -> Dict[str, Any]:
    """Register a new pet."""
    # TODO: Implement actual pet registration
    return {
        "message": "Pet registered successfully",
        "pet_id": pet.pet_id,
        "name": pet.name,
    }


@app.get("/camera/status", response_model=Dict[str, str])
async def camera_status() -> Dict[str, str]:
    """Check camera system status."""
    status = camera_manager.get_status()
    return {
        "status": "connected" if status["initialized"] else "disconnected",
        "streaming": "active" if status["streaming"] else "inactive",
        "recording": "active" if status["recording"] else "inactive",
        "resolution": f"{status['resolution'][0]}x{status['resolution'][1]}",
        "fps": str(status["frame_rate"]),
        "last_frame": datetime.now().isoformat(),
    }




# Add cleanup on app shutdown
@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources on app shutdown."""
    logger.info("Application shutting down...")
    camera_manager.cleanup()
    logger.info("Cleanup completed")
