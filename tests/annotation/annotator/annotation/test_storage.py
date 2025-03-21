import os
import tempfile
import unittest.mock as mock

import pytest

from microdetect.annotation.annotator.annotation.storage import AnnotationStorage


class TestAnnotationStorage:

    @pytest.fixture
    def storage(self):
        """Create an AnnotationStorage for testing"""
        return AnnotationStorage(progress_file=".test_progress.json")

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test files"""
        with tempfile.TemporaryDirectory() as temp:
            yield temp

    def test_initialization(self, storage):
        """Test initialization of AnnotationStorage"""
        assert storage.progress_file == ".test_progress.json"

    def test_save_annotations(self, storage, temp_dir):
        """Test saving annotations to a file"""
        # Create test data
        bounding_boxes = [
            ("0", 40, 40, 60, 60),  # center=(50,50), width=20, height=20
            ("1", 65, 65, 75, 75)  # center=(70,70), width=10, height=10
        ]
        original_w, original_h = 100, 100
        base_name = "test_image"

        # Save annotations
        annotation_path = storage.save_annotations(
            bounding_boxes, temp_dir, base_name, original_w, original_h
        )

        # Verify file creation
        assert os.path.exists(annotation_path)

        # Verify content
        with open(annotation_path, "r") as f:
            lines = f.readlines()

        assert len(lines) == 2

        # Verify YOLO format conversion (class_id, center_x, center_y, width, height)
        # First box: class="0", center=(0.5,0.5), size=(0.2,0.2)
        parts = lines[0].strip().split()
        assert parts[0] == "0"  # class_id
        assert float(parts[1]) == pytest.approx(0.5)  # center_x
        assert float(parts[2]) == pytest.approx(0.5)  # center_y
        assert float(parts[3]) == pytest.approx(0.2)  # width
        assert float(parts[4]) == pytest.approx(0.2)  # height

        # Second box: class="1", center=(0.7,0.7), size=(0.1,0.1)
        parts = lines[1].strip().split()
        assert parts[0] == "1"  # class_id
        assert float(parts[1]) == pytest.approx(0.7)  # center_x
        assert float(parts[2]) == pytest.approx(0.7)  # center_y
        assert float(parts[3]) == pytest.approx(0.1)  # width
        assert float(parts[4]) == pytest.approx(0.1)  # height

    def test_load_annotations(self, storage, temp_dir):
        """Test loading annotations from a file"""
        # Create test annotation file in YOLO format
        annotation_content = "0 0.5 0.5 0.2 0.2\n1 0.7 0.7 0.1 0.1"
        annotation_path = os.path.join(temp_dir, "test_image.txt")
        with open(annotation_path, "w") as f:
            f.write(annotation_content)

        # Load annotations
        original_w, original_h = 100, 100
        boxes = storage.load_annotations(annotation_path, original_w, original_h)

        # Verify results
        assert len(boxes) == 2

        # First box: class="0", center=(0.5,0.5), size=(0.2,0.2) -> x1=40, y1=40, x2=60, y2=60
        assert boxes[0][0] == "0"  # class_id
        assert boxes[0][1] == 40  # x1
        assert boxes[0][2] == 40  # y1
        assert boxes[0][3] == 60  # x2
        assert boxes[0][4] == 60  # y2

        # Second box: class="1", center=(0.7,0.7), size=(0.1,0.1) -> x1=65, y1=65, x2=75, y2=75
        assert boxes[1][0] == "1"  # class_id
        assert boxes[1][1] == 65  # x1
        assert boxes[1][2] == 65  # y1
        assert boxes[1][3] == 75  # x2
        assert boxes[1][4] == 75  # y2

        # Test with non-existent file
        boxes = storage.load_annotations("non_existent_file.txt", 100, 100)
        assert boxes == []

    @mock.patch('json.dump')
    def test_save_progress(self, mock_json_dump, storage, temp_dir):
        """Test saving progress information"""
        current_image = "/path/to/image.jpg"

        # Test success case
        result = storage.save_progress(temp_dir, current_image)
        assert result is True

        # Verify json.dump was called
        mock_json_dump.assert_called_once()
        args, _ = mock_json_dump.call_args
        data = args[0]

        # Check data structure
        assert "last_annotated" in data
        assert data["last_annotated"] == current_image
        assert "timestamp" in data

        # Test failure case
        mock_json_dump.side_effect = Exception("Test error")
        result = storage.save_progress(temp_dir, current_image)
        assert result is False

    @mock.patch('json.load')
    @mock.patch('os.path.exists')
    def test_load_progress(self, mock_exists, mock_json_load, storage, temp_dir):
        """Test loading progress information"""
        # Setup mocks
        mock_exists.return_value = True
        mock_json_load.return_value = {
            "last_annotated": "/path/to/image.jpg",
            "timestamp": "2023-01-01T12:00:00"
        }

        # Test successful load
        result = storage.load_progress(temp_dir)
        assert result == "/path/to/image.jpg"

        # Test when file doesn't exist
        mock_exists.return_value = False
        result = storage.load_progress(temp_dir)
        assert result is None

        # Test when file exists but image path doesn't
        mock_exists.side_effect = [True, False]  # First for progress file, second for image path
        mock_json_load.return_value = {
            "last_annotated": "non_existent_image.jpg",
            "timestamp": "2023-01-01T12:00:00"
        }
        result = storage.load_progress(temp_dir)
        assert result is None

        # Test with loading error
        mock_exists.side_effect = None
        mock_exists.return_value = True
        mock_json_load.side_effect = Exception("Test error")
        result = storage.load_progress(temp_dir)
        assert result is None

    @mock.patch('glob.glob')
    def test_count_annotations_by_class(self, mock_glob, storage, temp_dir):
        """Test counting annotations by class"""
        # Create mock annotation files
        mock_glob.return_value = [
            os.path.join(temp_dir, "img1.txt"),
            os.path.join(temp_dir, "img2.txt"),
            os.path.join(temp_dir, ".test_progress.json")  # Should be skipped
        ]

        # Create mock open to return annotation content
        with mock.patch('builtins.open',
                        mock.mock_open(read_data="0 0.5 0.5 0.2 0.2\n1 0.7 0.7 0.1 0.1\n0 0.3 0.3 0.1 0.1")):
            # Test with valid classes
            classes = ["0-class1", "1-class2", "2-class3"]
            class_counts, total_boxes = storage.count_annotations_by_class(temp_dir, classes)

            # Should find 2 boxes of class 0 and 1 box of class 1
            assert class_counts["0"] == 2
            assert class_counts["1"] == 1
            assert class_counts["2"] == 0
            assert total_boxes == 3