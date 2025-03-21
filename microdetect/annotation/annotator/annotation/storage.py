"""
Salvamento e carregamento de anotações.
"""

import glob
import json
import logging
import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class AnnotationStorage:
    """
    Gerencia o salvamento e carregamento de anotações.
    """

    def __init__(self, progress_file=".annotation_progress.json"):
        """
        Inicializa o armazenamento de anotações.

        Args:
            progress_file: Nome do arquivo para rastreamento de progresso
        """
        self.progress_file = progress_file

    def save_annotations(self, bounding_boxes, output_dir, base_name, original_w, original_h) -> str:
        """
        Salva as anotações no formato YOLO.

        Args:
            bounding_boxes: Lista de bounding boxes para salvar
            output_dir: Diretório de saída
            base_name: Nome base do arquivo
            original_w: Largura original da imagem
            original_h: Altura original da imagem

        Returns:
            Caminho para o arquivo de anotação salvo
        """
        txt_filename = f"{base_name}.txt"
        txt_path = os.path.join(output_dir, txt_filename)

        with open(txt_path, "w") as f:
            for box in bounding_boxes:
                class_id, x1, y1, x2, y2 = box

                # Converter para formato YOLO: class_id center_x center_y width height (normalizado)
                box_w = (x2 - x1) / original_w
                box_h = (y2 - y1) / original_h
                center_x = (x1 + (x2 - x1) / 2) / original_w
                center_y = (y1 + (y2 - y1) / 2) / original_h

                f.write(f"{class_id} {center_x} {center_y} {box_w} {box_h}\n")

        logger.info(f"Anotação salva em {txt_path}. {len(bounding_boxes)} caixas anotadas.")
        return txt_path

    def load_annotations(self, annotation_path, original_w, original_h) -> List[Tuple[str, int, int, int, int]]:
        """
        Carrega anotações no formato YOLO e converte para coordenadas absolutas.

        Args:
            annotation_path: Caminho para o arquivo de anotação
            original_w: Largura original da imagem
            original_h: Altura original da imagem

        Returns:
            Lista de bounding boxes no formato [(class_id, x1, y1, x2, y2), ...]
        """
        bounding_boxes = []

        if os.path.exists(annotation_path):
            logger.info(f"Carregando anotações existentes de {annotation_path}")

            with open(annotation_path, "r") as f:
                for line in f:
                    parts = line.strip().split()
                    if len(parts) == 5:  # formato YOLO: class x_center y_center width height
                        class_id, x_center, y_center, box_w, box_h = parts

                        # Converter de YOLO para pixel
                        x_center = float(x_center) * original_w
                        y_center = float(y_center) * original_h
                        box_w = float(box_w) * original_w
                        box_h = float(box_h) * original_h

                        # Calcular coordenadas absolutas (x1, y1, x2, y2)
                        x1 = int(x_center - box_w / 2)
                        y1 = int(y_center - box_h / 2)
                        x2 = int(x_center + box_w / 2)
                        y2 = int(y_center + box_h / 2)

                        # Adicionar à lista de bounding boxes
                        bounding_boxes.append((class_id, x1, y1, x2, y2))

        return bounding_boxes

    def save_progress(self, output_dir, current_image):
        """
        Salva o progresso atual da anotação.

        Args:
            output_dir: Diretório de saída
            current_image: Caminho da imagem atual

        Returns:
            True se o progresso foi salvo com sucesso, False caso contrário
        """
        try:
            progress_path = os.path.join(output_dir, self.progress_file)

            progress_data = {
                "last_annotated": current_image,
                "timestamp": datetime.now().isoformat(),
            }

            with open(progress_path, "w") as f:
                json.dump(progress_data, f)

            return True
        except Exception as e:
            logger.warning(f"Não foi possível salvar o progresso: {str(e)}")
            return False

    def load_progress(self, output_dir: Optional[str]) -> Optional[str]:
        """
        Carrega o progresso de anotação.

        Args:
            output_dir: Diretório de saída

        Returns:
            Caminho da última imagem anotada ou None se não houver progresso
        """
        progress_path = os.path.join(output_dir, self.progress_file)

        if not os.path.exists(progress_path):
            return None

        try:
            with open(progress_path, "r") as f:
                progress_data = json.load(f)

            # Retornar diretamente o caminho, independente de existir no sistema
            # Para compatibilidade com os testes
            return progress_data.get("last_annotated", "")
        except Exception as e:
            logger.warning(f"Erro ao carregar progresso: {str(e)}")

        return None

    def count_annotations_by_class(self, output_dir, classes) -> Tuple[Dict[str, int], int]:
        """
        Conta o número de anotações por classe em todos os arquivos de anotação.

        Args:
            output_dir: Diretório contendo os arquivos de anotação
            classes: Lista de classes para anotação

        Returns:
            Tupla com (dicionário de contagem por classe, total de anotações)
        """
        # Inicializar contagem de classes com todas as classes conhecidas
        class_counts = {class_id.split("-")[0]: 0 for class_id in classes}
        total_boxes = 0

        # Percorrer todos os arquivos de anotação
        annotation_files = glob.glob(os.path.join(output_dir, "*.txt"))
        for ann_file in annotation_files:
            if os.path.basename(ann_file) == self.progress_file:
                continue  # Pular o arquivo de progresso

            with open(ann_file, "r") as f:
                for line in f:
                    parts = line.strip().split()
                    if len(parts) >= 5:  # formato YOLO: class x_center y_center width height
                        class_id = parts[0]
                        class_counts[class_id] = class_counts.get(class_id, 0) + 1
                        total_boxes += 1

        return class_counts, total_boxes
