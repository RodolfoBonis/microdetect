# Cross-Validation and Benchmarking Guide

This guide explains how to use MicroDetect's cross-validation and benchmarking tools to thoroughly evaluate model performance and analyze resource usage.

## Table of Contents
- [Introduction](#introduction)
- [Cross-Validation](#cross-validation)
  - [Basic Usage](#basic-usage)
  - [Understanding Results](#understanding-results)
  - [Customizing Cross-Validation](#customizing-cross-validation)
- [Performance Benchmarking](#performance-benchmarking)
  - [Speed Benchmarking](#speed-benchmarking)
  - [Resource Monitoring](#resource-monitoring)
  - [Visualizing Benchmark Results](#visualizing-benchmark-results)
- [Model Comparison](#model-comparison)
  - [Basic Comparison](#basic-comparison)
  - [Advanced Comparison](#advanced-comparison)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)

## Introduction

Robust model evaluation is essential for developing reliable microorganism detection systems. MicroDetect provides two powerful evaluation tools:

- **Cross-Validation**: Evaluates model stability and reliability across different data subsets
- **Benchmarking**: Measures model speed, throughput, and resource usage

These tools help you:
- Identify overfitting and data bias
- Understand your model's performance across different data distributions
- Optimize for deployment by measuring speed and resource requirements
- Make informed decisions about model size and configuration

## Cross-Validation

Cross-validation is a technique for evaluating model performance by training and testing on different data subsets. MicroDetect implements k-fold cross-validation, where the dataset is divided into k equal parts (folds), and the model is trained k times, each time using a different fold as the test set.

### Basic Usage

To run cross-validation with 5 folds:

```python
from microdetect.training import CrossValidator

validator = CrossValidator(
    base_dataset_dir="dataset",
    output_dir="cv_results",
    model_size="m",
    epochs=100,
    folds=5,
    seed=42
)

# Run the cross-validation
results = validator.run()

# Generate a report
report_path = validator.generate_report()
```

This creates the following structure:
```
cv_results/
├── fold_1/
│   ├── train/
│   ├── val/
│   ├── runs/
│   ├── evaluation/
│   └── data.yaml
├── fold_2/
│   ├── ...
...
├── cross_validation_plot.png
└── cross_validation_report.json
```

### Understanding Results

The cross-validation report (`cross_validation_report.json`) contains:

```json
{
  "cross_validation": {
    "folds": 5,
    "model_size": "m",
    "epochs": 100,
    "seed": 42
  },
  "average_metrics": {
    "map50": 0.845,
    "map50_95": 0.623,
    "recall": 0.812,
    "precision": 0.867,
    "f1_score": 0.838
  },
  "std_metrics": {
    "map50": 0.035
  },
  "fold_results": [
    {
      "fold": 1,
      "train_files": 342,
      "val_files": 86,
      "model_path": "cv_results/fold_1/runs/train/weights/best.pt",
      "metrics": {
        "metricas_gerais": {
          "Precisão (mAP50)": 0.856,
          "Precisão (mAP50-95)": 0.634,
          "Recall": 0.823,
          "Precisão": 0.878,
          "F1-Score": 0.849
        },
        "metricas_por_classe": [
          ...
        ]
      }
    },
    ...
  ]
}
```

The `cross_validation_plot.png` shows metrics for each fold, helping you identify:
- Performance consistency across folds
- Potential data skew (if one fold performs significantly differently)
- Average performance with standard deviation

### Customizing Cross-Validation

You can customize cross-validation with:

```python
validator = CrossValidator(
    base_dataset_dir="dataset",
    output_dir="cv_results",
    model_size="s",        # Use a smaller model (n, s, m, l, x)
    epochs=50,             # Fewer epochs for faster training
    folds=10,              # More folds for finer-grained evaluation
    seed=123               # Different seed for reproducibility
)
```

## Performance Benchmarking

MicroDetect offers two types of benchmarking:
1. **Speed Benchmarking**: Evaluates inference speed across different batch sizes and image sizes
2. **Resource Monitoring**: Measures CPU, memory, and GPU usage during model execution

### Speed Benchmarking

To benchmark model speed:

```python
from microdetect.training import SpeedBenchmark

benchmark = SpeedBenchmark(model_path="runs/train/exp/weights/best.pt")

# Run benchmark with different configurations
results = benchmark.run(
    batch_sizes=[1, 2, 4, 8, 16],        # Test different batch sizes
    image_sizes=[640, 960, 1280],        # Test different image sizes
    iterations=50,                        # Number of inference iterations
    warmup=10                             # Number of warmup iterations
)

# Generate visualization
plot_path = benchmark.plot_results("benchmark_results.png")

# Save detailed results
benchmark.save_results("benchmark_results.csv")
```

The results show:
- Average inference time per sample
- Frames per second (FPS)
- Samples processed per second
- How performance scales with batch size and image size

Example output:
```
Batch Size: 1, Image Size: 640, Latency: 25.4ms, FPS: 39.4
Batch Size: 2, Image Size: 640, Latency: 43.2ms, FPS: 46.3
Batch Size: 4, Image Size: 640, Latency: 82.7ms, FPS: 48.4
...
```

### Resource Monitoring

To monitor resource usage during model execution:

```python
from microdetect.training import ResourceMonitor, YOLOTrainer

# Start monitoring
monitor = ResourceMonitor()
monitor.start()

# Run your model (example: training)
trainer = YOLOTrainer(model_size="m", epochs=100)
trainer.train("dataset/data.yaml")

# Stop monitoring and get statistics
stats = monitor.stop()
print(f"CPU usage (avg): {stats['cpu_percent_avg']}%")
print(f"Memory usage (max): {stats['memory_percent_max']}%")

# Generate usage graph
monitor.plot_usage("resource_usage.png")
```

This generates a time-series plot showing:
- CPU usage over time
- Memory usage over time
- GPU usage (if available)

Resource monitoring helps you:
- Identify performance bottlenecks
- Plan hardware requirements for deployment
- Compare efficiency of different model sizes

### Visualizing Benchmark Results

Speed benchmark visualization includes:
- **FPS vs. Batch Size**: Shows how throughput scales with batch size
- **Throughput vs. Image Size**: Shows performance impact of image resolution
- **Latency Distribution**: Shows consistency of inference times

Resource monitoring visualization includes:
- **CPU Usage**: Time-series of CPU utilization
- **Memory Usage**: Time-series of RAM consumption
- **GPU Usage**: Time-series of GPU utilization (if available)

## Model Comparison

### Basic Comparison

To compare different model sizes or configurations:

```python
from microdetect.training import ModelComparator

comparator = ModelComparator(output_dir="model_comparison")

# Compare multiple models
results = comparator.compare_models(
    model_paths=[
        "runs/train/yolov8n_custom/weights/best.pt",
        "runs/train/yolov8s_custom/weights/best.pt",
        "runs/train/yolov8m_custom/weights/best.pt"
    ],
    data_yaml="dataset/data.yaml",
    conf_threshold=0.25,
    iou_threshold=0.7
)
```

This generates:
- Comparative performance metrics (mAP50, recall, precision)
- Speed measurements for each model
- Visualizations showing the trade-off between accuracy and speed
- Size comparison (model parameters and file size)

### Advanced Comparison

For more interactive comparison:

```bash
microdetect compare_models --model_paths model1.pt,model2.pt,model3.pt --data_yaml dataset/data.yaml --dashboard
```

This launches an interactive dashboard showing:
- Side-by-side metrics comparison
- Trade-off visualization (precision vs. speed)
- Model size comparison
- Performance by class

## Best Practices

1. **Use consistent data**: Make sure all folds in cross-validation have similar class distributions

2. **Run multiple benchmarks**: For reliable speed measurements, run benchmarks multiple times and average the results

3. **Prioritize relevant metrics**: Focus on metrics that matter for your application (e.g., precision vs. speed)

4. **Match benchmark conditions to deployment**: Test with batch sizes and image sizes you'll use in production

5. **Consider resource constraints**: If deploying on resource-limited devices, prioritize models with lower resource usage

6. **Set appropriate seeds**: Use seed values for reproducible cross-validation results

7. **Compare models comprehensively**: Don't just look at accuracy; consider speed, size, and resource usage

## Troubleshooting

### Issue: Cross-validation takes too long
**Solution**: Reduce the number of epochs or use a smaller model size for initial validation

### Issue: Out of memory during cross-validation
**Solution**: Reduce batch size or image size; use a smaller model size; process one fold at a time

### Issue: Inconsistent benchmark results
**Solution**: Increase the number of iterations; use a warmup period; close other applications during benchmarking

### Issue: Resource monitor shows minimal GPU usage
**Solution**: Verify GPU is correctly configured; ensure PyTorch is using CUDA or MPS

### Issue: Large standard deviation in cross-validation results
**Solution**: Increase the number of folds; check for class imbalance; verify data quality across all samples

For more troubleshooting help, see the [Troubleshooting Guide](troubleshooting.md).