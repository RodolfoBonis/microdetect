# Statistical Analysis Guide

This guide explains how to use MicroDetect's statistical analysis tools to extract insights from detection results.

## Table of Contents
- [Introduction](#introduction)
- [Density Analysis](#density-analysis)
  - [Generating Density Maps](#generating-density-maps)
  - [Interpreting Density Maps](#interpreting-density-maps)
  - [Class-Specific Density Analysis](#class-specific-density-analysis)
- [Size Distribution Analysis](#size-distribution-analysis)
  - [Basic Size Analysis](#basic-size-analysis)
  - [Size Statistics](#size-statistics)
  - [Comparing Classes](#comparing-classes)
- [Spatial Analysis](#spatial-analysis)
  - [Distance Analysis](#distance-analysis)
  - [Clustering Analysis](#clustering-analysis)
  - [Class Relationship Analysis](#class-relationship-analysis)
- [Temporal Analysis](#temporal-analysis)
  - [Tracking Changes Over Time](#tracking-changes-over-time)
  - [Growth Rate Analysis](#growth-rate-analysis)
- [Batch Processing](#batch-processing)
  - [Processing Multiple Images](#processing-multiple-images)
  - [Custom Analysis Functions](#custom-analysis-functions)
- [Integrating with Other Tools](#integrating-with-other-tools)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)

## Introduction

Statistical analysis of detection results helps extract meaningful patterns and insights from microorganism data. MicroDetect provides several tools for analyzing:

- **Spatial Distribution**: Where microorganisms appear in images
- **Size Distribution**: How microorganism sizes vary
- **Density Patterns**: Concentrations and clusters
- **Relationships**: How different classes relate spatially
- **Temporal Changes**: How populations change over time

These analyses help you:
- Understand microorganism population characteristics
- Identify spatial patterns and relationships
- Track changes in populations over time
- Make data-driven decisions

## Density Analysis

Density analysis visualizes the concentration of detections across images, showing where microorganisms commonly appear.

### Generating Density Maps

To create density maps from detection results:

```python
from microdetect.analysis import StatisticalAnalyzer

analyzer = StatisticalAnalyzer(output_dir="analysis_results")

# Generate a density map from detections
density_map_path = analyzer.generate_density_map(
    detections=detection_results,              # List of detection dictionaries
    image_size=(1280, 960),                    # Width, height of the image
    output_path="density_map.png",             # Path to save the map
    sigma=10.0,                                # Smoothing parameter
    by_class=False                             # Generate a single map for all classes
)
```

You can also use the command-line interface:

```bash
microdetect analyze_distribution --model_path runs/train/exp/weights/best.pt \
                                --source path/to/images \
                                --output_dir density_maps \
                                --sigma 10.0
```

### Interpreting Density Maps

Density maps use color gradients to show concentration:
- **Red/Yellow areas**: High concentration of detections
- **Green areas**: Moderate concentration
- **Blue areas**: Low concentration
- **Dark blue areas**: Few or no detections

Density maps help identify:
- Hotspots where microorganisms frequently appear
- Empty regions with few or no detections
- Gradients that might indicate environmental factors

### Class-Specific Density Analysis

To analyze density patterns for specific classes:

```python
# Generate separate density maps for each class
class_density_maps = analyzer.generate_density_map(
    detections=detection_results,
    image_size=(1280, 960),
    output_path="density_maps/all_classes.png",
    by_class=True                  # Generate separate maps for each class
)

# Access individual class maps
print(f"Map for class 0: {class_density_maps['0']}")
print(f"Map for class 1: {class_density_maps['1']}")
```

Using the command-line interface with the `--by_class` flag:

```bash
microdetect analyze_distribution --model_path runs/train/exp/weights/best.pt \
                                --source path/to/images \
                                --output_dir density_maps \
                                --by_class
```

## Size Distribution Analysis

Size distribution analysis examines the variation in microorganism sizes across your dataset.

### Basic Size Analysis

To analyze the size distribution of detected microorganisms:

```python
from microdetect.analysis import StatisticalAnalyzer

analyzer = StatisticalAnalyzer(output_dir="analysis_results")

# Analyze size distribution
size_analysis_results = analyzer.analyze_size_distribution(
    detections=detection_results,              # List of detection dictionaries
    output_dir="size_analysis",                # Directory to save results
    by_class=True                              # Separate analysis by class
)
```

Using the command-line interface:

```bash
microdetect analyze_size --model_path runs/train/exp/weights/best.pt \
                        --source path/to/images \
                        --output_dir size_analysis
```

This generates:
- Histograms showing overall size distribution
- Class-specific size distribution histograms
- CSV data for further analysis
- Statistical summary in JSON format

### Size Statistics

The size analysis produces a JSON file (`size_stats.json`) with statistics:

```json
{
  "all": {
    "mean": 124.5,
    "median": 118.2,
    "std": 32.7,
    "min": 45.3,
    "max": 278.9,
    "count": 523
  },
  "class_0": {
    "mean": 135.8,
    "median": 129.4,
    "std": 35.2,
    "min": 48.7,
    "max": 278.9,
    "count": 312
  },
  "class_1": {
    "mean": 107.3,
    "median": 102.8,
    "std": 22.5,
    "min": 45.3,
    "max": 189.6,
    "count": 211
  }
}
```

These statistics help you:
- Understand the typical size range for each microorganism type
- Identify outliers that might indicate detection errors
- Compare size distributions between classes

### Comparing Classes

The `size_distribution_by_class.png` visualization shows size distributions for all classes on a single graph, making it easy to compare:
- Size ranges between different microorganism types
- Overlap between size distributions
- Potential size-based classification rules

## Spatial Analysis

Spatial analysis examines the relationships and patterns in the positions of detected microorganisms.

### Distance Analysis

To analyze the distances between detected microorganisms:

```python
from microdetect.analysis import StatisticalAnalyzer

analyzer = StatisticalAnalyzer(output_dir="analysis_results")

# Analyze spatial relationships
spatial_results = analyzer.analyze_spatial_relationships(
    detections=detection_results,              # List of detection dictionaries
    output_dir="spatial_analysis",             # Directory to save results
    min_distance=0.02,                         # Minimum distance for clustering
    by_class=True                              # Analyze relationships between classes
)
```

Using the command-line interface:

```bash
microdetect analyze_spatial --model_path runs/train/exp/weights/best.pt \
                           --source path/to/images \
                           --output_dir spatial_analysis \
                           --min_distance 0.02
```

The distance analysis produces:
- Histogram of distances between microorganisms
- Scatter plot showing spatial distribution
- Nearest neighbor statistics

### Clustering Analysis

Clustering analysis identifies groups of microorganisms that appear close together:

```python
# The analyze_spatial_relationships function also performs clustering
# Set a smaller min_distance for tighter clusters
spatial_results = analyzer.analyze_spatial_relationships(
    detections=detection_results,
    output_dir="spatial_analysis",
    min_distance=0.015,                       # Smaller distance for tighter clusters
    by_class=True
)
```

The clustering visualization shows:
- Identified clusters with different colors
- Number of microorganisms in each cluster
- Cluster boundaries and distribution

### Class Relationship Analysis

Class relationship analysis examines how different microorganism types interact spatially:

```bash
microdetect analyze_spatial --model_path runs/train/exp/weights/best.pt \
                           --source path/to/images \
                           --output_dir spatial_analysis \
                           --by_class
```

This generates a co-occurrence heatmap showing:
- Which classes tend to appear together
- Which classes rarely co-occur
- Spatial associations between classes

The co-occurrence ratio indicates:
- Values > 1: Classes co-occur more often than expected by chance (positive association)
- Values = 1: Classes co-occur as expected by chance (no association)
- Values < 1: Classes co-occur less often than expected by chance (negative association)

## Temporal Analysis

Temporal analysis tracks changes in microorganism populations over time, useful for studying growth, decline, or ecological changes.

### Tracking Changes Over Time

To analyze changes over time in your detections:

```python
from microdetect.analysis import StatisticalAnalyzer

analyzer = StatisticalAnalyzer(output_dir="analysis_results")

# Prepare time series data
time_series_data = [
    {
        "timestamp": "2023-01-01",
        "count": 245,
        "class_counts": {"0": 125, "1": 85, "2": 35}
    },
    {
        "timestamp": "2023-01-08",
        "count": 278,
        "class_counts": {"0": 142, "1": 92, "2": 44}
    },
    # Additional time points...
]

# Analyze temporal data
temporal_results = analyzer.analyze_temporal_data(
    time_series_data=time_series_data,         # List of time point dictionaries
    output_dir="temporal_analysis",            # Directory to save results
    date_format="%Y-%m-%d"                     # Format of date strings
)
```

Using the command-line interface (with a CSV file containing time-series data):

```bash
microdetect analyze_temporal --data_file time_series.csv \
                            --output_dir temporal_analysis
```

This generates:
- Line charts showing population changes over time
- Stacked area charts showing class proportions
- Growth rate charts

### Growth Rate Analysis

The temporal analysis calculates growth rates between time points:

```python
# The analyze_temporal_data function calculates growth rates
# Results include growth rate chart and statistics
temporal_results = analyzer.analyze_temporal_data(
    time_series_data=time_series_data,
    output_dir="temporal_analysis"
)
```

Growth rate visualization shows:
- Percentage change between time points
- Periods of growth and decline
- Growth rate differences between classes

The analysis also provides summary statistics:
- Average growth rate
- Maximum and minimum growth rates
- Growth rate variability

## Batch Processing

For analyzing large datasets, MicroDetect provides batch processing capabilities.

### Processing Multiple Images

To process a batch of images:

```python
from microdetect.analysis import BatchProcessor

processor = BatchProcessor(num_workers=4)      # Use 4 parallel workers

# Process a batch of images
results = processor.process_batch(
    model_path="runs/train/exp/weights/best.pt",  # Path to model
    source_dir="path/to/images",                  # Directory with images
    output_dir="batch_results",                   # Directory for results
    batch_size=16,                                # Images per batch
    conf_threshold=0.25,                          # Confidence threshold
    save_txt=True,                                # Save YOLO format annotations
    save_json=True                                # Save JSON results
)
```

Using the command-line interface:

```bash
microdetect batch_detect --model_path runs/train/exp/weights/best.pt \
                        --source path/to/images \
                        --output_dir batch_results \
                        --batch_size 16 \
                        --save_json
```

### Custom Analysis Functions

For advanced analysis, you can define custom processing functions:

```python
from microdetect.analysis import BatchProcessor

# Define a custom worker function
def custom_analysis(model, image_path, output_dir, **kwargs):
    # Run detection
    results = model(image_path, **kwargs)
    
    # Perform custom analysis
    # ...
    
    return {
        "custom_metric": custom_value,
        "detections": detections
    }

# Process with custom function
processor = BatchProcessor(num_workers=4)
results = processor.process_parallel(
    model_path="runs/train/exp/weights/best.pt",
    source_dir="path/to/images",
    output_dir="custom_analysis",
    worker_function=custom_analysis,
    worker_args={
        "conf": 0.25,
        "iou": 0.45
    }
)
```

## Integrating with Other Tools

MicroDetect's statistical analysis tools can be integrated with other tools:

### Exporting to CSV for External Analysis

```python
# Export to CSV for analysis in other tools
analyzer.export_to_csv(
    data=detection_results,
    output_file="detections.csv"
)
```

The CSV file can be imported into:
- Spreadsheet applications (Excel, Google Sheets)
- Statistical packages (R, SPSS)
- Data visualization tools (Tableau, Power BI)

### Integrating with Scientific Python Ecosystem

```python
# Convert results to pandas DataFrame for further analysis
import pandas as pd

# Size analysis data
size_df = pd.read_csv("size_analysis/size_distribution_data.csv")

# Additional pandas analysis
size_by_class = size_df.groupby('classe')['tamanho'].agg(['mean', 'std', 'min', 'max'])
print(size_by_class)

# Statistical tests (using scipy)
from scipy import stats
t_stat, p_value = stats.ttest_ind(
    size_df[size_df['classe'] == 0]['tamanho'],
    size_df[size_df['classe'] == 1]['tamanho']
)
print(f"t-statistic: {t_stat}, p-value: {p_value}")
```

## Best Practices

1. **Start with exploratory analysis**: Use density maps and size distribution before more complex analyses

2. **Combine analyses**: Integrate insights from different analyses for a complete picture

3. **Validate with domain knowledge**: Interpret results in the context of microbiological principles

4. **Verify detections first**: Run error analysis before statistical analysis to ensure reliable input data

5. **Consider scale**: Account for image scale/magnification when comparing sizes across different datasets

6. **Use appropriate smoothing**: Adjust the sigma parameter for density maps based on image resolution

7. **Document analysis parameters**: Record parameters like min_distance for reproducibility

8. **Validate clustering results**: Try different min_distance values to ensure robust cluster identification

## Troubleshooting

### Issue: Density maps appear too smooth or too noisy
**Solution**: Adjust the sigma parameter (higher for smoother, lower for finer detail)

### Issue: Size analysis shows unexpected results
**Solution**: Check if bounding boxes are normalized (0-1) or absolute pixels; verify detection quality

### Issue: No clusters found in spatial analysis
**Solution**: Try increasing the min_distance parameter; check if detections have proper coordinates

### Issue: Temporal analysis shows abrupt changes
**Solution**: Verify consistent detection settings across all time points; check for data collection issues

### Issue: Batch processing is slow
**Solution**: Reduce batch size; increase num_workers if CPU has many cores; use smaller model size

### Issue: Memory errors during batch processing
**Solution**: Reduce batch size; process images in smaller groups; use a lower resolution

For more troubleshooting information, see the [Troubleshooting Guide](troubleshooting.md).