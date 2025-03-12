# tests/utils/test_helpers.py

"""
Helper utilities for testing the MicroDetect package.

This module provides common mocking functions and fixtures used across different test modules.
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch


def create_temp_file(suffix=None, content=None, delete=True):
    """
    Create a temporary file for testing.

    Args:
        suffix: Optional file suffix (e.g., '.pt', '.yaml')
        content: Optional content to write to the file
        delete: Whether to delete the file after the test (for use with yield fixtures)

    Returns:
        Path to the temporary file
    """
    with tempfile.NamedTemporaryFile(mode='w+', suffix=suffix, delete=False) as temp:
        if content:
            temp.write(content)
        temp_path = temp.name

    # Return the path - for use with "yield" in fixtures to ensure cleanup
    if delete:
        return temp_path
    else:
        return temp_path


def mock_version(version="1.0.0"):
    """
    Creates a context manager to mock the package version.

    Args:
        version: The version string to use

    Returns:
        A patch context manager
    """
    return patch("microdetect.__version__", version)


def get_module_file_path(module_path):
    """
    Gets the actual file path of a module.

    Args:
        module_path: Import path of the module (e.g., 'microdetect.utils.config')

    Returns:
        Path object pointing to the module file
    """
    import importlib
    import inspect

    module = importlib.import_module(module_path)
    return Path(inspect.getfile(module))


def mock_aws_client():
    """
    Create necessary patches for AWS client operations.

    Returns:
        List of patch objects that can be used in a with statement
    """
    patches = [
        patch("microdetect.utils.aws_setup.subprocess.run"),
        patch("microdetect.utils.aws_setup.subprocess.check_output"),
        patch("microdetect.utils.updater.subprocess.check_output")
    ]
    return patches


def mock_file_operations():
    """
    Create patches for common file operations.

    Returns:
        List of patch objects for file operations
    """
    patches = [
        patch("os.path.exists", return_value=True),
        patch("pathlib.Path.exists", return_value=True),
        patch("builtins.open"),
    ]
    return patches