# Training Guide

This guide explains how to train YOLOv8 models for microorganism detection using MicroDetect's training tools.

## Overview

MicroDetect provides a comprehensive set of tools for training YOLOv8 models, optimized for microorganism detection in microscopy images. The `YOLOTrainer` class simplifies the process of training, resuming training from checkpoints, and finding optimal hyperparameters.

## Basic Training

### Command Line Interface

The simplest way to train a model is through the command line:

```bash
microdetect train --dataset_dir dataset --model_size s --epochs 100 --batch_size 16 --image_size 640
```

This command will:
1. Load the dataset configuration from `dataset/data.yaml`
2. Initialize a YOLOv8s model (small variant)
3. Train for 100 epochs with the specified batch size and image size
4. Save the results in the `runs/train` directory

### Command Line Options

| Parameter | Description | Default |
|-----------|-------------|---------|
| `--dataset_dir` | Directory containing the dataset | `dataset` |
| `--model_size` | YOLOv8 model size (n, s, m, l, x) | `s` |
| `--epochs` | Number of training epochs | `100` |
| `--batch_size` | Batch size for training | `16` |
| `--image_size` | Input image size | `640` |
| `--pretrained` | Use pretrained weights | `True` |
| `--output_dir` | Directory for saving results | `runs/train` |

## Model Size Selection

YOLOv8 comes in various sizes, each with different complexity/performance tradeoffs:

| Model Size | Description | Ideal Use Case |
|------------|-------------|----------------|
| `n` (nano) | Smallest model, fastest but less accurate | Resource-constrained environments, real-time applications |
| `s` (small) | Good balance of speed and accuracy | General use, balanced performance |
| `m` (medium) | Higher accuracy than small, still reasonably fast | Better detection when resources allow |
| `l` (large) | High accuracy, slower than medium | Prioritizing accuracy over speed |
| `x` (extra large) | Highest accuracy, slowest performance | Maximum accuracy requirements |

Example for training a medium model:

```bash
microdetect train --dataset_dir dataset --model_size m --epochs 150
```

## Advanced Training

### Using the Python API

For more control, you can use the `YOLOTrainer` class directly in Python:

```python
from microdetect.training.train import YOLOTrainer
from microdetect.data.dataset import DatasetManager

# Prepare dataset if needed
dataset_manager = DatasetManager()
data_yaml = dataset_manager.create_data_yaml()

# Initialize trainer with custom parameters
trainer = YOLOTrainer(
    model_size="m",
    epochs=150,
    batch_size=8,
    image_size=800,
    pretrained=True,
    output_dir="custom_runs/my_training"
)

# Start training
results = trainer.train(data_yaml=data_yaml)

# Print training summary
print(f"Training complete. Best mAP: {results.best_map}")
```

### Hardware Selection

MicroDetect automatically selects the best available hardware for training:

1. NVIDIA GPU (CUDA) if available
2. Apple Silicon GPU (MPS) if available
3. CPU as fallback

You can manually specify the device:

```bash
microdetect train --dataset_dir dataset --model_size s --device cuda:0  # Specific CUDA device
microdetect train --dataset_dir dataset --model_size s --device cpu     # Force CPU
microdetect train --dataset_dir dataset --model_size s --device mps     # Force Apple MPS
```

## Training Strategies

### Transfer Learning

By default, MicroDetect uses pre-trained weights trained on COCO dataset. You can start from scratch by disabling this:

```bash
microdetect train --dataset_dir dataset --model_size s --pretrained False
```

However, starting from pre-trained weights generally gives better results, even for specialized tasks like microorganism detection.

### Learning Rate Schedules

MicroDetect uses YOLOv8's built-in learning rate scheduler. You can customize it:

```bash
microdetect train --dataset_dir dataset --lr0 0.01 --lrf 0.01 --momentum 0.937 --weight_decay 0.0005
```

Where:
- `lr0`: Initial learning rate
- `lrf`: Final learning rate factor (final_lr = lr0 * lrf)
- `momentum`: SGD momentum
- `weight_decay`: Weight decay factor

