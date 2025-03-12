"""
Basic tests for the MicroDetect package.
"""

import unittest

import microdetect


class TestMicroDetect(unittest.TestCase):
    """Basic tests for the MicroDetect package."""

    def test_version(self):
        """Test that the version is defined."""
        self.assertIsNotNone(microdetect.__version__)

    def test_config_utils(self):
        """Test that the config utility exists and can be imported."""
        from microdetect.utils import config

        self.assertIsNotNone(config)

    def test_config_default(self):
        """Test that the default config has expected structure."""
        from microdetect.utils.config import Config

        # Create a temporary test config
        config = Config()
        default_config = config._get_default_config()

        # Verify structure
        self.assertIn("directories", default_config)
        self.assertIn("classes", default_config)
        self.assertIn("training", default_config)
        self.assertIn("dataset", default_config)
        self.assertIn("augmentation", default_config)

        # Verify default classes
        self.assertIn("0-levedura", default_config["classes"])
        self.assertIn("1-fungo", default_config["classes"])
        self.assertIn("2-micro-alga", default_config["classes"])


# For running tests directly
if __name__ == "__main__":
    unittest.main()
