import os
import unittest.mock as mock

import pytest

from microdetect.annotation.annotator.ui.main_window import MainWindow


class TestMainWindow:

    @pytest.fixture
    def main_window(self):
        """Create MainWindow with test parameters"""
        image_path = '/path/to/test/image.jpg'
        classes = ['0-class1', '1-class2', '2-class3']
        callbacks = {
            'on_closing': mock.MagicMock(),
            'set_current_class': mock.MagicMock()
        }
        return MainWindow(image_path, classes, callbacks)

    @mock.patch('tkinter.Tk')
    @mock.patch('tkinter.Frame')
    @mock.patch('tkinter.Canvas')
    @mock.patch('tkinter.Label')
    @mock.patch('microdetect.annotation.annotator.ui.buttons.ButtonManager')
    def test_create(self, mock_button_mgr, mock_label, mock_canvas, mock_frame, mock_tk, main_window):
        """Test creating the main window components"""
        # Setup mocks
        mock_button_mgr_instance = mock_button_mgr.return_value
        mock_button_mgr_instance.create_main_buttons.return_value = (mock.MagicMock(), mock.MagicMock())

        # Call create method
        root, canvas, class_var, status_label = main_window.create()

        # Verify window setup
        mock_tk.return_value.title.assert_called_once()
        mock_tk.return_value.protocol.assert_called_once_with(
            "WM_DELETE_WINDOW", main_window.callbacks['on_closing']
        )

        # Verify canvas creation
        mock_canvas.assert_called_once()

        # Verify components created
        assert root is not None
        assert canvas is not None
        assert class_var is not None
        assert status_label is not None

        # Verify button manager used
        mock_button_mgr_instance.create_main_buttons.assert_called_once()
        mock_button_mgr_instance.add_suggestion_buttons.assert_called_once()

    def test_update_image_info(self, main_window):
        """Test updating image info display"""
        main_window.info_label = mock.MagicMock()
        main_window.update_image_info(800, 600)

        expected_text = f"Imagem: {os.path.basename(main_window.image_path)} | Dimensões: 800x600"
        main_window.info_label.config.assert_called_once_with(text=expected_text)

    def test_update_status(self, main_window):
        """Test updating status label"""
        main_window.status_label = mock.MagicMock()

        # Test with message only
        main_window.update_status(msg="Testing status")
        main_window.status_label.config.assert_called_with(text="Testing status")

        # Test with box count only
        main_window.update_status(box_count=5)
        main_window.status_label.config.assert_called_with(text="Contagem: 5 | Desenhe clicando e arrastando")

        # Test with both
        main_window.update_status(msg="Testing both", box_count=10)
        main_window.status_label.config.assert_called_with(text="Contagem: 10 | Testing both")

        # Test with no status_label
        main_window.status_label = None
        main_window.update_status(msg="Should not raise error")