# Training Guide

## Overview

MicroDetect provides a comprehensive workflow for training YOLOv8 models to detect microorganisms in microscopy images. This guide will walk you through the process of preparing your data, training models, and evaluating results.

## Prerequisites

- Annotated dataset prepared using the Microdetect annotation tool
- Python environment with required dependencies installed

## Preparing Your Dataset

Before training, you need to organize your dataset in the YOLOv8 format:

```bash
microdetect dataset --source_img_dir /path/to/images --source_label_dir /path/to/labels --val_split 0.2 --test_split 0.1
```

This command:
1. Creates train/val/test splits from your data
2. Organizes images and labels in the correct directories
3. Generates a `data.yaml` configuration file for YOLOv8

### Options:

- `--val_split`: Proportion of data to use for validation (default: 0.2)
- `--test_split`: Proportion of data to use for testing (default: 0.1)
- `--classes`: Comma-separated list of class names (default: yeast,fungi,microalgae)
- `--output_dir`: Output directory for dataset (default: "dataset")

## Training a Model

Once your dataset is prepared, you can train a YOLOv8 model:

```bash
microdetect train --dataset_dir dataset --model_size m --epochs 100 --batch_size 16
```

### Options:

- `--dataset_dir`: Path to the dataset directory containing data.yaml
- `--model_size`: YOLOv8 model size (n, s, m, l, x) (default: "m")
- `--epochs`: Number of training epochs (default: 100)
- `--batch_size`: Batch size for training (default: 16)
- `--img_size`: Input image size (default: 640)
- `--patience`: Early stopping patience (default: 20)
- `--device`: Device to use (cpu, mps, 0, 1, etc.) (default: auto-detection)
- `--resume`: Resume training from last checkpoint
- `--pretrained`: Use pretrained weights
- `--freeze`: Number of layers to freeze (default: 0)

## Hyperparameter Optimization

MicroDetect supports hyperparameter optimization to find the best model configuration:

```bash
microdetect optimize --dataset_dir dataset --iterations 20 --metric map
```

### Options:

- `--dataset_dir`: Path to the dataset directory containing data.yaml
- `--iterations`: Number of hyperparameter combinations to try (default: 20)
- `--metric`: Metric to optimize (map, precision, recall, F1) (default: "map")
- `--params`: Comma-separated list of parameters to optimize (model_size,lr,batch_size,img_size)

## Cross-Validation

To better evaluate model performance, particularly with small datasets, use cross-validation:

```bash
microdetect cross_validate --dataset_dir dataset --model_size m --folds 5
```

### Options:

- `--dataset_dir`: Path to the dataset directory containing data.yaml
- `--model_size`: YOLOv8 model size (n, s, m, l, x) (default: "m")
- `--folds`: Number of cross-validation folds (default: 5)
- `--epochs`: Number of training epochs per fold (default: 50)

## Evaluating Models

After training, evaluate your model's performance:

```bash
microdetect evaluate --model_path runs/train/yolov8_m_custom/weights/best.pt --dataset_dir dataset
```

### Options:

- `--model_path`: Path to the trained model
- `--dataset_dir`: Path to the dataset directory containing data.yaml
- `--conf`: Confidence threshold (default: 0.25)
- `--iou`: IoU threshold (default: 0.5)
- `--batch_size`: Batch size for evaluation (default: 16)
- `--device`: Device to use (cpu, mps, 0, 1, etc.) (default: auto-detection)

## Comparing Multiple Models

Compare the performance of different models:

```bash
microdetect compare_models --model_paths model1.pt,model2.pt,model3.pt --data_yaml dataset/data.yaml
```

### Options:

- `--model_paths`: Comma-separated list of model paths
- `--data_yaml`: Path to data.yaml file
- `--conf`: Confidence threshold (default: 0.25)
- `--iou`: IoU threshold (default: 0.5)
- `--output_dir`: Directory to save comparison results (default: "comparison_results")

## Advanced Training Options

### Checkpoint Management

MicroDetect automatically saves checkpoints during training, which can be used to resume interrupted training sessions:

```bash
microdetect train --dataset_dir dataset --resume
```

### Hardware Acceleration

The training system automatically detects and uses available hardware acceleration:

- CUDA for NVIDIA GPUs
- MPS for Apple Silicon
- CPU fallback if no GPU is available

You can override this with the `--device` parameter.

### Transfer Learning

Use pretrained weights to speed up training and improve accuracy:

```bash
microdetect train --dataset_dir dataset --pretrained --freeze 10
```

This loads pretrained weights and freezes the first 10 layers of the model.

## Training Workflow Example

Complete workflow from annotation to deployment:

```bash
# Prepare dataset
microdetect dataset --source_img_dir data/images --source_label_dir data/labels

# Train initial model
microdetect train --dataset_dir dataset --model_size s --epochs 50 --pretrained

# Optimize hyperparameters
microdetect optimize --dataset_dir dataset --iterations 15

# Train final model with optimized parameters
microdetect train --dataset_dir dataset --model_size m --epochs 150 --batch_size 32 --img_size 800

# Evaluate model
microdetect evaluate --model_path runs/train/yolov8_m_custom/weights/best.pt --dataset_dir dataset

# Export model
microdetect export --model_path runs/train/yolov8_m_custom/weights/best.pt --format onnx
```

## Best Practices

1. **Start Small**: Begin with a smaller model size (n or s) to ensure the training pipeline works
2. **Use Pretrained Weights**: Always start with pretrained weights unless your domain is very different
3. **Data Augmentation**: Use data augmentation to improve model robustness
4. **Hyperparameter Tuning**: Find optimal hyperparameters for your specific dataset
5. **Monitor Training**: Watch for signs of overfitting (validation performance worsens while training improves)
6. **Multiple Models**: Train several model variants and compare their performance
7. **Error Analysis**: Analyze false positives and false negatives to understand model limitations

## Troubleshooting

### Common Issues

1. **Out of Memory Errors**: Reduce batch size or model size
2. **Slow Training**: Check hardware acceleration is working correctly
3. **Poor Convergence**: Try different learning rates or optimizer settings
4. **Overfitting**: Increase data augmentation or use early stopping
5. **Underfitting**: Train for more epochs or use a larger model

For more detailed troubleshooting, see the [Troubleshooting Guide](troubleshooting.md).