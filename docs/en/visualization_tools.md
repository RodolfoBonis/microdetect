# Visualization Tools Guide

This guide explains the visualization and reporting capabilities of MicroDetect for analyzing detection results.

## Table of Contents
- [Introduction](#introduction)
- [Detection Visualization](#detection-visualization)
  - [Basic Visualization](#basic-visualization)
  - [Interactive Visualization](#interactive-visualization)
  - [Batch Processing](#batch-processing)
- [Report Generation](#report-generation)
  - [PDF Reports](#pdf-reports)
  - [CSV Reports](#csv-reports)
  - [Exporting to YOLO Format](#exporting-to-yolo-format)
- [Interactive Dashboards](#interactive-dashboards)
  - [Detection Dashboard](#detection-dashboard)
  - [Model Comparison Dashboard](#model-comparison-dashboard)
- [Statistical Visualizations](#statistical-visualizations)
  - [Density Maps](#density-maps)
  - [Size Distribution](#size-distribution)
  - [Spatial Analysis](#spatial-analysis)
- [Customization](#customization)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)

## Introduction

MicroDetect provides a comprehensive set of visualization and reporting tools to help you understand, interpret, and present detection results. These tools allow you to:

- Visualize detections on images
- Create interactive dashboards for data exploration
- Generate professional reports in PDF and CSV formats
- Perform statistical analysis of detection patterns
- Compare different models visually

These visualizations help bridge the gap between raw data and actionable insights, making it easier to communicate results and make informed decisions.

## Detection Visualization

### Basic Visualization

The `visualize_detections` command allows you to visualize detection results on images:

```bash
microdetect visualize_detections --model_path runs/train/exp/weights/best.pt \
                                --source path/to/images \
                                --conf_threshold 0.25
```

This opens an interactive window where you can:
- View detections with bounding boxes and labels
- Navigate through images using keyboard controls
- Adjust confidence threshold in real-time
- See detection confidence scores

**Keyboard Controls:**
- `n`: Next image
- `p`: Previous image
- `+`: Increase confidence threshold
- `-`: Decrease confidence threshold
- `q`: Quit visualization

### Interactive Visualization

For a more detailed exploration of a single image:

```bash
microdetect visualize_detections --model_path runs/train/exp/weights/best.pt \
                                --source path/to/single_image.jpg \
                                --interactive
```

The interactive mode provides additional features:
- Zoom in/out of regions of interest
- Display extended information about each detection
- Compare with ground truth (if available)
- Save specific views to files

### Batch Processing

Process multiple images and save the visualization results:

```bash
microdetect batch_detect --model_path runs/train/exp/weights/best.pt \
                        --source path/to/images \
                        --output_dir path/to/output \
                        --save_img \
                        --batch_size 16
```

Options:
- `--save_img`: Save images with detection overlays
- `--save_txt`: Save detection results in YOLO format
- `--save_json`: Save detection results in JSON format
- `--batch_size`: Number of images to process in each batch
- `--conf_threshold`: Confidence threshold for detections

## Report Generation

### PDF Reports

Generate comprehensive PDF reports of model evaluation results:

```bash
microdetect generate_report --results_dir runs/detect/exp \
                          --output_file report.pdf \
                          --format pdf \
                          --include_images "img1.jpg,img2.jpg"
```

The PDF report includes:
- Model information and performance metrics
- Class-specific metrics (precision, recall, F1-score)
- Visualizations of key metrics
- Example detection images (if specified)
- Summary statistics and charts

### CSV Reports

Export metrics and results in CSV format for further analysis:

```bash
microdetect generate_report --results_dir runs/detect/exp \
                          --output_file metrics.csv \
                          --format csv
```

The CSV export includes:
- General metrics (mAP50, mAP50-95, recall, precision)
- Per-class metrics
- Raw data for custom analysis in spreadsheet software

### Exporting to YOLO Format

Export detection results in YOLO annotation format:

```bash
microdetect batch_detect --model_path runs/train/exp/weights/best.pt \
                        --source path/to/images \
                        --save_txt \
                        --output_dir path/to/output
```

This creates text files in YOLO format for each image, with one line per detection:
```
class_id center_x center_y width height
```

This format is compatible with YOLO training and other tools that use YOLO annotations.

## Interactive Dashboards

### Detection Dashboard

Launch an interactive web dashboard to explore detection results:

```bash
microdetect dashboard --results_dir runs/detect/exp \
                     --port 8050
```

The detection dashboard provides:
- Filterable visualization of detections by class and confidence
- Histograms of confidence scores
- Charts showing detection counts by class
- Details panel for exploring individual images
- Size vs. confidence scatter plots

### Model Comparison Dashboard

Compare multiple models with an interactive dashboard:

```bash
microdetect dashboard --comparison_file model_comparison_results.json \
                     --port 8051
```

The comparison dashboard includes:
- Side-by-side metrics comparison
- Performance vs. speed trade-off visualization
- Model size comparison
- Interactive metric selection
- Detailed comparison tables

## Statistical Visualizations

MicroDetect provides tools for statistical analysis of detection patterns:

### Density Maps

Generate heatmaps showing the density of detections across images:

```bash
microdetect analyze_distribution --model_path runs/train/exp/weights/best.pt \
                               --source path/to/images \
                               --output_dir density_maps
```

Density maps help visualize:
- Areas with high concentration of microorganisms
- Distribution patterns across images
- Class-specific distribution patterns (when using `--by_class`)

### Size Distribution

Analyze and visualize the size distribution of detected objects:

```bash
microdetect analyze_size --model_path runs/train/exp/weights/best.pt \
                        --source path/to/images \
                        --output_dir size_analysis
```

Size distribution analysis provides:
- Histograms of object sizes
- Class-specific size distributions
- Statistical summaries (mean, median, range)
- Outlier identification

### Spatial Analysis

Analyze spatial relationships between detected objects:

```bash
microdetect analyze_spatial --model_path runs/train/exp/weights/best.pt \
                          --source path/to/images \
                          --output_dir spatial_analysis
```

Spatial analysis includes:
- Nearest neighbor distance distributions
- Clustering analysis
- Spatial correlation between different classes
- Visualization of spatial patterns

## Customization

### Customizing Visualizations

You can customize various aspects of the visualizations:

```bash
microdetect visualize_detections --model_path model.pt \
                                --source images/ \
                                --conf_threshold 0.25 \
                                --line_thickness 2 \
                                --font_scale 0.6 \
                                --show_labels True
```

Options:
- `--line_thickness`: Thickness of bounding box lines
- `--font_scale`: Size of text labels
- `--show_labels`: Whether to display class labels and confidence scores

### Customizing Reports

For PDF reports, you can provide a custom HTML template:

```bash
microdetect generate_report --results_dir runs/detect/exp \
                          --output_file report.pdf \
                          --format pdf \
                          --template_path my_template.html
```

The template uses Jinja2 syntax and has access to:
- `model_name`: Name of the model
- `model_path`: Path to the model file
- `date`: Report generation date
- `general_metrics`: Dictionary of general metrics
- `class_metrics`: List of per-class metrics
- `images`: List of included image paths

## Best Practices

1. **Use batch processing for large datasets**: When processing many images, use batch detection with appropriate batch size

2. **Generate reports with examples**: Include representative images in PDF reports to provide context

3. **Start with interactive visualization**: Use interactive visualization to explore results before generating static reports

4. **Combine visualization types**: Use multiple visualization types to get a complete understanding of your results

5. **Customize for your audience**: Tailor reports and visualizations based on the technical knowledge of your audience

6. **Save intermediate results**: Save JSON results when running batch detection to enable future analysis without rerunning the model

## Troubleshooting

### Issue: Visualizations are too crowded with many detections
**Solution**: Increase the confidence threshold to show only high-confidence detections

### Issue: PDF report generation fails
**Solution**: Ensure that wkhtmltopdf is installed on your system (required by pdfkit)

### Issue: Dashboard doesn't load in browser
**Solution**: Check if the specified port is already in use; try a different port

### Issue: Images in PDF reports appear distorted
**Solution**: Check image dimensions; very large images might need to be resized before inclusion

### Issue: Missing data in dashboards
**Solution**: Ensure that your detection results have all required fields; check JSON format

For more troubleshooting information, see the [Troubleshooting Guide](troubleshooting.md).