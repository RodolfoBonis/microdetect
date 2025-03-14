# Checkpoint Management Guide

This guide explains how to effectively manage checkpoints when training YOLOv8 models with MicroDetect, including saving, resuming training, and best practices.

## Overview

Checkpoint management is crucial for efficient model development. MicroDetect's checkpoint functionality allows you to:

- Save model state at regular intervals during training
- Resume training from a saved checkpoint
- Export the best model for deployment
- Analyze different checkpoints to understand model improvement over time

## Understanding Checkpoints

In MicroDetect, a checkpoint is a saved state of the model during training, containing:

- Model weights
- Optimizer state
- Training epoch
- Best metrics achieved
- Learning rate schedule state
- Other training metadata

This allows you to continue training from where you left off without starting from scratch.

## Basic Checkpoint Operations

### Saving Checkpoints

By default, MicroDetect automatically saves checkpoints during training:

```bash
microdetect train --dataset_dir dataset --model_size s --epochs 100
```

This will save:
- `last.pt`: The most recent model state
- `best.pt`: The model with the best validation performance

You can customize the checkpoint saving frequency:

```bash
microdetect train --dataset_dir dataset --save_period 10
```

This saves a checkpoint every 10 epochs.

### Resuming Training

To resume training from a checkpoint:

```bash
microdetect resume --checkpoint_path runs/train/yolov8_s_custom/weights/last.pt --epochs 50
```

This will:
1. Load the model state from the checkpoint
2. Continue training for 50 additional epochs
3. Save results in a new directory (by default)

### Command Line Options

| Parameter | Description | Default |
|-----------|-------------|---------|
| `--checkpoint_path` | Path to the checkpoint file | |
| `--data_yaml` | Path to data.yaml file | `dataset/data.yaml` |
| `--epochs` | Additional epochs to train | `None` (uses original epochs) |
| `--batch_size` | Batch size for continued training | `None` (uses original batch size) |
| `--output_dir` | Directory for saving new results | `runs/train` |

## Advanced Checkpoint Management

### Using the Python API

For more control, you can use the `YOLOTrainer` class directly in Python:

```python
from microdetect.training.train import YOLOTrainer

# Resume training with custom parameters
trainer = YOLOTrainer(
    model_size="s",  # This is not used when resuming but still required
    batch_size=16,   # Override the original batch size
    output_dir="runs/resumed_training"
)

# Resume training with 50 additional epochs
results = trainer.resume_training(
    checkpoint_path="runs/train/yolov8_s_custom/weights/last.pt",
    data_yaml="dataset/data.yaml",
    additional_epochs=50
)

print(f"Training resumed and completed. Best mAP: {results.best_map}")
```

### Checkpoint Frequency Strategies

Different checkpoint saving strategies are suitable for different scenarios:

#### For Long Training Runs
```bash
microdetect train --dataset_dir dataset --model_size l --epochs 300 --save_period 10
```
Save every 10 epochs to track progress without excessive disk usage.

#### For Fine-tuning Runs
```bash
microdetect train --dataset_dir dataset --model_size s --epochs 20 --save_period 1
```
Save every epoch to capture small improvements during fine-tuning.

#### For Volatile Environments
```bash
microdetect train --dataset_dir dataset --model_size m --epochs 100 --save_period 5
```
More frequent checkpoints reduce potential data loss in unstable computing environments.

## Checkpoint Analysis and Management

### Comparing Checkpoints

You can evaluate and compare multiple checkpoints:

```bash
microdetect compare_checkpoints --checkpoints runs/train/exp1/weights/epoch_10.pt,runs/train/exp1/weights/epoch_20.pt,runs/train/exp1/weights/best.pt --data_yaml dataset/data.yaml
```

This generates a comparison report showing metrics for each checkpoint.

### Checkpoint Lifecycle Management

For long-term projects with many training runs:

```bash
microdetect manage_checkpoints --base_dir runs/train --keep best,last,epoch_50,epoch_100
```

This cleans up unnecessary checkpoints, keeping only the specified ones to save disk space.

### Creating Checkpoint Ensembles

Combine multiple checkpoints for potentially better performance:

```bash
microdetect create_ensemble --checkpoints runs/train/exp1/weights/best.pt,runs/train/exp2/weights/best.pt,runs/train/exp3/weights/best.pt --output ensemble.pt
```

## Special Training Scenarios

### Partially Frozen Training

Resume training with certain layers frozen:

```bash
microdetect resume --checkpoint_path runs/train/exp1/weights/best.pt --freeze 10
```

This freezes the first 10 layers of the backbone, useful for fine-tuning.

### Learning Rate Adjustment

Resume with a different learning rate:

```bash
microdetect resume --checkpoint_path runs/train/exp1/weights/best.pt --lr0 0.001
```

This is useful when fine-tuning or when the learning rate at the checkpoint is too high/low.

### Consolidated Training

For multiple short training sessions:

```bash
# First training session
microdetect train --dataset_dir dataset --model_size s --epochs 50

# Resume with additional data
microdetect resume --checkpoint_path runs/train/exp1/weights/best.pt --data_yaml new_dataset/data.yaml --epochs 50
```

This allows incremental training as new data becomes available.

## Best Practices

### Checkpoint Frequency

- For models that take >1 hour to train: Save every 5-10 epochs
- For quick experiments (<30 min): Save every epoch
- Always keep the best and last checkpoints

### Storage Management

- Regular checkpoints can consume significant disk space
- Use `manage_checkpoints` to clean up unnecessary files
- Consider archiving important checkpoints to external storage

### Naming Conventions

Adopt a clear naming convention:

```bash
microdetect train --dataset_dir dataset --model_size s --name "yolov8s_microalgae_v1"
```

This creates checkpoints with meaningful names that indicate the model size and dataset.

### Documentation

Keep notes on training runs and checkpoints:

```bash
microdetect log_experiment --checkpoint_path runs/train/exp1/weights/best.pt --notes "Increased augmentation, focused on small objects" --metrics "mAP50=0.876, precision=0.92"
```

## Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| Cannot resume training (version mismatch) | Ensure the same version of YOLOv8/MicroDetect was used |
| Poor performance after resuming | Check if the learning rate was reset properly |
| Disk space issues with many checkpoints | Use `manage_checkpoints` to clean up old checkpoints |
| Corrupted checkpoint file | Always keep multiple checkpoints (best, last, periodic) |

## Next Steps

After mastering checkpoint management:

- [Hyperparameter Optimization Guide](hyperparameter_optimization.md) - Fine-tune your model performance
- [Model Evaluation Guide](model_evaluation_analysis.md) - Evaluate your trained model
- [Model Deployment Guide](model_deployment.md) - Deploy your model for inference