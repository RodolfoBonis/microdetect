import os
import unittest
from unittest.mock import patch, MagicMock

import cv2
import numpy as np

from microdetect.annotation.annotator.suggestions.generator import SuggestionGenerator


class TestSuggestionGenerator(unittest.TestCase):
    def setUp(self):
        self.classes = ["0-Levedura", "1-Fungo", "2-Microalga"]
        self.generator = SuggestionGenerator(self.classes, yolo_model_path=None)

        # Create test image
        self.test_img = np.ones((300, 300, 3), dtype=np.uint8) * 128
        # Add some "cells" to the test image
        cv2.circle(self.test_img, (100, 100), 20, (200, 100, 100), -1)
        cv2.ellipse(self.test_img, (200, 150), (30, 15), 0, 0, 360, (100, 200, 100), -1)
        cv2.rectangle(self.test_img, (50, 200), (100, 250), (100, 100, 200), -1)

        self.test_img_path = "test_microorganisms.png"
        cv2.imwrite(self.test_img_path, self.test_img)

    def tearDown(self):
        if os.path.exists(self.test_img_path):
            os.remove(self.test_img_path)

    def test_initialization_no_model(self):
        generator = SuggestionGenerator(self.classes)
        self.assertIsNone(generator.model)
        self.assertTrue(generator.use_cv_fallback)

    @patch("microdetect.annotation.annotator.suggestions.generator.YOLO")
    def test_initialization_with_model(self, mock_yolo):
        with patch("os.path.exists", return_value=True):
            mock_model = MagicMock()
            mock_yolo.return_value = mock_model
            generator = SuggestionGenerator(self.classes, "dummy_model.pt")
            self.assertEqual(generator.model, mock_model)

    @patch("microdetect.annotation.annotator.suggestions.generator.SuggestionGenerator._detect_with_yolo")
    def test_generate_suggestions_with_yolo(self, mock_detect):
        # Setup mock YOLO detections
        expected_boxes = [("0", 10, 10, 50, 50), ("1", 100, 100, 150, 150)]
        mock_detect.return_value = expected_boxes

        # Mock the model presence
        self.generator.model = MagicMock()

        # Test
        results = self.generator.generate_suggestions(self.test_img_path)
        self.assertEqual(results, expected_boxes)
        mock_detect.assert_called_once()

    @patch("microdetect.annotation.annotator.suggestions.generator.SuggestionGenerator._detect_with_yolo")
    @patch("microdetect.annotation.annotator.suggestions.generator.SuggestionGenerator._detect_with_cv")
    def test_yolo_fallback_to_cv(self, mock_cv, mock_yolo):
        # Setup mock returns
        mock_yolo.return_value = []  # YOLO fails to detect anything
        expected_boxes = [("0", 10, 10, 50, 50), ("1", 100, 100, 150, 150)]
        mock_cv.return_value = expected_boxes

        # Mock the model presence
        self.generator.model = MagicMock()

        # Test
        results = self.generator.generate_suggestions(self.test_img_path)
        self.assertEqual(results, expected_boxes)
        mock_yolo.assert_called_once()
        mock_cv.assert_called_once()

    @patch("microdetect.annotation.annotator.suggestions.generator.SuggestionGenerator._detect_with_cv")
    def test_generate_suggestions_cv_only(self, mock_cv):
        # Setup mock CV detections
        expected_boxes = [("0", 10, 10, 50, 50), ("1", 100, 100, 150, 150)]
        mock_cv.return_value = expected_boxes

        # Ensure no model
        self.generator.model = None

        # Test
        results = self.generator.generate_suggestions(self.test_img_path)
        self.assertEqual(results, expected_boxes)
        mock_cv.assert_called_once()

    def test_toggle_cv_fallback(self):
        self.generator.toggle_cv_fallback(False)
        self.assertFalse(self.generator.use_cv_fallback)

        self.generator.toggle_cv_fallback(True)
        self.assertTrue(self.generator.use_cv_fallback)

    def test_set_model_path(self):
        with patch(
                "microdetect.annotation.annotator.suggestions.generator.SuggestionGenerator._load_model") as mock_load:
            mock_load.return_value = True
            result = self.generator.set_model_path("new_model.pt")
            self.assertEqual(self.generator.yolo_model_path, "new_model.pt")
            self.assertTrue(result)
            mock_load.assert_called_once()

    @patch("microdetect.annotation.annotator.suggestions.generator.cv2.imread")
    def test_generate_suggestions_image_load_failure(self, mock_imread):
        mock_imread.return_value = None
        results = self.generator.generate_suggestions("nonexistent.jpg")
        self.assertEqual(results, [])

    @patch("microdetect.annotation.annotator.suggestions.generator.cv2.imread")
    @patch("microdetect.annotation.annotator.suggestions.generator.SuggestionGenerator._detect_with_yolo")
    @patch("microdetect.annotation.annotator.suggestions.generator.SuggestionGenerator._detect_with_cv")
    @patch("random.randint")
    @patch("random.choice")
    def test_fallback_to_random_suggestions(self, mock_choice, mock_randint, mock_cv, mock_yolo, mock_imread):
        # Both YOLO and CV detection methods fail
        mock_yolo.return_value = []
        mock_cv.return_value = []
        mock_imread.return_value = self.test_img

        # Mock random values
        mock_randint.side_effect = [3, 30, 30, 50, 50, 30, 30, 50, 50, 30, 30, 50,
                                    50]  # Number of suggestions, dimensions
        mock_choice.side_effect = ["0", "1", "2"]

        # Mock model presence
        self.generator.model = MagicMock()

        # Test
        results = self.generator.generate_suggestions(self.test_img_path)

        # Should have 3 random suggestions
        self.assertEqual(len(results), 3)
        mock_yolo.assert_called_once()
        mock_cv.assert_called_once()
        self.assertEqual(mock_choice.call_count, 3)

    def test_map_yolo_class_to_annotator(self):
        # Test exact match
        self.assertEqual(self.generator._map_yolo_class_to_annotator("Levedura"), "0")
        self.assertEqual(self.generator._map_yolo_class_to_annotator("Fungo"), "1")

        # Test substring match
        self.assertEqual(self.generator._map_yolo_class_to_annotator("BudYeast"), "0")

        # Test keywords
        self.assertEqual(self.generator._map_yolo_class_to_annotator("Round yeast"), "0")
        self.assertEqual(self.generator._map_yolo_class_to_annotator("Long fungi"), "1")
        self.assertEqual(self.generator._map_yolo_class_to_annotator("Green algae"), "2")

        # Test no match - should return first class
        self.assertEqual(self.generator._map_yolo_class_to_annotator("Unknown"), "0")

    @patch("microdetect.annotation.annotator.suggestions.generator.logger")
    def test_emergency_detection(self, mock_logger):
        # Testing the emergency fallback detection with real image processing
        results = self.generator._emergency_detection(self.test_img)

        # Should detect at least one object
        self.assertGreater(len(results), 0)

        # Each result should have proper format
        for result in results:
            self.assertEqual(len(result), 5)
            class_id, x1, y1, x2, y2 = result
            self.assertIn(class_id, ["0", "1", "2"])
            self.assertIsInstance(x1, int)
            self.assertIsInstance(y1, int)
            self.assertIsInstance(x2, int)
            self.assertIsInstance(y2, int)
            self.assertGreater(x2, x1)
            self.assertGreater(y2, y1)


if __name__ == "__main__":
    unittest.main()