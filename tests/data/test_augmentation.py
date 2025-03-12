# tests/data/test_augmentation.py
import os
import tempfile
import pytest
import numpy as np
from PIL import Image

from microdetect.data.augmentation import DataAugmenter


@pytest.fixture
def sample_image_and_label():
    """Create a temporary sample image and label file."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create image and labels directories
        img_dir = os.path.join(temp_dir, "images")
        label_dir = os.path.join(temp_dir, "labels")
        os.makedirs(img_dir)
        os.makedirs(label_dir)

        # Create a test image
        img_path = os.path.join(img_dir, "test_img.jpg")
        img = np.zeros((100, 100, 3), dtype=np.uint8)
        img[25:75, 25:75] = [255, 255, 255]  # White square in the middle
        pil_img = Image.fromarray(img)
        pil_img.save(img_path)

        # Create a corresponding label file
        label_path = os.path.join(label_dir, "test_img.txt")
        with open(label_path, "w") as f:
            f.write("0 0.5 0.5 0.2 0.2")  # Sample YOLO format annotation

        yield temp_dir, img_dir, label_dir, img_path, label_path


def test_augment_data(sample_image_and_label):
    """Test data augmentation process."""
    temp_dir, img_dir, label_dir, img_path, label_path = sample_image_and_label

    # Create output directories
    output_img_dir = os.path.join(temp_dir, "aug_images")
    output_label_dir = os.path.join(temp_dir, "aug_labels")
    os.makedirs(output_img_dir, exist_ok=True)
    os.makedirs(output_label_dir, exist_ok=True)

    # Create augmenter with fixed settings for testing
    augmenter = DataAugmenter(
        brightness_range=(0.8, 1.2),
        contrast_range=(-10, 10),
        flip_probability=0.5,
        rotation_range=(-10, 10),
        noise_probability=0.5,
    )

    # Perform augmentation with a small factor
    augmentation_factor = 3
    original, augmented = augmenter.augment_data(img_dir, label_dir, output_img_dir, output_label_dir, augmentation_factor)

    # Check results
    assert original == 1  # One original image
    assert augmented == augmentation_factor  # Three augmented images

    # Check that augmented files exist
    assert len(os.listdir(output_img_dir)) == augmentation_factor
    assert len(os.listdir(output_label_dir)) == augmentation_factor

    # Check file naming convention
    base_name = os.path.splitext(os.path.basename(img_path))[0]
    for i in range(augmentation_factor):
        aug_img_path = os.path.join(output_img_dir, f"{base_name}_aug{i}.jpg")
        aug_label_path = os.path.join(output_label_dir, f"{base_name}_aug{i}.txt")

        assert os.path.exists(aug_img_path)
        assert os.path.exists(aug_label_path)

        # Check that images are valid
        img = Image.open(aug_img_path)
        assert img.size == (100, 100)  # Same size as original

        # Check that label files contain valid data
        with open(aug_label_path, "r") as f:
            content = f.read().strip()
            assert content  # Not empty
            parts = content.split()
            assert len(parts) == 5  # YOLO format: class x_center y_center width height
            assert parts[0] == "0"  # Class ID should remain the same


def test_adjust_annotations_for_flip():
    """Test adjusting annotations for horizontal flip."""
    augmenter = DataAugmenter()

    # Create sample annotations
    annotations = [
        "0 0.3 0.4 0.2 0.2\n",  # Class 0, x=0.3, y=0.4, w=0.2, h=0.2
        "1 0.7 0.6 0.1 0.3\n",  # Class 1, x=0.7, y=0.6, w=0.1, h=0.3
    ]

    # Adjust for flip
    flipped = augmenter._adjust_annotations_for_flip(annotations, 100)  # 100 is the image width

    # Check results
    assert len(flipped) == len(annotations)

    # First annotation: x should flip from 0.3 to 0.7
    parts1 = flipped[0].strip().split()
    assert parts1[0] == "0"  # Class unchanged
    assert float(parts1[1]) == pytest.approx(1.0 - 0.3)  # x flipped
    assert float(parts1[2]) == pytest.approx(0.4)  # y unchanged
    assert float(parts1[3]) == pytest.approx(0.2)  # w unchanged
    assert float(parts1[4]) == pytest.approx(0.2)  # h unchanged

    # Second annotation: x should flip from 0.7 to 0.3
    parts2 = flipped[1].strip().split()
    assert parts2[0] == "1"  # Class unchanged
    assert float(parts2[1]) == pytest.approx(1.0 - 0.7)  # x flipped
    assert float(parts2[2]) == pytest.approx(0.6)  # y unchanged
    assert float(parts2[3]) == pytest.approx(0.1)  # w unchanged
    assert float(parts2[4]) == pytest.approx(0.3)  # h unchanged
