"""
Módulo para augmentação de dados de imagens e anotações.
"""

import glob
import logging
import os
from typing import Dict, List, Optional, Tuple, Union

import cv2
import numpy as np
from tqdm import tqdm

from microdetect.utils.config import config

logger = logging.getLogger(__name__)


class DataAugmenter:
    """
    Classe para aplicar técnicas de augmentação em imagens e suas anotações.
    """

    def __init__(
        self,
        brightness_range: Tuple[float, float] = None,
        contrast_range: Tuple[float, float] = None,
        flip_probability: float = None,
        rotation_range: Tuple[float, float] = None,
        noise_probability: float = None,
    ):
        """
        Inicializa o augmentador com parâmetros configuráveis.

        Args:
            brightness_range: Intervalo para ajuste de brilho (alpha)
            contrast_range: Intervalo para ajuste de contraste (beta)
            flip_probability: Probabilidade de aplicar flip horizontal
            rotation_range: Intervalo para rotação em graus
            noise_probability: Probabilidade de aplicar ruído gaussiano
        """
        # Usar valores da configuração ou os padrões fornecidos
        self.brightness_range = brightness_range or config.get("augmentation.brightness_range", [0.8, 1.2])
        self.contrast_range = contrast_range or config.get("augmentation.contrast_range", [-30, 30])
        self.flip_probability = flip_probability or config.get("augmentation.flip_probability", 0.5)
        self.rotation_range = rotation_range or config.get("augmentation.rotation_range", [-15, 15])
        self.noise_probability = noise_probability or config.get("augmentation.noise_probability", 0.3)

    def augment_data(
        self,
        input_image_dir: str,
        input_label_dir: str,
        output_image_dir: str = None,
        output_label_dir: str = None,
        augmentation_factor: int = None,
    ) -> Tuple[int, int]:
        """
        Aplica técnicas de augmentação de dados nas imagens e suas anotações.

        Args:
            input_image_dir: Diretório com as imagens originais
            input_label_dir: Diretório com as anotações originais
            output_image_dir: Diretório para salvar as imagens aumentadas (se None, usa input_image_dir)
            output_label_dir: Diretório para salvar as anotações aumentadas (se None, usa input_label_dir)
            augmentation_factor: Número de variações a serem geradas para cada imagem

        Returns:
            Tupla com (número de imagens originais, número de imagens augmentadas)
        """
        # Configurar diretórios de saída (se não especificados, usa os de entrada)
        output_image_dir = output_image_dir or input_image_dir
        output_label_dir = output_label_dir or input_label_dir
        augmentation_factor = augmentation_factor or config.get("augmentation.factor", 5)

        # Criar diretórios de saída se não existirem
        os.makedirs(output_image_dir, exist_ok=True)
        os.makedirs(output_label_dir, exist_ok=True)

        # Obter todos os arquivos de imagem
        image_files = []
        for ext in ["*.jpg", "*.jpeg", "*.png"]:
            image_files.extend(glob.glob(os.path.join(input_image_dir, ext)))

        if not image_files:
            logger.warning(f"Nenhum arquivo de imagem encontrado em {input_image_dir}")
            return 0, 0

        logger.info(
            f"Iniciando augmentação para {len(image_files)} imagens, " f"gerando {augmentation_factor} variações de cada"
        )

        # Configurar barra de progresso
        progress_bar = tqdm(total=len(image_files), desc="Augmentando dados")

        total_augmented = 0

        # Processar cada imagem
        for img_path in image_files:
            # Carregar imagem
            img = cv2.imread(img_path)
            if img is None:
                logger.error(f"Não foi possível carregar a imagem {img_path}")
                progress_bar.update(1)
                continue

            h, w = img.shape[:2]

            # Carregar anotações
            base_name = os.path.basename(img_path)
            label_path = os.path.join(input_label_dir, os.path.splitext(base_name)[0] + ".txt")

            if not os.path.exists(label_path):
                logger.warning(f"Arquivo de anotação não encontrado para {img_path}")
                progress_bar.update(1)
                continue

            with open(label_path, "r") as f:
                annotations = f.readlines()

            # Gerar augmentações
            for i in range(augmentation_factor):
                # 1. Variação de brilho e contraste
                alpha = np.random.uniform(self.brightness_range[0], self.brightness_range[1])  # Contraste
                beta = np.random.uniform(self.contrast_range[0], self.contrast_range[1])  # Brilho
                img_aug = cv2.convertScaleAbs(img, alpha=alpha, beta=beta)

                # 2. Flip horizontal
                annotations_aug = annotations.copy()
                if np.random.random() < self.flip_probability:
                    img_aug = cv2.flip(img_aug, 1)
                    # Ajustar anotações para o flip
                    annotations_aug = self._adjust_annotations_for_flip(annotations, w)

                # 3. Rotação leve
                if np.random.random() < self.flip_probability:
                    angle = np.random.uniform(self.rotation_range[0], self.rotation_range[1])
                    M = cv2.getRotationMatrix2D((w / 2, h / 2), angle, 1.0)
                    img_aug = cv2.warpAffine(img_aug, M, (w, h))
                    # Para simplificar, mantemos as anotações originais para pequenas rotações

                # 4. Ruído gaussiano
                if np.random.random() < self.noise_probability:
                    noise = np.random.normal(0, 10, img_aug.shape).astype(np.uint8)
                    img_aug = cv2.add(img_aug, noise)

                # Salvar imagem e anotação aumentadas
                aug_filename = f"{os.path.splitext(base_name)[0]}_aug{i}{os.path.splitext(base_name)[1]}"
                aug_img_path = os.path.join(output_image_dir, aug_filename)
                aug_label_path = os.path.join(output_label_dir, os.path.splitext(aug_filename)[0] + ".txt")

                cv2.imwrite(aug_img_path, img_aug)
                with open(aug_label_path, "w") as f:
                    f.writelines(annotations_aug)

                total_augmented += 1

            progress_bar.update(1)

        # Fechar barra de progresso
        progress_bar.close()

        logger.info(f"Augmentação concluída: geradas {total_augmented} novas imagens a partir de {len(image_files)} originais")
        return len(image_files), total_augmented

    @staticmethod
    def _adjust_annotations_for_flip(annotations: List[str], image_width: int) -> List[str]:
        """
        Ajusta as coordenadas das anotações para o flip horizontal.

        Args:
            annotations: Lista de anotações no formato YOLO
            image_width: Largura da imagem

        Returns:
            Lista de anotações ajustadas
        """
        flipped_annotations = []
        for ann in annotations:
            parts = ann.strip().split()
            if len(parts) == 5:  # formato YOLO: class x_center y_center width height
                cls, x, y, w_box, h_box = parts
                # Inverter coordenada x para flip horizontal
                x_flipped = 1.0 - float(x)
                flipped_annotations.append(f"{cls} {x_flipped} {y} {w_box} {h_box}\n")
            else:
                # Se a anotação não estiver no formato esperado, mantê-la como está
                flipped_annotations.append(ann)

        return flipped_annotations
