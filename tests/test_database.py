"""
Unit tests for the database module.

This module contains comprehensive tests for the SQLite database operations
including schema creation, CRUD operations, and data integrity.
"""

import os
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from src.database import DatabaseManager
from src.models import EventType


class TestDatabaseManager:
    """Test cases for DatabaseManager class."""

    @pytest.fixture
    def temp_db(self):
        """Create a temporary database for testing."""
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        temp_file.close()
        db_manager = DatabaseManager(temp_file.name)
        yield db_manager
        # Cleanup
        os.unlink(temp_file.name)

    def test_database_initialization(self, temp_db):
        """Test that database tables are created correctly."""
        with temp_db.get_connection() as conn:
            cursor = conn.cursor()

            # Check that all tables exist
            cursor.execute(
                """
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name IN ('pets', 'event_log', 'alert_config')
            """
            )
            tables = [row[0] for row in cursor.fetchall()]

            assert "pets" in tables
            assert "event_log" in tables
            assert "alert_config" in tables

            # Check that indexes exist
            cursor.execute(
                """
                SELECT name FROM sqlite_master 
                WHERE type='index' AND name LIKE 'idx_%'
            """
            )
            indexes = [row[0] for row in cursor.fetchall()]

            assert "idx_event_log_timestamp" in indexes
            assert "idx_event_log_pet_id" in indexes
            assert "idx_event_log_event_type" in indexes

    def test_add_pet(self, temp_db):
        """Test adding a new pet."""
        pet_id = temp_db.add_pet("Fluffy", "cat")

        assert isinstance(pet_id, int)
        assert pet_id > 0

        # Verify pet was added
        pet = temp_db.get_pet_by_id(pet_id)
        assert pet is not None
        assert pet["name"] == "Fluffy"
        assert pet["species"] == "cat"
        assert pet["pet_id"] == pet_id

    def test_add_duplicate_pet_name(self, temp_db):
        """Test that adding a pet with duplicate name raises error."""
        temp_db.add_pet("Fluffy", "cat")

        with pytest.raises(ValueError, match="Pet with name 'Fluffy' already exists"):
            temp_db.add_pet("Fluffy", "dog")

    def test_get_pets(self, temp_db):
        """Test retrieving all pets."""
        # Add multiple pets
        temp_db.add_pet("Fluffy", "cat")
        temp_db.add_pet("Whiskers", "cat")
        temp_db.add_pet("Buddy", "dog")

        pets = temp_db.get_pets()

        assert len(pets) == 3
        pet_names = [pet["name"] for pet in pets]
        assert "Fluffy" in pet_names
        assert "Whiskers" in pet_names
        assert "Buddy" in pet_names

        # Check that pets are ordered by name
        assert pets[0]["name"] == "Buddy"  # Alphabetically first
        assert pets[1]["name"] == "Fluffy"
        assert pets[2]["name"] == "Whiskers"

    def test_get_pet_by_id_not_found(self, temp_db):
        """Test retrieving a non-existent pet."""
        pet = temp_db.get_pet_by_id(999)
        assert pet is None

    def test_log_event(self, temp_db):
        """Test logging a new event."""
        # Add a pet first
        pet_id = temp_db.add_pet("Fluffy", "cat")

        # Log an event
        event_id = temp_db.log_event(
            pet_id=pet_id,
            event_type=EventType.ENTERING_AREA.value,
            media_path="/recordings/video_001.mp4",
            duration=30,
            confidence=0.95,
        )

        assert isinstance(event_id, int)
        assert event_id > 0

        # Verify event was logged
        event = temp_db.get_event_by_id(event_id)
        assert event is not None
        assert event["pet_id"] == pet_id
        assert event["event_type"] == EventType.ENTERING_AREA.value
        assert event["media_path"] == "/recordings/video_001.mp4"
        assert event["duration"] == 30
        assert event["confidence"] == 0.95
        assert event["pet_name"] == "Fluffy"

    def test_log_event_without_pet(self, temp_db):
        """Test logging an event without a specific pet."""
        event_id = temp_db.log_event(
            pet_id=None, event_type=EventType.LEAVING_AREA.value, confidence=0.5
        )

        assert isinstance(event_id, int)

        event = temp_db.get_event_by_id(event_id)
        assert event is not None
        assert event["pet_id"] is None
        assert event["pet_name"] is None
        assert event["event_type"] == EventType.LEAVING_AREA.value

    def test_get_events_no_filter(self, temp_db):
        """Test retrieving events without filters."""
        pet_id = temp_db.add_pet("Fluffy", "cat")

        # Log multiple events
        temp_db.log_event(pet_id, EventType.ENTERING_AREA.value)
        temp_db.log_event(pet_id, EventType.LEAVING_AREA.value)
        temp_db.log_event(pet_id, EventType.ENTERING_AREA.value)

        events = temp_db.get_events()

        assert len(events) == 3
        # Events should be ordered by timestamp DESC (newest first)
        assert events[0]["event_type"] == EventType.ENTERING_AREA.value
        assert events[1]["event_type"] == EventType.LEAVING_AREA.value
        assert events[2]["event_type"] == EventType.ENTERING_AREA.value

    def test_get_events_with_pet_filter(self, temp_db):
        """Test retrieving events filtered by pet."""
        pet1_id = temp_db.add_pet("Fluffy", "cat")
        pet2_id = temp_db.add_pet("Whiskers", "cat")

        temp_db.log_event(pet1_id, EventType.ENTERING_AREA.value)
        temp_db.log_event(pet2_id, EventType.LEAVING_AREA.value)
        temp_db.log_event(pet1_id, EventType.LEAVING_AREA.value)

        # Filter by pet1
        events = temp_db.get_events(pet_id=pet1_id)

        assert len(events) == 2
        for event in events:
            assert event["pet_id"] == pet1_id
            assert event["pet_name"] == "Fluffy"

    def test_get_events_with_type_filter(self, temp_db):
        """Test retrieving events filtered by event type."""
        pet_id = temp_db.add_pet("Fluffy", "cat")

        temp_db.log_event(pet_id, EventType.ENTERING_AREA.value)
        temp_db.log_event(pet_id, EventType.LEAVING_AREA.value)
        temp_db.log_event(pet_id, EventType.ENTERING_AREA.value)

        # Filter by event type
        events = temp_db.get_events(event_type=EventType.ENTERING_AREA.value)

        assert len(events) == 2
        for event in events:
            assert event["event_type"] == EventType.ENTERING_AREA.value

    def test_get_events_with_date_filter(self, temp_db):
        """Test retrieving events filtered by date range."""
        pet_id = temp_db.add_pet("Fluffy", "cat")

        # Create events with different timestamps
        now = datetime.now()
        yesterday = now - timedelta(days=1)
        tomorrow = now + timedelta(days=1)

        temp_db.log_event(pet_id, EventType.ENTERING_AREA.value)

        # Filter by date range
        events = temp_db.get_events(start_date=yesterday, end_date=tomorrow)

        assert len(events) == 1
        event_time = datetime.fromisoformat(events[0]["timestamp"])
        assert yesterday <= event_time <= tomorrow

    def test_get_events_pagination(self, temp_db):
        """Test event pagination."""
        pet_id = temp_db.add_pet("Fluffy", "cat")

        # Create 5 events
        for i in range(5):
            event_type = (
                EventType.ENTERING_AREA.value
                if i % 2 == 0
                else EventType.LEAVING_AREA.value
            )
            temp_db.log_event(pet_id, event_type)

        # Get first 2 events
        events_page1 = temp_db.get_events(limit=2, offset=0)
        assert len(events_page1) == 2

        # Get next 2 events
        events_page2 = temp_db.get_events(limit=2, offset=2)
        assert len(events_page2) == 2

        # Ensure no overlap
        page1_ids = [e["event_id"] for e in events_page1]
        page2_ids = [e["event_id"] for e in events_page2]
        assert not set(page1_ids).intersection(set(page2_ids))

    def test_set_alert_config(self, temp_db):
        """Test setting alert configuration."""
        user_id = "test_user"
        notification_methods = ["email", "push"]

        temp_db.set_alert_config(
            user_id=user_id,
            no_event_threshold=120,
            alert_enabled=True,
            notification_methods=notification_methods,
        )

        config = temp_db.get_alert_config(user_id)

        assert config is not None
        assert config["user_id"] == user_id
        assert config["no_event_threshold"] == 120
        assert config["alert_enabled"] == 1  # SQLite stores as integer
        assert config["notification_methods"] == notification_methods

    def test_update_alert_config(self, temp_db):
        """Test updating existing alert configuration."""
        user_id = "test_user"

        # Set initial config
        temp_db.set_alert_config(user_id, 60, True, ["email"])

        # Update config
        temp_db.set_alert_config(user_id, 180, False, ["push", "sms"])

        config = temp_db.get_alert_config(user_id)

        assert config["no_event_threshold"] == 180
        assert config["alert_enabled"] == 0  # False stored as 0
        assert config["notification_methods"] == ["push", "sms"]

    def test_get_alert_config_not_found(self, temp_db):
        """Test retrieving non-existent alert configuration."""
        config = temp_db.get_alert_config("nonexistent_user")
        assert config is None

    def test_get_last_event_time(self, temp_db):
        """Test retrieving last event timestamp."""
        # No events initially
        last_time = temp_db.get_last_event_time()
        assert last_time is None

        # Add a pet and event
        pet_id = temp_db.add_pet("Fluffy", "cat")
        temp_db.log_event(pet_id, EventType.ENTERING_AREA.value)

        last_time = temp_db.get_last_event_time()
        assert last_time is not None
        assert isinstance(last_time, datetime)

        # Test with specific pet filter
        pet2_id = temp_db.add_pet("Whiskers", "cat")
        last_time_pet2 = temp_db.get_last_event_time(pet_id=pet2_id)
        assert last_time_pet2 is None  # No events for pet2

        temp_db.log_event(pet2_id, EventType.LEAVING_AREA.value)
        last_time_pet2 = temp_db.get_last_event_time(pet_id=pet2_id)
        assert last_time_pet2 is not None

    def test_cleanup_old_events(self, temp_db):
        """Test cleaning up old events."""
        pet_id = temp_db.add_pet("Fluffy", "cat")

        # Add some events
        for i in range(3):
            event_type = (
                EventType.ENTERING_AREA.value
                if i % 2 == 0
                else EventType.LEAVING_AREA.value
            )
            temp_db.log_event(pet_id, event_type)

        # Cleanup with 0 days to keep (should delete all)
        deleted_count = temp_db.cleanup_old_events(days_to_keep=0)

        assert deleted_count == 3

        # Verify events were deleted
        events = temp_db.get_events()
        assert len(events) == 0

    def test_get_database_stats(self, temp_db):
        """Test retrieving database statistics."""
        # Add some data
        pet_id = temp_db.add_pet("Fluffy", "cat")
        temp_db.log_event(pet_id, EventType.ENTERING_AREA.value)
        temp_db.set_alert_config("test_user", 60)

        stats = temp_db.get_database_stats()

        assert stats["pets"] == 1
        assert stats["events"] == 1
        assert stats["alert_configs"] == 1
        assert stats["database_size_bytes"] > 0
        assert stats["database_path"] == temp_db.db_path

    def test_event_class_name_field(self, temp_db):
        """Test that event class_name field works correctly."""
        pet_id = temp_db.add_pet("Fluffy", "cat")

        event_id = temp_db.log_event(
            pet_id=pet_id,
            event_type=EventType.ENTERING_AREA.value,
            class_name="cat",
            confidence=0.95,
        )

        event = temp_db.get_event_by_id(event_id)

        assert event["class_name"] == "cat"
        assert event["confidence"] == 0.95

    def test_foreign_key_constraint(self, temp_db):
        """Test that foreign key relationships work correctly."""
        # This test verifies that we can reference pets in events
        pet_id = temp_db.add_pet("Fluffy", "cat")
        event_id = temp_db.log_event(pet_id, EventType.ENTERING_AREA.value)

        # Get event with pet name
        event = temp_db.get_event_by_id(event_id)
        assert event["pet_name"] == "Fluffy"

        # Events can also have null pet_id for unknown pets
        event_id2 = temp_db.log_event(None, EventType.LEAVING_AREA.value)
        event2 = temp_db.get_event_by_id(event_id2)
        assert event2["pet_id"] is None
        assert event2["pet_name"] is None


if __name__ == "__main__":
    pytest.main([__file__])
