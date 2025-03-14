"""
Módulo para visualização de detecções em imagens.
"""

import json
import logging
import os
from typing import Any, Dict, List, Optional, Tuple

import cv2
import numpy as np
from ultralytics import YOLO

logger = logging.getLogger(__name__)


class DetectionVisualizer:
    """
    Classe para visualizar detecções em imagens.
    """

    def __init__(self, class_colors: Optional[Dict[int, Tuple[int, int, int]]] = None):
        """
        Inicializa o visualizador de detecções.

        Args:
            class_colors: Dicionário mapeando IDs de classe para cores RGB
        """
        # Cores padrão para diferentes classes (formato BGR para OpenCV)
        self.class_colors = class_colors or {
            0: (0, 255, 0),  # Verde
            1: (0, 0, 255),  # Vermelho
            2: (255, 0, 0),  # Azul
            3: (255, 255, 0),  # Ciano
            4: (255, 0, 255),  # Magenta
            5: (0, 255, 255),  # Amarelo
        }

    def generate_detection_overlay(
        self,
        image_path: str,
        detections: List[Dict[str, Any]],
        output_path: Optional[str] = None,
        conf_threshold: float = 0.25,
        show_labels: bool = True,
        line_thickness: int = 2,
        font_scale: float = 0.5,
    ) -> np.ndarray:
        """
        Gera uma imagem com sobreposição de caixas delimitadoras para detecções.

        Args:
            image_path: Caminho para a imagem de entrada
            detections: Lista de detecções (cada uma com 'bbox', 'class', 'conf')
            output_path: Caminho para salvar a imagem resultante (opcional)
            conf_threshold: Limiar de confiança para mostrar detecções
            show_labels: Se True, mostra rótulos de classe e confiança
            line_thickness: Espessura das linhas das caixas
            font_scale: Escala da fonte para os rótulos

        Returns:
            Imagem com sobreposições (array numpy)
        """
        # Carregar imagem
        image = cv2.imread(image_path)
        if image is None:
            logger.error(f"Não foi possível carregar a imagem: {image_path}")
            return None

        # Criar cópia para desenhar
        output_image = image.copy()

        # Desenhar cada detecção
        for detection in detections:
            # Verificar confiança
            confidence = detection.get("conf", 0)
            if confidence < conf_threshold:
                continue

            # Extrair informações
            bbox = detection.get("bbox", [0, 0, 0, 0])  # [x, y, width, height]
            class_id = detection.get("class", 0)

            # Converter para formato [x1, y1, x2, y2] se necessário
            if len(bbox) == 4 and isinstance(bbox[0], float) and bbox[0] <= 1.0:
                # Coordenadas normalizadas
                x, y, w, h = bbox
                height, width = output_image.shape[:2]
                x1 = int(x * width)
                y1 = int(y * height)
                x2 = int((x + w) * width)
                y2 = int((y + h) * height)
            else:
                # Coordenadas absolutas
                x1, y1, x2, y2 = bbox

            # Obter cor para a classe
            color = self.class_colors.get(class_id, (0, 255, 0))

            # Desenhar caixa delimitadora
            cv2.rectangle(output_image, (x1, y1), (x2, y2), color, line_thickness)

            # Adicionar rótulo
            if show_labels:
                label = f"{detection.get('name', f'Class {class_id}')} {confidence:.2f}"

                # Calcular tamanho do rótulo
                (label_width, label_height), baseline = cv2.getTextSize(
                    label, cv2.FONT_HERSHEY_SIMPLEX, font_scale, line_thickness
                )

                # Desenhar fundo para o rótulo
                cv2.rectangle(
                    output_image,
                    (x1, y1 - label_height - baseline - 5),
                    (x1 + label_width, y1),
                    color,
                    -1,  # -1 para preencher
                )

                # Desenhar texto
                cv2.putText(
                    output_image,
                    label,
                    (x1, y1 - baseline - 5),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    font_scale,
                    (255, 255, 255),  # Branco
                    line_thickness - 1,
                )

        # Salvar imagem resultante
        if output_path:
            os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
            cv2.imwrite(output_path, output_image)
            logger.info(f"Imagem com detecções salva em: {output_path}")

        return output_image

    def visualize_interactive(
        self, model_path: str, image_dir: str, conf_threshold: float = 0.25, iou_threshold: float = 0.45
    ) -> None:
        """
        Mostra uma interface interativa para visualizar detecções.

        Args:
            model_path: Caminho para o modelo treinado
            image_dir: Diretório com imagens para visualização
            conf_threshold: Limiar de confiança inicial
            iou_threshold: Limiar de IoU
        """
        try:
            import cv2
        except ImportError:
            logger.error("OpenCV é necessário para visualização interativa")
            return

        # Carregar o modelo
        model = YOLO(model_path)

        # Listar imagens no diretório
        image_files = [f for f in os.listdir(image_dir) if f.lower().endswith((".jpg", ".jpeg", ".png", ".bmp"))]

        if not image_files:
            logger.error(f"Nenhuma imagem encontrada em: {image_dir}")
            return

        image_files.sort()
        current_idx = 0
        current_conf = conf_threshold

        logger.info("Iniciando visualização interativa")
        logger.info("Pressione 'q' para sair, 'n' para próxima imagem, 'p' para anterior")
        logger.info("Use '+' para aumentar o limiar de confiança, '-' para diminuir")

        while True:
            # Obter imagem atual
            image_path = os.path.join(image_dir, image_files[current_idx])
            image = cv2.imread(image_path)

            if image is None:
                logger.warning(f"Não foi possível carregar: {image_path}")
                current_idx = (current_idx + 1) % len(image_files)
                continue

            # Executar detecção
            results = model(image, conf=current_conf, iou=iou_threshold)[0]

            # Converter resultados para o formato esperado
            detections = []
            if results.boxes is not None:
                for i in range(len(results.boxes)):
                    box = results.boxes[i]
                    x1, y1, x2, y2 = box.xyxy.cpu().numpy()[0]

                    detection = {
                        "bbox": [int(x1), int(y1), int(x2), int(y2)],
                        "class": int(box.cls.cpu().numpy()[0]),
                        "conf": float(box.conf.cpu().numpy()[0]),
                        "name": results.names[int(box.cls.cpu().numpy()[0])],
                    }
                    detections.append(detection)

            # Gerar imagem com overlays
            overlay_image = self.generate_detection_overlay(
                image_path, detections, conf_threshold=0, show_labels=True  # Já filtramos pelo conf_threshold no modelo
            )

            # Adicionar informações na imagem
            info_text = f"Imagem: {image_files[current_idx]} | Confiança: {current_conf:.2f} | {len(detections)} detecções"
            cv2.putText(overlay_image, info_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)
            cv2.putText(overlay_image, info_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 1)

            # Mostrar imagem
            cv2.imshow("MicroDetect - Visualização de Detecções", overlay_image)

            # Processar teclas
            key = cv2.waitKey(0) & 0xFF

            if key == ord("q"):
                break
            elif key == ord("n"):
                current_idx = (current_idx + 1) % len(image_files)
            elif key == ord("p"):
                current_idx = (current_idx - 1) % len(image_files)
            elif key == ord("+") or key == ord("="):
                current_conf = min(current_conf + 0.05, 1.0)
            elif key == ord("-") or key == ord("_"):
                current_conf = max(current_conf - 0.05, 0.05)

        cv2.destroyAllWindows()
        logger.info("Visualização interativa encerrada")

    def batch_visualization(
        self,
        model_path: str,
        image_dir: str,
        output_dir: str,
        conf_threshold: float = 0.25,
        iou_threshold: float = 0.45,
        image_size: int = 640,
    ) -> Dict[str, List[Dict]]:
        """
        Processa um lote de imagens e salva as visualizações com detecções.

        Args:
            model_path: Caminho para o modelo treinado
            image_dir: Diretório com imagens de entrada
            output_dir: Diretório para salvar imagens com detecções
            conf_threshold: Limiar de confiança
            iou_threshold: Limiar de IoU
            image_size: Tamanho da imagem para inferência

        Returns:
            Dicionário com resultados por imagem
        """
        # Carregar o modelo
        model = YOLO(model_path)

        # Listar imagens no diretório
        image_files = [f for f in os.listdir(image_dir) if f.lower().endswith((".jpg", ".jpeg", ".png", ".bmp"))]

        if not image_files:
            logger.error(f"Nenhuma imagem encontrada em: {image_dir}")
            return {}

        # Criar diretório de saída
        os.makedirs(output_dir, exist_ok=True)

        # Resultados por imagem
        all_results = {}

        # Processar cada imagem
        for i, image_file in enumerate(image_files):
            logger.info(f"Processando imagem {i + 1}/{len(image_files)}: {image_file}")

            # Caminhos
            image_path = os.path.join(image_dir, image_file)
            output_path = os.path.join(output_dir, image_file)

            # Verificar se a imagem existe
            if not os.path.exists(image_path):
                logger.warning(f"Imagem não encontrada: {image_path}")
                continue

            # Executar detecção
            results = model(image_path, conf=conf_threshold, iou=iou_threshold, size=image_size)[0]

            # Converter resultados para o formato esperado
            detections = []
            if results.boxes is not None:
                for i in range(len(results.boxes)):
                    box = results.boxes[i]
                    x1, y1, x2, y2 = box.xyxy.cpu().numpy()[0]

                    detection = {
                        "bbox": [int(x1), int(y1), int(x2), int(y2)],
                        "class": int(box.cls.cpu().numpy()[0]),
                        "conf": float(box.conf.cpu().numpy()[0]),
                        "name": results.names[int(box.cls.cpu().numpy()[0])],
                    }
                    detections.append(detection)

            # Gerar e salvar imagem com detecções
            self.generate_detection_overlay(image_path, detections, output_path)

            # Armazenar resultados
            all_results[image_file] = detections

        # Salvar resultados em formato JSON
        json_path = os.path.join(output_dir, "detection_results.json")
        with open(json_path, "w") as f:
            json.dump(all_results, f, indent=4)

        logger.info(f"Processamento em lote concluído. {len(image_files)} imagens processadas.")
        return all_results
