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
- [Evaluation Issues](#evaluation-issues)
- [Error Analysis Issues](#error-analysis-issues)
- [Visualization and Dashboard Issues](#visualization-and-dashboard-issues)
- [Statistical Analysis Issues](#statistical-analysis-issues)
- [Cross-Validation Issues](#cross-validation-issues)
- [Benchmarking Issues](#benchmarking-issues)
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

## Evaluation Issues

### Error: Evaluation metrics don't match expectations

**Symptoms:**
Metrics like mAP50 are much lower than expected based on training metrics.

**Solutions:**
1. Check if using the correct test dataset:
   ```bash
   # Make sure the test set has appropriate annotations
   ls -la dataset/test/labels/
   ```

2. Verify detection thresholds:
   ```bash
   # Try different confidence thresholds
   microdetect evaluate --model_path model.pt --dataset_dir dataset --conf_threshold 0.25
   ```

3. Examine model's best weights file:
   ```bash
   # Make sure you're using the best weights, not last
   microdetect evaluate --model_path runs/train/exp/weights/best.pt --dataset_dir dataset
   ```

### Error: Confusion matrix generation fails

**Symptoms:**
```
ERROR: Could not generate confusion matrix
```

**Solutions:**
1. Check if test dataset has enough samples:
   ```bash
   # Make sure you have enough samples per class
   ls -la dataset/test/labels/ | wc -l
   ```

2. Try disabling confusion matrix:
   ```bash
   microdetect evaluate --model_path model.pt --dataset_dir dataset --confusion_matrix False
   ```

## Error Analysis Issues

### Error: No errors found despite poor performance

**Symptoms:**
Error analysis shows few or no errors despite low model performance.

**Solutions:**
1. Lower confidence threshold:
   ```bash
   microdetect analyze_errors --model_path model.pt --dataset_dir dataset --conf_threshold 0.1
   ```

2. Check test dataset paths:
   ```bash
   # Verify test set structure
   ls -la dataset/test/images/
   ls -la dataset/test/labels/
   ```

3. Make sure image and label filenames match.

### Error: Missing visualization for some error types

**Symptoms:**
Some error folders are empty (e.g., no classification errors).

**Solutions:**
1. This may be normal if your model doesn't make those error types
2. Try a larger test set to capture more diverse errors
3. Check if annotation format matches detection output format

### Error: Memory issues during error analysis

**Symptoms:**
```
ERROR: Out of memory during error analysis
```

**Solutions:**
1. Process fewer images:
   ```bash
   # Limit maximum samples 
   microdetect analyze_errors --model_path model.pt --dataset_dir dataset --max_samples 10
   ```

2. Use a smaller model or reduce image size for analysis

## Visualization and Dashboard Issues

### Error: Dashboards don't load in browser

**Symptoms:**
Dashboard server starts but nothing appears in browser.

**Solutions:**
1. Check if port is already in use:
   ```bash
   # Check if port is in use (Linux/macOS)
   lsof -i :8050
   
   # Windows
   netstat -ano | findstr :8050
   ```

2. Try a different port:
   ```bash
   microdetect dashboard --results_dir results --port 8051
   ```

3. Install missing dashboard dependencies:
   ```bash
   pip install dash dash-bootstrap-components
   ```

### Error: PDF report generation fails

**Symptoms:**
```
ERROR: Failed to generate PDF report
```

**Solutions:**
1. Ensure wkhtmltopdf is installed:
   ```bash
   # For Ubuntu/Debian
   sudo apt-get install wkhtmltopdf
   
   # For macOS
   brew install wkhtmltopdf
   ```

2. Try generating HTML report first:
   ```bash
   microdetect generate_report --results_dir results --format html
   ```

### Error: Images missing in visualization

**Symptoms:**
Bounding boxes appear but not underlying images.

**Solutions:**
1. Check image paths:
   ```bash
   # Make sure paths are absolute or relative to current directory
   microdetect visualize_detections --model_path model.pt --source $(pwd)/images
   ```

2. Verify image format support:
   ```bash
   # Make sure images are in supported formats
   find images -type f | grep -v -E '\.(jpg|jpeg|png|bmp)$'
   ```

## Statistical Analysis Issues

### Error: Density maps show no patterns

**Symptoms:**
Density maps are blank or uniformly colored.

**Solutions:**
1. Adjust smoothing parameter:
   ```bash
   microdetect analyze_distribution --model_path model.pt --source images --sigma 5.0
   ```

2. Check if detections were found:
   ```bash
   # Verify your model is detecting objects
   microdetect batch_detect --model_path model.pt --source images --save_json
   ```

### Error: Size analysis shows unexpected results

**Symptoms:**
Size distribution histograms show unrealistic values.

**Solutions:**
1. Check bounding box normalization:
   ```bash
   # If using custom code, ensure values are normalized correctly
   # YOLO format uses normalized coordinates (0-1)
   ```

2. Filter small detections:
   ```bash
   # Set minimum confidence threshold
   microdetect analyze_size --model_path model.pt --source images --conf_threshold 0.5
   ```

### Error: Cluster analysis finds no clusters

**Symptoms:**
Spatial analysis shows no clusters despite visually apparent groups.

**Solutions:**
1. Adjust minimum distance parameter:
   ```bash
   microdetect analyze_spatial --model_path model.pt --source images --min_distance 0.05
   ```

2. Verify coordinate system:
   ```bash
   # Make sure coordinates are normalized (0-1)
   ```

## Cross-Validation Issues

### Error: Cross-validation takes too long

**Symptoms:**
Cross-validation process is extremely slow or seems stuck.

**Solutions:**
1. Reduce number of epochs for validation:
   ```python
   validator = CrossValidator(
       base_dataset_dir="dataset",
       output_dir="cv_results",
       model_size="s",
       epochs=20,  # Fewer epochs
       folds=5
   )
   ```

2. Use a smaller model size:
   ```python
   validator = CrossValidator(
       base_dataset_dir="dataset",
       output_dir="cv_results",
       model_size="n",  # Nano model
       epochs=50,
       folds=5
   )
   ```

3. Reduce the number of folds:
   ```python
   validator = CrossValidator(
       base_dataset_dir="dataset",
       output_dir="cv_results",
       model_size="m",
       epochs=100,
       folds=3  # Fewer folds
   )
   ```

### Error: Out of memory during cross-validation

**Symptoms:**
```
CUDA out of memory
```

**Solutions:**
1. Process one fold at a time:
   ```python
   # Instead of validator.run(), run each fold individually
   for fold in range(1, 6):
       # Setup fold manually
       # Train and evaluate
   ```

2. Reduce batch size:
   ```python
   # Configure trainer with smaller batch size
   trainer = YOLOTrainer(
       model_size="m",
       batch_size=8,  # Small batch size
       epochs=100
   )
   ```

### Error: Large standard deviation in cross-validation results

**Symptoms:**
Cross-validation results show very high standard deviation between folds.

**Solutions:**
1. Increase the number of folds:
   ```python
   validator = CrossValidator(
       base_dataset_dir="dataset",
       output_dir="cv_results",
       model_size="m",
       epochs=100,
       folds=10  # More folds for better estimate
   )
   ```

2. Check for data imbalance:
   ```bash
   # Count files in each class
   ls dataset/labels | grep -c "class1"
   ls dataset/labels | grep -c "class2"
   ```

3. Stratify folds manually to ensure class balance

## Benchmarking Issues

### Error: Inconsistent benchmark results

**Symptoms:**
Benchmarking results vary significantly between runs.

**Solutions:**
1. Increase iterations and warmup:
   ```python
   benchmark = SpeedBenchmark(model_path="model.pt")
   results = benchmark.run(
       batch_sizes=[1, 4, 8],
       image_sizes=[640],
       iterations=100,  # More iterations
       warmup=20  # More warmup iterations
   )
   ```

2. Close other applications using GPU resources

3. Fix CPU/GPU frequency:
   ```bash
   # On Linux, set CPU governor to performance
   echo performance | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor
   
   # For NVIDIA GPUs, lock clock frequency
   sudo nvidia-smi --lock-gpu-clocks=1000,1500
   ```

### Error: Resource monitor shows no GPU usage

**Symptoms:**
```
No GPU usage recorded during monitoring
```

**Solutions:**
1. Verify GPU detection:
   ```python
   import torch
   print(f"CUDA available: {torch.cuda.is_available()}")
   print(f"GPU count: {torch.cuda.device_count()}")
   print(f"GPU name: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'None'}")
   ```

2. Install required monitoring packages:
   ```bash
   pip install gputil nvidia-ml-py3
   ```

3. For Apple Silicon, check MPS availability:
   ```python
   import torch
   print(f"MPS available: {torch.backends.mps.is_available()}")
   ```

### Error: Benchmark visualization fails

**Symptoms:**
```
ERROR: Could not generate benchmark visualization
```

**Solutions:**
1. Install matplotlib:
   ```bash
   pip install matplotlib
   ```

2. Check if results data is valid:
   ```python
   # Save raw results for inspection
   import json
   with open('benchmark_results_raw.json', 'w') as f:
       json.dump(results, f, indent=4)
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

### Error: "No module named 'dash'"

**Solution:**
```bash
pip install dash dash-bootstrap-components
```

### Error: "matplotlib.pyplot not found"

**Solution:**
```bash
pip install matplotlib
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

For component-specific logging:

```bash
# Enable detailed logging for specific modules
python -c "import logging; logging.getLogger('microdetect.training').setLevel(logging.DEBUG)"

# Or edit logging configuration in code
```

## Support

If you're still experiencing problems:

1. Check [GitHub Issues](https://github.com/RodolfoBonis/microdetect/issues)
2. Open a new issue with complete problem details
3. Contact: dev@rodolfodebonis.com.br