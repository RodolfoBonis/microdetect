# Dataset Management Guide

This guide explains how to efficiently organize, split, and prepare your dataset for training using MicroDetect's dataset management tools.

## Overview

Proper dataset management is crucial for successful model training. MicroDetect provides a comprehensive set of tools to organize your annotated images into the appropriate structure for YOLOv8 training, validate your data, and generate the necessary configuration files.

## Dataset Structure

MicroDetect requires a specific directory structure for training:

```
dataset/
├── train/
│   ├── images/
│   │   ├── image1.jpg
│   │   ├── image2.jpg
│   │   └── ...
│   └── labels/
│       ├── image1.txt
│       ├── image2.txt
│       └── ...
├── val/
│   ├── images/
│   │   └── ...
│   └── labels/
│       └── ...
├── test/
│   ├── images/
│   │   └── ...
│   └── labels/
│       └── ...
└── data.yaml
```

The `DatasetManager` class handles the creation of this structure automatically.

## Basic Usage

### Creating a Dataset

The simplest way to create a dataset is to use the `microdetect dataset` command:

```bash
microdetect dataset --source_img_dir data/images --source_label_dir data/labels
```

This command will:
1. Create the appropriate directory structure
2. Split your data into train/validation/test sets
3. Generate a `data.yaml` configuration file

### Command Line Options

| Parameter | Description | Default |
|-----------|-------------|---------|
| `--source_img_dir` | Directory containing annotated images | |
| `--source_label_dir` | Directory containing label files | |
| `--dataset_dir` | Output directory for the dataset | `dataset` |
| `--train_ratio` | Proportion of data for training | 0.7 |
| `--val_ratio` | Proportion of data for validation | 0.15 |
| `--test_ratio` | Proportion of data for testing | 0.15 |
| `--seed` | Random seed for reproducibility | 42 |

## Advanced Dataset Management

### Using the Python API

For more control, you can use the `DatasetManager` class directly in Python:

```python
from microdetect.data.dataset import DatasetManager

# Initialize with custom parameters
dataset_manager = DatasetManager(
    dataset_dir="custom_dataset",
    train_ratio=0.8,
    val_ratio=0.1,
    test_ratio=0.1,
    seed=123
)

# Create directory structure
dataset_manager.prepare_directory_structure()

# Split the dataset
split_counts = dataset_manager.split_dataset(
    source_img_dir="data/preprocessed_images",
    source_label_dir="data/annotations"
)
print(f"Split dataset: {split_counts}")

# Create YAML configuration
yaml_path = dataset_manager.create_data_yaml()
print(f"Created configuration file: {yaml_path}")
```

### Custom Class Configuration

You can specify your own class names:

```python
# In config.yaml
classes:
  - "0-yeast"
  - "1-fungus"
  - "2-microalga"
  - "3-bacteria"
```

Or using the Python API:

```python
from microdetect.data.dataset import DatasetManager
from microdetect.utils.config import config

# Set classes
config.set("classes", ["0-yeast", "1-fungus", "2-microalga", "3-bacteria"])

# Initialize dataset manager
dataset_manager = DatasetManager()

# Proceed with dataset preparation
```

## Dataset Validation

### Checking Dataset Integrity

MicroDetect provides tools to validate your dataset:

```bash
microdetect validate_dataset --dataset_dir dataset
```

This checks for:
- Missing image files
- Missing label files
- Corrupted images
- Invalid label formats
- Class distribution imbalance

### Visualizing Class Distribution

Examine class balance in your dataset:

```bash
microdetect dataset_stats --dataset_dir dataset --visualize
```

This generates visualizations showing:
- Distribution of classes across train/val/test splits
- Sample counts per class
- Sample size and aspect ratio distribution

## Working with Existing Datasets

### Importing from Other Formats

MicroDetect can import datasets from other common formats:

```bash
# Import from COCO format
microdetect import_dataset --source coco_dataset --format coco --output dataset

# Import from VOC format
microdetect import_dataset --source voc_dataset --format pascal_voc --output dataset

# Import from CreateML format
microdetect import_dataset --source createml_dataset --format createml --output dataset
```

### Merging Multiple Datasets

Combine datasets from different sources:

```bash
microdetect merge_datasets --sources dataset1,dataset2,dataset3 --output merged_dataset
```

## Cross-Validation Setup

For k-fold cross-validation:

```bash
microdetect create_cv_folds --dataset_dir dataset --k 5 --output_dir cv_datasets
```

This creates 5 different train/validation splits for cross-validation while maintaining the test set consistent.

## Best Practices

### Class Balance

Aim for a balanced distribution of classes. If your dataset is imbalanced:

```bash
# Analyze class distribution
microdetect dataset_stats --dataset_dir dataset

# Balance dataset by oversampling minority classes
microdetect balance_dataset --dataset_dir dataset --method oversample
```

### Train/Val/Test Split

The default split (70% train, 15% validation, 15% test) works well for most cases, but consider:
- More training data (80/10/10) for smaller datasets
- More validation data (60/20/20) when fine-tuning hyperparameters

### Data Leakage Prevention

Ensure similar images don't appear across different splits:

```bash
# Check for potential data leakage
microdetect check_leakage --dataset_dir dataset

# Split by groups (e.g., by slide or sample) rather than randomly
microdetect dataset --source_img_dir images --source_label_dir labels --group_by slide_id
```

## Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| Unbalanced class distribution | Use `balance_dataset` command to oversample minority classes |
| Missing labels | Use `find_missing_labels` to identify images without annotations |
| Invalid YAML configuration | Validate your data.yaml with `validate_yaml` command |
| Dataset too small | Consider data augmentation techniques (see [Data Augmentation Guide](data_augmentation.md)) |

## Next Steps

After preparing your dataset:

- [Data Augmentation Guide](data_augmentation.md) - Enhance your dataset with augmentation
- [Training Guide](training_guide.md) - Train your YOLOv8 model using your prepared dataset