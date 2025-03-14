# Model Deployment Guide

This guide explains how to deploy your trained YOLOv8 models for microorganism detection in various environments, from local workstations to production systems.

## Overview

After successfully training a model, the next step is deploying it for practical use. MicroDetect provides tools and utilities to make model deployment straightforward across different platforms and environments, allowing you to integrate microorganism detection capabilities into your research or production workflows.

## Deployment Options

MicroDetect supports several deployment options for your trained models:

| Deployment Type | Use Case | Requirements |
|-----------------|----------|--------------|
| Local Python | Research and development | Python environment with dependencies |
| REST API | Network-accessible inference service | Server with Python and web frameworks |
| Containerized | Portable, isolated deployment | Docker |
| Edge Devices | On-site, low-resource deployment | Compatible edge device (Jetson, Raspberry Pi, etc.) |
| Mobile | Field applications | Mobile development tools and libraries |
| Web Browser | Interactive web applications | JavaScript and compatible model formats |

## Model Export

### Exporting to Different Formats

Before deployment, you'll need to export your model to the appropriate format:

```bash
microdetect export --model_path runs/train/yolov8_s_custom/weights/best.pt --format onnx
```

Supported export formats:

| Format | Description | Best For |
|--------|-------------|----------|
| ONNX | Open Neural Network Exchange format | Cross-platform deployment, integration with various frameworks |
| TorchScript | PyTorch's serialization format | PyTorch production environments |
| TensorRT | NVIDIA's optimized runtime | NVIDIA GPU deployment with maximum performance |
| CoreML | Apple's machine learning framework | iOS and macOS applications |
| TFLite | TensorFlow Lite format | Mobile and edge devices |
| OpenVINO | Intel's inference optimization toolkit | Intel CPU/GPU deployment |
| PaddlePaddle | Baidu's deep learning platform | Integration with PaddlePaddle ecosystem |

### Command Line Options

| Parameter | Description | Default |
|-----------|-------------|---------|
| `--model_path` | Path to the trained model | |
| `--format` | Export format (onnx, torchscript, tflite, etc.) | `onnx` |
| `--img_size` | Image size for the exported model | Model's training size |
| `--batch_size` | Batch size for the exported model | 1 |
| `--half` | Export in FP16 precision | `False` |
| `--dynamic` | Export with dynamic axes | `False` |
| `--simplify` | Simplify the ONNX model | `True` |
| `--output_dir` | Directory to save the exported model | Same as model_path directory |

## Local Python Deployment

### Basic Inference

The simplest deployment method is direct inference in Python:

```python
from microdetect.inference import MicroDetector

# Initialize detector with your trained model
detector = MicroDetector(model_path="runs/train/yolov8_s_custom/weights/best.pt")

# Run detection on a single image
results = detector.detect("path/to/image.jpg")

# Process and visualize results
detector.visualize_results(results, output_path="output.jpg")

# Get detection data
detections = detector.process_results(results)
for detection in detections:
    print(f"Class: {detection['class_name']}, Confidence: {detection['confidence']:.2f}")
    print(f"Bounding Box: {detection['bbox']}")
```

### Batch Processing

For processing multiple images:

```python
import glob
from microdetect.inference import MicroDetector

detector = MicroDetector(model_path="runs/train/yolov8_s_custom/weights/best.pt")

# Process all images in a directory
image_paths = glob.glob("data/test_images/*.jpg")
batch_results = detector.batch_detect(image_paths)

# Save results to a directory
detector.batch_visualize(
    image_paths=image_paths,
    results=batch_results,
    output_dir="output/detections"
)

# Export detection data to CSV
detector.export_detections(batch_results, "detections.csv")
```

### Performance Optimization

Optimize inference for your specific hardware:

```python
from microdetect.inference import MicroDetector

# GPU acceleration with FP16 precision for faster inference
detector = MicroDetector(
    model_path="runs/train/yolov8_s_custom/weights/best.pt",
    device="cuda:0",
    half=True,
    batch_size=4
)

# Set confidence threshold and NMS parameters for better results
detector.conf_threshold = 0.25
detector.iou_threshold = 0.45
```

## REST API Deployment

MicroDetect includes a ready-to-use REST API for remote inference:

```bash
# Start API server
microdetect serve --model_path runs/train/yolov8_s_custom/weights/best.pt --port 8000
```

### API Endpoints

Once the server is running, the following endpoints are available:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/detect` | POST | Submit an image for detection |
| `/batch_detect` | POST | Submit multiple images for detection |
| `/health` | GET | Check server health |
| `/info` | GET | Get model information |

### Example Client

```python
import requests
import base64
import json
import cv2
import numpy as np

def encode_image(image_path):
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

# Prepare the request
url = "http://localhost:8000/detect"
payload = {
    "image": encode_image("path/to/image.jpg"),
    "conf_threshold": 0.25,
    "save_results": True
}

# Send request
response = requests.post(url, json=payload)
detections = response.json()

# Process results
print(f"Detected {len(detections['objects'])} microorganisms")
for obj in detections['objects']:
    print(f"Class: {obj['class_name']}, Confidence: {obj['confidence']:.2f}")
    
# If save_results was True, download the visualization
if "result_image" in detections:
    img_data = base64.b64decode(detections["result_image"])
    with open("result.jpg", "wb") as f:
        f.write(img_data)
