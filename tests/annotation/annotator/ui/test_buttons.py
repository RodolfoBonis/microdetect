import unittest.mock as mock

import pytest

from microdetect.annotation.annotator.ui.buttons import ButtonManager


class TestButtonManager:

    @pytest.fixture
    def button_manager(self):
        """Create a ButtonManager with mock frame and callbacks"""
        parent_frame = mock.MagicMock()
        callbacks = {"reset": mock.MagicMock(), "save": mock.MagicMock(), "toggle_edit_mode": mock.MagicMock()}
        manager = ButtonManager(parent_frame, callbacks)
        return manager

    def test_initialization(self, button_manager):
        """Test ButtonManager initialization"""
        assert button_manager.parent is not None
        assert button_manager.callbacks is not None
        assert button_manager.buttons == {}

    def test_call_callback(self, button_manager):
        """Test callback invocation"""
        button_manager._call_callback("reset", "arg1", kwarg1="value")
        button_manager.callbacks["reset"].assert_called_once_with("arg1", kwarg1="value")

        # Test non-existent callback
        result = button_manager._call_callback("nonexistent")
        assert result is None

    @mock.patch("tkinter.Button")
    @mock.patch("tkinter.Frame")
    def test_create_main_buttons(self, mock_frame, mock_button, button_manager):
        """Test creation of main button interface"""
        mock_frame_instances = [mock.MagicMock(), mock.MagicMock()]
        mock_frame.side_effect = mock_frame_instances

        button_frame, button_frame2 = button_manager.create_main_buttons()

        # Verify frames were created and packed
        assert len(button_manager.buttons) > 0
        mock_frame_instances[0].pack.assert_called()
        mock_frame_instances[1].pack.assert_called()

        # Verify essential buttons exist
        assert "reset" in button_manager.buttons
        assert "save" in button_manager.buttons
        assert "next" in button_manager.buttons

    @mock.patch("tkinter.Button")
    def test_add_suggestion_buttons(self, mock_button, button_manager):
        """Test adding suggestion buttons"""
        button_frame = mock.MagicMock()
        button_frame2 = mock.MagicMock()

        button_manager.add_suggestion_buttons(button_frame, button_frame2)

        # Verify buttons were created and configured correctly
        assert "suggestion" in button_manager.buttons
        assert "apply_suggestions" in button_manager.buttons

    def test_update_button_state(self, button_manager):
        """Test updating button states"""
        mock_button = mock.MagicMock()
        button_manager.buttons["test_button"] = mock_button

        # Test updating an existing button
        button_manager.update_button_state("test_button", text="New Text", bg="red")
        mock_button.config.assert_called_once_with(text="New Text", bg="red")

        # Test updating a non-existent button
        button_manager.update_button_state("nonexistent", text="Should not error")

    def test_get_button(self, button_manager):
        """Test retrieving buttons"""
        mock_button = mock.MagicMock()
        button_manager.buttons["test_button"] = mock_button

        # Test getting existing button
        assert button_manager.get_button("test_button") is mock_button

        # Test getting non-existent button
        assert button_manager.get_button("nonexistent") is None
