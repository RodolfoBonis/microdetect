import unittest.mock as mock
import pytest

from microdetect.annotation.annotator.annotation.visualizer import AnnotationVisualizer


class TestAnnotationVisualizer:

    @pytest.fixture
    def mock_canvas(self):
        """Create a mock canvas for testing"""
        return mock.MagicMock()

    @pytest.fixture
    def visualizer(self, mock_canvas):
        """Create an AnnotationVisualizer for testing"""
        classes = ["0-class1", "1-class2", "2-class3"]
        return AnnotationVisualizer(mock_canvas, classes, handle_size=6)

    def test_initialization(self, visualizer, mock_canvas):
        """Test initialization of AnnotationVisualizer"""
        assert visualizer.canvas == mock_canvas
        assert visualizer.classes == ["0-class1", "1-class2", "2-class3"]
        assert visualizer.handle_size == 6

    def test_get_class_name(self, visualizer):
        """Test getting class name from class ID"""
        # Valid class ID
        assert visualizer.get_class_name("0") == "0-class1"
        assert visualizer.get_class_name("1") == "1-class2"
        assert visualizer.get_class_name("2") == "2-class3"

        # Invalid class ID
        assert visualizer.get_class_name("99") == "99-desconhecido"

    def test_draw_bounding_boxes(self, visualizer, mock_canvas):
        """Test drawing bounding boxes on canvas"""
        # Reset mock call counters
        mock_canvas.reset_mock()

        # Test with empty boxes list
        result = visualizer.draw_bounding_boxes([], display_scale=1.0, scale_factor=1.0)
        assert result is True
        mock_canvas.delete.assert_called()
        mock_canvas.create_rectangle.assert_not_called()

        # Test with boxes
        boxes = [
            ("0", 10, 10, 50, 50),
            ("1", 100, 100, 200, 200)
        ]

        # Reset mock call counters
        mock_canvas.reset_mock()

        # Test normal drawing (no highlight)
        result = visualizer.draw_bounding_boxes(boxes, display_scale=1.0, scale_factor=1.0)
        assert result is True

        # Should delete old elements and create new ones
        mock_canvas.delete.assert_called()
        assert mock_canvas.create_rectangle.call_count == 2
        assert mock_canvas.create_text.call_count == 2

        # Test with highlight
        mock_canvas.reset_mock()
        result = visualizer.draw_bounding_boxes(boxes, highlight_idx=1, display_scale=1.0, scale_factor=1.0)
        assert result is True

        # Should create rectangles, text, and handles for highlighted box
        assert mock_canvas.create_rectangle.call_count > 2  # Additional handles

        # Test with scaling
        mock_canvas.reset_mock()
        result = visualizer.draw_bounding_boxes(boxes, display_scale=0.5, scale_factor=2.0)
        assert result is True

        # Scale factors should multiply coordinates
        call_args = mock_canvas.create_rectangle.call_args_list[0][0]
        # First box: (10, 10, 50, 50) * 0.5 * 2.0 = (10, 10, 50, 50)
        assert call_args[0] == 10  # x1
        assert call_args[1] == 10  # y1
        assert call_args[2] == 50  # x2
        assert call_args[3] == 50  # y2

        # Test with error during drawing
        mock_canvas.create_rectangle.side_effect = Exception("Test error")
        result = visualizer.draw_bounding_boxes(boxes)
        assert result is False

    def test_draw_resize_handles(self, visualizer, mock_canvas):
        """Test drawing resize handles for a box"""
        # Call private method directly for testing
        visualizer._draw_resize_handles(10, 10, 50, 50, "red")

        # Should create 8 handle rectangles (4 corners, 4 sides)
        assert mock_canvas.create_rectangle.call_count == 8

    def test_draw_temporary_box(self, visualizer, mock_canvas):
        """Test drawing a temporary box during creation"""
        # Test creating a new temporary box
        temp_id = visualizer.draw_temporary_box(10, 10, 50, 50)

        # Should create a rectangle and return its ID
        mock_canvas.create_rectangle.assert_called_once()
        assert temp_id is not None

        # Test replacing an existing temporary box
        mock_canvas.reset_mock()
        existing_temp_id = "temp_box_id"
        temp_id = visualizer.draw_temporary_box(20, 20, 60, 60, existing_temp_id)

        # Should delete old rectangle and create a new one
        mock_canvas.delete.assert_called_once_with(existing_temp_id)
        mock_canvas.create_rectangle.assert_called_once()
        assert temp_id is not None

    def test_draw_suggestions(self, visualizer, mock_canvas):
        """Test drawing suggestion boxes"""
        # Reset mock call counters
        mock_canvas.reset_mock()

        # Test with empty suggestions
        visualizer.draw_suggestions([], 1.0, 1.0)
        mock_canvas.delete.assert_called()
        mock_canvas.create_rectangle.assert_not_called()

        # Test with suggestions
        suggestions = [
            ("0", 10, 10, 50, 50),
            ("1", 100, 100, 200, 200)
        ]

        # Reset mock call counters
        mock_canvas.reset_mock()

        # Test drawing suggestions
        visualizer.draw_suggestions(suggestions, 1.0, 1.0)

        # Should delete old elements and create new ones
        mock_canvas.delete.assert_called()
        assert mock_canvas.create_rectangle.call_count == 2
        assert mock_canvas.create_text.call_count == 2

        # Test with scaling
        mock_canvas.reset_mock()
        visualizer.draw_suggestions(suggestions, 0.5, 2.0)

        # Scale factors should multiply coordinates
        call_args = mock_canvas.create_rectangle.call_args_list[0][0]
        # First box: (10, 10, 50, 50) * 0.5 * 2.0 = (10, 10, 50, 50)
        assert call_args[0] == 10  # x1
        assert call_args[1] == 10  # y1
        assert call_args[2] == 50  # x2
        assert call_args[3] == 50  # y2

    def test_clear_all(self, visualizer, mock_canvas):
        """Test clearing all annotations"""
        visualizer.clear_all()

        # Should delete all types of elements
        assert mock_canvas.delete.call_count == 5  # box, label, handle, suggestion, temp_box
        mock_canvas.delete.assert_any_call("box")
        mock_canvas.delete.assert_any_call("label")
        mock_canvas.delete.assert_any_call("handle")
        mock_canvas.delete.assert_any_call("suggestion")
        mock_canvas.delete.assert_any_call("suggestion_label")
        mock_canvas.delete.assert_any_call("temp_box")