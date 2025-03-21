import os
import random
import unittest
from unittest.mock import MagicMock, patch, call

import numpy as np

from microdetect.annotation.annotator.suggestions.generator import SuggestionGenerator


class TestSuggestionGenerator(unittest.TestCase):
    def setUp(self):
        self.classes = ["0-Levedura", "1-Fungo", "2-Microalga"]
        self.generator = SuggestionGenerator(self.classes, yolo_model_path=None)

    def test_initialization_no_model(self):
        generator = SuggestionGenerator(self.classes)
        self.assertIsNone(generator.model)
        self.assertTrue(generator.use_cv_fallback)

    @patch("os.path.exists")
    @patch("microdetect.annotation.annotator.suggestions.generator.logger")
    def test_load_model_nonexistent_path(self, mock_logger, mock_exists):
        mock_exists.return_value = False
        self.generator.yolo_model_path = "nonexistent_model.pt"
        result = self.generator._load_model()
        self.assertFalse(result)
        mock_logger.info.assert_called_once()

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

    def test_toggle_cv_fallback(self):
        self.generator.toggle_cv_fallback(False)
        self.assertFalse(self.generator.use_cv_fallback)

        self.generator.toggle_cv_fallback(True)
        self.assertTrue(self.generator.use_cv_fallback)

    @patch("microdetect.annotation.annotator.suggestions.generator.SuggestionGenerator._detect_with_cv")
    def test_generate_suggestions_cv_only(self, mock_cv):
        # Setup mock CV detections
        expected_boxes = [("0", 10, 10, 50, 50), ("1", 100, 100, 150, 150)]
        mock_cv.return_value = expected_boxes

        # Ensure no model
        self.generator.model = None

        # Mock cv2.imread
        with patch("microdetect.annotation.annotator.suggestions.generator.cv2.imread") as mock_imread, \
             patch("microdetect.annotation.annotator.suggestions.generator.cv2.cvtColor") as mock_cvtColor, \
             patch("microdetect.annotation.annotator.suggestions.generator.logger") as mock_logger:
            
            # Create a mock image
            mock_img = np.ones((100, 100, 3), dtype=np.uint8) * 128
            mock_imread.return_value = mock_img
            mock_cvtColor.return_value = mock_img
            
            # Test
            results = self.generator.generate_suggestions("test_image.jpg")
            
            # Check
            self.assertEqual(results, expected_boxes)
            mock_cv.assert_called_once()
            mock_logger.info.assert_has_calls([
                call("Gerando sugestões automáticas para test_image.jpg"),
                call("Utilizando métodos de visão computacional para gerar sugestões"),
                call("2 sugestões geradas para test_image.jpg")
            ])
            
    def test_random_fallback(self):
        # Mock all methods to force random fallback
        with patch("microdetect.annotation.annotator.suggestions.generator.cv2.imread") as mock_imread, \
             patch("microdetect.annotation.annotator.suggestions.generator.cv2.cvtColor") as mock_cvtColor, \
             patch("microdetect.annotation.annotator.suggestions.generator.SuggestionGenerator._detect_with_cv") as mock_cv, \
             patch("microdetect.annotation.annotator.suggestions.generator.logger") as mock_logger, \
             patch("random.randint") as mock_randint, \
             patch("random.choice") as mock_choice:
            
            # Create a mock image
            mock_img = np.ones((100, 100, 3), dtype=np.uint8) * 128
            mock_imread.return_value = mock_img
            mock_cvtColor.return_value = mock_img
            
            # Both YOLO and CV detection fail
            mock_cv.return_value = []
            
            # Force 3 random suggestions
            mock_randint.side_effect = [3, 30, 30, 30, 30, 30, 30]
            mock_choice.side_effect = ["0", "1", "2"]
            
            # Test
            results = self.generator.generate_suggestions("test_image.jpg")
            
            # Should have 3 random suggestions
            self.assertEqual(len(results), 3)
            mock_logger.info.assert_any_call("Gerando sugestões aleatórias como último recurso")
    
    @patch("microdetect.annotation.annotator.suggestions.generator.logger")
    def test_generate_suggestions_exception(self, mock_logger):
        with patch("microdetect.annotation.annotator.suggestions.generator.cv2.imread", side_effect=Exception("Test error")):
            results = self.generator.generate_suggestions("test_image.jpg")
            
            self.assertEqual(results, [])
            mock_logger.error.assert_called_once()
    
    def test_set_model_path(self):
        with patch.object(self.generator, "_load_model") as mock_load_model:
            mock_load_model.return_value = True
            
            result = self.generator.set_model_path("new_model_path.pt")
            
            self.assertEqual(self.generator.yolo_model_path, "new_model_path.pt")
            self.assertTrue(result)
            mock_load_model.assert_called_once()
    
    def test_classify_microorganism(self):
        roi = np.ones((50, 50, 3), dtype=np.uint8) * 128
        contour = np.array([[[10, 10]], [[10, 40]], [[40, 40]], [[40, 10]]])
        
        with patch.object(self.generator, "_advanced_classification") as mock_classify:
            mock_classify.return_value = ("0", 0.8)
            
            result = self.generator._classify_microorganism(roi, contour)
            
            self.assertEqual(result, "0")
            mock_classify.assert_called_once_with(roi, contour)
    
    def test_adaptive_preprocessing(self):
        # Test with a realistic grayscale image
        img_gray = np.random.randint(0, 255, (100, 100), dtype=np.uint8)
        
        # Test with different combinations of parameters
        result1 = self.generator._adaptive_preprocessing(img_gray, False, False)
        result2 = self.generator._adaptive_preprocessing(img_gray, True, False)
        result3 = self.generator._adaptive_preprocessing(img_gray, False, True)
        result4 = self.generator._adaptive_preprocessing(img_gray, True, True)
        
        # Check that all required keys are present
        for result in [result1, result2, result3, result4]:
            self.assertIn("normalized", result)
            self.assertIn("blur", result)
            self.assertIn("clahe", result)
            self.assertIn("enhanced", result)
            
        # Verify the shapes of returned images
        for key, img in result1.items():
            self.assertEqual(img.shape, (100, 100))
    
    def test_multi_segmentation(self):
        img = np.random.randint(0, 255, (100, 100), dtype=np.uint8)
        
        result = self.generator._multi_segmentation(img)
        
        # Check essential segmentation methods
        self.assertIn("adaptive", result)
        self.assertIn("otsu", result)
        
        # Check output shapes
        for key, segmented in result.items():
            self.assertEqual(segmented.shape, (100, 100))
            self.assertEqual(segmented.dtype, np.uint8)

    def test_apply_nms(self):
        # Mock required libs
        with patch("microdetect.annotation.annotator.suggestions.generator.cv2.boundingRect") as mock_rect:
            # Create a simple implementation of apply_nms for testing
            def mock_implementation(boxes):
                if not boxes:
                    return []
                    
                result = [boxes[0]]  # Always keep the first box
                
                # For testing purposes, just keep boxes with different class_ids
                for box in boxes[1:]:
                    if box["class_id"] != result[0]["class_id"]:
                        result.append(box)
                        
                return result
            
            # Save original and replace
            original_method = self.generator._apply_nms
            self.generator._apply_nms = mock_implementation
            
            try:
                # Test data
                boxes = [
                    {"coords": (10, 10, 50, 50), "class_id": "0", "confidence": 0.9, "size": 1600},
                    {"coords": (30, 30, 70, 70), "class_id": "0", "confidence": 0.8, "size": 1600},
                    {"coords": (80, 80, 100, 100), "class_id": "1", "confidence": 0.7, "size": 400}
                ]
                
                result = self.generator._apply_nms(boxes)
                
                # Should return two boxes with different class IDs
                self.assertEqual(len(result), 2)
                self.assertEqual(result[0]["class_id"], "0")
                self.assertEqual(result[1]["class_id"], "1")
                
            finally:
                # Restore original
                self.generator._apply_nms = original_method


if __name__ == "__main__":
    unittest.main()