# Image Preprocessing Guide

This guide covers the preprocessing techniques available in MicroDetect for optimizing microscopy images before detection and classification.

## Overview

Image preprocessing is a crucial step in the microorganism detection workflow. Microscopy images often come in specialized formats with particular characteristics that need to be standardized before they can be effectively used for training deep learning models.

## Key Preprocessing Functionalities

### Image Format Conversion

MicroDetect provides tools to convert from specialized microscopy formats (like TIFF, particularly 16-bit TIFFs) to formats optimized for deep learning:

```bash
microdetect convert --input_dir data/raw_images --output_dir data/processed_images --use_opencv
```

#### Conversion Parameters

| Parameter | Description |
|-----------|-------------|
| `--input_dir` | Directory containing source images |
| `--output_dir` | Directory where processed images will be saved |
| `--use_opencv` | Use OpenCV for processing (recommended for most cases) |
| `--format` | Output format (default: png) |
| `--bit_depth` | Output bit depth (default: 8) |
| `--normalize` | Enable normalization for 16-bit to 8-bit conversion |

### Normalization

When converting from 16-bit to 8-bit images, proper normalization is essential to preserve the visible details:

```bash
microdetect convert --input_dir data/raw_images --output_dir data/processed_images --normalize
```

MicroDetect offers multiple normalization strategies:

- **Min-Max Scaling**: Scales the full dynamic range to 0-255
- **Percentile-Based**: Applies normalization based on percentile values (robust to outliers)
- **Histogram Equalization**: Enhances contrast by redistributing intensity values

### Contrast Enhancement

Improve contrast in low-contrast microscopy images:

```bash
microdetect enhance --input_dir data/images --output_dir data/enhanced --method clahe
```

Available enhancement methods:
- `clahe`: Contrast Limited Adaptive Histogram Equalization
- `stretch`: Simple contrast stretching
- `gamma`: Gamma correction (use with `--gamma_value`)

### Noise Reduction

Microscopy images often contain noise that can affect detection accuracy:

```bash
microdetect denoise --input_dir data/images --output_dir data/denoised --method bilateral
```

Available denoising methods:
- `bilateral`: Preserves edges while reducing noise
- `gaussian`: Gaussian blur (faster but less edge-preserving)
- `nlm`: Non-local means (highest quality but slowest)

### Batch Processing

Process multiple images with consistent settings:

```bash
microdetect batch_process --input_dir data/raw_images --output_dir data/processed \
                          --operations "normalize,denoise,enhance" \
                          --params "method=bilateral,strength=10"
```

## Advanced Preprocessing

### Custom Preprocessing Pipeline

Create a custom preprocessing pipeline in Python:

```python
from microdetect.preprocessing import ImageProcessor

processor = ImageProcessor()
processor.add_step("normalize", method="percentile", low=2, high=98)
processor.add_step("denoise", method="bilateral", d=5, sigma_color=75, sigma_space=75)
processor.add_step("enhance", method="clahe", clip_limit=2.0, tile_grid_size=(8, 8))

# Process a single image
processor.process_image("input.tif", "output.png")

# Process a directory
processor.process_directory("input_dir", "output_dir")
```

### Metadata Preservation

When needed, MicroDetect can preserve important metadata during conversion:

```bash
microdetect convert --input_dir data/raw_images --output_dir data/processed_images --preserve_metadata
```

## Best Practices

### For Light Microscopy Images

- Use normalization with percentile clipping (2-98%)
- Apply gentle denoising with bilateral filter
- Consider light CLAHE enhancement if contrast is poor

```bash
microdetect batch_process --input_dir light_microscopy --output_dir processed \
                          --operations "normalize,denoise,enhance" \
                          --params "normalize_method=percentile,low=2,high=98,denoise_method=bilateral,enhance_method=clahe,clip_limit=1.5"
```

### For Fluorescence Microscopy

- Use min-max normalization (often better for fluorescence)
- Apply more aggressive denoising
- Potentially apply channel-specific operations for multi-channel images

```bash
microdetect batch_process --input_dir fluorescence --output_dir processed \
                          --operations "normalize,denoise" \
                          --params "normalize_method=minmax,denoise_method=nlm"
```

### For Phase Contrast Microscopy

- Use histogram equalization for better contrast
- Apply edge enhancement
- Consider background subtraction

```bash
microdetect batch_process --input_dir phase_contrast --output_dir processed \
                          --operations "normalize,enhance,denoise" \
                          --params "normalize_method=equalize,enhance_method=edge,denoise_method=bilateral"
```

## Performance Considerations

- Processing large images can be memory-intensive
- For batch processing of many images, consider using the `--workers` parameter to utilize multiple CPU cores
- GPU acceleration is available for some operations when using the `--use_gpu` flag

## Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| Too bright/dark images after conversion | Adjust normalization parameters |
| Blurry images after denoising | Reduce filter strength or choose a different method |
| Processing very large images fails | Use `--max_size` parameter to resize during processing |
| Missing details in converted images | Try different bit depth handling methods |

For more specific issues, refer to the [Troubleshooting Guide](troubleshooting.md).

## Next Steps

After preprocessing your images, you can proceed to:

- [Annotation Guide](annotation_guide.md) - Annotate your preprocessed images
- [Dataset Management Guide](dataset_management.md) - Prepare your annotated images for training