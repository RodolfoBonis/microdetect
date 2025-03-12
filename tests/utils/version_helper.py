# tests/utils/version_helper.py

"""
Helper module for version-related test patches
"""

import contextlib
from unittest.mock import patch


@contextlib.contextmanager
def mock_microdetect_version(version="1.0.0"):
    """
    A context manager to mock the microdetect.__version__ attribute.

    Args:
        version: The version string to use for testing

    Yields:
        None - this is a context manager
    """
    # Create a patcher for the version attribute
    patcher = patch("microdetect.__version__", version)

    # Start the patch
    patcher.start()

    try:
        # Yield control back to the caller
        yield
    finally:
        # Stop the patch when we're done
        patcher.stop()