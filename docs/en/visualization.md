# Visualization Guide

This guide explains how to use MicroDetect's visualization tools to review annotations and visualize detection results.

## Table of Contents
- [Introduction](#introduction)
- [Visualizing Annotations](#visualizing-annotations)
  - [Basic Visualization](#basic-visualization)
  - [Batch Visualization](#batch-visualization)
  - [Filtering by Class](#filtering-by-class)
  - [Customizing Visual Output](#customizing-visual-output)
- [Visualizing Detection Results](#visualizing-detection-results)
  - [Basic Detection Visualization](#basic-detection-visualization)
  - [Interactive Visualization](#interactive-visualization)
  - [Detection Dashboard](#detection-dashboard)
- [Comparison Visualizations](#comparison-visualizations)
  - [Ground Truth vs. Predictions](#ground-truth-vs-predictions)
  - [Multiple Model Comparison](#multiple-model-comparison)
- [Exporting Visualizations](#exporting-visualizations)
  - [Saving Images](#saving-images)
  - [Creating Reports](#creating-reports)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)

## Introduction

Visualization is a crucial component of the microorganism detection workflow. MicroDetect provides comprehensive visualization tools that help you:

- Review and validate annotations
- Visualize detection results from trained models
- Compare model predictions with ground truth
- Create visual reports for presentations and publications
- Interactively explore detection data

These visualization tools support both single image review and batch processing for larger datasets.

## Visualizing Annotations

### Basic Visualization

To visualize annotations for a single image interactively:

```bash
microdetect visualize --image_dir path/to/images --label_dir path/to/labels
```

This opens a window showing the image with overlaid annotations. You can:
- Navigate through images using keyboard shortcuts (A/D for previous/next)
- Zoom in/out for detailed inspection
- View class labels and bounding boxes
- Filter annotations by class

### Batch Visualization

To generate annotated images for an entire directory:

```bash
microdetect visualize --image_dir path/to/images --label_dir path/to/labels --output_dir path/to/output
```

This creates a copy of each image with annotations drawn on it and saves them to the output directory. This is useful for:
- Creating a dataset overview
- Documenting annotation progress
- Generating training material
- Quality assurance of annotations

### Filtering by Class

To visualize only specific classes:

```bash
microdetect visualize --image_dir path/to/images --label_dir path/to/labels --filter_classes 0,1
```

This shows only annotations for classes with IDs 0 and 1. This is helpful when:
- Focusing on specific microorganism types
- Verifying annotations for a particular class
- Creating class-specific documentation

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

Alternatively, you can specify visualization parameters directly in the command:

```bash
microdetect visualize --image_dir path/to/images --label_dir path/to/labels --box_thickness 3 --text_size 0.6
```

## Visualizing Detection Results

### Basic Detection Visualization

To visualize detections from a trained model:

```bash
microdetect detect --model_path runs/train/exp/weights/best.pt --source path/to/images --save_img
```

This runs the model on the specified images and saves the visualization results with bounding boxes, class labels, and confidence scores. The output includes:
- Original image with overlaid detections
- Class labels
- Confidence scores
- Color-coded bounding boxes

### Interactive Visualization

For interactive exploration of detection results:

```bash
microdetect visualize_detections --model_path runs/train/exp/weights/best.pt --source path/to/images --interactive
```

The interactive mode allows you to:
- Adjust confidence threshold in real-time
- Filter detections by class
- Zoom in on regions of interest
- Measure detection sizes
- Compare different detection settings

### Detection Dashboard

For a more comprehensive visualization dashboard:

```bash
microdetect dashboard --results_dir runs/detect/exp --port 8050
```

This launches a web-based dashboard that provides:
- Summary statistics of detections
- Class distribution charts
- Size distribution histograms
- Interactive image browser
- Filtering capabilities
- Detection details panel

The dashboard is particularly useful for analyzing large sets of detection results and identifying patterns across multiple images.

## Comparison Visualizations

### Ground Truth vs. Predictions

To compare model predictions with ground truth annotations:

```bash
microdetect compare_detections --model_path runs/train/exp/weights/best.pt --source path/to/images --label_dir path/to/labels
```

This visualization shows:
- True Positives (matching detections) in green
- False Positives (extra detections) in red
- False Negatives (missed objects) in blue
- IoU values for each matched detection

This helps identify where your model is performing well and where it needs improvement.

### Multiple Model Comparison

To compare detections from multiple models:

```bash
microdetect compare_models --model_paths model1.pt,model2.pt,model3.pt --source path/to/images --visualization
```

This generates a visual comparison showing:
- Detections from each model with different colors
- Overlapping detections
- Differences in confidence scores
- Differences in bounding box precision

This is useful for selecting the best model for your application or understanding the trade-offs between different models.

## Exporting Visualizations

### Saving Images

To save visualization results:

```bash
microdetect visualize --image_dir path/to/images --label_dir path/to/labels --output_dir path/to/visualizations --format png
```

Supported formats:
- PNG (lossless, larger files)
- JPEG (lossy compression, smaller files)
- TIFF (high quality, preserves metadata)

### Creating Reports

To generate a visual report in PDF format:

```bash
microdetect generate_report --results_dir runs/detect/exp --format pdf --output_file report.pdf --include_images
```

This creates a comprehensive report including:
- Summary statistics
- Sample visualizations
- Detection charts
- Class distribution
- Confidence score distribution

## Best Practices

1. **Consistent Color Scheme**: Use consistent colors for classes across all visualizations

2. **Appropriate Thickness**: Adjust box thickness based on image resolution (thicker for high-res images)

3. **Include Scale Information**: When possible, include scale information in visualizations

4. **Use Appropriate Confidence Threshold**: Adjust confidence threshold to show meaningful detections

5. **Interactive First, Then Batch**: Use interactive visualization to determine optimal settings, then run batch visualization

6. **Include Context**: When creating reports, include both zoomed-in details and context views

7. **Balance Detail and Overview**: Provide both detailed individual visualizations and summary visualizations

8. **Consider Color Blindness**: Choose color schemes that are distinguishable for people with color blindness

## Troubleshooting

**Problem**: Visualizations show no annotations or detections
**Solution**: Verify file paths and naming conventions; check that label files match image names

**Problem**: Text labels are too small or too large
**Solution**: Adjust the `text_size` parameter to an appropriate value for your image resolution

**Problem**: Colors don't match between different visualization tools
**Solution**: Set consistent colors in config.yaml and verify they're being applied correctly

**Problem**: Dashboard fails to load
**Solution**: Check if required dependencies are installed (`pip install dash dash-bootstrap-components`)

**Problem**: High-resolution images cause performance issues
**Solution**: Resize images before visualization or use batch processing with lower resolution output

**Problem**: PDF report generation fails
**Solution**: Ensure wkhtmltopdf is installed for PDF generation

**Problem**: Class labels or IDs don't match expectations
**Solution**: Verify class configuration in config.yaml and check that it matches your dataset

For more troubleshooting information, see the [Troubleshooting Guide](troubleshooting.md).