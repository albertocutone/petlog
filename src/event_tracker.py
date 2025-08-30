"""
Event tracking module for PetLog.

This module handles simple object tracking and event detection for ENTERING_AREA and LEAVING_AREA events.
It maintains a simple list of detected object classes and logs events when objects appear or disappear.
"""

import logging
import time
from datetime import datetime
from typing import Dict, List, Any, Optional, Set

from .database import get_db
from .models import EventType

logger = logging.getLogger(__name__)


class EventTracker:
    """Simple tracker that detects when objects enter or leave the area."""
    
    def __init__(self, timeout_seconds: float = 3.0):
        """
        Initialize the event tracker.
        
        Args:
            timeout_seconds: Time after which an object is considered to have left the area
        """
        self.timeout_seconds = timeout_seconds
        
        # Simple tracking: class_name -> last_seen_time
        self.current_objects: Dict[str, float] = {}
        self.db = get_db()
        
        logger.info(f"EventTracker initialized with timeout={timeout_seconds}s")
    
    def _log_event(self, event_type: EventType, class_name: str, confidence: float) -> int:
        """
        Log an event to the database.
        
        Args:
            event_type: Type of event (ENTERING_AREA or LEAVING_AREA)
            class_name: The class of object involved in the event
            confidence: Detection confidence
            
        Returns:
            Event ID from database
        """
        # For now, we don't have pet_id identification, so we use None
        # Pass class_name directly, no metadata needed
        event_id = self.db.log_event(
            pet_id=None,
            event_type=event_type.value,
            class_name=class_name,
            confidence=confidence
        )
        
        logger.info(f"Logged {event_type.value} event (ID: {event_id}) for {class_name} "
                   f"(confidence: {confidence:.2f})")
        
        return event_id
    
    def process_detections(self, detections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Process new detections and generate events.
        
        Args:
            detections: List of detection dictionaries from YOLO
            
        Returns:
            List of events that were generated
        """
        current_time = time.time()
        events_generated = []
        
        # Get unique classes detected in this frame
        detected_classes = set()
        class_confidences = {}
        
        for detection in detections:
            class_name = detection['class_name']
            detected_classes.add(class_name)
            # Keep the highest confidence for each class
            if class_name not in class_confidences or detection['confidence'] > class_confidences[class_name]:
                class_confidences[class_name] = detection['confidence']
        
        for class_name in detected_classes:
            if class_name not in self.current_objects:
                confidence = class_confidences[class_name]
                event_id = self._log_event(EventType.ENTERING_AREA, class_name, confidence)
                
                events_generated.append({
                    'event_id': event_id,
                    'event_type': EventType.ENTERING_AREA.value,
                    'class_name': class_name,
                    'confidence': confidence,
                    'timestamp': datetime.now().isoformat()
                })
                
                logger.info(f"ENTERING_AREA: {class_name} detected with confidence {confidence:.2f}")
            
            # Update last seen time for this class
            self.current_objects[class_name] = current_time
        
        # Check for objects that may have left the area
        leaving_events = self._check_for_leaving_objects(current_time, detected_classes)
        events_generated.extend(leaving_events)
        
        return events_generated
    
    def _check_for_leaving_objects(self, current_time: float, 
                                  detected_classes: Optional[Set[str]] = None) -> List[Dict[str, Any]]:
        """
        Check for objects that have left the area (not seen for timeout_seconds).
        
        Args:
            current_time: Current timestamp
            detected_classes: Set of classes that were detected in current frame
            
        Returns:
            List of LEAVING_AREA events
        """
        if detected_classes is None:
            detected_classes = set()
        
        events_generated = []
        classes_to_remove = []
        
        for class_name, last_seen in self.current_objects.items():
            # Skip objects that were just seen
            if class_name in detected_classes:
                continue
            
            # Check if object has timed out
            time_since_last_seen = current_time - last_seen
            if time_since_last_seen >= self.timeout_seconds:
                # Object has left the area - log LEAVING_AREA event
                # Use a default confidence since we don't have the last detection confidence
                confidence = 0.8  # Default confidence for leaving events
                event_id = self._log_event(EventType.LEAVING_AREA, class_name, confidence)
                
                events_generated.append({
                    'event_id': event_id,
                    'event_type': EventType.LEAVING_AREA.value,
                    'class_name': class_name,
                    'confidence': confidence,
                    'timestamp': datetime.now().isoformat()
                })
                
                logger.info(f"LEAVING_AREA: {class_name} left area after {time_since_last_seen:.1f}s timeout")
                
                classes_to_remove.append(class_name)
        
        # Remove objects that have left
        for class_name in classes_to_remove:
            del self.current_objects[class_name]
        
        return events_generated

# Global event tracker instance
event_tracker = EventTracker()

def get_event_tracker() -> EventTracker:
    """Get the global event tracker instance."""
    return event_tracker
