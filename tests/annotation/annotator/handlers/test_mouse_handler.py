import unittest.mock as mock

import pytest

from microdetect.annotation.annotator.handlers.mouse_handler import MouseHandler
from microdetect.annotation.annotator.utils.constants import HANDLE_NONE


class TestMouseHandler:

    @pytest.fixture
    def mock_canvas(self):
        """Create a mock canvas"""
        return mock.MagicMock()

    @pytest.fixture
    def mock_box_manager(self):
        """Create a mock BoundingBoxManager"""
        manager = mock.MagicMock()
        manager.selected_idx = None
        manager.resize_handle = HANDLE_NONE
        manager.get_box_count.return_value = 0
        return manager

    @pytest.fixture
    def mock_visualizer(self):
        """Create a mock AnnotationVisualizer"""
        return mock.MagicMock()

    @pytest.fixture
    def mock_callbacks(self):
        """Create mock callbacks"""
        return {
            'reset_window_closed': mock.MagicMock(return_value=True),
            'update_status': mock.MagicMock(),
            'add_to_history': mock.MagicMock(),
            'get_current_class': mock.MagicMock(return_value="0-test"),
            'redraw_with_zoom': mock.MagicMock(),
            'check_auto_save': mock.MagicMock()
        }

    @pytest.fixture
    def mouse_handler(self, mock_canvas, mock_box_manager, mock_visualizer, mock_callbacks):
        """Create a MouseHandler with mock dependencies"""
        with mock.patch('microdetect.annotation.annotator.handlers.mouse_handler.is_window_valid',
                        return_value=True):
            handler = MouseHandler(mock_canvas, mock_box_manager, mock_visualizer, mock_callbacks)
            handler.set_config(1.0, 1.0, 100, 100)  # Set default config
            return handler

    def test_initialization(self, mouse_handler, mock_canvas, mock_box_manager, mock_visualizer, mock_callbacks):
        """Test initialization of MouseHandler"""
        assert mouse_handler.canvas == mock_canvas
        assert mouse_handler.box_manager == mock_box_manager
        assert mouse_handler.visualizer == mock_visualizer
        assert mouse_handler.callbacks == mock_callbacks

        # Check default state
        assert mouse_handler.start_x is None
        assert mouse_handler.start_y is None
        assert mouse_handler.current_rect_id is None
        assert mouse_handler.edit_mode is False
        assert mouse_handler.pan_mode is False

        # Check event bindings were set up
        assert mock_canvas.bind.call_count >= 9  # At least 9 bindings

    def test_set_config(self, mouse_handler):
        """Test setting configuration values"""
        mouse_handler.set_config(0.5, 2.0, 200, 150)

        assert mouse_handler.display_scale == 0.5
        assert mouse_handler.scale_factor == 2.0
        assert mouse_handler.original_w == 200
        assert mouse_handler.original_h == 150

    def test_set_mode(self, mouse_handler):
        """Test setting edit and pan modes"""
        mouse_handler.set_mode(True, False)

        assert mouse_handler.edit_mode is True
        assert mouse_handler.pan_mode is False

        mouse_handler.set_mode(False, True)

        assert mouse_handler.edit_mode is False
        assert mouse_handler.pan_mode is True

    def test_call_callback(self, mouse_handler, mock_callbacks):
        """Test calling a callback by name"""
        # Call existing callback
        mouse_handler._call_callback('update_status', 'test message')
        mock_callbacks['update_status'].assert_called_once_with('test message')

        # Call non-existent callback (should not raise error)
        result = mouse_handler._call_callback('non_existent')
        assert result is None

    def test_reset(self, mouse_handler, mock_canvas):
        """Test resetting the handler state"""
        # Set up initial state
        mouse_handler.start_x = 10
        mouse_handler.start_y = 20
        mouse_handler.current_rect_id = "rect123"

        # Reset state
        mouse_handler.reset()

        # Check state was reset
        assert mouse_handler.start_x is None
        assert mouse_handler.start_y is None
        assert mouse_handler.current_rect_id is None
        mock_canvas.delete.assert_called_once_with("rect123")

    def test_on_mouse_down(self, mouse_handler, mock_canvas, mock_box_manager, mock_callbacks):
        """Test the mouse down event handler"""
        # Mock event
        event = mock.MagicMock()
        event.x = 50
        event.y = 50

        # Mock canvas coordinates
        mock_canvas.canvasx.return_value = 50
        mock_canvas.canvasy.return_value = 50

        # Test in normal drawing mode (not edit or pan)
        mouse_handler.on_mouse_down(event)

        # Should set starting coordinates
        assert mouse_handler.start_x == 50
        assert mouse_handler.start_y == 50

        # Should call reset_window_closed
        mock_callbacks['reset_window_closed'].assert_called_once()

        # Test in pan mode
        mouse_handler.pan_mode = True
        mock_canvas.reset_mock()
        mock_callbacks['reset_window_closed'].reset_mock()

        mouse_handler.on_mouse_down(event)

        # Should use canvas.scan_mark
        mock_canvas.scan_mark.assert_called_once_with(50, 50)

        # Test in edit mode with box selection
        mouse_handler.pan_mode = False
        mouse_handler.edit_mode = True
        mock_box_manager.find_box_at_position.return_value = 1  # Found box with index 1
        mock_box_manager.get_box.return_value = ("0", 10, 10, 60, 60)  # Sample box
        mock_callbacks['reset_window_closed'].reset_mock()

        mouse_handler.on_mouse_down(event)

        # Should select the box
        mock_box_manager.select_box.assert_called_once_with(1)
        # Should call update_status
        mock_callbacks['update_status'].assert_called_with("Caixa 2 selecionada para edição")

    def test_on_mouse_move(self, mouse_handler, mock_canvas, mock_box_manager, mock_visualizer):
        """Test the mouse move event handler"""
        # Set up initial state
        mouse_handler.start_x = 10
        mouse_handler.start_y = 10

        # Mock event
        event = mock.MagicMock()
        event.x = 50
        event.y = 50

        # Mock canvas coordinates
        mock_canvas.canvasx.return_value = 50
        mock_canvas.canvasy.return_value = 50

        # Test in normal drawing mode (not edit or pan)
        mouse_handler.on_mouse_move(event)

        # Should draw temporary rectangle
        mock_visualizer.draw_temporary_box.assert_called_once()

        # Test in pan mode
        mouse_handler.pan_mode = True
        mock_canvas.reset_mock()
        mock_visualizer.reset_mock()

        mouse_handler.on_mouse_move(event)

        # Should use canvas.scan_dragto
        mock_canvas.scan_dragto.assert_called_once_with(50, 50, gain=1)

        # Test in edit mode with box selected
        mouse_handler.pan_mode = False
        mouse_handler.edit_mode = True
        mouse_handler.box_manager.selected_idx = 1
        mock_box_manager.get_box.return_value = ("0", 20, 20, 70, 70)  # Sample box
        mock_visualizer.reset_mock()

        mouse_handler.on_mouse_move(event)

        # Should update box
        mock_box_manager.update_box.assert_called_once()
        # Should redraw boxes
        mock_visualizer.draw_bounding_boxes.assert_called_once()

    def test_handle_resize(self, mouse_handler):
        """Test handling box resizing"""
        # Create a mock for update_box
        orig_box_manager = mouse_handler.box_manager
        mouse_handler.box_manager = mock.MagicMock()

        try:
            # Test each resize handle
            for handle in range(1, 9):  # 1-8 are valid handles
                mouse_handler.box_manager.resize_handle = handle
                mouse_handler._handle_resize("0", 10, 10, 50, 50, 5, 5)

                # Should call update_box with modified coordinates
                assert mouse_handler.box_manager.update_box.called
                mouse_handler.box_manager.reset_mock()
        finally:
            # Restore original box_manager
            mouse_handler.box_manager = orig_box_manager

    def test_on_mouse_up(self, mouse_handler, mock_canvas, mock_box_manager, mock_visualizer, mock_callbacks):
        """Test the mouse up event handler"""
        # Set up initial state
        mouse_handler.start_x = 10
        mouse_handler.start_y = 10
        mouse_handler.current_rect_id = "rect123"

        # Mock event
        event = mock.MagicMock()
        event.x = 50
        event.y = 50

        # Mock canvas coordinates
        mock_canvas.canvasx.return_value = 50
        mock_canvas.canvasy.return_value = 50

        # Test in normal drawing mode (not edit or pan) with enough movement
        mock_callbacks['get_current_class'].return_value = "0-test"

        mouse_handler.on_mouse_up(event)

        # Should add a new box
        mock_box_manager.add_box.assert_called_once()
        # Should add to history
        mock_callbacks['add_to_history'].assert_called_once()
        # Should clear the temporary rectangle
        mock_canvas.delete.assert_called_once_with("rect123")
        # Should check auto-save
        mock_callbacks['check_auto_save'].assert_called_once()

        # Test in edit mode with resize
        mouse_handler.edit_mode = True
        mouse_handler.box_manager.selected_idx = 1
        mouse_handler.box_manager.resize_handle = 1  # NW handle
        mouse_handler.box_manager.original_box_state = ("0", 10, 10, 50, 50)
        mock_box_manager.reset_mock()
        mock_callbacks['add_to_history'].reset_mock()

        mouse_handler.on_mouse_up(event)

        # Should add resize action to history
        mock_callbacks['add_to_history'].assert_called_once_with(
            'resize', {'index': 1, 'before': ("0", 10, 10, 50, 50), 'after': mock_box_manager.get_box.return_value}
        )
        # Should reset resize handle
        assert mock_box_manager.resize_handle == 0

    def test_on_mouse_wheel(self, mouse_handler, mock_callbacks):
        """Test the mouse wheel event handler for zooming"""
        # Mock event
        event = mock.MagicMock()
        event.delta = 120  # Positive delta (zoom in)
        event.num = 4  # Linux scroll up

        # Test zoom in
        mouse_handler.on_mouse_wheel(event)

        # Scale factor should increase
        assert mouse_handler.scale_factor > 1.0
        # Should redraw with zoom
        mock_callbacks['redraw_with_zoom'].assert_called_once_with(mouse_handler.scale_factor)

        # Reset mocks
        mock_callbacks['redraw_with_zoom'].reset_mock()

        # Test zoom out
        event.delta = -120  # Negative delta (zoom out)
        event.num = 5  # Linux scroll down

        # Set scale factor high to see clear change
        mouse_handler.scale_factor = 2.0

        mouse_handler.on_mouse_wheel(event)

        # Scale factor should decrease
        assert mouse_handler.scale_factor < 2.0
        # Should redraw with zoom
        mock_callbacks['redraw_with_zoom'].assert_called_once_with(mouse_handler.scale_factor)

    def test_on_middle_press_drag(self, mouse_handler, mock_canvas):
        """Test middle button press and drag for panning"""
        # Mock event
        event = mock.MagicMock()
        event.x = 50
        event.y = 50

        # Test middle button press
        mouse_handler.on_middle_press(event)

        # Should mark scan position
        mock_canvas.scan_mark.assert_called_once_with(50, 50)

        # Test middle button drag
        mouse_handler.on_middle_drag(event)

        # Should drag to new position
        mock_canvas.scan_dragto.assert_called_once_with(50, 50, gain=1)

    def test_on_right_press_drag(self, mouse_handler):
        """Test right button press and drag for panning"""
        # Create spies for middle press/drag methods
        with mock.patch.object(mouse_handler, 'on_middle_press') as mock_press:
            with mock.patch.object(mouse_handler, 'on_middle_drag') as mock_drag:
                # Mock event
                event = mock.MagicMock()

                # Test right button press
                mouse_handler.on_right_press(event)

                # Should call on_middle_press
                mock_press.assert_called_once_with(event)

                # Test right button drag
                mouse_handler.on_right_drag(event)

                # Should call on_middle_drag
                mock_drag.assert_called_once_with(event)

    def test_invalid_window(self, mock_canvas, mock_box_manager, mock_visualizer, mock_callbacks):
        """Test behavior when window is invalid"""
        # Create handler with invalid window
        with mock.patch('microdetect.annotation.annotator.handlers.mouse_handler.is_window_valid',
                        return_value=False):
            handler = MouseHandler(mock_canvas, mock_box_manager, mock_visualizer, mock_callbacks)

            # Test all event handlers with invalid window
            event = mock.MagicMock()

            # Should return early without error
            handler.on_mouse_down(event)
            handler.on_mouse_move(event)
            handler.on_mouse_up(event)
            handler.on_mouse_wheel(event)
            handler.on_middle_press(event)
            handler.on_middle_drag(event)

            # None of these should raise exceptions