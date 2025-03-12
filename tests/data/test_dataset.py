# tests/data/test_dataset.py
import os
import tempfile
import pytest
import yaml
import shutil
from pathlib import Path

from microdetect.data.dataset import DatasetManager


@pytest.fixture
def sample_dataset():
    """Create a temporary sample dataset structure for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create source directories
        source_img_dir = os.path.join(temp_dir, "images")
        source_label_dir = os.path.join(temp_dir, "labels")
        os.makedirs(source_img_dir)
        os.makedirs(source_label_dir)

        # Create sample images and labels
        for i in range(10):
            # Create empty image files
            img_path = os.path.join(source_img_dir, f"img_{i}.jpg")
            with open(img_path, "w") as f:
                f.write("dummy image content")

            # Create corresponding label files
            label_path = os.path.join(source_label_dir, f"img_{i}.txt")
            with open(label_path, "w") as f:
                f.write(f"0 0.5 0.5 0.2 0.2")  # Sample YOLO format annotation

        # Create dataset directory
        dataset_dir = os.path.join(temp_dir, "dataset")
        os.makedirs(dataset_dir)

        yield temp_dir, source_img_dir, source_label_dir, dataset_dir


def test_prepare_directory_structure(sample_dataset):
    """Test creating the directory structure for the dataset."""
    _, _, _, dataset_dir = sample_dataset

    manager = DatasetManager(dataset_dir)
    manager.prepare_directory_structure()

    # Check that directories were created
    for split in ["train", "val", "test"]:
        for subdir in ["images", "labels"]:
            path = os.path.join(dataset_dir, split, subdir)
            assert os.path.exists(path)
            assert os.path.isdir(path)


def test_split_dataset(sample_dataset):
    """Test splitting the dataset into train/val/test sets."""
    temp_dir, source_img_dir, source_label_dir, dataset_dir = sample_dataset

    # Create manager with specific ratios
    manager = DatasetManager(
        dataset_dir=dataset_dir, train_ratio=0.6, val_ratio=0.2, test_ratio=0.2, seed=42  # Use fixed seed for reproducibility
    )

    # Split dataset
    split_counts = manager.split_dataset(source_img_dir, source_label_dir)

    # Check that files were distributed correctly
    assert "train" in split_counts
    assert "val" in split_counts
    assert "test" in split_counts

    # Check that all 10 files were used
    assert split_counts["train"] + split_counts["val"] + split_counts["test"] == 10

    # Check specific counts with our ratios
    assert split_counts["train"] == 6
    assert split_counts["val"] == 2
    assert split_counts["test"] == 2

    # Check that files exist in the right places
    for split in ["train", "val", "test"]:
        img_dir = os.path.join(dataset_dir, split, "images")
        label_dir = os.path.join(dataset_dir, split, "labels")
        assert len(os.listdir(img_dir)) == split_counts[split]
        assert len(os.listdir(label_dir)) == split_counts[split]


def test_create_data_yaml(sample_dataset):
    """Test creating the data.yaml configuration file."""
    _, _, _, dataset_dir = sample_dataset

    # Create manager
    manager = DatasetManager(dataset_dir)

    # Create data.yaml
    yaml_path = manager.create_data_yaml()

    # Check that file exists
    assert os.path.exists(yaml_path)

    # Check content
    with open(yaml_path, "r") as f:
        data = yaml.safe_load(f)

    # Check structure
    assert "train" in data
    assert "val" in data
    assert "test" in data
    assert "nc" in data
    assert "names" in data

    # Check values
    assert data["nc"] == len(manager.classes)
    assert data["names"] == manager.classes
    assert os.path.abspath(dataset_dir) in data["train"]
    assert os.path.abspath(dataset_dir) in data["val"]
    assert os.path.abspath(dataset_dir) in data["test"]
