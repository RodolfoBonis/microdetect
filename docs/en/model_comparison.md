# Model Comparison Guide

This guide explains how to use MicroDetect's model comparison tools to evaluate and select the best model for your microorganism detection tasks.

## Table of Contents
- [Introduction](#introduction)
- [Comparing Models](#comparing-models)
  - [Basic Comparison](#basic-comparison)
  - [Advanced Comparison](#advanced-comparison)
  - [Interactive Comparison Dashboard](#interactive-comparison-dashboard)
- [Comparison Metrics](#comparison-metrics)
  - [Accuracy Metrics](#accuracy-metrics)
  - [Performance Metrics](#performance-metrics)
  - [Size and Resource Metrics](#size-and-resource-metrics)
- [Visualizing Comparison Results](#visualizing-comparison-results)
  - [Comparison Charts](#comparison-charts)
  - [Trade-off Visualization](#trade-off-visualization)
  - [Detection Comparison](#detection-comparison)
- [Decision Making Framework](#decision-making-framework)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)

## Introduction

Model comparison is essential for selecting the optimal model for your microorganism detection needs. Different models offer different trade-offs between:

- Detection accuracy
- Inference speed
- Resource requirements
- Model size

MicroDetect provides comprehensive tools to compare multiple models across these dimensions, helping you make informed decisions based on your specific requirements.

## Comparing Models

### Basic Comparison

To compare different models or model configurations:

```bash
microdetect compare_models --model_paths model1.pt,model2.pt,model3.pt --data_yaml dataset/data.yaml
```

This command evaluates the specified models on the test dataset defined in `data.yaml` and generates a comparison report including:

- Performance metrics (mAP50, mAP50-95, precision, recall) for each model
- Inference speed measurements
- Model size comparison
- Per-class metrics comparison

Example output:
```
+-------------+-------+--------+----------+--------+-------------+----------+
| Model       | mAP50 | mAP50- | Precis.  | Recall | Infer. Time | Size(MB) |
|             |       | 95     |          |        | (ms/img)    |          |
+-------------+-------+--------+----------+--------+-------------+----------+
| yolov8n_m1  | 0.823 | 0.615  | 0.856    | 0.827  | 4.5         | 6.2      |
| yolov8s_m2  | 0.867 | 0.654  | 0.895    | 0.843  | 8.7         | 22.8     |
| yolov8m_m3  | 0.892 | 0.703  | 0.912    | 0.867  | 19.2        | 52.1     |
+-------------+-------+--------+----------+--------+-------------+----------+
```

### Advanced Comparison

For more detailed comparison with additional metrics and customization:

```python
from microdetect.training import ModelComparator

comparator = ModelComparator(output_dir="comparison_results")

# Compare multiple models with custom settings
results = comparator.compare_models(
    model_paths=[
        "runs/train/yolov8n_custom/weights/best.pt",
        "runs/train/yolov8s_custom/weights/best.pt",
        "runs/train/yolov8m_custom/weights/best.pt"
    ],
    data_yaml="dataset/data.yaml",
    conf_threshold=0.25,
    iou_threshold=0.7,
    batch_size=16,
    device="0",  # Use specific GPU
    include_precision_recall_curve=True,
    include_class_metrics=True,
    save_json=True
)

# Generate comprehensive comparison report
comparator.generate_comparison_report(
    results=results,
    output_file="model_comparison_report.pdf",
    include_images=True,
    include_charts=True
)
```

This generates a comprehensive comparison with:
- Detailed per-class metrics
- Precision-recall curves
- F1 score vs. confidence threshold curves
- Size and performance trade-off charts
- Example detection images from each model

### Interactive Comparison Dashboard

For interactive exploration of model comparisons:

```bash
microdetect compare_models --model_paths model1.pt,model2.pt,model3.pt --data_yaml dataset/data.yaml --dashboard
```

This launches an interactive dashboard allowing you to:
- Visualize metrics side-by-side
- Filter comparison by class
- Adjust confidence and IoU thresholds in real-time
- Compare detection results on sample images
- Create custom comparison charts
- Export results in various formats

## Comparison Metrics

### Accuracy Metrics

MicroDetect compares models using the following accuracy metrics:

1. **mAP50**: Mean Average Precision at IoU threshold of 0.5
2. **mAP50-95**: Mean Average Precision averaged over IoU thresholds from 0.5 to 0.95
3. **Precision**: Ratio of true positives to all detections
4. **Recall**: Ratio of true positives to all ground truth objects
5. **F1-Score**: Harmonic mean of precision and recall

For class-specific comparisons, these metrics are calculated for each class, allowing you to identify which model performs best for specific microorganism types.

### Performance Metrics

To compare model performance and efficiency:

1. **Inference Time**: Average time to process one image (ms/image)
2. **Frames Per Second (FPS)**: Number of images that can be processed per second
3. **Latency**: Time from input to output
4. **Throughput**: Number of objects processed per second at batch size

These metrics are measured across different:
- Batch sizes (1, 2, 4, 8, 16)
- Image sizes (640, 960, 1280)
- Hardware configurations (CPU, GPU, different devices)

### Size and Resource Metrics

To evaluate model deployment requirements:

1. **Model Size**: Size of the model file in megabytes
2. **Parameter Count**: Number of parameters in the model
3. **Memory Usage**: Peak RAM consumption during inference
4. **GPU Memory**: VRAM required for inference
5. **CPU Usage**: CPU utilization during inference

## Visualizing Comparison Results

### Comparison Charts

MicroDetect generates several charts to aid in model comparison:

1. **Radar Charts**: Multi-dimensional comparison of models across key metrics
2. **Bar Charts**: Side-by-side comparison of individual metrics
3. **Line Charts**: Metrics across different confidence thresholds or batch sizes
4. **Scatter Plots**: Trade-off visualization (accuracy vs. speed)

Example visualizations:
- Precision-Recall curves for each model
- mAP vs. model size chart
- Inference time vs. model size
- mAP by class bar chart

### Trade-off Visualization

To understand the performance trade-offs between models:

```bash
microdetect compare_models --model_paths model1.pt,model2.pt,model3.pt --data_yaml dataset/data.yaml --plot_tradeoff
```

This generates a scatter plot showing:
- mAP50 on the Y-axis
- Inference time on the X-axis
- Model size represented by bubble size
- Each model as a point on the plot

This visualization helps you quickly identify models that offer the best balance between accuracy and speed for your needs.

### Detection Comparison

To visually compare detection results from multiple models:

```bash
microdetect compare_detections --model_paths model1.pt,model2.pt,model3.pt --source path/to/images --output_dir comparison_detections
```

This creates visualizations showing:
- Detections from each model with different colored bounding boxes
- Confidence scores for each detection
- Class labels and model identifier
- Overlapping and unique detections

These visualizations help you understand qualitative differences between model outputs.

## Decision Making Framework

When selecting the optimal model, consider the following framework:

1. **Define Requirements**:
   - Accuracy threshold (minimum acceptable mAP)
   - Speed requirements (minimum FPS needed)
   - Resource constraints (memory, compute)
   - Size limitations (for edge deployment)

2. **Prioritize Metrics**:
   - Research applications: Prioritize accuracy (mAP, recall)
   - Real-time applications: Prioritize speed (FPS, latency)
   - Edge deployment: Prioritize model size and efficiency

3. **Evaluate Trade-offs**:
   - Plot mAP vs. inference time to find Pareto-optimal models
   - Calculate efficiency scores (mAP/size or mAP/inference time)
   - Consider class-specific performance for specialized applications

4. **Test in Target Environment**:
   - Validate shortlisted models in actual deployment conditions
   - Measure real-world performance metrics
   - Test with representative data

## Best Practices

1. **Use consistent evaluation settings**: Compare models using the same confidence threshold, IoU threshold, and test dataset

2. **Perform multiple runs**: Average results from multiple evaluation runs for reliable comparisons

3. **Test on diverse samples**: Use a representative test set that covers various conditions and edge cases

4. **Consider domain-specific metrics**: For microorganism detection, class-specific metrics may be more important than overall metrics

5. **Document comparison conditions**: Record hardware, software versions, and specific settings for reproducibility

6. **Match test environment to deployment**: Evaluate models in conditions similar to your intended deployment environment

7. **Compare against baselines**: Include established models as baselines in your comparison

## Troubleshooting

**Problem**: Large disparity in metrics between models
**Solution**: Verify that all models were trained on similar data; check for overfitting in high-performance models

**Problem**: Inconsistent speed measurements
**Solution**: Ensure that hardware conditions are consistent; use more iterations with warmup periods

**Problem**: Dashboard fails to load
**Solution**: Check if required dependencies are installed (`pip install dash dash-bootstrap-components plotly`)

**Problem**: Error when comparing models with different classes
**Solution**: Ensure all models have compatible class configurations; use `--force_merge_classes` option

**Problem**: Memory issues when comparing multiple large models
**Solution**: Compare models sequentially rather than simultaneously; reduce batch size; use CPU mode if VRAM is limited

**Problem**: Detection comparison visualizations too cluttered
**Solution**: Reduce the number of models being compared at once; increase confidence threshold; compare on simpler images

For more detailed troubleshooting, see the [Troubleshooting Guide](troubleshooting.md).