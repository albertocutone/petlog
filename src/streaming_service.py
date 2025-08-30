"""
Streaming service module for PetLog.

This module provides MJPEG streaming capabilities for the web dashboard.
It consumes frames from the camera service without controlling the camera directly.
"""

import logging
import time
from typing import Iterator

from fastapi.responses import StreamingResponse

from .camera_manager import get_camera_manager

logger = logging.getLogger(__name__)


class StreamingService:
    """
    Streaming service that consumes frames from the camera service
    and provides MJPEG streaming for the web dashboard.
    """

    def __init__(self):
        self.camera_manager = get_camera_manager()
        self.active_streams = 0
        self.is_streaming_active = False
        logger.info("StreamingService initialized")

    def start_streaming(self) -> bool:
        """
        Start streaming service.
        Note: This doesn't start the camera, just marks streaming as active.
        """
        try:
            # Ensure camera service is running
            if not self.camera_manager.is_running():
                logger.info("Camera service not running, starting it...")
                if not self.camera_manager.start():
                    logger.error("Failed to start camera service for streaming")
                    return False

            self.is_streaming_active = True
            logger.info("Streaming service activated")
            return True

        except Exception as e:
            logger.error(f"Failed to start streaming service: {e}")
            return False

    def stop_streaming(self) -> None:
        """
        Stop streaming service.
        Note: This doesn't stop the camera service, just marks streaming as inactive.
        """
        self.is_streaming_active = False
        logger.info("Streaming service deactivated")

    def is_active(self) -> bool:
        """Check if streaming service is active."""
        return self.is_streaming_active

    def get_stream_count(self) -> int:
        """Get number of active streams."""
        return self.active_streams

    def create_stream_response(self) -> StreamingResponse:
        """Create streaming response for MJPEG."""
        if not self.is_streaming_active:
            raise Exception("Streaming service not active, cannot stream")

        return StreamingResponse(
            self._create_stream(),
            media_type="multipart/x-mixed-replace; boundary=frame",
        )

    def _create_stream(self) -> Iterator[bytes]:
        """Generate MJPEG frames for streaming."""
        self.active_streams += 1
        logger.info(f"New stream started. Active streams: {self.active_streams}")

        try:
            camera_service = self.camera_manager.get_camera_service()
            
            while self.is_streaming_active and camera_service.is_active():
                try:
                    # Get latest frame from camera manager
                    frame = self.camera_manager.get_latest_frame()
                    
                    if frame is None:
                        logger.debug("No frame data available, waiting...")
                        time.sleep(0.1)
                        continue

                    # Convert frame to JPEG (consumer responsibility)
                    frame_jpeg = frame.to_jpeg(quality=camera_service.config.quality)

                    # Format frame for MJPEG streaming
                    yield self._format_frame(frame_jpeg)
                    
                    # Control frame rate for streaming
                    time.sleep(1.0 / camera_service.config.frame_rate)

                except Exception as e:
                    logger.error(f"Error generating frame: {e}")
                    break

        finally:
            self.active_streams -= 1
            logger.info(f"Stream ended. Active streams: {self.active_streams}")

    def _format_frame(self, frame_data: bytes) -> bytes:
        """Format frame data for MJPEG streaming."""
        return (
            (
                "--frame\r\n"
                "Content-Type: image/jpeg\r\n"
                f"Content-Length: {len(frame_data)}\r\n\r\n"
            ).encode()
            + frame_data
            + b"\r\n"
        )

    def get_status(self) -> dict:
        """Get current streaming service status."""
        return {
            "streaming_active": self.is_streaming_active,
            "active_streams": self.active_streams,
            "camera_running": self.camera_manager.is_running(),
            "camera_status": self.camera_manager.get_status()
        }


# Global streaming service instance
_streaming_service = None


def get_streaming_service() -> StreamingService:
    """Get or create the global streaming service instance."""
    global _streaming_service
    if _streaming_service is None:
        _streaming_service = StreamingService()
    return _streaming_service
