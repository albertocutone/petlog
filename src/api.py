# petlog/src/api.py
import logging
import os
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .camera_manager import get_camera_manager
from .camera_service import CameraConfig
from .database import get_db
from .detection_service import (
    get_detection_service,
    start_detection_service,
    stop_detection_service,
)
from .event_tracker import get_event_tracker
from .models import (
    AlertConfig,
    Event,
    EventCreate,
    EventType,
    HealthCheck,
    PaginatedResponse,
    Pet,
    PetGender,
    PetSpecies,
    Recording,
)
from .streaming_service import get_streaming_service

from .version import VERSION

# Configure logging - console only
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
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


# All data models are now imported from models.py - single source of truth


class EventsResponse(BaseModel):
    """Response model for events listing."""

    events: List[Event]
    total_count: int
    page: int
    page_size: int


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


@app.get("/health", response_model=HealthCheck)
async def health_check() -> HealthCheck:
    """Health check endpoint for monitoring system status."""
    # TODO: Implement actual health checks for camera, database, storage
    return HealthCheck(
        status="healthy",
        service="petlog-api",
        timestamp=datetime.now(),
        version=VERSION,
        uptime_seconds=0,  # TODO: Implement actual uptime tracking
        database_status="connected",  # TODO: Implement actual database check
        camera_status="available",  # TODO: Implement actual camera check
        storage_usage={"used_percent": 0, "available_gb": 100},  # TODO: Implement actual storage check
    )


@app.get("/live/stream")
async def live_video_stream(request: Request):
    """Live MJPEG video stream endpoint."""
    client_ip = request.client.host
    logger.info(f"MJPEG stream requested from {client_ip}")

    try:
        streaming_service = get_streaming_service()

        # Ensure streaming service is active
        if not streaming_service.is_active():
            logger.info("Streaming service not active, activating...")
            if not streaming_service.start_streaming():
                logger.error("Failed to start streaming service")
                raise HTTPException(
                    status_code=500, detail="Failed to start streaming service"
                )

        logger.info(f"Serving MJPEG stream to {client_ip}")
        return streaming_service.create_stream_response()

    except Exception as e:
        logger.error(f"Error serving MJPEG stream to {client_ip}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/live/start")
async def start_live_stream(
    request: Request,
    record_duration: Optional[int] = None,
    filename: Optional[str] = None,
) -> Dict[str, Any]:
    """Start the live video stream with optional recording.

    Args:
        record_duration: Duration in seconds to record (optional)
        filename: Custom filename for recording (optional)
    """
    client_ip = request.client.host
    logger.info(
        f"Stream start requested from {client_ip} - duration: {record_duration}, filename: {filename}"
    )

    try:
        streaming_service = get_streaming_service()

        # Start streaming service
        if not streaming_service.start_streaming():
            logger.error("Failed to start streaming service")
            raise HTTPException(
                status_code=500, detail="Failed to start streaming service"
            )

        response = {
            "message": "Live stream started successfully",
            "status": "streaming",
            "stream_url": "/live/stream",
            "active_streams": streaming_service.get_stream_count(),
        }

        # TODO: Implement recording functionality in the new architecture
        if record_duration is not None:
            logger.warning(
                "Recording functionality not yet implemented in new architecture"
            )
            response["recording_note"] = (
                "Recording functionality will be implemented soon"
            )

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
        streaming_service = get_streaming_service()

        # Stop streaming service (but keep camera service running for detection)
        streaming_service.stop_streaming()

        response = {"message": "Live stream stopped successfully", "status": "stopped"}

        # TODO: Implement recording functionality in the new architecture
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
        streaming_service = get_streaming_service()
        status = streaming_service.get_status()
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
    """Get all events with optional filtering. end_date is used for filtering date ranges."""
    try:
        db = get_db()
        offset = (page - 1) * page_size

        # Get events from database with full date range filtering
        db_events = db.get_events(
            pet_id=pet_id,
            event_type=event_type.value if event_type else None,
            start_date=start_date,
            end_date=end_date,
            limit=page_size,
            offset=offset,
        )

        # Convert to API format
        events = []
        for db_event in db_events:
            # Create metadata with class_name if it exists as a direct field
            metadata = db_event.get("metadata") or {}
            if db_event.get("class_name"):
                metadata["class_name"] = db_event["class_name"]

            event = Event(
                event_id=db_event["event_id"],
                timestamp=datetime.fromisoformat(db_event["timestamp"]),
                created_at=datetime.fromisoformat(db_event["timestamp"]),
                pet_id=db_event["pet_id"],
                event_type=EventType(db_event["event_type"]),
                media_path=db_event.get("media_path"),
                duration=db_event.get("duration"),
                confidence=db_event.get("confidence"),
                metadata=metadata if metadata else None,
            )
            events.append(event)

        # Get total count for pagination
        total_events = db.get_events(
            pet_id=pet_id,
            event_type=event_type.value if event_type else None,
            start_date=start_date,
            end_date=end_date,
            limit=999999,  # Large number to get total count
            offset=0,
        )
        total_count = len(total_events)

        return EventsResponse(
            events=events, total_count=total_count, page=page, page_size=page_size
        )

    except Exception as e:
        logger.error(f"Error fetching events: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/events/{event_id}", response_model=Event)
