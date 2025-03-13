"""
Módulo para realizar validação cruzada com modelos YOLO.
"""

import json
import logging
import os
import shutil
from datetime import datetime
from typing import Any, Dict, List

import matplotlib.pyplot as plt
import numpy as np
import yaml

from microdetect.training import ModelEvaluator

logger = logging.getLogger(__name__)


class CrossValidator:
    """
    Classe para realizar validação cruzada com modelos YOLO.
    """

    def __init__(
        self,
        base_dataset_dir: str,
        output_dir: str = None,
        model_size: str = "m",
        epochs: int = 100,
        folds: int = 5,
        seed: int = 42,
    ):
        """
        Inicializa o validador cruzado.

        Args:
            base_dataset_dir: Diretório contendo o dataset
            output_dir: Diretório para salvar resultados
            model_size: Tamanho do modelo YOLO (n, s, m, l, x)
            epochs: Número de épocas para cada fold
            folds: Número de folds para validação cruzada
            seed: Semente para reprodutibilidade
        """
        self.base_dataset_dir = base_dataset_dir
        self.output_dir = output_dir or os.path.join("cv_results", datetime.now().strftime("%Y%m%d_%H%M%S"))
        self.model_size = model_size
        self.epochs = epochs
        self.folds = folds
        self.seed = seed
        self.results = []

        # Criar diretório de saída
        os.makedirs(self.output_dir, exist_ok=True)

    def run(self) -> List[Dict[str, Any]]:
        """
        Executa a validação cruzada.

        Returns:
            Lista com os resultados de cada fold
        """
        logger.info(f"Iniciando validação cruzada com {self.folds} folds")

        # Verificar estrutura do dataset
        images_dir = os.path.join(self.base_dataset_dir, "images")
        labels_dir = os.path.join(self.base_dataset_dir, "labels")

        if not (os.path.exists(images_dir) and os.path.exists(labels_dir)):
            logger.error(f"Estrutura de dataset inválida em {self.base_dataset_dir}")
            return []

        # Listar todos os arquivos
        image_files = [f for f in os.listdir(images_dir) if f.endswith((".jpg", ".jpeg", ".png"))]

        if not image_files:
            logger.error(f"Nenhuma imagem encontrada em {images_dir}")
            return []

        # Embaralhar os dados
        np.random.seed(self.seed)
        np.random.shuffle(image_files)

        # Dividir em folds
        fold_size = len(image_files) // self.folds
        folds = [image_files[i : i + fold_size] for i in range(0, len(image_files), fold_size)]

        # Ajustar o último fold se necessário
        if len(folds) > self.folds:
            folds[self.folds - 1].extend(folds[self.folds :])
            folds = folds[: self.folds]

        # Executar treinamento e validação para cada fold
        self.results = []

        for fold_idx in range(self.folds):
            logger.info(f"Iniciando Fold {fold_idx + 1}/{self.folds}")

            # Criar diretórios para este fold
            fold_dir = os.path.join(self.output_dir, f"fold_{fold_idx + 1}")
            os.makedirs(fold_dir, exist_ok=True)

            # Criar diretórios de treino e validação
            train_dir = os.path.join(fold_dir, "train")
            val_dir = os.path.join(fold_dir, "val")

            os.makedirs(os.path.join(train_dir, "images"), exist_ok=True)
            os.makedirs(os.path.join(train_dir, "labels"), exist_ok=True)
            os.makedirs(os.path.join(val_dir, "images"), exist_ok=True)
            os.makedirs(os.path.join(val_dir, "labels"), exist_ok=True)

            # Atribuir fold atual como validação, o resto como treino
            val_files = folds[fold_idx]
            train_files = [f for i, fold in enumerate(folds) if i != fold_idx for f in fold]

            # Copiar arquivos para os diretórios correspondentes
            for f in train_files:
                base_name = os.path.splitext(f)[0]
                shutil.copy(os.path.join(images_dir, f), os.path.join(train_dir, "images", f))
                label_file = f"{base_name}.txt"
                if os.path.exists(os.path.join(labels_dir, label_file)):
                    shutil.copy(os.path.join(labels_dir, label_file), os.path.join(train_dir, "labels", label_file))

            for f in val_files:
                base_name = os.path.splitext(f)[0]
                shutil.copy(os.path.join(images_dir, f), os.path.join(val_dir, "images", f))
                label_file = f"{base_name}.txt"
                if os.path.exists(os.path.join(labels_dir, label_file)):
                    shutil.copy(os.path.join(labels_dir, label_file), os.path.join(val_dir, "labels", label_file))

            # Criar arquivo data.yaml para este fold
            yaml_path = os.path.join(fold_dir, "data.yaml")

            with open(yaml_path, "w") as f:
                yaml.dump(
                    {
                        "path": fold_dir,
                        "train": "train/images",
                        "val": "val/images",
                        "nc": 3,  # Número de classes, pode precisar ser ajustado
                        "names": ["0-levedura", "1-fungo", "2-micro-alga"],  # Nomes das classes
                    },
                    f,
                )

            # Treinar o modelo para este fold
            try:
                from microdetect.training.train import YOLOTrainer

                trainer = YOLOTrainer(
                    model_size=self.model_size, epochs=self.epochs, output_dir=os.path.join(fold_dir, "runs")
                )

                results = trainer.train(yaml_path)

                # Avaliar o modelo treinado
                evaluator = ModelEvaluator(os.path.join(fold_dir, "evaluation"))
                best_model_path = os.path.join(fold_dir, "runs", "train", "weights", "best.pt")

                if os.path.exists(best_model_path):
                    metrics = evaluator.evaluate_model(best_model_path, yaml_path)

                    # Registrar resultados deste fold
                    self.results.append(
                        {
                            "fold": fold_idx + 1,
                            "train_files": len(train_files),
                            "val_files": len(val_files),
                            "model_path": best_model_path,
                            "metrics": metrics,
                        }
                    )
                else:
                    logger.error(f"Modelo não encontrado após treinamento: {best_model_path}")

            except Exception as e:
                logger.error(f"Erro durante o treinamento do fold {fold_idx + 1}: {str(e)}")

        logger.info(f"Validação cruzada concluída. Resultados salvos em {self.output_dir}")
        return self.results

    def generate_report(self) -> str:
        """
        Gera um relatório consolidado dos resultados da validação cruzada.

        Returns:
            Caminho para o relatório gerado
        """
        if not self.results:
            logger.warning("Não há resultados para gerar relatório")
            return None

        try:
            # Caminho para o relatório
            report_path = os.path.join(self.output_dir, "cross_validation_report.json")

            # Estatísticas agregadas
            avg_map50 = np.mean([r["metrics"]["metricas_gerais"]["Precisão (mAP50)"] for r in self.results])
            avg_map = np.mean([r["metrics"]["metricas_gerais"]["Precisão (mAP50-95)"] for r in self.results])
            avg_recall = np.mean([r["metrics"]["metricas_gerais"]["Recall"] for r in self.results])
            avg_precision = np.mean([r["metrics"]["metricas_gerais"]["Precisão"] for r in self.results])
            avg_f1 = np.mean([r["metrics"]["metricas_gerais"]["F1-Score"] for r in self.results])

            # Desvio padrão
            std_map50 = np.std([r["metrics"]["metricas_gerais"]["Precisão (mAP50)"] for r in self.results])

            # Relatório
            report = {
                "cross_validation": {
                    "folds": self.folds,
                    "model_size": self.model_size,
                    "epochs": self.epochs,
                    "seed": self.seed,
                },
                "average_metrics": {
                    "map50": float(avg_map50),
                    "map50_95": float(avg_map),
                    "recall": float(avg_recall),
                    "precision": float(avg_precision),
                    "f1_score": float(avg_f1),
                },
                "std_metrics": {"map50": float(std_map50)},
                "fold_results": self.results,
            }

            # Salvar relatório
            with open(report_path, "w") as f:
                json.dump(report, f, indent=4)

            logger.info(f"Relatório de validação cruzada salvo em: {report_path}")

            # Gerar gráfico
            self._plot_cv_results()

            return report_path

        except Exception as e:
            logger.error(f"Erro ao gerar relatório de validação cruzada: {str(e)}")
            return None

    def _plot_cv_results(self) -> str:
        """
        Plota os resultados da validação cruzada.

        Returns:
            Caminho para o gráfico gerado
        """
        if not self.results:
            return None

        try:
            # Extrair métricas por fold
            folds = [r["fold"] for r in self.results]
            map50 = [r["metrics"]["metricas_gerais"]["Precisão (mAP50)"] for r in self.results]
            recall = [r["metrics"]["metricas_gerais"]["Recall"] for r in self.results]
            precision = [r["metrics"]["metricas_gerais"]["Precisão"] for r in self.results]
            f1 = [r["metrics"]["metricas_gerais"]["F1-Score"] for r in self.results]

            plt.figure(figsize=(12, 8))

            width = 0.2
            ind = np.arange(len(folds))

            plt.bar(ind - width * 1.5, map50, width, label="mAP50")
            plt.bar(ind - width / 2, recall, width, label="Recall")
            plt.bar(ind + width / 2, precision, width, label="Precision")
            plt.bar(ind + width * 1.5, f1, width, label="F1-Score")

            plt.xlabel("Fold")
            plt.ylabel("Valor")
            plt.title("Métricas por Fold na Validação Cruzada")
            plt.xticks(ind, [f"Fold {i}" for i in folds])
            plt.ylim(0, 1.1)
            plt.legend(loc="lower right")
            plt.grid(axis="y", linestyle="--", alpha=0.7)

            # Adicionar média como linha horizontal
            avg_map50 = np.mean(map50)
            plt.axhline(y=avg_map50, color="r", linestyle="-", alpha=0.5)
            plt.text(len(folds) - 1, avg_map50 + 0.02, f"Média mAP50: {avg_map50:.3f}", color="r")

            # Salvar figura
            plot_path = os.path.join(self.output_dir, "cross_validation_plot.png")
            plt.tight_layout()
            plt.savefig(plot_path)

            logger.info(f"Gráfico de validação cruzada salvo em: {plot_path}")
            return plot_path

        except Exception as e:
            logger.error(f"Erro ao plotar resultados de validação cruzada: {str(e)}")
            return None
