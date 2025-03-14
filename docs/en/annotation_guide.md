# Annotation Guide

This guide explains how to use MicroDetect's annotation tools to label microorganisms in microscopy images.

## Table of Contents
- [Introduction](#introduction)
- [Annotation Tool](#annotation-tool)
  - [Starting the Annotation Tool](#starting-the-annotation-tool)
  - [Interface Overview](#interface-overview)
  - [Annotation Workflow](#annotation-workflow)
  - [Keyboard Shortcuts](#keyboard-shortcuts)
  - [Auto-save and Progress Tracking](#auto-save-and-progress-tracking)
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

Accurate annotation of microscopy images is a critical step in developing effective microorganism detection models. MicroDetect provides a specialized annotation tool designed specifically for annotating microorganisms in microscopy images, with features such as:

1. User-friendly interface with familiar controls
2. Resumable annotation sessions
3. Progress tracking
4. Automatic saving to prevent data loss
5. Support for multiple microorganism classes
6. Keyboard shortcuts for efficient workflow

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

![Annotation Interface](https://example.com/annotation_interface.png)

### Annotation Workflow

1. **Load Image**: The tool loads an image from the specified directory
2. **Select Class**: Choose the appropriate microorganism class from the dropdown
3. **Draw Bounding Box**: Click and drag to create a bounding box around the microorganism
4. **Adjust Box**: Fine-tune the position and size of the box if needed
5. **Add More Objects**: Repeat steps 2-4 for additional microorganisms
6. **Save Annotations**: Annotations are automatically saved or press 'S' to save manually
7. **Navigate**: Use navigation buttons or keyboard shortcuts to move to the next/previous image

Tips for effective annotation:
- Draw tight bounding boxes around each microorganism
- For clustered microorganisms, annotate each one individually if distinguishable
- Be consistent in annotation across all images
- Use zoom for small microorganisms
- Use keyboard shortcuts to speed up the process

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

These shortcuts make the annotation process faster and more efficient, especially when annotating large datasets.

### Auto-save and Progress Tracking

The annotation tool automatically saves your work to prevent data loss:

- Annotations are saved in YOLO format (.txt files) in the output directory
- Progress is tracked in a `.annotation_progress.json` file
- When restarting the tool with the same directories, you can resume where you left off
- A backup of previous annotation versions is maintained in case of errors

To resume an annotation session:

```bash
microdetect annotate --image_dir path/to/images --output_dir path/to/labels --resume
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
- Example: `0 0.5 0.5 0.1 0.2` represents a class 0 object in the center of the image with width 10% and height 20% of the image dimensions

Example annotation file for an image containing three microorganisms (two of class 0 and one of class 1):
```
0 0.762 0.451 0.112 0.087
0 0.245 0.321 0.098 0.076
1 0.542 0.622 0.156 0.143
```

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

These conversions can be useful when integrating with other tools or frameworks that require different annotation formats.

### Backing Up Annotations

It's recommended to regularly back up your annotation files:

```bash
# Create a timestamped backup
backup_dir="backup_annotations_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$backup_dir"
cp -r path/to/labels/* "$backup_dir"
```

You can also use version control systems like Git to track changes to your annotation files.

## Best Practices

### Annotation Consistency

For best results:
- Define clear annotation guidelines before starting
- Be consistent in how you annotate similar objects
- For clustered microorganisms, decide whether to annotate them individually or as a group
- Consider using a validation process where multiple annotators review the same images

Example annotation guidelines:
1. Always draw tight bounding boxes that contain the complete microorganism
2. For partially visible microorganisms at image borders, include the visible part
3. For overlapping microorganisms, annotate each one separately if boundaries are clear
4. For out-of-focus microorganisms, annotate only those that are clearly visible
5. Use consistent class assignments for similar-looking microorganisms

### Handling Difficult Cases

For challenging images:
- Use zoom for small microorganisms
- For partially visible objects at image edges, include the visible part
- For microorganisms in different focal planes, annotate those that are clearly in focus
- Document any special cases for reference

For very crowded images:
- Consider breaking annotation into multiple sessions to avoid fatigue
- Use the zoom feature to focus on specific regions
- Be methodical in covering all areas of the image (e.g., work from top to bottom)

### Quality Control

Regularly check annotation quality:
- Use the visualization tool to review annotations
- Check for missed microorganisms or incorrect classifications
- Verify that bounding boxes are tight around the microorganisms
- Review class distribution to ensure a balanced dataset

Establish a validation process:
- Have another person review a sample of annotations
- Compare annotations between annotators to establish consistency
- Create a reference guide with examples of correctly annotated images

## Troubleshooting

**Problem**: Annotation tool doesn't start
**Solution**: Check if Tkinter is installed (`pip install tk`) and if you're using a display-enabled environment

**Problem**: Annotations not saving
**Solution**: Check directory permissions and paths; use absolute paths if necessary

**Problem**: Can't see annotations when reviewing
**Solution**: Verify that the label filename matches the image filename (without extension)

**Problem**: Performance issues with large images
**Solution**: Resize large images to a manageable size before annotation

**Problem**: Incomplete progress tracking
**Solution**: Check for and remove empty `.annotation_progress.json` files

**Problem**: Difficult to draw precise annotations
**Solution**: Use the zoom feature to get a more detailed view; adjust boxes after initial drawing

**Problem**: Missing classes in dropdown
**Solution**: Verify that classes are properly defined in config.yaml or use the `--classes` parameter

For more issues, refer to the [Troubleshooting Guide](troubleshooting.md).