import unittest.mock as mock
import pytest

from microdetect.annotation.annotator.handlers.keyboard_handler import KeyboardHandler


class TestKeyboardHandler:

    @pytest.fixture
    def mock_root(self):
        """Create a mock Tkinter root widget"""
        return mock.MagicMock()

    @pytest.fixture
    def mock_callbacks(self):
        """Create mock callbacks"""
        return {
            'reset_zoom': mock.MagicMock(),
            'toggle_pan_mode': mock.MagicMock(),
            'undo': mock.MagicMock(),
            'delete_selected': mock.MagicMock(),
            'save': mock.MagicMock(),
            'on_closing': mock.MagicMock()
        }

    @pytest.fixture
    def keyboard_handler(self, mock_root, mock_callbacks):
        """Create a KeyboardHandler with mocked dependencies"""
        with mock.patch('microdetect.annotation.annotator.handlers.keyboard_handler.is_window_valid',
                        return_value=True):
            return KeyboardHandler(mock_root, mock_callbacks)

    def test_initialization(self, keyboard_handler, mock_root, mock_callbacks):
        """Test initialization of KeyboardHandler"""
        assert keyboard_handler.root == mock_root
        assert keyboard_handler.callbacks == mock_callbacks

    def test_call_callback(self, keyboard_handler, mock_callbacks):
        """Test calling a callback by name"""
        # Call existing callback
        keyboard_handler._call_callback('reset_zoom', 'arg1', kwarg1='value')
        mock_callbacks['reset_zoom'].assert_called_once_with('arg1', kwarg1='value')

        # Call non-existent callback (should not raise error)
        result = keyboard_handler._call_callback('non_existent')
        assert result is None

    def test_setup_keyboard_shortcuts(self, mock_root, mock_callbacks):
        """Test setting up keyboard shortcuts"""
        # Test with valid window
        with mock.patch('microdetect.annotation.annotator.handlers.keyboard_handler.is_window_valid',
                        return_value=True):
            handler = KeyboardHandler(mock_root, mock_callbacks)

            # Check that bind was called for each shortcut
            assert mock_root.bind.call_count > 0

            # Check specific shortcuts
            mock_root.bind.assert_any_call("<r>", mock.ANY)
            mock_root.bind.assert_any_call("<p>", mock.ANY)
            mock_root.bind.assert_any_call("<z>", mock.ANY)
            mock_root.bind.assert_any_call("<s>", mock.ANY)
            mock_root.bind.assert_any_call("<q>", mock.ANY)

        # Test with invalid window
        mock_root.reset_mock()
        with mock.patch('microdetect.annotation.annotator.handlers.keyboard_handler.is_window_valid',
                        return_value=False):
            handler = KeyboardHandler(mock_root, mock_callbacks)

            # Should not attempt to bind events
            mock_root.bind.assert_not_called()

    def test_setup_keyboard_shortcuts_exception(self, mock_root, mock_callbacks):
        """Test handling exceptions during keyboard setup"""
        # Make bind raise an exception
        mock_root.bind.side_effect = Exception("Test error")

        # Should not raise error to caller
        with mock.patch('microdetect.annotation.annotator.handlers.keyboard_handler.is_window_valid',
                        return_value=True):
            with mock.patch('microdetect.annotation.annotator.handlers.keyboard_handler.logger') as mock_logger:
                handler = KeyboardHandler(mock_root, mock_callbacks)

                # Should log the error
                mock_logger.error.assert_called()

    def test_update_root(self, keyboard_handler):
        """Test updating the root widget"""
        new_root = mock.MagicMock()

        # Update with new root
        keyboard_handler.update_root(new_root)

        # Should update internal reference and set up shortcuts
        assert keyboard_handler.root == new_root
        assert new_root.bind.call_count > 0

    def test_keypress_handlers(self, keyboard_handler, mock_callbacks):
        """Test that keypress handlers call the right callbacks"""
        # Get lambda function for a specific key
        keypress_handlers = {}
        for call in keyboard_handler.root.bind.call_args_list:
            key_sequence = call[0][0]
            handler = call[0][1]
            keypress_handlers[key_sequence] = handler

        # Test reset_zoom handler
        event = mock.MagicMock()
        keypress_handlers["<r>"](event)
        mock_callbacks['reset_zoom'].assert_called_once()

        # Test toggle_pan_mode handler
        event = mock.MagicMock()
        keypress_handlers["<p>"](event)
        mock_callbacks['toggle_pan_mode'].assert_called_once()

        # Test undo handler
        event = mock.MagicMock()
        keypress_handlers["<z>"](event)
        mock_callbacks['undo'].assert_called_once()

        # Test save handler
        event = mock.MagicMock()
        keypress_handlers["<s>"](event)
        mock_callbacks['save'].assert_called_once()

        # Test close handler
        event = mock.MagicMock()
        keypress_handlers["<q>"](event)
        mock_callbacks['on_closing'].assert_called_once()