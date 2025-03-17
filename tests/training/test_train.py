# tests/training/test_train.py
import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest
import yaml

from microdetect.training import YOLOTrainer


@pytest.fixture
def sample_data_yaml():
    """Create a temporary data.yaml file for testing."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as temp:
        data = {
            "train": "/path/to/train/images",
            "val": "/path/to/val/images",
            "test": "/path/to/test/images",
            "nc": 3,
            "names": ["0-levedura", "1-fungo", "2-micro-alga"],
        }
        yaml.dump(data, temp)
        temp_path = temp.name

    yield temp_path

    # Cleanup
    os.unlink(temp_path)


@patch("microdetect.training.train.YOLO")
@patch("microdetect.training.train.torch")
def test_train_initialization(mock_torch, mock_yolo, sample_data_yaml):
    """Test initialization of YOLOTrainer."""
    # Configure mock
    mock_torch.cuda.is_available.return_value = True
    mock_torch.backends.mps.is_available.return_value = False
    mock_torch.cuda.get_device_name.return_value = "NVIDIA Test GPU"

    # Create trainer
    trainer = YOLOTrainer(model_size="s", epochs=10, batch_size=8, image_size=320, pretrained=True, output_dir="test_output")

    # Check initialization
    assert trainer.model_size == "s"
    assert trainer.epochs == 10
    assert trainer.batch_size == 8
    assert trainer.image_size == 320
    assert trainer.pretrained is True
    assert trainer.output_dir == "test_output"


@patch("microdetect.training.train.YOLO")
@patch("microdetect.training.train.torch")
def test_train(mock_torch, mock_yolo, sample_data_yaml):
    """Test the train method."""
    # Configure mock YOLO
    mock_model = MagicMock()
    mock_yolo.return_value = mock_model

    # Configure mock torch
    mock_torch.cuda.is_available.return_value = True
    mock_torch.backends.mps.is_available.return_value = False

    # Create trainer
    trainer = YOLOTrainer(model_size="s", epochs=10, batch_size=8)

    # Call train method
    trainer.train(sample_data_yaml)

    # Check that YOLO was initialized with the right model
    mock_yolo.assert_called_once_with("yolov8s.pt")

    # Check that train was called with the right parameters
    mock_model.train.assert_called_once()
    args, kwargs = mock_model.train.call_args

    assert kwargs["data"] == sample_data_yaml
    assert kwargs["epochs"] == 10
    assert kwargs["batch"] == 8
    assert kwargs["imgsz"] == 640  # Default if not specified
    assert kwargs["device"] == "0"  # CUDA device
    assert "patience" in kwargs
    assert kwargs["save"] is True


@pytest.fixture
def checkpoint_path():
    """Create a temporary file to represent a checkpoint path."""
    with tempfile.NamedTemporaryFile(suffix=".pt", delete=False) as temp:
        temp_path = temp.name

    # Return the path and ensure it's cleaned up after the test
    yield temp_path
    if os.path.exists(temp_path):
        os.unlink(temp_path)


@patch("microdetect.training.train.YOLO")
@patch("microdetect.training.train.torch")
def test_resume_training(mock_torch, mock_yolo, checkpoint_path, sample_data_yaml):
    """Test resuming training from a checkpoint."""
    # Configure mock YOLO
    mock_model = MagicMock()
    mock_model.ckpt = {"epoch": 5}
    mock_yolo.return_value = mock_model

    # Configure mock torch
    mock_torch.cuda.is_available.return_value = True
    mock_torch.backends.mps.is_available.return_value = False

    # Create trainer
    trainer = YOLOTrainer(model_size="s", epochs=10, batch_size=8)

    # Call resume_training method with actual checkpoint file
    trainer.resume_training(checkpoint_path, sample_data_yaml)

    # Check that YOLO was initialized with the checkpoint
    mock_yolo.assert_called_once_with(checkpoint_path)

    # Check that train was called with the right parameters
    mock_model.train.assert_called_once()
    args, kwargs = mock_model.train.call_args

    assert kwargs["data"] == sample_data_yaml
    assert kwargs["epochs"] == 15  # 5 (from checkpoint) + 10 (additional)
    assert kwargs["batch"] == 8
    assert kwargs["resume"] is True
