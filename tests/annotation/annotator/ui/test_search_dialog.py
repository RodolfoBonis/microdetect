import unittest.mock as mock

import pytest

from microdetect.annotation.annotator.ui.search_dialog import SearchDialog


class TestSearchDialog:

    @pytest.fixture
    def search_dialog(self):
        """Create SearchDialog with test parameters"""
        image_dir = '/path/to/images'
        output_dir = '/path/to/output'
        last_annotated = '/path/to/images/last.jpg'
        return SearchDialog(image_dir, output_dir, last_annotated)

    @mock.patch('glob.glob')
    def test_get_all_images(self, mock_glob, search_dialog):
        """Test getting all images from a directory"""
        # Mock glob to return test files
        test_images = [
            '/path/to/images/img1.jpg',
            '/path/to/images/img2.png',
            '/path/to/images/img3.jpeg'
        ]
        mock_glob.side_effect = lambda path: test_images if '.jpg' in path else []

        images = search_dialog.get_all_images()
        assert images == test_images
        assert mock_glob.call_count == 3  # Called for each extension

    @mock.patch('microdetect.annotation.annotator.ui.base.create_secure_dialog')
    @mock.patch('microdetect.annotation.annotator.ui.search_dialog.SearchDialog.get_all_images')
    @mock.patch('os.path.exists')
    def test_show_with_no_images(self, mock_exists, mock_get_images, mock_create_dialog, search_dialog):
        """Test showing dialog with no images"""
        # Setup mocks
        mock_get_images.return_value = []
        mock_dialog = mock.MagicMock()
        mock_create_dialog.return_value = mock_dialog

        # Call show method
        result = search_dialog.show()

        # Verify result
        assert result == ([], 0)

    @mock.patch('microdetect.annotation.annotator.ui.base.create_secure_dialog')
    @mock.patch('microdetect.annotation.annotator.ui.search_dialog.SearchDialog.get_all_images')
    @mock.patch('os.path.exists')
    @mock.patch('PIL.Image.open')
    def test_show_with_image_selection(self, mock_pil_open, mock_exists, mock_get_images,
                                       mock_create_dialog, search_dialog):
        """Test showing dialog and selecting an image"""
        # Setup mocks for a more complex test scenario
        mock_get_images.return_value = ['/path/to/images/img1.jpg', '/path/to/images/img2.jpg']
        mock_dialog = mock.MagicMock()
        mock_create_dialog.return_value = mock_dialog

        # Mock dialog behavior for selection
        def fake_wait_window():
            # Simulate user selecting an image and clicking annotate
            search_dialog.result_images = mock_get_images.return_value
            search_dialog.result_mode = 3
            search_dialog.start_index = 0

        mock_dialog.wait_window.side_effect = fake_wait_window
        mock_exists.return_value = True

        # Mock PIL image
        mock_img = mock.MagicMock()
        mock_img.size = (500, 300)
        mock_pil_open.return_value = mock_img

        # Call show method
        result_images, result_mode = search_dialog.show()

        # Verify results
        assert result_images == mock_get_images.return_value
        assert result_mode == 3