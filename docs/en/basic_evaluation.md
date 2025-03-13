# Basic Evaluation Guide

This guide explains the fundamental methods for evaluating models in MicroDetect, providing an introduction to model assessment before diving into more advanced evaluation techniques.

## Table of Contents
- [Introduction](#introduction)
- [Basic Model Evaluation](#basic-model-evaluation)
  - [Evaluating a Trained Model](#evaluating-a-trained-model)
  - [Understanding Evaluation Metrics](#understanding-evaluation-metrics)
  - [Interpreting Results](#interpreting-results)
- [Validation During Training](#validation-during-training)
  - [Validation Metrics](#validation-metrics)
  - [Learning Curves](#learning-curves)
- [Testing on New Images](#testing-on-new-images)
  - [Single Image Testing](#single-image-testing)
  - [Batch Testing](#batch-testing)
- [Adjusting Detection Parameters](#adjusting-detection-parameters)
  - [Confidence Threshold](#confidence-threshold)
  - [IoU Threshold](#iou-threshold)
- [Saving and Exporting Results](#saving-and-exporting-results)
- [Next Steps](#next-steps)

## Introduction

Model evaluation is a critical step in developing effective microorganism detection systems. It helps you understand:

- How well your model is performing
- Whether it's ready for practical use
- What areas need improvement

MicroDetect provides several tools for basic model evaluation that don't require advanced statistical knowledge but still provide valuable insights into model performance.

## Basic Model Evaluation

### Evaluating a Trained Model

To evaluate a trained model on a test dataset:

```bash
microdetect evaluate --model_path runs/train/exp/weights/best.pt --dataset_dir dataset
```

Required parameters:
- `--model_path`: Path to the trained model file (.pt)
- `--dataset_dir`: Directory containing the dataset with test images and labels

Optional parameters:
- `--conf_threshold`: Confidence threshold for detections (default: 0.25)
- `--iou_threshold`: IoU threshold for Non-Maximum Suppression (default: 0.7)
- `--batch_size`: Number of images to process at once (default: 16)

This command generates a comprehensive evaluation report in the console and saves detailed results in the model's directory.

### Understanding Evaluation Metrics

The basic evaluation provides the following key metrics:

1. **Precision**: The proportion of detections that are correct (true positives divided by all detections)
   - Higher precision means fewer false positives
   - Range: 0 to 1 (higher is better)

2. **Recall**: The proportion of actual microorganisms that were detected (true positives divided by all actual objects)
   - Higher recall means fewer false negatives (missed detections)
   - Range: 0 to 1 (higher is better)

3. **mAP50**: Mean Average Precision at IoU threshold of 0.5
   - Overall measure of detection quality, balancing precision and recall
   - Range: 0 to 1 (higher is better)

4. **F1-Score**: Harmonic mean of precision and recall
   - Single metric balancing precision and recall
   - Range: 0 to 1 (higher is better)

Example output:
```
Class         Images    Labels  Precision   Recall   mAP50  F1
All           50        230     0.962       0.921    0.947   0.941
Class 0       50        98      0.981       0.934    0.972   0.957
Class 1       50        87      0.953       0.932    0.943   0.942
Class 2       50        45      0.951       0.897    0.925   0.923
```

### Interpreting Results

How to interpret basic evaluation results:

- **Good performance**: Generally, mAP50 > 0.8 indicates good performance for microorganism detection
- **Balanced precision and recall**: Ideally, both precision and recall should be high
- **Class imbalance**: Check if performance varies significantly between classes
- **Common issues**:
  - High precision but low recall: Model is missing detections (conservative)
  - High recall but low precision: Model has many false positives (too permissive)
  - Both low: Model needs improvement or retraining

## Validation During Training

### Validation Metrics

During training, MicroDetect automatically validates the model on the validation dataset at regular intervals. These metrics are saved in:

```
runs/train/exp/results.csv
```

This file contains per-epoch metrics including:
- Validation mAP50
- Validation precision
- Validation recall
- Training loss components (box loss, class loss)

### Learning Curves

To visualize learning curves from the training:

```bash
microdetect plot_metrics --logdir runs/train/exp
```

This generates plots showing:
- Training and validation metrics over time
- Loss curves
- Precision and recall development
- Learning rate schedule

These plots help you identify:
- Whether the model has converged
- If the model is overfitting (training metrics improve while validation metrics worsen)
- Optimal training duration
- Effect of learning rate changes

## Testing on New Images

### Single Image Testing

To test your model on a single image:

```bash
microdetect detect --model_path runs/train/exp/weights/best.pt --source path/to/image.jpg
```

This runs inference on the image and displays/saves the result with detected microorganisms.

### Batch Testing

To test on multiple images:

```bash
microdetect detect --model_path runs/train/exp/weights/best.pt --source path/to/images
```

Options:
- `--save_txt`: Save detections in YOLO format
- `--save_conf`: Include confidence scores in saved results
- `--save_crop`: Save cropped images of detected microorganisms
- `--hide_labels`: Hide class labels on output images
- `--hide_conf`: Hide confidence scores on output images

## Adjusting Detection Parameters

### Confidence Threshold

The confidence threshold controls how confident the model must be to report a detection:

```bash
microdetect detect --model_path runs/train/exp/weights/best.pt --source path/to/images --conf_threshold 0.4
```

- **Lower threshold** (e.g., 0.1): More detections, including more false positives
- **Higher threshold** (e.g., 0.7): Fewer detections, but higher confidence

Finding the optimal threshold:
- Start with the default (0.25)
- Increase if you see too many false positives
- Decrease if you're missing detections you want to catch

### IoU Threshold

The IoU (Intersection over Union) threshold controls how much overlap detections need to have to be considered duplicates:

```bash
microdetect detect --model_path runs/train/exp/weights/best.pt --source path/to/images --iou_threshold 0.5
```

- **Lower threshold** (e.g., 0.3): More aggressive at removing overlapping boxes
- **Higher threshold** (e.g., 0.7): More permissive with overlapping detections

This parameter is especially important for densely packed microorganisms.

## Saving and Exporting Results

To save evaluation results for further analysis:

```bash
microdetect evaluate --model_path runs/train/exp/weights/best.pt --dataset_dir dataset --save_json
```

This saves results in a JSON file that includes:
- Overall metrics
- Per-class metrics
- Evaluation parameters
- Performance statistics

You can also export results in different formats:

```bash
# Export as CSV
microdetect evaluate --model_path runs/train/exp/weights/best.pt --dataset_dir dataset --format csv --output_file results.csv

# Generate HTML report
microdetect evaluate --model_path runs/train/exp/weights/best.pt --dataset_dir dataset --format html --output_file report.html
```

## Next Steps

After basic evaluation, consider these next steps:

1. **Advanced evaluation**: For deeper insights, see the [Model Evaluation and Analysis Guide](model_evaluation_analysis.md)

2. **Error analysis**: To understand model weaknesses, see the [Error Analysis Guide](error_analysis.md)

3. **Model comparison**: To compare different models, see the [Model Comparison Guide](model_comparison.md)

4. **Model optimization**: If performance is insufficient, try:
   - Collecting more training data
   - Improving annotation quality
   - Using a larger model (from nano to small, medium, or large)
   - Adjusting training hyperparameters

5. **Statistical analysis**: For analyzing detection patterns, see the [Statistical Analysis Guide](statistical_analysis.md)