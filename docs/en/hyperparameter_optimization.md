# Hyperparameter Optimization Guide

This guide explains how to effectively tune your YOLOv8 model hyperparameters using MicroDetect's optimization tools to achieve the best detection performance.

## Overview

Hyperparameters are configuration variables that determine how a model trains and performs. Proper hyperparameter tuning can significantly improve model accuracy, inference speed, and overall performance. MicroDetect provides specialized tools for optimizing YOLOv8 models for microorganism detection.

## Understanding Key Hyperparameters

### Critical Hyperparameters

| Hyperparameter | Description | Impact |
|----------------|-------------|--------|
| Learning Rate (`lr0`) | Initial learning rate | Controls how quickly the model adapts to the problem |
| Batch Size (`batch_size`) | Number of samples processed before updating the model | Affects training stability and speed |
| Image Size (`image_size`) | Input image resolution | Influences detection of small microorganisms |
| Weight Decay (`weight_decay`) | L2 regularization parameter | Controls model complexity to prevent overfitting |
| Mosaic | Data augmentation technique | Increases variability during training |
| Anchors | Base detection box dimensions | Optimized anchors improve detection accuracy |

## Basic Hyperparameter Search

### Command Line Interface

The simplest way to optimize hyperparameters is through the command line:

```bash
microdetect optimize_hyperparams --dataset_dir dataset --model_size s --trials 10
```

This command will:
1. Run 10 training trials with different hyperparameter combinations
2. Evaluate each model's performance
3. Report the best configuration found

### Command Line Options

| Parameter | Description | Default |
|-----------|-------------|---------|
| `--dataset_dir` | Directory containing the dataset | `dataset` |
| `--model_size` | YOLOv8 model size (n, s, m, l, x) | `s` |
| `--trials` | Number of optimization trials | `10` |
| `--epochs_per_trial` | Epochs per optimization trial | `10` |
| `--metric` | Metric to optimize (map50, map50-95, recall, precision) | `map50-95` |
| `--output_dir` | Directory for saving results | `runs/hyp_tuning` |

## Advanced Hyperparameter Optimization

### Using the Python API

For more control, you can use the `YOLOTrainer` class directly in Python:

```python
from microdetect.training.train import YOLOTrainer

# Initialize trainer
trainer = YOLOTrainer(model_size="s")

# Search for best hyperparameters
best_params = trainer.find_best_hyperparameters(
    data_yaml="dataset/data.yaml"
)

print(f"Best hyperparameters found: {best_params}")

# Train with the best hyperparameters
trainer = YOLOTrainer(
    model_size="s",
    batch_size=best_params["batch_size"],
    epochs=100,
    output_dir="runs/optimized_model"
)

results = trainer.train(data_yaml="dataset/data.yaml")
```

### Custom Hyperparameter Search Space

For more control over the search space:

```python
import optuna
from microdetect.training.train import YOLOTrainer

def objective(trial):
    # Define search space
    batch_size = trial.suggest_categorical("batch_size", [8, 16, 32, 64])
    lr0 = trial.suggest_float("lr0", 1e-5, 1e-2, log=True)
    weight_decay = trial.suggest_float("weight_decay", 1e-5, 1e-2, log=True)
    image_size = trial.suggest_categorical("image_size", [512, 640, 768])
    
    # Train with suggested hyperparameters
    trainer = YOLOTrainer(
        model_size="s",
        batch_size=batch_size,
        image_size=image_size,
        epochs=10,
        output_dir=f"runs/hyp_trial_{trial.number}"
    )
    
    # Use custom training arguments
    custom_args = {
        "lr0": lr0,
        "weight_decay": weight_decay,
        "patience": 5,
        "save": False  # Don't save intermediate models
    }
    
    results = trainer.train(data_yaml="dataset/data.yaml", **custom_args)
    
    # Return metric to optimize (higher is better)
    return results.maps.mean()  # Mean mAP

# Create study and optimize
study = optuna.create_study(direction="maximize")
study.optimize(objective, n_trials=20)

print("Best hyperparameters:", study.best_params)
```

