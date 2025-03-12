# Model Evaluation and Data Analysis Guide

This guide explains how to evaluate trained models and analyze detection results in MicroDetect.

## Table of Contents
- [Introduction](#introduction)
- [Model Evaluation](#model-evaluation)
  - [Basic Evaluation](#basic-evaluation)
  - [Evaluation Metrics](#evaluation-metrics)
  - [Confusion Matrix](#confusion-matrix)
  - [Threshold Adjustment](#threshold-adjustment)
  - [Cross-Validation](#cross-validation)
- [Performance Analysis](#performance-analysis)
  - [Detection Speed](#detection-speed)
  - [Resource Usage](#resource-usage)
  - [Model Size Comparison](#model-size-comparison)
- [Result Visualization](#result-visualization)
  - [Generating Detection Overlays](#generating-detection-overlays)
  - [Interactive Visualization](#interactive-visualization)
  - [Batch Processing](#batch-processing)
  - [Exporting Results](#exporting-results)
- [Error Analysis](#error-analysis)
  - [False Positives](#false-positives)
  - [False Negatives](#false-negatives)
  - [Classification Errors](#classification-errors)
  - [Localization Errors](#localization-errors)
- [Statistical Analysis](#statistical-analysis)
  - [Density Maps](#density-maps)
  - [Size Distribution](#size-distribution)
  - [Spatial Analysis](#spatial-analysis)
  - [Temporal Analysis](#temporal-analysis)
- [Reporting](#reporting)
  - [Generating PDF Reports](#generating-pdf-reports)
  - [Exporting to CSV](#exporting-to-csv)
  - [Interactive Dashboards](#interactive-dashboards)
- [Best Practices](#best-practices)
  - [Model Selection](#model-selection)
  - [Dataset Considerations](#dataset-considerations)
  - [Iterative Improvement](#iterative-improvement)
- [Troubleshooting](#troubleshooting)

## Introduction

Model evaluation is a critical step in the microorganism detection workflow. It helps:

- Assess model accuracy and reliability
- Identify areas for improvement
- Compare different model configurations
- Determine the optimal settings for deployment

MicroDetect provides comprehensive tools for evaluating models and analyzing detection results.

## Model Evaluation

### Basic Evaluation

To evaluate a trained model on a test dataset:

```bash
microdetect evaluate --model_path runs/train/exp/weights/best.pt --dataset_dir dataset --data_yaml dataset/data.yaml
```

This command generates a comprehensive evaluation report including:
- Precision, recall, and F1-score for each class
- mAP50 and mAP50-95 metrics
- Inference speed
- Confusion matrix (if enabled)

### Evaluation Metrics

MicroDetect calculates several key metrics:

- **Precision**: The proportion of true positive detections among all detections
- **Recall**: The proportion of true positive detections among all actual objects
- **F1-score**: The harmonic mean of precision and recall
- **mAP50**: Mean Average Precision at IoU threshold of 0.5
- **mAP50-95**: Mean Average Precision averaged over IoU thresholds from 0.5 to 0.95

Example output:

```
Class         Images    Labels  Precision   Recall   mAP50  mAP50-95
All           50        230     0.962       0.921    0.947   0.736
Class 0       50        98      0.981       0.934    0.972   0.762
Class 1       50        87      0.953       0.932    0.943   0.726
Class 2       50        45      0.951       0.897    0.925   0.721
```

### Confusion Matrix

To generate a confusion matrix for detailed error analysis:

```bash
microdetect evaluate --model_path runs/train/exp/weights/best.pt --dataset_dir dataset --confusion_matrix
```

The confusion matrix visualization shows:
- True positives (diagonal elements)
- False positives (off-diagonal elements in columns)
- False negatives (off-diagonal elements in rows)
- Background detections or missed objects

### Threshold Adjustment

You can adjust detection confidence and IoU thresholds to optimize performance:

```bash
microdetect evaluate --model_path runs/train/exp/weights/best.pt --dataset_dir dataset --conf_threshold 0.4 --iou_threshold 0.6
```

To find the optimal thresholds:

```python
# Python script to sweep threshold values
import numpy as np
from microdetect.training.evaluate import ModelEvaluator

evaluator = ModelEvaluator()
model_path = "runs/train/exp/weights/best.pt"
data_yaml = "dataset/data.yaml"

# Sweep confidence thresholds
conf_thresholds = np.arange(0.1, 0.9, 0.1)
results = []

for conf in conf_thresholds:
    metrics = evaluator.evaluate_model(model_path, data_yaml, conf_threshold=conf)
    results.append({
        'conf_threshold': conf,
        'mAP50': metrics['metricas_gerais']['Precisão (mAP50)'],
        'recall': metrics['metricas_gerais']['Recall']
    })
    
# Print results table
for result in results:
    print(f"Conf: {result['conf_threshold']:.1f}, mAP50: {result['mAP50']:.4f}, Recall: {result['recall']:.4f}")
```

### Cross-Validation

For more robust evaluation, especially with limited data, use cross-validation:

```python
from microdetect.training.cross_validate import CrossValidator

validator = CrossValidator(
    base_dataset_dir="dataset",
    output_dir="cross_val_results",
    model_size="m",
    epochs=100,
    folds=5
)

results = validator.run()
validator.generate_report()
```

This performs k-fold cross-validation, training and evaluating the model on different data splits.

## Performance Analysis

### Detection Speed

To evaluate detection speed:

```bash
microdetect evaluate --model_path runs/train/exp/weights/best.pt --dataset_dir dataset --benchmark_speed
```

This measures:
- Inference time per image (ms)
- Frames per second (FPS)
- Pre-processing and post-processing times

For batch inference speed:

```python
from microdetect.training.evaluate import SpeedBenchmark

benchmark = SpeedBenchmark(model_path="runs/train/exp/weights/best.pt")
results = benchmark.run(
    batch_sizes=[1, 2, 4, 8, 16],
    image_sizes=[640, 960, 1280],
    iterations=100
)
benchmark.plot_results("speed_benchmark.png")
```

### Resource Usage

To monitor GPU memory and CPU usage during inference:

```python
from microdetect.utils.resource_monitor import ResourceMonitor
from microdetect.training.evaluate import ModelEvaluator

monitor = ResourceMonitor()
monitor.start()

evaluator = ModelEvaluator()
evaluator.evaluate_model("runs/train/exp/weights/best.pt", "dataset/data.yaml")

stats = monitor.stop()
monitor.plot_usage("resource_usage.png")
```

### Model Size Comparison

To compare models of different sizes:

```bash
microdetect evaluate --model_path runs/train/exp1/weights/best.pt,runs/train/exp2/weights/best.pt --dataset_dir dataset --output_dir comparison
```

This generates a comparison report including:
- Model size (parameters, file size)
- Accuracy metrics
- Inference speed
- Trade-off visualization (accuracy vs. speed)

## Result Visualization

### Generating Detection Overlays

To visualize detections on images:

```bash
microdetect detect --model_path runs/train/exp/weights/best.pt --source path/to/images --output_dir path/to/output
```

This creates images with bounding boxes, class labels, and confidence scores.

### Interactive Visualization

For interactive visualization of results:

```bash
microdetect visualize_results --model_path runs/train/exp/weights/best.pt --source path/to/images
```

This opens an interface where you can:
- View detections
- Adjust confidence thresholds in real-time
- Filter classes
- Compare with ground truth (if available)

### Batch Processing

For large datasets, use batch processing:

```bash
microdetect batch_detect --model_path runs/train/exp/weights/best.pt --source path/to/images --output_dir path/to/output --batch_size 16
```

### Exporting Results

To export detection results for further analysis:

```bash
microdetect detect --model_path runs/train/exp/weights/best.pt --source path/to/images --save_txt --save_json
```

This saves:
- Text files with YOLO format annotations
- JSON file with detailed detection information
- CSV file summarizing all detections

## Error Analysis

### False Positives

To analyze false positive detections:

```bash
microdetect analyze_errors --model_path runs/train/exp/weights/best.pt --dataset_dir dataset --focus false_positives --output_dir error_analysis
```

This generates:
- Images showing false positive detections
- Analysis of common error patterns
- Suggestions for improvement

### False Negatives

To analyze false negative detections (missed objects):

```bash
microdetect analyze_errors --model_path runs/train/exp/weights/best.pt --dataset_dir dataset --focus false_negatives --output_dir error_analysis
```

### Classification Errors

To analyze classification errors (correct detection but wrong class):

```bash
microdetect analyze_errors --model_path runs/train/exp/weights/best.pt --dataset_dir dataset --focus classification_errors --output_dir error_analysis
```

### Localization Errors

To analyze localization errors (IoU below threshold):

```bash
microdetect analyze_errors --model_path runs/train/exp/weights/best.pt --dataset_dir dataset --focus localization_errors --output_dir error_analysis
```

## Statistical Analysis

### Density Maps

To generate density maps showing microorganism distribution:

```bash
microdetect analyze_distribution --model_path runs/train/exp/weights/best.pt --source path/to/images --output_dir density_maps
```

This creates heatmaps showing the spatial distribution of detected microorganisms.

### Size Distribution

To analyze the size distribution of detected microorganisms:

```bash
microdetect analyze_size --model_path runs/train/exp/weights/best.pt --source path/to/images --output_dir size_analysis
```

This generates histograms and statistics on microorganism sizes by class.

### Spatial Analysis

For spatial relationship analysis:

```bash
microdetect analyze_spatial --model_path runs/train/exp/weights/best.pt --source path/to/images --output_dir spatial_analysis
```

This analyzes:
- Nearest neighbor distances
- Clustering patterns
- Spatial correlations between different classes

### Temporal Analysis

If you have time-series images, analyze changes over time:

```bash
microdetect analyze_temporal --model_path runs/train/exp/weights/best.pt --source path/to/time_series --output_dir temporal_analysis
```

This generates:
- Time series plots of microorganism counts
- Growth/decline rate analysis
- Change visualization over time

## Reporting

### Generating PDF Reports

To generate a comprehensive PDF report:

```bash
microdetect generate_report --results_dir runs/detect/exp --output_file report.pdf
```

This creates a PDF including:
- Model summary
- Evaluation metrics
- Sample detection images
- Error analysis
- Statistical insights

### Exporting to CSV

To export data for analysis in other tools:

```bash
microdetect export_results --results_dir runs/detect/exp --format csv --output_file results.csv
```

### Interactive Dashboards

For interactive data exploration:

```bash
microdetect dashboard --results_dir runs/detect/exp --port 8050
```

This starts a web dashboard with:
- Interactive visualizations
- Filtering capabilities
- Export options
- Comparison tools

## Best Practices

### Model Selection

Guidelines for selecting the appropriate model:

- **YOLOv8-n**: Fast inference, lower accuracy, suitable for resource-constrained environments
- **YOLOv8-s**: Balance of speed and accuracy for many applications
- **YOLOv8-m**: Higher accuracy with moderate speed, good for general detection
- **YOLOv8-l**: High accuracy, slower speed, for applications requiring precision
- **YOLOv8-x**: Highest accuracy, slowest speed, for research or when speed is not critical

### Dataset Considerations

For optimal evaluation:

- Use a representative test dataset
- Ensure proper class distribution
- Include challenging cases
- Maintain data independence (no overlap with training data)
- Consider real-world conditions

### Iterative Improvement

Process for continuous model improvement:

1. Evaluate the current model
2. Analyze errors and limitations
3. Collect additional data targeting weaknesses
4. Refine annotation guidelines if needed
5. Retrain with improved data
6. Re-evaluate and compare with previous versions

## Troubleshooting

**Problem**: Low precision despite high training accuracy
**Solution**: Check for data leakage between train and test sets; analyze false positives

**Problem**: Low recall despite good validation metrics
**Solution**: Check for class imbalance; review annotation consistency; analyze false negatives

**Problem**: Evaluation is very slow
**Solution**: Reduce batch size; use smaller image size; check hardware utilization

**Problem**: Out of memory during evaluation
**Solution**: Reduce batch size; use device="cpu" for large models on limited hardware

**Problem**: Inconsistent metrics between runs
**Solution**: Set a fixed random seed; increase test dataset size; check for edge cases

For more detailed troubleshooting, refer to the [Troubleshooting Guide](troubleshooting.md).