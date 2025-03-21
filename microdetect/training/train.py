"""
Módulo para treinamento de modelos YOLOv8.
"""

import gc
import logging
import os
import shutil
import time
from datetime import datetime
from typing import Any, Dict, Optional, List

import numpy as np
import torch
from ultralytics import YOLO

from microdetect.utils.config import config

logger = logging.getLogger(__name__)


def extract_map_from_results(results):
    """Extrai o valor mAP dos resultados do modelo, lidando com diferentes formatos."""
    try:
        if hasattr(results, 'maps') and hasattr(results.maps, 'mean'):
            return float(results.maps.mean())
        elif isinstance(results, dict):
            if 'metrics/mAP50(B)' in results:
                return float(results['metrics/mAP50(B)'])
            elif 'maps' in results:
                if hasattr(results['maps'], 'mean'):
                    return float(results['maps'].mean())
                elif isinstance(results['maps'], (list, np.ndarray)):
                    return float(np.mean(results['maps']))
        return 0.0
    except Exception as e:
        logger.error(f"Erro ao extrair mAP: {str(e)}")
        return 0.0


class YOLOTrainer:
    """
    Classe para treinar modelos YOLOv8 para detecção de microorganismos.
    """

    def __init__(
        self,
        model_size: str = None,
        epochs: int = None,
        batch_size: int = None,
        image_size: int = None,
        pretrained: bool = None,
        output_dir: str = None,
    ):
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
        self.model_size = model_size or config.get("training.model_size", "s")
        self.epochs = epochs or config.get("training.epochs", 100)
        self.batch_size = batch_size or config.get("training.batch_size", 16)
        self.image_size = image_size or config.get("training.image_size", 640)
        self.pretrained = pretrained if pretrained is not None else config.get("training.pretrained", True)
        self.output_dir = output_dir or config.get("directories.output", "runs/train")

    def train(self, data_yaml: str, **kwargs) -> Dict[str, Any]:
        """
        Treina um modelo YOLO no dataset.

        Args:
            data_yaml: Caminho para configuração YAML do dados
            **kwargs: Argumentos adicionais para o treinamento (passados para model.train())

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
            device = "mps"
            logger.info("Treinando na GPU Apple (MPS)")
        elif torch.cuda.is_available():
            device = "0"  # Primeiro dispositivo CUDA
            logger.info("Treinando na GPU NVIDIA (CUDA)")
            logger.info(f"GPU disponível: {torch.cuda.get_device_name(0)}")
        else:
            device = "cpu"
            logger.info("Treinando na CPU (sem aceleração GPU disponível)")

        # Iniciar treinamento
        logger.info(
            f"Iniciando treinamento com configuração: "
            f"epochs={self.epochs}, batch={self.batch_size}, img_size={self.image_size}"
        )

        try:
            # Preparar argumentos para treinamento
            train_args = {
                "data": data_yaml,
                "epochs": self.epochs,
                "batch": self.batch_size,
                "imgsz": self.image_size,
                "project": self.output_dir,
                "name": f"yolov8_{self.model_size}_custom",
                "patience": 20,
                "save": True,
                "device": device,
            }

            # Adicionar argumentos extras (como lr0)
            train_args.update(kwargs)

            results = model.train(**train_args)

            logger.info("Treinamento concluído com sucesso")

            # Exportar o modelo para formato ONNX para implantação
            try:
                export_path = model.export(format="onnx")
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
            device = "mps"
        elif torch.cuda.is_available():
            device = "0"
        else:
            device = "cpu"

        # Calcular épocas totais
        if additional_epochs is None:
            additional_epochs = self.epochs

        total_epochs = model.ckpt["epoch"] + additional_epochs

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
                resume=True,
            )

            logger.info("Treinamento retomado concluído com sucesso")
            return results

        except Exception as e:
            logger.error(f"Erro durante o treinamento retomado: {str(e)}")
            raise

    def find_best_hyperparameters(
            self,
            data_yaml: str,
            checkpoint_dir: str = None,
            resume: bool = False,
            search_space: Dict[str, List] = None
    ) -> Dict[str, Any]:
        """
        Realiza uma busca por hiperparâmetros para múltiplos modelos YOLO de diferentes tamanhos,
        com gerenciamento de memória melhorado para evitar OOM (Out of Memory).

        Args:
            data_yaml: Caminho para configuração YAML dos dados
            checkpoint_dir: Diretório para salvar/carregar checkpoints da busca
            resume: Se True, tenta retomar a busca a partir do último checkpoint
            search_space: Dicionário definindo o espaço de busca personalizado
                     Ex: {"batch_sizes": [8, 16, 32], "learning_rates": [0.001, 0.01, 0.1], "model_sizes": ["n", "s", "m"]}

        Returns:
            Dicionário com os melhores hiperparâmetros encontrados para cada tamanho de modelo
        """
        # Se não especificado, usa o tamanho de modelo atual
        if checkpoint_dir is None:
            checkpoint_dir = os.path.join(self.output_dir, "hyperparam_search")

        os.makedirs(checkpoint_dir, exist_ok=True)
        checkpoint_file = os.path.join(checkpoint_dir, "hyperparam_search_state.json")
        checkpoint_file_tmp = os.path.join(checkpoint_dir, "hyperparam_search_state.tmp.json")

        if search_space is None:
            search_space = {
                "batch_sizes": [8, 16, 32],
                "learning_rates": [0.001, 0.01, 0.1],
                "model_sizes": ["n", "s", "m"],
            }

        batch_sizes = search_space["batch_sizes"]
        learning_rates = search_space["learning_rates"]
        model_sizes = search_space["model_sizes"]

        best_result = None
        best_config = None
        tested_configs = []
        model_name = ""

        # Determinar dispositivo
        if torch.backends.mps.is_available():
            device = "mps"
            logger.info("Usando GPU Apple (MPS)")
        elif torch.cuda.is_available():
            device = "0"
            logger.info(f"Usando GPU NVIDIA: {torch.cuda.get_device_name(0)}")
        else:
            device = "cpu"
            logger.info("Usando CPU (sem aceleração GPU disponível)")

        if resume and os.path.exists(checkpoint_file):
            try:
                with open(checkpoint_file, "r") as f:
                    import json
                    checkpoint_data = json.load(f)

                best_result = checkpoint_data.get("best_result")
                best_config = checkpoint_data.get("best_config")
                tested_configs = checkpoint_data.get("tested_configs", [])

                logger.info(f"Checkpoint carregado: {len(tested_configs)} configurações já testadas")

                if best_config:
                    logger.info(f"Melhor configuração até agora: {best_config}")
            except Exception as e:
                logger.error(f"Erro ao carregar checkpoint: {str(e)}")
                best_result = None
                best_config = None
                tested_configs = []

        total_configs = (len(batch_sizes) * len(learning_rates)) * len(model_sizes)
        current_config = 0

        # Testar cada tamanho de modelo - começando pelos menores para evitar OOM
        model_sizes_ordered = sorted(model_sizes, key=lambda s: "nsmltx".index(s))
        for model_size in model_sizes_ordered:
            logger.info(f"Buscando hiperparâmetros para YOLOv8{model_size}")

            # Modelo base para este tamanho
            model_name = f"yolov8{model_size}.pt" if self.pretrained else f"yolov8{model_size}.yaml"

            # Número de épocas reduzido para economizar tempo/memória
            search_epochs = min(20, self.epochs)
            logger.info(f"Usando {search_epochs} épocas para busca de hiperparâmetros")

            # Testar combinações para este tamanho de modelo
            for batch_size in batch_sizes:
                for lr in learning_rates:
                    current_config += 1

                    config_key = f"batch_{model_size}_{batch_size}_{lr}"
                    # Create a set of tested config keys for faster lookup
                    tested_config_keys = {c.get("config_key") for c in tested_configs
                                          if isinstance(c, dict) and "config_key" in c}

                    # Check if this config has been tested
                    if config_key in tested_config_keys:
                        logger.info(f"Pulando configuração já testada [{len(tested_configs)}/{total_configs}]: "
                                    f"batch_size={batch_size}, lr={lr} para YOLOv8{model_size}")
                        continue

                    run_name = f"hp_yeast_{model_size}_{batch_size}_{lr}"
                    logger.info(
                        f"Testando configuração [{current_config}/{total_configs}]: batch_size={batch_size}, lr={lr} para YOLOv8{model_size}")

                    try:
                        # Limpar manualmente a memória da GPU e CPU antes de cada teste
                        gc.collect()
                        if torch.cuda.is_available():
                            torch.cuda.empty_cache()

                        # Aguardar um momento para garantir que a memória foi liberada
                        time.sleep(1)

                        # Inicializar modelo com cuidado
                        model = None
                        model = YOLO(model_name)

                        # Configurar o treinamento com argumentos para minimizar uso de memória
                        results = model.train(
                            data=data_yaml,
                            epochs=search_epochs,
                            batch=batch_size,
                            imgsz=self.image_size,
                            project=self.output_dir,
                            name=run_name,
                            patience=5,
                            save=True,
                            device=device,
                            lr0=lr,
                            cache=False,
                            optimizer="SGD",
                        )

                        # Verificar se este é o melhor resultado para este modelo
                        # Usamos try/except porque a estrutura do results pode variar
                        try:
                            # Verificar a estrutura do resultado e extrair o mAP
                            current_map = extract_map_from_results(results)

                            if current_map > 0:
                                config_result = {
                                    "config_key": config_key,
                                    "batch_size": batch_size,
                                    "learning_rate": lr,
                                    "model_size": model_size,
                                    "map": float(current_map),
                                    "timestamp": datetime.now().isoformat()
                                }

                                tested_configs.append(config_result)

                                if best_result is None or current_map > best_result:
                                    logger.info(f"Nova melhor configuração encontrada para YOLO8{model_size}! mAP={current_map:.4f}")
                                    best_result = float(current_map)
                                    best_config = {
                                        "model_size": model_size,
                                        "batch_size": batch_size,
                                        "learning_rate": lr,
                                        "map": float(current_map),
                                    }
                                else:
                                    logger.info(
                                        f"Resultado: mAP={current_map:.4f} (melhor até agora: {best_result:.4f})")

                                checkpoint_data = {
                                    "best_result": best_result,
                                    "best_config": best_config,
                                    "tested_configs": tested_configs,
                                    "timestamp": datetime.now().isoformat(),
                                    "progress": {
                                        "total_configs": total_configs,
                                        "tested_configs": len(tested_configs),
                                        "remaining_configs": total_configs - len(tested_configs),
                                        "percent_complete": round(len(tested_configs) / total_configs * 100, 2)
                                    }
                                }

                                with open(checkpoint_file_tmp, "w") as f:
                                    import json
                                    json.dump(checkpoint_data, f, indent=4)

                                # Mover arquivo temporário para o final (operação atômica)
                                shutil.move(checkpoint_file_tmp, checkpoint_file)

                                logger.info(f"Checkpoint salvo: {checkpoint_file}")
                            else:
                                # Se não conseguimos encontrar o mAP nos resultados
                                logger.warning(
                                    f"Não foi possível extrair o mAP dos resultados. Estrutura: {type(results)}")
                                # Tentar imprimir informações sobre a estrutura para diagnóstico
                                if isinstance(results, dict):
                                    logger.debug(f"Chaves disponíveis: {list(results.keys())}")
                        except Exception as e:
                            logger.error(f"Erro ao extrair métricas: {str(e)}")

                            # Liberar memória explicitamente
                        del model
                        del results
                        gc.collect()
                        if torch.cuda.is_available():
                            torch.cuda.empty_cache()

                    except Exception as e:
                        logger.error(f"Erro ao testar configuração: {str(e)}")

                        # Mesmo em caso de erro, salvamos o progresso
                        checkpoint_data = {
                            "best_result": best_result,
                            "best_config": best_config,
                            "tested_configs": tested_configs,
                            "timestamp": datetime.now().isoformat(),
                            "last_error": {
                                "config": f"batch{batch_size}_lr{lr}",
                                "message": str(e)
                            }
                        }

                        # Primeiro escrever em arquivo temporário, depois mover
                        with open(checkpoint_file_tmp, "w") as f:
                            import json
                            json.dump(checkpoint_data, f, indent=4)

                        # Mover arquivo temporário para o final (operação atômica)
                        shutil.move(checkpoint_file_tmp, checkpoint_file)

                    # Aguardar um pouco entre testes para dar tempo ao sistema
                    time.sleep(3)

                    # Limpar memória após testar todos os learning rates para um batch size
                    gc.collect()
                    if torch.cuda.is_available():
                        torch.cuda.empty_cache()

        # Resumo geral
        logger.info("=== Resumo da Busca por Hiperparâmetros ===")
        for results in tested_configs:
            if results:
                logger.info(
                    f"YOLOv8{results.get('model_size')}: batch={results.get('batch_size')}, "
                    f"lr={results.get('learning_rate')}, mAP={results.get('map', 0):.4f}"
                )
            else:
                logger.info(f"YOLOv8{results.get('model_size')}: Falha na busca")

        # Salvar resultados em um arquivo para referência futura
        import json
        results_path = os.path.join(self.output_dir, "hyperparameter_search_results.json")
        with open(results_path, "w", encoding="utf-8") as f:
            json.dump(tested_configs, f, indent=4)
        logger.info(f"Resultados da busca por hiperparâmetros salvos em: {results_path}")

        if best_config:
            logger.info(f"Melhor configuração encontrada: {best_config}")
            answer = input(
                f"\nDeseja treinar o modelo YOLOv8{best_config['model_size']} com os melhores hiperparâmetros? (s/n): ")
            if answer.lower() in ["s", "sim", "y", "yes"]:
                try:
                    model = YOLO(model_name)
                    final_results = model.train(
                        data=data_yaml,
                        epochs=self.epochs,
                        batch=best_config["batch_size"],
                        imgsz=self.image_size,
                        project=self.output_dir,
                        name=f"yolov8_{best_config['model_size']}_optimized",
                        patience=20,
                        save=True,
                        device=device,
                        lr0=best_config["learning_rate"],
                    )

                    logger.info("Treinamento com hiperparâmetros otimizados concluído com sucesso")

                    final_map = extract_map_from_results(final_results)

                    checkpoint_data = {
                        "best_result": best_result,
                        "best_config": best_config,
                        "tested_configs": tested_configs,
                        "timestamp": datetime.now().isoformat(),
                        "final_training_completed": True,
                        "final_training_results": {
                            "maps": final_map,
                            "epochs_completed": final_results.get("epoch", 0),
                        }
                    }

                    with open(checkpoint_file_tmp, "w") as f:
                        import json
                        json.dump(checkpoint_data, f, indent=4)

                    # Mover arquivo temporário para o final (operação atômica)
                    shutil.move(checkpoint_file_tmp, checkpoint_file)

                    return best_config
                except Exception as e:
                    logger.error(f"Erro ao treinar modelo com hiperparâmetros otimizados: {str(e)}")

        if not best_config:
            logger.warning("Nenhuma configuração válida foi encontrada durante a busca")

        return best_config or {}

