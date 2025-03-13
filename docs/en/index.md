# MicroDetect Documentation

Welcome to the MicroDetect documentation portal. Here you'll find comprehensive guides and information to help you get the most out of MicroDetect.

## What is MicroDetect?

**MicroDetect** is a specialized toolkit for detecting and classifying microorganisms in microscopy images using the YOLOv8 object detection framework. It provides a complete workflow from image preparation to model evaluation, designed specifically for microscopy applications in microbiology, biotechnology, and related fields.

## Key Features

<div class="feature-grid">
  <div class="feature-card">
    <h3>🔍 Image Conversion</h3>
    <p>Convert TIFF microscopy images to formats optimized for deep learning, with support for 16-bit to 8-bit normalization.</p>
  </div>
  
  <div class="feature-card">
    <h3>🏷️ Smart Annotation</h3>
    <p>User-friendly graphical interface for annotating microorganisms with resumable sessions and progress tracking.</p>
  </div>
  
  <div class="feature-card">
    <h3>👁️ Visualization</h3>
    <p>Tools to review and validate annotations with class filtering and batch processing capabilities.</p>
  </div>
  
  <div class="feature-card">
    <h3>🔄 Data Augmentation</h3>
    <p>Enhance your datasets with techniques like brightness adjustment, rotation, flipping, and noise addition.</p>
  </div>
  
  <div class="feature-card">
    <h3>📊 Dataset Management</h3>
    <p>Organize your data into train/validation/test splits with proper YOLO format configuration.</p>
  </div>
  
  <div class="feature-card">
    <h3>🧠 Model Training</h3>
    <p>Train YOLOv8 models with checkpoint support, early stopping, and hyperparameter optimization.</p>
  </div>
  
  <div class="feature-card">
    <h3>📈 Evaluation</h3>
    <p>Comprehensive evaluation metrics, confusion matrices, and visual reports for model assessment.</p>
  </div>
  
  <div class="feature-card">
    <h3>🔍 Error Analysis</h3>
    <p>Detailed analysis of false positives, false negatives, and other detection errors to improve model performance.</p>
  </div>
  
  <div class="feature-card">
    <h3>📊 Statistical Analysis</h3>
    <p>Analyze spatial distribution, size patterns, and temporal changes in microorganism populations.</p>
  </div>
  
  <div class="feature-card">
    <h3>⚖️ Model Comparison</h3>
    <p>Compare performance across different model sizes and configurations to find the optimal balance.</p>
  </div>
  
  <div class="feature-card">
    <h3>🔄 Cross-Validation</h3>
    <p>Validate model performance across different data splits with k-fold cross-validation.</p>
  </div>
  
  <div class="feature-card">
    <h3>⏱️ Benchmarking</h3>
    <p>Measure inference speed, throughput, and hardware resource utilization for different model configurations.</p>
  </div>
  
  <div class="feature-card">
    <h3>🔄 Automatic Updates</h3>
    <p>Keep your toolkit up-to-date with seamless updates via AWS CodeArtifact integration.</p>
  </div>
</div>

## Getting Started

If you're new to MicroDetect, we recommend starting with these guides:

- [Installation Guide](installation_guide.md) - Comprehensive installation instructions for different environments
- [Troubleshooting](troubleshooting.md) - Solve common problems you might encounter

## Documentation Structure

### Core Workflow Sections

1. **Image Preparation**
   - [Image Conversion Guide](image_conversion.md) - Converting microscopy images to suitable formats
   - [Preprocessing Guide](preprocessing.md) - Preprocessing techniques for better detection

2. **Annotation**
   - [Annotation Guide](annotation_guide.md) - Manual annotation with the graphical interface
   - [Visualization Guide](visualization.md) - Visualization and validation of annotations

3. **Dataset Management**
   - [Dataset Management Guide](dataset_management.md) - Creating train/validation/test splits
   - [Data Augmentation Guide](data_augmentation.md) - Data augmentation for improved model performance

4. **Training**
   - [Training Guide](training_guide.md) - Training YOLOv8 models with different configurations
   - [Checkpoint Management](checkpoint_management.md) - Resuming training from checkpoints
   - [Hyperparameter Optimization](hyperparameter_optimization.md) - Optimizing model parameters

5. **Evaluation**
   - [Basic Evaluation Guide](basic_evaluation.md) - Assessing model performance with metrics
   - [Model Evaluation & Analysis](model_evaluation_analysis.md) - Comprehensive model evaluation

### Advanced Analysis and Tools

1. **Model Evaluation & Analysis**
   - [Model Evaluation Guide](model_evaluation_analysis.md) - Comprehensive model evaluation metrics and visualization
   - [Cross-Validation Guide](cross_validation_benchmarking.md) - K-fold cross-validation and model stability analysis
   - [Benchmarking Guide](cross_validation_benchmarking.md) - Speed and resource utilization benchmarking
   - [Model Comparison Guide](model_comparison.md) - Comparing different models and configurations

