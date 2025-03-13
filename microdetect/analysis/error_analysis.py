"""
Módulo para análise detalhada de erros de detecção.
"""

import json
import logging
import os
from typing import Any, Dict, List

import cv2
import matplotlib.pyplot as plt
import numpy as np
from ultralytics import YOLO

logger = logging.getLogger(__name__)


class ErrorAnalyzer:
    """
    Classe para analisar erros de detecção em modelos YOLO.
    """

    def __init__(self, output_dir: str = None):
        """
        Inicializa o analisador de erros.

        Args:
            output_dir: Diretório para salvar os resultados da análise
        """
        self.output_dir = output_dir or "error_analysis"
        os.makedirs(self.output_dir, exist_ok=True)

    def analyze_errors(
        self,
        model_path: str,
        data_yaml: str,
        dataset_dir: str,
        error_type: str = "all",
        conf_threshold: float = 0.25,
        iou_threshold: float = 0.5,
        max_samples: int = 20,
    ) -> Dict[str, Any]:
        """
        Analisa diferentes tipos de erros de detecção.

        Args:
            model_path: Caminho para o modelo treinado
            data_yaml: Caminho para o arquivo de configuração do dataset
            dataset_dir: Diretório com imagens e anotações de teste
            error_type: Tipo de erro a analisar (false_positives, false_negatives,
                       classification_errors, localization_errors, all)
            conf_threshold: Limiar de confiança para detecções
            iou_threshold: Limiar de IoU para correspondência
            max_samples: Número máximo de exemplos a salvar

        Returns:
            Dicionário com resultados da análise
        """
        # Criar diretórios para cada tipo de erro
        error_dirs = {
            "false_positives": os.path.join(self.output_dir, "false_positives"),
            "false_negatives": os.path.join(self.output_dir, "false_negatives"),
            "classification_errors": os.path.join(self.output_dir, "classification_errors"),
            "localization_errors": os.path.join(self.output_dir, "localization_errors"),
        }

        for dir_name in error_dirs.values():
            os.makedirs(dir_name, exist_ok=True)

        # Carregar modelo
        model = YOLO(model_path)

        # Estrutura para armazenar caminhos de imagens com erros
        error_examples = {k: [] for k in error_dirs.keys()}
        error_counts = {k: 0 for k in error_dirs.keys()}

        # Diretório de imagens de teste
        test_images_dir = os.path.join(dataset_dir, "test", "images")
        test_labels_dir = os.path.join(dataset_dir, "test", "labels")

        if not os.path.exists(test_images_dir) or not os.path.exists(test_labels_dir):
            logger.error(f"Diretórios de teste não encontrados: {test_images_dir} ou {test_labels_dir}")
            return {"error": "Diretórios de teste não encontrados"}

        # Listar imagens de teste
        image_files = [f for f in os.listdir(test_images_dir) if f.lower().endswith((".jpg", ".jpeg", ".png", ".bmp"))]

        if not image_files:
            logger.error(f"Nenhuma imagem encontrada em: {test_images_dir}")
            return {"error": "Nenhuma imagem encontrada"}

        # Carregar mapeamento de IDs de classe para nomes (do arquivo data.yaml)
        import yaml

        with open(data_yaml, "r") as f:
            data_config = yaml.safe_load(f)

        class_names = data_config.get("names", {})

        # Analisar cada imagem
        for image_file in image_files:
            base_name = os.path.splitext(image_file)[0]
            image_path = os.path.join(test_images_dir, image_file)
            label_path = os.path.join(test_labels_dir, base_name + ".txt")

            # Verificar se o arquivo de anotação existe
            if not os.path.exists(label_path):
                logger.warning(f"Arquivo de anotação não encontrado: {label_path}")
                continue

            # Carregar anotações (ground truth)
            ground_truth = self._load_yolo_annotations(label_path, class_names)

            # Realizar detecção
            results = model(image_path, conf=conf_threshold, iou=iou_threshold)[0]

            # Extrair detecções
            detections = []
            if results.boxes is not None:
                boxes = results.boxes
                for i in range(len(boxes)):
                    box = boxes[i]
                    x1, y1, x2, y2 = box.xyxy.cpu().numpy()[0]  # Formato absoluto
                    cls = int(box.cls.cpu().numpy()[0])
                    conf = float(box.conf.cpu().numpy()[0])

                    # Obter dimensões da imagem
                    img = cv2.imread(image_path)
                    if img is None:
                        logger.warning(f"Não foi possível carregar a imagem: {image_path}")
                        continue

                    height, width = img.shape[:2]

                    # Converter para formato normalizado (centro_x, centro_y, largura, altura)
                    center_x = (x1 + x2) / 2 / width
                    center_y = (y1 + y2) / 2 / height
                    bbox_width = (x2 - x1) / width
                    bbox_height = (y2 - y1) / height

                    detections.append(
                        {
                            "bbox": [center_x, center_y, bbox_width, bbox_height],
                            "bbox_abs": [int(x1), int(y1), int(x2), int(y2)],
                            "class": cls,
                            "class_name": results.names.get(cls, f"Class {cls}"),
                            "confidence": conf,
                        }
                    )

            # Identificar diferentes tipos de erros
            identified_errors = self._identify_errors(image_path, detections, ground_truth, iou_threshold)

            # Atualizar contagens
            for error_type, errors in identified_errors.items():
                error_counts[error_type] += len(errors)

                # Armazenar exemplos (até o limite)
                if len(error_examples[error_type]) < max_samples and errors:
                    error_examples[error_type].append({"image_path": image_path, "errors": errors})

        # Gerar visualizações para cada tipo de erro
        for error_type, examples in error_examples.items():
            if not examples:
                continue

            # Gerar e salvar visualizações
            for i, example in enumerate(examples):
                self._visualize_error(
                    example["image_path"],
                    example["errors"],
                    os.path.join(error_dirs[error_type], f"example_{i + 1}.png"),
                    error_type,
                )

        # Gerar gráfico de resumo
        summary_path = self._generate_error_summary(error_counts)

        # Salvar relatório detalhado
        report_path = os.path.join(self.output_dir, "error_analysis_report.json")
        with open(report_path, "w") as f:
            json.dump(
                {
                    "model": os.path.basename(model_path),
                    "conf_threshold": conf_threshold,
                    "iou_threshold": iou_threshold,
                    "images_analyzed": len(image_files),
                    "error_counts": error_counts,
                    "error_examples": {k: len(v) for k, v in error_examples.items()},
                    "summary_chart": summary_path,
                },
                f,
                indent=4,
            )

        return {
            "error_counts": error_counts,
            "error_examples": {k: len(v) for k, v in error_examples.items()},
            "report_path": report_path,
            "summary_chart": summary_path,
            "output_dir": self.output_dir,
        }

    def _load_yolo_annotations(self, label_path: str, class_names: Dict[int, str]) -> List[Dict[str, Any]]:
        """
        Carrega anotações no formato YOLO.

        Args:
            label_path: Caminho para o arquivo de anotações
            class_names: Dicionário mapeando IDs de classe para nomes

        Returns:
            Lista de anotações
        """
        annotations = []

        with open(label_path, "r") as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) >= 5:
                    cls = int(parts[0])
                    center_x = float(parts[1])
                    center_y = float(parts[2])
                    width = float(parts[3])
                    height = float(parts[4])

                    annotations.append(
                        {
                            "bbox": [center_x, center_y, width, height],
                            "class": cls,
                            "class_name": class_names.get(cls, f"Class {cls}"),
                        }
                    )

        return annotations

    def _calculate_iou(self, box1: List[float], box2: List[float]) -> float:
        """
        Calcula IoU (Intersection over Union) entre duas caixas.

        Args:
            box1: Caixa 1 no formato [center_x, center_y, width, height]
            box2: Caixa 2 no formato [center_x, center_y, width, height]

        Returns:
            Valor de IoU
        """

        # Converter de [center_x, center_y, width, height] para [x1, y1, x2, y2]
        def to_xyxy(box):
            center_x, center_y, width, height = box
            x1 = center_x - width / 2
            y1 = center_y - height / 2
            x2 = center_x + width / 2
            y2 = center_y + height / 2
            return [x1, y1, x2, y2]

        box1_xyxy = to_xyxy(box1)
        box2_xyxy = to_xyxy(box2)

        # Calcular coordenadas da interseção
        xi1 = max(box1_xyxy[0], box2_xyxy[0])
        yi1 = max(box1_xyxy[1], box2_xyxy[1])
        xi2 = min(box1_xyxy[2], box2_xyxy[2])
        yi2 = min(box1_xyxy[3], box2_xyxy[3])

        # Verificar se há interseção
        if xi2 < xi1 or yi2 < yi1:
            return 0.0

        # Calcular áreas
        inter_area = (xi2 - xi1) * (yi2 - yi1)
        box1_area = (box1_xyxy[2] - box1_xyxy[0]) * (box1_xyxy[3] - box1_xyxy[1])
        box2_area = (box2_xyxy[2] - box2_xyxy[0]) * (box2_xyxy[3] - box2_xyxy[1])

        # Calcular IoU
        union_area = box1_area + box2_area - inter_area
        iou = inter_area / union_area if union_area > 0 else 0.0

        return iou

    def _identify_errors(
        self, image_path: str, detections: List[Dict[str, Any]], ground_truth: List[Dict[str, Any]], iou_threshold: float
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Identifica diferentes tipos de erros de detecção.

        Args:
            image_path: Caminho para a imagem
            detections: Lista de detecções do modelo
            ground_truth: Lista de anotações ground truth
            iou_threshold: Limiar de IoU para correspondência

        Returns:
            Dicionário com erros identificados por tipo
        """
        # Criar cópias das listas para manipulação
        remaining_dets = list(detections)
        remaining_gt = list(ground_truth)

        # Estrutura para armazenar erros
        errors = {"false_positives": [], "false_negatives": [], "classification_errors": [], "localization_errors": []}

        # Matriz de IoU entre detecções e ground truth
        iou_matrix = np.zeros((len(detections), len(ground_truth)))
        for i, det in enumerate(detections):
            for j, gt in enumerate(ground_truth):
                iou_matrix[i, j] = self._calculate_iou(det["bbox"], gt["bbox"])

        # Encontrar correspondências
        matched_dets = []
        matched_gt = []

        # Para cada detecção, encontrar o ground truth com maior IoU
        for i, det in enumerate(detections):
            if len(ground_truth) == 0:
                continue

            # Encontrar o ground truth com maior IoU
            best_gt_idx = np.argmax(iou_matrix[i, :])
            best_iou = iou_matrix[i, best_gt_idx]
            best_gt = ground_truth[best_gt_idx]

            # Verificar se é uma correspondência válida
            if best_iou >= iou_threshold:
                matched_dets.append(i)
                matched_gt.append(best_gt_idx)

                # Verificar se é um erro de classificação
                if det["class"] != best_gt["class"]:
                    errors["classification_errors"].append({"detection": det, "ground_truth": best_gt, "iou": best_iou})

                # Verificar se é um erro de localização (IoU < 0.7)
                elif best_iou < 0.7:
                    errors["localization_errors"].append({"detection": det, "ground_truth": best_gt, "iou": best_iou})

        # Identificar falsos positivos
        for i, det in enumerate(detections):
            if i not in matched_dets:
                errors["false_positives"].append({"detection": det})

        # Identificar falsos negativos
        for j, gt in enumerate(ground_truth):
            if j not in matched_gt:
                errors["false_negatives"].append({"ground_truth": gt})

        return errors

    def _visualize_error(self, image_path: str, errors: List[Dict[str, Any]], output_path: str, error_type: str) -> None:
        """
        Visualiza erros em uma imagem.

        Args:
            image_path: Caminho para a imagem
            errors: Lista de erros a serem visualizados
            output_path: Caminho para salvar a imagem com visualização
            error_type: Tipo de erro (para ajustar cores e estilo)
        """
        # Carregar imagem
        img = cv2.imread(image_path)
        if img is None:
            logger.warning(f"Não foi possível carregar a imagem: {image_path}")
            return

        height, width = img.shape[:2]

        # Definir cores para cada tipo de erro
        colors = {
            "false_positives": (0, 0, 255),  # Vermelho
            "false_negatives": (0, 255, 0),  # Verde
            "classification_errors": (255, 0, 0),  # Azul
            "localization_errors": (255, 255, 0),  # Ciano
        }

        # Desenhar erros
        for error in errors:
            if error_type == "false_positives":
                # Desenhar detecção falso positivo
                det = error["detection"]
                bbox_abs = det.get("bbox_abs")

                if not bbox_abs:
                    # Converter de normalizado para absoluto
                    cx, cy, w, h = det["bbox"]
                    x1 = int((cx - w / 2) * width)
                    y1 = int((cy - h / 2) * height)
                    x2 = int((cx + w / 2) * width)
                    y2 = int((cy + h / 2) * height)
                    bbox_abs = [x1, y1, x2, y2]

                cv2.rectangle(img, (bbox_abs[0], bbox_abs[1]), (bbox_abs[2], bbox_abs[3]), colors[error_type], 2)

                label = f"FP: {det['class_name']} ({det['confidence']:.2f})"
                cv2.putText(img, label, (bbox_abs[0], bbox_abs[1] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, colors[error_type], 2)

            elif error_type == "false_negatives":
                # Desenhar ground truth não detectado
                gt = error["ground_truth"]
                cx, cy, w, h = gt["bbox"]
                x1 = int((cx - w / 2) * width)
                y1 = int((cy - h / 2) * height)
                x2 = int((cx + w / 2) * width)
                y2 = int((cy + h / 2) * height)

                cv2.rectangle(img, (x1, y1), (x2, y2), colors[error_type], 2)

                label = f"FN: {gt['class_name']}"
                cv2.putText(img, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, colors[error_type], 2)

            elif error_type == "classification_errors":
                # Desenhar erro de classificação
                det = error["detection"]
                gt = error["ground_truth"]

                bbox_abs = det.get("bbox_abs")
                if not bbox_abs:
                    cx, cy, w, h = det["bbox"]
                    x1 = int((cx - w / 2) * width)
                    y1 = int((cy - h / 2) * height)
                    x2 = int((cx + w / 2) * width)
                    y2 = int((cy + h / 2) * height)
                    bbox_abs = [x1, y1, x2, y2]

                cv2.rectangle(img, (bbox_abs[0], bbox_abs[1]), (bbox_abs[2], bbox_abs[3]), colors[error_type], 2)

                label = f"CE: {det['class_name']} (GT: {gt['class_name']})"
                cv2.putText(img, label, (bbox_abs[0], bbox_abs[1] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, colors[error_type], 2)

            elif error_type == "localization_errors":
                # Desenhar erro de localização
                det = error["detection"]
                gt = error["ground_truth"]

                # Desenhar detecção
                bbox_abs = det.get("bbox_abs")
                if not bbox_abs:
                    cx, cy, w, h = det["bbox"]
                    x1 = int((cx - w / 2) * width)
                    y1 = int((cy - h / 2) * height)
                    x2 = int((cx + w / 2) * width)
                    y2 = int((cy + h / 2) * height)
                    bbox_abs = [x1, y1, x2, y2]

                cv2.rectangle(img, (bbox_abs[0], bbox_abs[1]), (bbox_abs[2], bbox_abs[3]), colors[error_type], 2)

                # Desenhar ground truth
                cx, cy, w, h = gt["bbox"]
                x1_gt = int((cx - w / 2) * width)
                y1_gt = int((cy - h / 2) * height)
                x2_gt = int((cx + w / 2) * width)
                y2_gt = int((cy + h / 2) * height)

                cv2.rectangle(img, (x1_gt, y1_gt), (x2_gt, y2_gt), (0, 255, 0), 1)  # Verde

                label = f"LE: IoU={error['iou']:.2f}"
                cv2.putText(img, label, (bbox_abs[0], bbox_abs[1] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, colors[error_type], 2)

        # Adicionar título
        title = f"{error_type.replace('_', ' ').title()}: {len(errors)} encontrados"
        cv2.putText(img, title, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 3)
        cv2.putText(img, title, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 1)

        # Salvar imagem
        cv2.imwrite(output_path, img)

    def _generate_error_summary(self, error_counts: Dict[str, int]) -> str:
        """
        Gera um gráfico de resumo dos erros.

        Args:
            error_counts: Dicionário com contagens de erros por tipo

        Returns:
            Caminho para o gráfico gerado
        """
        # Preparar dados
        error_types = list(error_counts.keys())
        counts = [error_counts[et] for et in error_types]

        # Cores para cada tipo de erro
        colors = ["#FF6B6B", "#4ECDC4", "#1A535C", "#FFE66D"]

        # Criar figura
        plt.figure(figsize=(10, 6))
        bars = plt.bar(range(len(error_types)), counts, color=colors)
        plt.xticks(range(len(error_types)), [et.replace("_", " ").title() for et in error_types])
        plt.title("Resumo de Erros de Detecção")
        plt.ylabel("Contagem")

        # Adicionar valores nas barras
        for bar in bars:
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width() / 2.0, height + 0.1, str(int(height)), ha="center", va="bottom")

        # Adicionar total
        total = sum(counts)
        plt.figtext(0.5, 0.01, f"Total de erros: {total}", ha="center", fontsize=12)

        # Salvar figura
        summary_path = os.path.join(self.output_dir, "error_summary.png")
        plt.tight_layout()
        plt.savefig(summary_path)
        plt.close()

        return summary_path
