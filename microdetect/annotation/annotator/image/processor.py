"""
Módulo para processamento de imagens na ferramenta de anotação.
"""

import logging
from typing import Optional, Tuple

import cv2
import numpy as np

logger = logging.getLogger(__name__)


class ImageProcessor:
    """
    Classe para processamento de imagens na ferramenta de anotação.
    """

    @staticmethod
    def resize_image(img: np.ndarray, max_width: int = 800, max_height: int = 600) -> Tuple[np.ndarray, float]:
        """
        Redimensiona uma imagem mantendo a proporção para exibição.

        Args:
            img: Imagem a ser redimensionada
            max_width: Largura máxima para exibição
            max_height: Altura máxima para exibição

        Returns:
            Tuple com (imagem redimensionada, fator de escala)
        """
        h, w = img.shape[:2]

        # Calcular fator de escala
        scale = min(max_width / w, max_height / h)

        # Redimensionar apenas se a imagem for maior que os limites
        if scale < 1:
            new_w, new_h = int(w * scale), int(h * scale)
            img_resized = cv2.resize(img, (new_w, new_h))
            return img_resized, scale
        else:
            return img.copy(), 1.0

    @staticmethod
    def apply_zoom(img: np.ndarray, scale_factor: float) -> np.ndarray:
        """
        Aplica zoom a uma imagem.

        Args:
            img: Imagem original
            scale_factor: Fator de escala para o zoom

        Returns:
            Imagem com zoom aplicado
        """
        if scale_factor == 1.0:
            return img.copy()

        h, w = img.shape[:2]
        new_w = int(w * scale_factor)
        new_h = int(h * scale_factor)

        return cv2.resize(img, (new_w, new_h))

    @staticmethod
    def apply_brightness_contrast(img: np.ndarray, brightness: float = 0, contrast: float = 0) -> np.ndarray:
        """
        Ajusta o brilho e contraste de uma imagem.

        Args:
            img: Imagem original
            brightness: Valor de ajuste de brilho (-100 a 100)
            contrast: Valor de ajuste de contraste (-100 a 100)

        Returns:
            Imagem com brilho e contraste ajustados
        """
        if brightness == 0 and contrast == 0:
            return img.copy()

        # Converter para valores entre 0-2 (onde 1 é neutro)
        brightness = (brightness + 100) / 100
        contrast = (contrast + 100) / 100

        # Aplicar brilho e contraste
        img_adjusted = img.copy().astype(np.float32)

        # Aplicar brilho
        img_adjusted = img_adjusted * brightness

        # Aplicar contraste
        img_adjusted = (img_adjusted - 128) * contrast + 128

        # Clamp values entre 0-255
        img_adjusted = np.clip(img_adjusted, 0, 255).astype(np.uint8)

        return img_adjusted

    @staticmethod
    def apply_sharpen(img: np.ndarray, amount: float = 1.0) -> np.ndarray:
        """
        Aplica nitidez (sharpen) a uma imagem.

        Args:
            img: Imagem original
            amount: Intensidade do efeito (1.0 é o padrão)

        Returns:
            Imagem com nitidez aplicada
        """
        if amount <= 0:
            return img.copy()

        # Kernel para sharpen
        kernel = np.array([[-1, -1, -1], [-1, 9, -1], [-1, -1, -1]])

        # Ajustar intensidade
        if amount != 1.0:
            kernel_adjusted = np.eye(3) + (kernel - np.eye(3)) * amount
            kernel = kernel_adjusted

        return cv2.filter2D(img, -1, kernel)

    @staticmethod
    def enhance_contrast_for_microscopy(img: np.ndarray) -> np.ndarray:
        """
        Melhora o contraste para imagens de microscopia usando equalização de histograma.

        Args:
            img: Imagem original

        Returns:
            Imagem com contraste melhorado
        """
        # Converter para escala de cinza se for uma imagem colorida
        if len(img.shape) > 2 and img.shape[2] == 3:
            img_gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)

            # Equalização de histograma adaptativa (CLAHE)
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            img_enhanced = clahe.apply(img_gray)

            # Converter de volta para RGB
            img_enhanced = cv2.cvtColor(img_enhanced, cv2.COLOR_GRAY2RGB)
            return img_enhanced
        else:
            # Já é escala de cinza
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            return clahe.apply(img)

    @staticmethod
    def denoise_image(img: np.ndarray, strength: float = 10) -> np.ndarray:
        """
        Remove ruído da imagem.

        Args:
            img: Imagem original
            strength: Força do filtro de denoising (maior = mais suave)

        Returns:
            Imagem com ruído reduzido
        """
        if strength <= 0:
            return img.copy()

        # Non-local means denoising
        return cv2.fastNlMeansDenoisingColored(img, None, strength, strength, 7, 21)
