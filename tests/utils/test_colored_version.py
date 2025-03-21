import unittest
import argparse
import sys
from io import StringIO
from unittest.mock import patch, MagicMock

from microdetect.utils.colors import BRIGHT, INFO, RESET
from microdetect.utils.colored_version import ColoredVersionAction


class TestColoredVersionAction(unittest.TestCase):
    """Test cases for ColoredVersionAction class."""

    def setUp(self):
        """Set up test fixtures."""
        self.version = "1.0.0"
        self.action = ColoredVersionAction(
            option_strings=["--version"],
            version=self.version,
            dest="version"  # Explicitly set the dest parameter
        )

    def test_init(self):
        """Test initialization."""
        self.assertEqual(self.action.version, self.version)
        self.assertEqual(self.action.option_strings, ["--version"])
        self.assertEqual(self.action.dest, "version")
        self.assertEqual(self.action.nargs, 0)
        self.assertTrue("show program's version number" in self.action.help)

    def test_call(self):
        """Test __call__ method."""
        # Create a mock for microdetect.utils module
        mock_utils = MagicMock()
        mock_utils.get_logo_with_name_ascii.return_value = "MOCK LOGO"
        
        # Patch the import statement inside __call__
        with patch.dict('sys.modules', {'microdetect.utils': mock_utils}):
            parser = argparse.ArgumentParser()
            namespace = argparse.Namespace()
            
            # Mock parser.exit to avoid SystemExit
            with patch.object(parser, 'exit') as mock_exit:
                self.action(parser, namespace, None)
                
                # Check that parser.exit was called with the right message
                mock_exit.assert_called_once()
                self.assertEqual(mock_exit.call_args[1]['message'], "MOCK LOGO")
                
                # Check that get_logo_with_name_ascii was called with the right custom_text
                mock_utils.get_logo_with_name_ascii.assert_called_once()
                custom_text = mock_utils.get_logo_with_name_ascii.call_args[1]['custom_text']
                self.assertIn(self.version, custom_text)
                self.assertIn(INFO, custom_text)
                self.assertIn(BRIGHT, custom_text)
                self.assertIn(RESET, custom_text)

    def test_integrated_with_parser(self):
        """Test integration with ArgumentParser."""
        parser = argparse.ArgumentParser()
        parser.add_argument('--version', action=ColoredVersionAction, version="1.0.0")
        
        # Check the action object in the parser
        version_action = None
        for action in parser._actions:
            if '--version' in action.option_strings:
                version_action = action
                break
        
        self.assertIsNotNone(version_action)
        self.assertIsInstance(version_action, ColoredVersionAction)
        self.assertEqual(version_action.version, "1.0.0")


if __name__ == "__main__":
    unittest.main()