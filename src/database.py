"""
Database module for Pet Camera Monitoring System.

This module handles SQLite database operations including schema creation,
initialization, and basic CRUD operations for the pet monitoring system.
"""

import json
import logging
import os
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages SQLite database operations for the pet monitoring system."""

    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize the database manager.

        Args:
            db_path: Path to the SQLite database file. If None, will use environment
                    variable DATABASE_URL or default to project root/petlog.db
        """
        if db_path is None:
            # Try to get database path from environment variable
            database_url = os.getenv("DATABASE_URL", "sqlite:///petlog.db")
            if database_url.startswith("sqlite:///"):
                db_filename = database_url.replace("sqlite:///", "")
                # If it's just a filename, put it in the project root
                if not os.path.isabs(db_filename):
                    # Get the project root (parent of src directory)
                    project_root = Path(__file__).parent.parent
                    self.db_path = str(project_root / db_filename)
                else:
                    self.db_path = db_filename
            else:
                # Fallback to project root
                project_root = Path(__file__).parent.parent
                self.db_path = str(project_root / "petlog.db")
        else:
            self.db_path = db_path

        # Ensure the directory exists
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

        logger.info(f"Database will be stored at: {self.db_path}")
        self.init_database()

    def get_connection(self) -> sqlite3.Connection:
        """Get a database connection with row factory."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_database(self) -> None:
        """Initialize the database with required tables."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                # Create Pet table
                cursor.execute(
                    """
                        CREATE TABLE IF NOT EXISTS pets (
                            pet_id INTEGER PRIMARY KEY AUTOINCREMENT,
                            name TEXT NOT NULL UNIQUE,
                            species TEXT NOT NULL,
                            breed TEXT,
                            color TEXT,
                            birth_date DATE,
                            gender TEXT CHECK(gender IN ('male', 'female', 'unknown')),
                            weight_kg REAL,
                            microchip_id TEXT,
                            notes TEXT,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    """
                )

                # Create Event Log table
                cursor.execute(
                    """
                        CREATE TABLE IF NOT EXISTS event_log (
                            event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                            timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                            pet_id INTEGER,
                            event_type TEXT NOT NULL,
                            class_name TEXT,
                            media_path TEXT,
                            duration INTEGER,
                            confidence REAL,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            FOREIGN KEY (pet_id) REFERENCES pets (pet_id)
                        )
                    """
                )

                # Create Alert Config table
                cursor.execute(
                    """
                        CREATE TABLE IF NOT EXISTS alert_config (
                            config_id INTEGER PRIMARY KEY AUTOINCREMENT,
                            user_id TEXT NOT NULL,
                            no_event_threshold INTEGER NOT NULL DEFAULT 60,
                            alert_enabled BOOLEAN NOT NULL DEFAULT 1,
                            notification_methods TEXT,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            UNIQUE(user_id)
                        )
                    """
                )

                # Create indexes for better performance
                cursor.execute(
                    """
                        CREATE INDEX IF NOT EXISTS idx_event_log_timestamp 
                        ON event_log (timestamp)
                    """
                )

                cursor.execute(
                    """
                        CREATE INDEX IF NOT EXISTS idx_event_log_pet_id 
                        ON event_log (pet_id)
                    """
                )

                cursor.execute(
                    """
                        CREATE INDEX IF NOT EXISTS idx_event_log_event_type 
                        ON event_log (event_type)
                    """
                )

                conn.commit()
                logger.info("Database initialized successfully")

        except sqlite3.Error as e:
            logger.error(f"Error initializing database: {e}")
            raise

    def add_pet(
        self,
        name: str,
        species: str,
        breed: Optional[str] = None,
        color: Optional[str] = None,
        birth_date: Optional[datetime] = None,
        gender: str = "unknown",
        weight_kg: Optional[float] = None,
        microchip_id: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> int:
        """
        Add a new pet to the database.

        Args:
            name: Pet's name
            species: Pet species (cat, dog, etc.)
            breed: Pet breed (optional)
            color: Primary color/pattern (optional)
            birth_date: Approximate birth date (optional)
            gender: Pet gender (male, female, unknown)
            weight_kg: Weight in kilograms (optional)
            microchip_id: Microchip identifier (optional)
            notes: Additional notes (optional)

        Returns:
            The pet_id of the newly created pet
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO pets (name, species, breed, color, birth_date, gender, 
                                    weight_kg, microchip_id, notes, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """,
                    (
                        name,
                        species,
                        breed,
                        color,
                        birth_date,
                        gender,
                        weight_kg,
                        microchip_id,
                        notes,
                    ),
                )
                conn.commit()
                pet_id = cursor.lastrowid
                logger.info(f"Added pet '{name}' ({species}) with ID {pet_id}")
                return pet_id
        except sqlite3.IntegrityError:
            logger.error(f"Pet with name '{name}' already exists")
            raise ValueError(f"Pet with name '{name}' already exists")
        except sqlite3.Error as e:
            logger.error(f"Error adding pet: {e}")
            raise

    def get_pets(self) -> List[Dict[str, Any]]:
        """
        Get all pets from the database.

        Returns:
            List of pet dictionaries
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM pets ORDER BY name")
                return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            logger.error(f"Error fetching pets: {e}")
            raise

    def get_pet_by_id(self, pet_id: int) -> Optional[Dict[str, Any]]:
        """
        Get a pet by ID.

        Args:
            pet_id: The pet's ID

        Returns:
            Pet dictionary or None if not found
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM pets WHERE pet_id = ?", (pet_id,))
                row = cursor.fetchone()
                return dict(row) if row else None
        except sqlite3.Error as e:
            logger.error(f"Error fetching pet {pet_id}: {e}")
            raise

    def log_event(
        self,
        pet_id: Optional[int],
        event_type: str,
        class_name: Optional[str] = None,
        media_path: Optional[str] = None,
        duration: Optional[int] = None,
        confidence: Optional[float] = None,
    ) -> int:
        """
        Log a new event to the database.

        Args:
            pet_id: ID of the pet involved (can be None for unknown pets)
            event_type: Type of event detected
            class_name: Object class name (person, cat, dog, etc.)
            media_path: Path to associated media file
            duration: Duration of the event in seconds
            confidence: Confidence score of the detection

        Returns:
            The event_id of the newly created event
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO event_log 
                    (pet_id, event_type, class_name, media_path, duration, confidence)
                    VALUES (?, ?, ?, ?, ?, ?)
                """,
                    (
                        pet_id,
                        event_type,
                        class_name,
                        media_path,
                        duration,
                        confidence,
                    ),
                )
                conn.commit()
                event_id = cursor.lastrowid
                logger.info(
                    f"Logged event {event_id}: {event_type} for {class_name} (pet {pet_id})"
                )
                return event_id
        except sqlite3.Error as e:
            logger.error(f"Error logging event: {e}")
            raise

    def get_events(
        self,
        pet_id: Optional[int] = None,
        event_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """
        Get events from the database with optional filtering.

        Args:
            pet_id: Filter by pet ID
            event_type: Filter by event type
            start_date: Filter events after this date
            end_date: Filter events before this date
            limit: Maximum number of events to return
            offset: Number of events to skip

        Returns:
            List of event dictionaries
        """
        try:
            query = """
                SELECT e.*, p.name as pet_name 
                FROM event_log e 
                LEFT JOIN pets p ON e.pet_id = p.pet_id 
                WHERE 1=1
            """
            params = []

            if pet_id is not None:
                query += " AND e.pet_id = ?"
                params.append(pet_id)

            if event_type:
                query += " AND e.event_type = ?"
                params.append(event_type)

            if start_date:
                query += " AND e.timestamp >= ?"
                params.append(start_date.isoformat())

            if end_date:
                query += " AND e.timestamp <= ?"
                params.append(end_date.isoformat())

            query += " ORDER BY e.timestamp DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])

            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                events = []
                for row in cursor.fetchall():
                    event = dict(row)
                    events.append(event)
                return events
        except sqlite3.Error as e:
            logger.error(f"Error fetching events: {e}")
            raise

    def get_event_by_id(self, event_id: int) -> Optional[Dict[str, Any]]:
        """
        Get a specific event by ID.

        Args:
            event_id: The event's ID

        Returns:
            Event dictionary or None if not found
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT e.*, p.name as pet_name 
                    FROM event_log e 
                    LEFT JOIN pets p ON e.pet_id = p.pet_id 
                    WHERE e.event_id = ?
                """,
                    (event_id,),
                )
                row = cursor.fetchone()
                if row:
                    event = dict(row)
                    return event
                return None
        except sqlite3.Error as e:
            logger.error(f"Error fetching event {event_id}: {e}")
            raise

    def set_alert_config(
        self,
        user_id: str,
        no_event_threshold: int = 60,
        alert_enabled: bool = True,
        notification_methods: Optional[List[str]] = None,
    ) -> None:
        """
        Set or update alert configuration for a user.

        Args:
            user_id: User identifier
            no_event_threshold: Minutes without events before alerting
            alert_enabled: Whether alerts are enabled
            notification_methods: List of notification methods
        """
        try:
            methods_json = (
                json.dumps(notification_methods) if notification_methods else None
            )

            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO alert_config 
                    (user_id, no_event_threshold, alert_enabled, notification_methods, updated_at)
                    VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                """,
                    (user_id, no_event_threshold, alert_enabled, methods_json),
                )
                conn.commit()
                logger.info(f"Updated alert config for user {user_id}")
        except sqlite3.Error as e:
            logger.error(f"Error setting alert config: {e}")
            raise

    def get_alert_config(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get alert configuration for a user.

        Args:
            user_id: User identifier

        Returns:
            Alert configuration dictionary or None if not found
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT * FROM alert_config WHERE user_id = ?
                """,
                    (user_id,),
                )
                row = cursor.fetchone()
                if row:
                    config = dict(row)
                    if config["notification_methods"]:
                        config["notification_methods"] = json.loads(
                            config["notification_methods"]
                        )
                    return config
                return None
        except sqlite3.Error as e:
            logger.error(f"Error fetching alert config for user {user_id}: {e}")
            raise

    def get_last_event_time(self, pet_id: Optional[int] = None) -> Optional[datetime]:
        """
        Get the timestamp of the last recorded event.

        Args:
            pet_id: Optional pet ID to filter by

        Returns:
            Datetime of last event or None if no events found
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                if pet_id is not None:
                    cursor.execute(
                        """
                        SELECT MAX(timestamp) FROM event_log WHERE pet_id = ?
                    """,
                        (pet_id,),
                    )
                else:
                    cursor.execute("SELECT MAX(timestamp) FROM event_log")

                result = cursor.fetchone()[0]
                if result:
                    return datetime.fromisoformat(result)
                return None
        except sqlite3.Error as e:
            logger.error(f"Error fetching last event time: {e}")
            raise

    def cleanup_old_events(self, days_to_keep: int = 30) -> int:
        """
        Clean up old events from the database.

        Args:
            days_to_keep: Number of days of events to keep

        Returns:
            Number of events deleted
        """
        try:
            cutoff_date = datetime.now().replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            cutoff_date = cutoff_date.replace(day=cutoff_date.day - days_to_keep)

            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    DELETE FROM event_log WHERE timestamp < ?
                """,
                    (cutoff_date.isoformat(),),
                )
                deleted_count = cursor.rowcount
                conn.commit()
                logger.info(f"Cleaned up {deleted_count} old events")
                return deleted_count
        except sqlite3.Error as e:
            logger.error(f"Error cleaning up old events: {e}")
            raise

    def get_database_stats(self) -> Dict[str, Any]:
        """
        Get database statistics.

        Returns:
            Dictionary with database statistics
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                # Get table counts
                cursor.execute("SELECT COUNT(*) FROM pets")
                pet_count = cursor.fetchone()[0]

                cursor.execute("SELECT COUNT(*) FROM event_log")
                event_count = cursor.fetchone()[0]

                cursor.execute("SELECT COUNT(*) FROM alert_config")
                config_count = cursor.fetchone()[0]

                # Get database file size
                db_size = (
                    Path(self.db_path).stat().st_size
                    if Path(self.db_path).exists()
                    else 0
                )

                return {
                    "pets": pet_count,
                    "events": event_count,
                    "alert_configs": config_count,
                    "database_size_bytes": db_size,
                    "database_path": self.db_path,
                }
        except sqlite3.Error as e:
            logger.error(f"Error getting database stats: {e}")
            raise


# Global database instance
db_manager = DatabaseManager()


def get_db() -> DatabaseManager:
    """Get the global database manager instance."""
    return db_manager
