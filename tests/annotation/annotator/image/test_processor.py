import unittest
import numpy as np
import cv2
from microdetect.annotation.annotator.image.processor import ImageProcessor


class TestImageProcessor(unittest.TestCase):
    def setUp(self):
        # Create test images
        self.gray_img = np.ones((100, 100), dtype=np.uint8) * 128
        self.color_img = np.zeros((100, 100, 3), dtype=np.uint8)
        for i in range(100):
            self.color_img[:, i] = [i, 100, 255 - i]  # RGB gradient

    def test_resize_image(self):
        # Test image larger than bounds
        img = np.ones((1200, 1600, 3), dtype=np.uint8) * 128
        resized, scale = ImageProcessor.resize_image(img)

        self.assertLessEqual(resized.shape[1], 800)
        self.assertLessEqual(resized.shape[0], 600)
        self.assertLess(scale, 1.0)

        # Test small image (shouldn't resize)
        small_img = np.ones((300, 400, 3), dtype=np.uint8) * 128
        resized, scale = ImageProcessor.resize_image(small_img)
        self.assertEqual(resized.shape, small_img.shape)
        self.assertEqual(scale, 1.0)

    def test_apply_zoom(self):
        # Test zoom in
        zoomed = ImageProcessor.apply_zoom(self.color_img, 2.0)
        self.assertEqual(zoomed.shape, (200, 200, 3))

        # Test zoom out
        zoomed = ImageProcessor.apply_zoom(self.color_img, 0.5)
        self.assertEqual(zoomed.shape, (50, 50, 3))

        # Test no zoom
        zoomed = ImageProcessor.apply_zoom(self.color_img, 1.0)
        np.testing.assert_array_equal(zoomed, self.color_img)

    def test_apply_brightness_contrast(self):
        # Test no change
        adjusted = ImageProcessor.apply_brightness_contrast(self.gray_img, 0, 0)
        np.testing.assert_array_equal(adjusted, self.gray_img)

        # Test brightness increase
        brightened = ImageProcessor.apply_brightness_contrast(self.gray_img, 50, 0)
        self.assertTrue(np.mean(brightened) > np.mean(self.gray_img))

        # Test contrast increase
        contrasted = ImageProcessor.apply_brightness_contrast(self.gray_img, 0, 50)
        self.assertTrue(np.std(contrasted) > np.std(self.gray_img))

    def test_apply_sharpen(self):
        # Create blurry image
        blurry = cv2.GaussianBlur(self.gray_img, (7, 7), 2.0)

        # Test sharpening
        sharpened = ImageProcessor.apply_sharpen(blurry)
        self.assertTrue(np.std(sharpened) > np.std(blurry))

        # Test no sharpening
        not_sharpened = ImageProcessor.apply_sharpen(blurry, amount=0)
        np.testing.assert_array_equal(not_sharpened, blurry)

    def test_enhance_contrast_for_microscopy(self):
        enhanced_gray = ImageProcessor.enhance_contrast_for_microscopy(self.gray_img)
        self.assertEqual(enhanced_gray.shape, self.gray_img.shape)

        enhanced_color = ImageProcessor.enhance_contrast_for_microscopy(self.color_img)
        self.assertEqual(enhanced_color.shape, self.color_img.shape)

    def test_denoise_image(self):
        # Create noisy image
        noise = np.random.randint(0, 50, size=self.color_img.shape).astype(np.uint8)
        noisy_img = cv2.add(self.color_img, noise)

        # Test denoising
        denoised = ImageProcessor.denoise_image(noisy_img)
        self.assertTrue(np.std(denoised) < np.std(noisy_img))

        # Test no denoising
        not_denoised = ImageProcessor.denoise_image(noisy_img, strength=0)
        np.testing.assert_array_equal(not_denoised, noisy_img)


if __name__ == '__main__':
    unittest.main()