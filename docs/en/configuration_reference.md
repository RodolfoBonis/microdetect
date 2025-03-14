# Configuration Reference

This document provides a complete reference for all configuration options available in MicroDetect's `config.yaml` file, detailing each parameter and its usage.

## Table of Contents
- [Introduction](#introduction)
- [Configuration File Structure](#configuration-file-structure)
- [Directories Configuration](#directories-configuration)
- [Classes Configuration](#classes-configuration)
- [Color Mapping](#color-mapping)
- [Training Configuration](#training-configuration)
- [Dataset Configuration](#dataset-configuration)
- [Data Augmentation Configuration](#data-augmentation-configuration)
- [Evaluation Configuration](#evaluation-configuration)
- [Image Conversion Configuration](#image-conversion-configuration)
- [Annotation Configuration](#annotation-configuration)
- [AWS CodeArtifact Configuration](#aws-codeartifact-configuration)
- [Logging Configuration](#logging-configuration)
- [Cache Configuration](#cache-configuration)
- [Inference Configuration](#inference-configuration)

## Introduction

MicroDetect uses a YAML configuration file (`config.yaml`) to centralize settings and parameters. This file is automatically created when you run `microdetect init` and can be manually edited to customize the behavior of various components.

The configuration file is loaded from the following locations, in order of priority:
1. Path specified manually in commands
2. Current directory (`./config.yaml`)
3. User directory (`~/.microdetect/config.yaml`)
4. Internal default package configuration

## Configuration File Structure

The complete structure of `config.yaml` with all available options is described below:

```yaml
# Directories
directories:
  dataset: ./dataset              # Directory for structured dataset
  images: ./data/images           # Directory for original images
  labels: ./data/labels           # Directory for annotations
  output: ./runs/train            # Directory for training results
  reports: ./reports              # Directory for reports
  cache: ~/.cache/microdetect     # Cache directory

# Classes for detection
classes:
  - "0-levedura"                  # Format: "ID-name"
  - "1-fungo"
  - "2-micro-alga"
  # Add more classes as needed

# Color mapping for visualization
color_map:
  "0": [0, 255, 0]                # Green for yeasts (RGB format)
  "1": [0, 0, 255]                # Red for fungi
  "2": [255, 0, 0]                # Blue for micro-algae
  # Add colors for additional classes

# Training parameters
training:
  model_size: s                   # Model size (n, s, m, l, x)
  epochs: 100                     # Number of epochs
  batch_size: 32                  # Batch size
  image_size: 640                 # Image size
  pretrained: true                # Use pretrained weights
  patience: 20                    # Patience for early stopping
  optimizer: AdamW                # Optimizer (SGD, Adam, AdamW)
  lr0: 0.01                       # Initial learning rate
  lrf: 0.01                       # Final learning rate
  momentum: 0.937                 # Momentum for SGD
  weight_decay: 0.0005            # Weight decay
  warmup_epochs: 3                # Warmup epochs
  warmup_momentum: 0.8            # Momentum during warmup
  warmup_bias_lr: 0.1             # Bias learning rate during warmup
  box: 7.5                        # Box loss weight
  cls: 0.5                        # Class loss weight
  dfl: 1.5                        # DFL loss weight
  fl_gamma: 0.0                   # Focal loss gamma
  workers: 8                      # Number of workers for data loading
  cos_lr: true                    # Use cosine learning rate

# Dataset parameters
dataset:
  train_ratio: 0.7                # Training proportion
  val_ratio: 0.15                 # Validation proportion
  test_ratio: 0.15                # Test proportion
  seed: 42                        # Seed for reproducibility
  cache: true                     # Cache images in RAM
  rect: false                     # Use rectangular crops
  mosaic: 1.0                     # Mosaic probability
  mixup: 0.5                      # Mixup probability
  copy_images: true               # Copy images to dataset directory

# Data augmentation parameters
augmentation:
  factor: 20                      # Number of images to generate per original
  brightness_range: [0.8, 1.2]    # Brightness range (min, max)
  contrast_range: [-30, 30]       # Contrast range (min, max)
  flip_probability: 0.5           # Horizontal flip probability
  rotation_range: [-15, 15]       # Rotation range (min, max)
  noise_probability: 0.3          # Noise probability
  blur_probability: 0.2           # Blur probability
  cutout_probability: 0.2         # Cutout probability
  cutout_size: [0.05, 0.2]        # Cutout size (min%, max%)
  hue_shift: 0.1                  # Hue shift
  saturation_shift: 0.1           # Saturation shift

# Evaluation parameters
evaluation:
  conf_threshold: 0.25            # Confidence threshold
  iou_threshold: 0.45             # IoU threshold
  max_detections: 300             # Maximum detections
  save_confusion_matrix: true     # Save confusion matrix
  save_json: true                 # Save results as JSON
  verbose: true                   # Detailed output
  plots: true                     # Generate plots

# Image conversion parameters
conversion:
  format: png                     # Target format (png, jpg)
  quality: 95                     # Quality for JPG
  use_opencv: true                # Use OpenCV instead of PIL
  delete_original: false          # Delete original file after conversion
  preserve_metadata: true         # Preserve EXIF metadata
  resize: false                   # Resize images
  max_size: [1024, 1024]          # Maximum size after resizing

# Annotation parameters
annotation:
  box_thickness: 2                # Box thickness
  text_size: 0.5                  # Text size
  auto_save: true                 # Auto-save annotations
  auto_save_interval: 300         # Auto-save interval (seconds)
  undo_levels: 10                 # Undo levels

# AWS CodeArtifact parameters
aws:
  domain: your-domain             # CodeArtifact domain name
  repository: your-repository     # Repository name
  region: us-east-1               # AWS region
  auto_check: true                # Check for updates automatically
  check_interval: 86400           # Check interval (seconds)

# Logging configuration
logging:
  level: INFO                     # Logging level (DEBUG, INFO, WARNING, ERROR)
  file: microdetect.log           # Log file
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"  # Format
  max_size: 10485760              # Maximum log file size (10MB)
  backup_count: 3                 # Number of backups

# Cache configuration
caching:
  enabled: true                   # Enable caching
  directory: ~/.cache/microdetect  # Cache directory
  max_size_gb: 10                 # Maximum cache size (GB)
  ttl: 604800                     # TTL in seconds (7 days)
  compression: true               # Use compression

# Inference configuration
inference:
  conf_threshold: 0.25            # Confidence threshold for detection
  iou_threshold: 0.45             # IoU threshold for NMS
  max_detections: 300             # Maximum number of detections
  agnostic_nms: false             # Class-agnostic NMS
  show_labels: true               # Show labels
  show_conf: true                 # Show confidence
  save_crops: false               # Save detection crops
  hide_conf: false                # Hide confidence value
  hide_labels: false              # Hide labels
  half: false                     # Use mixed precision (FP16)
```

## Directories Configuration

The `directories` section defines default paths used by MicroDetect:

| Parameter | Description | Default |
|-----------|-------------|---------|
| `dataset` | Directory for the structured dataset | `./dataset` |
| `images` | Directory for original images | `./data/images` |
| `labels` | Directory for annotations | `./data/labels` |
| `output` | Directory for training results | `./runs/train` |
| `reports` | Directory for generated reports | `./reports` |
| `cache` | Directory for cached files | `~/.cache/microdetect` |

## Classes Configuration

The `classes` section defines the microorganism classes to detect:

```yaml
classes:
  - "0-levedura"                  # Format: "ID-name"
  - "1-fungo"
  - "2-micro-alga"
```

Each class is defined in the format `"ID-name"` where:
- `ID` is a numeric identifier starting from 0
- `name` is a descriptive name for the class

## Color Mapping

The `color_map` section defines RGB colors for visualizing each class:

```yaml
color_map:
  "0": [0, 255, 0]                # Green for yeasts
  "1": [0, 0, 255]                # Red for fungi
  "2": [255, 0, 0]                # Blue for micro-algae
```

Each entry maps a class ID to an RGB color (red, green, blue) with values from 0 to 255.

## Training Configuration

The `training` section controls model training parameters:

| Parameter | Description | Default |
|-----------|-------------|---------|
| `model_size` | YOLOv8 model size (n, s, m, l, x) | `s` |
| `epochs` | Number of training epochs | `100` |
| `batch_size` | Training batch size | `32` |
| `image_size` | Training image size (pixels) | `640` |
| `pretrained` | Use pretrained weights | `true` |
| `patience` | Epochs without improvement before early stopping | `20` |
| `optimizer` | Optimization algorithm (SGD, Adam, AdamW) | `AdamW` |
| `lr0` | Initial learning rate | `0.01` |
| `lrf` | Final learning rate factor | `0.01` |
| `momentum` | Momentum for SGD optimizer | `0.937` |
| `weight_decay` | Weight decay (L2 regularization) | `0.0005` |
| `warmup_epochs` | Epochs for learning rate warmup | `3` |
| `warmup_momentum` | Initial momentum during warmup | `0.8` |
| `warmup_bias_lr` | Initial learning rate for bias during warmup | `0.1` |
| `box` | Box loss weight | `7.5` |
| `cls` | Class loss weight | `0.5` |
| `dfl` | Distribution focal loss weight | `1.5` |
| `fl_gamma` | Focal loss gamma | `0.0` |
| `workers` | Number of data loading workers | `8` |
| `cos_lr` | Use cosine learning rate schedule | `true` |

## Dataset Configuration

The `dataset` section controls dataset splitting and processing:

| Parameter | Description | Default |
|-----------|-------------|---------|
| `train_ratio` | Proportion of data for training | `0.7` |
| `val_ratio` | Proportion of data for validation | `0.15` |
| `test_ratio` | Proportion of data for testing | `0.15` |
| `seed` | Random seed for reproducible splits | `42` |
| `cache` | Cache images in RAM during training | `true` |
| `rect` | Use rectangular training (maintains aspect ratio) | `false` |
| `mosaic` | Mosaic augmentation probability | `1.0` |
| `mixup` | Mixup augmentation probability | `0.5` |
| `copy_images` | Copy images to dataset directory | `true` |

## Data Augmentation Configuration

The `augmentation` section controls data augmentation parameters:

| Parameter | Description | Default |
|-----------|-------------|---------|
| `factor` | Number of augmented images per original | `20` |
| `brightness_range` | Brightness adjustment range [min, max] | `[0.8, 1.2]` |
| `contrast_range` | Contrast adjustment range [min, max] | `[-30, 30]` |
| `flip_probability` | Horizontal flip probability | `0.5` |
| `rotation_range` | Rotation range in degrees [min, max] | `[-15, 15]` |
| `noise_probability` | Probability of adding noise | `0.3` |
| `blur_probability` | Probability of applying blur | `0.2` |
| `cutout_probability` | Probability of applying cutout | `0.2` |
| `cutout_size` | Cutout size range as fraction [min, max] | `[0.05, 0.2]` |
| `hue_shift` | Maximum hue shift | `0.1` |
| `saturation_shift` | Maximum saturation shift | `0.1` |

## Evaluation Configuration

The `evaluation` section controls model evaluation parameters:

| Parameter | Description | Default |
|-----------|-------------|---------|
| `conf_threshold` | Confidence threshold for detections | `0.25` |
| `iou_threshold` | IoU threshold for matching | `0.45` |
| `max_detections` | Maximum detections per image | `300` |
| `save_confusion_matrix` | Generate and save confusion matrix | `true` |
| `save_json` | Save results as JSON | `true` |
| `verbose` | Show detailed output | `true` |
| `plots` | Generate evaluation plots | `true` |

## Image Conversion Configuration

The `conversion` section controls image conversion parameters:

| Parameter | Description | Default |
|-----------|-------------|---------|
| `format` | Target image format (png, jpg) | `png` |
| `quality` | JPG quality setting (1-100) | `95` |
| `use_opencv` | Use OpenCV instead of PIL | `true` |
| `delete_original` | Delete original file after conversion | `false` |
| `preserve_metadata` | Preserve EXIF metadata | `true` |
| `resize` | Resize images during conversion | `false` |
| `max_size` | Maximum dimensions after resizing [width, height] | `[1024, 1024]` |

## Annotation Configuration

The `annotation` section controls annotation tool parameters:

| Parameter | Description | Default |
|-----------|-------------|---------|
| `box_thickness` | Bounding box line thickness | `2` |
| `text_size` | Text size for labels | `0.5` |
| `auto_save` | Enable automatic saving of annotations | `true` |
| `auto_save_interval` | Seconds between auto-saves | `300` |
| `undo_levels` | Number of undo operations supported | `10` |

## AWS CodeArtifact Configuration

The `aws` section controls AWS CodeArtifact integration for updates:

| Parameter | Description | Default |
|-----------|-------------|---------|
| `domain` | AWS CodeArtifact domain name | `your-domain` |
| `repository` | AWS CodeArtifact repository name | `your-repository` |
| `region` | AWS region | `us-east-1` |
| `auto_check` | Automatically check for updates | `true` |
| `check_interval` | Update check interval in seconds | `86400` (1 day) |

## Logging Configuration

The `logging` section controls logging behavior:

| Parameter      | Description                                 | Default                                                |
|----------------|---------------------------------------------|--------------------------------------------------------|
| `level`        | Logging level (DEBUG, INFO, WARNING, ERROR) | `INFO`                                                 |
| `file`         | Log file path                               | `microdetect.log`                                      |
| `format`       | Log message format                          | `%(asctime)s - %(name)s - %(levelname)s - %(message)s` |
| `max_size`     | Maximum log file size in bytes              | `10485760` (10MB)                                      |
| `backup_count` | Number of log backups to keep               | `3`                                                    |

## Cache Configuration

The `caching` section controls caching behavior:

| Parameter     | Description                             | Default                |
|---------------|-----------------------------------------|------------------------|
| `enabled`     | Enable caching                          | `true`                 |
| `directory`   | Cache directory                         | `~/.cache/microdetect` |
| `max_size_gb` | Maximum cache size in GB                | `10`                   |
| `ttl`         | Time-to-live for cache items in seconds | `604800` (7 days)      |
| `compression` | Use compression for cached items        | `true`                 |

## Inference Configuration

The `inference` section controls the behavior of detection and inference:

| Parameter        | Description                             | Default |
|------------------|-----------------------------------------|---------|
| `conf_threshold` | Confidence threshold for detection      | `0.25`  |
| `iou_threshold`  | IoU threshold for NMS                   | `0.45`  |
| `max_detections` | Maximum number of detections per image  | `300`   |
| `agnostic_nms`   | Class-agnostic Non-Maximum Suppression  | `false` |
| `show_labels`    | Show class labels on detections         | `true`  |
| `show_conf`      | Show confidence scores on detections    | `true`  |
| `save_crops`     | Save crops of detected objects          | `false` |
| `hide_conf`      | Hide confidence values in output        | `false` |
| `hide_labels`    | Hide class labels in output             | `false` |
| `half`           | Use FP16 (half-precision) for inference | `false` |