async def get_event_details(event_id: int) -> Event:
    """Get event details and associated media."""
    try:
        db = get_db()
        db_event = db.get_event_by_id(event_id)

        if not db_event:
            raise HTTPException(status_code=404, detail="Event not found")

        # Create metadata with class_name if it exists as a direct field
        metadata = db_event.get("metadata") or {}
        if db_event.get("class_name"):
            metadata["class_name"] = db_event["class_name"]

        event = Event(
            event_id=db_event["event_id"],
            timestamp=datetime.fromisoformat(db_event["timestamp"]),
            created_at=datetime.fromisoformat(db_event["timestamp"]),
            pet_id=db_event["pet_id"],
            event_type=EventType(db_event["event_type"]),
            media_path=db_event.get("media_path"),
            duration=db_event.get("duration"),
            confidence=db_event.get("confidence"),
            metadata=metadata if metadata else None,
        )

        return event

    except ValueError as e:
        raise HTTPException(status_code=404, detail="Event not found")
    except Exception as e:
        logger.error(f"Error fetching event {event_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


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


class PetCreateRequest(BaseModel):
    """Request model for creating a new pet."""

    name: str = Field(..., min_length=1, max_length=100, description="Pet's name")
    species: PetSpecies = Field(..., description="Pet species")
    breed: Optional[str] = Field(None, max_length=100, description="Pet breed")
    color: Optional[str] = Field(
        None, max_length=100, description="Primary color/pattern"
    )
    birth_date: Optional[datetime] = Field(None, description="Approximate birth date")
    gender: PetGender = Field(PetGender.UNKNOWN, description="Pet gender")
    weight_kg: Optional[float] = Field(None, ge=0.0, description="Weight in kilograms")
    microchip_id: Optional[str] = Field(
        None, max_length=50, description="Microchip identifier"
    )
    notes: Optional[str] = Field(None, max_length=1000, description="Additional notes")


@app.get("/pets", response_model=List[Pet])
async def get_pets() -> List[Pet]:
    """Get all registered pets."""
    try:
        db = get_db()
        db_pets = db.get_pets()

        pets = []
        for db_pet in db_pets:
            pet = Pet(
                pet_id=db_pet["pet_id"],
                name=db_pet["name"],
                species=PetSpecies(db_pet["species"]),
                breed=db_pet.get("breed"),
                color=db_pet.get("color"),
                birth_date=(
                    datetime.fromisoformat(db_pet["birth_date"])
                    if db_pet.get("birth_date")
                    else None
                ),
                gender=PetGender(db_pet.get("gender", "unknown")),
                weight_kg=db_pet.get("weight_kg"),
                microchip_id=db_pet.get("microchip_id"),
                notes=db_pet.get("notes"),
                created_at=datetime.fromisoformat(db_pet["created_at"]),
                updated_at=datetime.fromisoformat(db_pet["updated_at"]),
            )
            pets.append(pet)

        return pets

    except Exception as e:
        logger.error(f"Error fetching pets: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/pets", response_model=Dict[str, Any])
async def create_pet(pet_request: PetCreateRequest) -> Dict[str, Any]:
    """Register a new pet."""
    try:
        db = get_db()
        pet_id = db.add_pet(
            name=pet_request.name,
            species=pet_request.species.value,
            breed=pet_request.breed,
            color=pet_request.color,
            birth_date=pet_request.birth_date,
            gender=pet_request.gender.value,
            weight_kg=pet_request.weight_kg,
            microchip_id=pet_request.microchip_id,
            notes=pet_request.notes,
        )

        return {
            "message": "Pet registered successfully",
            "pet_id": pet_id,
            "name": pet_request.name,
            "species": pet_request.species.value,
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating pet: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/pets/{pet_id}", response_model=Pet)
async def get_pet(pet_id: int) -> Pet:
    """Get a specific pet by ID."""
    try:
        db = get_db()
        db_pet = db.get_pet_by_id(pet_id)

        if not db_pet:
            raise HTTPException(status_code=404, detail="Pet not found")

        pet = Pet(
            pet_id=db_pet["pet_id"],
            name=db_pet["name"],
            species=PetSpecies(db_pet["species"]),
            breed=db_pet.get("breed"),
            color=db_pet.get("color"),
            birth_date=(
                datetime.fromisoformat(db_pet["birth_date"])
                if db_pet.get("birth_date")
                else None
            ),
            gender=PetGender(db_pet.get("gender", "unknown")),
            weight_kg=db_pet.get("weight_kg"),
            microchip_id=db_pet.get("microchip_id"),
            notes=db_pet.get("notes"),
            created_at=datetime.fromisoformat(db_pet["created_at"]),
            updated_at=datetime.fromisoformat(db_pet["updated_at"]),
        )

        return pet

    except ValueError as e:
        raise HTTPException(status_code=404, detail="Pet not found")
    except Exception as e:
        logger.error(f"Error fetching pet {pet_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/camera/status", response_model=Dict[str, str])
async def camera_status() -> Dict[str, str]:
    """Check camera system status."""
    camera_manager = get_camera_manager()
    status = camera_manager.get_status()
    return {
        "status": "connected" if status["initialized"] else "disconnected",
        "streaming": "active" if status.get("running", False) else "inactive",
        "recording": "inactive",  # TODO: Implement recording in new architecture
        "resolution": (
            f"{status['resolution'][0]}x{status['resolution'][1]}"
            if status.get("resolution")
            else "unknown"
        ),
        "fps": str(status.get("frame_rate", 0)),
        "last_frame": status.get("latest_frame_time", "never"),
    }


# Detection service endpoints
@app.get("/detection/status")
async def get_detection_status() -> Dict[str, Any]:
    """Get current detection service status."""
    try:
        detection_service = get_detection_service()
        return detection_service.get_status()
    except Exception as e:
        logger.error(f"Error getting detection status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/detection/start")
async def start_detection() -> Dict[str, str]:
    """Start the background detection service."""
    try:
        if start_detection_service():
            return {
                "message": "Detection service started successfully",
                "status": "running",
            }
        else:
            raise HTTPException(
                status_code=500, detail="Failed to start detection service"
            )
    except Exception as e:
        logger.error(f"Error starting detection service: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/detection/stop")
async def stop_detection() -> Dict[str, str]:
    """Stop the background detection service."""
    try:
        stop_detection_service()
        return {
            "message": "Detection service stopped successfully",
            "status": "stopped",
        }
    except Exception as e:
        logger.error(f"Error stopping detection service: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.on_event("startup")
async def startup_event():
    """Initialize services on app startup."""
    logger.info("Application starting up...")

    # Start camera service first, then detection service
    try:
        camera_manager = get_camera_manager()
        if camera_manager.start():
            logger.info("Camera service started automatically on startup")

            if start_detection_service():
                logger.info("Detection service started automatically on startup")
            else:
                logger.warning("Failed to start detection service on startup")
        else:
            logger.warning("Failed to start camera service on startup")
    except Exception as e:
        logger.error(f"Error starting services on startup: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources on app shutdown."""
    logger.info("Application shutting down...")

    # Stop detection service
    try:
        stop_detection_service()
        logger.info("Detection service stopped")
    except Exception as e:
        logger.error(f"Error stopping detection service: {e}")

    # Clean up camera resources
    from .camera_manager import cleanup_camera_manager

    cleanup_camera_manager()
    logger.info("Cleanup completed")
