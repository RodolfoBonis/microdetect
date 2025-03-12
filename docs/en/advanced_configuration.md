# Advanced Configuration

This document explains all the advanced configuration options available in MicroDetect to customize and optimize its functionality to suit your specific needs.

## Table of Contents
- [Configuration File Overview](#configuration-file-overview)
- [Configuration File Structure](#configuration-file-structure)
- [Environment Variables](#environment-variables)
- [Command Line Configuration](#command-line-configuration)
- [Configuration Profiles](#configuration-profiles)
- [Advanced Training Options](#advanced-training-options)
- [Inference Configuration](#inference-configuration)
- [Callbacks Configuration](#callbacks-configuration)
- [Persistent Configuration](#persistent-configuration)
- [Logging Configuration](#logging-configuration)
- [Cache Configuration](#cache-configuration)
- [Multi-Project Configuration](#multi-project-configuration)
- [CI/CD Integration](#cicd-integration)

## Configuration File Overview

MicroDetect uses a centralized `config.yaml` file for most configuration settings. This file is created automatically when you run `microdetect init` and can be edited manually.

### Configuration File Location

The system looks for the configuration file in the following locations, in order of priority:

1. Path specified manually in commands
2. Current directory (`./config.yaml`)
3. User directory (`~/.microdetect/config.yaml`)
4. Internal default package configuration

## Configuration File Structure

Below is the complete structure with all available options:

```yaml
# Configuration for the MicroDetect Project

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
```

## Environment Variables

In addition to the configuration file, MicroDetect also respects various environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `MICRODETECT_CONFIG_PATH` | Path to the configuration file | `./config.yaml` |
| `MICRODETECT_LOG_LEVEL` | Logging level | `INFO` |
| `MICRODETECT_SKIP_UPDATE_CHECK` | Disable update check | Not set |
| `MICRODETECT_CACHE_DIR` | Cache directory | `~/.cache/microdetect` |
| `AWS_CODEARTIFACT_DOMAIN` | AWS CodeArtifact domain | Set by `setup-aws` |
| `AWS_CODEARTIFACT_REPOSITORY` | AWS CodeArtifact repository | Set by `setup-aws` |
| `AWS_CODEARTIFACT_OWNER` | AWS domain owner | Set by `setup-aws` |
| `CUDA_VISIBLE_DEVICES` | GPUs to use | All available |
| `OMP_NUM_THREADS` | OpenMP threads | Number of CPUs |

## Command Line Configuration

Many settings can be overridden using command line arguments:

```bash
# Example: override training settings
microdetect train --dataset_dir dataset --model_size m --epochs 200 --batch_size 16 --image_size 640
```

### Configuration Priority

MicroDetect uses the following order of priority to determine the settings:

1. Command line arguments
2. Environment variables
3. Configuration file
4. Internal default values

## Configuration Profiles

You can maintain multiple configuration profiles for different use cases:

```bash
# Create a new profile
cp config.yaml config_training.yaml

# Use a specific profile
microdetect train --config config_training.yaml
```

## Advanced Training Options

### GPU Configuration

To control GPU usage:

```bash
# Use specific GPU
CUDA_VISIBLE_DEVICES=0 microdetect train --dataset_dir dataset

# Use multiple GPUs (if available)
microdetect train --dataset_dir dataset --device 0,1

# Force CPU usage
microdetect train --dataset_dir dataset --device cpu
```

### Hyperparameter Tuning

MicroDetect supports hyperparameter search:

```bash
# Basic hyperparameter search
microdetect train --dataset_dir dataset --find_hyperparams

# Custom search space (requires JSON file)
microdetect train --dataset_dir dataset --find_hyperparams --search_space hyperparams.json
```

Example of `hyperparams.json`:

```json
{
  "learning_rate": {"type": "float", "min": 0.001, "max": 0.1, "log": true},
  "batch_size": {"type": "int", "values": [8, 16, 32, 64]},
  "model_size": {"type": "categorical", "values": ["n", "s", "m"]}
}
```

## Inference Configuration

To configure inference and detection:

```yaml
# In config.yaml
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

## Callbacks Configuration

MicroDetect supports custom callbacks for training:

```python
# In your custom Python script
from microdetect.training.train import YOLOTrainer
from ultralytics.callbacks import Callback

# Define your callback
class CustomCallback(Callback):
    def on_train_start(self, trainer):
        print("Training started!")
    
    def on_train_end(self, trainer):
        print("Training completed!")

# Use with the trainer
trainer = YOLOTrainer()
trainer.model.add_callback("custom", CustomCallback())
trainer.train(data_yaml="dataset/data.yaml")
```

## Persistent Configuration

To save frequently used settings, add them to the `.env` file:

```bash
# Create/edit .env
echo "MICRODETECT_LOG_LEVEL=DEBUG" >> .env
echo "AWS_CODEARTIFACT_DOMAIN=my-domain" >> .env
```

To automatically load these settings:

```bash
# Linux/macOS
source <(grep -v '^#' .env | sed 's/^/export /')

# Windows PowerShell
Get-Content .env | ForEach-Object { 
    if ($_ -match '(.+)=(.+)') { 
        [Environment]::SetEnvironmentVariable($Matches[1], $Matches[2]) 
    } 
}
```

## Logging Configuration

For detailed logging configuration:

```python
# In your custom script
import logging
from microdetect.utils.config import config

# Configure logging
logging.basicConfig(
    level=getattr(logging, config.get("logging.level", "INFO")),
    format=config.get("logging.format", "%(asctime)s - %(name)s - %(levelname)s - %(message)s"),
    handlers=[
        logging.FileHandler(config.get("logging.file", "microdetect.log")),
        logging.StreamHandler()
    ]
)
```

## Cache Configuration

To improve performance with caching:

```yaml
# In config.yaml
caching:
  enabled: true                   # Enable caching
  directory: ~/.cache/microdetect  # Cache directory
  max_size_gb: 10                 # Maximum cache size (GB)
  ttl: 604800                     # TTL in seconds (7 days)
  compression: true               # Use compression
```

## Multi-Project Configuration

To manage multiple projects:

```
projects/
├── project1/
│   ├── config.yaml            # Project1-specific configuration
│   ├── data/
│   │   ├── images/
│   │   └── labels/
│   └── dataset/
├── project2/
│   ├── config.yaml            # Project2-specific configuration
│   ├── data/
│   │   ├── images/
│   │   └── labels/
│   └── dataset/
└── global_config.yaml         # Shared settings
```

Each project can have its own configuration but inherit from global settings:

```bash
# Combine configurations
python -c "import yaml; global_cfg=yaml.safe_load(open('global_config.yaml')); project_cfg=yaml.safe_load(open('project1/config.yaml')); merged_cfg={**global_cfg, **project_cfg}; print(yaml.dump(merged_cfg))" > project1/merged_config.yaml

# Use combined configuration
microdetect --config project1/merged_config.yaml train
```

## CI/CD Integration

For CI/CD environments, you can use environment variables or pass a configuration file:

```bash
# GitHub Actions example
MICRODETECT_CONFIG_PATH=ci_config.yaml microdetect train --dataset_dir dataset --no-interactive
```

Using the Makefile with configurations:

```bash
# Example with multiple configurations
make train MODEL_SIZE=m EPOCHS=200 BATCH_SIZE=16 IMAGE_SIZE=640 DOMAIN=my-domain
```

For more information about specific features and workflow, check the corresponding documentation pages.