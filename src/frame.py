"""
Frame module for PetLog.

This module defines the Frame class that encapsulates frame data and metadata
for consistent handling across the camera service and consumers.
"""

import numpy as np
from datetime import datetime
from typing import Any, Dict, Optional
from dataclasses import dataclass, field
from enum import Enum
import cv2


class FrameFormat(Enum):
    """Enumeration of supported frame formats."""
    
    BGR = "BGR"  # Blue-Green-Red (OpenCV default)
    RGB = "RGB"  # Red-Green-Blue
    RGBA = "RGBA"  # Red-Green-Blue-Alpha
    BGRA = "BGRA"  # Blue-Green-Red-Alpha
    GRAY = "GRAY"  # Grayscale
    YUV = "YUV"  # YUV color space
    HSV = "HSV"  # Hue-Saturation-Value
    LAB = "LAB"  # L*a*b* color space
    RGB888 = "RGB888"  # 8-bit RGB
    BGR888 = "BGR888"  # 8-bit BGR


@dataclass
class FrameMetadata:
    """Metadata associated with a camera frame."""
    
    timestamp: datetime
    frame_number: int
    width: int
    height: int
    format: FrameFormat
    quality: Optional[int] = None  # JPEG quality if applicable
    frame_rate: Optional[float] = None
    camera_config: Optional[Dict[str, Any]] = None
    processing_time: Optional[float] = None  # Time taken to capture/process
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metadata to dictionary for serialization."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "frame_number": self.frame_number,
            "width": self.width,
            "height": self.height,
            "format": self.format.value,
            "quality": self.quality,
            "frame_rate": self.frame_rate,
            "camera_config": self.camera_config,
            "processing_time": self.processing_time
        }


@dataclass
class Frame:
    """
    Frame class that encapsulates camera frame data and metadata.
    
    This class provides a structured way to pass frame information between
    the camera service and consumers (detection, streaming, etc.).
    """
    
    data: np.ndarray  # Raw frame data as numpy array
    metadata: FrameMetadata
    _cached_copies: Dict[str, Any] = field(default_factory=dict, init=False)
    
    def __post_init__(self):
        """Validate frame data after initialization."""
        if not isinstance(self.data, np.ndarray):
            raise ValueError("Frame data must be a numpy array")
        
        if len(self.data.shape) not in [2, 3]:
            raise ValueError("Frame data must be 2D (grayscale) or 3D (color) array")
    
    @property
    def shape(self) -> tuple:
        """Get the shape of the frame data."""
        return self.data.shape
    
    @property
    def width(self) -> int:
        """Get frame width."""
        return self.data.shape[1]
    
    @property
    def height(self) -> int:
        """Get frame height."""
        return self.data.shape[0]
    
    @property
    def channels(self) -> int:
        """Get number of channels (1 for grayscale, 3 for RGB)."""
        return self.data.shape[2] if len(self.data.shape) == 3 else 1
    
    @property
    def timestamp(self) -> datetime:
        """Get frame timestamp."""
        return self.metadata.timestamp
    
    @property
    def frame_number(self) -> int:
        """Get frame number."""
        return self.metadata.frame_number
    
    def copy_data(self) -> np.ndarray:
        """
        Get a copy of the frame data.
        
        This method ensures thread safety by returning a copy of the data
        rather than a reference to the original array.
        """
        return self.data.copy()
    
    def get_cached_copy(self, key: str) -> Optional[Any]:
        """Get a cached processed version of the frame."""
        return self._cached_copies.get(key)
    
    def set_cached_copy(self, key: str, value: Any) -> None:
        """Cache a processed version of the frame."""
        self._cached_copies[key] = value
    
    def to_jpeg(self, quality: int = 85) -> bytes:
        """
        Convert frame data to JPEG bytes.
        
        Args:
            quality: JPEG compression quality (1-100)
            
        Returns:
            JPEG encoded frame as bytes
        """
        cache_key = f"jpeg_{quality}"
        cached = self.get_cached_copy(cache_key)
        if cached is not None:
            return cached
        
        _, jpeg_buffer = cv2.imencode(
            ".jpg", self.data, [cv2.IMWRITE_JPEG_QUALITY, quality]
        )
        jpeg_bytes = jpeg_buffer.tobytes()
        
        # Cache the result for potential reuse
        self.set_cached_copy(cache_key, jpeg_bytes)
        return jpeg_bytes
    
    def to_png(self) -> bytes:
        """
        Convert frame data to PNG bytes.
        
        Returns:
            PNG encoded frame as bytes
        """
        cache_key = "png"
        cached = self.get_cached_copy(cache_key)
        if cached is not None:
            return cached
        
        _, png_buffer = cv2.imencode(".png", self.data)
        png_bytes = png_buffer.tobytes()
        
        # Cache the result for potential reuse
        self.set_cached_copy(cache_key, png_bytes)
        return png_bytes
    
    def resize(self, width: int, height: int) -> 'Frame':
        """
        Create a new Frame with resized data.
        
        Args:
            width: Target width
            height: Target height
            
        Returns:
            New Frame with resized data
        """
        resized_data = cv2.resize(self.data, (width, height))
        
        # Create new metadata with updated width and height
        new_metadata = FrameMetadata(
            timestamp=self.metadata.timestamp,
            frame_number=self.metadata.frame_number,
            width=width,
            height=height,
            format=self.metadata.format,
            quality=self.metadata.quality,
            frame_rate=self.metadata.frame_rate,
            camera_config=self.metadata.camera_config,
            processing_time=self.metadata.processing_time
        )
        
        return Frame(data=resized_data, metadata=new_metadata)
    
    def get_info(self) -> Dict[str, Any]:
        """Get comprehensive frame information."""
        return {
            "shape": self.shape,
            "width": self.width,
            "height": self.height,
            "channels": self.channels,
            "dtype": str(self.data.dtype),
            "size_bytes": self.data.nbytes,
            "metadata": self.metadata.to_dict()
        }
    
    def __str__(self) -> str:
        """String representation of the frame."""
        return (
            f"Frame(shape={self.shape}, "
            f"timestamp={self.metadata.timestamp.isoformat()}, "
            f"frame_number={self.metadata.frame_number}, "
            f"width={self.metadata.width}, height={self.metadata.height}))"
        )
