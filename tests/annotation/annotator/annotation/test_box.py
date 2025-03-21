import pytest

from microdetect.annotation.annotator.annotation.box import BoundingBoxManager
from microdetect.annotation.annotator.utils.constants import (
    HANDLE_NONE, HANDLE_NW, HANDLE_NE, HANDLE_SE, HANDLE_SW,
    HANDLE_N, HANDLE_E, HANDLE_S, HANDLE_W
)


class TestBoundingBoxManager:

    @pytest.fixture
    def box_manager(self):
        """Create a BoundingBoxManager for testing"""
        return BoundingBoxManager()

    def test_initialization(self, box_manager):
        """Test initialization of BoundingBoxManager"""
        assert box_manager.boxes == []
        assert box_manager.selected_idx is None
        assert box_manager.resize_handle == HANDLE_NONE
        assert box_manager.handle_size == 6
        assert box_manager.original_box_state is None

    def test_add_box(self, box_manager):
        """Test adding a new bounding box"""
        # Add first box
        idx = box_manager.add_box("0", 10, 10, 50, 50)
        assert idx == 0
        assert box_manager.get_box_count() == 1
        assert box_manager.boxes[0] == ("0", 10, 10, 50, 50)

        # Add another box
        idx = box_manager.add_box("1", 20, 20, 60, 60)
        assert idx == 1
        assert box_manager.get_box_count() == 2
        assert box_manager.boxes[1] == ("1", 20, 20, 60, 60)

    def test_update_box(self, box_manager):
        """Test updating an existing box"""
        # Add test box
        box_manager.add_box("0", 10, 10, 50, 50)

        # Update with all new values
        result = box_manager.update_box(0, "1", 20, 20, 60, 60)
        assert result is True
        assert box_manager.boxes[0] == ("1", 20, 20, 60, 60)

        # Update only class_id
        result = box_manager.update_box(0, "2")
        assert result is True
        assert box_manager.boxes[0] == ("2", 20, 20, 60, 60)

        # Update only coordinates
        result = box_manager.update_box(0, None, 25, 25, 65, 65)
        assert result is True
        assert box_manager.boxes[0] == ("2", 25, 25, 65, 65)

        # Test updating non-existent box
        result = box_manager.update_box(99)
        assert result is False

        # Test coordinate swapping (x1 > x2 or y1 > y2)
        result = box_manager.update_box(0, None, 70, 70, 30, 30)
        assert result is True
        # Should swap coordinates to ensure x1 < x2, y1 < y2
        assert box_manager.boxes[0] == ("2", 30, 30, 70, 70)

    def test_remove_box(self, box_manager):
        """Test removing a box"""
        # Add test boxes
        box_manager.add_box("0", 10, 10, 50, 50)
        box_manager.add_box("1", 20, 20, 60, 60)
        box_manager.add_box("2", 30, 30, 70, 70)

        # Test removing a specific box
        removed = box_manager.remove_box(1)
        assert removed == ("1", 20, 20, 60, 60)
        assert box_manager.get_box_count() == 2
        assert box_manager.boxes[0] == ("0", 10, 10, 50, 50)
        assert box_manager.boxes[1] == ("2", 30, 30, 70, 70)

        # Test removing an invalid index
        removed = box_manager.remove_box(99)
        assert removed is None
        assert box_manager.get_box_count() == 2

        # Test remove_last
        removed = box_manager.remove_last()
        assert removed == ("2", 30, 30, 70, 70)
        assert box_manager.get_box_count() == 1

        # Test remove_last with empty list
        box_manager.clear_all()
        removed = box_manager.remove_last()
        assert removed is None

    def test_get_box(self, box_manager):
        """Test getting a box by index"""
        # Add test box
        box_manager.add_box("0", 10, 10, 50, 50)

        # Get box with valid index
        box = box_manager.get_box(0)
        assert box == ("0", 10, 10, 50, 50)

        # Get box with invalid index
        box = box_manager.get_box(99)
        assert box is None

    def test_select_box(self, box_manager):
        """Test selecting a box"""
        # Add test boxes
        box_manager.add_box("0", 10, 10, 50, 50)
        box_manager.add_box("1", 20, 20, 60, 60)

        # Select a valid box
        result = box_manager.select_box(1)
        assert result is True
        assert box_manager.selected_idx == 1

        # Select an invalid box
        result = box_manager.select_box(99)
        assert result is False
        assert box_manager.selected_idx == 1  # Doesn't change

        # Deselect by passing None
        result = box_manager.select_box(None)
        assert result is True
        assert box_manager.selected_idx is None

    def test_clear_all(self, box_manager):
        """Test clearing all boxes"""
        # Add test boxes
        box_manager.add_box("0", 10, 10, 50, 50)
        box_manager.add_box("1", 20, 20, 60, 60)
        box_manager.select_box(1)

        # Clear all boxes
        count = box_manager.clear_all()
        assert count == 2
        assert box_manager.get_box_count() == 0
        assert box_manager.selected_idx is None
        assert box_manager.boxes == []

    def test_detect_resize_handle(self, box_manager):
        """Test detection of resize handles"""
        # Add test box
        box_manager.add_box("0", 100, 100, 200, 200)

        # Calculate expected handle positions for a box at 100,100,200,200
        # with display_scale=1.0 and scale_factor=1.0
        # NW corner
        assert box_manager.detect_resize_handle(100, 100, 0, 1.0, 1.0) == HANDLE_NW
        # NE corner
        assert box_manager.detect_resize_handle(200, 100, 0, 1.0, 1.0) == HANDLE_NE
        # SE corner
        assert box_manager.detect_resize_handle(200, 200, 0, 1.0, 1.0) == HANDLE_SE
        # SW corner
        assert box_manager.detect_resize_handle(100, 200, 0, 1.0, 1.0) == HANDLE_SW

        # Middle of edges
        # N edge
        assert box_manager.detect_resize_handle(150, 100, 0, 1.0, 1.0) == HANDLE_N
        # E edge
        assert box_manager.detect_resize_handle(200, 150, 0, 1.0, 1.0) == HANDLE_E
        # S edge
        assert box_manager.detect_resize_handle(150, 200, 0, 1.0, 1.0) == HANDLE_S
        # W edge
        assert box_manager.detect_resize_handle(100, 150, 0, 1.0, 1.0) == HANDLE_W

        # No handle (middle of box)
        assert box_manager.detect_resize_handle(150, 150, 0, 1.0, 1.0) == HANDLE_NONE

        # Test with invalid box index
        assert box_manager.detect_resize_handle(100, 100, 99, 1.0, 1.0) == HANDLE_NONE

        # Test with display_scale and scale_factor
        # For a 2.0 scale, the box would be at 200,200,400,400 on canvas
        assert box_manager.detect_resize_handle(200, 200, 0, 1.0, 2.0) == HANDLE_NW
        assert box_manager.detect_resize_handle(400, 400, 0, 1.0, 2.0) == HANDLE_SE

    def test_find_box_at_position(self, box_manager):
        """Test finding a box at a specific position"""
        # Add test boxes with non-overlapping positions
        box_manager.add_box("0", 10, 10, 50, 50)  # Box 0: (10,10) to (50,50)
        box_manager.add_box("1", 100, 100, 200, 200)  # Box 1: (100,100) to (200,200)

        # Test position inside first box
        found_idx = box_manager.find_box_at_position(30, 30, 1.0, 1.0)
        assert found_idx == 0

        # Test position inside second box
        found_idx = box_manager.find_box_at_position(150, 150, 1.0, 1.0)
        assert found_idx == 1

        # Test position outside any box
        found_idx = box_manager.find_box_at_position(75, 75, 1.0, 1.0)
        assert found_idx is None

        # Test with display_scale and scale_factor
        # With scale 2.0, Box 0 would be at (20,20) to (100,100) on canvas
        found_idx = box_manager.find_box_at_position(60, 60, 1.0, 2.0)
        assert found_idx == 0

    def test_get_box_count(self, box_manager):
        """Test getting the number of boxes"""
        assert box_manager.get_box_count() == 0

        box_manager.add_box("0", 10, 10, 50, 50)
        assert box_manager.get_box_count() == 1

        box_manager.add_box("1", 20, 20, 60, 60)
        assert box_manager.get_box_count() == 2

        box_manager.remove_box(0)
        assert box_manager.get_box_count() == 1

    def test_get_all_boxes(self, box_manager):
        """Test getting all boxes"""
        # Initial state - empty list
        assert box_manager.get_all_boxes() == []

        # Add boxes
        box_manager.add_box("0", 10, 10, 50, 50)
        box_manager.add_box("1", 20, 20, 60, 60)

        # Check all boxes
        all_boxes = box_manager.get_all_boxes()
        assert len(all_boxes) == 2
        assert all_boxes[0] == ("0", 10, 10, 50, 50)
        assert all_boxes[1] == ("1", 20, 20, 60, 60)

        # Verify that get_all_boxes returns a copy
        all_boxes[0] = ("modified", 0, 0, 0, 0)
        assert box_manager.boxes[0] == ("0", 10, 10, 50, 50)  # Original unchanged