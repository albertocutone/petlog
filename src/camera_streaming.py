"""
Camera streaming module for PetLog.

This module provides MJPEG streaming capabilities with optional recording functionality.
Requires a real Raspberry Pi camera to be available.
"""

import logging
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterator, Optional

import cv2
from fastapi import HTTPException
from fastapi.responses import StreamingResponse
from picamera2 import Picamera2
from picamera2.encoders import H264Encoder
from picamera2.outputs import FileOutput

from .detection import DetectionConfig, prediction

logger = logging.getLogger(__name__)


class CameraConfig:
    def __init__(
        self,
        resolution: tuple = (1280, 720),
        frame_rate: int = 30,
        quality: int = 85,
        format: str = "JPEG",
        enable_storage: bool = False,
        storage_path: str = "recordings",
    ):
        self.resolution = resolution
        self.frame_rate = frame_rate
        self.quality = quality
        self.format = format
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
        return True


class CameraManager:
    """Manages camera operations for streaming and recording."""

    def __init__(self, config: CameraConfig, detection_config: DetectionConfig):
        self.config = config
        self.detection_config = detection_config
        self.camera = None
        self.is_streaming = False
        self.is_recording = False
        self.current_recording_path = None
        self._lock = threading.Lock()

        if self.config.enable_storage:
            Path(self.config.storage_path).mkdir(exist_ok=True)

    def initialize(self) -> bool:
        """Initialize the camera with current configuration."""
        try:
            with self._lock:
                if self.camera is not None:
                    logger.warning("Camera already initialized")
                    return True

                self.camera = Picamera2()

                camera_config = self.camera.create_video_configuration(
                    main={"size": self.config.resolution, "format": "RGB888"}
                )
                self.camera.configure(camera_config)

                self.camera.set_controls({
                    "AwbEnable": True,
                    "AwbMode": 0,
                })

                logger.info(
                    f"Camera initialized with resolution {self.config.resolution}"
                )
                return True

        except Exception as e:
            logger.error(f"Failed to initialize camera: {e}")
            return False

    def start_streaming(self) -> None:
        """Start camera streaming."""
        with self._lock:
            if not self.camera:
                raise HTTPException(status_code=500, detail="Camera not initialized")

            if self.is_streaming:
                logger.warning("Camera already streaming")
                return

            try:
                self.camera.start()
                time.sleep(1)

                self.is_streaming = True
                logger.info("Camera streaming started")

            except Exception as e:
                logger.error(f"Failed to start streaming: {e}")
                raise HTTPException(
                    status_code=500, detail=f"Failed to start camera: {e}"
                )

    def stop_streaming(self) -> None:
        """Stop camera streaming."""
        with self._lock:
            if not self.is_streaming:
                return

            try:
                if self.is_recording:
                    self.stop_recording()

                if self.camera:
                    self.camera.stop()

                self.is_streaming = False
                logger.info("Camera streaming stopped")

            except Exception as e:
                logger.error(f"Error stopping camera: {e}")

    def start_recording(
        self, filename: Optional[str] = None, duration: Optional[int] = None
    ) -> str:
        """Start recording stream to file.

        Args:
            filename: Custom filename for recording (optional)
            duration: Recording duration in seconds (optional, for future auto-stop)
        """
        if not self.config.enable_storage:
            raise HTTPException(status_code=400, detail="Storage not enabled")

        with self._lock:
            if self.is_recording:
                raise HTTPException(status_code=400, detail="Already recording")

            if not self.is_streaming:
                raise HTTPException(status_code=400, detail="Camera not streaming")

            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"recording_{timestamp}.h264"

            self.current_recording_path = Path(self.config.storage_path) / filename

            try:
                encoder = H264Encoder(bitrate=10000000)
                output = FileOutput(str(self.current_recording_path))
                self.camera.start_recording(encoder, output)

                self.is_recording = True
                logger.info(f"Recording started: {self.current_recording_path}")

                # TODO: Implement auto-stop after duration if specified
                if duration:
                    logger.info(f"Recording will auto-stop after {duration} seconds")

                return str(self.current_recording_path)

            except Exception as e:
                logger.error(f"Failed to start recording: {e}")
                raise HTTPException(
                    status_code=500, detail=f"Failed to start recording: {e}"
                )

    def stop_recording(self) -> Optional[str]:
        """Stop recording and return the file path."""
        with self._lock:
            if not self.is_recording:
                return None

            try:
                if self.camera:
                    self.camera.stop_recording()

                recording_path = self.current_recording_path
                self.is_recording = False
                self.current_recording_path = None

                logger.info(f"Recording stopped: {recording_path}")
                return str(recording_path) if recording_path else None

            except Exception as e:
                logger.error(f"Error stopping recording: {e}")
                return None

    def capture_frame(self) -> bytes:
        """Capture a single frame as JPEG bytes with optional object detection."""
        if not self.is_streaming:
            raise HTTPException(status_code=400, detail="Camera not streaming")

        try:
            frame = self.camera.capture_array()
            frame = cv2.rotate(frame, cv2.ROTATE_180)

            if self.detection_config.enabled:
                try:
                    annotated_frame, detections = prediction(
                        config=self.detection_config,
                        image=frame
                    )
                    
                    frame = annotated_frame
                    
                    if detections:
                        class_counts = {}
                        for det in detections:
                            class_name = det['class_name']
                            class_counts[class_name] = class_counts.get(class_name, 0) + 1
                        logger.info(f"Objects detected: {dict(class_counts)}")
                        
                except Exception as e:
                    logger.error(f"Detection failed, using original frame: {e}")

            _, jpeg_buffer = cv2.imencode(
                ".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, self.config.quality]
            )
            return jpeg_buffer.tobytes()

        except Exception as e:
            logger.error(f"Failed to capture frame: {e}")
            raise HTTPException(status_code=500, detail="Failed to capture frame")

    def get_status(self) -> Dict[str, Any]:
        """Get current camera status."""
        return {
            "initialized": self.camera is not None,
            "streaming": self.is_streaming,
            "recording": self.is_recording,
            "resolution": self.config.resolution,
            "frame_rate": self.config.frame_rate,
            "storage_enabled": self.config.enable_storage,
            "detection_enabled": self.detection_config.enabled,
            "detection_model": self.detection_config.model_name,
            "current_recording": (
                str(self.current_recording_path)
                if self.current_recording_path
                else None
            ),
        }

    def cleanup(self) -> None:
        """Clean up camera resources."""
        with self._lock:
            try:
                if self.is_recording:
                    self.stop_recording()

                if self.is_streaming:
                    self.stop_streaming()

                if self.camera:
                    self.camera.close()

                self.camera = None
                logger.info("Camera cleanup completed")

            except Exception as e:
                logger.error(f"Error during cleanup: {e}")


