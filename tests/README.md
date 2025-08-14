# Hardware Tests

This directory contains hardware validation tests for the petlog project.

## Camera Hardware Test

### Purpose
The `test_camera_hardware.py` script validates that the Raspberry Pi Camera Module V2 is properly connected and functioning correctly.

### What it tests
1. **Library imports** - Verifies picamera2 and OpenCV are installed
2. **Camera initialization** - Tests camera connection and startup
3. **Image capture** - Captures a test image at 1080p resolution
4. **Video recording** - Records a 5-second test video at 720p
5. **Media validation** - Validates captured files using OpenCV

### Usage

#### On Raspberry Pi
```bash
# Navigate to project root
cd /path/to/petlog

# Activate virtual environment
source venv/bin/activate

# Run the hardware test
python tests/HW/test_camera.py
```

#### Prerequisites
- Raspberry Pi with Camera Module V2 connected
- Camera interface enabled in raspi-config
- Required Python packages installed:
  ```bash
  pip install picamera2 opencv-python
  ```

### Expected Output
```
=== Raspberry Pi Camera Hardware Validation ===
✓ Camera libraries imported successfully
✓ Camera object created successfully
✓ Camera started successfully
Capturing test image...
✓ Image captured successfully: tests/output/test_image.jpg
Recording 5s test video...
✓ Video recorded successfully: tests/output/test_video.h264
✓ Image validation successful: 1920x1080, 3 channels
✓ Video validation successful:
  Frames: 150
  FPS: 30.00
  Duration: 5.00 seconds

=== Test Results Summary ===
Image capture: ✓ PASS
Video recording: ✓ PASS
Image validation: ✓ PASS
Video validation: ✓ PASS

🎉 All camera hardware tests PASSED!
Camera module is working correctly and ready for use.
```

### Test Output
Test files are saved to `tests/output/`:
- `test_image.jpg` - Test image capture (1920x1080)
- `test_video.h264` - Test video recording (1280x720, 5 seconds)

### Troubleshooting

#### Common Issues
1. **ImportError: No module named 'picamera2'**
   ```bash
   pip install picamera2
   ```

2. **Camera not detected**
   - Check camera cable connection
   - Enable camera interface: `sudo raspi-config` → Interface Options → Camera
   - Reboot after enabling camera

3. **Permission denied**
   - Ensure user is in `video` group: `sudo usermod -a -G video $USER`
   - Log out and back in

4. **Camera already in use**
   - Close other applications using the camera
   - Reboot if necessary

### Integration with CI/CD
This test can be integrated into automated deployment pipelines to validate hardware setup before deploying the main application.

### Exit Codes
- `0` - All tests passed
- `1` - One or more tests failed

Use the exit code to determine test success in automated scripts:
```bash
python tests/HW/test_camera.py
if [ $? -eq 0 ]; then
    echo "Hardware validation successful"
else
    echo "Hardware validation failed"
    exit 1
fi
```
