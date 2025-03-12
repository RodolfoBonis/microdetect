"""
Common test fixtures for the MicroDetect test suite.
"""

import os
import shutil
import tempfile
from pathlib import Path
from unittest.mock import patch

import cv2
import numpy as np
import pytest
import yaml


@pytest.fixture(scope="session")
def test_config():
    """Load test configuration from YAML file."""
    config_path = Path(__file__).parent / "test_config.yaml"
    if config_path.exists():
        with open(config_path, "r") as f:
            return yaml.safe_load(f)
    else:
        # Default configuration if file doesn't exist
        return {
            "paths": {
                "temp_dir": "/tmp/microdetect_tests",
            },
            "mocks": {
                "classes": ["0-levedura", "1-fungo", "2-micro-alga"],
                "color_map": {"0": [0, 255, 0], "1": [0, 0, 255], "2": [255, 0, 0]},
            },
            "parameters": {
                "augmentation": {
                    "factor": 3,
                    "brightness_range": [0.8, 1.2],
                    "contrast_range": [-10, 10],
                    "flip_probability": 0.5,
                },
                "dataset": {
                    "train_ratio": 0.6,
                    "val_ratio": 0.2,
                    "test_ratio": 0.2,
                    "seed": 42,
                },
            },
            "skip": {
                "gpu_tests": True,
                "network_tests": False,
                "aws_tests": True,
                "gui_tests": True,
            },
        }


@pytest.fixture(scope="session")
def test_dir(test_config):
    """Create a temporary directory for test files."""
    # If a specific test directory is configured, use it
    if "temp_dir" in test_config.get("paths", {}):
        temp_dir = Path(test_config["paths"]["temp_dir"])
        temp_dir.mkdir(parents=True, exist_ok=True)
        yield temp_dir
        # Don't cleanup if using a configured directory
    else:
        # Create a temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)
            # Auto-cleanup when using tempfile.TemporaryDirectory


@pytest.fixture
def sample_image(test_dir):
    """Create a sample test image."""
    # Create image directory
    img_dir = test_dir / "images"
    img_dir.mkdir(exist_ok=True)

    # Create a test image
    img_path = img_dir / "test_img.jpg"
    img = np.zeros((100, 100, 3), dtype=np.uint8)
    img[25:75, 25:75] = [255, 255, 255]  # White square in the middle
    cv2.imwrite(str(img_path), img)

    yield img_path

    # Cleanup
    if img_path.exists():
        os.unlink(img_path)


@pytest.fixture
def sample_image_and_label(test_dir, test_config):
    """Create a sample image and corresponding label file."""
    # Create directories
    img_dir = test_dir / "images"
    label_dir = test_dir / "labels"
    img_dir.mkdir(exist_ok=True)
    label_dir.mkdir(exist_ok=True)

    # Create a test image
    img_path = img_dir / "test_img.jpg"
    img = np.zeros((100, 100, 3), dtype=np.uint8)
    img[25:75, 25:75] = [255, 255, 255]  # White square in the middle
    cv2.imwrite(str(img_path), img)

    # Create a corresponding label file
    label_path = label_dir / "test_img.txt"
    sample_annotation = test_config.get("mocks", {}).get("annotations", ["0 0.5 0.5 0.2 0.2"])[0]
    with open(label_path, "w") as f:
        f.write(sample_annotation)

    yield test_dir, img_dir, label_dir, img_path, label_path

    # Cleanup
    if img_path.exists():
        os.unlink(img_path)
    if label_path.exists():
        os.unlink(label_path)


