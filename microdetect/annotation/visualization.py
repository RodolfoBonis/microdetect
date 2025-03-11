"""
Módulo para visualização de anotações em imagens.
"""

import glob
import logging
import os
from typing import Dict, List, Optional, Set, Tuple, Union

import cv2
import numpy as np

from microdetect.utils.config import config

logger = logging.getLogger(__name__)


class AnnotationVisualizer:
    """
    Classe para visualizar anotações de bounding boxes em imagens.
    """

    def __init__(
        self,
        class_map: Dict[str, str] = None,
        color_map: Dict[str, Tuple[int, int, int]] = None,
    ):
        """
        Inicializa o visualizador de anotações.

        Args:
            class_map: Mapeamento de IDs de classe para nomes (ex: {"0": "0-levedura"})
            color_map: Mapeamento de IDs de classe para cores RGB (ex: {"0": (0, 255, 0)})
        """
        classes = config.get("classes", ["0-levedura", "1-fungo", "2-micro-alga"])

        # Criar class_map a partir das classes se não fornecido
        if class_map is None:
            self.class_map = {}
            for cls in classes:
                parts = cls.split("-", 1)
                if len(parts) == 2:
                    self.class_map[parts[0]] = cls
        else:
            self.class_map = class_map

        # Usar color_map da configuração ou o padrão
        self.color_map = color_map or config.get(
            "color_map",
            {
                "0": (0, 255, 0),  # Verde para levedura
                "1": (0, 0, 255),  # Vermelho para fungo
                "2": (255, 0, 0),  # Azul para micro-alga
            },
        )

    def visualize_annotations(
        self,
        image_dir: str,
        label_dir: Optional[str] = None,
        output_dir: Optional[str] = None,
        filter_classes: Optional[Set[str]] = None,
    ) -> None:
        """
        Desenha bounding boxes em todas as imagens em um diretório e permite navegação entre elas.

        Args:
            image_dir: Diretório contendo as imagens
            label_dir: Diretório contendo os arquivos de anotação (se None, procura no mesmo dir que as imagens)
            output_dir: Diretório para salvar imagens anotadas (se None, não salva)
            filter_classes: Conjunto de IDs de classe para exibir (se None, mostra todas as classes)
        """
        # Obter todos os arquivos de imagem
        image_files = sorted(glob.glob(os.path.join(image_dir, "*.jpg")) + glob.glob(os.path.join(image_dir, "*.png")))

        if not image_files:
            logger.warning(f"Nenhum arquivo de imagem encontrado em {image_dir}")
            return

        current_idx = 0
        total_images = len(image_files)

        # Rastrear quais classes mostrar (inicializar todas como visíveis)
        class_visibility = {cls_id: True for cls_id in self.class_map.keys()}

        if filter_classes:
            # Inicializar apenas com classes especificadas visíveis
            class_visibility = {cls_id: (cls_id in filter_classes) for cls_id in self.class_map.keys()}

        save_current = False

        logger.info(f"Iniciando visualização de {total_images} imagens com anotações")

        while True:
            img_path = image_files[current_idx]
            img = cv2.imread(img_path)
            if img is None:
                logger.error(f"Erro: Não foi possível carregar a imagem {img_path}")
                current_idx = (current_idx + 1) % total_images
                continue

            h, w = img.shape[:2]

            # Encontrar arquivo de anotação correspondente
            base_name = os.path.splitext(os.path.basename(img_path))[0]
            if label_dir:
                label_path = os.path.join(label_dir, f"{base_name}.txt")
            else:
                label_path = os.path.join(os.path.dirname(img_path), f"{base_name}.txt")

            # Contar anotações visíveis para cada classe
            class_counts = {cls_id: 0 for cls_id in self.class_map.keys()}
            total_visible = 0

            # Desenhar caixas se as anotações existirem
            annotations = []
            if os.path.exists(label_path):
                with open(label_path, "r") as f:
                    annotations = f.readlines()

                # Desenhar cada anotação
                box_idx = 0
                for ann in annotations:
                    parts = ann.strip().split()
                    if len(parts) == 5:  # Formato YOLO: classe x_center y_center width height
                        cls, x_center, y_center, box_w, box_h = parts

                        # Pular se a classe for filtrada
                        if not class_visibility.get(cls, True):
                            continue

                        # Atualizar contagens de classe
                        class_counts[cls] = class_counts.get(cls, 0) + 1
                        total_visible += 1

                        # Converter coordenadas normalizadas para valores de pixel
                        x_center = float(x_center) * w
                        y_center = float(y_center) * h
                        box_w = float(box_w) * w
                        box_h = float(box_h) * h

                        # Calcular pontos de canto
                        x1 = int(x_center - box_w / 2)
                        y1 = int(y_center - box_h / 2)
                        x2 = int(x_center + box_w / 2)
                        y2 = int(y_center + box_h / 2)

                        # Obter cor da classe (diferente para cada classe)
                        color = self.color_map.get(cls, (0, 255, 0))

                        # Desenhar retângulo
                        cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)

                        # Obter nome da classe para exibição
                        class_name = self.class_map.get(cls, f"Classe {cls}")

                        # Adicionar nome da classe e número de identificação
                        cv2.putText(
                            img,
                            f"{class_name} #{box_idx + 1}",
                            (x1, y1 - 5),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.5,
                            color,
                            1,
                            cv2.LINE_AA,
                        )

                        box_idx += 1

            # Adicionar informações de contagem e navegação
            y_offset = 30
            cv2.putText(
                img,
                f"Total visível: {total_visible}",
                (10, y_offset),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 0),
                2,
                cv2.LINE_AA,
            )

            y_offset += 30

            # Mostrar contagem para cada classe
            for cls_id, cls_name in self.class_map.items():
                count = class_counts.get(cls_id, 0)
                visibility = "✓" if class_visibility.get(cls_id, True) else "✗"
                color = (0, 255, 0) if class_visibility.get(cls_id, True) else (0, 0, 255)

                cv2.putText(
                    img,
                    f"{visibility} {cls_name}: {count}",
                    (10, y_offset),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    color,
                    2,
                    cv2.LINE_AA,
                )
                y_offset += 30

            cv2.putText(
                img,
                f"Imagem: {current_idx + 1}/{total_images} - {os.path.basename(img_path)}",
                (10, y_offset),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 0),
                2,
                cv2.LINE_AA,
            )

            y_offset += 30
            cv2.putText(
                img,
                "Controles: 'n'=próx, 'p'=ant, 'q'=sair, '0'-'9'=alternar classe",
                (10, y_offset),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 0),
                2,
                cv2.LINE_AA,
            )

            # Salvar se diretório de saída especificado
            if output_dir and save_current:
                os.makedirs(output_dir, exist_ok=True)
                output_path = os.path.join(output_dir, f"annotated_{os.path.basename(img_path)}")
                cv2.imwrite(output_path, img)
                logger.info(f"Imagem anotada salva em {output_path}")
                save_current = False

            # Exibir a imagem
            scale = min(1.0, min(1200 / w, 800 / h))
            if scale < 1.0:
                img_display = cv2.resize(img, (int(w * scale), int(h * scale)))
            else:
                img_display = img.copy()

            cv2.imshow("Imagens Anotadas - Navegação", img_display)

            # Processar entrada do teclado
            key = cv2.waitKey(0) & 0xFF

            if key == ord("q"):  # Sair
                break
            elif key == ord("n"):  # Próxima imagem
                current_idx = (current_idx + 1) % total_images
            elif key == ord("p"):  # Imagem anterior
                current_idx = (current_idx - 1) % total_images
            elif key == ord("s"):  # Salvar imagem atual
                save_current = True
            elif key >= ord("0") and key <= ord("9"):  # Alternar visibilidade da classe
                cls_id = chr(key)
                if cls_id in class_visibility:
                    class_visibility[cls_id] = not class_visibility[cls_id]
            elif key == ord("a"):  # Mostrar todas as classes
                for cls_id in class_visibility:
                    class_visibility[cls_id] = True

        cv2.destroyAllWindows()
        logger.info("Visualização de anotações encerrada")

    def save_annotated_images(
        self,
        image_dir: str,
        label_dir: Optional[str] = None,
        output_dir: str = "annotated_images",
        filter_classes: Optional[Set[str]] = None,
    ) -> int:
        """
        Salva todas as imagens com suas anotações desenhadas.

        Args:
            image_dir: Diretório contendo as imagens
            label_dir: Diretório contendo os arquivos de anotação
            output_dir: Diretório para salvar as imagens anotadas
            filter_classes: Conjunto de IDs de classe para exibir

        Returns:
            Número de imagens anotadas salvas
        """
        os.makedirs(output_dir, exist_ok=True)

        # Obter todos os arquivos de imagem
        image_files = sorted(glob.glob(os.path.join(image_dir, "*.jpg")) + glob.glob(os.path.join(image_dir, "*.png")))

        if not image_files:
            logger.warning(f"Nenhum arquivo de imagem encontrado em {image_dir}")
            return 0

        # Rastrear quais classes mostrar
        class_visibility = {cls_id: True for cls_id in self.class_map.keys()}
        if filter_classes:
            class_visibility = {cls_id: (cls_id in filter_classes) for cls_id in self.class_map.keys()}

        saved_count = 0

        # Configurar barra de progresso
        print(f"Salvando {len(image_files)} imagens anotadas...")

        for img_path in image_files:
            img = cv2.imread(img_path)
            if img is None:
                logger.error(f"Erro: Não foi possível carregar a imagem {img_path}")
                continue

            h, w = img.shape[:2]

            # Encontrar arquivo de anotação correspondente
            base_name = os.path.splitext(os.path.basename(img_path))[0]
            if label_dir:
                label_path = os.path.join(label_dir, f"{base_name}.txt")
            else:
                label_path = os.path.join(os.path.dirname(img_path), f"{base_name}.txt")

            # Desenhar caixas se as anotações existirem
            if os.path.exists(label_path):
                with open(label_path, "r") as f:
                    annotations = f.readlines()

                # Desenhar cada anotação
                box_idx = 0
                for ann in annotations:
                    parts = ann.strip().split()
                    if len(parts) == 5:  # Formato YOLO: classe x_center y_center width height
                        cls, x_center, y_center, box_w, box_h = parts

                        # Pular se a classe for filtrada
                        if not class_visibility.get(cls, True):
                            continue

                        # Converter coordenadas normalizadas para valores de pixel
                        x_center = float(x_center) * w
                        y_center = float(y_center) * h
                        box_w = float(box_w) * w
                        box_h = float(box_h) * h

                        # Calcular pontos de canto
                        x1 = int(x_center - box_w / 2)
                        y1 = int(y_center - box_h / 2)
                        x2 = int(x_center + box_w / 2)
                        y2 = int(y_center + box_h / 2)

                        # Obter cor da classe
                        color = self.color_map.get(cls, (0, 255, 0))

                        # Desenhar retângulo
                        cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)

                        # Obter nome da classe para exibição
                        class_name = self.class_map.get(cls, f"Classe {cls}")

                        # Adicionar nome da classe e número de identificação
                        cv2.putText(
                            img,
                            f"{class_name} #{box_idx + 1}",
                            (x1, y1 - 5),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.5,
                            color,
                            1,
                            cv2.LINE_AA,
                        )

                        box_idx += 1

                # Salvar imagem anotada
                output_path = os.path.join(output_dir, f"annotated_{os.path.basename(img_path)}")
                cv2.imwrite(output_path, img)
                saved_count += 1

            else:
                logger.warning(f"Arquivo de anotação não encontrado para: {img_path}")

        logger.info(f"Processo concluído: {saved_count} imagens anotadas salvas em {output_dir}")
        return saved_count
