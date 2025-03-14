"""
Módulo para processamento em lote de grandes conjuntos de dados.
"""

import concurrent.futures
import json
import logging
import os
from typing import Any, Callable, Dict, List

from tqdm import tqdm
from ultralytics import YOLO

logger = logging.getLogger(__name__)


class BatchProcessor:
    """
    Classe para processamento em lote de imagens para detecção.
    """

    def __init__(self, num_workers: int = 2):
        """
        Inicializa o processador em lote.

        Args:
            num_workers: Número de workers para processamento paralelo
        """
        self.num_workers = num_workers

    def process_batch(
        self,
        model_path: str,
        source_dir: str,
        output_dir: str,
        batch_size: int = 16,
        conf_threshold: float = 0.25,
        iou_threshold: float = 0.45,
        image_size: int = 640,
        save_txt: bool = False,
        save_img: bool = True,
        save_json: bool = True,
        file_extensions: List[str] = [".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff"],
    ) -> Dict[str, Any]:
        """
        Processa um lote de imagens usando o modelo YOLO.

        Args:
            model_path: Caminho para o modelo treinado
            source_dir: Diretório com imagens de entrada
            output_dir: Diretório para salvar resultados
            batch_size: Tamanho do batch para inferência
            conf_threshold: Limiar de confiança para detecções
            iou_threshold: Limiar de IoU para NMS
            image_size: Tamanho da imagem para inferência
            save_txt: Se True, salva anotações no formato YOLO (txt)
            save_img: Se True, salva imagens com detecções
            save_json: Se True, salva resultados em formato JSON
            file_extensions: Extensões de arquivo a serem processadas

        Returns:
            Dicionário com resultados do processamento
        """
        # Verificar caminhos
        if not os.path.exists(model_path):
            logger.error(f"Modelo não encontrado: {model_path}")
            return {"error": "Modelo não encontrado"}

        if not os.path.exists(source_dir):
            logger.error(f"Diretório de origem não encontrado: {source_dir}")
            return {"error": "Diretório de origem não encontrado"}

        # Criar diretório de saída
        os.makedirs(output_dir, exist_ok=True)
        if save_txt:
            os.makedirs(os.path.join(output_dir, "labels"), exist_ok=True)
        if save_img:
            os.makedirs(os.path.join(output_dir, "images"), exist_ok=True)

        # Listar arquivos de imagem
        image_files = []
        for root, _, files in os.walk(source_dir):
            for file in files:
                if any(file.lower().endswith(ext) for ext in file_extensions):
                    image_files.append(os.path.join(root, file))

        if not image_files:
            logger.error(f"Nenhuma imagem encontrada em: {source_dir}")
            return {"error": "Nenhuma imagem encontrada"}

        # Carregar modelo
        try:
            model = YOLO(model_path)
            logger.info(f"Modelo carregado: {model_path}")
        except Exception as e:
            logger.error(f"Erro ao carregar modelo: {str(e)}")
            return {"error": f"Erro ao carregar modelo: {str(e)}"}

        # Processar em batches
        logger.info(f"Iniciando processamento de {len(image_files)} imagens com batch_size={batch_size}")

        all_results = {}
        processed_count = 0
        error_count = 0

        # Criar batches
        batches = [image_files[i : i + batch_size] for i in range(0, len(image_files), batch_size)]

        for batch_idx, batch in enumerate(tqdm(batches, desc="Processando batches")):
            try:
                # Executar detecção no batch
                results = model(batch, conf=conf_threshold, iou=iou_threshold, imgsz=image_size)

                # Processar resultados
                for i, result in enumerate(results):
                    image_path = batch[i]
                    filename = os.path.basename(image_path)

                    # Extrair detecções
                    detections = []
                    if result.boxes is not None:
                        boxes = result.boxes
                        for j in range(len(boxes)):
                            # Extrair caixa, classe e confiança
                            box = boxes[j]
                            x1, y1, x2, y2 = box.xyxy.cpu().numpy()[0]
                            cls = int(box.cls.cpu().numpy()[0])
                            conf = float(box.conf.cpu().numpy()[0])

                            # Calcular largura e altura
                            w = x2 - x1
                            h = y2 - y1

                            # Normalizar para o formato YOLO (centro_x, centro_y, largura, altura)
                            img_height, img_width = result.orig_shape
                            center_x = (x1 + x2) / 2 / img_width
                            center_y = (y1 + y2) / 2 / img_height
                            width = w / img_width
                            height = h / img_height

                            # Armazenar detecção
                            detections.append(
                                {
                                    "bbox": [float(x1), float(y1), float(x2), float(y2)],
                                    "bbox_normalized": [center_x, center_y, width, height],
                                    "class": cls,
                                    "class_name": result.names[cls],
                                    "confidence": conf,
                                }
                            )

                    # Guardar resultados
                    all_results[filename] = detections
                    processed_count += 1

                    # Salvar em formato YOLO (txt)
                    if save_txt and detections:
                        txt_filename = os.path.splitext(filename)[0] + ".txt"
                        txt_path = os.path.join(output_dir, "labels", txt_filename)

                        with open(txt_path, "w") as f:
                            for det in detections:
                                # Formato YOLO: class_id center_x center_y width height
                                line = f"{det['class']} {det['bbox_normalized'][0]} {det['bbox_normalized'][1]} {det['bbox_normalized'][2]} {det['bbox_normalized'][3]}\n"
                                f.write(line)

                    # Salvar imagem com detecções
                    if save_img:
                        img_output_path = os.path.join(output_dir, "images", filename)
                        result.save(filename=img_output_path)

            except Exception as e:
                logger.error(f"Erro ao processar batch {batch_idx + 1}: {str(e)}")
                error_count += len(batch)

        # Salvar resultados em JSON
        if save_json:
            json_path = os.path.join(output_dir, "detection_results.json")
            with open(json_path, "w") as f:
                json.dump(all_results, f, indent=4)

            logger.info(f"Resultados salvos em: {json_path}")

        return {
            "processed": processed_count,
            "errors": error_count,
            "total": len(image_files),
            "output_dir": output_dir,
            "results": all_results if not save_json else json_path,
        }

    def process_parallel(
        self,
        model_path: str,
        source_dir: str,
        output_dir: str,
        worker_function: Callable,
        worker_args: Dict[str, Any],
        file_extensions: List[str] = [".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff"],
    ) -> Dict[str, Any]:
        """
        Processa imagens em paralelo usando uma função worker personalizada.

        Args:
            model_path: Caminho para o modelo treinado
            source_dir: Diretório com imagens de entrada
            output_dir: Diretório para salvar resultados
            worker_function: Função worker a ser chamada para cada imagem
            worker_args: Argumentos adicionais para a função worker
            file_extensions: Extensões de arquivo a serem processadas

        Returns:
            Dicionário com resultados do processamento
        """
        # Verificar caminhos
        if not os.path.exists(model_path):
            logger.error(f"Modelo não encontrado: {model_path}")
            return {"error": "Modelo não encontrado"}

        if not os.path.exists(source_dir):
            logger.error(f"Diretório de origem não encontrado: {source_dir}")
            return {"error": "Diretório de origem não encontrado"}

        # Criar diretório de saída
        os.makedirs(output_dir, exist_ok=True)

        # Listar arquivos de imagem
        image_files = []
        for root, _, files in os.walk(source_dir):
            for file in files:
                if any(file.lower().endswith(ext) for ext in file_extensions):
                    image_files.append(os.path.join(root, file))

        if not image_files:
            logger.error(f"Nenhuma imagem encontrada em: {source_dir}")
            return {"error": "Nenhuma imagem encontrada"}

        # Carregar modelo
        try:
            model = YOLO(model_path)
            logger.info(f"Modelo carregado: {model_path}")
        except Exception as e:
            logger.error(f"Erro ao carregar modelo: {str(e)}")
            return {"error": f"Erro ao carregar modelo: {str(e)}"}

        # Processar em paralelo
        logger.info(f"Iniciando processamento paralelo de {len(image_files)} imagens com {self.num_workers} workers")

        results = {}
        errors = []

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.num_workers) as executor:
            future_to_file = {
                executor.submit(worker_function, model, image_path, output_dir, **worker_args): image_path
                for image_path in image_files
            }

            for future in tqdm(
                concurrent.futures.as_completed(future_to_file), total=len(image_files), desc="Processando imagens"
            ):
                file_path = future_to_file[future]
                try:
                    result = future.result()
                    results[os.path.basename(file_path)] = result
                except Exception as e:
                    logger.error(f"Erro ao processar {file_path}: {str(e)}")
                    errors.append({"file": file_path, "error": str(e)})

        # Salvar resultados
        json_path = os.path.join(output_dir, "parallel_processing_results.json")
        with open(json_path, "w") as f:
            json.dump({"results": results, "errors": errors}, f, indent=4)

        return {
            "processed": len(results),
            "errors": len(errors),
            "total": len(image_files),
            "output_dir": output_dir,
            "results_file": json_path,
        }
