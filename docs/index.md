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
    <h3>🔄 Automatic Updates</h3>
    <p>Keep your toolkit up-to-date with seamless updates via AWS CodeArtifact integration.</p>
  </div>
</div>

## Getting Started

If you're new to MicroDetect, we recommend starting with these guides:

- [Installation Guide](installation_guide.md) - Comprehensive installation instructions for different environments
- [Quick Start Tutorial](troubleshooting.md) - Begin using MicroDetect with a simple example workflow
- [Common Issues & Solutions](troubleshooting.md) - Solve common problems you might encounter

## Documentation Structure

### Core Workflow Sections

1. **Image Preparation**
   - Converting microscopy images to suitable formats
   - Preprocessing techniques for better detection

2. **Annotation**
   - Manual annotation with the graphical interface
   - Visualization and validation of annotations

3. **Dataset Management**
   - Creating train/validation/test splits
   - Data augmentation for improved model performance

4. **Training**
   - Training YOLOv8 models with different configurations
   - Resuming training from checkpoints
   - Hyperparameter optimization

5. **Evaluation**
   - Assessing model performance with metrics
   - Generating reports and visualizations

### Configuration & Customization

- [Advanced Configuration](advanced_configuration.md) - Detailed options to customize MicroDetect
- [AWS Integration](aws_codeartifact_setup.md) - Setting up AWS CodeArtifact for updates

### Development & Contributing

- [Development Guide](development_guide.md) - Information for developers who want to contribute
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