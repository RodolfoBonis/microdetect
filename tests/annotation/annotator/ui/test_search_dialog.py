import unittest.mock as mock

import pytest

from microdetect.annotation.annotator.ui.search_dialog import SearchDialog


class TestSearchDialog:

    @pytest.fixture
    def search_dialog(self):
        """Create SearchDialog with test parameters"""
        image_dir = "/path/to/images"
        output_dir = "/path/to/output"
        last_annotated = "/path/to/images/last.jpg"
        return SearchDialog(image_dir, output_dir, last_annotated)

    @mock.patch("glob.glob")
    def test_get_all_images(self, mock_glob, search_dialog):
        """Test getting all images from a directory"""
        # Mock glob to return test files
        test_images = ["/path/to/images/img1.jpg", "/path/to/images/img2.png", "/path/to/images/img3.jpeg"]
        mock_glob.side_effect = lambda path: test_images if ".jpg" in path else []

        images = search_dialog.get_all_images()
        assert images == test_images
        assert mock_glob.call_count == 3  # Called for each extension
