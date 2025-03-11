# MicroDetect

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![Python](https://img.shields.io/badge/python-3.12-blue)
![License](https://img.shields.io/badge/license-PROPRIETARY-green)

**MicroDetect** is a comprehensive tool for detecting and classifying microorganisms in microscopy images using YOLOv8. This project provides a complete pipeline from image conversion, manual annotation, data augmentation, training to model evaluation.

## Documentation Languages
[English](README.md)(Current) | [Portuguese](README.pt.md)

## Key Features

- 🔍 **Image Conversion**: Converts TIFF images to formats suitable for processing
- 🏷️ **Manual Annotation**: Graphical interface for marking microorganisms in images
- 👁️ **Visualization**: Visualizes existing annotations in images
- 🔄 **Data Augmentation**: Enhances dataset with augmentation techniques
- 📊 **Dataset Preparation**: Splits and organizes data for training/validation/testing
- 🧠 **Model Training**: Trains custom YOLOv8 models with your images
- 📈 **Evaluation**: Evaluates models with detailed metrics and visual reports

## Supported Microorganisms

- 🦠 **Yeasts**
- 🍄 **Fungi**
- 🌱 **Micro-algae**

## Installation

### Prerequisites

- Python 3.12 or higher
- Conda (recommended for environment management)

### Setup with Conda (Recommended)

```bash
# Clone the repository
git clone https://github.com/your-username/microdetect.git
cd microdetect

# Setup environment
chmod +x scripts/setup.sh
./scripts/setup.sh --create

# Activate environment
conda activate yeast_detection

# Install dependencies
./scripts/setup.sh --install
```

### Windows Setup

```bash
# Clone the repository
git clone https://github.com/your-username/microdetect.git
cd microdetect

# Setup environment
scripts\setup.bat --create

# Activate environment
conda activate yeast_detection

# Install dependencies
scripts\setup.bat --install
```

### Manual Installation

```bash
# Clone the repository
git clone https://github.com/your-username/microdetect.git
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

### Converting TIFF Images to PNG

```bash
microdetect convert --input_dir data/raw_images --output_dir data/images --use_opencv
```

### Manual Image Annotation

```bash
microdetect annotate --image_dir data/images --output_dir data/labels
```

### Visualizing Annotations

```bash
microdetect visualize --image_dir data/images --label_dir data/labels
```

### Data Augmentation

```bash
microdetect augment --image_dir data/images --label_dir data/labels --factor 10
```

### Dataset Preparation

```bash
microdetect dataset --source_img_dir data/images --source_label_dir data/labels --dataset_dir dataset
```

### Model Training

```bash
microdetect train --dataset_dir dataset --model_size s --epochs 100
```

### Model Evaluation

```bash
microdetect evaluate --model_path runs/train/yolov8_s_custom/weights/best.pt --dataset_dir dataset --confusion_matrix
```

## Project Structure

```
microdetect/
├── README.md                  # Main documentation
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
    ├── setup.sh               # Setup on Linux/Mac
    └── setup.bat              # Setup on Windows
```

## Dataset Structure

The project follows the standard YOLOv8 structure:

```
dataset/
├── train/                     # Training data
│   ├── images/                # Images for training
│   └── labels/                # Annotations in YOLO format
├── val/                       # Validation data
│   ├── images/
│   └── labels/
├── test/                      # Test data
│   ├── images/
│   └── labels/
└── data.yaml                  # Dataset configuration
```

## Annotation Format

Annotations follow the YOLO format:

```
<class_id> <x_center> <y_center> <width> <height>
```

Where:
- `class_id`: Class ID (0=yeast, 1=fungus, 2=micro-algae)
- `x_center`, `y_center`: Normalized coordinates (0-1) of the box center
- `width`, `height`: Normalized width and height (0-1) of the box

## Using with Makefile

The project includes a Makefile for convenience:

```bash
# Create directories
make create-dirs

# Annotate images
make annotate

# Prepare dataset
make prepare-data

# Train model
make train

# Complete pipeline
make pipeline
```

## Contributing

Contributions are welcome! Feel free to open issues or submit pull requests.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contact

For questions, suggestions, or collaborations, please contact:

- Email: contact@example.com
- GitHub Issues: [https://github.com/your-username/microdetect/issues](https://github.com/your-username/microdetect/issues)