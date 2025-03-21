# tests/utils/test_config.py
import os
import tempfile

import pytest
import yaml

from microdetect.utils.config import Config


@pytest.fixture
def temp_config_file():
    """Create a temporary config file for testing."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as temp:
        config_data = {
            "test_section": {"test_key": "test_value", "nested_key": {"inner_key": "inner_value"}},
            "directories": {"dataset": "./test_dataset"},
        }
        yaml.dump(config_data, temp)
        temp_path = temp.name

    yield temp_path

    # Cleanup
    os.unlink(temp_path)


def test_config_loading(temp_config_file):
    """Test loading configuration from a file."""
    config = Config(temp_config_file)

    # Test direct access to configuration data
    assert "test_section" in config.config_data
    assert config.config_data["test_section"]["test_key"] == "test_value"

    # Test using get method
    assert config.get("test_section.test_key") == "test_value"
    assert config.get("test_section.nested_key.inner_key") == "inner_value"

    # Test default value for non-existent key
    assert config.get("non_existent", "default") == "default"


def test_config_default_values():
    """Test that default configuration is loaded if no file is provided."""
    # Use a non-existent file path
    config = Config("non_existent_file.yaml")

    # Test that default configuration is loaded
    assert "directories" in config.config_data
    assert "classes" in config.config_data
    assert "training" in config.config_data

    # Test specific default values
    assert config.get("directories.dataset") == "dataset"
    assert "0-levedura" in config.get("classes")


def test_config_save(tmp_path):
    """Test saving configuration to a file."""
    config_path = tmp_path / "test_config.yaml"

    # Create a config with default values
    config = Config()

    # Modify some values
    config.config_data["test_key"] = "test_value"

    # Save configuration
    config.save(str(config_path))

    # Check that file exists
    assert config_path.exists()

    # Load the saved configuration and verify values
    with open(config_path, "r") as f:
        saved_data = yaml.safe_load(f)

    assert "test_key" in saved_data
    assert saved_data["test_key"] == "test_value"
