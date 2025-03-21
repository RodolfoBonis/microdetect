import unittest
import argparse
import re

from microdetect.utils.colors import BRIGHT, INFO, RESET, SUCCESS
from microdetect.utils.colored_help import ColoredHelpFormatter


class TestColoredHelpFormatter(unittest.TestCase):
    """Test cases for ColoredHelpFormatter class."""

    def setUp(self):
        """Set up test fixtures."""
        self.parser = argparse.ArgumentParser(
            prog="testprog",
            formatter_class=ColoredHelpFormatter
        )
        self.formatter = ColoredHelpFormatter("testprog")

    def test_init(self):
        """Test initialization."""
        self.assertEqual(self.formatter._prog, "testprog")
        self.assertEqual(self.formatter._width, 100)
        self.assertEqual(self.formatter._max_help_position, 24)

    def test_start_section(self):
        """Test start_section method adds colors."""
        mock_heading = "Test Heading"
        
        # Use a patching approach instead of checking the internal value
        orig_super_start_section = argparse.RawDescriptionHelpFormatter.start_section
        
        try:
            # Mock the parent class method to check what's passed to it
            calls = []
            def mock_start_section(self, heading):
                calls.append(heading)
            
            argparse.RawDescriptionHelpFormatter.start_section = mock_start_section
            
            # Now call our method
            self.formatter.start_section(mock_heading)
            
            # Check that the heading passed to super() contained color codes
            self.assertEqual(len(calls), 1)
            self.assertTrue(BRIGHT in calls[0])
            self.assertTrue(INFO in calls[0])
            self.assertTrue(RESET in calls[0])
            self.assertTrue(mock_heading in calls[0])
            
        finally:
            # Restore the original method
            argparse.RawDescriptionHelpFormatter.start_section = orig_super_start_section

    def test_format_action_help(self):
        """Test _format_action method handles help action."""
        # Create an action for --help
        help_action = argparse.Action(
            option_strings=['--help'],
            dest='help',
            default=argparse.SUPPRESS,
            help='show this help message'
        )
        
        result = self.formatter._format_action(help_action)
        
        # Check that --help is colored
        self.assertIn(f"{SUCCESS}--help{RESET}", result)

    def test_format_action_version(self):
        """Test _format_action method handles version action."""
        # Create an action for --version
        version_action = argparse.Action(
            option_strings=['--version'],
            dest='version',
            default=argparse.SUPPRESS,
            help='show program version'
        )
        
        result = self.formatter._format_action(version_action)
        
        # Check that --version is colored
        self.assertIn(f"{SUCCESS}--version{RESET}", result)

    def test_format_action_regular(self):
        """Test _format_action method with regular action."""
        # Create a regular action
        regular_action = argparse.Action(
            option_strings=['--test'],
            dest='test',
            default=None,
            help='test action'
        )
        
        result = self.formatter._format_action(regular_action)
        
        # Check that it doesn't include the colored strings
        self.assertNotIn(f"{SUCCESS}--test{RESET}", result)
        # Should contain the normal option
        self.assertIn("--test", result)

    def test_formatter_integrated_with_parser(self):
        """Test that the formatter works when integrated with a parser."""
        parser = argparse.ArgumentParser(
            prog="testprog",
            formatter_class=ColoredHelpFormatter,
            description="Test program description"
        )
        parser.add_argument('--test', help='Test argument')
        
        # Instead of capturing the help output (which is complex),
        # let's directly check that the formatter class is properly registered
        self.assertIsInstance(parser._get_formatter(), ColoredHelpFormatter)
        
        # And then test that the help action is properly formatted by accessing it directly
        for action in parser._actions:
            if action.dest == 'help':
                help_text = parser._get_formatter()._format_action(action)
                self.assertIn(f"{SUCCESS}--help{RESET}", help_text)
                break
        else:
            self.fail("Help action not found in parser")


if __name__ == "__main__":
    unittest.main()