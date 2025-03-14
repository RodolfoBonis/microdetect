# Data Augmentation Guide

This guide explains how to use MicroDetect's data augmentation tools to enhance your dataset, increase its diversity, and improve model performance.

## Overview

Data augmentation is a technique to artificially expand your dataset by creating modified versions of existing images. This helps to:

- Increase the size of your training dataset
- Improve model generalization
- Make the model more robust to variations in lighting, orientation, and noise
- Reduce overfitting, especially when working with small datasets

MicroDetect provides a comprehensive set of augmentation techniques specifically tailored for microscopy images.

## Basic Usage

### Command Line Interface

The simplest way to augment your dataset is through the command line:

```bash
microdetect augment --image_dir data/images --label_dir data/labels --output_image_dir data/augmented/images --output_label_dir data/augmented/labels --factor 5
```

This command will:
1. Load images from `data/images` and their corresponding labels from `data/labels`
2. Generate 5 augmented versions of each image
3. Save the augmented images and updated labels to the specified output directories

### Command Line Options

| Parameter | Description | Default |
|-----------|-------------|---------|
| `--image_dir` | Directory containing original images | |
| `--label_dir` | Directory containing original labels | |
| `--output_image_dir` | Directory for augmented images | Same as `image_dir` |
| `--output_label_dir` | Directory for augmented labels | Same as `label_dir` |
| `--factor` | Number of augmented versions per image | 5 |
| `--brightness_range` | Range for brightness adjustment | [0.8, 1.2] |
| `--contrast_range` | Range for contrast adjustment | [-30, 30] |
| `--flip_probability` | Probability of horizontal flipping | 0.5 |
| `--rotation_range` | Range for rotation in degrees | [-15, 15] |
| `--noise_probability` | Probability of adding noise | 0.3 |

## Augmentation Techniques

MicroDetect's `DataAugmenter` class implements several augmentation techniques:

### Brightness and Contrast Adjustment

Changes the brightness and contrast of images to simulate different lighting conditions:

```bash
microdetect augment --image_dir images --label_dir labels --brightness_range 0.7,1.3 --contrast_range -40,40
```

### Horizontal Flipping

Flips images horizontally with a specified probability:

```bash
microdetect augment --image_dir images --label_dir labels --flip_probability 0.7
```

Note: Labels are automatically adjusted for flipped images.

### Rotation

Rotates images within a specified range:

```bash
microdetect augment --image_dir images --label_dir labels --rotation_range -20,20
```

### Gaussian Noise

Adds random noise to simulate camera sensor noise:

```bash
microdetect augment --image_dir images --label_dir labels --noise_probability 0.5
```

## Advanced Usage

### Using the Python API

For more control, you can use the `DataAugmenter` class directly in Python:

```python
from microdetect.data.augmentation import DataAugmenter

# Initialize with custom parameters
augmenter = DataAugmenter(
    brightness_range=(0.7, 1.3),
    contrast_range=(-40, 40),
    flip_probability=0.6,
    rotation_range=(-25, 25),
    noise_probability=0.4
)

# Augment data
num_original, num_augmented = augmenter.augment_data(
    input_image_dir="data/images",
    input_label_dir="data/labels",
    output_image_dir="data/augmented/images",
    output_label_dir="data/augmented/labels",
    augmentation_factor=8
)

print(f"Generated {num_augmented} augmented images from {num_original} original images")
```

### Custom Augmentation Pipeline

You can create more complex augmentation pipelines by combining techniques:

```python
import cv2
import numpy as np
from microdetect.data.augmentation import DataAugmenter

class CustomAugmenter(DataAugmenter):
    def augment_image(self, image, annotations):
        # Apply standard augmentations
        augmented_image, augmented_annotations = super().augment_image(image, annotations)
        
        # Apply additional custom augmentations
        
        # Example: Color jittering
        if np.random.random() < 0.3:
            # Convert to HSV and adjust saturation
            hsv = cv2.cvtColor(augmented_image, cv2.COLOR_BGR2HSV)
            hsv[:,:,1] = hsv[:,:,1] * np.random.uniform(0.8, 1.2)
            augmented_image = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
        
        # Example: Blur
        if np.random.random() < 0.2:
            augmented_image = cv2.GaussianBlur(augmented_image, (5, 5), 0)
            
        return augmented_image, augmented_annotations

# Use the custom augmenter
custom_augmenter = CustomAugmenter()
custom_augmenter.augment_data("images", "labels", "augmented/images", "augmented/labels")
```

### Integration with Dataset Management

When preparing your dataset, you can include augmentation as part of the workflow:

```bash
# First, create your dataset structure
microdetect dataset --source_img_dir original/images --source_label_dir original/labels

# Then augment the training set
microdetect augment --image_dir dataset/train/images --label_dir dataset/train/labels --factor 5
```

Note: It's generally recommended to only augment the training set, not the validation or test sets.

## Best Practices

### Augmentation Strategies by Microorganism Type

Different microorganisms benefit from different augmentation strategies:

#### For Yeasts
```bash
microdetect augment --image_dir yeast_images --label_dir yeast_labels \
                    --brightness_range 0.7,1.3 \
                    --contrast_range -30,30 \
                    --flip_probability 0.5 \
                    --rotation_range -180,180  # Yeasts often have circular shape, so full rotation is appropriate
```

#### For Fungi with Hyphae
```bash
microdetect augment --image_dir fungi_images --label_dir fungi_labels \
                    --brightness_range 0.8,1.2 \
                    --contrast_range -20,20 \
                    --flip_probability 0.5 \
                    --rotation_range -30,30  # Limited rotation to maintain characteristic shapes
```

#### For Micro-algae
```bash
microdetect augment --image_dir algae_images --label_dir algae_labels \
                    --brightness_range 0.6,1.4  # Greater brightness variation for fluorescence images
                    --contrast_range -40,40 \
                    --flip_probability 0.5 \
                    --rotation_range -45,45
```

### Finding the Right Balance

- Too little augmentation: Limited generalization improvement
- Too much augmentation: Risk of creating unrealistic images

Start with moderate settings and adjust based on model performance:

1. Train with no augmentation as a baseline
2. Add light augmentation and compare validation metrics
3. Gradually increase augmentation strength until validation metrics plateau or decline

### Dataset Size Considerations

- Small datasets (<100 images): More aggressive augmentation (factor 10-20)
- Medium datasets (100-1000 images): Moderate augmentation (factor 5-10)
- Large datasets (>1000 images): Light augmentation (factor 2-5)

## Evaluating Augmentation Impact

To assess the effectiveness of your augmentation strategy:

```bash
# Train a model without augmentation
microdetect train --dataset_dir original_dataset --output_dir runs/no_augmentation

# Train a model with augmentation
microdetect augment --image_dir original_dataset/train/images --label_dir original_dataset/train/labels
microdetect train --dataset_dir original_dataset --output_dir runs/with_augmentation

# Compare the results
microdetect compare_results --result_dirs runs/no_augmentation,runs/with_augmentation
```

## Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| Augmented annotations outside image boundaries | Reduce rotation range or implement boundary checking |
| Unrealistic brightness/contrast | Narrow the brightness/contrast ranges |
| Too much noise degrades image quality | Reduce noise probability or intensity |
| Long processing time | Consider using fewer augmentations per image or process in batches |

## Next Steps

After augmenting your dataset:

- [Training Guide](training_guide.md) - Train your YOLOv8 model using your augmented dataset
- [Evaluation Guide](model_evaluation_analysis.md) - Evaluate the impact of augmentation on model performance