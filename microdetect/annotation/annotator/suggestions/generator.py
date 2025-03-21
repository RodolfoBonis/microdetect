"""
Geração de sugestões automáticas para anotações com suporte a modelos YOLO
e métodos de visão computacional.
"""

import logging
import os
import random
from typing import Any, Dict, List, Optional, Tuple

import cv2
import numpy as np

logger = logging.getLogger(__name__)


class SuggestionGenerator:
    """
    Gera sugestões automáticas para anotações usando modelos YOLO ou
    métodos de visão computacional.
    """

    def __init__(self, classes, yolo_model_path: Optional[str] = None, use_cv_fallback: bool = True):
        """
        Inicializa o gerador de sugestões.

        Args:
            classes: Lista de classes disponíveis para anotação
            yolo_model_path: Caminho para o modelo YOLO (opcional)
            use_cv_fallback: Se True, usa métodos de visão computacional quando o modelo não estiver disponível
        """
        self.classes = classes
        self.yolo_model_path = yolo_model_path
        self.use_cv_fallback = use_cv_fallback
        self.model = None
        self._load_model()

    def _load_model(self) -> bool:
        """
        Carrega o modelo YOLO se disponível.

        Returns:
            True se o modelo foi carregado com sucesso, False caso contrário
        """
        if not self.yolo_model_path or not os.path.exists(self.yolo_model_path):
            logger.info("Modelo YOLO não encontrado. Usando métodos alternativos de visão computacional.")
            return False

        try:
            # Tenta importar o ultralytics para YOLO v8
            import ultralytics
            from ultralytics import YOLO

            # Verificar versão do ultralytics
            logger.info(f"Usando ultralytics versão: {ultralytics.__version__}")

            # Carregar o modelo YOLO
            self.model = YOLO(self.yolo_model_path)
            logger.info(f"Modelo YOLO carregado de {self.yolo_model_path}")

            return True
        except ImportError:
            logger.warning("Biblioteca ultralytics não encontrada. Instale com 'pip install ultralytics'")
            return False
        except Exception as e:
            logger.error(f"Erro ao carregar modelo YOLO: {str(e)}")
            return False

    def _detect_with_yolo(self, img_rgb: np.ndarray, confidence: float) -> List[Tuple[str, int, int, int, int]]:
        """
        Detecta objetos na imagem usando o modelo YOLO.

        Args:
            img_rgb: Imagem RGB como numpy array
            confidence: Limiar de confiança para as detecções

        Returns:
            Lista de bounding boxes no formato [(class_id, x1, y1, x2, y2), ...]
        """
        suggested_boxes = []

        try:
            # Executar detecção
            results = self.model(img_rgb, conf=confidence)

            # Processar resultados
            for result in results:
                for box in result.boxes:
                    # Extrair classe e coordenadas
                    class_idx = int(box.cls.item())
                    class_name = result.names[class_idx]

                    # Mapear para as classes disponíveis no anotador
                    class_id = self._map_yolo_class_to_annotator(class_name)
                    if class_id is None:
                        continue  # Pular se não conseguir mapear

                    # Obter coordenadas (formato xyxy)
                    x1, y1, x2, y2 = map(int, box.xyxy.cpu().numpy()[0])

                    # Adicionar à lista de sugestões
                    suggested_boxes.append((class_id, x1, y1, x2, y2))

            logger.info(f"YOLO detectou {len(suggested_boxes)} objetos com confiança >= {confidence}")
            return suggested_boxes

        except Exception as e:
            logger.error(f"Erro na detecção com YOLO: {str(e)}")
            return []

    def _map_yolo_class_to_annotator(self, yolo_class: str) -> Optional[str]:
        """
        Mapeia uma classe do modelo YOLO para uma classe do anotador.

        Args:
            yolo_class: Nome da classe no modelo YOLO

        Returns:
            ID da classe no anotador ou None se não houver correspondência
        """
        # Normalizar o nome da classe para comparação
        yolo_class_lower = yolo_class.lower()

        # Procurar correspondência nas classes disponíveis
        for cls in self.classes:
            cls_id, cls_name = cls.split("-") if "-" in cls else (cls, cls)
            if cls_name.lower() in yolo_class_lower or yolo_class_lower in cls_name.lower():
                return cls_id

        # Se não encontrar correspondência direta, tentar correspondências aproximadas
        for keyword, class_id in [
            (("levedura", "yeast"), "0"),
            (("fungo", "fungus", "fungi"), "1"),
            (("alga", "microalga"), "2"),
        ]:
            if any(k in yolo_class_lower for k in keyword):
                return class_id

        # Se não encontrar, retornar a primeira classe disponível
        return self.classes[0].split("-")[0] if self.classes else None

    def _detect_with_cv(self, img_rgb: np.ndarray) -> List[Tuple[str, int, int, int, int]]:
        """
        Detecta microorganismos usando técnicas avançadas de visão computacional.

        Args:
            img_rgb: Imagem RGB como numpy array

        Returns:
            Lista de bounding boxes no formato [(class_id, x1, y1, x2, y2), ...]
        """
        suggested_boxes = []

        try:
            # Análise inicial das características da imagem para adaptar parâmetros
            h, w = img_rgb.shape[:2]
            img_mean = np.mean(img_rgb)
            img_std = np.std(img_rgb)
            is_dark_image = img_mean < 100
            is_low_contrast = img_std < 30

            logger.info(
                f"Características da imagem: média={img_mean:.1f}, std={img_std:.1f}, "
                + f"dimensões={w}x{h}, {'baixo contraste' if is_low_contrast else 'contraste normal'}"
            )

            # Converter para escala de cinza
            img_gray = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2GRAY)

            # Pré-processamento adaptativo baseado nas características da imagem
            preprocessed_imgs = self._adaptive_preprocessing(img_gray, is_dark_image, is_low_contrast)

            # 1. Detecção por múltiplos métodos de segmentação
            segmentation_results = []

            for prep_name, prep_img in preprocessed_imgs.items():
                # Aplicar diversos métodos de segmentação
                segmented_imgs = self._multi_segmentation(prep_img)

                for seg_name, seg_img in segmented_imgs.items():
                    # Encontrar contornos
                    contours, _ = cv2.findContours(seg_img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

                    # Filtrar contornos com critérios mais sofisticados
                    valid_contours = self._filter_contours(contours, img_rgb)

                    segmentation_results.append({"method": f"{prep_name}_{seg_name}", "contours": valid_contours})

                    logger.debug(f"Método {prep_name}_{seg_name}: {len(valid_contours)} contornos válidos")

            # 2. Detecção específica para diferentes tipos de microorganismos

            # 2.1 Detecção de leveduras (formas circulares/ovais)
            yeast_candidates = self._detect_yeasts(img_gray, preprocessed_imgs["enhanced"])

            # 2.2 Detecção de fungos (estruturas filamentosas)
            fungi_candidates = self._detect_fungi(img_gray, preprocessed_imgs["enhanced"])

            # 2.3 Detecção de microalgas
            algae_candidates = self._detect_algae(img_rgb, preprocessed_imgs["enhanced"])

            # 3. Combinar e filtrar resultados para reduzir duplicatas
            all_boxes = []

            # Adicionar caixas de segmentação geral
            for result in segmentation_results:
                for contour in result["contours"]:
                    x, y, box_w, box_h = cv2.boundingRect(contour)

                    # Extrair região de interesse para classificação
                    roi = img_rgb[y : y + box_h, x : x + box_w]

                    # Ignorar ROIs muito pequenas para análise
                    if roi.size <= 0 or box_w < 5 or box_h < 5:
                        continue

                    # Classificar com base em múltiplas características
                    class_id, confidence = self._advanced_classification(roi, contour)

                    # Adicionar apenas se a confiança for razoável
                    if confidence > 0.4:
                        all_boxes.append(
                            {
                                "coords": (int(x), int(y), int(x + box_w), int(y + box_h)),
                                "class_id": class_id,
                                "confidence": confidence,
                                "size": box_w * box_h,
                            }
                        )

            # Adicionar detecções específicas de cada tipo
            for coords, conf in yeast_candidates:
                x1, y1, x2, y2 = coords
                all_boxes.append(
                    {
                        "coords": (int(x1), int(y1), int(x2), int(y2)),
                        "class_id": "0",  # Levedura
                        "confidence": conf,
                        "size": (x2 - x1) * (y2 - y1),
                    }
                )

            for coords, conf in fungi_candidates:
                x1, y1, x2, y2 = coords
                all_boxes.append(
                    {
                        "coords": (int(x1), int(y1), int(x2), int(y2)),
                        "class_id": "1",  # Fungo
                        "confidence": conf,
                        "size": (x2 - x1) * (y2 - y1),
                    }
                )

            for coords, conf in algae_candidates:
                x1, y1, x2, y2 = coords
                all_boxes.append(
                    {
                        "coords": (int(x1), int(y1), int(x2), int(y2)),
                        "class_id": "2",  # Microalga
                        "confidence": conf,
                        "size": (x2 - x1) * (y2 - y1),
                    }
                )

            # Remover duplicatas usando Non-Maximum Suppression (NMS)
            final_boxes = self._apply_nms(all_boxes)

            # Converter para o formato final
            for box in final_boxes:
                x1, y1, x2, y2 = box["coords"]
                class_id = box["class_id"]
                suggested_boxes.append((class_id, x1, y1, x2, y2))

            logger.info(f"Detectados {len(suggested_boxes)} objetos após processamento e filtragem")

            # Se ainda não encontrou nada, tente um método mais agressivo
            if len(suggested_boxes) < 2:
                logger.info("Poucos objetos detectados, aplicando método mais sensível")
                emergency_boxes = self._emergency_detection(img_rgb)
                suggested_boxes.extend(emergency_boxes)

            return suggested_boxes

        except Exception as e:
            logger.error(f"Erro na detecção com visão computacional: {str(e)}")
            return []

    def _adaptive_preprocessing(self, img_gray: np.ndarray, is_dark: bool, is_low_contrast: bool) -> Dict[str, np.ndarray]:
        """
        Aplica pré-processamento adaptativo com base nas características da imagem.

        Args:
            img_gray: Imagem em escala de cinza
            is_dark: Se a imagem tem baixa luminosidade
            is_low_contrast: Se a imagem tem baixo contraste

        Returns:
            Dicionário com diferentes versões pré-processadas da imagem
        """
        results = {}

        # Versão normalizada - útil para imagens com problemas de iluminação
        normalized = cv2.normalize(img_gray, None, 0, 255, cv2.NORM_MINMAX)
        results["normalized"] = normalized

        # Aplicar desfoque para redução de ruído
        # Use bilateral filter para preservar bordas
        blur = cv2.bilateralFilter(img_gray, 9, 75, 75)
        results["blur"] = blur

        # Aplicar CLAHE com parâmetros adaptados
        clip_limit = 3.0 if is_low_contrast else 2.0
        clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=(8, 8))
        clahe_result = clahe.apply(blur)
        results["clahe"] = clahe_result

        # Versão aprimorada combinando as técnicas
        enhanced = clahe_result.copy()

        # Para imagens escuras, aplique correção gama
        if is_dark:
            # Correção gama: valores menores que 1 aumentam o brilho de regiões escuras
            gamma = 0.7
            inv_gamma = 1.0 / gamma
            table = np.array([((i / 255.0) ** inv_gamma) * 255 for i in range(256)], dtype=np.uint8)
            enhanced = cv2.LUT(enhanced, table)

        # Para imagens de baixo contraste, reforce as bordas
        if is_low_contrast:
            # Detector de bordas Sobel
            sobel_x = cv2.Sobel(enhanced, cv2.CV_64F, 1, 0, ksize=3)
            sobel_y = cv2.Sobel(enhanced, cv2.CV_64F, 0, 1, ksize=3)

            # Combinar os gradientes
            magnitude = cv2.magnitude(sobel_x, sobel_y)
            magnitude = cv2.normalize(magnitude, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)

            # Misturar a imagem original com as bordas para realçá-las
            edge_enhanced = cv2.addWeighted(enhanced, 0.7, magnitude, 0.3, 0)
            enhanced = edge_enhanced

        results["enhanced"] = enhanced

        return results

    def _multi_segmentation(self, img: np.ndarray) -> Dict[str, np.ndarray]:
        """
        Aplica múltiplos métodos de segmentação para detectar diferentes tipos de estruturas.

        Args:
            img: Imagem pré-processada em escala de cinza

        Returns:
            Dicionário com diferentes resultados de segmentação
        """
        results = {}

        # 1. Limiarização adaptativa - boa para detecção de objetos locais
        adaptive_thresh = cv2.adaptiveThreshold(img, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2)
        results["adaptive"] = adaptive_thresh

        # 2. Limiarização de Otsu - bom para separação bimodal (fundo vs objetos)
        _, otsu_thresh = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        results["otsu"] = otsu_thresh

        # 3. Limiarização multi-level (K-Means) - útil para diferentes intensidades
        try:
            # Converter para float32 para K-means
            img_float = img.astype(np.float32)
            # Reshape para vetor unidimensional
            pixels = img_float.reshape((-1, 1))

            # Defina critérios e aplique K-means
            criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 100, 0.2)
            _, labels, centers = cv2.kmeans(pixels, 3, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)

            # Converter de volta para formato de imagem
            segmented = labels.reshape(img.shape).astype(np.uint8)

            # Limiarizar os resultados do K-means para obter uma máscara binária
            # Selecionamos o cluster mais escuro (geralmente os microorganismos)
            darkest_cluster = np.argmin(centers)
            kmeans_mask = (segmented == darkest_cluster).astype(np.uint8) * 255

            results["kmeans"] = kmeans_mask
        except Exception as e:
            logger.debug(f"K-means falhou: {e}")

        # 4. Watershed para separar objetos agrupados
        try:
            # Processamento para watershed
            # Crie marcadores usando operações morfológicas
            kernel = np.ones((3, 3), np.uint8)
            opening = cv2.morphologyEx(otsu_thresh, cv2.MORPH_OPEN, kernel, iterations=2)

            # Certeza de fundo - dilatação
            sure_bg = cv2.dilate(opening, kernel, iterations=3)

            # Certeza de primeiro plano - transformação de distância
            dist_transform = cv2.distanceTransform(opening, cv2.DIST_L2, 5)
            _, sure_fg = cv2.threshold(dist_transform, 0.5 * dist_transform.max(), 255, 0)
            sure_fg = sure_fg.astype(np.uint8)

            # Região desconhecida
            unknown = cv2.subtract(sure_bg, sure_fg)

            # Rotulagem
            _, markers = cv2.connectedComponents(sure_fg)
            markers = markers + 1
            markers[unknown == 255] = 0

            # Aplicar watershed
            img_color = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
            cv2.watershed(img_color, markers)

            # Extrair objetos do watershed (valores > 1)
            watershed_mask = (markers > 1).astype(np.uint8) * 255

            results["watershed"] = watershed_mask
        except Exception as e:
            logger.debug(f"Watershed falhou: {e}")

        # Pós-processamento para todos os resultados
        for key in results:
            # Remover pequenos ruídos com abertura morfológica
            kernel = np.ones((3, 3), np.uint8)
            results[key] = cv2.morphologyEx(results[key], cv2.MORPH_OPEN, kernel, iterations=1)

            # Preencher pequenos buracos nos objetos
            results[key] = cv2.morphologyEx(results[key], cv2.MORPH_CLOSE, kernel, iterations=2)

        return results

    def _filter_contours(self, contours: List[np.ndarray], img_rgb: np.ndarray) -> List[np.ndarray]:
        """
        Filtra contornos baseado em múltiplos critérios para reduzir falsos positivos.

        Args:
            contours: Lista de contornos detectados
            img_rgb: Imagem RGB original

        Returns:
            Lista de contornos filtrados
        """
        h, w = img_rgb.shape[:2]
        img_area = w * h

        valid_contours = []

        for cnt in contours:
            # Calcular área
            area = cv2.contourArea(cnt)

            # Ignorar contornos muito pequenos ou muito grandes
            min_area = img_area * 0.0003  # 0.03% da imagem
            max_area = img_area * 0.15  # 15% da imagem

            if area < min_area or area > max_area:
                continue

            # Filtro de forma: calcular circularidade e alongamento
            perimeter = cv2.arcLength(cnt, True)
            if perimeter == 0:
                continue

            circularity = 4 * np.pi * area / (perimeter * perimeter)

            # Obter retângulo delimitador e calcular razão de aspecto
            x, y, w, h = cv2.boundingRect(cnt)
            aspect_ratio = float(w) / h if h > 0 else 0

            # Contornos muito alongados (aspect_ratio > 5 ou < 0.2) ou
            # muito "tortos" (circularity < 0.1) são provavelmente ruído
            if aspect_ratio > 7 or aspect_ratio < 0.15 or circularity < 0.05:
                continue

            # Verificar se o contorno toca a borda da imagem
            # Contornos que tocam a borda frequentemente são artefatos
            img_h, img_w = img_rgb.shape[:2]
            rect_x, rect_y, rect_w, rect_h = cv2.boundingRect(cnt)
            if rect_x <= 1 or rect_y <= 1 or rect_x + rect_w >= img_w - 1 or rect_y + rect_h >= img_h - 1:
                # Se tocar na borda, permitir apenas se for grande o suficiente
                if area < img_area * 0.01:  # 1% da imagem
                    continue

            # Verificar densidade de pixels
            mask = np.zeros((img_h, img_w), dtype=np.uint8)
            cv2.drawContours(mask, [cnt], 0, 255, -1)
            roi = cv2.bitwise_and(img_rgb, img_rgb, mask=mask)
            non_zero_pixels = np.count_nonzero(mask)

            if non_zero_pixels == 0:
                continue

            mean_color = cv2.mean(roi, mask=mask)[:3]  # Média de cor RGB

            # Microorganismos geralmente têm um contraste diferente do fundo
            mean_intensity = sum(mean_color) / 3
            roi_std = np.std(roi[mask > 0])

            # Regiões com desvio padrão muito baixo geralmente são ruído uniforme
            if roi_std < 5:
                continue

            # Filtrar com base no contraste com o ambiente
            padding = 10
            padded_x = max(0, rect_x - padding)
            padded_y = max(0, rect_y - padding)
            padded_w = min(img_w - padded_x, rect_w + 2 * padding)
            padded_h = min(img_h - padded_y, rect_h + 2 * padding)

            # Se o padded retângulo é válido
            if padded_w > 0 and padded_h > 0:
                surrounding_mask = np.zeros((img_h, img_w), dtype=np.uint8)
                surrounding_mask[padded_y : padded_y + padded_h, padded_x : padded_x + padded_w] = 255
                surrounding_mask = cv2.subtract(surrounding_mask, mask)

                if np.count_nonzero(surrounding_mask) > 0:
                    surrounding_mean = cv2.mean(img_rgb, mask=surrounding_mask)[:3]
                    surrounding_intensity = sum(surrounding_mean) / 3

                    # Calcular contraste
                    contrast = abs(mean_intensity - surrounding_intensity)

                    # Objetos com muito pouco contraste podem ser ruído
                    if contrast < 5:
                        continue

            # Passou por todos os filtros
            valid_contours.append(cnt)

        return valid_contours

    def _detect_yeasts(self, img_gray: np.ndarray, enhanced_img: np.ndarray) -> List[Tuple[Tuple[int, int, int, int], float]]:
        """
        Detecta leveduras usando técnicas específicas para formas circulares/ovais.

        Args:
            img_gray: Imagem em escala de cinza
            enhanced_img: Imagem pré-processada com realce

        Returns:
            Lista de tuplas: (coordenadas (x1,y1,x2,y2), confiança)
        """
        detected = []
        h, w = img_gray.shape

        try:
            # 1. Detectar usando transformada de Hough para círculos
            circles = cv2.HoughCircles(
                enhanced_img,
                cv2.HOUGH_GRADIENT,
                dp=1,
                minDist=20,
                param1=50,
                param2=25,  # Menos restritivo
                minRadius=8,
                maxRadius=100,
            )

            if circles is not None:
                circles = np.uint16(np.around(circles))

                for circle in circles[0, :]:
                    center_x, center_y, radius = circle

                    # Verificar qualidade do círculo
                    # Extrair a região e verificar homogeneidade
                    roi_x1 = max(0, center_x - radius)
                    roi_y1 = max(0, center_y - radius)
                    roi_x2 = min(w, center_x + radius)
                    roi_y2 = min(h, center_y + radius)

                    if roi_x2 <= roi_x1 or roi_y2 <= roi_y1:
                        continue

                    roi = img_gray[roi_y1:roi_y2, roi_x1:roi_x2]

                    # Verificar forma através de máscara circular
                    mask = np.zeros(roi.shape, dtype=np.uint8)
                    cv2.circle(mask, (radius, radius), radius, 255, -1)

                    # Verificar simetria e homogeneidade - características de leveduras
                    masked_roi = cv2.bitwise_and(roi, roi, mask=mask)
                    non_zero = np.count_nonzero(mask)

                    if non_zero == 0:
                        continue

                    mean_val = np.sum(masked_roi) / non_zero
                    std_val = np.std(masked_roi[mask > 0])

                    # Calcular confiança com base em características
                    # Leveduras tendem a ter forma simétrica e textura homogênea
                    homogeneity_score = 1.0 - min(1.0, std_val / 50.0)
                    size_score = min(1.0, (radius**2) / 2500)  # Favorece tamanhos médios

                    # Confiança combinada
                    confidence = 0.4 + (0.3 * homogeneity_score) + (0.3 * size_score)

                    detected.append(((int(roi_x1), int(roi_y1), int(roi_x2), int(roi_y2)), confidence))

            # 2. Detectar usando análise de blobs para formas ovais
            # Parâmetros para detector de blobs
            params = cv2.SimpleBlobDetector_Params()

            # Definir parâmetros de área
            params.filterByArea = True
            params.minArea = 100
            params.maxArea = 5000

            # Definir parâmetros de circularidade
            params.filterByCircularity = True
            params.minCircularity = 0.7  # Leveduras são bastante circulares

            # Definir parâmetros de convexidade
            params.filterByConvexity = True
            params.minConvexity = 0.8  # Leveduras têm alta convexidade

            # Definir parâmetros de inércia (alongamento)
            params.filterByInertia = True
            params.minInertiaRatio = 0.6  # Não muito alongadas

            # Criar detector e detectar blobs
            detector = cv2.SimpleBlobDetector_create(params)

            # Inverter a imagem pois buscamos regiões escuras em fundo claro
            inverted = cv2.bitwise_not(enhanced_img)
            keypoints = detector.detect(inverted)

            for kp in keypoints:
                # Obter coordenadas e tamanho
                center_x, center_y = map(int, kp.pt)
                size = int(kp.size)

                # Definir região da bounding box
                roi_x1 = max(0, center_x - size)
                roi_y1 = max(0, center_y - size)
                roi_x2 = min(w, center_x + size)
                roi_y2 = min(h, center_y + size)

                if roi_x2 <= roi_x1 or roi_y2 <= roi_y1:
                    continue

                # Calcular confiança baseada nas propriedades do blob
                confidence = 0.6 + (0.2 * (kp.response / 100)) + (0.2 * (kp.size / 100))
                confidence = min(0.95, confidence)  # Limitar confiança máxima

                detected.append(((int(roi_x1), int(roi_y1), int(roi_x2), int(roi_y2)), confidence))

            return detected

        except Exception as e:
            logger.error(f"Erro na detecção de leveduras: {str(e)}")
            return []

    def _detect_fungi(self, img_gray: np.ndarray, enhanced_img: np.ndarray) -> List[Tuple[Tuple[int, int, int, int], float]]:
        """
        Detecta fungos usando técnicas específicas para estruturas filamentosas.

        Args:
            img_gray: Imagem em escala de cinza
            enhanced_img: Imagem pré-processada com realce

        Returns:
            Lista de tuplas: (coordenadas (x1,y1,x2,y2), confiança)
        """
        detected = []
        h, w = img_gray.shape

        try:
            # 1. Realçar estruturas filamentosas com filtros direcionais
            # Kernel Gabor para texturas direcionais
            ksize = 31
            sigma = 4.0
            theta = 0
            lambd = 10.0
            gamma = 0.5

            results = []

            # Aplicar filtros em diferentes ângulos para capturar hifas em qualquer direção
            for angle in range(0, 180, 30):
                theta = angle * np.pi / 180.0
                kernel = cv2.getGaborKernel((ksize, ksize), sigma, theta, lambd, gamma, 0, ktype=cv2.CV_32F)
                filtered = cv2.filter2D(enhanced_img, cv2.CV_8UC3, kernel)
                results.append(filtered)

            # Combinar resultados dos filtros (máximo em cada pixel)
            gabor_result = results[0]
            for i in range(1, len(results)):
                gabor_result = np.maximum(gabor_result, results[i])

            # Limiarizar resultado do Gabor
            _, gabor_thresh = cv2.threshold(gabor_result, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

            # Encontrar contornos nas estruturas filamentosas
            contours, _ = cv2.findContours(gabor_thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            for cnt in contours:
                # Calcular propriedades do contorno
                area = cv2.contourArea(cnt)
                if area < 100:  # Ignorar contornos muito pequenos
                    continue

                # Obter bounding box
                x, y, box_w, box_h = cv2.boundingRect(cnt)

                # Verificar razão de aspecto - fungos filamentosos tendem a ser alongados
                aspect_ratio = float(box_w) / box_h if box_h > 0 else 0

                # Calcular perimeter e medidas de forma
                perimeter = cv2.arcLength(cnt, True)
                if perimeter == 0:
                    continue

                circularity = 4 * np.pi * area / (perimeter * perimeter)
                extent = float(area) / (box_w * box_h)

                # Calcular confiança com base nas características
                # Fungos tendem a ter forma menos circular e mais alongada
                elongation_score = min(1.0, abs(aspect_ratio - 1.0))
                shape_score = 1.0 - min(1.0, circularity)
                extent_score = 1.0 - min(1.0, extent)  # Fungos tendem a ocupar menos da bbox

                # Elementos filamentosos têm baixa circularidade e são mais alongados
                is_filamentous = circularity < 0.5 and (aspect_ratio > 2.0 or aspect_ratio < 0.5)

                # Confiança combinada
                confidence = 0.0
                if is_filamentous:
                    confidence = 0.5 + (0.2 * elongation_score) + (0.2 * shape_score) + (0.1 * extent_score)

                    detected.append(((int(x), int(y), int(x + box_w), int(y + box_h)), confidence))

            # 2. Detectar usando análise de esqueletos - método específico para estruturas filamentosas
            # Aplicar limiarização adaptativa para obter máscara binária
            thresh = cv2.adaptiveThreshold(enhanced_img, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2)

            # Aplicar operações morfológicas para limpar a máscara
            kernel = np.ones((3, 3), np.uint8)
            cleaned = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel, iterations=1)

            # Obter esqueleto através de transformação de distância e watershed
            dist_transform = cv2.distanceTransform(cleaned, cv2.DIST_L2, 3)
            _, skeleton = cv2.threshold(dist_transform, 0.3 * dist_transform.max(), 255, 0)
            skeleton = skeleton.astype(np.uint8)

            # Dilatar levemente o esqueleto para reconectar partes quebradas
            skeleton_dilated = cv2.dilate(skeleton, kernel, iterations=1)

            # Encontrar componentes conectados
            num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(skeleton_dilated, connectivity=8)

            # Analisar cada componente para identificar estruturas filamentosas
            for i in range(1, num_labels):  # Pular o fundo (label 0)
                x = stats[i, cv2.CC_STAT_LEFT]
                y = stats[i, cv2.CC_STAT_TOP]
                w = stats[i, cv2.CC_STAT_WIDTH]
                h = stats[i, cv2.CC_STAT_HEIGHT]
                area = stats[i, cv2.CC_STAT_AREA]

                # Calcular características do componente
                component_mask = (labels == i).astype(np.uint8) * 255

                # Verificar se é uma estrutura filamentosa
                # Calcular razão de aspecto e extensão
                aspect_ratio = float(w) / h if h > 0 else 0
                extent = float(area) / (w * h)

                # Alongamento alto e extensão baixa são características de estruturas filamentosas
                is_filamentous = (aspect_ratio > 2.0 or aspect_ratio < 0.5) and extent < 0.5

                if is_filamentous and area > 100:
                    # Calcular confiança baseada nas características
                    elongation_score = min(1.0, max(aspect_ratio, 1.0 / aspect_ratio) / 5.0)
                    thinness_score = 1.0 - min(1.0, extent)
                    size_score = min(1.0, area / 1000.0)

                    confidence = 0.4 + (0.3 * elongation_score) + (0.2 * thinness_score) + (0.1 * size_score)

                    detected.append(((int(x), int(y), int(x + w), int(y + h)), confidence))

            return detected

        except Exception as e:
            logger.error(f"Erro na detecção de fungos: {str(e)}")
            return []

    def _detect_algae(self, img_rgb: np.ndarray, enhanced_img: np.ndarray) -> List[Tuple[Tuple[int, int, int, int], float]]:
        """
        Detecta microalgas usando técnicas específicas para suas características.

        Args:
            img_rgb: Imagem RGB original
            enhanced_img: Imagem pré-processada com realce

        Returns:
            Lista de tuplas: (coordenadas (x1,y1,x2,y2), confiança)
        """
        detected = []

        try:
            h, w = img_rgb.shape[:2]

            # 1. Análise de componentes de cor - microalgas frequentemente têm tons de verde
            hsv = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2HSV)

            # Extrair canal de matiz (H)
            h_channel = hsv[:, :, 0]

            # Definir máscaras para tons de verde (aproximadamente 60-170 no espaço HSV)
            lower_green = np.array([40, 10, 10])
            upper_green = np.array([170, 255, 255])

            green_mask = cv2.inRange(hsv, lower_green, upper_green)

            # Aplicar operações morfológicas para limpar a máscara
            kernel = np.ones((3, 3), np.uint8)
            green_mask = cv2.morphologyEx(green_mask, cv2.MORPH_OPEN, kernel, iterations=1)
            green_mask = cv2.morphologyEx(green_mask, cv2.MORPH_CLOSE, kernel, iterations=2)

            # Encontrar contornos nas regiões verdes
            contours, _ = cv2.findContours(green_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            for cnt in contours:
                # Calcular área e verificar se é grande o suficiente
                area = cv2.contourArea(cnt)
                if area < 150:  # Ignorar regiões muito pequenas
                    continue

                # Obter bounding box
                x, y, box_w, box_h = cv2.boundingRect(cnt)

                # Extrair região de interesse
                roi = img_rgb[y : y + box_h, x : x + box_w]
                hsv_roi = hsv[y : y + box_h, x : x + box_h]

                if roi.size == 0:
                    continue

                # Calcular características da região
                mean_color = cv2.mean(roi)
                mean_hsv = cv2.mean(hsv_roi)

                # Verificar dominância de verde
                is_greenish = mean_hsv[0] > 40 and mean_hsv[0] < 170 and mean_hsv[1] > 30

                # Calcular textura
                if len(roi.shape) > 2:
                    gray_roi = cv2.cvtColor(roi, cv2.COLOR_RGB2GRAY)
                else:
                    gray_roi = roi

                std_val = np.std(gray_roi)

                # Microalgas têm textura característica - não muito lisa e não muito rugosa
                texture_score = min(1.0, std_val / 30.0) if std_val < 30 else 1.0 - min(1.0, (std_val - 30) / 50.0)

                # Calcular confiança
                color_score = 0.6 if is_greenish else 0.2

                # Confiança combinada
                confidence = (0.7 * color_score) + (0.3 * texture_score)

                # Adicionar apenas se houver confiança razoável
                if confidence > 0.3:
                    detected.append(((int(x), int(y), int(x + box_w), int(y + box_h)), confidence))

            # 2. Segmentação baseada em textura - microalgas têm padrões texturais distintos

            # Converter para escala de cinza se necessário
            if len(img_rgb.shape) > 2:
                gray = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2GRAY)
            else:
                gray = img_rgb.copy()

            # Extração de características de textura usando LBP (Local Binary Patterns)
            # Implementação simplificada de LBP
            texture_features = np.zeros_like(gray)

            for i in range(1, h - 1):
                for j in range(1, w - 1):
                    center = gray[i, j]
                    code = 0
                    # Percorrer 8-vizinhança
                    if gray[i - 1, j - 1] >= center:
                        code += 1
                    if gray[i - 1, j] >= center:
                        code += 2
                    if gray[i - 1, j + 1] >= center:
                        code += 4
                    if gray[i, j + 1] >= center:
                        code += 8
                    if gray[i + 1, j + 1] >= center:
                        code += 16
                    if gray[i + 1, j] >= center:
                        code += 32
                    if gray[i + 1, j - 1] >= center:
                        code += 64
                    if gray[i, j - 1] >= center:
                        code += 128

                    texture_features[i, j] = code

            # Aplicar K-means na textura para segmentar regiões distintas
            texture_features_flat = texture_features.reshape((-1, 1))
            texture_features_flat = np.float32(texture_features_flat)

            criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
            K = 3  # Número de clusters
            _, labels, _ = cv2.kmeans(texture_features_flat, K, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)

            # Reshaping do resultado
            labels = labels.reshape(texture_features.shape)

            # Para cada cluster, verificar se contém microalgas
            for k in range(K):
                # Criar máscara para este cluster
                mask = (labels == k).astype(np.uint8) * 255

                # Aplicar operações morfológicas para limpar
                mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)
                mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)

                # Encontrar contornos
                contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

                for cnt in contours:
                    area = cv2.contourArea(cnt)
                    if area < 200:  # Ignorar muito pequenos
                        continue

                    x, y, box_w, box_h = cv2.boundingRect(cnt)

                    # Extrair região
                    roi = img_rgb[y : y + box_h, x : x + box_w] if y + box_h <= h and x + box_w <= w else None

                    if roi is None or roi.size == 0:
                        continue

                    # Analisar características da região
                    # Microalgas tendem a ter textura mais uniforme que fungos
                    # mas menos uniforme que o fundo
                    if len(roi.shape) > 2:
                        gray_roi = cv2.cvtColor(roi, cv2.COLOR_RGB2GRAY)
                    else:
                        gray_roi = roi

                    mean_val = np.mean(gray_roi)
                    std_val = np.std(gray_roi)

                    # Medidas de forma
                    perimeter = cv2.arcLength(cnt, True)
                    if perimeter == 0:
                        continue

                    circularity = 4 * np.pi * area / (perimeter * perimeter)

                    # Microalgas têm formas variadas, mas tendem a ser mais regulares
                    # que fungos e menos circulares que leveduras
                    shape_score = 0.5 + (0.5 * min(circularity, 1.0 - circularity))

                    # Características de textura
                    texture_score = 0.5
                    if 20 < std_val < 60:  # Faixa ideal para microalgas
                        texture_score = 0.8

                    # Confiança final
                    confidence = 0.3 + (0.4 * shape_score) + (0.3 * texture_score)

                    # Adicionar apenas microalgas prováveis
                    if confidence > 0.4:
                        detected.append(((int(x), int(y), int(x + box_w), int(y + box_h)), confidence))

            return detected

        except Exception as e:
            logger.error(f"Erro na detecção de microalgas: {str(e)}")
            return []

    def _apply_nms(self, boxes: List[Dict]) -> List[Dict]:
        """
        Aplica Non-Maximum Suppression para eliminar caixas sobrepostas.

        Args:
            boxes: Lista de dicionários com informações das caixas

        Returns:
            Lista filtrada de caixas após NMS
        """
        if not boxes:
            return []

        # Ordenar caixas por confiança (decrescente)
        sorted_boxes = sorted(boxes, key=lambda x: x["confidence"], reverse=True)

        # Lista para armazenar caixas finais após NMS
        keep_boxes = []

        while sorted_boxes:
            # Pegar a caixa de maior confiança
            current = sorted_boxes.pop(0)
            keep_boxes.append(current)

            # Calcular IoU com todas as caixas restantes e remover sobreposições
            remaining_boxes = []

            for box in sorted_boxes:
                # Se as classes forem diferentes, manter ambas
                if box["class_id"] != current["class_id"]:
                    remaining_boxes.append(box)
                    continue

                # Calcular IoU
                x1_a, y1_a, x2_a, y2_a = current["coords"]
                x1_b, y1_b, x2_b, y2_b = box["coords"]

                # Calcular área de interseção
                x_left = max(x1_a, x1_b)
                y_top = max(y1_a, y1_b)
                x_right = min(x2_a, x2_b)
                y_bottom = min(y2_a, y2_b)

                # Se não há sobreposição
                if x_right < x_left or y_bottom < y_top:
                    remaining_boxes.append(box)
                    continue

                # Calcular área da interseção
                intersection_area = (x_right - x_left) * (y_bottom - y_top)

                # Calcular áreas das duas caixas
                box_a_area = (x2_a - x1_a) * (y2_a - y1_a)
                box_b_area = (x2_b - x1_b) * (y2_b - y1_b)

                # Calcular IoU
                iou = intersection_area / float(box_a_area + box_b_area - intersection_area)

                # Se a sobreposição for menor que um limiar, manter a caixa
                if iou < 0.5:
                    remaining_boxes.append(box)

            # Atualizar a lista de caixas restantes
            sorted_boxes = remaining_boxes

        return keep_boxes

    def _advanced_classification(self, roi: np.ndarray, contour: np.ndarray) -> Tuple[str, float]:
        """
        Classifica o tipo de microorganismo com base em várias características avançadas.

        Args:
            roi: Região de interesse (imagem recortada)
            contour: Contorno do objeto

        Returns:
            Tupla com (ID da classe mais provável, confiança)
        """
        try:
            if roi.size == 0:
                return random.choice([c.split("-")[0] for c in self.classes]), 0.3

            # Converter para escala de cinza se for colorido
            if len(roi.shape) > 2:
                gray_roi = cv2.cvtColor(roi, cv2.COLOR_RGB2GRAY)
            else:
                gray_roi = roi

            # 1. Calcular características de forma
            area = cv2.contourArea(contour)
            perimeter = cv2.arcLength(contour, True)

            if perimeter == 0:
                return random.choice([c.split("-")[0] for c in self.classes]), 0.3

            # Circularidade: 4π * área / perímetro²
            circularity = 4 * np.pi * area / (perimeter * perimeter)

            # Obter retângulo delimitador e calcular razão de aspecto
            x, y, w, h = cv2.boundingRect(contour)
            aspect_ratio = float(w) / h if h > 0 else 0

            # Calcular momentos de Hu para invariância à rotação, escala e translação
            moments = cv2.moments(contour)
            hu_moments = cv2.HuMoments(moments).flatten()

            # 2. Calcular características de textura
            # Média e desvio padrão
            mean_val = np.mean(gray_roi)
            std_val = np.std(gray_roi)

            # Histograma de gradientes locais (simplificado)
            sobelx = cv2.Sobel(gray_roi, cv2.CV_64F, 1, 0, ksize=3)
            sobely = cv2.Sobel(gray_roi, cv2.CV_64F, 0, 1, ksize=3)
            magnitude = cv2.magnitude(sobelx, sobely)
            direction = cv2.phase(sobelx, sobely, angleInDegrees=True)

            gradient_mean = np.mean(magnitude)
            gradient_std = np.std(magnitude)

            # Homogeneidade
            homogeneity = 1.0 / (1.0 + gradient_std) if gradient_std > 0 else 1.0

            # 3. Calcular características de cor (se disponível)
            color_features = []
            if len(roi.shape) > 2:
                # Canal dominante
                mean_color = np.mean(roi, axis=(0, 1))
                dominant_channel = np.argmax(mean_color)

                # Converter para HSV para características de cor
                roi_hsv = cv2.cvtColor(roi, cv2.COLOR_RGB2HSV)
                mean_hsv = np.mean(roi_hsv, axis=(0, 1))

                color_features = [
                    dominant_channel,
                    mean_hsv[0],  # Hue (matiz)
                    mean_hsv[1],  # Saturation (saturação)
                    mean_hsv[2],  # Value (valor)
                ]

            # 4. Combinar características para classificação

            # Pesos para diferentes características
            levedura_score = 0.0
            fungo_score = 0.0
            alga_score = 0.0

            # --- Classificação por forma ---

            # Leveduras: alta circularidade, aspect ratio próximo de 1
            if circularity > 0.8 and 0.8 < aspect_ratio < 1.2:
                levedura_score += 0.6
            elif circularity > 0.7 and 0.7 < aspect_ratio < 1.3:
                levedura_score += 0.4
            elif circularity > 0.6 and 0.6 < aspect_ratio < 1.4:
                levedura_score += 0.2

            # Fungos: baixa circularidade, formas alongadas
            if circularity < 0.5 and (aspect_ratio > 1.5 or aspect_ratio < 0.67):
                fungo_score += 0.6
            elif circularity < 0.6 and (aspect_ratio > 1.3 or aspect_ratio < 0.75):
                fungo_score += 0.4
            elif circularity < 0.7 and (aspect_ratio > 1.2 or aspect_ratio < 0.8):
                fungo_score += 0.2

            # Microalgas: circularidade intermediária, formas variadas
            if 0.5 < circularity < 0.8:
                alga_score += 0.3

            # --- Classificação por textura ---

            # Leveduras: textura mais homogênea
            if homogeneity > 0.7 and std_val < 30:
                levedura_score += 0.3

            # Fungos: textura mais heterogênea, com padrões de hifas
            if homogeneity < 0.5 and gradient_std > 20:
                fungo_score += 0.3

            # Microalgas: textura intermediária
            if 0.4 < homogeneity < 0.7 and 15 < std_val < 50:
                alga_score += 0.4

            # --- Classificação por cor ---

            if color_features:
                hue = color_features[1]
                saturation = color_features[2]

                # Microalgas: tons de verde (hue ~ 60-180)
                if 50 < hue < 190 and saturation > 30:
                    alga_score += 0.3

            # 5. Decidir a classe final
            scores = {
                "0": levedura_score,  # Levedura
                "1": fungo_score,  # Fungo
                "2": alga_score,  # Microalga
            }

            # Encontrar a classe com maior pontuação
            max_class = max(scores.items(), key=lambda x: x[1])
            class_id = max_class[0]
            confidence = max(0.3, min(0.95, max_class[1]))

            return class_id, confidence

        except Exception as e:
            logger.warning(f"Erro na classificação avançada: {str(e)}")
            return random.choice([c.split("-")[0] for c in self.classes]), 0.3

    def _emergency_detection(self, img_rgb: np.ndarray) -> List[Tuple[str, int, int, int, int]]:
        """
        Método de detecção de último recurso, mais agressivo para detectar
        estruturas quando outros métodos falham.

        Args:
            img_rgb: Imagem RGB original

        Returns:
            Lista de bounding boxes no formato [(class_id, x1, y1, x2, y2), ...]
        """
        emergency_boxes = []

        try:
            h, w = img_rgb.shape[:2]

            # Converter para escala de cinza
            gray = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2GRAY)

            # Aplicar forte equalização de histograma
            clahe = cv2.createCLAHE(clipLimit=4.0, tileGridSize=(4, 4))
            enhanced = clahe.apply(gray)

            # Aplicar filtro bilateral para reduzir ruído preservando bordas
            smoothed = cv2.bilateralFilter(enhanced, 9, 150, 150)

            # Aplicar detecção de bordas Canny com limiares baixos
            edges = cv2.Canny(smoothed, 20, 120)

            # Dilatar bordas para conectar regiões próximas
            kernel = np.ones((5, 5), np.uint8)
            dilated = cv2.dilate(edges, kernel, iterations=2)

            # Preencher buracos
            contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            mask = np.zeros((h, w), dtype=np.uint8)
            cv2.drawContours(mask, contours, -1, 255, -1)

            # Encontrar componentes conectados
            num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(mask, connectivity=8)

            # Filtrar componentes por tamanho
            min_area = w * h * 0.0002  # 0.02% da imagem
            max_area = w * h * 0.2  # 20% da imagem

            # Mapa para associar classes com regiões detectadas
            class_map = {}
            for i in range(len(self.classes)):
                cls = self.classes[i].split("-")[0]
                class_map[i % 3] = cls  # Distribuir uniformemente entre as 3 classes

            for i in range(1, num_labels):  # Pular o fundo (0)
                area = stats[i, cv2.CC_STAT_AREA]

                if min_area <= area <= max_area:
                    x = stats[i, cv2.CC_STAT_LEFT]
                    y = stats[i, cv2.CC_STAT_TOP]
                    width = stats[i, cv2.CC_STAT_WIDTH]
                    height = stats[i, cv2.CC_STAT_HEIGHT]

                    # Extrair região para classificação
                    component_mask = (labels == i).astype(np.uint8)
                    roi = img_rgb[y : y + height, x : x + width]

                    if roi.size == 0:
                        continue

                    # Encontrar contorno preciso para esta região
                    component_contours, _ = cv2.findContours(
                        component_mask[y : y + height, x : x + width], cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
                    )

                    if not component_contours:
                        continue

                    # Usar o maior contorno
                    cnt = max(component_contours, key=cv2.contourArea)

                    # Classificar usando forma e textura
                    class_id, confidence = self._advanced_classification(roi, cnt)

                    # Para o método de emergência, aceitamos qualquer confiança
                    emergency_boxes.append((class_id, x, y, x + width, y + height))

            logger.info(f"Detecção de emergência encontrou {len(emergency_boxes)} objetos")
            return emergency_boxes

        except Exception as e:
            logger.error(f"Erro na detecção de emergência: {str(e)}")
            return []

    def _classify_microorganism(self, roi: np.ndarray, contour: np.ndarray) -> str:
        """
        Classifica o tipo de microorganismo com base em características visuais.
        Este método é mantido para compatibilidade, mas o _advanced_classification
        deve ser usado para novos desenvolvimentos.

        Args:
            roi: Região de interesse (imagem recortada)
            contour: Contorno do objeto

        Returns:
            ID da classe mais provável
        """
        # Usar a classificação avançada
        class_id, _ = self._advanced_classification(roi, contour)
        return class_id

    def generate_suggestions(self, image_path: str, confidence: float = 0.5) -> List[Tuple[str, int, int, int, int]]:
        """
        Sugere anotações automáticas usando um modelo YOLO ou métodos de visão computacional.

        Args:
            image_path: Caminho para a imagem
            confidence: Limiar de confiança para detecções

        Returns:
            Lista de bounding boxes sugeridas no formato [(class_id, x1, y1, x2, y2), ...]
        """
        try:
            logger.info(f"Gerando sugestões automáticas para {image_path}")

            # Carregar a imagem
            img = cv2.imread(image_path)
            if img is None:
                logger.error(f"Não foi possível carregar a imagem: {image_path}")
                return []

            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            suggested_boxes = []

            # 1. Tentar usar modelo YOLO se disponível
            if self.model is not None:
                logger.info("Utilizando modelo YOLO para gerar sugestões")
                suggested_boxes = self._detect_with_yolo(img_rgb, confidence)

                # Se houve detecções, retornar
                if suggested_boxes:
                    return suggested_boxes
                else:
                    logger.info("YOLO não encontrou objetos. Tentando métodos alternativos.")

            # 2. Usar visão computacional como fallback se permitido
            if self.use_cv_fallback:
                logger.info("Utilizando métodos de visão computacional para gerar sugestões")
                suggested_boxes = self._detect_with_cv(img_rgb)

                # Se houve detecções, retornar
                if suggested_boxes:
                    return suggested_boxes

            # 3. Como último recurso, gerar sugestões aleatórias
            if not suggested_boxes:
                logger.info("Gerando sugestões aleatórias como último recurso")
                h, w = img_rgb.shape[:2]

                # Número de sugestões aleatórias
                num_suggestions = random.randint(3, 8)

                suggested_boxes = []
                for _ in range(num_suggestions):
                    # Escolher classe aleatoriamente
                    class_id = random.choice([c.split("-")[0] for c in self.classes])

                    # Gerar coordenadas aleatórias
                    box_w = random.randint(w // 10, w // 3)
                    box_h = random.randint(h // 10, h // 3)

                    x1 = random.randint(0, w - box_w)
                    y1 = random.randint(0, h - box_h)
                    x2 = x1 + box_w
                    y2 = y1 + box_h

                    # Adicionar à lista de sugestões
                    suggested_boxes.append((class_id, x1, y1, x2, y2))

            logger.info(f"{len(suggested_boxes)} sugestões geradas para {image_path}")
            return suggested_boxes

        except Exception as e:
            logger.error(f"Erro ao gerar sugestões automáticas: {str(e)}")
            return []

    def set_model_path(self, model_path: str) -> bool:
        """
        Define um novo caminho para o modelo YOLO e tenta carregá-lo.

        Args:
            model_path: Caminho para o modelo YOLO

        Returns:
            True se o modelo foi carregado com sucesso, False caso contrário
        """
        self.yolo_model_path = model_path
        self.model = None
        return self._load_model()

    def toggle_cv_fallback(self, enabled: bool = True) -> None:
        """
        Ativa ou desativa o uso de visão computacional como fallback.

        Args:
            enabled: Se True, ativa o fallback; se False, desativa
        """
        self.use_cv_fallback = enabled