```

### Docker Deployment

For containerized API deployment:

```bash
# Build Docker image
microdetect build_docker --model_path runs/train/yolov8_s_custom/weights/best.pt --tag microdetect:latest

# Run container
docker run -p 8000:8000 microdetect:latest
```

## Edge Device Deployment

### Raspberry Pi Deployment

```bash
# Export model optimized for Raspberry Pi
microdetect export --model_path runs/train/yolov8_s_custom/weights/best.pt --format tflite --quantize int8 --output_dir rpi_deploy

# Copy files to Raspberry Pi
scp -r rpi_deploy pi@raspberry:/home/pi/microdetect

# On the Raspberry Pi
pip install microdetect-edge
microdetect-edge run --model_path /home/pi/microdetect/model_int8.tflite
```

### NVIDIA Jetson Deployment

```bash
# Export model optimized for Jetson
microdetect export --model_path runs/train/yolov8_s_custom/weights/best.pt --format tensorrt --device cuda:0 --output_dir jetson_deploy

# Install on Jetson
# Note: Ensure you have the right JetPack version installed
pip install microdetect-edge
microdetect-edge run --model_path jetson_deploy/model_tensorrt.engine --device cuda:0
```

## Web Browser Deployment

MicroDetect provides utilities for deploying models to web browsers using ONNX.js or TensorFlow.js:

```bash
# Export for web deployment
microdetect export_web --model_path runs/train/yolov8_s_custom/weights/best.pt --framework tfjs --output_dir web_deploy

# This creates a complete deployment package with JavaScript inference code
# Serve the directory with any web server
python -m http.server --directory web_deploy
```

## Integration with Existing Systems

### Python Libraries

```python
# Integration with OpenCV for video processing
import cv2
from microdetect.inference import MicroDetector

detector = MicroDetector(model_path="runs/train/yolov8_s_custom/weights/best.pt")

cap = cv2.VideoCapture(0)  # Open webcam
while True:
    ret, frame = cap.read()
    if not ret:
        break
        
    # Detect microorganisms
    results = detector.detect(frame)
    
    # Draw detections
    annotated_frame = detector.draw_results(frame, results)
    
    # Display
    cv2.imshow("MicroDetect", annotated_frame)
    if cv2.waitKey(1) == ord('q'):
        break
        
cap.release()
cv2.destroyAllWindows()
```

### Integration with Laboratory Information Management Systems (LIMS)

```python
from microdetect.inference import MicroDetector
from microdetect.integrations import LIMSConnector

# Initialize detector
detector = MicroDetector(model_path="runs/train/yolov8_s_custom/weights/best.pt")

# Configure LIMS connector (adjust based on your LIMS API)
lims = LIMSConnector(
    api_url="https://your-lims-system.com/api",
    api_key="your-api-key"
)

# Process sample and update LIMS
def process_sample(sample_id, image_path):
    # Detect microorganisms
    results = detector.detect(image_path)
    detections = detector.process_results(results)
    
    # Prepare data for LIMS
    counts = {}
    for det in detections:
        class_name = det['class_name']
        counts[class_name] = counts.get(class_name, 0) + 1
    
    # Update LIMS
    lims.update_sample(
        sample_id=sample_id,
        detection_results=counts,
        image_path=image_path
    )
    
    return counts

# Example usage
sample_counts = process_sample("S12345", "path/to/sample/image.jpg")
print(f"Sample analysis complete: {sample_counts}")
```

## Performance Monitoring and Optimization

### Benchmarking Deployment

```bash
microdetect benchmark --model_path runs/train/yolov8_s_custom/weights/best.pt --batch_sizes 1,4,8 --img_sizes 640,1280
```

This provides detailed metrics on:
- Inference time per image
- Memory usage
- CPU/GPU utilization
- Throughput (images per second)

### Real-time Monitoring

For production deployments:

```python
from microdetect.inference import MicroDetector
from microdetect.monitoring import PerformanceMonitor

detector = MicroDetector(model_path="runs/train/yolov8_s_custom/weights/best.pt")
monitor = PerformanceMonitor(log_dir="logs/performance")

# Monitor performance during inference
with monitor.track_inference():
    results = detector.detect("path/to/image.jpg")

# Get performance metrics
metrics = monitor.get_metrics()
print(f"Inference time: {metrics['inference_time_ms']:.2f} ms")
print(f"Memory usage: {metrics['memory_mb']:.2f} MB")
```

## Troubleshooting

### Common Deployment Issues

| Issue | Solution |
|-------|----------|
| Slow inference | Try lower resolution, batch processing, or FP16 precision |
| Out of memory errors | Reduce batch size or export to a more optimized format |
| CUDA errors | Ensure CUDA drivers match the version used for export |
| Model format compatibility | Check target environment supports the exported format |
| Different results after export | Validate exported model against original with test images |

### Deployment Checklist

Before deploying to production:

1. Benchmark the model on target hardware
2. Validate model accuracy with test dataset
3. Set appropriate confidence thresholds
4. Implement error handling and logging
5. Set up monitoring for performance issues
6. Create backup inference paths for critical systems

## Next Steps

After successfully deploying your model:

- [Model Monitoring Guide](model_monitoring.md) - Monitor model performance in production
- [Model Updating Guide](model_updating.md) - Update deployed models without service interruption
- [Systems Integration Guide](systems_integration.md) - Integrate with other laboratory systems