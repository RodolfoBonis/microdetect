# tests/utils/test_aws_setup.py
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from microdetect.aws import AWSSetupManager


# Alternative implementation using pytest fixtures
@pytest.fixture
def aws_mocks():
    """Create and start all required mocks."""
    with patch("microdetect.utils.aws_setup.AWSSetupManager.check_aws_cli") as mock_check, patch(
        "microdetect.utils.aws_setup.AWSSetupManager.run_command"
    ) as mock_run, patch("microdetect.utils.aws_setup.sys.platform", "darwin"), patch(
        "builtins.print"
    ):  # Suppress output

        # Configure the check_aws_cli mock
        mock_check.side_effect = [False, True]
        mock_run.return_value = "Success"

        yield {"check_aws": mock_check, "run_command": mock_run}


@pytest.fixture
def temp_aws_config():
    """Create temporary AWS config and credentials files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create mock .aws directory
        aws_dir = Path(temp_dir) / ".aws"
        aws_dir.mkdir()

        # Create mock config file
        config_file = aws_dir / "config"
        with open(config_file, "w") as f:
            f.write("[default]\nregion = us-east-1\n")

        # Create mock credentials file
        credentials_file = aws_dir / "credentials"
        with open(credentials_file, "w") as f:
            f.write("[default]\naws_access_key_id = test_key\naws_secret_access_key = test_secret\n")

        yield temp_dir


@patch("microdetect.utils.aws_setup.subprocess.run")
def test_run_command(mock_run):
    """Test the run_command utility method."""
    # Configure mock
    mock_result = MagicMock()
    mock_result.stdout = "command output"
    mock_run.return_value = mock_result

    # Run the command
    command = ["aws", "--version"]
    result = AWSSetupManager.run_command(command)

    # Check that subprocess.run was called with the right arguments
    mock_run.assert_called_once_with(command, check=True, capture_output=True, text=True)

    # Check result
    assert result == "command output"


@patch("microdetect.utils.aws_setup.subprocess.run")
def test_check_aws_cli_available(mock_run):
    """Test checking AWS CLI availability when it's installed."""
    # Configure mock to simulate AWS CLI being available
    mock_run.return_value = MagicMock()

    # Check AWS CLI
    result = AWSSetupManager.check_aws_cli()

    # Verify subprocess.run was called correctly
    mock_run.assert_called_once_with(["aws", "--version"], capture_output=True, check=True)

    # Check result
    assert result is True


@patch("microdetect.utils.aws_setup.subprocess.run")
def test_check_aws_cli_not_available(mock_run):
    """Test checking AWS CLI availability when it's not installed."""
    # Configure mock to simulate AWS CLI not being available
    mock_run.side_effect = FileNotFoundError("No such file or directory: 'aws'")

    # Check AWS CLI
    result = AWSSetupManager.check_aws_cli()

    # Verify subprocess.run was called correctly
    mock_run.assert_called_once_with(["aws", "--version"], capture_output=True, check=True)

    # Check result
    assert result is False


@patch("pathlib.Path.mkdir")
@patch("pathlib.Path.open")
@patch("configparser.ConfigParser")
def test_configure_aws(mock_configparser, mock_open, mock_mkdir):
    """Test configuring AWS credentials and settings."""
    # Configure mocks
    mock_config_instance = MagicMock()
    mock_configparser.return_value = mock_config_instance

    # Call configure_aws
    result = AWSSetupManager.configure_aws(
        domain="test-domain",
        repository="test-repo",
        domain_owner="123456789012",
        aws_access_key="TEST_KEY",
        aws_secret_key="TEST_SECRET",
        aws_region="us-west-2",
    )

    # Check result
    assert result is True

    # Verify that credentials were set
    mock_config_instance.__setitem__.assert_any_call("default", {})

    # Check environment variables
    assert os.environ.get("AWS_CODEARTIFACT_DOMAIN") == "test-domain"
    assert os.environ.get("AWS_CODEARTIFACT_REPOSITORY") == "test-repo"
    assert os.environ.get("AWS_CODEARTIFACT_OWNER") == "123456789012"


@patch("microdetect.utils.updater.UpdateManager.get_aws_codeartifact_token")
@patch("microdetect.utils.updater.UpdateManager.get_latest_version")
def test_test_codeartifact_login_success(mock_get_latest_version, mock_get_token):
    """Test successful CodeArtifact login test."""
    # Configure mocks
    mock_get_token.return_value = (True, "dummy-token", "dummy-endpoint")
    mock_get_latest_version.return_value = (True, "1.0.0")

    # Test login
    success, message = AWSSetupManager.test_codeartifact_login()

    # Check results
    assert success is True
    assert "1.0.0" in message
    assert mock_get_token.call_count == 1
    assert mock_get_latest_version.call_count == 1


@patch("microdetect.utils.updater.UpdateManager.get_aws_codeartifact_token")
def test_test_codeartifact_login_failure(mock_get_token):
    """Test failed CodeArtifact login test."""
    # Configure mock to simulate failure
    mock_get_token.return_value = (False, "", "")

    # Test login
    success, message = AWSSetupManager.test_codeartifact_login()

    # Check results
    assert success is False
    assert "Falha" in message
    assert mock_get_token.call_count == 1