## Specialized Optimization Strategies

### Optimizing for Small Microorganisms

Smaller microorganisms (like certain yeasts) require special attention:

```bash
microdetect optimize_hyperparams_small --dataset_dir small_microbes_dataset --model_size m --min_image_size 800 --focus anchor_scale
```

This command focuses on optimizing parameters crucial for small object detection:
- Higher resolution images
- Anchor box scales
- Feature pyramid network settings

### Optimizing for Inference Speed

When deployment speed is critical:

```bash
microdetect optimize_hyperparams_speed --dataset_dir dataset --target_device cpu --max_latency 50
```

This optimizes hyperparameters while keeping inference latency below 50ms on CPU.

### Optimizing for Different Microorganism Types

#### For Yeast Detection
```bash
microdetect optimize_hyperparams --dataset_dir yeast_dataset --model_size s --focus "anchor_scale,image_size"
```

#### For Fungi with Hyphae
```bash
microdetect optimize_hyperparams --dataset_dir fungi_dataset --model_size m --focus "mosaic,mixup,copy_paste"
```
Hyphal structures benefit from augmentation optimizations.

#### For Micro-algae
```bash
microdetect optimize_hyperparams --dataset_dir algae_dataset --model_size s --focus "image_size,focal_loss"
```
Micro-algae often have distinctive shapes but varied sizes.

## Multi-objective Optimization

Balance multiple objectives (accuracy, speed, model size):

```bash
microdetect optimize_multi_objective --dataset_dir dataset --model_size s --objectives "map50-95,latency,param_count" --weights "0.6,0.3,0.1"
```

This optimizes for a weighted combination of model accuracy, inference speed, and model size.

## Best Practices

### Cross-validation During Optimization

For more robust hyperparameter selection:

```bash
microdetect optimize_hyperparams --dataset_dir dataset --model_size s --cross_validation_folds 3
```

This evaluates each hyperparameter set using 3-fold cross-validation for more reliable results.

### Progressive Optimization Strategy

For efficient optimization:

1. Start with a coarse search:
```bash
microdetect optimize_hyperparams --dataset_dir dataset --model_size s --trials 10 --epochs_per_trial 5 --search_strategy coarse
```

2. Refine with a focused search:
```bash
microdetect optimize_hyperparams --dataset_dir dataset --model_size s --trials 10 --epochs_per_trial 10 --search_strategy fine --base_params best_params.yaml
```

### Parameter Freezing

When optimizing a specific aspect:

```bash
microdetect optimize_hyperparams --dataset_dir dataset --model_size s --focus "learning_rate,batch_size" --freeze "image_size=640,weight_decay=0.0005"
```

This freezes certain parameters while optimizing others.

## Visualizing Optimization Results

Generate visualizations of the hyperparameter search:

```bash
microdetect analyze_hyp_results --results_dir runs/hyp_tuning --visualize
```

This creates:
- Parameter importance plots
- Parallel coordinates plot
- Contour plots of key parameter interactions
- Optimization history

## Exporting and Sharing Hyperparameters

Save optimized hyperparameters for future use:

```bash
microdetect export_hyperparams --model_path runs/hyp_tuning/best/weights/best.pt --output hyp_microalgae.yaml
```

Use the exported hyperparameters for training:

```bash
microdetect train --dataset_dir dataset --model_size s --hyperparameters hyp_microalgae.yaml
```

## Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| Optimization taking too long | Reduce `epochs_per_trial` or use a smaller model size |
| Unstable results across trials | Increase `epochs_per_trial` or add cross-validation |
| Out of memory errors | Reduce batch size range or image size range |
| Optimization not improving performance | Check dataset quality or expand hyperparameter search space |

## Next Steps

After optimizing your hyperparameters:

- [Training Guide](training_guide.md) - Train your model with the optimized hyperparameters
- [Model Evaluation Guide](model_evaluation_analysis.md) - Evaluate your optimized model
- [Model Comparison Guide](model_comparison.md) - Compare performance against baseline models