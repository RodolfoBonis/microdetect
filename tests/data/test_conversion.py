# tests/data/test_conversion.py
import os
import tempfile
import pytest
from pathlib import Path
import numpy as np
from PIL import Image

from microdetect.data.conversion import ImageConverter


@pytest.fixture
def temp_tif_file():
    """Create a temporary TIFF file for testing."""
    with tempfile.NamedTemporaryFile(suffix=".tif", delete=False) as temp:
        # Create a simple TIFF image
        img = np.zeros((100, 100), dtype=np.uint8)
        img[25:75, 25:75] = 255  # White square in the middle

        # Save as TIFF
        pil_img = Image.fromarray(img)
        pil_img.save(temp.name)

        temp_path = temp.name

    yield temp_path

    # Cleanup
    if os.path.exists(temp_path):
        os.unlink(temp_path)


@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for output files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


def test_convert_tiff_to_png(temp_tif_file, temp_output_dir):
    """Test converting a TIFF file to PNG."""
    converter = ImageConverter()

    # Convert the file
    success, errors, error_messages = converter.convert_tiff_to_png(
        os.path.dirname(temp_tif_file), temp_output_dir, use_opencv=False, delete_original=False
    )

    # Check results
    assert success == 1
    assert errors == 0
    assert not error_messages

    # Check that output file exists
    input_filename = os.path.basename(temp_tif_file)
    output_filename = os.path.splitext(input_filename)[0] + ".png"
    output_path = os.path.join(temp_output_dir, output_filename)

    assert os.path.exists(output_path)

    # Check that the file is a valid PNG
    img = Image.open(output_path)
    assert img.format == "PNG"


def test_delete_original_after_conversion(temp_tif_file, temp_output_dir):
    """Test that original file is deleted when delete_original=True."""
    converter = ImageConverter()

    # Convert with delete_original=True
    success, errors, error_messages = converter.convert_tiff_to_png(
        os.path.dirname(temp_tif_file), temp_output_dir, use_opencv=False, delete_original=True
    )

    # Check that the original file is deleted
    assert not os.path.exists(temp_tif_file)

    # Check that output file exists
    input_filename = os.path.basename(temp_tif_file)
    output_filename = os.path.splitext(input_filename)[0] + ".png"
    output_path = os.path.join(temp_output_dir, output_filename)

    assert os.path.exists(output_path)


def test_batch_convert(temp_tif_file, temp_output_dir):
    """Test batch conversion method."""
    converter = ImageConverter()

    # Use batch_convert method
    success, errors, error_messages = converter.batch_convert(
        os.path.dirname(temp_tif_file),
        temp_output_dir,
        source_format="tif",
        target_format="png",
        use_opencv=False,
        delete_original=False,
    )

    # Check results
    assert success == 1
    assert errors == 0
    assert not error_messages

    # Check output file
    input_filename = os.path.basename(temp_tif_file)
    output_filename = os.path.splitext(input_filename)[0] + ".png"
    output_path = os.path.join(temp_output_dir, output_filename)

    assert os.path.exists(output_path)
