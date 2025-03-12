# Visualization and Annotation Guide

This guide explains how to use MicroDetect's tools for annotating microorganism images and visualizing annotations.

## Table of Contents
- [Introduction](#introduction)
- [Annotation Tool](#annotation-tool)
  - [Starting the Annotation Tool](#starting-the-annotation-tool)
  - [Interface Overview](#interface-overview)
  - [Annotation Workflow](#annotation-workflow)
  - [Keyboard Shortcuts](#keyboard-shortcuts)
  - [Auto-save and Progress Tracking](#auto-save-and-progress-tracking)
- [Visualization Tool](#visualization-tool)
  - [Visualizing Single Images](#visualizing-single-images)
  - [Batch Visualization](#batch-visualization)
  - [Filtering by Class](#filtering-by-class)
  - [Customizing Visual Output](#customizing-visual-output)
- [Managing Annotation Data](#managing-annotation-data)
  - [YOLO Format](#yolo-format)
  - [Converting to Other Formats](#converting-to-other-formats)
  - [Backing Up Annotations](#backing-up-annotations)
- [Best Practices](#best-practices)
  - [Annotation Consistency](#annotation-consistency)
  - [Handling Difficult Cases](#handling-difficult-cases)
  - [Quality Control](#quality-control)
- [Troubleshooting](#troubleshooting)

## Introduction

MicroDetect provides specialized tools for annotating microorganisms in microscopy images and visualizing these annotations. This process is crucial for:

1. Creating training datasets for machine learning models
2. Validating detection results
3. Analyzing the distribution of microorganisms

## Annotation Tool

### Starting the Annotation Tool

To start the annotation tool, use the following command:

```bash
microdetect annotate --image_dir path/to/images --output_dir path/to/labels
```

Required parameters:
- `--image_dir`: Directory containing the images to annotate
- `--output_dir`: Directory where annotation files will be saved

Optional parameters:
- `--classes`: Comma-separated list of class names (default: from config.yaml)
- `--resume`: Resume from last annotated image
- `--auto_save`: Enable auto-saving (default: true)
- `--auto_save_interval`: Time between auto-saves in seconds (default: 300)

### Interface Overview

The annotation interface includes:

1. **Main Image Canvas**: Displays the current image for annotation
2. **Navigation Panel**: Controls for moving between images
3. **Class Selection**: Dropdown to select the microorganism class
4. **Tool Panel**: Tools for annotation (Rectangle, Zoom, Pan)
5. **Status Bar**: Shows current image name, progress, and status

### Annotation Workflow

1. **Load Image**: The tool loads an image from the specified directory
2. **Select Class**: Choose the appropriate microorganism class from the dropdown
3. **Draw Bounding Box**: Click and drag to create a bounding box around the microorganism
4. **Adjust Box**: Fine-tune the position and size of the box if needed
5. **Add More Objects**: Repeat steps 2-4 for additional microorganisms
6. **Save Annotations**: Annotations are automatically saved or press 'S' to save manually
7. **Navigate**: Use navigation buttons or keyboard shortcuts to move to the next/previous image

### Keyboard Shortcuts

The annotation tool supports the following keyboard shortcuts:

| Key | Function |
|-----|----------|
| A | Previous image |
| D | Next image |
| S | Save current annotations |
| Z | Undo last annotation |
| C | Change class (cycles through classes) |
| R | Reset zoom and pan |
| E | Toggle between rectangle and move tools |
| Del | Delete selected annotation |
| ESC | Deselect all annotations |
| Q | Quit annotation tool |

### Auto-save and Progress Tracking

The annotation tool automatically saves your work to prevent data loss:

- Annotations are saved in YOLO format (.txt files) in the output directory
- Progress is tracked in a `.annotation_progress.json` file
- When restarting the tool with the same directories, you can resume where you left off
- A backup of previous annotation versions is maintained in case of errors

## Visualization Tool

### Visualizing Single Images

To visualize annotations for a single image interactively:

```bash
microdetect visualize --image_dir path/to/images --label_dir path/to/labels
```

This opens a window showing the image with overlaid annotations.

### Batch Visualization

To generate annotated images for an entire directory:

```bash
microdetect visualize --image_dir path/to/images --label_dir path/to/labels --output_dir path/to/output
```

This creates a copy of each image with annotations drawn on it and saves them to the output directory.

### Filtering by Class

To visualize only specific classes:

```bash
microdetect visualize --image_dir path/to/images --label_dir path/to/labels --filter_classes 0,1
```

This shows only annotations for classes with IDs 0 and 1.

### Customizing Visual Output

You can customize the visualization in `config.yaml`:

```yaml
annotation:
  box_thickness: 2                # Box thickness for visualization
  text_size: 0.5                  # Text size for class labels
  
color_map:
  "0": [0, 255, 0]                # RGB color for class 0
  "1": [0, 0, 255]                # RGB color for class 1
  "2": [255, 0, 0]                # RGB color for class 2
```

## Managing Annotation Data

### YOLO Format

MicroDetect uses the YOLO annotation format:
- Each image has a corresponding .txt file with the same name
- Each line in the .txt file represents one object in the format:
  ```
  class_id center_x center_y width height
  ```
- All values are normalized to the range [0,1]
- Example: `0 0.5 0.5 0.1 0.2` represents a class 0 object in the center of the image

### Converting to Other Formats

To convert annotations to other formats, use the conversion module:

```python
from microdetect.utils.convert_annotations import yolo_to_pascal_voc

# Convert YOLO format to Pascal VOC format
yolo_to_pascal_voc("path/to/labels", "path/to/images", "path/to/output_xml")
```

Supported conversions:
- YOLO ↔ Pascal VOC
- YOLO ↔ COCO
- YOLO ↔ CSV

### Backing Up Annotations

It's recommended to regularly back up your annotation files:

```bash
# Create a timestamped backup
backup_dir="backup_annotations_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$backup_dir"
cp -r path/to/labels/* "$backup_dir"
```

## Best Practices

### Annotation Consistency

For best results:
- Define clear annotation guidelines before starting
- Be consistent in how you annotate similar objects
- For clustered microorganisms, decide whether to annotate them individually or as a group
- Consider using a validation process where multiple annotators review the same images

### Handling Difficult Cases

For challenging images:
- Use zoom for small microorganisms
- For partially visible objects at image edges, include the visible part
- For microorganisms in different focal planes, annotate those that are clearly in focus
- Document any special cases for reference

### Quality Control

Regularly check annotation quality:
- Use the visualization tool to review annotations
- Check for missed microorganisms or incorrect classifications
- Verify that bounding boxes are tight around the microorganisms
- Review class distribution to ensure a balanced dataset

## Troubleshooting

**Problem**: Annotation tool doesn't start
**Solution**: Check if Tkinter is installed (`pip install tk`) and if you're using a display-enabled environment

**Problem**: Annotations not saving
**Solution**: Check directory permissions and paths; use absolute paths if necessary

**Problem**: Annotation boxes not visible in visualization
**Solution**: Verify that the label filename matches the image filename (without extension)

**Problem**: Performance issues with large images
**Solution**: Resize large images to a manageable size before annotation

**Problem**: Incomplete progress tracking
**Solution**: Check for and remove empty `.annotation_progress.json` files

For more issues, refer to the [Troubleshooting Guide](troubleshooting.md).