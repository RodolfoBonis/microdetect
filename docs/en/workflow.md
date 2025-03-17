# Documentation: Complete Workflow with MicroDetect

## Overview

This document describes the complete workflow for using the MicroDetect framework for microorganism detection with YOLOv8, from initial data preparation to generating reports and dashboards for presenting results.

## Prerequisites

- MicroDetect installed and configured
- Python 3.8+ with dependencies installed
- Access to microorganism images
- GPU recommended for training (optional, but desirable)

## 1. Environment and Data Preparation

### 1.1 Project Initialization

```bash
microdetect init --project project_name
```

**Description**: This command creates the base directory structure for the project, including folders for datasets, models, results, and reports. It also sets up initial configuration files.

**Parameters**:
- `--project`: Name of the project/directory to be created

### 1.2 Image Conversion

```bash
microdetect convert --source path/to/images --format yolo --output datasets/raw
```

**Description**: Converts images from the original format to a standardized format compatible with the YOLO training and annotation pipeline.

**Parameters**:
- `--source`: Directory containing the original images
- `--format`: Desired output format (usually 'yolo')
- `--output`: Destination directory for the converted images

### 1.3 Image Annotation

```bash
microdetect annotate --images datasets/raw/images --output datasets/raw/labels
```

**Description**: Opens the annotation interface to manually mark objects in the images. This step is only necessary if the images are not already annotated.

**Parameters**:
- `--images`: Directory containing the images to be annotated
- `--output`: Directory where annotations will be saved

## 2. Dataset Organization and Augmentation

### 2.1 Data Augmentation

```bash
microdetect augment --images datasets/raw/images --labels datasets/raw/labels --output datasets/augmented --factor 3 --techniques flip,rotate,brightness
```

**Description**: Applies data augmentation techniques to expand the training set, improving the model's generalization capability.

**Parameters**:
- `--images`: Path to original images
- `--labels`: Path to original annotations
- `--output`: Directory to save augmented images and annotations
- `--factor`: Dataset multiplication factor (3 = final size 3x larger)
- `--techniques`: List of augmentation techniques to be applied

### 2.2 Dataset Organization

```bash
microdetect dataset --source datasets/augmented --output datasets/final --split 70,20,10
```

**Description**: Organizes the dataset into training, validation, and test sets, applying the specified division.

**Parameters**:
- `--source`: Directory containing the augmented dataset
- `--output`: Directory for the final organized dataset
- `--split`: Proportion of train/validation/test split in percentage

## 3. Model Training

### 3.1 Base Model Training

```bash
microdetect train --data datasets/final/data.yaml --model yolov8n.pt --epochs 100 --batch 16 --name base_model --img 640 --patience 20
```

**Description**: Trains a YOLOv8 nano model using the prepared dataset.

**Parameters**:
- `--data`: YAML file describing the dataset
- `--model`: Pre-trained base model for fine-tuning
- `--epochs`: Number of training epochs
- `--batch`: Batch size
- `--name`: Experiment name
- `--img`: Training image resolution
- `--patience`: Number of epochs for early stopping

### 3.2 Training Variant Models

```bash
microdetect train --data datasets/final/data.yaml --model yolov8s.pt --epochs 100 --batch 16 --name medium_model --img 640 --patience 20
```

```bash
microdetect train --data datasets/final/data.yaml --model yolov8m.pt --epochs 100 --batch 8 --name large_model --img 640 --patience 20
```

**Description**: Trains YOLOv8 variant models (small and medium) to enable performance comparison between different model sizes.

## 4. Model Evaluation and Comparison

### 4.1 Individual Model Evaluation

```bash
microdetect evaluate --model runs/train/base_model/weights/best.pt --data datasets/final/data.yaml --batch 16 --output_dir reports/evaluation/base_model
```

**Description**: Evaluates the performance of the trained model on the test set, generating detailed metrics.

**Parameters**:
- `--model`: Path to the model weights file
- `--data`: Dataset YAML file
- `--batch`: Batch size for evaluation
- `--output_dir`: Directory to save evaluation results

### 4.2 Multiple Model Comparison

```bash
microdetect compare_models --model_paths runs/train/base_model/weights/best.pt,runs/train/medium_model/weights/best.pt,runs/train/large_model/weights/best.pt --data_yaml datasets/final/data.yaml --output_dir reports/model_comparison --conf_threshold 0.25 --iou_threshold 0.45 --dashboard
```

**Description**: Compares the different trained models, generating comparative tables and graphs of performance metrics.

**Parameters**:
- `--model_paths`: Comma-separated list of paths to the models to be compared
- `--data_yaml`: Dataset YAML file
- `--output_dir`: Directory to save comparison results
- `--conf_threshold`: Confidence threshold for detections
- `--iou_threshold`: IoU threshold for evaluation
- `--dashboard`: Generates an interactive dashboard with comparison results

### 4.3 Error Analysis

```bash
microdetect analyze_errors --model_path runs/train/medium_model/weights/best.pt --data_yaml datasets/final/data.yaml --dataset_dir datasets/final/test --error_type all --output_dir reports/error_analysis
```

**Description**: Analyzes different types of errors made by the model, categorizing them and providing visual examples.

