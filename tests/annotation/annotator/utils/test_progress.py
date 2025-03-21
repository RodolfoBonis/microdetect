import json
import os
import unittest.mock as mock

import pytest

from microdetect.annotation.annotator.utils.progress import ProgressManager


class TestProgressManager:

    @pytest.fixture
    def progress_manager(self):
        """Create a ProgressManager with test parameters"""
        return ProgressManager(progress_file=".test_progress.json")

    def test_initialization(self, progress_manager):
        """Test progress manager initialization"""
        assert progress_manager.progress_file == ".test_progress.json"

    @mock.patch('builtins.open', new_callable=mock.mock_open)
    @mock.patch('json.dump')
    def test_save_progress(self, mock_json_dump, mock_open, progress_manager):
        """Test saving progress"""
        # Call save_progress
        result = progress_manager.save_progress(
            '/output', '/path/to/image.jpg', {'custom': 'data'}
        )

        # Verify file operations
        mock_open.assert_called_once()
        mock_json_dump.assert_called_once()

        # Check arguments to json.dump
        args, kwargs = mock_json_dump.call_args
        data = args[0]
        assert data['last_annotated'] == '/path/to/image.jpg'
        assert 'timestamp' in data
        assert data['custom'] == 'data'

        # Verify result
        assert result is True

    @mock.patch('os.path.exists')
    @mock.patch('builtins.open', new_callable=mock.mock_open)
    @mock.patch('json.dump')
    def test_save_progress_with_existing_data(self, mock_json_dump, mock_open,
                                              mock_exists, progress_manager):
        """Test saving progress with existing data"""
        # Setup mocks
        mock_exists.return_value = True
        mock_open.return_value.__enter__.return_value.read.return_value = json.dumps({
            'last_annotated': '/old/path.jpg',
            'annotation_history': [
                {'image': '/old/path.jpg', 'timestamp': '2023-01-01T12:00:00'}
            ]
        })

        # Call save_progress
        result = progress_manager.save_progress('/output', '/path/to/image.jpg')

        # Verify result
        assert result is True

        # Check arguments to json.dump
        args, kwargs = mock_json_dump.call_args
        data = args[0]
        assert data['last_annotated'] == '/path/to/image.jpg'
        assert len(data['annotation_history']) == 2  # Old + new entry

    @mock.patch('os.path.exists')
    @mock.patch('builtins.open', new_callable=mock.mock_open)
    @mock.patch('json.load')
    def test_load_progress(self, mock_json_load, mock_open, mock_exists, progress_manager):
        """Test loading progress"""
        # Setup mocks
        mock_exists.return_value = True
        test_data = {'last_annotated': '/path/to/image.jpg'}
        mock_json_load.return_value = test_data

        # Call load_progress
        result = progress_manager.load_progress('/output')

        # Verify result
        assert result == test_data
        mock_open.assert_called_once_with(os.path.join('/output', '.test_progress.json'), 'r')

    @mock.patch('os.path.exists')
    def test_load_progress_no_file(self, mock_exists, progress_manager):
        """Test loading progress when file doesn't exist"""
        # Setup mocks
        mock_exists.return_value = False

        # Call load_progress
        result = progress_manager.load_progress('/output')

        # Verify result
        assert result is None

    @mock.patch('microdetect.annotation.annotator.utils.progress.ProgressManager.load_progress')
    @mock.patch('os.path.exists')
    def test_get_last_annotated_image(self, mock_exists, mock_load_progress, progress_manager):
        """Test getting the last annotated image"""
        # Setup mocks
        mock_load_progress.return_value = {'last_annotated': '/path/to/image.jpg'}
        mock_exists.return_value = True

        # Call get_last_annotated_image
        result = progress_manager.get_last_annotated_image('/output')

        # Verify result
        assert result == '/path/to/image.jpg'

    @mock.patch('glob.glob')
    @mock.patch('os.path.exists')
    def test_calculate_progress(self, mock_exists, mock_glob, progress_manager):
        """Test calculating annotation progress"""
        # Setup mocks
        mock_glob.side_effect = lambda path: [
            '/images/img1.jpg',
            '/images/img2.jpg',
            '/images/img3.jpg',
            '/images/img4.jpg'
        ] if '.jpg' in path else []

        # Mock only 2 of 4 images have annotations
        def exists_check(path):
            return 'img1.txt' in path or 'img2.txt' in path

        mock_exists.side_effect = exists_check

        # Call calculate_progress
        annotated, total, percentage = progress_manager.calculate_progress('/images', '/output')

        # Verify results
        assert annotated == 2
        assert total == 4
        assert percentage == 50.0