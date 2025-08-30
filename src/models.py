"""
Pydantic models for the Pet Camera Monitoring System.

This module defines the data models used for API request/response validation
and database operations.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator
from enum import Enum


class EventType(str, Enum):
    """Enumeration of possible pet events."""
    # Currently implemented events
    ENTERING_AREA = "entering_area"
    LEAVING_AREA = "leaving_area"
    
    # Future event types (not yet implemented)
    # PASSING_BY = "passing_by"
    # MOVING = "moving"
    # SLEEPING = "sleeping"
    # RESTING = "resting"
    # PLAYING = "playing"
    # EATING = "eating"
    # DRINKING = "drinking"
    # GROOMING = "grooming"
    # JUMPING = "jumping"
    # CLIMBING = "climbing"
    # SITTING = "sitting"
    # LYING_DOWN = "lying_down"
    # INTERACTING = "interacting"
    # VOCALIZING = "vocalizing"
    # ABNORMAL_BEHAVIOR = "abnormal_behavior"
    # NO_MOVEMENT = "no_movement"
    # UNKNOWN = "unknown"


class PetBase(BaseModel):
    """Base model for pet data."""
    name: str = Field(..., min_length=1, max_length=100, description="Pet's name")


class PetCreate(PetBase):
    """Model for creating a new pet."""
    face_embedding: Optional[str] = Field(None, description="Serialized face embedding data")


class PetUpdate(BaseModel):
    """Model for updating pet data."""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="Pet's name")
    face_embedding: Optional[str] = Field(None, description="Serialized face embedding data")


class Pet(PetBase):
    """Model for pet data with database fields."""
    pet_id: int = Field(..., description="Unique pet identifier")
    face_embedding: Optional[str] = Field(None, description="Serialized face embedding data")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    model_config = {"from_attributes": True}


class EventBase(BaseModel):
    """Base model for event data."""
    pet_id: Optional[int] = Field(None, description="ID of the pet involved")
    event_type: EventType = Field(..., description="Type of event detected")
    media_path: Optional[str] = Field(None, description="Path to associated media file")
    duration: Optional[int] = Field(None, ge=0, description="Duration of the event in seconds")
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="Confidence score of detection")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional event metadata")


class EventCreate(EventBase):
    """Model for creating a new event."""
    pass


class Event(EventBase):
    """Model for event data with database fields."""
    event_id: int = Field(..., description="Unique event identifier")
    timestamp: datetime = Field(..., description="Event timestamp")
    created_at: datetime = Field(..., description="Creation timestamp")
    pet_name: Optional[str] = Field(None, description="Name of the pet involved")

    model_config = {"from_attributes": True}


class EventFilter(BaseModel):
    """Model for filtering events."""
    pet_id: Optional[int] = Field(None, description="Filter by pet ID")
    event_type: Optional[EventType] = Field(None, description="Filter by event type")
    start_date: Optional[datetime] = Field(None, description="Filter events after this date")
    end_date: Optional[datetime] = Field(None, description="Filter events before this date")
    limit: int = Field(100, ge=1, le=1000, description="Maximum number of events to return")
    offset: int = Field(0, ge=0, description="Number of events to skip")

    @field_validator('end_date')
    @classmethod
    def end_date_after_start_date(cls, v, info):
        if v and info.data.get('start_date'):
            if v <= info.data['start_date']:
                raise ValueError('end_date must be after start_date')
        return v


class AlertConfigBase(BaseModel):
    """Base model for alert configuration."""
    no_event_threshold: int = Field(60, ge=1, le=10080, description="Minutes without events before alerting")
    alert_enabled: bool = Field(True, description="Whether alerts are enabled")
    notification_methods: Optional[List[str]] = Field(None, description="List of notification methods")


class AlertConfigCreate(AlertConfigBase):
    """Model for creating alert configuration."""
    user_id: str = Field(..., min_length=1, max_length=100, description="User identifier")


class AlertConfigUpdate(BaseModel):
    """Model for updating alert configuration."""
    no_event_threshold: Optional[int] = Field(None, ge=1, le=10080, description="Minutes without events before alerting")
    alert_enabled: Optional[bool] = Field(None, description="Whether alerts are enabled")
    notification_methods: Optional[List[str]] = Field(None, description="List of notification methods")


class AlertConfig(AlertConfigBase):
    """Model for alert configuration with database fields."""
    config_id: int = Field(..., description="Unique configuration identifier")
    user_id: str = Field(..., description="User identifier")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    model_config = {"from_attributes": True}


class RecordingBase(BaseModel):
    """Base model for recording data."""
    filename: str = Field(..., description="Recording filename")
    file_path: str = Field(..., description="Full path to recording file")
    file_size: int = Field(..., ge=0, description="File size in bytes")
    duration: Optional[int] = Field(None, ge=0, description="Recording duration in seconds")
    created_at: datetime = Field(..., description="Recording creation timestamp")


class Recording(RecordingBase):
    """Model for recording data."""
    event_id: Optional[int] = Field(None, description="Associated event ID")

    model_config = {"from_attributes": True}


class SystemStatus(BaseModel):
    """Model for system status information."""
    camera_status: str = Field(..., description="Camera system status")
    database_status: str = Field(..., description="Database status")
    storage_usage: float = Field(..., ge=0.0, le=100.0, description="Storage usage percentage")
    last_event_time: Optional[datetime] = Field(None, description="Timestamp of last recorded event")
    uptime_seconds: int = Field(..., ge=0, description="System uptime in seconds")


class DatabaseStats(BaseModel):
    """Model for database statistics."""
    pets: int = Field(..., ge=0, description="Number of pets in database")
    events: int = Field(..., ge=0, description="Number of events in database")
    alert_configs: int = Field(..., ge=0, description="Number of alert configurations")
    database_size_bytes: int = Field(..., ge=0, description="Database file size in bytes")
    database_path: str = Field(..., description="Path to database file")


class APIResponse(BaseModel):
    """Generic API response model."""
    success: bool = Field(..., description="Whether the operation was successful")
    message: str = Field(..., description="Response message")
    data: Optional[Any] = Field(None, description="Response data")


class ErrorResponse(BaseModel):
    """Error response model."""
    success: bool = Field(False, description="Always false for error responses")
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")


class PaginatedResponse(BaseModel):
    """Paginated response model."""
    items: List[Any] = Field(..., description="List of items")
    total: int = Field(..., ge=0, description="Total number of items")
    limit: int = Field(..., ge=1, description="Items per page")
    offset: int = Field(..., ge=0, description="Number of items skipped")
    has_more: bool = Field(..., description="Whether there are more items available")


class HealthCheck(BaseModel):
    """Health check response model."""
    status: str = Field(..., description="Health status")
    timestamp: datetime = Field(..., description="Health check timestamp")
    version: str = Field(..., description="Application version")
    uptime_seconds: int = Field(..., ge=0, description="Application uptime in seconds")
    database_connected: bool = Field(..., description="Database connection status")
    camera_available: bool = Field(..., description="Camera availability status")
