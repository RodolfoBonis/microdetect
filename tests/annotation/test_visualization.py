# tests/annotation/test_visualization.py
import os
import tempfile
from pathlib import Path

import cv2
import numpy as np
import pytest

from microdetect.annotation.visualization import AnnotationVisualizer


@pytest.fixture
def sample_image_and_annotation():
    """Create a temporary sample image and annotation file."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create image and labels directories
        img_dir = os.path.join(temp_dir, "images")
        label_dir = os.path.join(temp_dir, "labels")
        os.makedirs(img_dir)
        os.makedirs(label_dir)

        # Create a test image
        img_path = os.path.join(img_dir, "test_img.jpg")
        img = np.zeros((100, 100, 3), dtype=np.uint8)
        cv2.imwrite(img_path, img)

        # Create a corresponding annotation file
        label_path = os.path.join(label_dir, "test_img.txt")
        with open(label_path, "w") as f:
            # YOLO format: class x_center y_center width height
            f.write("0 0.5 0.5 0.2 0.2\n")  # Center box
            f.write("1 0.2 0.2 0.1 0.1\n")  # Top-left box

        yield temp_dir, img_dir, label_dir, img_path, label_path


def test_init_with_custom_maps(sample_image_and_annotation):
    """Test initializing the visualizer with custom class and color maps."""
    # Custom class and color maps
    class_map = {"0": "levedura", "1": "fungo"}
    color_map = {"0": (255, 0, 0), "1": (0, 255, 0)}

    visualizer = AnnotationVisualizer(class_map=class_map, color_map=color_map)

    # Check that the maps were set correctly
    assert visualizer.class_map == class_map
    assert visualizer.color_map == color_map


def test_save_annotated_images(sample_image_and_annotation):
    """Test saving annotated images."""
    temp_dir, img_dir, label_dir, img_path, label_path = sample_image_and_annotation

    # Create output directory
    output_dir = os.path.join(temp_dir, "output")
    os.makedirs(output_dir, exist_ok=True)

    # Create visualizer
    visualizer = AnnotationVisualizer()

    # Save annotated images
    count = visualizer.save_annotated_images(img_dir, label_dir, output_dir)

    # Check results
    assert count == 1  # One image processed

    # Check that output file exists
    output_path = os.path.join(output_dir, f"annotated_{os.path.basename(img_path)}")
    assert os.path.exists(output_path)

    # Load the image and check dimensions
    img = cv2.imread(output_path)
    assert img is not None
    assert img.shape[:2] == (100, 100)  # Same size as original


def test_save_annotated_images_with_filter(sample_image_and_annotation):
    """Test saving annotated images with class filtering."""
    temp_dir, img_dir, label_dir, img_path, label_path = sample_image_and_annotation

    # Create output directory
    output_dir = os.path.join(temp_dir, "output_filtered")
    os.makedirs(output_dir, exist_ok=True)

    # Create visualizer
    visualizer = AnnotationVisualizer()

    # Save annotated images, filtering only class 0
    filter_classes = {"0"}
    count = visualizer.save_annotated_images(img_dir, label_dir, output_dir, filter_classes)

    # Check results
    assert count == 1  # One image processed

    # Check that output file exists
    output_path = os.path.join(output_dir, f"annotated_{os.path.basename(img_path)}")
    assert os.path.exists(output_path)