class MJPEGStreamer:
    """Handles MJPEG streaming responses."""

    def __init__(self, camera_manager: CameraManager):
        self.camera_manager = camera_manager
        self.boundary = "frame"
        self.active_streams = 0

    def generate_frames(self) -> Iterator[bytes]:
        """Generate MJPEG frames for streaming."""
        self.active_streams += 1
        logger.info(f"New stream started. Active streams: {self.active_streams}")

        try:
            while self.camera_manager.is_streaming:
                try:
                    frame_data = self.camera_manager.capture_frame()
                    yield self.format_frame(frame_data)
                    time.sleep(1.0 / self.camera_manager.config.frame_rate)

                except Exception as e:
                    logger.error(f"Error generating frame: {e}")
                    break

        finally:
            self.active_streams -= 1
            logger.info(f"Stream ended. Active streams: {self.active_streams}")

    def format_frame(self, frame_data: bytes) -> bytes:
        """Format frame data for MJPEG streaming."""
        return (
            (
                f"--{self.boundary}\r\n"
                f"Content-Type: image/jpeg\r\n"
                f"Content-Length: {len(frame_data)}\r\n\r\n"
            ).encode()
            + frame_data
            + b"\r\n"
        )

    def create_response(self) -> StreamingResponse:
        """Create streaming response for MJPEG."""
        return StreamingResponse(
            self.generate_frames(),
            media_type=f"multipart/x-mixed-replace; boundary={self.boundary}",
        )

    def get_stream_count(self) -> int:
        """Get number of active streams."""
        return self.active_streams


# Global instances with YOLO11 NCNN detection enabled
camera_config = CameraConfig(
    resolution=(1280, 720),
    frame_rate=72,
    quality=85,
    enable_storage=True,
    storage_path="recordings",
)

detection_config = DetectionConfig(
    enabled=True,
    model_name="yolo11n",
    confidence=0.5,
    target_classes=None,
)

camera_manager = CameraManager(camera_config, detection_config)
mjpeg_streamer = MJPEGStreamer(camera_manager)