@pytest.fixture
def sample_dataset(test_dir):
    """Create a sample dataset for testing."""
    # Create source directories
    source_img_dir = test_dir / "source_images"
    source_label_dir = test_dir / "source_labels"
    dataset_dir = test_dir / "dataset"

    source_img_dir.mkdir(exist_ok=True)
    source_label_dir.mkdir(exist_ok=True)
    dataset_dir.mkdir(exist_ok=True)

    # Create sample images and labels
    for i in range(10):
        # Create dummy image
        img_path = source_img_dir / f"img_{i}.jpg"
        img = np.zeros((100, 100, 3), dtype=np.uint8)
        cv2.imwrite(str(img_path), img)

        # Create corresponding label
        label_path = source_label_dir / f"img_{i}.txt"
        with open(label_path, "w") as f:
            # YOLO format: class x_center y_center width height
            f.write(f"0 0.5 0.5 0.2 0.2")

    yield test_dir, source_img_dir, source_label_dir, dataset_dir

    # Cleanup
    shutil.rmtree(source_img_dir, ignore_errors=True)
    shutil.rmtree(source_label_dir, ignore_errors=True)
    shutil.rmtree(dataset_dir, ignore_errors=True)


@pytest.fixture
def temp_config_file(test_config):
    """Create a temporary config file for testing."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as temp:
        # Create a minimal config for testing
        config_data = {
            "test_section": {"test_key": "test_value", "nested_key": {"inner_key": "inner_value"}},
            "directories": {"dataset": "./test_dataset"},
            "classes": test_config.get("mocks", {}).get("classes", ["0-levedura", "1-fungo", "2-micro-alga"]),
            "color_map": test_config.get("mocks", {}).get("color_map", {"0": [0, 255, 0], "1": [0, 0, 255], "2": [255, 0, 0]}),
        }
        yaml.dump(config_data, temp)
        temp_path = temp.name

    yield temp_path

    # Cleanup
    os.unlink(temp_path)


@pytest.fixture
def mock_yolo_results():
    """Create a mock for YOLO validation results."""
    from unittest.mock import MagicMock

    mock_results = MagicMock()

    # Configure box metrics
    mock_results.box = MagicMock()
    mock_results.box.map = 0.85  # mAP50-95
    mock_results.box.map50 = 0.92  # mAP50
    mock_results.box.recall = 0.88
    mock_results.box.precision = 0.90

    # Configure per-class metrics
    mock_results.box.ap_class_index = np.array([0, 1, 2])
    mock_results.box.ap50 = np.array([0.95, 0.90, 0.85])
    mock_results.box.r = np.array([0.92, 0.87, 0.82])  # Recall
    mock_results.box.p = np.array([0.94, 0.89, 0.84])  # Precision

    # Configure class names
    mock_results.names = {0: "0-levedura", 1: "1-fungo", 2: "2-micro-alga"}

    return mock_results


@pytest.fixture
def skip_gui_tests(test_config):
    """Skip tests requiring GUI if configured to do so."""
    skip_gui = test_config.get("skip", {}).get("gui_tests", True)
    if skip_gui:
        pytest.skip("GUI tests are disabled in test configuration")


@pytest.fixture
def skip_gpu_tests(test_config):
    """Skip tests requiring GPU if configured to do so."""
    skip_gpu = test_config.get("skip", {}).get("gpu_tests", True)
    if skip_gpu:
        pytest.skip("GPU tests are disabled in test configuration")


@pytest.fixture
def skip_aws_tests(test_config):
    """Skip tests requiring AWS credentials if configured to do so."""
    skip_aws = test_config.get("skip", {}).get("aws_tests", True)
    if skip_aws:
        pytest.skip("AWS tests are disabled in test configuration")


@pytest.fixture
def skip_network_tests(test_config):
    """Skip tests requiring network access if configured to do so."""
    skip_network = test_config.get("skip", {}).get("network_tests", False)
    if skip_network:
        pytest.skip("Network tests are disabled in test configuration")


@pytest.fixture
def patch_environment_variables():
    """Patch environment variables for tests and restore after."""
    original_env = os.environ.copy()

    # Set test environment variables
    os.environ["MICRODETECT_SKIP_UPDATE_CHECK"] = "1"

    yield

    # Restore original environment variables
    os.environ.clear()
    os.environ.update(original_env)
