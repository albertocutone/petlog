"""
Background detection service for PetLog.

This service runs continuously in the background, performing object detection
and event logging independently of camera streaming for the dashboard.
"""

import cv2
import logging
import numpy as np
import threading
import time
from datetime import datetime
from typing import Optional

from .camera_manager import get_camera_manager
from .detection import DetectionConfig, prediction
from .event_tracker import get_event_tracker

logger = logging.getLogger(__name__)


class DetectionService:
    """Background service for continuous object detection and event logging."""
    
    def __init__(self, 
                 detection_interval: float = 2.0,
                 detection_config: Optional[DetectionConfig] = None):
        """
        Initialize the detection service.
        
        Args:
            detection_interval: Time between detection runs in seconds
            detection_config: Configuration for object detection
        """
        self.detection_interval = detection_interval
        self.detection_config = detection_config or DetectionConfig(
            enabled=True,
            model_name="yolo11n",
            confidence=0.5,
            target_classes=["person", "cat", "dog"]  # Focus on pets and people
        )
        
        # Try to use the global camera manager if available, otherwise create our own
        self.camera_manager = get_camera_manager()
        self.event_tracker = get_event_tracker()
        
        self._running = False
        self._detection_thread = None
        self._lock = threading.Lock()
        
        logger.info(f"DetectionService initialized with interval={detection_interval}s")
    
    def start(self) -> bool:
        """Start the background detection service."""
        with self._lock:
            if self._running:
                logger.warning("Detection service already running")
                return True
            
            try:
                # Use the camera manager to access camera service
                logger.info("Using camera manager for detection")
                self.camera_manager = get_camera_manager()
                self.use_global_camera = True
                
                # Ensure camera service is running
                if not self.camera_manager.is_running():
                    logger.info("Camera service not running, starting it...")
                    if not self.camera_manager.start():
                        logger.error("Failed to start camera service for detection")
                        return False
                
                # Start detection thread
                self._running = True
                self._detection_thread = threading.Thread(
                    target=self._detection_loop,
                    name="DetectionService",
                    daemon=True
                )
                self._detection_thread.start()
                
                logger.info("Detection service started successfully")
                return True
                
            except Exception as e:
                logger.error(f"Failed to start detection service: {e}")
                self._running = False
                return False
    
    def stop(self) -> None:
        """Stop the background detection service."""
        with self._lock:
            if not self._running:
                return
            
            logger.info("Stopping detection service...")
            self._running = False
            
            # Wait for detection thread to finish
            if self._detection_thread and self._detection_thread.is_alive():
                self._detection_thread.join(timeout=5.0)
            
            # Don't stop the global camera manager - let the main camera service handle it
            logger.info("Detection service stopped")
    
    def _detection_loop(self) -> None:
        """Main detection loop that runs in background thread."""
        logger.info("Detection loop started")
        
        while self._running:
            try:
                start_time = time.time()
                
                # Check if camera service is running
                if not self.camera_manager.is_running():
                    logger.warning("Camera service not active, skipping detection")
                    time.sleep(self.detection_interval)
                    continue
                
                # Get frame from camera manager
                frame = self.camera_manager.get_latest_frame()
                
                if frame is None:
                    logger.warning("No frame available for detection")
                    time.sleep(self.detection_interval)
                    continue
                
                # Get frame data for detection
                frame_data = frame.copy_data()
                
                # Run object detection
                annotated_frame, detections = prediction(
                    config=self.detection_config,
                    image=frame_data,
                    display_result=False
                )
                
                # Process detections and generate events
                if detections:
                    events = self.event_tracker.process_detections(detections)
                    if events:
                        logger.info(f"Generated {len(events)} events from detection")
                else:
                    # Check for leaving events even when no detections
                    events = self.event_tracker._check_for_leaving_objects(time.time())
                    if events:
                        logger.info(f"Generated {len(events)} leaving events")
                
                # Calculate processing time and adjust sleep
                processing_time = time.time() - start_time
                sleep_time = max(0, self.detection_interval - processing_time)
                
                if processing_time > self.detection_interval:
                    logger.warning(f"Detection took {processing_time:.2f}s, longer than interval {self.detection_interval}s")
                
                time.sleep(sleep_time)
                
            except Exception as e:
                logger.error(f"Error in detection loop: {e}")
                time.sleep(self.detection_interval)
        
        logger.info("Detection loop ended")
    
    def get_status(self) -> dict:
        """Get current status of the detection service."""
        camera_status = self.camera_manager.get_status()
        return {
            "running": self._running,
            "detection_interval": self.detection_interval,
            "camera_service_running": camera_status.get("running", False),
            "camera_service_active": camera_status.get("active", False),
            "detection_config": {
                "enabled": self.detection_config.enabled,
                "model_name": self.detection_config.model_name,
                "confidence": self.detection_config.confidence,
                "target_classes": self.detection_config.target_classes
            },
            "current_objects": dict(self.event_tracker.current_objects) if hasattr(self.event_tracker, 'current_objects') else {}
        }
    
    def is_running(self) -> bool:
        """Check if the detection service is running."""
        return self._running


# Global detection service instance
_detection_service: Optional[DetectionService] = None


def get_detection_service() -> DetectionService:
    """Get or create the global detection service instance."""
    global _detection_service
    if _detection_service is None:
        _detection_service = DetectionService()
    return _detection_service


def start_detection_service() -> bool:
    """Start the global detection service."""
    service = get_detection_service()
    return service.start()


def stop_detection_service() -> None:
    """Stop the global detection service."""
    global _detection_service
    if _detection_service:
        _detection_service.stop()
        _detection_service = None
