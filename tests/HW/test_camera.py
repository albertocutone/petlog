#!/usr/bin/env python3
"""
Hardware validation script for Raspberry Pi Camera Module V2.

This script tests the camera module functionality by:
1. Initializing the camera
2. Capturing a test image
3. Recording a short video clip
4. Validating the captured media

Usage:
    python tests/test_camera_hardware.py

Requirements:
    - Raspberry Pi with Camera Module V2 connected
    - picamera2 library installed
    - OpenCV installed
"""

import logging
import sys
import time
from pathlib import Path
from typing import Optional, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Test output directory
TEST_OUTPUT_DIR = Path("tests/output")
TEST_IMAGE_PATH = TEST_OUTPUT_DIR / "test_image.jpg"
TEST_VIDEO_PATH = TEST_OUTPUT_DIR / "test_video.h264"

# Test configuration constants
TEST_VIDEO_DURATION_SECONDS = 1
IMAGE_RESOLUTION = (1920, 1080)  # 1080p
VIDEO_RESOLUTION = (1280, 720)  # 720p


def setup_test_environment() -> None:
    """Create test output directory if it doesn't exist."""
    TEST_OUTPUT_DIR.mkdir(exist_ok=True)
    logger.info(f"Test output directory: {TEST_OUTPUT_DIR.absolute()}")


def test_camera_import() -> bool:
    """Test if camera libraries can be imported."""
    try:
        import cv2
        from picamera2 import Picamera2

        logger.info("✓ Camera libraries imported successfully")
        return True
    except ImportError as e:
        logger.error(f"✗ Failed to import camera libraries: {e}")
        return False


def test_camera_initialization() -> Optional[object]:
    """Test camera initialization and return camera object if successful."""
    try:
        from picamera2 import Picamera2

        camera = Picamera2()
        logger.info("✓ Camera object created successfully")

        # Configure camera for still capture
        camera_config = camera.create_still_configuration(
            main={"size": IMAGE_RESOLUTION}
        )
        camera.configure(camera_config)

        camera.start()
        logger.info("✓ Camera started successfully")

        # Allow camera to warm up
        time.sleep(2)

        return camera

    except Exception as e:
        logger.error(f"✗ Camera initialization failed: {e}")
        logger.error("Check camera connection and enable camera interface")
        return None


def test_image_capture(camera: object) -> bool:
    """Test capturing a still image."""
    try:
        logger.info("Capturing test image...")
        camera.capture_file(str(TEST_IMAGE_PATH))

        if TEST_IMAGE_PATH.exists():
            file_size = TEST_IMAGE_PATH.stat().st_size
            logger.info(f"✓ Image captured successfully: {TEST_IMAGE_PATH}")
            logger.info(f"  File size: {file_size:,} bytes")
            return True
        else:
            logger.error("✗ Image file was not created")
            return False

    except Exception as e:
        logger.error(f"✗ Image capture failed: {e}")
        return False


def test_video_recording(camera: object) -> bool:
    """Test recording a short video clip."""
    try:
        from picamera2.encoders import H264Encoder
        from picamera2.outputs import FileOutput

        logger.info(f"Recording {TEST_VIDEO_DURATION_SECONDS}s test video...")

        # Reconfigure camera for video recording
        video_config = camera.create_video_configuration(
            main={"size": VIDEO_RESOLUTION}
        )
        camera.configure(video_config)

        # Start camera with new configuration
        camera.start()
        logger.info("Camera restarted for video recording")

        # Set up encoder and output
        encoder = H264Encoder(bitrate=10000000)  # 10Mbps
        output = FileOutput(str(TEST_VIDEO_PATH))

        # Start recording
        camera.start_recording(encoder, output)
        time.sleep(TEST_VIDEO_DURATION_SECONDS)
        camera.stop_recording()

        if TEST_VIDEO_PATH.exists():
            file_size = TEST_VIDEO_PATH.stat().st_size
            logger.info(f"✓ Video recorded successfully: {TEST_VIDEO_PATH}")
            logger.info(f"  File size: {file_size:,} bytes")
            logger.info(f"  Duration: {TEST_VIDEO_DURATION_SECONDS} seconds")
            return True
        else:
            logger.error("✗ Video file was not created")
            return False

    except Exception as e:
        logger.error(f"✗ Video recording failed: {e}")
        return False


def validate_captured_media() -> Tuple[bool, bool]:
    """Validate the captured image and video using OpenCV."""
    image_valid = False
    video_valid = False

    try:
        import cv2

        # Validate image
        if TEST_IMAGE_PATH.exists():
            image = cv2.imread(str(TEST_IMAGE_PATH))
            if image is not None:
                height, width, channels = image.shape
                logger.info(
                    f"✓ Image validation successful: {width}x{height}, {channels} channels"
                )
                image_valid = True
            else:
                logger.error("✗ Image validation failed: Could not read image")

        # Validate video
        if TEST_VIDEO_PATH.exists():
            cap = cv2.VideoCapture(str(TEST_VIDEO_PATH))
            if cap.isOpened():
                frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                fps = cap.get(cv2.CAP_PROP_FPS)
                duration = frame_count / fps if fps > 0 else 0

                logger.info(f"✓ Video validation successful:")
                logger.info(f"  Frames: {frame_count}")
                logger.info(f"  FPS: {fps:.2f}")
                logger.info(f"  Duration: {duration:.2f} seconds")
                video_valid = True
                cap.release()
            else:
                logger.error("✗ Video validation failed: Could not open video")

    except Exception as e:
        logger.error(f"✗ Media validation failed: {e}")

    return image_valid, video_valid


def cleanup_camera(camera: Optional[object]) -> None:
    """Safely cleanup camera resources."""
    if camera is not None:
        try:
            camera.stop()
            camera.close()
            logger.info("✓ Camera resources cleaned up")
        except Exception as e:
            logger.warning(f"Camera cleanup warning: {e}")


def main() -> int:
    """Main test execution function."""
    logger.info("=== Raspberry Pi Camera Hardware Validation ===")

    # Setup test environment
    setup_test_environment()

    # Test 1: Import libraries
    if not test_camera_import():
        return 1

    # Test 2: Initialize camera
    camera = test_camera_initialization()
    if camera is None:
        return 1

    try:
        # Test 3: Capture image
        image_success = test_image_capture(camera)

        camera.stop()
        logger.info("Camera stopped")

        # Test 4: Record video
        video_success = test_video_recording(camera)

        # Test 5: Validate captured media
        image_valid, video_valid = validate_captured_media()

        # Summary
        logger.info("\n=== Test Results Summary ===")
        logger.info(f"Image capture: {'✓ PASS' if image_success else '✗ FAIL'}")
        logger.info(f"Video recording: {'✓ PASS' if video_success else '✗ FAIL'}")
        logger.info(f"Image validation: {'✓ PASS' if image_valid else '✗ FAIL'}")
        logger.info(f"Video validation: {'✓ PASS' if video_valid else '✗ FAIL'}")

        all_tests_passed = all([image_success, video_success, image_valid, video_valid])

        if all_tests_passed:
            logger.info("\n🎉 All camera hardware tests PASSED!")
            logger.info("Camera module is working correctly and ready for use.")
            return 0
        else:
            logger.error("\n❌ Some camera hardware tests FAILED!")
            logger.error("Check camera connection and system configuration.")
            return 1

    finally:
        cleanup_camera(camera)


if __name__ == "__main__":
    sys.exit(main())
