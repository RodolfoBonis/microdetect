# Troubleshooting Guide

This guide helps solve common problems you might encounter when using MicroDetect.

## Table of Contents

- [Installation Issues](#installation-issues)
- [Image Conversion Issues](#image-conversion-issues)
- [Annotation Issues](#annotation-issues)
- [Visualization Issues](#visualization-issues)
- [Dataset Issues](#dataset-issues)
- [Training Issues](#training-issues)
- [GPU Issues](#gpu-issues)
- [Update System Issues](#update-system-issues)
- [Common Errors and Solutions](#common-errors-and-solutions)
- [Logging and Diagnosis](#logging-and-diagnosis)

## Installation Issues

### Error: "No module named 'microdetect'"

**Symptoms:**
```
ImportError: No module named 'microdetect'
```

**Solutions:**
1. Verify the package is installed:
   ```bash
   pip list | grep microdetect
   ```

2. Reinstall the package:
   ```bash
   pip install -e .
   ```

3. Check if you're in the correct virtual environment:
   ```bash
   # Check active environment
   which python  # Linux/macOS
   where python  # Windows
   ```

### Error: Version Incompatibility

**Symptoms:**
```
ERROR: pip's dependency resolver does not support this constraint
```

**Solutions:**
1. Update pip:
   ```bash
   pip install --upgrade pip
   ```

2. Install with `--no-deps` and then install dependencies:
   ```bash
   pip install --no-deps -e .
   pip install -r requirements.txt
   ```

### Error: Extension Compilation

**Symptoms:**
```
error: Microsoft Visual C++ 14.0 or greater is required.
```

**Solutions:**
1. Install Microsoft C++ Build Tools (Windows)
2. Install essential development tools (Linux):
   ```bash
   sudo apt-get install build-essential python3-dev
   ```
3. Use a pre-compiled version:
   ```bash
   pip install --only-binary=:all: -r requirements.txt
   ```

## Image Conversion Issues

### Error: TIFF Image Not Recognized

**Symptoms:**
```
ERROR: Error converting image.tiff: Image format not recognized
```

**Solutions:**
1. Use the OpenCV option:
   ```bash
   microdetect convert --input_dir data/raw_images --output_dir data/images --use_opencv
   ```

2. Check if the TIFF image is corrupted:
   ```bash
   identify -verbose image.tiff  # requires ImageMagick
   ```

3. Try converting with other tools:
   ```bash
   # Using ImageMagick
   convert image.tiff image.png
   ```

### Error: 16-bit Images

**Symptoms:**
Converted image is too dark or has incorrect colors.

**Solutions:**
1. Use the OpenCV option for normalization:
   ```bash
   microdetect convert --input_dir data/raw_images --output_dir data/images --use_opencv
   ```

2. If still having issues, do manual preprocessing:
   ```python
   import cv2
   import numpy as np
   
   # Load 16-bit image
   img = cv2.imread('image.tiff', cv2.IMREAD_UNCHANGED)
   
   # Normalize to 8-bit
   img_norm = cv2.normalize(img, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
   
   # Save
   cv2.imwrite('image.png', img_norm)
   ```

## Annotation Issues

### Error: Annotation Interface Doesn't Open

**Symptoms:**
```
No module named 'tkinter'
```

**Solutions:**
1. Install Tkinter:
   ```bash
   # Ubuntu/Debian
   sudo apt-get install python3-tk
   
   # Fedora
   sudo dnf install python3-tkinter
   
   # macOS (Homebrew)
   brew install python-tk
   ```

2. For Python 3.12 on macOS, use:
   ```bash
   # Install an alternative Python version with Tkinter
   brew install python@3.11
   ```

### Error: Annotations Not Saving

**Symptoms:**
Annotations aren't saved or appear in incorrect locations.

**Solutions:**
1. Check directory permissions:
   ```bash
   chmod 755 data/labels
   ```

2. Use absolute paths:
   ```bash
   microdetect annotate --image_dir $(pwd)/data/images --output_dir $(pwd)/data/labels
   ```

3. Check the progress file:
   ```bash
   cat data/labels/.annotation_progress.json
   ```

### Error: Large Images Cause Issues

**Symptoms:**
The interface hangs or becomes slow with very large images.

**Solutions:**
1. Resize images to a manageable size:
   ```bash
   # Using ImageMagick
   mogrify -resize 1024x1024\> data/images/*.png
   ```

## Visualization Issues

### Error: Visualization Interface Doesn't Open

**Symptoms:**
No window appears or error message about display.

**Solutions:**
1. Install Tkinter:
   ```bash
   sudo apt-get install python3-tk
   ```

2. Check if you're in a display-enabled environment:
   ```bash
   # Set display variable if needed
   export DISPLAY=:0
   ```

### Error: Annotations Not Visible

**Symptoms:**
Images display, but the annotations don't appear.

**Solutions:**
1. Verify label file paths:
   ```bash
   # Check if annotation files exist
   ls path/to/labels/*.txt
   ```

2. Check label file format:
   ```bash
   # Cat the content of a label file
   cat path/to/labels/image_name.txt
   # Should contain lines like: class_id center_x center_y width height
   ```

3. Use explicit label directory:
   ```bash
   microdetect visualize --image_dir path/to/images --label_dir path/to/labels
   ```

### Error: Performance Issues with Large Images

**Symptoms:**
Visualization is slow or freezes with large images.

**Solutions:**
1. Use batch mode for large collections:
   ```bash
   microdetect visualize --image_dir path/to/images --label_dir path/to/labels --batch --output_dir path/to/output
   ```

2. Resize images for visualization only:
   ```bash
   # In Python
   from PIL import Image
   Image.open('large_image.jpg').resize((1024, 768)).save('resized_image.jpg')
   ```

## Dataset Issues

### Error: Unbalanced Dataset Split

**Symptoms:**
The dataset isn't properly split between train/validation/test.

**Solutions:**
1. Specify ratios manually:
   ```bash
   microdetect dataset --source_img_dir data/images --source_label_dir data/labels --dataset_dir dataset --train_ratio 0.7 --val_ratio 0.15 --test_ratio 0.15
   ```

2. Check directory structure:
   ```bash
   find dataset -type f | sort | head -n 20
   ```

### Error: data.yaml file

**Symptoms:**
```
ERROR: data.yaml not found
```

**Solutions:**
1. Check correct path:
   ```bash
   ls -la dataset/data.yaml
   ```

2. Generate file manually:
   ```bash
   microdetect dataset --source_img_dir data/images --source_label_dir data/labels --dataset_dir dataset
   ```

3. Make sure classes are defined in config.yaml:
   ```bash
   cat config.yaml | grep -A5 classes
   ```

## Training Issues

### Error: CUDA out of memory

**Symptoms:**
```
RuntimeError: CUDA out of memory.
```

**Solutions:**
1. Reduce batch size:
   ```bash
   microdetect train --dataset_dir dataset --model_size s --batch_size 8
   ```

2. Reduce image size:
   ```bash
   microdetect train --dataset_dir dataset --model_size s --image_size 480
   ```

3. Use a smaller model:
   ```bash
   microdetect train --dataset_dir dataset --model_size n
   ```

### Error: Performance Drop

**Symptoms:**
The model converges and then performance drops dramatically.

**Solutions:**
1. Enable early stopping by increasing patience:
   ```bash
   python -m microdetect.training.train --dataset_dir dataset --patience 30
   ```

2. Reduce learning rate:
   ```python
   # Use ultralytics module directly with custom parameters
   from ultralytics import YOLO
   model = YOLO('yolov8s.pt')
   model.train(data='dataset/data.yaml', epochs=100, lr0=0.001)
   ```

### Error: Slow Training

**Symptoms:**
Training is taking much longer than expected.

**Solutions:**
1. Check if you're using GPU:
   ```bash
   python -c "import torch; print(torch.cuda.is_available())"
   ```

2. Optimize data loading:
   ```bash
   microdetect train --dataset_dir dataset --batch_size 32 --workers 4
   ```

3. On macOS with Apple Silicon, enable MPS acceleration:
   ```python
   import torch
   print(f"MPS available: {torch.backends.mps.is_available()}")
   ```

## GPU Issues

### Error: CUDA not available

**Symptoms:**
```
CUDA not available, using CPU
```

**Solutions:**
1. Check CUDA installation:
   ```bash
   nvidia-smi
   ```

2. Check PyTorch-CUDA compatibility:
   ```bash
   python -c "import torch; print(f'PyTorch: {torch.__version__}, CUDA: {torch.version.cuda}')"
   ```

3. Reinstall PyTorch with CUDA support:
   ```bash
   pip uninstall torch torchvision
   pip install torch torchvision --extra-index-url https://download.pytorch.org/whl/cu118
   ```

### Error: Mac MPS not available

**Symptoms:**
```
MPS not available on macOS with Apple Silicon chip
```

**Solutions:**
1. Update macOS to version 12.3+
2. Update PyTorch:
   ```bash
   pip install torch==2.6.0 torchvision==0.21.0
   ```

## Update System Issues

### Error: AWS CodeArtifact Connection Failure

**Symptoms:**
```
ERROR: Could not get token from AWS CodeArtifact
```

**Solutions:**
1. Check AWS credentials:
   ```bash
   aws sts get-caller-identity
   ```

2. Check if domain and repository exist:
   ```bash
   aws codeartifact list-repositories --domain your-domain
   ```

3. Reconfigure:
   ```bash
   microdetect setup-aws --domain your-domain --repository your-repository --configure-aws
   ```

### Error: Failed to Install Update

**Symptoms:**
```
ERROR: Failed to update to version X.Y.Z
```

**Solutions:**
1. Try updating manually:
   ```bash
   pip install --upgrade microdetect --index-url <repository_url>
   ```

2. Check log for specific errors:
   ```bash
   export MICRODETECT_LOG_LEVEL=DEBUG
   microdetect update
   ```

3. Clear pip cache:
   ```bash
   pip cache purge
   ```

## Common Errors and Solutions

### Error: "ModuleNotFoundError: No module named 'cv2'"

**Solution:**
```bash
pip install opencv-python
```

### Error: "AttributeError: module 'numpy' has no attribute 'float'"

**Solution:**
```bash
pip uninstall numpy
pip install numpy==1.23.5
```

### Error: "Cannot import name 'PILLOW_VERSION' from 'PIL'"

**Solution:**
```bash
pip uninstall pillow
pip install pillow
```

### Error: "FileNotFoundError: [Errno 2] No such file or directory: 'scripts/setup.sh'"

**Solution:**
```bash
# Make sure you're in the project root directory
cd microdetect
# Or specify full path
/path/to/microdetect/scripts/setup.sh
```

### Error: "JSONDecodeError: Expecting value: line 1 column 1"

**Solution:**
```bash
# Clean cache files
find . -name "*.json" -size 0 -delete
```

### Error: "YOLO model not found"

**Solution:**
```bash
# Create directory in Ultralytics cache
mkdir -p ~/.cache/ultralytics/
# Or specify full model path
microdetect train --dataset_dir dataset --model_size s --model_path yolov8s.pt
```

### Error: "Permission denied"

**Solution:**
```bash
# Linux/macOS
chmod +x scripts/*.sh

# Windows - Make sure to run as administrator
```

### Error: "File [filename] doesn't match the expected format"

**Solution:**
```bash
# Check if annotations are in YOLO format
cat data/labels/image_name.txt
# Should contain: class_id center_x center_y width height
```

## Logging and Diagnosis

For more complex issue diagnosis, enable debug mode:

```bash
# Export environment variable for detailed logging
export MICRODETECT_LOG_LEVEL=DEBUG

# Run command with detailed output
microdetect command --args > debug.log 2>&1

# Analyze the log
cat debug.log
```

## Support

If you're still experiencing problems:

1. Check [GitHub Issues](https://github.com/RodolfoBonis/microdetect/issues)
2. Open a new issue with complete problem details
3. Contact: dev@rodolfodebonis.com.br