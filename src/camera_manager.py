"""
Camera manager module for PetLog.

This module provides a high-level interface to manage the camera service
and coordinate between different consumers (detection, streaming, etc.).
"""

import logging
from typing import Any, Dict, Optional

from .camera_service import get_camera_service, cleanup_camera_service, CameraService
from .frame import Frame

logger = logging.getLogger(__name__)


class CameraManager:
    """
    High-level camera manager that coordinates the camera service
    and provides a unified interface for consumers.
    """

    def __init__(self):
        self._camera_service = None
        logger.info("CameraManager initialized")

    def get_camera_service(self) -> CameraService:
        """Get the camera service instance."""
        if self._camera_service is None:
            self._camera_service = get_camera_service()
        return self._camera_service

    def get_latest_frame(self) -> Optional[Frame]:
        """Get the latest frame from the camera service."""
        try:
            camera_service = self.get_camera_service()
            return camera_service.get_latest_frame()
        except Exception as e:
            logger.error(f"Failed to get latest frame: {e}")
            return None

    def initialize(self) -> bool:
        """Initialize the camera service."""
        try:
            camera_service = self.get_camera_service()
            return camera_service.initialize()
        except Exception as e:
            logger.error(f"Failed to initialize camera manager: {e}")
            return False

    def start(self) -> bool:
        """Start the camera service."""
        try:
            camera_service = self.get_camera_service()
            
            # Initialize if not already done
            if not camera_service.camera:
                if not camera_service.initialize():
                    return False
            
            # Start the service
            return camera_service.start()
        except Exception as e:
            logger.error(f"Failed to start camera manager: {e}")
            return False

    def stop(self) -> None:
        """Stop the camera service."""
        try:
            if self._camera_service:
                self._camera_service.stop()
        except Exception as e:
            logger.error(f"Error stopping camera manager: {e}")

    def is_running(self) -> bool:
        """Check if the camera service is running."""
        if self._camera_service:
            return self._camera_service.is_active()
        return False

    def get_status(self) -> Dict[str, Any]:
        """Get current camera manager status."""
        if self._camera_service:
            status = self._camera_service.get_status()
            status["manager_initialized"] = True
            return status
        else:
            return {
                "manager_initialized": False,
                "initialized": False,
                "running": False,
                "active": False,
                "has_frame_data": False
            }

    def cleanup(self) -> None:
        """Clean up camera resources."""
        try:
            cleanup_camera_service()
            self._camera_service = None
            logger.info("Camera manager cleanup completed")
        except Exception as e:
            logger.error(f"Error during camera manager cleanup: {e}")


# Global camera manager instance
_camera_manager = None


def get_camera_manager() -> CameraManager:
    """Get or create the global camera manager instance."""
    global _camera_manager
    if _camera_manager is None:
        _camera_manager = CameraManager()
    return _camera_manager


def cleanup_camera_manager() -> None:
    """Cleanup the global camera manager."""
    global _camera_manager
    if _camera_manager:
        _camera_manager.cleanup()
        _camera_manager = None
