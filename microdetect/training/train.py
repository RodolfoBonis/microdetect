"""
Módulo para treinamento de modelos YOLOv8.
"""

import os
import logging
from typing import Dict, Any, Optional, Union, Tuple
import torch
from ultralytics import YOLO

from microdetect.utils.config import config

logger = logging.getLogger(__name__)


class YOLOTrainer:
    """
    Classe para treinar modelos YOLOv8 para detecção de microorganismos.
    """

    def __init__(self,
                 model_size: str = None,
                 epochs: int = None,
                 batch_size: int = None,
                 image_size: int = None,
                 pretrained: bool = None,
                 output_dir: str = None):
        """
        Inicializa o treinador com parâmetros configuráveis.

        Args:
            model_size: Tamanho do modelo ('n', 's', 'm', 'l', 'x')
            epochs: Número de épocas de treinamento
            batch_size: Tamanho do batch
            image_size: Tamanho da imagem de entrada
            pretrained: Se deve usar pesos pré-treinados
            output_dir: Diretório para salvar resultados de treinamento
        """
        self.model_size = model_size or config.get('training.model_size', 's')
        self.epochs = epochs or config.get('training.epochs', 100)
        self.batch_size = batch_size or config.get('training.batch_size', 16)
        self.image_size = image_size or config.get('training.image_size', 640)
        self.pretrained = pretrained if pretrained is not None else config.get('training.pretrained', True)
        self.output_dir = output_dir or config.get('directories.output', 'runs/train')

    def train(self, data_yaml: str) -> Dict[str, Any]:
        """
        Treina um modelo YOLO no dataset.

        Args:
            data_yaml: Caminho para configuração YAML do dados

        Returns:
            Resultados do treinamento
        """
        # Selecionar modelo com base no tamanho
        model_name = f"yolov8{self.model_size}.pt" if self.pretrained else f"yolov8{self.model_size}.yaml"

        # Inicializar modelo
        try:
            model = YOLO(model_name)
            logger.info(f"Modelo carregado: {model_name}")
        except Exception as e:
            logger.error(f"Erro ao carregar modelo {model_name}: {str(e)}")
            raise

        # Determinar dispositivo - usar MPS se disponível no Apple Silicon
        if torch.backends.mps.is_available():
            device = 'mps'
            logger.info("Treinando na GPU Apple (MPS)")
        elif torch.cuda.is_available():
            device = '0'  # Primeiro dispositivo CUDA
            logger.info("Treinando na GPU NVIDIA (CUDA)")
            logger.info(f"GPU disponível: {torch.cuda.get_device_name(0)}")
        else:
            device = 'cpu'
            logger.info("Treinando na CPU (sem aceleração GPU disponível)")

        # Iniciar treinamento
        logger.info(f"Iniciando treinamento com configuração: "
                    f"epochs={self.epochs}, batch={self.batch_size}, img_size={self.image_size}")

        try:
            results = model.train(
                data=data_yaml,
                epochs=self.epochs,
                batch=self.batch_size,
                imgsz=self.image_size,
                project=self.output_dir,
                name=f"yolov8_{self.model_size}_custom",
                patience=20,
                save=True,
                device=device
            )

            logger.info("Treinamento concluído com sucesso")

            # Exportar o modelo para formato ONNX para implantação
            try:
                export_path = model.export(format='onnx')
                logger.info(f"Modelo exportado para ONNX: {export_path}")
            except Exception as e:
                logger.error(f"Erro ao exportar modelo para ONNX: {str(e)}")

            return results

        except Exception as e:
            logger.error(f"Erro durante o treinamento: {str(e)}")
            raise

    def resume_training(self, checkpoint_path: str, data_yaml: str, additional_epochs: int = None) -> Dict[str, Any]:
        """
        Retoma o treinamento de um checkpoint.

        Args:
            checkpoint_path: Caminho para o checkpoint do modelo
            data_yaml: Caminho para configuração YAML dos dados
            additional_epochs: Número adicional de épocas para treinar

        Returns:
            Resultados do treinamento
        """
        if not os.path.exists(checkpoint_path):
            raise FileNotFoundError(f"Checkpoint não encontrado: {checkpoint_path}")

        # Carregar modelo do checkpoint
        try:
            model = YOLO(checkpoint_path)
            logger.info(f"Modelo carregado do checkpoint: {checkpoint_path}")
        except Exception as e:
            logger.error(f"Erro ao carregar checkpoint {checkpoint_path}: {str(e)}")
            raise

        # Determinar dispositivo
        if torch.backends.mps.is_available():
            device = 'mps'
        elif torch.cuda.is_available():
            device = '0'
        else:
            device = 'cpu'

        # Calcular épocas totais
        if additional_epochs is None:
            additional_epochs = self.epochs

        total_epochs = model.ckpt['epoch'] + additional_epochs

        # Retomar treinamento
        logger.info(f"Retomando treinamento do epoch {model.ckpt['epoch']} até {total_epochs}")

        try:
            results = model.train(
                data=data_yaml,
                epochs=total_epochs,
                batch=self.batch_size,
                imgsz=self.image_size,
                project=self.output_dir,
                name=f"yolov8_{self.model_size}_resumed",
                patience=20,
                save=True,
                device=device,
                resume=True
            )

            logger.info("Treinamento retomado concluído com sucesso")
            return results

        except Exception as e:
            logger.error(f"Erro durante o treinamento retomado: {str(e)}")
            raise

    def find_best_hyperparameters(self, data_yaml: str) -> Dict[str, Any]:
        """
        Realiza uma busca por hiperparâmetros para o modelo YOLO.

        Args:
            data_yaml: Caminho para configuração YAML dos dados

        Returns:
            Melhores hiperparâmetros encontrados
        """
        # Isso é uma implementação simplificada. Para um uso real,
        # você poderia implementar uma busca mais completa usando
        # algo como Optuna ou Ray Tune.

        logger.info("Iniciando busca por hiperparâmetros")

        # Configurações para testar
        batch_sizes = [8, 16, 32]
        learning_rates = [0.001, 0.01, 0.1]

        best_result = None
        best_config = None

        # Modelo base
        model_name = f"yolov8{self.model_size}.pt" if self.pretrained else f"yolov8{self.model_size}.yaml"

        # Determinar dispositivo
        if torch.backends.mps.is_available():
            device = 'mps'
        elif torch.cuda.is_available():
            device = '0'
        else:
            device = 'cpu'

        # Testar combinações
        for batch_size in batch_sizes:
            for lr in learning_rates:
                logger.info(f"Testando batch_size={batch_size}, lr={lr}")

                try:
                    model = YOLO(model_name)

                    # Usar menos épocas para a busca
                    search_epochs = min(10, self.epochs)

                    results = model.train(
                        data=data_yaml,
                        epochs=search_epochs,
                        batch=batch_size,
                        imgsz=self.image_size,
                        project=self.output_dir,
                        name=f"hyperparam_search_b{batch_size}_lr{lr}",
                        patience=5,
                        save=True,
                        device=device,
                        lr0=lr
                    )

                    # Verificar se este é o melhor resultado
                    current_map = results.maps.mean()  # Média do mAP

                    if best_result is None or current_map > best_result:
                        best_result = current_map
                        best_config = {
                            'batch_size': batch_size,
                            'learning_rate': lr,
                            'map': current_map
                        }

                    logger.info(f"Resultado: mAP={current_map:.4f}")

                except Exception as e:
                    logger.error(f"Erro ao testar configuração: {str(e)}")

        if best_config:
            logger.info(f"Melhor configuração encontrada: {best_config}")

            # Treinar o modelo final com os melhores hiperparâmetros
            try:
                model = YOLO(model_name)

                final_results = model.train(
                    data=data_yaml,
                    epochs=self.epochs,
                    batch=best_config['batch_size'],
                    imgsz=self.image_size,
                    project=self.output_dir,
                    name=f"yolov8_{self.model_size}_optimized",
                    patience=20,
                    save=True,
                    device=device,
                    lr0=best_config['learning_rate']
                )

                logger.info("Treinamento com hiperparâmetros otimizados concluído")
                return best_config

            except Exception as e:
                logger.error(f"Erro durante treinamento final: {str(e)}")

        return best_config or {}