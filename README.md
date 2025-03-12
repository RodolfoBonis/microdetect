# MicroDetect

<div align="center">

![MicroDetect Logo](https://img.shields.io/badge/MicroDetect-Microorganism%20Detection-blue?style=for-the-badge&logo=data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IiNmZmZmZmYiIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIj48Y2lyY2xlIGN4PSIxMiIgY3k9IjEyIiByPSIxMCIvPjxjaXJjbGUgY3g9IjEyIiBjeT0iMTIiIHI9IjYiLz48L3N2Zz4=)

[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](https://github.com/RodolfoBonis/microdetect)
[![Python](https://img.shields.io/badge/python-3.9%20%7C%203.10%20%7C%203.11%20%7C%203.12-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Documentation](https://img.shields.io/badge/docs-available-brightgreen.svg)](docs/en/index.md)

*Read in [Português](README.pt.md)*

</div>

## Overview

**MicroDetect** is a complete toolkit for detection and classification of microorganisms in microscopy images using YOLOv8. It streamlines the entire process from image preparation to model evaluation.

<div align="center">
<img src="https://img.shields.io/badge/YOLOv8-Powered-blue?style=for-the-badge" alt="YOLOv8 Powered"/>
</div>

## 🔑 Key Features

- 📷 **Image Conversion** - Transform microscopy TIFF images to optimized formats
- 🏷️ **Smart Annotation** - User-friendly interface with resumable sessions
- 📊 **Data Management** - Organize and prepare your datasets efficiently 
- 🔄 **Data Augmentation** - Enhance datasets with advanced transformation techniques
- 🧠 **Model Training** - Train custom YOLOv8 models with checkpoint management
- 📈 **Performance Evaluation** - Comprehensive metrics and visualizations
- 🔄 **Automatic Updates** - Seamless updates through AWS CodeArtifact

## 🦠 Supported Microorganisms

- **Yeasts**
- **Fungi**
- **Micro-algae**
- **Custom Classes** - Easily configurable for other microorganism types

## 📋 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/RodolfoBonis/microdetect.git
cd microdetect

# Install with script (recommended)
chmod +x scripts/install_production.sh
./scripts/install_production.sh --virtual-env
```

### Initialize Project

```bash
mkdir my_project
cd my_project
microdetect init
```

### Basic Workflow

```bash
# Convert TIFF images to PNG
microdetect convert --input_dir data/raw_images --output_dir data/images --use_opencv

# Annotate images
microdetect annotate --image_dir data/images --output_dir data/labels

# Prepare dataset
microdetect dataset --source_img_dir data/images --source_label_dir data/labels

# Train model
microdetect train --dataset_dir dataset --model_size s --epochs 100

# Evaluate model
microdetect evaluate --model_path runs/train/yolov8_s_custom/weights/best.pt --dataset_dir dataset
```

## 📚 Documentation

For detailed information, see our documentation:

- [Installation Guide](docs/pt/installation_guide.md) - Detailed installation instructions
- [Troubleshooting](docs/en/troubleshooting.md) - Solutions to common problems
- [Advanced Configuration](docs/en/advanced_configuration.md) - Customize MicroDetect for your needs
- [Development Guide](docs/en/development_guide.md) - Contribute to MicroDetect

Browse all documentation with the built-in docs server:

```bash
microdetect docs
```

## 🛠️ Project Structure

```
microdetect/
├── annotation/        # Image annotation tools
├── data/              # Data processing modules
├── training/          # Model training and evaluation
└── utils/             # Utility functions and configuration
```

## 🧪 Testing

Run the comprehensive test suite:

```bash
# Install test dependencies
pip install pytest pytest-cov

# Run tests with coverage report
pytest --cov=microdetect
```

## 🙏 Contributing

Contributions welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📞 Contact & Support

- GitHub Issues: [https://github.com/RodolfoBonis/microdetect/issues](https://github.com/RodolfoBonis/microdetect/issues)
- Email: dev@rodolfodebonis.com.br