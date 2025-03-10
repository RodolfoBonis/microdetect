# Makefile for Yeast Detection Project

# Configuration variables
CONDA_ENV_NAME = yeast_detection
PYTHON_VERSION = 3.12

# Data directories
DATASET_DIR = dataset
SOURCE_IMG_DIR = data/images
SOURCE_LABEL_DIR = data/labels
OUTPUT_DIR = runs/train

# Training parameters
MODEL_SIZE = s
EPOCHS = 50
BATCH_SIZE = 32
IMAGE_SIZE = 640
AUGMENT_FACTOR = 5

# Default target
all: help

# Environment setup
setup:
	@echo "Setting up environment..."
	@chmod +x scripts/setup.sh
	./scripts/setup.sh --create
	@echo "Now activate the environment with: conda activate $(CONDA_ENV_NAME)"
	@echo "Then run: make install"

# Install dependencies (after conda environment activation)
install:
	@echo "Installing dependencies..."
	@chmod +x scripts/setup.sh
	./scripts/setup.sh --install

# Windows setup (alternative to setup target)
setup-win:
	@echo "Setting up environment on Windows..."
	scripts\setup.bat

# Prepare dataset (split into train/val/test)
prepare-data:
	@echo "Preparing dataset..."
	python training_model.py --source_img_dir $(SOURCE_IMG_DIR) --source_label_dir $(SOURCE_LABEL_DIR) --dataset_dir $(DATASET_DIR)

# Data augmentation
augment:
	@echo "Augmenting training data..."
	python training_model.py --dataset_dir $(DATASET_DIR) --augment --augment_factor $(AUGMENT_FACTOR)

fix-torch:
	@echo "Fixing PyTorch/torchvision compatibility..."
	pip install torchvision==0.21.0

update-torch:
	@echo "Updating PyTorch and torchvision..."
	pip install -U torch torchvision

create-dirs:
	@echo "Creating necessary directories..."
	mkdir -p scripts dataset data/images data/labels runs/train

# Annotation tool
annotate:
	@echo "Starting annotation tool..."
	python main.py annotate --image_dir $(SOURCE_IMG_DIR) --output_dir $(SOURCE_LABEL_DIR)

# Visualize annotations
visualize:
	@echo "Visualizing annotations..."
	python bounding_boxes.py --image_dir $(SOURCE_IMG_DIR) --label_dir $(SOURCE_LABEL_DIR)

# Train YOLO model
train:
	@echo "Training YOLO model..."
	python training_model.py --dataset_dir $(DATASET_DIR) --model_size $(MODEL_SIZE) \
		--epochs $(EPOCHS) --batch_size $(BATCH_SIZE) --image_size $(IMAGE_SIZE) \
		--output_dir $(OUTPUT_DIR) --train

# Train YOLO with augmentation
train-augmented:
	@echo "Training YOLO model with augmentation..."
	python training_model.py --dataset_dir $(DATASET_DIR) --model_size $(MODEL_SIZE) \
		--epochs $(EPOCHS) --batch_size $(BATCH_SIZE) --image_size $(IMAGE_SIZE) \
		--output_dir $(OUTPUT_DIR) --augment --augment_factor $(AUGMENT_FACTOR) --train

# Train YOLO with dataset existing
train-simple:
	@echo "Training YOLO model with dataset existing..."
	python training_model.py --dataset_dir $(DATASET_DIR)

# Evaluate model and generate report
evaluate:
	@echo "Evaluating model and generating report..."
	python training_model.py --evaluate --model_path $(OUTPUT_DIR)/yolov8_$(MODEL_SIZE)_custom/weights/best.pt \
		--dataset_dir $(DATASET_DIR)

# Clean up generated files
clean:
	@echo "Cleaning up augmented data..."
	rm -rf $(DATASET_DIR)/train/images/*_aug*
	rm -rf $(DATASET_DIR)/train/labels/*_aug*

# Help command
help:
	@echo "Yeast Detection Project Makefile"
	@echo ""
	@echo "Commands:"
	@echo "  make setup          - Create conda environment (Mac/Linux)"
	@echo "  make setup-win      - Create conda environment (Windows)"
	@echo "  make install        - Install dependencies (after activating env)"
	@echo "  make prepare-data   - Prepare dataset (train/val/test split)"
	@echo "  make annotate       - Start annotation tool"
	@echo "  make augment        - Augment training data"
	@echo "  make visualize      - Visualize annotations"
	@echo "  make train          - Train YOLO model"
	@echo "  make train-augmented - Train with augmentation"
	@echo "  make train-simple   - Train YOLO with dataset existing"
	@echo "  make evaluate       - Evaluate model and generate report"
	@echo "  make fix-torch      - Fix PyTorch/torchvision compatibility"
	@echo "  make update-torch   - Update PyTorch and torchvision"
	@echo "  make create-dirs    - Create necessary directories"
	@echo "  make clean          - Clean up generated files"
	@echo ""
	@echo "Configuration (override with make VAR=value):"
	@echo "  SOURCE_IMG_DIR = $(SOURCE_IMG_DIR)"
	@echo "  SOURCE_LABEL_DIR = $(SOURCE_LABEL_DIR)"
	@echo "  MODEL_SIZE = $(MODEL_SIZE) (options: n, s, m, l, x)"
	@echo "  EPOCHS = $(EPOCHS)"
	@echo "  BATCH_SIZE = $(BATCH_SIZE)"
	@echo "  AUGMENT_FACTOR = $(AUGMENT_FACTOR)"

.PHONY: all setup install setup-win prepare-data augment annotate visualize train train-augmented train-simple evaluate fix-torch update-torch create-dirs clean help