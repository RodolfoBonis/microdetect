# Image Conversion Guide

This guide explains how to use MicroDetect's image conversion tools to prepare microscopy images for optimal analysis and detection.

## Table of Contents
- [Introduction](#introduction)
- [Supported Image Formats](#supported-image-formats)
- [Basic Image Conversion](#basic-image-conversion)
- [Advanced Conversion Options](#advanced-conversion-options)
  - [Format Selection](#format-selection)
  - [Quality Settings](#quality-settings)
  - [Resizing Images](#resizing-images)
  - [Preserving Metadata](#preserving-metadata)
  - [Using OpenCV vs PIL](#using-opencv-vs-pil)
- [Batch Processing](#batch-processing)
- [16-bit to 8-bit Conversion](#16-bit-to-8-bit-conversion)
- [Handling Special Microscopy Formats](#handling-special-microscopy-formats)
  - [Multi-page TIFF Files](#multi-page-tiff-files)
  - [Z-stacks](#z-stacks)
  - [Time Series](#time-series)
- [Integration with Preprocessing](#integration-with-preprocessing)
- [Configuration](#configuration)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)

## Introduction

Microscopy images often come in specialized formats (like TIFF) with high bit depths that aren't optimally compatible with deep learning workflows. MicroDetect provides tools to convert these images to formats that are better suited for microorganism detection while preserving important details.

The image conversion tools help you:
- Convert specialized microscopy formats to standard formats
- Normalize bit depth (e.g., from 16-bit to 8-bit)
- Optimize image storage and processing efficiency
- Prepare images for training and inference
- Apply basic preprocessing during conversion

## Supported Image Formats

**Input Formats**:
- TIFF (.tif, .tiff) - including multi-page and high bit-depth
- BMP (.bmp)
- JPEG (.jpg, .jpeg)
- PNG (.png)
- GIF (.gif)
- Various microscopy-specific formats (with optional dependencies)

**Output Formats**:
- PNG (.png) - default, lossless with good compression
- JPEG (.jpg) - lossy with configurable quality
- TIFF (.tif) - for cases where preservation of specific data is needed

## Basic Image Conversion

To convert images from one format to another:

```bash
microdetect convert --input_dir path/to/input_images --output_dir path/to/output_images
```

This command:
- Processes all supported images in the input directory
- Converts them to PNG format by default
- Saves the converted images to the output directory
- Preserves the original filename with the new extension

## Advanced Conversion Options

### Format Selection

To specify the output format:

```bash
microdetect convert --input_dir path/to/input_images --output_dir path/to/output_images --format jpg
```

Supported format values:
- `png` - Lossless format, good for preservation of details (default)
- `jpg` - Smaller file size, lossy compression
- `tif` - For preserving additional data layers

### Quality Settings

For JPEG format, you can set the compression quality:

```bash
microdetect convert --input_dir path/to/input_images --output_dir path/to/output_images --format jpg --quality 90
```

The quality parameter ranges from 1 (lowest quality, smallest file) to 100 (highest quality, largest file). The default is 95.

### Resizing Images

To resize images during conversion:

```bash
microdetect convert --input_dir path/to/input_images --output_dir path/to/output_images --resize --max_size 1024 1024
```

This resizes images to fit within the specified dimensions while maintaining the aspect ratio. The `--max_size` parameter takes width and height values.

### Preserving Metadata

By default, MicroDetect attempts to preserve EXIF metadata during conversion:

```bash
microdetect convert --input_dir path/to/input_images --output_dir path/to/output_images --preserve_metadata
```

To disable metadata preservation:

```bash
microdetect convert --input_dir path/to/input_images --output_dir path/to/output_images --no-preserve_metadata
```

### Using OpenCV vs PIL

MicroDetect supports two image processing backends:

```bash
# Use OpenCV (better for scientific images)
microdetect convert --input_dir path/to/input_images --output_dir path/to/output_images --use_opencv

# Use PIL (Python Imaging Library)
microdetect convert --input_dir path/to/input_images --output_dir path/to/output_images --no-use_opencv
```

OpenCV generally provides better support for scientific image formats and bit depth conversion, while PIL may have better metadata preservation.

## Batch Processing

For large datasets, batch processing is automatically enabled:

```bash
microdetect convert --input_dir path/to/input_images --output_dir path/to/output_images --workers 4
```

The `--workers` parameter controls the number of parallel conversion processes. By default, it uses the number of available CPU cores.

## 16-bit to 8-bit Conversion

Many microscopy images are stored in 16-bit format, but deep learning models typically work with 8-bit images. MicroDetect automatically handles this conversion:

```bash
microdetect convert --input_dir path/to/16bit_images --output_dir path/to/8bit_images --use_opencv
```

The conversion uses intelligent scaling to preserve as much information as possible:

1. For normal 16-bit range images, linear scaling is applied
2. For microscopy images with concentrated values, histogram equalization may be applied
3. For fluorescence microscopy with extreme peaks, logarithmic scaling may be used

You can specify the scaling method explicitly:

```bash
microdetect convert --input_dir path/to/16bit_images --output_dir path/to/8bit_images --bit_conversion linear
```

Available methods:
- `linear` - Simple linear scaling (default)
- `equalize` - Histogram equalization
- `adaptive` - Automatically select the best method
- `log` - Logarithmic scaling for extreme dynamic ranges

## Handling Special Microscopy Formats

### Multi-page TIFF Files

For multi-page TIFF files (common in microscopy z-stacks or time series):

```bash
microdetect convert --input_dir path/to/multipage_tiffs --output_dir path/to/output_images --handle_multipage extract_all
```

Options for `--handle_multipage`:
- `extract_all` - Extract all pages as separate images
- `first_only` - Extract only the first page (default)
- `max_projection` - Create a maximum intensity projection (useful for z-stacks)

### Z-stacks

For Z-stack images (3D volumes):

```bash
microdetect convert --input_dir path/to/zstacks --output_dir path/to/output_images --handle_multipage max_projection
```

This creates a maximum intensity projection, combining the strongest signals from all z-slices.

### Time Series

For time series data:

```bash
microdetect convert --input_dir path/to/time_series --output_dir path/to/output_images --handle_multipage extract_all --naming_pattern {basename}_t{page:03d}
```

The `--naming_pattern` parameter controls how extracted pages are named, using Python's string formatting with:
- `{basename}` - Original filename without extension
- `{page}` - Page number (0-based)
- `{page:03d}` - Page number with leading zeros

## Integration with Preprocessing

Image conversion can be combined with basic preprocessing:

```bash
microdetect convert --input_dir path/to/input_images --output_dir path/to/output_images --normalize_contrast --normalize_brightness
```

Available preprocessing options:
- `--normalize_contrast` - Enhance contrast using histogram equalization
- `--normalize_brightness` - Adjust brightness to a standard level
- `--remove_background` - Attempt to remove uniform backgrounds
- `--denoise` - Apply noise reduction filtering

For more advanced preprocessing, see the [Preprocessing Guide](preprocessing.md).

## Configuration

You can configure default conversion settings in the `config.yaml` file:

```yaml
conversion:
  format: png                     # Target format (png, jpg)
  quality: 95                     # Quality for JPG
  use_opencv: true                # Use OpenCV instead of PIL
  delete_original: false          # Delete original file after conversion
  preserve_metadata: true         # Preserve EXIF metadata
  resize: false                   # Resize images
  max_size: [1024, 1024]          # Maximum size after resizing
  bit_conversion: linear          # 16-bit to 8-bit conversion method
  handle_multipage: first_only    # How to handle multi-page files
  naming_pattern: "{basename}_p{page:03d}"  # Naming pattern for extracted pages
```

## Best Practices

1. **Preserve original images**: Keep the original images as a backup before conversion

2. **Use PNG for training data**: PNG provides lossless compression and is well-supported by deep learning frameworks

3. **Process representative samples first**: Test your conversion settings on a few representative images before processing the entire dataset

4. **Check converted images**: Visually inspect converted images to ensure important details are preserved

5. **Consider resolution requirements**: Higher resolution isn't always better for detection; many models work well with images around 640-1280 pixels

6. **Use OpenCV for scientific images**: OpenCV provides better handling of scientific image formats and bit depth conversion

7. **Match preprocessing to your data**: Different microscopy techniques may require different preprocessing approaches

8. **Document your conversion settings**: Keep track of how you processed your images for reproducibility

## Troubleshooting

### Problem: Dark or Low Contrast Converted Images
**Solution**: Try different bit conversion methods:
```bash
microdetect convert --input_dir path/to/16bit_images --output_dir path/to/8bit_images --bit_conversion equalize
```

### Problem: Out of Memory with Large Images
**Solution**: Process images in smaller batches or resize them during conversion:
```bash
microdetect convert --input_dir path/to/large_images --output_dir path/to/output_images --resize --max_size 2048 2048
```

### Problem: Missing Pages from Multi-page TIFFs
**Solution**: Ensure you're using the correct multipage handling option:
```bash
microdetect convert --input_dir path/to/multipage_tiffs --output_dir path/to/output_images --handle_multipage extract_all
```

### Problem: Conversion Very Slow
**Solution**: Increase the number of worker processes:
```bash
microdetect convert --input_dir path/to/input_images --output_dir path/to/output_images --workers 8
```

### Problem: File Format Not Recognized
**Solution**: Install additional dependencies for specialized formats:
```bash
pip install tifffile bioformats
```

### Problem: Loss of Scale Information
**Solution**: Preserve metadata and consider tracking resolution separately:
```bash
microdetect convert --input_dir path/to/input_images --output_dir path/to/output_images --preserve_metadata
```

For more troubleshooting information, see the [Troubleshooting Guide](troubleshooting.md).