### Early Stopping

MicroDetect implements early stopping to prevent overfitting:

```bash
microdetect train --dataset_dir dataset --patience 15
```

This stops training if no improvement is seen for 15 consecutive epochs.

## Monitoring Training

### Training Metrics

During training, MicroDetect logs various metrics:

- mAP50: Mean Average Precision at IoU threshold 0.5
- mAP50-95: Mean Average Precision over multiple IoU thresholds
- Precision, Recall, and F1-score
- Loss components (box, class, dfl)

You can visualize these metrics in real-time:

```bash
microdetect train --dataset_dir dataset --model_size s --plot True
```

### TensorBoard Integration

For detailed training visualization, you can use TensorBoard:

```bash
# Start training with TensorBoard logging
microdetect train --dataset_dir dataset --model_size s --use_tensorboard

# Launch TensorBoard
tensorboard --logdir runs/train
```

## Hyperparameter Optimization

MicroDetect provides tools for hyperparameter optimization:

```bash
microdetect optimize_hyperparams --dataset_dir dataset --model_size s --trials 10
```

This will perform multiple training runs with different hyperparameters to find the optimal configuration.

### Using the Python API for Detailed Control

```python
from microdetect.training.train import YOLOTrainer

trainer = YOLOTrainer(model_size="s")
best_params = trainer.find_best_hyperparameters("dataset/data.yaml")

print(f"Best hyperparameters found: {best_params}")
```

This tries different combinations of batch sizes and learning rates to find the optimal configuration.

## Model Export

After training, MicroDetect automatically exports the model to ONNX format for deployment:

```bash
# The model is already exported during training, but you can manually export it
microdetect export --model_path runs/train/yolov8_s_custom/weights/best.pt --format onnx
```

Other supported export formats:
- `torchscript`: For PyTorch deployment
- `tflite`: For TensorFlow Lite (mobile)
- `coreml`: For Apple Core ML (iOS/macOS)

## Tips for Successful Training

### Microorganism-Specific Recommendations

#### For Yeast Detection
```bash
microdetect train --dataset_dir yeast_dataset --model_size s --image_size 800 --epochs 150
```
Yeasts often require higher resolution due to their small size and round shape.

#### For Fungi with Hyphae
```bash
microdetect train --dataset_dir fungi_dataset --model_size m --image_size 640 --epochs 200
```
Complex structures like hyphae benefit from more powerful models and longer training.

#### For Micro-algae
```bash
microdetect train --dataset_dir algae_dataset --model_size s --image_size 640 --epochs 100 --batch_size 8
```
Micro-algae often have distinctive shapes and may require less training time.

### Common Challenges

#### Small Objects
For very small microorganisms:
```bash
microdetect train --dataset_dir dataset --model_size m --image_size 1280
```
Higher resolution inputs help detect smaller objects.

#### Class Imbalance
If your dataset has imbalanced classes:
```bash
microdetect train --dataset_dir dataset --model_size s --class_weights 1.0,2.0,1.5
```
The weights correspond to each class, giving higher importance to underrepresented classes.

#### Overfitting
If you observe overfitting (good training metrics but poor validation):
```bash
microdetect train --dataset_dir dataset --model_size s --augment strong --dropout 0.2
```
Increase data augmentation and add dropout regularization.

## Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| Out of memory errors | Reduce batch size or image size |
| Training loss not decreasing | Try a different learning rate (--lr0 0.001) |
| Poor validation performance | Check data quality, increase augmentation |
| Training too slow | Try a smaller model size or reduce image resolution |
| NaN loss values | Reduce learning rate and check for extreme pixel values |

## Next Steps

After training your model:

- [Checkpoint Management Guide](checkpoint_management.md) - Learn how to manage and resume training from checkpoints
- [Hyperparameter Optimization Guide](hyperparameter_optimization.md) - Fine-tune your model performance
- [Model Evaluation Guide](model_evaluation_analysis.md) - Evaluate your trained model