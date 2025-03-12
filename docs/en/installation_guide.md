# Installation Guide

This guide provides step-by-step instructions for installing MicroDetect on different operating systems and environments.

## Table of Contents
- [System Requirements](#system-requirements)
- [Installation Methods](#installation-methods)
  - [Quick Installation Scripts](#quick-installation-scripts)
  - [Manual Installation](#manual-installation)
- [Platform-Specific Installation](#platform-specific-installation)
  - [Linux/macOS](#linuxmacos)
  - [Windows](#windows)
  - [Apple Silicon (M1/M2/M3)](#apple-silicon-m1m2m3)
- [Installation for Development](#installation-for-development)
- [AWS CodeArtifact Installation](#aws-codeartifact-installation)
- [Verifying Your Installation](#verifying-your-installation)
- [Configure Update System](#configure-update-system)
- [Troubleshooting](#troubleshooting)
- [Uninstallation](#uninstallation)

## System Requirements

### Minimum Requirements
- **Python**: 3.9 or higher
- **RAM**: 4GB (8GB recommended for training)
- **Disk Space**: 2GB for installation and basic usage
- **CUDA** (optional): For GPU acceleration on NVIDIA hardware

### Primary Dependencies
- PyTorch (1.7+)
- OpenCV
- Ultralytics YOLOv8
- NumPy, Matplotlib, Pillow
- AWS CLI (for automatic updates)

## Installation Methods

### Quick Installation Scripts

For a streamlined installation experience, we provide ready-to-use installation scripts.

#### Linux/macOS
```bash
# Clone the repository
git clone https://github.com/RodolfoBonis/microdetect.git
cd microdetect

# Make the script executable
chmod +x scripts/install_production.sh

# Install using the script
./scripts/install_production.sh

# To create a virtual environment during installation
./scripts/install_production.sh --virtual-env

# To create an example project after installation
./scripts/install_production.sh --with-example
```

#### Windows
```batch
# Clone the repository
git clone https://github.com/RodolfoBonis/microdetect.git
cd microdetect

# Install using the script
scripts\install_production.bat

# To create a virtual environment during installation
scripts\install_production.bat --virtual-env

# To create an example project after installation
scripts\install_production.bat --with-example
```

### Manual Installation

If you prefer more control over the installation process, you can install MicroDetect manually.

#### Using Virtual Environment
```bash
# Clone the repository
git clone https://github.com/RodolfoBonis/microdetect.git
cd microdetect

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate  # On Linux/macOS
# Or on Windows:
# venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install the package in development mode
pip install -e .

# Test the installation
python -c "import microdetect; print(f'MicroDetect version {microdetect.__version__} installed successfully!')"
```

## Platform-Specific Installation

### Linux/macOS

For Linux and macOS environments, the installation process is similar:

```bash
# Clone the repository
git clone https://github.com/RodolfoBonis/microdetect.git
cd microdetect

# Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install the package in development mode
pip install -e .
```

### Windows

For Windows environments:

```batch
# Clone the repository
git clone https://github.com/RodolfoBonis/microdetect.git
cd microdetect

# Create and activate a virtual environment
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install the package in development mode
pip install -e .
```

### Apple Silicon (M1/M2/M3)

For Mac computers with Apple Silicon chips, additional steps are needed for optimal performance:

```bash
# Clone the repository
git clone https://github.com/RodolfoBonis/microdetect.git
cd microdetect

# Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate

# Install PyTorch optimized for MPS (GPU on Mac)
pip install torch==2.6.0 torchvision==0.21.0

# Install other dependencies
pip install -r requirements.txt

# Install the package
pip install -e .
```

## Installation for Development

If you plan to contribute to the project:

```bash
# Clone the repository
git clone https://github.com/RodolfoBonis/microdetect.git
cd microdetect

# Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Install dependencies (including development tools)
pip install -r requirements.txt
pip install -r requirements-dev.txt  # additional tools for development

# Install the package in editable mode
pip install -e .

# Set up pre-commit hooks
pre-commit install
```

## AWS CodeArtifact Installation

To install MicroDetect directly from AWS CodeArtifact:

```bash
# Configure AWS CLI with your credentials
aws configure

# Get authentication token
export CODEARTIFACT_AUTH_TOKEN=$(aws codeartifact get-authorization-token \
    --domain your-domain \
    --query authorizationToken \
    --output text)

# Get repository URL
export CODEARTIFACT_REPOSITORY_URL=$(aws codeartifact get-repository-endpoint \
    --domain your-domain \
    --repository your-repository \
    --format pypi \
    --query repositoryEndpoint \
    --output text)

# Install MicroDetect
pip install microdetect \
    --index-url "${CODEARTIFACT_REPOSITORY_URL}simple/" \
    --extra-index-url https://pypi.org/simple
```

## Verifying Your Installation

After installation, verify that everything is working correctly:

```bash
# Check the version
microdetect --version

# Initialize an example project
mkdir my_project
cd my_project
microdetect init
```

## Configure Update System

After installation, configure the automatic update system:

```bash
# Configure AWS CodeArtifact
microdetect setup-aws --domain your-domain --repository your-repository --configure-aws

# Check for updates
microdetect update --check-only
```

## Troubleshooting

### PyTorch Issues

If you encounter problems with PyTorch:

```bash
# Uninstall current version
pip uninstall torch torchvision

# Reinstall the specific version for your hardware
# For CUDA:
pip install torch torchvision --extra-index-url https://download.pytorch.org/whl/cu118

# For CPU:
pip install torch torchvision --extra-index-url https://download.pytorch.org/whl/cpu

# For Apple Silicon:
pip install torch==2.6.0 torchvision==0.21.0
```

### OpenCV Issues

If you encounter problems with OpenCV:

```bash
# Uninstall and reinstall
pip uninstall opencv-python
pip install opencv-python-headless
```

### CUDA Issues

If you encounter problems with GPU support:

```bash
# Check CUDA availability
python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}')"

# View available devices
python -c "import torch; print(f'CUDA devices: {torch.cuda.device_count()}')"

# Check CUDA version
python -c "import torch; print(f'CUDA version: {torch.version.cuda}')"
```

### AWS Credential Issues

If you encounter problems with AWS CodeArtifact:

```bash
# Check AWS configuration
aws configure list

# Test access to CodeArtifact
aws codeartifact get-repository \
    --domain your-domain \
    --repository your-repository
```

## Uninstallation

To uninstall MicroDetect:

```bash
# Uninstall the package
pip uninstall microdetect

# Remove virtual environment (optional)
# Linux/macOS
rm -rf venv

# Windows
rmdir /s /q venv

# Or deactivate and remove conda environment (optional)
conda deactivate
conda env remove -n microdetect
```

For more detailed troubleshooting, refer to the [Troubleshooting Guide](troubleshooting.md).