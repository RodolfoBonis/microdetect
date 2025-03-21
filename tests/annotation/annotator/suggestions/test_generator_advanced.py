import unittest
from unittest.mock import MagicMock, patch

import numpy as np

from microdetect.annotation.annotator.suggestions.generator import SuggestionGenerator


class TestSuggestionGeneratorAdvanced(unittest.TestCase):
    """Tests focused on more complex methods requiring more mocking."""
    
    def setUp(self):
        self.classes = ["0-Levedura", "1-Fungo", "2-Microalga"]
        self.generator = SuggestionGenerator(self.classes, yolo_model_path=None)
        
        # Create a simple test image and contour for testing
        self.test_img = np.ones((100, 100, 3), dtype=np.uint8) * 128
        self.test_contour = np.array([[[10, 10]], [[10, 40]], [[40, 40]], [[40, 10]]])

    @patch("microdetect.annotation.annotator.suggestions.generator.logger")
    def test_emergency_detection(self, mock_logger):
        # This complex method requires extensive mocking
        with patch("microdetect.annotation.annotator.suggestions.generator.cv2.cvtColor") as mock_cvtColor, \
             patch("microdetect.annotation.annotator.suggestions.generator.cv2.bilateralFilter") as mock_filter, \
             patch("microdetect.annotation.annotator.suggestions.generator.cv2.Canny") as mock_canny, \
             patch("microdetect.annotation.annotator.suggestions.generator.cv2.dilate") as mock_dilate, \
             patch("microdetect.annotation.annotator.suggestions.generator.cv2.findContours") as mock_find, \
             patch("microdetect.annotation.annotator.suggestions.generator.cv2.drawContours") as mock_draw, \
             patch("microdetect.annotation.annotator.suggestions.generator.cv2.connectedComponentsWithStats") as mock_connected:
            
            # Set up mock returns
            mock_cvtColor.return_value = np.ones((100, 100), dtype=np.uint8) * 128
            mock_filter.return_value = np.ones((100, 100), dtype=np.uint8) * 128
            mock_canny.return_value = np.ones((100, 100), dtype=np.uint8) * 255
            mock_dilate.return_value = np.ones((100, 100), dtype=np.uint8) * 255
            mock_find.return_value = ([], None)
            mock_draw.return_value = np.ones((100, 100), dtype=np.uint8) * 255
            
            # Mock connected components to return one object
            num_labels = 2  # 0=background, 1=object
            labels = np.zeros((100, 100), dtype=np.int32)
            labels[30:50, 30:50] = 1  # One square object
            stats = np.array([
                [0, 0, 100, 100, 10000],  # Background
                [30, 30, 20, 20, 400]     # Object 1
            ])
            centroids = np.array([
                [50, 50],                  # Background centroid
                [40, 40]                   # Object 1 centroid
            ])
            mock_connected.return_value = (num_labels, labels, stats, centroids)
            
            # Mock advanced_classification to return a predictable result
            with patch.object(self.generator, '_advanced_classification') as mock_classify:
                mock_classify.return_value = ("1", 0.7)  # Object classified as fungus
                
                # Test the emergency detection
                results = self.generator._emergency_detection(self.test_img)
                
                # Should return one detected object
                self.assertEqual(len(results), 1)
                self.assertEqual(results[0][0], "1")  # Class ID
                self.assertEqual(len(results[0]), 5)  # Tuple format (class_id, x1, y1, x2, y2)
    
    @patch("microdetect.annotation.annotator.suggestions.generator.logger")
    def test_emergency_detection_exception(self, mock_logger):
        # Test exception handling
        with patch("microdetect.annotation.annotator.suggestions.generator.cv2.cvtColor", side_effect=Exception("Test error")):
            results = self.generator._emergency_detection(self.test_img)
            
            self.assertEqual(results, [])
            mock_logger.error.assert_called_once()
    
    @patch("microdetect.annotation.annotator.suggestions.generator.logger")    
    def test_advanced_classification(self, mock_logger):
        roi = np.ones((50, 50, 3), dtype=np.uint8) * 128
        contour = self.test_contour
        
        # Complex mocking
        with patch("microdetect.annotation.annotator.suggestions.generator.cv2.cvtColor") as mock_cvtColor, \
             patch("microdetect.annotation.annotator.suggestions.generator.cv2.moments") as mock_moments, \
             patch("microdetect.annotation.annotator.suggestions.generator.cv2.HuMoments") as mock_hu, \
             patch("microdetect.annotation.annotator.suggestions.generator.cv2.contourArea") as mock_area, \
             patch("microdetect.annotation.annotator.suggestions.generator.cv2.arcLength") as mock_length, \
             patch("microdetect.annotation.annotator.suggestions.generator.cv2.boundingRect") as mock_rect, \
             patch("microdetect.annotation.annotator.suggestions.generator.cv2.Sobel") as mock_sobel, \
             patch("microdetect.annotation.annotator.suggestions.generator.cv2.magnitude") as mock_mag, \
             patch("microdetect.annotation.annotator.suggestions.generator.cv2.phase") as mock_phase, \
             patch("microdetect.annotation.annotator.suggestions.generator.np.mean") as mock_mean, \
             patch("microdetect.annotation.annotator.suggestions.generator.np.std") as mock_std:
            
            # Configure mocks
            mock_cvtColor.return_value = np.ones((50, 50), dtype=np.uint8) * 128
            mock_moments.return_value = {"m00": 100, "m10": 2500, "m01": 2500}
            mock_hu.return_value = np.zeros((7, 1))
            mock_area.return_value = 900
            mock_length.return_value = 120
            mock_rect.return_value = (10, 10, 30, 30)
            mock_sobel.return_value = np.zeros((50, 50), dtype=np.float64)
            mock_mag.return_value = np.zeros((50, 50), dtype=np.float64)
            mock_phase.return_value = np.zeros((50, 50), dtype=np.float64)
            
            # Make it classify as a yeast (circular, homogeneous)
            mock_mean.side_effect = [128, 10, [128, 128, 128], [30, 30, 30]]
            mock_std.return_value = 10
            
            # Test classification result
            class_id, confidence = self.generator._advanced_classification(roi, contour)
            
            # Should classify as yeast (class 0) with reasonable confidence
            self.assertEqual(class_id, "0")
            self.assertGreater(confidence, 0.5)
            
            # Test with different parameters for fungi classification
            mock_area.return_value = 800
            mock_length.return_value = 200  # Higher perimeter = less circular
            mock_rect.return_value = (10, 10, 40, 20)  # More elongated
            mock_std.return_value = 40  # Less homogeneous
            
            class_id, confidence = self.generator._advanced_classification(roi, contour)
            
            # Could be fungus or another class, but confidence should be reasonable
            self.assertIn(class_id, ["0", "1", "2"])
            self.assertGreater(confidence, 0.3)
    
    @patch("microdetect.annotation.annotator.suggestions.generator.logger")
    def test_detect_yeast_hough_circles(self, mock_logger):
        img_gray = np.ones((100, 100), dtype=np.uint8) * 128
        enhanced = np.ones((100, 100), dtype=np.uint8) * 200
        
        # Mock Hough circles to return some circles
        with patch("microdetect.annotation.annotator.suggestions.generator.cv2.HoughCircles") as mock_hough, \
             patch("microdetect.annotation.annotator.suggestions.generator.np.uint16") as mock_uint16, \
             patch("microdetect.annotation.annotator.suggestions.generator.cv2.circle") as mock_circle, \
             patch("microdetect.annotation.annotator.suggestions.generator.cv2.bitwise_and") as mock_bitwise, \
             patch("microdetect.annotation.annotator.suggestions.generator.np.count_nonzero") as mock_nonzero, \
             patch("microdetect.annotation.annotator.suggestions.generator.np.sum") as mock_sum, \
             patch("microdetect.annotation.annotator.suggestions.generator.np.std") as mock_std, \
             patch("microdetect.annotation.annotator.suggestions.generator.cv2.SimpleBlobDetector_create") as mock_detector_create:
            
            # Configure the Hough circles output
            circles_array = np.array([[[50, 50, 15]]])  # One circle at (50,50) with radius 15
            mock_hough.return_value = circles_array
            mock_uint16.return_value = circles_array.astype(np.uint16)
            
            # Configure bitwise_and output
            mock_bitwise.return_value = np.ones((30, 30), dtype=np.uint8) * 150
            
            # Configure nonzero, sum, std
            mock_nonzero.return_value = 700  # π*15^2 ≈ 700
            mock_sum.return_value = 105000  # 700 * 150
            mock_std.return_value = 10  # Low std = homogeneous texture (typical for yeasts)
            
            # Make blob detector return nothing
            mock_detector = MagicMock()
            mock_detector.detect.return_value = []
            mock_detector_create.return_value = mock_detector
            
            # Test the yeast detection function
            results = self.generator._detect_yeasts(img_gray, enhanced)
            
            # Should return one circle detection
            self.assertEqual(len(results), 1)
            
            # The detection should be a tuple ((x1,y1,x2,y2), confidence)
            coords, confidence = results[0]
            self.assertEqual(len(coords), 4)  # x1,y1,x2,y2
            self.assertGreater(confidence, 0.5)  # Reasonable confidence
    
    @patch("microdetect.annotation.annotator.suggestions.generator.logger")
    def test_detect_fungi(self, mock_logger):
        img_gray = np.ones((100, 100), dtype=np.uint8) * 128
        enhanced = np.ones((100, 100), dtype=np.uint8) * 200
        
        # This method is complex - mock many cv2 functions
        with patch("microdetect.annotation.annotator.suggestions.generator.cv2.getGaborKernel") as mock_gabor, \
             patch("microdetect.annotation.annotator.suggestions.generator.cv2.filter2D") as mock_filter2d, \
             patch("microdetect.annotation.annotator.suggestions.generator.cv2.threshold") as mock_threshold, \
             patch("microdetect.annotation.annotator.suggestions.generator.cv2.findContours") as mock_contours, \
             patch("microdetect.annotation.annotator.suggestions.generator.cv2.boundingRect") as mock_rect, \
             patch("microdetect.annotation.annotator.suggestions.generator.cv2.contourArea") as mock_area, \
             patch("microdetect.annotation.annotator.suggestions.generator.cv2.arcLength") as mock_length, \
             patch("microdetect.annotation.annotator.suggestions.generator.cv2.adaptiveThreshold") as mock_adaptive, \
             patch("microdetect.annotation.annotator.suggestions.generator.cv2.morphologyEx") as mock_morph, \
             patch("microdetect.annotation.annotator.suggestions.generator.cv2.distanceTransform") as mock_dist, \
             patch("microdetect.annotation.annotator.suggestions.generator.cv2.connectedComponents") as mock_connected:
            
            # Configure mocks for filamentous fungi detection
            mock_gabor.return_value = np.ones((10, 10), dtype=np.float32) * 0.1
            mock_filter2d.return_value = np.ones((100, 100), dtype=np.uint8) * 150
            mock_threshold.return_value = (None, np.ones((100, 100), dtype=np.uint8) * 255)
            
            # Create a filamentous contour (elongated)
            filamentous_contour = np.array([
                [[10, 10]], [[20, 5]], [[30, 10]], [[40, 5]], 
                [[50, 10]], [[50, 20]], [[40, 25]], [[30, 20]], 
                [[20, 25]], [[10, 20]]
            ])
            mock_contours.return_value = ([filamentous_contour], None)
            
            # Configure measurements for filamentous structure
            mock_area.return_value = 300
            mock_length.return_value = 120  # High perimeter to area ratio
            mock_rect.return_value = (10, 5, 40, 20)  # Elongated bounding box
            
            # Configure watershed related mocks
            mock_adaptive.return_value = np.ones((100, 100), dtype=np.uint8) * 255
            mock_morph.return_value = np.ones((100, 100), dtype=np.uint8) * 255
            mock_dist.return_value = np.ones((100, 100), dtype=np.float32) * 10
            
            # Connected components for skeleton analysis
            labels = np.zeros((100, 100), dtype=np.int32)
            labels[10:50, 10:20] = 1  # Elongated object
            mock_connected.return_value = (2, labels)  # 0=background, 1=object
            
            # Test fungi detection
            results = self.generator._detect_fungi(img_gray, enhanced)
            
            # Should detect at least one fungi structure
            self.assertGreaterEqual(len(results), 1)
            
            if results:
                # Each result should be ((x1,y1,x2,y2), confidence)
                coords, confidence = results[0]
                self.assertEqual(len(coords), 4)
                self.assertGreaterEqual(confidence, 0.4)
            
    @patch("microdetect.annotation.annotator.suggestions.generator.logger")
    def test_detect_algae(self, mock_logger):
        img_rgb = np.ones((100, 100, 3), dtype=np.uint8) * 128
        # Make some green-tinted areas
        img_rgb[30:50, 30:50, 1] = 200  # Boost green channel
        
        enhanced = np.ones((100, 100), dtype=np.uint8) * 150
        
        # Mock cv2 functions
        with patch("microdetect.annotation.annotator.suggestions.generator.cv2.cvtColor") as mock_cvtColor, \
             patch("microdetect.annotation.annotator.suggestions.generator.cv2.inRange") as mock_range, \
             patch("microdetect.annotation.annotator.suggestions.generator.cv2.morphologyEx") as mock_morph, \
             patch("microdetect.annotation.annotator.suggestions.generator.cv2.findContours") as mock_contours, \
             patch("microdetect.annotation.annotator.suggestions.generator.cv2.boundingRect") as mock_rect, \
             patch("microdetect.annotation.annotator.suggestions.generator.cv2.mean") as mock_mean, \
             patch("microdetect.annotation.annotator.suggestions.generator.np.std") as mock_std, \
             patch("microdetect.annotation.annotator.suggestions.generator.cv2.arcLength") as mock_length, \
             patch("microdetect.annotation.annotator.suggestions.generator.cv2.contourArea") as mock_area, \
             patch("microdetect.annotation.annotator.suggestions.generator.cv2.kmeans") as mock_kmeans:
            
            # Configure HSV color space conversion
            hsv_img = np.ones((100, 100, 3), dtype=np.uint8) * 128
            hsv_img[30:50, 30:50, 0] = 60  # Hue = green
            hsv_img[30:50, 30:50, 1] = 200  # High saturation
            mock_cvtColor.return_value = hsv_img
            
            # Configure green mask detection
            green_mask = np.zeros((100, 100), dtype=np.uint8)
            green_mask[30:50, 30:50] = 255  # Detected green area
            mock_range.return_value = green_mask
            mock_morph.return_value = green_mask  # No change in morphology for simplicity
            
            # Configure green contour
            green_contour = np.array([
                [[30, 30]], [[30, 50]], [[50, 50]], [[50, 30]]
            ])
            mock_contours.return_value = ([green_contour], None)
            
            # Configure measurements
            mock_rect.return_value = (30, 30, 20, 20)  # Square box
            mock_area.return_value = 400  # Square area
            mock_length.return_value = 80  # Perimeter
            
            # Configure color statistics
            mock_mean.return_value = [60, 180, 150, 0]  # Green-ish in HSV
            mock_std.return_value = 25  # Medium texture variation
            
            # Configure kmeans
            labels = np.zeros((100*100, 1), dtype=np.float32)
            labels[3000:5500] = 1  # Some cluster
            centers = np.array([[10], [200], [100]])  # Different intensity clusters
            mock_kmeans.return_value = (None, labels, centers)
            
            # Test algae detection
            results = self.generator._detect_algae(img_rgb, enhanced)
            
            # Should detect at least one algae
            self.assertGreaterEqual(len(results), 1)
            
            if results:
                # Each result should be ((x1,y1,x2,y2), confidence)
                coords, confidence = results[0]
                self.assertEqual(len(coords), 4)
                self.assertGreaterEqual(confidence, 0.3)


if __name__ == "__main__":
    unittest.main()