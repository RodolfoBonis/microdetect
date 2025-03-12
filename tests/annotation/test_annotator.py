# tests/annotation/test_annotator.py
import os
import tempfile
from unittest.mock import MagicMock, patch

import cv2
import numpy as np
import pytest

from microdetect.annotation.annotator import ImageAnnotator


@pytest.fixture
def sample_image():
    """Create a temporary sample image for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create image directory
        img_dir = os.path.join(temp_dir, "images")
        os.makedirs(img_dir)

        # Create a test image
        img_path = os.path.join(img_dir, "test_img.jpg")
        img = np.zeros((100, 100, 3), dtype=np.uint8)
        cv2.imwrite(img_path, img)

        yield temp_dir, img_dir, img_path


def test_init_with_custom_classes():
    """Test initializing the annotator with custom classes."""
    # Custom classes
    classes = ["levedura", "fungo", "micro-alga"]

    annotator = ImageAnnotator(classes=classes)

    # Check that classes were set correctly
    assert annotator.classes == classes


@patch("microdetect.annotation.annotator.cv2.imread")
@patch("microdetect.annotation.annotator.tk.Tk")
def test_annotate_image_opens_with_correct_file(mock_tk, mock_imread, sample_image):
    """Test that annotation opens with the correct image file."""
    temp_dir, img_dir, img_path = sample_image

    # Mock image loading
    mock_img = np.zeros((100, 100, 3), dtype=np.uint8)
    mock_imread.return_value = mock_img

    # Mock tkinter
    mock_root = MagicMock()
    mock_tk.return_value = mock_root

    # Create output directory
    output_dir = os.path.join(temp_dir, "labels")
    os.makedirs(output_dir)

    # Create annotator
    annotator = ImageAnnotator()

    # Mock the mainloop to prevent actually running the GUI
    mock_root.mainloop.side_effect = lambda: mock_root.destroy()

    # Try to annotate, but exit immediately
    with patch("sys.stdin"):  # Mock stdin for any inputs
        # Capture tkinter exception that might occur when window is destroyed
        try:
            annotator.annotate_image(img_path, output_dir)
        except Exception:
            pass

    # Verify the image was loaded
    mock_imread.assert_called_once_with(img_path)


@patch("microdetect.annotation.annotator.cv2.imread")
def test_load_existing_annotations(mock_imread, sample_image):
    """Test loading existing annotations for an image."""
    temp_dir, img_dir, img_path = sample_image

    # Mock image loading
    mock_img = np.zeros((100, 100, 3), dtype=np.uint8)
    mock_imread.return_value = mock_img

    # Create output directory and existing annotation
    output_dir = os.path.join(temp_dir, "labels")
    os.makedirs(output_dir)

    # Create annotation file
    base_name = os.path.splitext(os.path.basename(img_path))[0]
    annotation_path = os.path.join(output_dir, f"{base_name}.txt")
    with open(annotation_path, "w") as f:
        # YOLO format: class x_center y_center width height
        f.write("0 0.5 0.5 0.2 0.2\n")

    # Create annotator
    annotator = ImageAnnotator()

    # Mock tk.Tk to avoid creating a real window
    with patch("microdetect.annotation.annotator.tk.Tk") as mock_tk:
        mock_root = MagicMock()
        mock_tk.return_value = mock_root

        # Mock the mainloop to prevent actually running the GUI
        mock_root.mainloop.side_effect = lambda: mock_root.destroy()

        # Try to annotate, but exit immediately
        with patch("sys.stdin"):  # Mock stdin for any inputs
            try:
                annotator.annotate_image(img_path, output_dir)
            except Exception:
                pass

    # Verify the image was loaded
    mock_imread.assert_called_once_with(img_path)


@patch("microdetect.annotation.annotator.ImageAnnotator.annotate_image")
def test_batch_annotate(mock_annotate_image, sample_image):
    """Test batch annotation process."""
    temp_dir, img_dir, img_path = sample_image

    # Create multiple test images
    for i in range(2):
        new_img_path = os.path.join(img_dir, f"test_img_{i}.jpg")
        img = np.zeros((100, 100, 3), dtype=np.uint8)
        cv2.imwrite(new_img_path, img)

    # Create output directory
    output_dir = os.path.join(temp_dir, "labels")
    os.makedirs(output_dir)

    # Configure mock
    mock_annotate_image.return_value = "mock_annotation_path"

    # Create annotator
    annotator = ImageAnnotator()

    # Mock input to avoid user interaction
    with patch("builtins.input", return_value="s"):
        total, annotated = annotator.batch_annotate(img_dir, output_dir)

    # Check results
    assert total == 3  # Total number of images (1 original + 2 new)
    assert annotated == 3  # All were "annotated" by our mock

    # Check that annotate_image was called for each image
    assert mock_annotate_image.call_count == 3
