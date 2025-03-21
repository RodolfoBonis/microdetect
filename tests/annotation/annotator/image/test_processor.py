import unittest
import numpy as np
import cv2
from microdetect.annotation.annotator.image.processor import ImageProcessor


class TestImageProcessor(unittest.TestCase):
    def setUp(self):
        # Create test images
        # Imagem com gradiente em vez de uniforme para testes de contraste
        self.gray_img = np.zeros((100, 100), dtype=np.uint8)
        for i in range(100):
            self.gray_img[i, :] = i * 255 // 100  # Gradiente vertical de 0 a 255

        # Imagem colorida com gradiente
        self.color_img = np.zeros((100, 100, 3), dtype=np.uint8)
        for i in range(100):
            self.color_img[:, i] = [i, 100, 255 - i]  # RGB gradient

        # Imagem com padrões para testes de nitidez
        self.pattern_img = np.ones((100, 100), dtype=np.uint8) * 128
        # Adicionar linhas e bordas para testes de nitidez
        self.pattern_img[40:60, :] = 200  # Linha horizontal
        self.pattern_img[:, 40:60] = 50  # Linha vertical

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

        # Test custom dimensions
        img = np.ones((1200, 1600, 3), dtype=np.uint8) * 128
        custom_max_width, custom_max_height = 1000, 800
        resized, scale = ImageProcessor.resize_image(img, custom_max_width, custom_max_height)
        self.assertLessEqual(resized.shape[1], custom_max_width)
        self.assertLessEqual(resized.shape[0], custom_max_height)

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

        # Test brightness decrease
        darkened = ImageProcessor.apply_brightness_contrast(self.gray_img, -50, 0)
        self.assertTrue(np.mean(darkened) < np.mean(self.gray_img))

        # Test contrast increase - usamos uma imagem com gradiente definido
        original_std = np.std(self.gray_img.astype(np.float32))
        contrasted = ImageProcessor.apply_brightness_contrast(self.gray_img, 0, 50)
        contrasted_std = np.std(contrasted.astype(np.float32))
        self.assertGreater(contrasted_std, original_std)

        # Test contrast decrease
        low_contrast = ImageProcessor.apply_brightness_contrast(self.gray_img, 0, -50)
        low_contrast_std = np.std(low_contrast.astype(np.float32))
        self.assertLess(low_contrast_std, original_std)

        # Test extreme values (to trigger clamp)
        # Very high brightness (will be clamped to 255)
        extreme_bright = ImageProcessor.apply_brightness_contrast(self.gray_img, 100, 0)
        self.assertTrue(np.max(extreme_bright) <= 255)
        self.assertTrue(np.mean(extreme_bright) > np.mean(self.gray_img))

        # Very high contrast with dark and bright pixels
        extreme_contrast = ImageProcessor.apply_brightness_contrast(self.color_img, 0, 100)
        self.assertTrue(np.max(extreme_contrast) <= 255)
        self.assertTrue(np.min(extreme_contrast) >= 0)

        # Test combined brightness and contrast
        combined = ImageProcessor.apply_brightness_contrast(self.gray_img, 30, 30)
        self.assertFalse(np.array_equal(combined, self.gray_img))

    def test_apply_sharpen(self):
        # Usar imagem com padrões para testar nitidez
        blurry = cv2.GaussianBlur(self.pattern_img, (7, 7), 2.0)

        # Calcular variação de alta frequência usando Laplaciano
        # (melhor métrica para detectar nitidez do que desvio padrão)
        def calculate_sharpness(img):
            laplacian = cv2.Laplacian(img, cv2.CV_64F)
            return np.var(laplacian)

        original_sharpness = calculate_sharpness(blurry)

        # Test sharpening
        sharpened = ImageProcessor.apply_sharpen(blurry)
        sharpened_metric = calculate_sharpness(sharpened)
        self.assertGreater(sharpened_metric, original_sharpness)

        # Test no sharpening
        not_sharpened = ImageProcessor.apply_sharpen(blurry, amount=0)
        np.testing.assert_array_equal(not_sharpened, blurry)

        # Test negative amount (should return copy without sharpening)
        not_sharpened_neg = ImageProcessor.apply_sharpen(blurry, amount=-0.5)
        np.testing.assert_array_equal(not_sharpened_neg, blurry)

        # Test custom amount
        custom_sharpened = ImageProcessor.apply_sharpen(blurry, amount=0.5)
        custom_sharpness = calculate_sharpness(custom_sharpened)
        self.assertGreater(custom_sharpness, original_sharpness)
        self.assertLess(custom_sharpness, sharpened_metric)

    def test_enhance_contrast_for_microscopy(self):
        # Para testar CLAHE, precisamos de uma imagem com distribuição desigual
        # e áreas de baixo contraste
        test_img = np.zeros((100, 100), dtype=np.uint8)
        # Criar uma imagem com iluminação desigual
        for i in range(100):
            for j in range(100):
                # Criar um gradiente circular com baixo contraste em áreas escuras
                dist = np.sqrt((i - 50) ** 2 + (j - 50) ** 2)
                test_img[i, j] = max(0, min(255, int(128 - dist)))

        # Test grayscale image
        enhanced_gray = ImageProcessor.enhance_contrast_for_microscopy(test_img)
        self.assertEqual(enhanced_gray.shape, test_img.shape)

        # Verificar se CLAHE realmente ajustou o contraste local
        # Verificamos a entropia da imagem, que aumenta quando o contraste melhora
        def calculate_entropy(img):
            hist = cv2.calcHist([img], [0], None, [256], [0, 256])
            hist = hist / hist.sum()
            entropy = -np.sum(hist * np.log2(hist + 1e-7))
            return entropy

        original_entropy = calculate_entropy(test_img)
        enhanced_entropy = calculate_entropy(enhanced_gray)
        self.assertGreater(enhanced_entropy, original_entropy)

        # Test color image (será convertida para grayscale e depois de volta para RGB)
        color_test_img = cv2.cvtColor(test_img, cv2.COLOR_GRAY2RGB)
        enhanced_color = ImageProcessor.enhance_contrast_for_microscopy(color_test_img)
        self.assertEqual(enhanced_color.shape, color_test_img.shape)

        # Testar com imagem já em escala de cinza mas com 3 dimensões
        gray_3d = cv2.cvtColor(test_img, cv2.COLOR_GRAY2RGB)
        enhanced_gray_3d = ImageProcessor.enhance_contrast_for_microscopy(gray_3d)
        self.assertEqual(enhanced_gray_3d.shape, gray_3d.shape)

    def test_denoise_image(self):
        # Create noisy image
        noise = np.random.randint(0, 50, size=self.color_img.shape).astype(np.uint8)
        noisy_img = cv2.add(self.color_img, noise)

        # Test denoising
        denoised = ImageProcessor.denoise_image(noisy_img)
        self.assertTrue(np.std(cv2.absdiff(denoised, noisy_img)) > 0)

        # Test different strength
        light_denoised = ImageProcessor.denoise_image(noisy_img, strength=5)
        strong_denoised = ImageProcessor.denoise_image(noisy_img, strength=20)
        # Verificar se denoising mais forte causa maior diferença com a imagem ruidosa
        light_diff = np.mean(cv2.absdiff(light_denoised, noisy_img))
        strong_diff = np.mean(cv2.absdiff(strong_denoised, noisy_img))
        self.assertTrue(strong_diff > light_diff)

        # Test no denoising
        not_denoised = ImageProcessor.denoise_image(noisy_img, strength=0)
        np.testing.assert_array_equal(not_denoised, noisy_img)


if __name__ == '__main__':
    unittest.main()