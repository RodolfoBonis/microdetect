# Microorganism Detection Project

This project provides a complete pipeline for detecting and classifying microorganisms (yeasts, fungi, and micro-algae) using YOLOv8 object detection. The tools include image annotation, data augmentation, training, and evaluation functionalities.

**Documentation Languages:**
- [English](README.md) (current)
- [Portuguese](README-pt.md)

## Features

- Manual annotation tool for creating bounding boxes
- Data augmentation to expand your training dataset
- TIFF to PNG image conversion
- Annotation visualization and validation
- Training pipeline with YOLOv8
- Model evaluation with detailed metrics and reports
- Support for multiple operating systems

## Requirements

- Python 3.8+
- OpenCV
- PyTorch
- Ultralytics YOLOv8
- NumPy
- Pillow
- YAML
- TensorBoard (for training visualization)
- CUDA-capable GPU (recommended for training)

## Installation

### Windows

```bash
# Clone the repository
git clone https://github.com/yourusername/microorganism-detection.git
cd microorganism-detection

# Create and activate conda environment
make setup-win
conda activate yeast_detection

# Install dependencies
make install
```

### macOS/Linux

```bash
# Clone the repository
git clone https://github.com/yourusername/microorganism-detection.git
cd microorganism-detection

# Create and activate conda environment
make setup
conda activate yeast_detection

# Install dependencies
make install
```

### Manual Installation (Any OS)

```bash
# Create conda environment
conda create -n yeast_detection python=3.12 -y
conda activate yeast_detection

# Install dependencies
pip install ultralytics opencv-python-headless numpy pillow pyyaml tqdm
pip install torch torchvision
```

## Project Structure

```
microorganism-detection/
├── data/
│   ├── images/         # Raw images for annotation
│   └── labels/         # Annotation files in YOLO format
├── dataset/            # Processed dataset with train/val/test splits
├── scripts/            # Helper scripts
├── runs/               # Training results and models
├── reports/            # Evaluation reports and metrics
├── bounding_boxes.py   # Visualization tool
├── convert_tiff.py     # TIFF conversion utility
├── main.py             # Annotation tool
├── training_model.py   # Training and evaluation script
└── makefile            # Automation commands
```

## Usage

### Directory Setup

Create necessary directories for your project:

```bash
make create-dirs
```

### Convert TIFF Images to PNG

If your images are in TIFF format, convert them to PNG:

```bash
make convert-tiff
# or manually:
python convert_tiff.py --input_dir data/images --output_dir data/images --use_opencv --delete_original
```

### Annotate Images

Launch the annotation tool to create bounding boxes:

```bash
make annotate
# or manually:
python main.py annotate --image_dir data/images --output_dir data/labels
```

Instructions:
- Click and drag to create bounding boxes
- Use the class dropdown to select microorganism type
- 'r' to reset, 'd' to delete last box, 's' to save, 'q' to quit

### Visualize Annotations

Check your annotations visually:

```bash
make visualize
# or manually:
python bounding_boxes.py --image_dir data/images --label_dir data/labels
```

Navigation:
- 'n' for next image, 'p' for previous image
- '0', '1', '2' to toggle class visibility
- 'a' to show all classes, 'q' to quit

### Prepare Dataset

Split your annotated data into training, validation, and test sets:

```bash
make prepare-data
# or manually:
python training_model.py --source_img_dir data/images --source_label_dir data/labels --dataset_dir dataset
```

### Data Augmentation

Augment your training data to improve model performance:

```bash
make augment
# or manually:
python training_model.py --dataset_dir dataset --augment --augment_factor 20
```

### Train Model

Train the YOLOv8 model on your dataset:

```bash
make train
# or with augmentation:
make train-augmented
# or manually:
python training_model.py --dataset_dir dataset --model_size s --epochs 50 --batch_size 32 --train
```

Model size options:
- `n`: nano (smallest, fastest)
- `s`: small
- `m`: medium
- `l`: large
- `x`: xlarge (largest, most accurate)

### Evaluate Model

Generate evaluation metrics and reports:

```bash
make evaluate
# or manually:
python training_model.py --evaluate --model_path runs/train/yolov8_s_custom/weights/best.pt --dataset_dir dataset
```

## Common Issues & Troubleshooting

### PyTorch/Torchvision Compatibility
If you encounter compatibility issues:
```bash
make fix-torch
# or
make update-torch
```

### GPU Acceleration
- The script automatically selects the best available device (CUDA GPU, Apple Metal, or CPU)
- For optimal training performance, use a CUDA-capable NVIDIA GPU

### Memory Issues
If you encounter CUDA out-of-memory errors:
- Reduce batch size: `--batch_size 8` or lower
- Use a smaller model: `--model_size s` or `--model_size n`
- Reduce image size: `--image_size 416`

## Complete Workflow Example

```bash
# 1. Setup environment
make setup
conda activate yeast_detection
make install

# 2. Convert TIFF images (if needed)
make convert-tiff

# 3. Annotate images
make annotate

# 4. Visualize annotations
make visualize

# 5. Prepare dataset
make prepare-data

# 6. Augment training data
make augment

# 7. Train model
make train-augmented

# 8. Evaluate model
make evaluate
```

## License

This project is licensed under [Proprietary License](LICENSE) - see the LICENSE file for details.