# Annotation Guide

## Overview

MicroDetect provides a powerful annotation tool for labeling microorganisms in microscopy images. The tool is designed to make the annotation process efficient and accurate, with support for automatic suggestions based on YOLO models or computer vision techniques.

## Starting the Annotation Tool

```bash
microdetect annotate --image_dir /path/to/images --output_dir /path/to/labels
```

Additional options:

- `--model_path`: Path to a YOLOv8 model to generate suggestions
- `--classes`: Comma-separated list of class names (default: yeast,fungi,microalgae)
- `--no_cv_fallback`: Disable computer vision fallback when model is not available

## Interface Controls

### Mouse Controls

- **Left Click**: Select a bounding box
- **Left Click + Drag**: Draw a new bounding box
- **Right Click on Box**: Delete selected bounding box
- **Mouse Wheel**: Zoom in/out
- **Mouse Wheel + Ctrl**: Adjust box size

### Keyboard Controls

- **Arrow Keys**: Move selected bounding box
- **Shift + Arrow Keys**: Resize selected bounding box
- **1, 2, 3, ...**: Change class of selected box
- **S**: Save annotations
- **Z**: Undo last action
- **Y**: Redo last action
- **A**: Toggle automatic suggestions
- **N**: Go to next image
- **P**: Go to previous image
- **R**: Reset view
- **ESC**: Quit annotation tool

## Automatic Suggestions

The annotation tool can automatically suggest bounding boxes in two ways:

1. **YOLOv8 Model**: When a trained model is available, it will be used to provide highly accurate suggestions
2. **Computer Vision Fallback**: When no model is available or model detections are insufficient, advanced computer vision techniques are applied

### Computer Vision Detection

The fallback system uses sophisticated algorithms to detect different types of microorganisms:

- **Yeasts**: Detected using circle detection and blob analysis for circular/oval shapes
- **Fungi**: Detected using Gabor filters and skeleton analysis for filamentous structures
- **Microalgae**: Detected through color analysis (typically greenish) and texture features

Multiple preprocessing and segmentation methods are applied to handle various image conditions:

- Adaptive preprocessing based on image brightness and contrast
- Multiple segmentation techniques (adaptive thresholding, Otsu, K-means clustering)
- Advanced filtering to reduce false positives
- Non-Maximum Suppression to eliminate duplicate detections

## Annotation Workflow

1. Open the annotation tool with your image directory
2. Navigate through images with Next/Previous buttons
3. Use automatic suggestions or draw boxes manually
4. Adjust and refine bounding boxes as needed
5. Save annotations (automatically done when navigating between images)
6. Export annotated dataset for training

## Tips for Efficient Annotation

- Use a trained model for suggestions whenever possible
- Start with a small batch of manually annotated images, train an initial model, then use it to suggest annotations for the rest of your dataset
- Review all automatic suggestions before accepting them
- For challenging images with low contrast or unusual lighting, adjust the suggestions manually
- Save your work frequently
- Use keyboard shortcuts to speed up the annotation process

## Advanced Features

### Search and Filter

Access the search dialog to find specific images by name or annotation content.

### Statistics View

View statistics about your annotation progress, including:
- Number of images annotated
- Number of objects per class
- Average objects per image

### Backup and Recovery

The annotation tool automatically creates backups of your annotation sessions. If the application crashes, your work will be recoverable from the last backup.

## Exporting Annotations

After completing annotations, you can export them for training:

```bash
microdetect dataset --source_img_dir /path/to/images --source_label_dir /path/to/labels
```

This prepares a properly structured dataset for YOLOv8 training.

## Example

```bash
# Start annotation with a pre-trained model for suggestions
microdetect annotate --image_dir data/images --output_dir data/labels --model_path models/yolov8n.pt

# Export annotations for training
microdetect dataset --source_img_dir data/images --source_label_dir data/labels
```