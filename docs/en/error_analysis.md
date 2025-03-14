# Error Analysis Guide

This guide explains how to use MicroDetect's error analysis capabilities to identify and understand detection errors.

## Table of Contents
- [Introduction](#introduction)
- [Types of Detection Errors](#types-of-detection-errors)
- [Using the Error Analysis Tool](#using-the-error-analysis-tool)
- [Analyzing Error Visualizations](#analyzing-error-visualizations)
- [Understanding Error Distributions](#understanding-error-distributions)
- [Improving Model Performance](#improving-model-performance)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)

## Introduction

Error analysis is a critical step in refining object detection models. It helps you understand:

- Where and why your model fails
- Which types of errors are most common
- How to improve your model's performance
- What data augmentation might be beneficial

MicroDetect provides comprehensive tools to analyze different types of detection errors, visualize them, and generate actionable insights.

## Types of Detection Errors

MicroDetect identifies and analyzes four main types of detection errors:

1. **False Positives**: Detections that don't correspond to actual objects
   - The model detects something that isn't there
   - Often occurs with background features that resemble microorganisms

2. **False Negatives**: Objects that the model fails to detect
   - The model misses objects that are present in the image
   - Common with small, blurry, or partially visible microorganisms

3. **Classification Errors**: Correct detection but wrong class
   - The model detects an object but assigns the wrong class
   - Common with similar-looking microorganism types

4. **Localization Errors**: Objects detected but with poor bounding box accuracy
   - The model detects the object but doesn't accurately define its boundaries
   - IoU (Intersection over Union) is below optimal threshold but still above detection threshold

## Using the Error Analysis Tool

### Basic Usage

```bash
microdetect analyze_errors --model_path runs/train/exp/weights/best.pt \
                          --data_yaml dataset/data.yaml \
                          --dataset_dir dataset
```

This command analyzes all types of errors on the test set and generates visualizations.

### Focusing on Specific Error Types

```bash
microdetect analyze_errors --model_path runs/train/exp/weights/best.pt \
                          --data_yaml dataset/data.yaml \
                          --dataset_dir dataset \
                          --error_type false_positives
```

Valid error types:
- `all` - Analyze all types of errors (default)
- `false_positives` - Focus on false positive detections
- `false_negatives` - Focus on missed objects
- `classification_errors` - Focus on correct detections with wrong class
- `localization_errors` - Focus on detections with poor bounding box accuracy

### Additional Options

```bash
microdetect analyze_errors --model_path runs/train/exp/weights/best.pt \
                          --data_yaml dataset/data.yaml \
                          --dataset_dir dataset \
                          --output_dir error_analysis \
                          --conf_threshold 0.3 \
                          --iou_threshold 0.5 \
                          --max_samples 30
```

- `--output_dir`: Directory to save error analysis results (default: error_analysis)
- `--conf_threshold`: Confidence threshold for detections (default: 0.25)
- `--iou_threshold`: IoU threshold for matching detections to ground truth (default: 0.5)
- `--max_samples`: Maximum number of examples to save for each error type (default: 20)

## Analyzing Error Visualizations

The error analysis tool generates visualizations for each type of error. These visualizations show:

1. **False Positives**: Red bounding boxes showing detections without corresponding ground truth 
   - Format: "FP: [class_name] ([confidence])"
   
2. **False Negatives**: Green bounding boxes showing ground truth that was missed
   - Format: "FN: [class_name]"
   
3. **Classification Errors**: Blue bounding boxes showing misclassified detections
   - Format: "CE: [detected_class] (GT: [ground_truth_class])"
   
4. **Localization Errors**: Cyan bounding boxes showing detections with poor localization
   - Format: "LE: IoU=[iou_value]"
   - Also shows ground truth in thin green outline

The visualizations are saved in the output directory, organized by error type:
```
error_analysis/
├── false_positives/
├── false_negatives/
├── classification_errors/
├── localization_errors/
├── error_analysis_report.json
└── error_summary.png
```

## Understanding Error Distributions

The tool also generates an error summary chart (`error_summary.png`) showing the distribution of different error types.

This bar chart helps you understand:
- Which error types are most common
- The relative proportions of different errors
- Total error count

The error analysis report (`error_analysis_report.json`) contains detailed statistics about the errors:

```json
{
  "model": "yolov8s_custom.pt",
  "conf_threshold": 0.25,
  "iou_threshold": 0.5,
  "images_analyzed": 50,
  "error_counts": {
    "false_positives": 24,
    "false_negatives": 18,
    "classification_errors": 7,
    "localization_errors": 12
  },
  "error_examples": {
    "false_positives": 20,
    "false_negatives": 18,
    "classification_errors": 7,
    "localization_errors": 12
  }
}
```

## Improving Model Performance

Based on error analysis, you can take the following actions to improve your model:

### For False Positives:
- Increase the confidence threshold
- Add more negative examples (images without microorganisms)
- Add hard negatives (background features that resemble microorganisms)
- Review annotation quality for potential errors

### For False Negatives:
- Decrease the confidence threshold (but watch for increasing false positives)
- Add more training data for underrepresented cases
- Use data augmentation techniques to increase variation
- Consider using a model with more capacity

### For Classification Errors:
- Add more training data for confused classes
- Ensure annotation guidelines are clear for similar classes
- Consider merging very similar classes if distinction isn't critical
- Use specialized data augmentation for difficult classes

### For Localization Errors:
- Review annotation guidelines for consistency in bounding box placement
- Consider using a larger model with better localization capabilities
- Add more training examples for objects with difficult boundaries
- Train for more epochs to improve precision

## Best Practices

1. **Start with balanced analysis**: First analyze all error types to get a complete picture

2. **Focus on the most common errors**: Address the error types with the highest counts first

3. **Look for patterns**: Analyze multiple examples to identify patterns in errors
   - Are false positives more common in certain image regions?
   - Are false negatives associated with smaller objects?
   - Are classification errors occurring between specific classes?

4. **Iterate methodically**: Make one change at a time and evaluate its impact

5. **Combine with other analysis**: Use alongside other tools like:
   - Model comparison (`microdetect compare_models`)
   - Statistical analysis (`microdetect analyze_distribution`)
   - Performance benchmarking

## Troubleshooting

### Issue: No errors found despite poor model performance
**Solution**: Check test dataset paths and annotation formats; try lowering confidence threshold

### Issue: Too many localization errors
**Solution**: Review annotation consistency; consider retraining with more focus on bounding box accuracy

### Issue: Error analysis is very slow
**Solution**: Reduce the test dataset size or use the `--max_samples` parameter to limit examples

### Issue: Memory issues during analysis
**Solution**: Process fewer images at a time with a smaller batch size

For more troubleshooting information, see the [Troubleshooting Guide](troubleshooting.md).