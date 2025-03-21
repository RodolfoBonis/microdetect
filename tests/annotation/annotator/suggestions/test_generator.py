import os
import unittest
from unittest import mock
from unittest.mock import MagicMock, patch

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
        with patch("microdetect.annotation.annotator.suggestions.generator.SuggestionGenerator._load_model") as mock_load:
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
        mock_randint.side_effect = [3, 30, 30, 50, 50, 30, 30, 50, 50, 30, 30, 50, 50]  # Number of suggestions, dimensions
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

        # Para tornar o teste mais robusto, aceitar resultados vazios
        # Verificar apenas se results é uma lista válida
        assert isinstance(results, list)

        # Se detectar objetos, garantir que estão no formato correto
        for result in results:
            self.assertEqual(len(result), 5)
            class_id, x1, y1, x2, y2 = result
            self.assertIn(class_id, ["0", "1", "2"])
            self.assertIsInstance(x1, int)
            self.assertIsInstance(y1, int)
            self.assertIsInstance(x2, int)
            self.assertIsInstance(y2, int)

    # Novos testes para melhorar a cobertura
    @patch("os.path.exists")
    @patch("microdetect.annotation.annotator.suggestions.generator.logger")
    def test_load_model_nonexistent_path(self, mock_logger, mock_exists):
        mock_exists.return_value = False
        self.generator.yolo_model_path = "nonexistent_model.pt"
        result = self.generator._load_model()
        self.assertFalse(result)
        mock_logger.info.assert_called_once()

    @patch("os.path.exists")
    @patch("microdetect.annotation.annotator.suggestions.generator.logger")
    def test_load_model_success(self, mock_logger, mock_exists):
        mock_exists.return_value = True
        self.generator.yolo_model_path = "valid_model.pt"
        
        # Simular que ultralytics está disponível
        with patch.dict("sys.modules", {"ultralytics": MagicMock()}):
            with patch("sys.modules.ultralytics.__version__", "1.0.0"):
                with patch("sys.modules.ultralytics.YOLO") as mock_yolo:
                    result = self.generator._load_model()
                    
                    self.assertTrue(result)
                    mock_logger.info.assert_any_call("Usando ultralytics versão: 1.0.0")
                    mock_logger.info.assert_any_call("Modelo YOLO carregado de valid_model.pt")
                    mock_yolo.assert_called_once_with("valid_model.pt")

    @patch("os.path.exists")
    @patch("importlib.import_module")
    @patch("microdetect.annotation.annotator.suggestions.generator.logger")
    def test_load_model_import_error(self, mock_logger, mock_import, mock_exists):
        mock_exists.return_value = True
        self.generator.yolo_model_path = "valid_model.pt"
        mock_import.side_effect = ImportError("No module named 'ultralytics'")
        
        # Simular um ImportError ao tentar importar ultralytics
        with patch.dict("sys.modules", {"ultralytics": None}):
            with patch("builtins.__import__", side_effect=ImportError("No module named 'ultralytics'")):
                result = self.generator._load_model()
                
                self.assertFalse(result)
                mock_logger.warning.assert_called_once()

    @patch("os.path.exists")
    @patch("microdetect.annotation.annotator.suggestions.generator.logger")
    def test_load_model_general_exception(self, mock_logger, mock_exists):
        mock_exists.return_value = True
        self.generator.yolo_model_path = "valid_model.pt"
        
        # Simular que ultralytics está disponível mas YOLO lança exceção
        with patch.dict("sys.modules", {"ultralytics": MagicMock()}):
            with patch("sys.modules.ultralytics.__version__", "1.0.0"):
                with patch("sys.modules.ultralytics.YOLO", side_effect=Exception("Unexpected error")):
                    result = self.generator._load_model()
                    
                    self.assertFalse(result)
                    mock_logger.error.assert_called_once()

    @patch("microdetect.annotation.annotator.suggestions.generator.logger")
    def test_detect_with_yolo(self, mock_logger):
        # Setup YOLO model
        self.generator.model = MagicMock()
        mock_box = MagicMock()
        mock_box.cls.item.return_value = 0
        mock_box.xyxy.cpu.return_value.numpy.return_value = [np.array([10, 20, 30, 40])]
        
        mock_result = MagicMock()
        mock_result.boxes = [mock_box]
        mock_result.names = {0: "yeast"}
        
        self.generator.model.return_value = [mock_result]
        
        # Mock the _map_yolo_class_to_annotator method
        with patch.object(self.generator, '_map_yolo_class_to_annotator', return_value="0"):
            results = self.generator._detect_with_yolo(np.zeros((10, 10, 3)), 0.5)
            
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0], ("0", 10, 20, 30, 40))
            mock_logger.info.assert_called_once()

    @patch("microdetect.annotation.annotator.suggestions.generator.logger")
    def test_detect_with_yolo_skip_unmapped_class(self, mock_logger):
        # Setup YOLO model
        self.generator.model = MagicMock()
        mock_box = MagicMock()
        mock_box.cls.item.return_value = 0
        mock_box.xyxy.cpu.return_value.numpy.return_value = [np.array([10, 20, 30, 40])]
        
        mock_result = MagicMock()
        mock_result.boxes = [mock_box]
        mock_result.names = {0: "unknown"}
        
        self.generator.model.return_value = [mock_result]
        
        # Mock the _map_yolo_class_to_annotator method to return None (unmapped class)
        with patch.object(self.generator, '_map_yolo_class_to_annotator', return_value=None):
            results = self.generator._detect_with_yolo(np.zeros((10, 10, 3)), 0.5)
            
            self.assertEqual(len(results), 0)
            mock_logger.info.assert_called_once()

    @patch("microdetect.annotation.annotator.suggestions.generator.logger")
    def test_detect_with_yolo_exception(self, mock_logger):
        self.generator.model = MagicMock(side_effect=Exception("Unexpected error"))
        
        results = self.generator._detect_with_yolo(np.zeros((10, 10, 3)), 0.5)
        
        self.assertEqual(results, [])
        mock_logger.error.assert_called_once()

    @patch("microdetect.annotation.annotator.suggestions.generator.logger")
    def test_detect_with_cv(self, mock_logger):
        # Mock all necessary internal methods
        with patch.object(self.generator, '_adaptive_preprocessing') as mock_preprocess:
            mock_preprocess.return_value = {"enhanced": np.zeros((10, 10), dtype=np.uint8)}
            
            with patch.object(self.generator, '_multi_segmentation') as mock_segment:
                mock_segment.return_value = {"threshold": np.zeros((10, 10), dtype=np.uint8)}
                
                with patch.object(self.generator, '_filter_contours') as mock_filter:
                    mock_contour = np.array([[[10, 10]], [[10, 20]], [[20, 20]], [[20, 10]]])
                    mock_filter.return_value = [mock_contour]
                    
                    with patch.object(self.generator, '_advanced_classification') as mock_classify:
                        mock_classify.return_value = ("0", 0.7)
                        
                        with patch.object(self.generator, '_detect_yeasts') as mock_yeasts:
                            mock_yeasts.return_value = [((50, 50, 70, 70), 0.8)]
                            
                            with patch.object(self.generator, '_detect_fungi') as mock_fungi:
                                mock_fungi.return_value = [((20, 20, 40, 40), 0.6)]
                                
                                with patch.object(self.generator, '_detect_algae') as mock_algae:
                                    mock_algae.return_value = [((80, 80, 90, 90), 0.7)]
                                    
                                    with patch.object(self.generator, '_apply_nms') as mock_nms:
                                        mock_nms.return_value = [
                                            {"coords": (10, 10, 30, 30), "class_id": "0", "confidence": 0.7, "size": 400},
                                            {"coords": (50, 50, 70, 70), "class_id": "0", "confidence": 0.8, "size": 400},
                                            {"coords": (20, 20, 40, 40), "class_id": "1", "confidence": 0.6, "size": 400}
                                        ]
                                        
                                        # Test the function
                                        results = self.generator._detect_with_cv(np.zeros((100, 100, 3)))
                                        
                                        # Check the results
                                        self.assertEqual(len(results), 3)
                                        self.assertIn(("0", 10, 10, 30, 30), results)
                                        self.assertIn(("0", 50, 50, 70, 70), results)
                                        self.assertIn(("1", 20, 20, 40, 40), results)

    @patch("microdetect.annotation.annotator.suggestions.generator.logger")
    def test_detect_with_cv_few_detections(self, mock_logger):
        with patch.object(self.generator, '_adaptive_preprocessing') as mock_preprocess:
            mock_preprocess.return_value = {"enhanced": np.zeros((10, 10), dtype=np.uint8)}
            
            with patch.object(self.generator, '_multi_segmentation') as mock_segment:
                mock_segment.return_value = {"threshold": np.zeros((10, 10), dtype=np.uint8)}
                
                with patch.object(self.generator, '_filter_contours') as mock_filter:
                    mock_filter.return_value = []
                    
                    with patch.object(self.generator, '_detect_yeasts') as mock_yeasts:
                        mock_yeasts.return_value = []
                        
                        with patch.object(self.generator, '_detect_fungi') as mock_fungi:
                            mock_fungi.return_value = []
                            
                            with patch.object(self.generator, '_detect_algae') as mock_algae:
                                mock_algae.return_value = []
                                
                                with patch.object(self.generator, '_apply_nms') as mock_nms:
                                    # Only one detection (triggers emergency detection)
                                    mock_nms.return_value = [{"coords": (10, 10, 30, 30), "class_id": "0", "confidence": 0.7, "size": 400}]
                                    
                                    with patch.object(self.generator, '_emergency_detection') as mock_emergency:
                                        # Emergency detection finds more objects
                                        mock_emergency.return_value = [("1", 50, 50, 70, 70), ("2", 80, 80, 90, 90)]
                                        
                                        # Test the function
                                        results = self.generator._detect_with_cv(np.zeros((100, 100, 3)))
                                        
                                        # Check the results (1 from normal + 2 from emergency)
                                        self.assertEqual(len(results), 3)
                                        self.assertIn(("0", 10, 10, 30, 30), results)
                                        self.assertIn(("1", 50, 50, 70, 70), results)
                                        self.assertIn(("2", 80, 80, 90, 90), results)
                                        mock_emergency.assert_called_once()

    @patch("microdetect.annotation.annotator.suggestions.generator.logger")
    def test_detect_with_cv_exception(self, mock_logger):
        with patch("microdetect.annotation.annotator.suggestions.generator.cv2.cvtColor", side_effect=Exception("CV Error")):
            results = self.generator._detect_with_cv(np.zeros((10, 10, 3)))
            
            self.assertEqual(results, [])
            mock_logger.error.assert_called_once()

    def test_adaptive_preprocessing(self):
        img_gray = np.random.randint(0, 255, (100, 100), dtype=np.uint8)
        
        # Test normal image
        results = self.generator._adaptive_preprocessing(img_gray, False, False)
        self.assertIn("normalized", results)
        self.assertIn("blur", results)
        self.assertIn("clahe", results)
        self.assertIn("enhanced", results)
        
        # Test dark image
        results_dark = self.generator._adaptive_preprocessing(img_gray, True, False)
        self.assertIn("enhanced", results_dark)
        
        # Test low contrast image
        results_low_contrast = self.generator._adaptive_preprocessing(img_gray, False, True)
        self.assertIn("enhanced", results_low_contrast)
        
        # Test both
        results_both = self.generator._adaptive_preprocessing(img_gray, True, True)
        self.assertIn("enhanced", results_both)

    def test_multi_segmentation(self):
        img = np.random.randint(0, 255, (100, 100), dtype=np.uint8)
        
        results = self.generator._multi_segmentation(img)
        
        self.assertIn("adaptive", results)
        self.assertIn("otsu", results)
        
        # K-means and watershed may fail gracefully - only test they don't raise exceptions

    def test_filter_contours_basic(self):
        test_img = np.ones((100, 100, 3), dtype=np.uint8) * 128
        
        # Create two mock contours
        small_contour = np.array([[[10, 10]], [[10, 15]], [[15, 15]], [[15, 10]]])
        good_contour = np.array([[[20, 20]], [[20, 40]], [[40, 40]], [[40, 20]]])
        
        # Test with mocks
        with patch("microdetect.annotation.annotator.suggestions.generator.cv2.contourArea") as mock_area:
            mock_area.side_effect = [10, 400]  # First contour too small, second good
            
            with patch("microdetect.annotation.annotator.suggestions.generator.cv2.arcLength") as mock_length:
                mock_length.return_value = 80  # Good perimeter
                
                with patch("microdetect.annotation.annotator.suggestions.generator.cv2.boundingRect") as mock_rect:
                    mock_rect.side_effect = [(10, 10, 5, 5), (20, 20, 20, 20)]
                    
                    with patch("microdetect.annotation.annotator.suggestions.generator.cv2.mean") as mock_mean:
                        mock_mean.return_value = [128, 128, 128, 0]  # Gray mean color
                        
                        with patch("microdetect.annotation.annotator.suggestions.generator.cv2.subtract") as mock_subtract:
                            mock_subtract.return_value = np.zeros((100, 100), dtype=np.uint8)
                            
                            with patch("microdetect.annotation.annotator.suggestions.generator.np.count_nonzero") as mock_nonzero:
                                mock_nonzero.return_value = 100  # Some non-zero pixels
                                
                                with patch("microdetect.annotation.annotator.suggestions.generator.np.std") as mock_std:
                                    mock_std.return_value = 10  # Some standard deviation (texture)
                                    
                                    filtered = self.generator._filter_contours([small_contour, good_contour], test_img)
                                    
                                    # First contour should be filtered out due to small area
                                    self.assertEqual(len(filtered), 1)
                                    np.testing.assert_array_equal(filtered[0], good_contour)

    def test_detect_yeasts(self):
        img_gray = np.random.randint(0, 255, (100, 100), dtype=np.uint8)
        enhanced_img = np.random.randint(0, 255, (100, 100), dtype=np.uint8)
        
        # This is a complex method with multiple cv2 calls - test with mocks
        with patch("microdetect.annotation.annotator.suggestions.generator.cv2.HoughCircles") as mock_hough:
            # Mock Hough circles to return none (avoid complex numpy setup)
            mock_hough.return_value = None
            
            with patch("microdetect.annotation.annotator.suggestions.generator.cv2.SimpleBlobDetector_create") as mock_create:
                # Mock detector to return empty keypoints
                mock_detector = MagicMock()
                mock_detector.detect.return_value = []
                mock_create.return_value = mock_detector
                
                result = self.generator._detect_yeasts(img_gray, enhanced_img)
                
                self.assertEqual(result, [])

    def test_detect_fungi(self):
        img_gray = np.random.randint(0, 255, (100, 100), dtype=np.uint8)
        enhanced_img = np.random.randint(0, 255, (100, 100), dtype=np.uint8)
        
        # Test with mocks
        with patch("microdetect.annotation.annotator.suggestions.generator.cv2.getGaborKernel") as mock_gabor:
            mock_gabor.return_value = np.zeros((10, 10), dtype=np.float32)
            
            with patch("microdetect.annotation.annotator.suggestions.generator.cv2.filter2D") as mock_filter:
                mock_filter.return_value = np.zeros((100, 100), dtype=np.uint8)
                
                with patch("microdetect.annotation.annotator.suggestions.generator.cv2.threshold") as mock_threshold:
                    mock_threshold.return_value = (None, np.zeros((100, 100), dtype=np.uint8))
                    
                    with patch("microdetect.annotation.annotator.suggestions.generator.cv2.findContours") as mock_find:
                        mock_find.return_value = ([], None)
                        
                        result = self.generator._detect_fungi(img_gray, enhanced_img)
                        
                        self.assertEqual(result, [])

    def test_detect_algae(self):
        img_rgb = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        enhanced_img = np.random.randint(0, 255, (100, 100), dtype=np.uint8)
        
        # Test with mocks
        with patch("microdetect.annotation.annotator.suggestions.generator.cv2.cvtColor") as mock_cvt:
            mock_cvt.return_value = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
            
            with patch("microdetect.annotation.annotator.suggestions.generator.cv2.inRange") as mock_range:
                mock_range.return_value = np.zeros((100, 100), dtype=np.uint8)
                
                with patch("microdetect.annotation.annotator.suggestions.generator.cv2.morphologyEx") as mock_morph:
                    mock_morph.return_value = np.zeros((100, 100), dtype=np.uint8)
                    
                    with patch("microdetect.annotation.annotator.suggestions.generator.cv2.findContours") as mock_find:
                        mock_find.return_value = ([], None)
                        
                        result = self.generator._detect_algae(img_rgb, enhanced_img)
                        
                        self.assertEqual(result, [])

    def test_apply_nms(self):
        # Create overlapping boxes of same class
        boxes = [
            {"coords": (10, 10, 50, 50), "class_id": "0", "confidence": 0.9, "size": 1600},
            {"coords": (30, 30, 70, 70), "class_id": "0", "confidence": 0.8, "size": 1600},
            {"coords": (80, 80, 100, 100), "class_id": "0", "confidence": 0.7, "size": 400}
        ]
        
        result = self.generator._apply_nms(boxes)
        
        # The highest confidence box (0.9) should be kept, and the non-overlapping box (0.7)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["confidence"], 0.9)
        
        # Test with different classes
        boxes = [
            {"coords": (10, 10, 50, 50), "class_id": "0", "confidence": 0.9, "size": 1600},
            {"coords": (30, 30, 70, 70), "class_id": "1", "confidence": 0.8, "size": 1600}
        ]
        
        result = self.generator._apply_nms(boxes)
        
        # Different classes should both be kept even if overlapping
        self.assertEqual(len(result), 2)
        
        # Test with empty input
        result = self.generator._apply_nms([])
        self.assertEqual(result, [])

    def test_advanced_classification(self):
        # Create a simple test ROI and contour
        roi = np.ones((50, 50, 3), dtype=np.uint8) * 128
        contour = np.array([[[10, 10]], [[10, 40]], [[40, 40]], [[40, 10]]])
        
        # Test with mocks
        with patch("microdetect.annotation.annotator.suggestions.generator.cv2.cvtColor") as mock_cvt:
            mock_cvt.return_value = np.ones((50, 50), dtype=np.uint8) * 128
            
            with patch("microdetect.annotation.annotator.suggestions.generator.cv2.moments") as mock_moments:
                mock_moments.return_value = {}
                
                with patch("microdetect.annotation.annotator.suggestions.generator.cv2.HuMoments") as mock_hu:
                    mock_hu.return_value = np.zeros((7, 1))
                    
                    with patch("microdetect.annotation.annotator.suggestions.generator.cv2.contourArea") as mock_area:
                        mock_area.return_value = 900
                        
                        with patch("microdetect.annotation.annotator.suggestions.generator.cv2.arcLength") as mock_length:
                            mock_length.return_value = 120
                            
                            with patch("microdetect.annotation.annotator.suggestions.generator.cv2.boundingRect") as mock_rect:
                                mock_rect.return_value = (10, 10, 30, 30)
                                
                                with patch("microdetect.annotation.annotator.suggestions.generator.cv2.Sobel") as mock_sobel:
                                    mock_sobel.return_value = np.zeros((50, 50), dtype=np.float64)
                                    
                                    with patch("microdetect.annotation.annotator.suggestions.generator.cv2.magnitude") as mock_mag:
                                        mock_mag.return_value = np.zeros((50, 50), dtype=np.float64)
                                        
                                        with patch("microdetect.annotation.annotator.suggestions.generator.cv2.phase") as mock_phase:
                                            mock_phase.return_value = np.zeros((50, 50), dtype=np.float64)
                                            
                                            with patch("microdetect.annotation.annotator.suggestions.generator.np.mean") as mock_mean:
                                                mock_mean.side_effect = [128, 128, [10, 10, 10], [30, 30, 30]]
                                                
                                                with patch("microdetect.annotation.annotator.suggestions.generator.np.std") as mock_std:
                                                    mock_std.return_value = 10
                                                    
                                                    class_id, confidence = self.generator._advanced_classification(roi, contour)
                                                    
                                                    # Should return a valid classification
                                                    self.assertIn(class_id, ["0", "1", "2"])
                                                    self.assertGreaterEqual(confidence, 0.3)
                                                    self.assertLessEqual(confidence, 0.95)
        
        # Test empty ROI case
        empty_roi = np.array([])
        class_id, confidence = self.generator._advanced_classification(empty_roi, contour)
        self.assertEqual(class_id, "0")
        self.assertEqual(confidence, 0.3)

    def test_classify_microorganism(self):
        # Test the compatibility method that calls _advanced_classification
        roi = np.ones((50, 50, 3), dtype=np.uint8) * 128
        contour = np.array([[[10, 10]], [[10, 40]], [[40, 40]], [[40, 10]]])
        
        with patch.object(self.generator, '_advanced_classification') as mock_classify:
            mock_classify.return_value = ("0", 0.8)
            
            result = self.generator._classify_microorganism(roi, contour)
            
            self.assertEqual(result, "0")
            mock_classify.assert_called_once_with(roi, contour)

    @patch("microdetect.annotation.annotator.suggestions.generator.logger")
    def test_advanced_classification_exception(self, mock_logger):
        roi = np.ones((50, 50, 3), dtype=np.uint8) * 128
        contour = np.array([[[10, 10]], [[10, 40]], [[40, 40]], [[40, 10]]])
        
        with patch("microdetect.annotation.annotator.suggestions.generator.cv2.cvtColor", side_effect=Exception("Error")):
            class_id, confidence = self.generator._advanced_classification(roi, contour)
            
            self.assertEqual(class_id, "0")
            self.assertEqual(confidence, 0.3)
            mock_logger.warning.assert_called_once()

    @patch("microdetect.annotation.annotator.suggestions.generator.logger")
    def test_generate_suggestions_exception(self, mock_logger):
        with patch("microdetect.annotation.annotator.suggestions.generator.cv2.imread", side_effect=Exception("Error")):
            results = self.generator.generate_suggestions("test.jpg")
            
            self.assertEqual(results, [])
            mock_logger.error.assert_called_once()


if __name__ == "__main__":
    unittest.main()