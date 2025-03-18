"""
Módulo para carregamento e manipulação de imagens.
"""

import logging
from typing import Optional, Tuple

import cv2
import numpy as np
from PIL import Image, ImageTk

logger = logging.getLogger(__name__)


class ImageLoader:
    """
    Classe para carregamento e manipulação de imagens.
    """

    def __init__(self):
        """Inicializa o carregador de imagens."""
        # Armazenar referências a objetos PhotoImage para evitar coleta de lixo
        self.image_references = {}
        self.current_img_tk = None

    def load_image(self, image_path: str) -> Optional[Tuple[np.ndarray, int, int]]:
        """
        Carrega uma imagem com tratamento de erro adequado.

        Args:
            image_path: Caminho para a imagem

        Returns:
            Tuple com imagem carregada (RGB), largura e altura ou (None, 0, 0) em caso de erro
        """
        try:
            img = cv2.imread(image_path)
            if img is None:
                raise ValueError(f"Imagem não pôde ser carregada: {image_path}")

            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            h, w = img_rgb.shape[:2]
            return img_rgb, w, h
        except Exception as e:
            logger.error(f"Erro ao carregar imagem {image_path}: {str(e)}")
            return None, 0, 0

    def resize_for_display(self, img: np.ndarray, max_width: int = 800, max_height: int = 600) -> Tuple[np.ndarray, float]:
        """
        Redimensiona uma imagem para exibição, respeitando proporções.

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

    def create_tkinter_image(self, img: np.ndarray, key: str = "main") -> ImageTk.PhotoImage:
        """
        Converte uma imagem NumPy para ImageTk para exibição no Tkinter.

        Args:
            img: Imagem NumPy (RGB)
            key: Chave para referenciar a imagem no dicionário

        Returns:
            ImageTk.PhotoImage para uso com Tkinter
        """
        # Converter para PIL Image
        pil_img = Image.fromarray(img)

        # Remover a referência anterior se existir
        if key in self.image_references:
            del self.image_references[key]

        # Criar nova referência
        self.image_references[key] = ImageTk.PhotoImage(pil_img)
        self.current_img_tk = self.image_references[key]

        return self.current_img_tk

    def redraw_with_zoom(
        self, img: np.ndarray, canvas, scale_factor: float, display_w: int, display_h: int, display_scale: float
    ):
        """
        Redesenha a imagem com o zoom atual.

        Args:
            img: Imagem original para exibição
            canvas: Canvas onde a imagem será desenhada
            scale_factor: Fator de escala do zoom
            display_w: Largura atual da imagem exibida
            display_h: Altura atual da imagem exibida
            display_scale: Escala original aplicada à imagem

        Returns:
            True se redimensionado com sucesso, False caso contrário
        """
        try:
            # Calcular novas dimensões
            new_w = int(display_w * scale_factor)
            new_h = int(display_h * scale_factor)

            # Redimensionar imagem
            img_resized = cv2.resize(img, (new_w, new_h))

            # Criar nova instância de PhotoImage
            key = "zoomed_image"

            # Converter para PIL Image
            pil_img = Image.fromarray(img_resized)

            # Remover a referência anterior se existir
            if key in self.image_references:
                del self.image_references[key]

            # Criar nova referência
            self.image_references[key] = ImageTk.PhotoImage(pil_img)
            self.current_img_tk = self.image_references[key]

            # Atualizar imagem no canvas
            canvas.delete("background")
            canvas.create_image(0, 0, anchor="nw", image=self.current_img_tk, tags="background")
            canvas.config(scrollregion=canvas.bbox("all"))

            return True
        except Exception as e:
            logger.error(f"Erro ao redesenhar imagem com zoom: {e}")
            return False

    def cleanup_references(self):
        """
        Limpa referências a imagens que não são mais necessárias.
        Chamado quando uma imagem é fechada ou quando a aplicação é encerrada.
        """
        try:
            # Manter apenas a referência atual, se houver
            current_key = None
            for key, img in self.image_references.items():
                if img is self.current_img_tk:
                    current_key = key
                    break

            # Nova lista de referências
            new_refs = {}
            if current_key:
                new_refs[current_key] = self.image_references[current_key]

            # Substituir o dicionário
            self.image_references = new_refs
        except Exception as e:
            logger.error(f"Erro ao limpar referências de imagem: {e}")
