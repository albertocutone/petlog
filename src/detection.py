import logging
import cv2
import numpy as np
from ultralytics import YOLO
from typing import Optional, Tuple, List, Dict, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)

COCO_CLASSES = [
    'person', 'bicycle', 'car', 'motorcycle', 'airplane', 'bus', 'train',
    'truck', 'boat', 'traffic light', 'fire hydrant', 'stop sign',
    'parking meter', 'bench', 'bird', 'cat', 'dog', 'horse', 'sheep',
    'cow', 'elephant', 'bear', 'zebra', 'giraffe', 'backpack', 'umbrella',
    'handbag', 'tie', 'suitcase', 'frisbee', 'skis', 'snowboard',
    'sports ball', 'kite', 'baseball bat', 'baseball glove', 'skateboard',
    'surfboard', 'tennis racket', 'bottle', 'wine glass', 'cup', 'fork',
    'knife', 'spoon', 'bowl', 'banana', 'apple', 'sandwich', 'orange',
    'broccoli', 'carrot', 'hot dog', 'pizza', 'donut', 'cake', 'chair',
    'couch', 'potted plant', 'bed', 'dining table', 'toilet', 'tv',
    'laptop', 'mouse', 'remote', 'keyboard', 'cell phone', 'microwave',
    'oven', 'toaster', 'sink', 'refrigerator', 'book', 'clock', 'vase',
    'scissors', 'teddy bear', 'hair drier', 'toothbrush'
]

_model_cache = {}


@dataclass
class DetectionConfig:
    enabled: bool = True
    model_name: str = "yolo11n"
    confidence: float = 0.5
    iou: float = 0.45
    target_classes: Optional[List[str]] = None
    max_size: int = 416


def get_model(config: DetectionConfig) -> YOLO:
    ncnn_model_name = f"{config.model_name}_ncnn_model"
    
    if ncnn_model_name not in _model_cache:
        logger.info(f"Loading YOLO model: {config.model_name}")
        
        try:
            model = YOLO(ncnn_model_name)
            logger.info("Loaded existing NCNN model")
        except Exception:
            logger.info("NCNN model not found, creating from PyTorch model...")
            pytorch_model = YOLO(f"{config.model_name}.pt")
            logger.info("Exporting to NCNN format...")
            pytorch_model.export(format="ncnn")
            
            model = YOLO(ncnn_model_name)
            logger.info("NCNN model exported and loaded successfully")
        
        _model_cache[ncnn_model_name] = model
        logger.info(f"Model {ncnn_model_name} ready for inference")
    
    return _model_cache[ncnn_model_name]


def prediction(
    config: DetectionConfig,
    image: np.ndarray,
    display_result: bool = False
) -> Tuple[np.ndarray, List[Dict[str, Any]]]:
    try:
        model = get_model(config)
        
        original_height, original_width = image.shape[:2]
        
        if max(original_height, original_width) > config.max_size:
            scale = config.max_size / max(original_height, original_width)
            new_width = int(original_width * scale)
            new_height = int(original_height * scale)
            resized_image = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_LINEAR)
        else:
            resized_image = image
            scale = 1.0
        
        results = model(
            resized_image, 
            conf=config.confidence, 
            iou=config.iou, 
            verbose=False,
            device='cpu',
            half=False,
            augment=False,
            agnostic_nms=False,
            max_det=100
        )
        
        # Process results
        detections = []
        annotated_image = image.copy()
        
        for result in results:
            boxes = result.boxes
            if boxes is not None:
                for box in boxes:
                    # Extract detection info
                    class_id = int(box.cls[0])
                    conf = float(box.conf[0])
                    bbox = box.xyxy[0].cpu().numpy()  # [x1, y1, x2, y2]
                    
                    # Scale bounding box back to original image size if we resized
                    if scale != 1.0:
                        bbox = bbox / scale
                    
                    # Get class name
                    class_name = COCO_CLASSES[class_id] if class_id < len(COCO_CLASSES) else f"class_{class_id}"
                    
                    # Filter by target classes if specified
                    if config.target_classes and class_name not in config.target_classes:
                        continue
                    
                    # Store detection info
                    detection = {
                        'class': class_id,
                        'confidence': conf,
                        'bbox': bbox.tolist(),
                        'class_name': class_name
                    }
                    detections.append(detection)
                    
                    # Draw bounding box and label on original image
                    x1, y1, x2, y2 = bbox.astype(int)
                    
                    # Choose color based on class (person = red, others = green)
                    color = (0, 0, 255) if class_name == 'person' else (0, 255, 0)
                    
                    # Draw bounding box
                    cv2.rectangle(annotated_image, (x1, y1), (x2, y2), color, 2)
                    
                    # Draw label background
                    label = f"{class_name}: {conf:.2f}"
                    label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)[0]
                    cv2.rectangle(
                        annotated_image,
                        (x1, y1 - label_size[1] - 10),
                        (x1 + label_size[0], y1),
                        color,
                        -1
                    )
                    
                    # Draw label text
                    cv2.putText(
                        annotated_image,
                        label,
                        (x1, y1 - 5),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.5,
                        (255, 255, 255),
                        2
                    )
        
        # Log detections
        if detections:
            class_counts = {}
            for det in detections:
                class_name = det['class_name']
                class_counts[class_name] = class_counts.get(class_name, 0) + 1
            
            logger.info(f"Detected objects: {dict(class_counts)}")
            
            # Special logging for person detection
            person_count = class_counts.get('person', 0)
            if person_count > 0:
                logger.info(f"PERSON DETECTED! Found {person_count} person(s)")
        
        # Display result if requested (for debugging)
        if display_result:
            cv2.imshow('YOLO Detection', annotated_image)
            cv2.waitKey(1)
        
        return annotated_image, detections
        
    except Exception as e:
        logger.error(f"Error during prediction: {e}")
        return image, []


def apply_detection_to_frame(
    frame: np.ndarray,
    model_type: str = 'yolov8n.pt',
    confidence: float = 0.5,
    target_classes: Optional[List[str]] = None
) -> np.ndarray:
    """
    Apply object detection to a camera frame and return annotated frame.
    This function is designed to integrate with the camera streaming system.
    
    Args:
        frame: Camera frame (BGR format)
        model_type: YOLO model to use
        confidence: Detection confidence threshold
        target_classes: Classes to detect (None for all)
    
    Returns:
        Annotated frame with bounding boxes
    """
    try:
        annotated_frame, detections = prediction(
            model_type=model_type,
            image=frame,
            confidence=confidence,
            target_classes=target_classes
        )
        return annotated_frame
    except Exception as e:
        logger.error(f"Error applying detection to frame: {e}")
        return frame


# Example usage functions
def main():
    """Example usage of the detection module."""
    import time
    
    # Test with a sample image (you would replace this with actual camera frame)
    # For testing purposes, create a dummy image
    test_image = np.zeros((480, 640, 3), dtype=np.uint8)
    cv2.putText(test_image, "Test Image", (50, 240), cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 3)
    
    # Run detection
    start_time = time.time()
    annotated_image, detections = prediction(
        model_type='yolov8n.pt',
        image=test_image,
        confidence=0.5,
        display_result=True
    )
    
    inference_time = time.time() - start_time
    logger.info(f"Inference completed in {inference_time:.3f} seconds")
    logger.info(f"Found {len(detections)} objects")
    
    # Test all object detection
    annotated_image_all, all_detections = prediction(
        model_type='yolov8n.pt',
        image=test_image,
        confidence=0.5
    )
    
    logger.info(f"Found {len(all_detections)} objects total")


if __name__ == "__main__":
    main()