**Parameters**:
- `--model_path`: Path to the model weights file
- `--data_yaml`: Dataset YAML file
- `--dataset_dir`: Directory containing the test set
- `--error_type`: Type of error to analyze ('false_positives', 'false_negatives', 'classification', 'localization', or 'all')
- `--output_dir`: Directory to save analysis results

## 5. Image Processing and Visualization

### 5.1 Batch Detection

```bash
microdetect batch_detect --model_path runs/train/medium_model/weights/best.pt --source datasets/final/test/images --output_dir results/batch_detections --conf_threshold 0.25 --batch_size 16 --save_txt --save_img --save_json
```

**Description**: Processes a set of images with the trained model, generating visualizations and detection files.

**Parameters**:
- `--model_path`: Path to the model weights file
- `--source`: Directory containing the images to be processed
- `--output_dir`: Directory to save results
- `--conf_threshold`: Confidence threshold for detections
- `--batch_size`: Batch size for processing
- `--save_txt`: Saves detections in text format (YOLO)
- `--save_img`: Saves images with drawn detections
- `--save_json`: Saves detections in JSON format

### 5.2 Interactive Detection Visualization

```bash
microdetect visualize_detections --model_path runs/train/medium_model/weights/best.pt --source results/batch_detections/images --conf_threshold 0.25
```

**Description**: Opens an interactive interface to visualize and explore the detections made by the model.

**Parameters**:
- `--model_path`: Path to the model weights file
- `--source`: Directory containing the images to be visualized
- `--conf_threshold`: Confidence threshold for detections

## 6. Report and Dashboard Generation

### 6.1 Report Generation

```bash
microdetect generate_report --results_dir reports/model_comparison --format pdf --output_file thesis_results.pdf --include_images results/batch_detections/images/example1.jpg,results/batch_detections/images/example2.jpg
```

**Description**: Generates a complete PDF report containing metrics, graphs, and detection examples.

**Parameters**:
- `--results_dir`: Directory containing evaluation/comparison results
- `--format`: Report format ('pdf', 'csv', 'json')
- `--output_file`: Path to the output file
- `--include_images`: Comma-separated list of images to include in the report

### 6.2 Dashboard Creation

```bash
microdetect dashboard --results_dir reports/model_comparison --port 8050 --no_browser
```

**Description**: Creates an interactive web dashboard to explore detection and evaluation results.

**Parameters**:
- `--results_dir`: Directory containing the results to be visualized
- `--port`: Port to serve the dashboard (default: 8050)
- `--no_browser`: Does not automatically open the browser

## Complete Workflow (Script)

To automate the complete process, you can create a script with all commands in sequence:

```bash
#!/bin/bash

# 1. Environment and data preparation
microdetect init --project thesis_microdetect
microdetect convert --source original_images/ --format yolo --output datasets/raw

# Manual step: image annotation (if necessary)
# microdetect annotate --images datasets/raw/images --output datasets/raw/labels

# 2. Dataset organization and augmentation
microdetect augment --images datasets/raw/images --labels datasets/raw/labels --output datasets/augmented --factor 3 --techniques flip,rotate,brightness
microdetect dataset --source datasets/augmented --output datasets/final --split 70,20,10

# 3. Model training
microdetect train --data datasets/final/data.yaml --model yolov8n.pt --epochs 100 --batch 16 --name base_model
microdetect train --data datasets/final/data.yaml --model yolov8s.pt --epochs 100 --batch 16 --name medium_model
microdetect train --data datasets/final/data.yaml --model yolov8m.pt --epochs 100 --batch 8 --name large_model

# 4. Evaluation and comparison
microdetect evaluate --model runs/train/base_model/weights/best.pt --data datasets/final/data.yaml --output_dir reports/evaluation/base_model
microdetect evaluate --model runs/train/medium_model/weights/best.pt --data datasets/final/data.yaml --output_dir reports/evaluation/medium_model
microdetect evaluate --model runs/train/large_model/weights/best.pt --data datasets/final/data.yaml --output_dir reports/evaluation/large_model

microdetect compare_models --model_paths runs/train/base_model/weights/best.pt,runs/train/medium_model/weights/best.pt,runs/train/large_model/weights/best.pt --data_yaml datasets/final/data.yaml --output_dir reports/model_comparison --dashboard

microdetect analyze_errors --model_path runs/train/medium_model/weights/best.pt --data_yaml datasets/final/data.yaml --dataset_dir datasets/final/test --output_dir reports/error_analysis

# 5. Processing and visualization
microdetect batch_detect --model_path runs/train/medium_model/weights/best.pt --source datasets/final/test/images --output_dir results/batch_detections --save_txt --save_img --save_json

# 6. Report and dashboard
microdetect generate_report --results_dir reports/model_comparison --format pdf --output_file thesis_results.pdf
microdetect dashboard --results_dir reports/model_comparison
```

## Final Considerations

- Choose the best model based on metric comparison and requirements (speed vs. accuracy)
- Include visual examples of model successes and failures in the final report
- Document all choices and experiments made during development
- Keep metrics and results files organized to facilitate thesis writing
- For presentations, the interactive dashboard offers a dynamic way to show results

## Recommended Reading

- Official YOLOv8 documentation
- Articles on object detection techniques in microscopic images
- Guides on interpreting evaluation metrics for object detection models