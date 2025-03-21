import os
import unittest
from unittest.mock import MagicMock, patch

import cv2
import numpy as np

from microdetect.annotation.annotator.image.loader import ImageLoader


class TestImageLoader(unittest.TestCase):
    def setUp(self):
        self.loader = ImageLoader()
        # Create test image
        self.test_img = np.ones((100, 100, 3), dtype=np.uint8) * 128
        self.test_img_path = "test_image.png"
        cv2.imwrite(self.test_img_path, self.test_img)

        # Create a mock for the PhotoImage class
        self.pil_image_mock_patcher = patch("PIL.ImageTk.PhotoImage")
        self.mock_photo_image = self.pil_image_mock_patcher.start()
        self.mock_photo_image.return_value = MagicMock()

    def tearDown(self):
        if os.path.exists(self.test_img_path):
            os.remove(self.test_img_path)
        self.pil_image_mock_patcher.stop()

    def test_load_image_success(self):
        img, w, h = self.loader.load_image(self.test_img_path)
        self.assertIsNotNone(img)
        self.assertEqual(w, 100)
        self.assertEqual(h, 100)
        self.assertEqual(img.shape, (100, 100, 3))

    def test_load_image_failure(self):
        img, w, h = self.loader.load_image("nonexistent_image.jpg")
        self.assertIsNone(img)
        self.assertEqual(w, 0)
        self.assertEqual(h, 0)

    def test_resize_for_display_smaller(self):
        # Test when image is already smaller than limits
        img_small = np.ones((50, 50, 3), dtype=np.uint8)
        resized, scale = self.loader.resize_for_display(img_small, 800, 600)
        self.assertEqual(resized.shape, (50, 50, 3))
        self.assertEqual(scale, 1.0)

    def test_resize_for_display_larger(self):
        # Test when image is larger than limits
        img_large = np.ones((1000, 1000, 3), dtype=np.uint8)
        resized, scale = self.loader.resize_for_display(img_large, 800, 600)
        self.assertEqual(resized.shape[0], 600)
        self.assertEqual(resized.shape[1], 600)
        self.assertEqual(scale, 0.6)

    def test_create_tkinter_image(self):
        # Test creating Tkinter image
        tk_img = self.loader.create_tkinter_image(self.test_img)
        self.assertIn("main", self.loader.image_references)
        self.assertEqual(self.loader.current_img_tk, tk_img)

    def test_create_tkinter_image_replace(self):
        # Test replacing existing reference
        first_img = self.loader.create_tkinter_image(self.test_img, "test")
        second_img = self.loader.create_tkinter_image(self.test_img, "test")
        self.assertEqual(len(self.loader.image_references), 1)
        self.assertEqual(self.loader.image_references["test"], second_img)

    @patch("cv2.resize")
    @patch("PIL.Image.fromarray")
    def test_redraw_with_zoom(self, mock_fromarray, mock_resize):
        canvas = MagicMock()
        mock_resize.return_value = self.test_img
        mock_pil_img = MagicMock()
        mock_fromarray.return_value = mock_pil_img

        # Ensure mocking is correct
        self.mock_photo_image.return_value = MagicMock()

        result = self.loader.redraw_with_zoom(self.test_img, canvas, 1.5, 100, 100, 1.0)

        self.assertTrue(result)
        mock_resize.assert_called_once_with(self.test_img, (150, 150))
        canvas.delete.assert_called_once_with("background")
        canvas.create_image.assert_called_once()
        canvas.config.assert_called_once()

    def test_redraw_with_zoom_exception(self):
        canvas = MagicMock()
        canvas.create_image.side_effect = Exception("Test exception")

        result = self.loader.redraw_with_zoom(self.test_img, canvas, 1.5, 100, 100, 1.0)

        self.assertFalse(result)

    def test_cleanup_references(self):
        # Add multiple references
        self.loader.create_tkinter_image(self.test_img, "ref1")
        self.loader.create_tkinter_image(self.test_img, "ref2")
        self.loader.create_tkinter_image(self.test_img, "ref3")

        # Keep current reference
        current_ref = self.loader.current_img_tk

        # Clean up
        self.loader.cleanup_references()

        # Should keep only current reference
        self.assertEqual(len(self.loader.image_references), 1)

        # Current image should still be in references
        self.assertIn(current_ref, self.loader.image_references.values())


if __name__ == "__main__":
    unittest.main()
