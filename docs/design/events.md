# Pet Camera Event Detection on Raspberry Pi 4

## Overview

This guide explains how to set up a system on Raspberry Pi 4 to detect when your specific cat enters or leaves the camera scene, using a custom-trained YOLOv5 model in PyTorch. It covers data collection, labeling, training, deployment, and future directions.

---

## 1. Local Recognition: Steps and Technologies

### **A. Data Collection**

- **Capture images** of your cat in various poses, lighting, and backgrounds.
- Aim for at least 100–200 images for a basic model (more is better).
- Include some images without your cat for negative samples.

### **B. Data Labeling**

- Use [LabelImg](https://github.com/tzutalin/labelImg) (cross-platform, easy to use) or [Roboflow](https://roboflow.com/) (web-based, free tier).
- **Label each image** with a bounding box around your cat.
    - Save labels in YOLO format (one `.txt` file per image, with lines like: `0 x_center y_center width height` in normalized coordinates).
    - Use class `0` for your cat (if only one cat).

### **C. Organize Dataset**

- Structure your dataset as follows:
    ```
    dataset/
      images/
        train/
        val/
      labels/
        train/
        val/
    ```
- Split your data (e.g., 80% train, 20% val).

### **D. Prepare YOLOv5 Environment (PyTorch)**

- Clone YOLOv5 repo and install dependencies:
    ```bash
    git clone https://github.com/ultralytics/yolov5.git
    cd yolov5
    pip install -r requirements.txt
    ```

### **E. Create a Custom Data Config File**

- Example `cat.yaml`:
    ```yaml
    train: /path/to/dataset/images/train
    val: /path/to/dataset/images/val

    nc: 1
    names: ['my_cat']
    ```

### **F. Train YOLOv5 Model**

- Run training (replace paths as needed):
    ```bash
    python train.py --img 640 --batch 16 --epochs 50 --data cat.yaml --weights yolov5s.pt --cache
    ```
- Monitor training progress in the terminal or with TensorBoard.

### **G. Export the Trained Model**

- The best model will be saved as `runs/train/exp*/weights/best.pt`.

### **H. Deploy on Raspberry Pi 4**

- Copy `best.pt` to your Pi.
- Install PyTorch, OpenCV, and FastAPI on the Pi:
    ```bash
    pip install torch torchvision yolov5 fastapi uvicorn opencv-python
    ```
- Use the following sample FastAPI endpoint for inference:

    ```python
    from fastapi import FastAPI
    import torch
    import cv2

    app = FastAPI()
    model = torch.hub.load('ultralytics/yolov5', 'custom', path='best.pt', force_reload=True)
    last_seen = False

    @app.get("/detect")
    def detect_cat():
        global last_seen
        cap = cv2.VideoCapture(0)
        ret, frame = cap.read()
        cap.release()
        results = model(frame)
        detected = any([x for x in results.xyxy[0] if int(x[-1]) == 0])  # class 0 = your cat
        event = None
        if detected and not last_seen:
            event = "ENTERING_AREA"
        elif not detected and last_seen:
            event = "LEAVING_AREA"
        last_seen = detected
        return {"cat_detected": detected, "event": event}
    ```

- Test and tune detection logic as needed.

---

## 2. Limitations and Future Directions

### **A. Limitations of Local Recognition**

- **Model complexity:** Only lightweight models are practical on the Pi.
- **Accuracy:** May be affected by lighting, occlusion, or changes in your cat’s appearance.
- **Scalability:** Adding more pets or complex behaviors increases data and compute needs.

### **B. Hybrid and Offloading Approaches**

- For more complex event recognition (e.g., activity detection, multiple pets), consider a **hybrid approach**:
    - The Pi detects entry/exit and records video.
    - Video is sent to a more powerful server for advanced analysis (e.g., using Vision-Language Models like CLIP or DINOv2).
    - This enables zero-shot or prompt-based event detection, but requires more compute and introduces network dependency.

---

## References

- [YOLOv5 Documentation](https://docs.ultralytics.com/)
- [LabelImg](https://github.com/tzutalin/labelImg)
- [Roboflow](https://roboflow.com/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [PyTorch](https://pytorch.org/)

---

**Summary:**
- Use YOLOv5 (PyTorch) for custom, on-device cat detection.
- Label your own data for best results.
- For advanced features, consider hybrid or server-based approaches in the future.
