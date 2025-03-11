# MicroDetect

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![Python](https://img.shields.io/badge/python-3.9%20%7C%203.10%20%7C%203.11%20%7C%203.12-blue)
![License](https://img.shields.io/badge/license-MIT-green)

*Leia em [Português](README_PT.md)*

**MicroDetect** is a comprehensive tool for detecting and classifying microorganisms in microscopy images using YOLOv8. This project provides a complete pipeline from image conversion, manual annotation with resume capability, data augmentation, checkpoint training to model evaluation.

## Table of Contents

- [Key Features](#key-features)
- [Supported Microorganisms](#supported-microorganisms)
- [Installation](#installation)
- [Quick Guide](#quick-guide)
- [Project Structure](#project-structure)
- [Detailed Features](#detailed-features)
  - [Image Conversion](#image-conversion)
  - [Manual Annotation with Resume](#manual-annotation-with-resume)
  - [Annotation Visualization](#annotation-visualization)
  - [Dataset Preparation](#dataset-preparation)
  - [Data Augmentation](#data-augmentation)
  - [Training with Checkpoints](#training-with-checkpoints)
  - [Model Evaluation](#model-evaluation)
- [Custom Configuration](#custom-configuration)
- [Using with Makefile](#using-with-makefile)
- [Contributing](#contributing)
- [License](#license)
- [Contact](#contact)

## Key Features

- 🔍 **Image Conversion**: Converts TIFF images to formats suitable for processing
- 🏷️ **Manual Annotation with Resume**: Graphical interface for marking microorganisms with the ability to save progress and resume where you left off
- 👁️ **Visualization**: Visualizes existing annotations in images
- 🔄 **Data Augmentation**: Enhances dataset with augmentation techniques
- 📊 **Dataset Preparation**: Splits and organizes data for training/validation/testing
- 🧠 **Training with Checkpoints**: Trains custom YOLOv8 models with checkpoint system for resuming
- 📈 **Evaluation**: Evaluates models with detailed metrics and visual reports

## Supported Microorganisms

- 🦠 **Yeasts**
- 🍄 **Fungi**
- 🌱 **Micro-algae**

## Installation

### Prerequisites

- Python 3.9 or higher
- Conda (recommended for environment management)

### Setup with Conda (Recommended)

```bash
# Clone the repository
git clone https://github.com/RodolfoBonis/microdetect.git
cd microdetect

# Setup environment
chmod +x scripts/install_production.sh
./scripts/install_production.sh

# OR to create a virtual environment
./scripts/install_production.sh --virtual-env

# To also create an example project
./scripts/install_production.sh --with-example
```

### Windows Setup

```bash
# Clone the repository
git clone https://github.com/RodolfoBonis/microdetect.git
cd microdetect

# Setup environment
scripts\install_production.bat

# OR to create a virtual environment
scripts\install_production.bat --virtual-env

# To also create an example project
scripts\install_production.bat --with-example
```

### Manual Installation

```bash
# Clone the repository
git clone https://github.com/RodolfoBonis/microdetect.git
cd microdetect

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt
pip install -e .
```

## Quick Guide

### Initialize Project

```bash
# Create a directory for your project
mkdir my_project
cd my_project

# Initialize MicroDetect
microdetect init
```

### Converting TIFF Images to PNG

```bash
microdetect convert --input_dir data/raw_images --output_dir data/images --use_opencv
```

### Manual Image Annotation (with resume system)

```bash
microdetect annotate --image_dir data/images --output_dir data/labels
```

### Visualizing Annotations

```bash
microdetect visualize --image_dir data/images --label_dir data/labels
```

### Dataset Preparation

```bash
microdetect dataset --source_img_dir data/images --source_label_dir data/labels --dataset_dir dataset
```

### Data Augmentation

```bash
microdetect augment --image_dir data/images --label_dir data/labels --factor 10
```

### Model Training

```bash
microdetect train --dataset_dir dataset --model_size s --epochs 100
```

### Resuming Training from a Checkpoint

```bash
microdetect train --resume runs/train/yolov8_s_custom/weights/last.pt --dataset_dir dataset --epochs 50
```

### Model Evaluation

```bash
microdetect evaluate --model_path runs/train/yolov8_s_custom/weights/best.pt --dataset_dir dataset --confusion_matrix
```

## Project Structure

```
microdetect/
├── README.md                  # Main documentation
├── README_PT.md               # Portuguese documentation
├── requirements.txt           # Project dependencies
├── setup.py                   # Installation script
├── Makefile                   # Make commands for automation
├── config.yaml                # Central project configuration
├── microdetect/               # Main package
│   ├── __init__.py            # Package initialization
│   ├── cli.py                 # Command line interface
│   ├── data/                  # Data processing modules
│   │   ├── __init__.py
│   │   ├── augmentation.py    # Image augmentation
│   │   ├── conversion.py      # Format conversion
│   │   └── dataset.py         # Dataset management
│   ├── annotation/            # Annotation modules
│   │   ├── __init__.py
│   │   ├── annotator.py       # Annotation tool
│   │   └── visualization.py   # Annotation visualization
│   ├── training/              # Training modules
│   │   ├── __init__.py
│   │   ├── train.py           # Model training
│   │   └── evaluate.py        # Model evaluation
│   └── utils/                 # Utility functions and classes
│       ├── __init__.py
│       └── config.py          # Configuration management
└── scripts/                   # Helper scripts
    ├── install_production_robust.sh  # Linux/Mac installation
    └── install_production_robust.bat # Windows installation
```

## Detailed Features

### Image Conversion

The conversion module allows transforming TIFF images into formats more suitable for processing, such as PNG:

```bash
# Basic usage
microdetect convert --input_dir data/raw_images --output_dir data/images

# With OpenCV for better processing of 16-bit images
microdetect convert --input_dir data/raw_images --output_dir data/images --use_opencv

# Delete original files after conversion
microdetect convert --input_dir data/raw_images --output_dir data/images --delete_original
```

Conversion is especially important for microscopy images, which are often saved in high-resolution TIFF formats.

### Manual Annotation with Resume

The annotation system has a complete graphical interface for marking microorganisms and allows you to resume work where you left off:

```bash
microdetect annotate --image_dir data/images --output_dir data/labels
```

**Key features:**

- Automatically loads existing annotations when editing an image
- Saves progress for later resumption
- Allows pausing and continuing where you left off
- Options to skip, edit, or overwrite existing annotations

**Keyboard shortcuts:**

- **R**: Reset (clear all annotations in current image)
- **D**: Delete the last drawn box
- **S**: Save annotations and go to next image
- **Q**: Quit without saving
- **E**: Save current annotation and exit (to resume later)

When you restart the annotation tool, it asks if you want to resume from where you previously left off.

### Annotation Visualization

To review the annotations made:

```bash
# Interactive visualization
microdetect visualize --image_dir data/images --label_dir data/labels

# Save images with drawn annotations
microdetect visualize --image_dir data/images --label_dir data/labels --output_dir data/annotated_images

# Filter specific classes
microdetect visualize --image_dir data/images --label_dir data/labels --filter_classes "0,1"
```

Visualization allows navigating between images using the keys:
- 'n': next image
- 'p': previous image
- '0'-'9': toggle class visibility
- 's': save current image with annotations
- 'q': quit

### Dataset Preparation

Organizes your dataset in a structure for training:

```bash
microdetect dataset --source_img_dir data/images --source_label_dir data/labels --dataset_dir dataset
```

This creates:
- Split into train/validation/test
- YAML configuration file for training
- Directory structure compatible with YOLOv8

You can customize the proportions:

```bash
microdetect dataset --source_img_dir data/images --source_label_dir data/labels --dataset_dir dataset --train_ratio 0.8 --val_ratio 0.1 --test_ratio 0.1
```

### Data Augmentation

Increases your dataset with automatic variations:

```bash
microdetect augment --image_dir data/images --label_dir data/labels --factor 10
```

Applied augmentation techniques:
- Brightness and contrast variation
- Horizontal flipping
- Slight rotation
- Gaussian noise addition

Augmentation parameters can be customized in `config.yaml`.

### Training with Checkpoints

Trains YOLOv8 models with checkpoint system:

```bash
# Basic training
microdetect train --dataset_dir dataset --model_size s --epochs 100

# Advanced configuration
microdetect train --dataset_dir dataset --model_size m --epochs 200 --batch_size 16 --image_size 640
```

**Checkpoint System:**

Training automatically saves:
- The best model (`best.pt`)
- The most recent model (`last.pt`)
- Optimizer state and metrics

To resume an interrupted training:

```bash
microdetect train --resume runs/train/yolov8_s_custom/weights/last.pt --dataset_dir dataset --epochs 50
```

### Model Evaluation

Evaluate the performance of the trained model:

```bash
microdetect evaluate --model_path runs/train/yolov8_s_custom/weights/best.pt --dataset_dir dataset
```

To generate a confusion matrix:

```bash
microdetect evaluate --model_path runs/train/yolov8_s_custom/weights/best.pt --dataset_dir dataset --confusion_matrix
```

Evaluation reports include:
- Precision (mAP50, mAP50-95)
- Recall
- F1-Score
- Metrics by class
- Performance graphs
- Confusion matrix (optional)

## Custom Configuration

MicroDetect uses a `config.yaml` file for centralized configuration. When you run `microdetect init`, this file is created in the current directory with default values.

Example customization:

```yaml
# config.yaml
directories:
  dataset: ./my_dataset
  images: ./my_images
  labels: ./my_annotations

classes:
  - "0-yeast"
  - "1-fungus"
  - "2-micro-algae"
  - "3-my-new-class"

training:
  model_size: m
  epochs: 300
  batch_size: 16
```

After customizing, commands will automatically use these values as defaults.

## Using with Makefile

The project includes a Makefile for task automation:

```bash
# Create directories
make create-dirs

# Convert TIFF images
make convert-tiff

# Annotate images
make annotate

# Visualize annotations
make visualize

# Prepare dataset
make prepare-data

# Apply augmentation
make augment

# Train model
make train

# Evaluate model
make evaluate

# Complete pipeline
make pipeline
```

You can customize parameters:

```bash
make train MODEL_SIZE=m EPOCHS=200 BATCH_SIZE=16
```

## Contributing

Contributions are welcome! Feel free to open issues or submit pull requests.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contact

For questions, suggestions, or collaborations, please contact:

- Email: dev@rodolfodebonis.com.br
- GitHub Issues: [https://github.com/RodolfoBonis/microdetect/issues](https://github.com/RodolfoBonis/microdetect/issues)