# petlog/tests/test_api.py
"""Tests for the FastAPI application."""

import pytest
from fastapi.testclient import TestClient
from src.api import app
from src.version import VERSION

client = TestClient(app)


def test_root_endpoint():
    """Test the root endpoint serves the dashboard."""
    response = client.get("/")
    assert response.status_code == 200
    # Root endpoint now serves HTML dashboard, not JSON


def test_api_info_endpoint():
    """Test the API info endpoint returns correct information."""
    response = client.get("/api")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Welcome to PetLog API"
    assert data["version"] == VERSION
    assert data["status"] == "running"
    assert data["documentation"] == "/docs"


def test_health_endpoint():
    """Test the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "petlog-api"
    assert "timestamp" in data
    assert "camera_status" in data
    assert "database_status" in data
    assert "storage_usage" in data


def test_version_consistency():
    """Test that version is consistent across endpoints."""
    api_response = client.get("/api")
    assert api_response.status_code == 200
    assert api_response.json()["version"] == VERSION


def test_events_endpoint():
    """Test the events listing endpoint."""
    response = client.get("/events")
    assert response.status_code == 200
    data = response.json()
    assert "events" in data
    assert "total_count" in data
    assert "page" in data
    assert "page_size" in data
    assert data["page"] == 1
    assert data["page_size"] == 50


def test_events_pagination():
    """Test events endpoint with pagination parameters."""
    response = client.get("/events?page=2&page_size=25")
    assert response.status_code == 200
    data = response.json()
    assert data["page"] == 2
    assert data["page_size"] == 25


def test_pets_endpoint():
    """Test the pets listing endpoint."""
    response = client.get("/pets")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_camera_status_endpoint():
    """Test the camera status endpoint."""
    response = client.get("/camera/status")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "resolution" in data
    assert "fps" in data


def test_create_event_endpoint():
    """Test creating a new event."""
    event_data = {
        "pet_id": 1,
        "event_type": "playing",
        "duration": 30.5,
        "confidence": 0.95,
        "metadata": {"location": "living_room"},
    }
    response = client.post("/event", json=event_data)
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Event logged successfully"
    assert "event_id" in data
    assert "timestamp" in data
    assert data["event_type"] == "playing"
    assert data["pet_id"] == 1


def test_invalid_event_type():
    """Test creating an event with invalid event type."""
    event_data = {"pet_id": 1, "event_type": "invalid_event", "duration": 30.5}
    response = client.post("/event", json=event_data)
    assert response.status_code == 422  # Validation error


def test_api_documentation_endpoints():
    """Test that API documentation endpoints are accessible."""
    # Test OpenAPI docs
    docs_response = client.get("/docs")
    assert docs_response.status_code == 200

    # Test ReDoc
    redoc_response = client.get("/redoc")
    assert redoc_response.status_code == 200

    # Test OpenAPI JSON schema
    openapi_response = client.get("/openapi.json")
    assert openapi_response.status_code == 200
    openapi_data = openapi_response.json()
    assert openapi_data["info"]["title"] == "PetLog API"
    assert openapi_data["info"]["version"] == VERSION
