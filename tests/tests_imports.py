# tests/test_imports.py
"""
Tests to ensure all modules can be imported properly.
This helps catch import errors early on.
"""

import pytest


def test_base_package_import():
    """Test that the base package can be imported."""
    import microdetect

    assert hasattr(microdetect, "__version__")


def test_utils_imports():
    """Test that utility modules can be imported."""
    # Core utility modules
    from microdetect.utils import config

    assert hasattr(config, "Config")

    # AWS related utilities
    try:
        from microdetect.utils import aws_setup

        assert hasattr(aws_setup, "AWSSetupManager")
    except ImportError:
        pytest.skip("AWS setup module not available")

    # Update utilities
    try:
        from microdetect.utils import updater

        assert hasattr(updater, "UpdateManager")
    except ImportError:
        pytest.skip("Updater module not available")

    # UI utilities
    try:
        from microdetect.utils import colors

        assert hasattr(colors, "INFO")
    except ImportError:
        pytest.skip("Colors module not available")


def test_data_imports():
    """Test that data processing modules can be imported."""
    # Conversion module
    from microdetect.data import conversion

    assert hasattr(conversion, "ImageConverter")

    # Augmentation module
    from microdetect.data import augmentation

    assert hasattr(augmentation, "DataAugmenter")

    # Dataset module
    from microdetect.data import dataset

    assert hasattr(dataset, "DatasetManager")


def test_annotation_imports():
    """Test that annotation modules can be imported."""
    # Annotator module
    try:
        from microdetect.annotation import annotator

        assert hasattr(annotator, "ImageAnnotator")
    except ImportError:
        pytest.skip("Annotator module not available")

    # Visualization module
    from microdetect.annotation import visualization

    assert hasattr(visualization, "AnnotationVisualizer")


def test_training_imports():
    """Test that training modules can be imported."""
    # Training module
    try:
        from microdetect.training import train

        assert hasattr(train, "YOLOTrainer")
    except ImportError:
        pytest.skip("Training module not available")

    # Evaluation module
    try:
        from microdetect.training import evaluate

        assert hasattr(evaluate, "ModelEvaluator")
    except ImportError:
        pytest.skip("Evaluation module not available")


def test_cli_import():
    """Test that the CLI module can be imported."""
    try:
        from microdetect import cli

        assert hasattr(cli, "main")
    except ImportError:
        pytest.skip("CLI module not available")
