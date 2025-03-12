# tests/utils/test_updater.py
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from microdetect.utils.updater import UpdateManager


@patch("microdetect.utils.updater.subprocess.check_output")
def test_get_aws_codeartifact_token_success(mock_check_output):
    """Test successful retrieval of AWS CodeArtifact token."""
    # Configure mocks
    mock_check_output.side_effect = [b"dummy-token\n", b"https://example.com/\n"]

    # Set environment variables
    os.environ["AWS_CODEARTIFACT_DOMAIN"] = "test-domain"
    os.environ["AWS_CODEARTIFACT_REPOSITORY"] = "test-repo"

    # Call the method
    success, token, endpoint = UpdateManager.get_aws_codeartifact_token()

    # Check results
    assert success is True
    assert token == "dummy-token"
    assert endpoint == "https://example.com/"
    assert mock_check_output.call_count == 2

    # Clean up
    del os.environ["AWS_CODEARTIFACT_DOMAIN"]
    del os.environ["AWS_CODEARTIFACT_REPOSITORY"]


@patch("microdetect.utils.updater.subprocess.check_output")
def test_get_aws_codeartifact_token_failure(mock_check_output):
    """Test failure in retrieving AWS CodeArtifact token."""
    # Configure mock to raise an exception
    mock_check_output.side_effect = Exception("Command failed")

    # Call the method
    success, token, endpoint = UpdateManager.get_aws_codeartifact_token()

    # Check results
    assert success is False
    assert token == ""
    assert endpoint == ""


@patch("microdetect.utils.updater.UpdateManager.get_aws_codeartifact_token")
@patch("microdetect.utils.updater.subprocess.check_output")
def test_get_latest_version_success(mock_check_output, mock_get_token):
    """Test successful retrieval of the latest version."""
    # Configure mocks
    mock_get_token.return_value = (True, "dummy-token", "https://example.com/")
    mock_check_output.return_value = b"microdetect (1.2.3), latest"

    # Call the method
    success, version = UpdateManager.get_latest_version()

    # Check results
    assert success is True
    assert version == "1.2.3"


@patch("microdetect.utils.updater.UpdateManager.get_aws_codeartifact_token")
def test_get_latest_version_token_failure(mock_get_token):
    """Test failure in retrieving the latest version due to token failure."""
    # Configure mock to simulate token failure
    mock_get_token.return_value = (False, "", "")

    # Call the method
    success, version = UpdateManager.get_latest_version()

    # Check results
    assert success is False
    assert version == ""


def test_compare_versions():
    """Test version comparison logic."""
    # Test cases where newer version is higher
    assert UpdateManager.compare_versions("1.0.0", "1.0.1") is True
    assert UpdateManager.compare_versions("1.0.0", "1.1.0") is True
    assert UpdateManager.compare_versions("1.0.0", "2.0.0") is True

    # Test cases where versions are equal
    assert UpdateManager.compare_versions("1.0.0", "1.0.0") is False

    # Test cases where current version is higher
    assert UpdateManager.compare_versions("1.0.1", "1.0.0") is False
    assert UpdateManager.compare_versions("1.1.0", "1.0.0") is False
    assert UpdateManager.compare_versions("2.0.0", "1.0.0") is False

    # Test different length versions
    assert UpdateManager.compare_versions("1.0", "1.0.1") is True
    assert UpdateManager.compare_versions("1.0.0", "1.0") is False


@patch("microdetect.utils.updater.UpdateManager.get_latest_version")
def test_check_for_updates(mock_get_latest_version):
    """Test the check_for_updates method."""
    # Configure mock
    mock_get_latest_version.return_value = (True, "1.1.0")

    # Patch __version__ import
    with patch("microdetect.utils.updater.__version__", "1.0.0"):
        # Call the method
        update_info = UpdateManager.check_for_updates()

    # Check results
    assert "current" in update_info
    assert "latest" in update_info
    assert "needs_update" in update_info
    assert update_info["current"] == "1.0.0"
    assert update_info["latest"] == "1.1.0"
    assert update_info["needs_update"] is True


@patch("microdetect.utils.updater.UpdateManager.get_latest_version")
def test_check_for_updates_no_update_needed(mock_get_latest_version):
    """Test the check_for_updates method when no update is needed."""
    # Configure mock
    mock_get_latest_version.return_value = (True, "1.0.0")

    # Patch __version__ import
    with patch("microdetect.utils.updater.__version__", "1.0.0"):
        # Call the method
        update_info = UpdateManager.check_for_updates()

    # Check results
    assert update_info["needs_update"] is False


@patch("microdetect.utils.updater.UpdateManager.get_latest_version")
def test_check_for_updates_error(mock_get_latest_version):
    """Test the check_for_updates method when an error occurs."""
    # Configure mock to simulate failure
    mock_get_latest_version.return_value = (False, "")

    # Patch __version__ import
    with patch("microdetect.utils.updater.__version__", "1.0.0"):
        # Call the method
        update_info = UpdateManager.check_for_updates()

    # Check results
    assert "error" in update_info
    assert "current" in update_info
    assert update_info["current"] == "1.0.0"


def test_check_for_updates_before_command():
    """Test the check_for_updates_before_command method."""
    # Set environment variable to skip check
    os.environ["MICRODETECT_SKIP_UPDATE_CHECK"] = "1"

    # Call the method
    result = UpdateManager.check_for_updates_before_command()

    # Check result
    assert result is False

    # Clean up
    del os.environ["MICRODETECT_SKIP_UPDATE_CHECK"]


@patch("microdetect.utils.updater.json.dump")
@patch("microdetect.utils.updater.UpdateManager.check_for_updates")
def test_check_for_updates_before_command_with_cache(mock_check_for_updates, mock_json_dump, tmp_path, monkeypatch):
    """Test using the update check cache."""
    # Configure mock
    mock_check_for_updates.return_value = {"current": "1.0.0", "latest": "1.1.0", "needs_update": True}

    # Redirect tempfile.gettempdir to our pytest tmp_path
    monkeypatch.setattr("tempfile.gettempdir", lambda: str(tmp_path))

    # Create cache directory
    cache_dir = tmp_path / "microdetect"
    cache_dir.mkdir()

    # Create old cache file (more than 24 hours old)
    cache_file = cache_dir / "update_check.json"
    with open(cache_file, "w") as f:
        json.dump({"last_check_time": 0}, f)

    # Call the method
    with patch("time.time", return_value=100000):  # Mock current time
        with patch("sys.stdout"):  # Suppress prints
            result = UpdateManager.check_for_updates_before_command()

    # Check that the check was performed and cache was updated
    assert mock_check_for_updates.called
    assert mock_json_dump.called
    assert result is False
