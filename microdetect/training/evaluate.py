"""
Módulo para avaliação de modelos treinados.
"""

import csv
import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union

import matplotlib.pyplot as plt
import numpy as np
from ultralytics import YOLO

from microdetect.utils.config import config

logger = logging.getLogger(__name__)


class ModelEvaluator:
    """
    Classe para avaliar modelos treinados e gerar relatórios.
    """

    def __init__(self, output_dir: str = None):
        """
        Inicializa o avaliador de modelos.

        Args:
            output_dir: Diretório para salvar relatórios de avaliação
        """
        self.output_dir = output_dir or config.get("directories.reports", "reports")
        os.makedirs(self.output_dir, exist_ok=True)

    def evaluate_model(self, model_path: str, data_yaml: str) -> Dict[str, Any]:
        """
        Avalia o modelo treinado e gera métricas detalhadas.

        Args:
            model_path: Caminho para o modelo treinado (.pt)
            data_yaml: Caminho para o arquivo de configuração do dataset

        Returns:
            Dicionário com métricas de desempenho
        """
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Modelo não encontrado: {model_path}")

        # Carregar o modelo
        try:
            model = YOLO(model_path)
            logger.info(f"Modelo carregado: {model_path}")
        except Exception as e:
            logger.error(f"Erro ao carregar modelo: {str(e)}")
            raise

        # Avaliar o modelo no conjunto de teste
        logger.info("Avaliando modelo no conjunto de teste...")

        try:
            results = model.val(data=data_yaml)
            logger.info("Avaliação concluída")
        except Exception as e:
            logger.error(f"Erro durante avaliação: {str(e)}")
            raise

        # Extrair métricas
        metrics = self._extract_metrics(results)

        return metrics

    def _extract_metrics(self, results) -> Dict[str, Any]:
        """
        Extrai métricas de desempenho dos resultados da avaliação.

        Args:
            results: Objeto de resultados da validação YOLO

        Returns:
            Dicionário com métricas extraídas
        """
        # Métricas gerais
        general_metrics = {
            "Precisão (mAP50)": float(results.box.map50),
            "Precisão (mAP50-95)": float(results.box.map),
            "Recall": float(results.box.recall),
            "Precisão": float(results.box.precision),
            "F1-Score": self._calculate_f1(float(results.box.precision), float(results.box.recall)),
            "Taxa de Erro": 1.0 - float(results.box.map50),
        }

        # Métricas por classe
        class_metrics = []
        for i, class_name in enumerate(results.names.values()):
            if i < len(results.box.ap_class_index):
                idx = results.box.ap_class_index.tolist().index(i) if i in results.box.ap_class_index else -1
                if idx >= 0:
                    class_metrics.append(
                        {
                            "Classe": class_name,
                            "Precisão (AP50)": float(results.box.ap50[idx]),
                            "Recall": float(results.box.r[idx]),
                            "Precisão": float(results.box.p[idx]),
                            "F1-Score": self._calculate_f1(float(results.box.p[idx]), float(results.box.r[idx])),
                        }
                    )

        return {
            "metricas_gerais": general_metrics,
            "metricas_por_classe": class_metrics,
        }

    @staticmethod
    def _calculate_f1(precision: float, recall: float) -> float:
        """
        Calcula o F1-Score a partir da precisão e do recall.

        Args:
            precision: Valor de precisão
            recall: Valor de recall

        Returns:
            F1-Score calculado
        """
        return 2 * (precision * recall) / (precision + recall + 1e-10)

    def generate_report(self, metrics: Dict[str, Any], model_path: str) -> Dict[str, str]:
        """
        Gera relatórios detalhados de avaliação do modelo.

        Args:
            metrics: Métricas de desempenho do modelo
            model_path: Caminho para o modelo avaliado (para informações)

        Returns:
            Dicionário com caminhos para os relatórios gerados
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        model_name = os.path.basename(model_path)

        # Caminho para os arquivos de saída
        csv_path = os.path.join(self.output_dir, f"relatorio_metricas_{timestamp}.csv")
        json_path = os.path.join(self.output_dir, f"relatorio_metricas_{timestamp}.json")
        graph_path = os.path.join(self.output_dir, f"metricas_grafico_{timestamp}.png")

        # 1. Salvar resultados em CSV
        self._save_csv_report(csv_path, metrics)

        # 2. Salvar resultados em JSON
        self._save_json_report(json_path, metrics, model_path)

        # 3. Gerar gráficos
        self._generate_plots(graph_path, metrics)

        logger.info(f"Relatórios salvos em: {self.output_dir}")
        logger.info(f"- CSV: {os.path.basename(csv_path)}")
        logger.info(f"- JSON: {os.path.basename(json_path)}")
        logger.info(f"- Gráficos: {os.path.basename(graph_path)}")

        return {"csv": csv_path, "json": json_path, "graphs": graph_path}

    def _save_csv_report(self, csv_path: str, metrics: Dict[str, Any]) -> None:
        """
        Salva as métricas em formato CSV.

        Args:
            csv_path: Caminho para salvar o arquivo CSV
            metrics: Métricas de desempenho do modelo
        """
        try:
            with open(csv_path, "w", newline="") as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(["Métrica", "Valor"])

                # Métricas gerais
                for key, value in metrics["metricas_gerais"].items():
                    writer.writerow([key, f"{value:.4f}"])

                writer.writerow([])
                writer.writerow(["Classe", "Precisão (AP50)", "Recall", "Precisão", "F1-Score"])

                # Métricas por classe
                for item in metrics["metricas_por_classe"]:
                    writer.writerow(
                        [
                            item["Classe"],
                            f"{item['Precisão (AP50)']:.4f}",
                            f"{item['Recall']:.4f}",
                            f"{item['Precisão']:.4f}",
                            f"{item['F1-Score']:.4f}",
                        ]
                    )

            logger.info(f"Relatório CSV salvo em: {csv_path}")
        except Exception as e:
            logger.error(f"Erro ao salvar relatório CSV: {str(e)}")

    def _save_json_report(self, json_path: str, metrics: Dict[str, Any], model_path: str) -> None:
        """
        Salva as métricas em formato JSON com informações adicionais.

        Args:
            json_path: Caminho para salvar o arquivo JSON
            metrics: Métricas de desempenho do modelo
            model_path: Caminho para o modelo avaliado
        """
        # Adicionar informações extras
        report_data = {
            "modelo": {
                "caminho": model_path,
                "nome": os.path.basename(model_path),
                "data_avaliacao": datetime.now().isoformat(),
            },
            "metricas_gerais": metrics["metricas_gerais"],
            "metricas_por_classe": metrics["metricas_por_classe"],
        }

        try:
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(report_data, f, indent=4, ensure_ascii=False)
            logger.info(f"Relatório JSON salvo em: {json_path}")
        except Exception as e:
            logger.error(f"Erro ao salvar relatório JSON: {str(e)}")

    def _generate_plots(self, graph_path: str, metrics: Dict[str, Any]) -> None:
        """
        Gera gráficos visualizando as métricas do modelo.

        Args:
            graph_path: Caminho para salvar os gráficos
            metrics: Métricas de desempenho do modelo
        """
        try:
            plt.figure(figsize=(12, 10))

            # Gráfico de barras para métricas gerais
            plt.subplot(2, 1, 1)
            metrics_to_plot = {k: v for k, v in metrics["metricas_gerais"].items() if k != "Taxa de Erro"}
            bars = plt.bar(metrics_to_plot.keys(), metrics_to_plot.values())
            plt.title("Métricas Gerais do Modelo")
            plt.xticks(rotation=45)
            plt.ylim(0, 1)

            for bar in bars:
                height = bar.get_height()
                plt.text(
                    bar.get_x() + bar.get_width() / 2.0,
                    height + 0.01,
                    f"{height:.4f}",
                    ha="center",
                    va="bottom",
                )

            # Gráfico de barras para precisão por classe
            if metrics["metricas_por_classe"]:
                plt.subplot(2, 1, 2)
                classes = [m["Classe"] for m in metrics["metricas_por_classe"]]
                ap_values = [m["Precisão (AP50)"] for m in metrics["metricas_por_classe"]]

                bars = plt.bar(classes, ap_values)
                plt.title("Precisão (AP50) por Classe")
                plt.ylim(0, 1)

                for bar in bars:
                    height = bar.get_height()
                    plt.text(
                        bar.get_x() + bar.get_width() / 2.0,
                        height + 0.01,
                        f"{height:.4f}",
                        ha="center",
                        va="bottom",
                    )

            plt.tight_layout()
            plt.savefig(graph_path)
            logger.info(f"Gráficos salvos em: {graph_path}")

        except Exception as e:
            logger.error(f"Erro ao gerar gráficos: {str(e)}")

    def confusion_matrix(self, model_path: str, data_yaml: str) -> str:
        """
        Gera matriz de confusão para o modelo.

        Args:
            model_path: Caminho para o modelo treinado
            data_yaml: Caminho para o arquivo de configuração do dataset

        Returns:
            Caminho para a imagem da matriz de confusão
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        conf_matrix_path = os.path.join(self.output_dir, f"confusion_matrix_{timestamp}.png")

        try:
            # Carregar modelo
            model = YOLO(model_path)

            # Rodar validação para gerar matriz de confusão
            results = model.val(data=data_yaml, conf_matrix=True)

            if hasattr(results, "confusion_matrix") and hasattr(results.confusion_matrix, "plot"):
                try:
                    # Usar método integrado para plotar matriz de confusão
                    results.confusion_matrix.plot(save_dir=self.output_dir, names=results.names)
                    logger.info(f"Matriz de confusão salva em: {self.output_dir}")
                    return conf_matrix_path
                except Exception as plot_error:
                    logger.error(f"Erro ao plotar matriz de confusão: {str(plot_error)}")

                    # Fallback manual
                    self._plot_confusion_matrix_manually(results.confusion_matrix.matrix, results.names, conf_matrix_path)
                    return conf_matrix_path
            else:
                logger.warning("Matriz de confusão não disponível nos resultados")
                return ""

        except Exception as e:
            logger.error(f"Erro ao gerar matriz de confusão: {str(e)}")
            return ""

    def _plot_confusion_matrix_manually(self, matrix: np.ndarray, class_names: Dict[int, str], save_path: str) -> None:
        """
        Plota a matriz de confusão manualmente.

        Args:
            matrix: Matriz de confusão como array numpy
            class_names: Nomes das classes
            save_path: Caminho para salvar a imagem
        """
        try:
            plt.figure(figsize=(10, 8))

            # Normalizar a matriz por linha (previsões verdadeiras)
            matrix_normalized = matrix.astype("float") / (matrix.sum(axis=1, keepdims=True) + 1e-6)

            plt.imshow(matrix_normalized, interpolation="nearest", cmap=plt.cm.Blues)
            plt.title("Matriz de Confusão Normalizada")
            plt.colorbar()

            # Adicionar rótulos
            classes = list(class_names.values())
            tick_marks = np.arange(len(classes))
            plt.xticks(tick_marks, classes, rotation=45)
            plt.yticks(tick_marks, classes)

            # Adicionar valores na matriz
            thresh = matrix_normalized.max() / 2.0
            for i, j in np.ndindex(matrix_normalized.shape):
                plt.text(
                    j,
                    i,
                    f"{matrix[i, j]}\n({matrix_normalized[i, j]:.2f})",
                    ha="center",
                    va="center",
                    color="white" if matrix_normalized[i, j] > thresh else "black",
                )

            plt.ylabel("Real")
            plt.xlabel("Previsto")
            plt.tight_layout()

            plt.savefig(save_path)
            logger.info(f"Matriz de confusão manual salva em: {save_path}")

        except Exception as e:
            logger.error(f"Erro ao plotar matriz de confusão manualmente: {str(e)}")
