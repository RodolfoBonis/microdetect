import tkinter as tk
import unittest.mock as mock

import pytest

from microdetect.annotation.annotator.ui.base import (
    center_window,
    configure_window_close,
    create_secure_dialog,
    is_window_valid,
)


class TestUIBase:

    @pytest.fixture
    def mock_tk(self):
        """Mock tkinter functionality for testing"""
        with mock.patch("tkinter.Toplevel") as mock_toplevel, mock.patch("tkinter.Tk") as mock_tk, mock.patch(
            "tkinter._default_root", None
        ):
            mock_instance = mock_toplevel.return_value
            mock_instance.winfo_exists.return_value = True
            yield {"toplevel": mock_toplevel, "tk": mock_tk, "instance": mock_instance}

    def test_create_secure_dialog(self, mock_tk):
        """Test the creation of secure dialog windows"""
        dialog = create_secure_dialog()
        assert dialog is not None
        mock_tk["toplevel"].assert_called_once()

        # Test with existing root
        with mock.patch("tkinter._default_root", mock.MagicMock()):
            dialog = create_secure_dialog()
            assert dialog is not None

    def test_is_window_valid(self, mock_tk):
        """Test window validation function"""
        # Test with valid window
        widget = mock.MagicMock()
        widget.winfo_exists.return_value = True
        assert is_window_valid(widget) is True

        # Test with destroyed window
        widget.winfo_exists.side_effect = tk.TclError("application has been destroyed")
        assert is_window_valid(widget) is False

        # Test with None
        assert is_window_valid(None) is True

    def test_center_window(self, mock_tk):
        """Test window centering functionality"""
        window = mock.MagicMock()
        window.winfo_width.return_value = 500
        window.winfo_height.return_value = 300
        window.winfo_screenwidth.return_value = 1920
        window.winfo_screenheight.return_value = 1080

        center_window(window)
        window.geometry.assert_called_once_with("500x300+710+390")

    def test_configure_window_close(self):
        """Test window close configuration"""
        window = mock.MagicMock()
        callback = mock.MagicMock()

        configure_window_close(window, callback)
        window.protocol.assert_called_once_with("WM_DELETE_WINDOW", callback)