2. **Error Analysis**
   - [Error Analysis Guide](error_analysis.md) - Identifying and analyzing detection errors
   - [False Positive Analysis](error_analysis.md#false-positives) - Understanding and reducing false positives
   - [False Negative Analysis](error_analysis.md#false-negatives) - Identifying missed detections
   - [Classification Error Analysis](error_analysis.md#classification-errors) - Analyzing misclassifications

3. **Visualization and Reporting**
   - [Visualization Tools](visualization_tools.md) - Tools for visualizing results and generating reports
   - [Interactive Dashboards](visualization_tools.md#interactive-dashboards) - Creating interactive dashboards for data exploration
   - [Report Generation](visualization_tools.md#report-generation) - Creating PDF and CSV reports
   - [Detection Visualization](visualization_tools.md#detection-visualization) - Visualizing detection results

4. **Statistical Analysis**
   - [Statistical Analysis Guide](statistical_analysis.md) - Analyzing distributions, patterns, and relationships
   - [Density Analysis](statistical_analysis.md#density-analysis) - Analyzing concentration of microorganisms
   - [Size Distribution Analysis](statistical_analysis.md#size-distribution-analysis) - Analyzing microorganism sizes
   - [Spatial Analysis](statistical_analysis.md#spatial-analysis) - Analyzing spatial relationships
   - [Temporal Analysis](statistical_analysis.md#temporal-analysis) - Tracking changes over time

5. **Batch Processing**
   - [Batch Processing Guide](statistical_analysis.md#batch-processing) - Processing large datasets efficiently
   - [Parallel Processing](statistical_analysis.md#processing-multiple-images) - Using multiple workers for faster processing
   - [Custom Analysis Functions](statistical_analysis.md#custom-analysis-functions) - Creating custom analysis pipelines

### Configuration & Customization

- [Advanced Configuration](advanced_configuration.md) - Detailed options to customize MicroDetect
- [Configuration File Reference](configuration_reference.md) - Complete reference for config.yaml options
- [AWS Integration](aws_codeartifact_setup.md) - Setting up AWS CodeArtifact for updates
- [Environment Variables](environment_variables.md) - Configuring MicroDetect with environment variables

### Development & Contributing

- [Development Guide](development_guide.md) - Information for developers who want to contribute
- [Project Structure](development_guide.md#architecture-overview) - Understanding the codebase structure
- [Development Environment](development_guide.md#setting-up-development-environment) - Setting up for development
- [Testing Guide](development_guide.md#testing) - Writing and running tests
- [Documentation Guide](development_guide.md#documentation) - Contributing to documentation
- [Release & Update Model](update_and_release_model.md) - Understanding version management

## Command Line Interface

MicroDetect provides a comprehensive command-line interface:

```bash
# Get help on available commands
microdetect --help

# Get help on a specific command
microdetect annotate --help
```

### Core Commands

```bash
# Initialize a new project
microdetect init

# Convert images
microdetect convert --input_dir [input] --output_dir [output]

# Annotate images
microdetect annotate --image_dir [images] --output_dir [labels]

# Visualize annotations
microdetect visualize --image_dir [images] --label_dir [labels]

# Prepare dataset
microdetect dataset --source_img_dir [images] --source_label_dir [labels]

# Augment data
microdetect augment --image_dir [images] --label_dir [labels] --factor [number]

# Train model
microdetect train --dataset_dir [dataset] --model_size [s/m/l/x]

# Evaluate model
microdetect evaluate --model_path [model.pt] --dataset_dir [dataset]

# Analyze errors
microdetect analyze_errors --model_path [model.pt] --dataset_dir [dataset]

# Compare models
microdetect compare_models --model_paths [models] --data_yaml [data.yaml]

# Process detections in batch
microdetect batch_detect --model_path [model.pt] --source [images]

# Visualize detections interactively
microdetect visualize_detections --model_path [model.pt] --source [images]

# Generate statistical analysis
microdetect analyze_distribution --model_path [model.pt] --source [images]

# Generate reports
microdetect generate_report --results_dir [results] --format [pdf/csv]

# Launch dashboard
microdetect dashboard --results_dir [results]

# Check for updates
microdetect update --check-only

# View this documentation
microdetect docs
```

## System Requirements

- **Python:** 3.9 or newer
- **RAM:** 4GB minimum (8GB+ recommended for training)
- **GPU:** Optional but recommended for training (CUDA or Apple Silicon MPS supported)
- **Storage:** 2GB minimum for installation and basic use

## Support

If you encounter issues or have questions not covered in this documentation:

1. Check the [Troubleshooting Guide](troubleshooting.md)
2. Search or open an issue on [GitHub](https://github.com/RodolfoBonis/microdetect/issues)
3. Contact the development team at dev@rodolfodebonis.com.br

---

<div class="footer-note">
  <p>MicroDetect is an open-source project developed to assist researchers and professionals in the field of microbiology and microscopy.</p>
</div>