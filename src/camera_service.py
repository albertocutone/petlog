"""
Camera service module for PetLog.

This module provides a continuously running camera service that captures frames
in the background and provides them to consumers (detection, streaming, etc.).
"""

import cv2
import logging
import queue
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from picamera2 import Picamera2
from .frame import Frame, FrameMetadata, FrameFormat

logger = logging.getLogger(__name__)


class CameraConfig:
    """Configuration for camera operations."""

    def __init__(
        self,
        resolution: tuple = (1280, 720),
        frame_rate: int = 15,
        quality: int = 85,
        format: str = "JPEG",
        buffer_size: int = 5,  # Number of frames to keep in buffer
        enable_storage: bool = True,
        storage_path: str = "recordings",
    ):
        self.resolution = resolution
        self.frame_rate = frame_rate
        self.quality = quality
        self.format = format
        self.buffer_size = buffer_size
        self.enable_storage = enable_storage
        self.storage_path = storage_path

    def validate(self) -> bool:
        """Validate configuration parameters."""
        if not isinstance(self.resolution, tuple) or len(self.resolution) != 2:
            return False
        if self.frame_rate <= 0 or self.frame_rate > 60:
            return False
        if self.quality < 1 or self.quality > 100:
            return False
        if self.buffer_size < 1 or self.buffer_size > 20:
            return False
        return True


class CameraService:
    """
    Continuously running camera service that captures frames in background.
    
    This service runs independently and provides frames to multiple consumers
    (detection service, streaming service, etc.) without any consumer controlling
    the camera directly.
    """

    def __init__(self, config: CameraConfig):
        self.config = config
        self.camera = None
        self.is_running = False
        self._capture_thread = None
        self._lock = threading.Lock()
        
        # Frame buffer - stores Frame objects
        self._latest_frame: Optional[Frame] = None
        self._frame_counter: int = 0
        
        # Create storage directory if needed
        if self.config.enable_storage:
            Path(self.config.storage_path).mkdir(exist_ok=True)
        
        logger.info(f"CameraService initialized with resolution {self.config.resolution}")

    def initialize(self) -> bool:
        """Initialize the camera hardware."""
        try:
            with self._lock:
                if self.camera is not None:
                    logger.warning("Camera already initialized")
                    return True

                self.camera = Picamera2()

                # Configure for continuous capture
                camera_config = self.camera.create_video_configuration(
                    main={"size": self.config.resolution, "format": "RGB888"}
                )
                self.camera.configure(camera_config)

                logger.info(f"Camera initialized with resolution {self.config.resolution}")
                return True

        except Exception as e:
            logger.error(f"Failed to initialize camera: {e}")
            return False

    def start(self) -> bool:
        """Start the continuous camera capture service."""
        with self._lock:
            if self.is_running:
                logger.warning("Camera service already running")
                return True
            
            if not self.camera:
                logger.error("Camera not initialized")
                return False

            try:
                # Start camera hardware
                self.camera.start()
                time.sleep(1)  # Allow camera to warm up

                # Start capture thread
                self.is_running = True
                self._capture_thread = threading.Thread(
                    target=self._capture_loop,
                    name="CameraService",
                    daemon=True
                )
                self._capture_thread.start()

                logger.info("Camera service started successfully")
                return True

            except Exception as e:
                logger.error(f"Failed to start camera service: {e}")
                self.is_running = False
                return False

    def stop(self) -> None:
        """Stop the camera service."""
        with self._lock:
            if not self.is_running:
                return

            logger.info("Stopping camera service...")
            self.is_running = False

            # Wait for capture thread to finish
            if self._capture_thread and self._capture_thread.is_alive():
                self._capture_thread.join(timeout=5.0)

            # Stop camera hardware
            try:
                if self.camera:
                    self.camera.stop()
                logger.info("Camera service stopped")
            except Exception as e:
                logger.error(f"Error stopping camera: {e}")

    def _capture_loop(self) -> None:
        """Main capture loop that runs in background thread."""
        logger.info("Camera capture loop started")
        frame_interval = 1.0 / self.config.frame_rate
        
        while self.is_running:
            try:
                start_time = time.time()
                
                # Capture frame from camera
                frame_array = self.camera.capture_array()
                
                # Rotate image 180 degrees
                frame_array = cv2.rotate(frame_array, cv2.ROTATE_180)
                
                # Calculate processing time
                processing_time = time.time() - start_time
                
                # Create frame metadata
                metadata = FrameMetadata(
                    timestamp=datetime.now(),
                    frame_number=self._frame_counter,
                    width=self.config.resolution[0],
                    height=self.config.resolution[1],
                    format=FrameFormat.RGB888,
                    quality=self.config.quality,
                    frame_rate=self.config.frame_rate,
                    camera_config={
                        "resolution": self.config.resolution,
                        "frame_rate": self.config.frame_rate,
                        "quality": self.config.quality
                    },
                    processing_time=processing_time
                )
                
                # Create Frame object
                frame = Frame(data=frame_array, metadata=metadata)
                
                # Update frame buffer (thread-safe)
                with self._lock:
                    self._latest_frame = frame
                    self._frame_counter += 1
                
                # Calculate sleep time to maintain frame rate
                processing_time = time.time() - start_time
                sleep_time = max(0, frame_interval - processing_time)
                
                if processing_time > frame_interval:
                    logger.debug(f"Frame processing took {processing_time:.3f}s, longer than interval {frame_interval:.3f}s")
                
                time.sleep(sleep_time)
                
            except Exception as e:
                logger.error(f"Error in capture loop: {e}")
                time.sleep(frame_interval)
        
        logger.info("Camera capture loop ended")

    def get_latest_frame(self) -> Optional[Frame]:
        """Get the latest frame."""
        with self._lock:
            return self._latest_frame

    def is_active(self) -> bool:
        """Check if the camera service is actively running."""
        return self.is_running and self._capture_thread and self._capture_thread.is_alive()

    def get_status(self) -> Dict[str, Any]:
        """Get current camera service status."""
        with self._lock:
            return {
                "initialized": self.camera is not None,
                "running": self.is_running,
                "active": self.is_active(),
                "resolution": self.config.resolution,
                "frame_rate": self.config.frame_rate,
                "quality": self.config.quality,
                "buffer_size": self.config.buffer_size,
                "storage_enabled": self.config.enable_storage,
                "latest_frame_time": self._latest_frame.timestamp.isoformat() if self._latest_frame else None,
                "has_frame_data": self._latest_frame is not None,
                "frame_counter": self._frame_counter
            }

    def cleanup(self) -> None:
        """Clean up camera resources."""
        with self._lock:
            try:
                if self.is_running:
                    self.stop()

                if self.camera:
                    self.camera.close()

                self.camera = None
                self._latest_frame = None
                self._frame_counter = 0
                
                logger.info("Camera service cleanup completed")

            except Exception as e:
                logger.error(f"Error during camera service cleanup: {e}")


# Global camera service instance
_camera_service: Optional[CameraService] = None


def get_camera_service() -> CameraService:
    """Get or create the global camera service instance."""
    global _camera_service
    if _camera_service is None:
        # Default configuration for shared camera service
        config = CameraConfig(
            resolution=(1280, 720),
            frame_rate=15,  # Balanced for both detection and streaming
            quality=85,
            buffer_size=5,
            enable_storage=True,
            storage_path="recordings",
        )
        _camera_service = CameraService(config)
    return _camera_service


def cleanup_camera_service() -> None:
    """Cleanup the global camera service."""
    global _camera_service
    if _camera_service:
        _camera_service.cleanup()
        _camera_service = None
