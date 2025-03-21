import unittest
import sys
import os

# Add the project root to the path so we can import modules directly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import directly without going through the entire package hierarchy
from microdetect.annotation.annotator.handlers.action_history import ActionHistory


class TestActionHistory(unittest.TestCase):
    """Test cases for ActionHistory class."""

    def setUp(self):
        """Set up test fixtures."""
        self.action_history = ActionHistory(max_history=5)  # Smaller max_history for testing

    def test_init(self):
        """Test initialization."""
        self.assertEqual(self.action_history.history, [])
        self.assertEqual(self.action_history.max_history, 5)

        # Test with default max_history
        default_history = ActionHistory()
        self.assertEqual(default_history.max_history, 50)

    def test_add(self):
        """Test adding actions to history."""
        action_data = {"box_id": "box1", "original_pos": (10, 10, 20, 20)}
        self.action_history.add("add", action_data)

        self.assertEqual(len(self.action_history.history), 1)
        self.assertEqual(self.action_history.history[0]["type"], "add")
        self.assertEqual(self.action_history.history[0]["data"], action_data)

    def test_add_limit(self):
        """Test that history is limited to max_history."""
        # Add more actions than max_history allows
        for i in range(10):
            self.action_history.add(f"action{i}", {"data": i})

        # Check that only the most recent max_history actions are kept
        self.assertEqual(len(self.action_history.history), 5)
        self.assertEqual(self.action_history.history[0]["type"], "action5")
        self.assertEqual(self.action_history.history[4]["type"], "action9")

    def test_undo_with_history(self):
        """Test undo when history is not empty."""
        action1 = {"box_id": "box1", "position": (10, 10, 20, 20)}
        action2 = {"box_id": "box2", "position": (30, 30, 40, 40)}
        
        self.action_history.add("add", action1)
        self.action_history.add("add", action2)
        
        # Undo last action
        last_action = self.action_history.undo()
        
        self.assertEqual(last_action["type"], "add")
        self.assertEqual(last_action["data"], action2)
        self.assertEqual(len(self.action_history.history), 1)

    def test_undo_empty_history(self):
        """Test undo when history is empty."""
        self.assertIsNone(self.action_history.undo())

    def test_clear(self):
        """Test clearing the history."""
        self.action_history.add("add", {"box_id": "box1"})
        self.action_history.add("move", {"box_id": "box1"})
        
        self.assertEqual(len(self.action_history.history), 2)
        
        self.action_history.clear()
        self.assertEqual(len(self.action_history.history), 0)

    def test_is_empty(self):
        """Test is_empty method."""
        # Initially should be empty
        self.assertTrue(self.action_history.is_empty())
        
        # After adding an action, should not be empty
        self.action_history.add("add", {"box_id": "box1"})
        self.assertFalse(self.action_history.is_empty())
        
        # After undoing, should be empty again
        self.action_history.undo()
        self.assertTrue(self.action_history.is_empty())


if __name__ == "__main__":
    unittest.main()