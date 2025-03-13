"""
Módulo para avaliação de modelos treinados.
"""

import csv
import json
import logging
import os
import shutil
import threading
import time
from datetime import datetime
from functools import wraps
from typing import Any, Dict, List, Optional, Tuple, Union, Callable

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import yaml
from scipy.ndimage import gaussian_filter
from scipy.spatial.distance import squareform, pdist
from sklearn.metrics import confusion_matrix as sk_confusion_matrix
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

    def evaluate_model(
        self,
        model_path: str,
        data_yaml: str,
        conf_threshold: float = 0.25,
        iou_threshold: float = 0.7
    ) -> Dict[str, Any]:
        """
        Avalia o modelo treinado e gera métricas detalhadas.

        Args:
            model_path: Caminho para o modelo treinado (.pt)
            data_yaml: Caminho para o arquivo de configuração do dataset
            conf_threshold: Limiar de confiança para detecções (0-1)
            iou_threshold: Limiar de IoU para supressão não-máxima (0-1)

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
        logger.info(f"Avaliando modelo no conjunto de teste com conf={conf_threshold}, iou={iou_threshold}...")

        try:
            results = model.val(
                data=data_yaml,
                conf=conf_threshold,
                iou=iou_threshold
            )
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

    def optimize_threshold(
        self,
        model_path: str,
        data_yaml: str,
        metric: str = "F1-Score",
        conf_range: Tuple[float, float, float] = (0.1, 0.9, 0.1),
        iou_range: Tuple[float, float, float] = (0.5, 0.85, 0.05)
    ) -> Dict[str, Any]:
        """
        Busca os limiares ótimos de confiança e IoU para maximizar uma métrica específica.

        Args:
            model_path: Caminho para o modelo treinado
            data_yaml: Caminho para o arquivo de configuração do dataset
            metric: Métrica a ser otimizada (ex: "F1-Score", "Precisão (mAP50)", "Recall")
            conf_range: Tupla com (início, fim, passo) para limiar de confiança
            iou_range: Tupla com (início, fim, passo) para limiar de IoU

        Returns:
            Dicionário com os melhores limiares e resultados
        """
        logger.info(f"Iniciando busca por limiares ótimos para maximizar {metric}...")

        conf_thresholds = np.arange(conf_range[0], conf_range[1] + 1e-10, conf_range[2])
        iou_thresholds = np.arange(iou_range[0], iou_range[1] + 1e-10, iou_range[2])

        best_score = -1
        best_conf = None
        best_iou = None
        best_metrics = None

        # Carregar o modelo uma vez fora do loop para economizar tempo
        model = YOLO(model_path)

        # Armazenar todos os resultados para análise e visualização
        all_results = []

        # Grid search para encontrar os melhores limiares
        total_combinations = len(conf_thresholds) * len(iou_thresholds)
        current = 0

        for conf in conf_thresholds:
            for iou in iou_thresholds:
                current += 1
                logger.info(f"Testando combinação {current}/{total_combinations}: conf={conf:.2f}, iou={iou:.2f}")

                try:
                    results = model.val(data=data_yaml, conf=conf, iou=iou)
                    metrics = self._extract_metrics(results)

                    # Obter a métrica desejada
                    if metric in metrics["metricas_gerais"]:
                        score = metrics["metricas_gerais"][metric]
                    else:
                        logger.warning(f"Métrica {metric} não encontrada, usando mAP50")
                        score = metrics["metricas_gerais"]["Precisão (mAP50)"]

                    all_results.append({
                        "conf_threshold": conf,
                        "iou_threshold": iou,
                        "score": score,
                        **{k: v for k, v in metrics["metricas_gerais"].items()}
                    })

                    if score > best_score:
                        best_score = score
                        best_conf = conf
                        best_iou = iou
                        best_metrics = metrics

                except Exception as e:
                    logger.error(f"Erro ao avaliar com conf={conf:.2f}, iou={iou:.2f}: {str(e)}")

        # Salvar resultados em CSV para análise
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_path = os.path.join(self.output_dir, f"threshold_optimization_{timestamp}.csv")

        try:
            df = pd.DataFrame(all_results)
            df.to_csv(results_path, index=False)
            logger.info(f"Resultados de otimização salvos em: {results_path}")
        except Exception as e:
            logger.error(f"Erro ao salvar resultados de otimização: {str(e)}")

        # Gerar gráfico de superfície
        surface_plot_path = os.path.join(self.output_dir, f"threshold_surface_{timestamp}.png")
        self._plot_threshold_surface(all_results, metric, surface_plot_path)

        logger.info(f"Melhores limiares encontrados: conf={best_conf:.2f}, iou={best_iou:.2f} com {metric}={best_score:.4f}")

        return {
            "best_conf_threshold": best_conf,
            "best_iou_threshold": best_iou,
            "best_score": best_score,
            "best_metrics": best_metrics,
            "results_csv": results_path,
            "surface_plot": surface_plot_path
        }

    def _plot_threshold_surface(self, results: List[Dict[str, Any]], metric: str, save_path: str) -> None:
        """
        Plota um gráfico de superfície dos resultados da otimização de limiar.

        Args:
            results: Lista de resultados da otimização
            metric: Métrica utilizada na otimização
            save_path: Caminho para salvar o gráfico
        """
        try:
            # Converter para DataFrame
            df = pd.DataFrame(results)

            # Criar figura 3D
            fig = plt.figure(figsize=(12, 10))
            ax = fig.add_subplot(111, projection='3d')

            # Pivot da tabela para formato adequado
            pivot = df.pivot_table(
                index='conf_threshold',
                columns='iou_threshold',
                values='score'
            )

            # Preparar dados para o gráfico
            X, Y = np.meshgrid(pivot.columns, pivot.index)
            Z = pivot.values

            # Plotar superfície
            surf = ax.plot_surface(X, Y, Z, cmap='viridis', alpha=0.8)

            # Adicionar barra de cores
            fig.colorbar(surf, ax=ax, shrink=0.5, aspect=5)

            # Configurar rótulos
            ax.set_xlabel('IoU Threshold')
            ax.set_ylabel('Confidence Threshold')
            ax.set_zlabel(metric)
            ax.set_title(f'Optimization Surface for {metric}')

            # Encontrar e marcar o ponto máximo
            max_idx = df['score'].idxmax()
            max_conf = df.loc[max_idx, 'conf_threshold']
            max_iou = df.loc[max_idx, 'iou_threshold']
            max_score = df.loc[max_idx, 'score']

            ax.scatter([max_iou], [max_conf], [max_score], color='red', s=100, label=f'Max: {max_score:.4f}')
            ax.legend()

            # Salvar figura
            plt.tight_layout()
            plt.savefig(save_path)
            logger.info(f"Gráfico de superfície salvo em: {save_path}")

        except Exception as e:
            logger.error(f"Erro ao gerar gráfico de superfície: {str(e)}")

    def analyze_errors(
        self,
        model_path: str,
        data_yaml: str,
        dataset_dir: str,
        output_dir: str = None,
        error_type: str = "all",  # "false_positives", "false_negatives", "classification_errors", "all"
        conf_threshold: float = 0.25,
        iou_threshold: float = 0.5,
        max_samples: int = 20
    ) -> Dict[str, Any]:
        """
        Analisa e visualiza erros de detecção específicos.

        Args:
            model_path: Caminho para o modelo treinado
            data_yaml: Caminho para o arquivo de configuração do dataset
            dataset_dir: Diretório raiz do dataset
            output_dir: Diretório para salvar resultados (opcional)
            error_type: Tipo de erro a analisar
            conf_threshold: Limiar de confiança para detecções
            iou_threshold: Limiar de IoU para correspondência
            max_samples: Número máximo de exemplos a salvar

        Returns:
            Dicionário com contagens de erro e caminhos para resultados
        """
        output_dir = output_dir or os.path.join(self.output_dir, f"error_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        os.makedirs(output_dir, exist_ok=True)

        logger.info(f"Analisando erros ({error_type}) do modelo {os.path.basename(model_path)}...")

        # Diretório das imagens de teste
        test_dir = os.path.join(dataset_dir, "test", "images")
        if not os.path.exists(test_dir):
            logger.error(f"Diretório de imagens de teste não encontrado: {test_dir}")
            return {"error": "Diretório de teste não encontrado"}

        # Carregar modelo
        model = YOLO(model_path)

        # Executar detecção em todas as imagens de teste
        results = model(test_dir, conf=conf_threshold, iou=iou_threshold, save=False)

        # Preparar diretorios para salvar imagens de erro
        error_dirs = {
            "false_positives": os.path.join(output_dir, "false_positives"),
            "false_negatives": os.path.join(output_dir, "false_negatives"),
            "classification_errors": os.path.join(output_dir, "classification_errors"),
        }

        # Criar diretórios necessários
        for dir_name in error_dirs.values():
            if error_type == "all" or dir_name == error_dirs[error_type]:
                os.makedirs(dir_name, exist_ok=True)

        # Contar erros
        error_counts = {
            "false_positives": 0,
            "false_negatives": 0,
            "classification_errors": 0,
        }

        # Analisar cada resultado
        for result in results:
            # TODO: Esta implementação requer acesso aos ground truths
            # Precisa ser adaptada para acessar as anotações reais em cada imagem
            # Esta é uma versão simplificada que identifica erros com base no score de confiança

            # Para uma implementação completa, precisamos comparar as detecções
            # com as anotações reais das imagens de teste

            # Exemplo simplificado:
            if hasattr(result, 'boxes'):
                # Contar detecções de baixa confiança como potenciais FPs
                boxes = result.boxes
                if len(boxes) > 0:
                    low_conf_boxes = boxes[boxes.conf < 0.5]
                    error_counts["false_positives"] += len(low_conf_boxes)

        # Gerar relatório de erros
        report_path = os.path.join(output_dir, "error_analysis_report.json")
        with open(report_path, "w") as f:
            json.dump({
                "model": os.path.basename(model_path),
                "error_counts": error_counts,
                "conf_threshold": conf_threshold,
                "iou_threshold": iou_threshold,
                "timestamp": datetime.now().isoformat()
            }, f, indent=4)

        logger.info(f"Análise de erros concluída, resultados salvos em: {output_dir}")

        return {
            "error_counts": error_counts,
            "report_path": report_path,
            "output_dir": output_dir
        }


class SpeedBenchmark:
    """
    Classe para realizar benchmarks de velocidade de inferência em modelos.
    """

    def __init__(self, model_path: str, device: str = None):
        """
        Inicializa o benchmark de velocidade.

        Args:
            model_path: Caminho para o modelo a ser avaliado
            device: Dispositivo para execução (auto, cpu, cuda, etc.)
        """
        self.model_path = model_path
        self.device = device
        self.results = []

    def run(
        self,
        batch_sizes: List[int] = [1, 2, 4, 8, 16],
        image_sizes: List[int] = [640, 960, 1280],
        iterations: int = 50,
        warmup: int = 10
    ) -> Dict[str, Any]:
        """
        Executa benchmark de velocidade para diferentes tamanhos de batch e imagem.

        Args:
            batch_sizes: Lista de tamanhos de batch para testar
            image_sizes: Lista de tamanhos de imagem para testar
            iterations: Número de iterações para cada configuração
            warmup: Número de iterações de aquecimento

        Returns:
            Dicionário com resultados do benchmark
        """
        logger.info(f"Iniciando benchmark de velocidade para modelo {os.path.basename(self.model_path)}")

        try:
            # Carregar modelo
            model = YOLO(self.model_path)
            if self.device:
                model.to(self.device)

            # Preparar variáveis para resultados
            self.results = []

            # Executar benchmark para cada combinação
            for img_size in image_sizes:
                for batch_size in batch_sizes:
                    logger.info(f"Testando: batch_size={batch_size}, img_size={img_size}")

                    # Criar dados sintéticos para o teste
                    dummy_input = np.random.randint(0, 255,
                                                   (batch_size, img_size, img_size, 3),
                                                   dtype=np.uint8)

                    # Warmup para estabilizar a execução
                    for _ in range(warmup):
                        _ = model(dummy_input)

                    # Medir tempo para cada iteração
                    latencies = []

                    for i in range(iterations):
                        start_time = time.time()
                        _ = model(dummy_input)
                        end_time = time.time()

                        latency = (end_time - start_time) * 1000  # em ms
                        latencies.append(latency)

                    # Calcular estatísticas
                    avg_latency = np.mean(latencies)
                    std_latency = np.std(latencies)
                    min_latency = np.min(latencies)
                    max_latency = np.max(latencies)
                    p95_latency = np.percentile(latencies, 95)
                    fps = 1000 / avg_latency * batch_size

                    # Registrar resultados
                    self.results.append({
                        "batch_size": batch_size,
                        "image_size": img_size,
                        "avg_latency_ms": avg_latency,
                        "std_latency_ms": std_latency,
                        "min_latency_ms": min_latency,
                        "max_latency_ms": max_latency,
                        "p95_latency_ms": p95_latency,
                        "fps": fps,
                        "samples_per_second": batch_size * fps
                    })

                    logger.info(f"Resultado: Latência={avg_latency:.2f}ms, FPS={fps:.2f}, Amostras/seg={batch_size * fps:.2f}")

            return {
                "model": os.path.basename(self.model_path),
                "device": self.device or "auto",
                "results": self.results
            }

        except Exception as e:
            logger.error(f"Erro durante benchmark: {str(e)}")
            return {"error": str(e)}

    def save_results(self, output_path: str) -> None:
        """
        Salva os resultados do benchmark em CSV.

        Args:
            output_path: Caminho para salvar o arquivo CSV
        """
        if not self.results:
            logger.warning("Não há resultados para salvar")
            return

        try:
            df = pd.DataFrame(self.results)
            df.to_csv(output_path, index=False)
            logger.info(f"Resultados do benchmark salvos em: {output_path}")
        except Exception as e:
            logger.error(f"Erro ao salvar resultados: {str(e)}")

    def plot_results(self, output_path: str = None) -> str:
        """
        Gera gráficos com os resultados do benchmark.

        Args:
            output_path: Caminho para salvar o gráfico

        Returns:
            Caminho para o gráfico gerado
        """
        if not self.results:
            logger.warning("Não há resultados para plotar")
            return None

        try:
            # Criar DataFrame para facilitar a visualização
            df = pd.DataFrame(self.results)

            # Configurar figura
            fig, axs = plt.subplots(2, 1, figsize=(12, 10))

            # Primeiro gráfico: FPS vs Tamanho do Batch para diferentes tamanhos de imagem
            for img_size in df["image_size"].unique():
                subset = df[df["image_size"] == img_size]
                axs[0].plot(
                    subset["batch_size"],
                    subset["fps"],
                    marker="o",
                    label=f"Imagem {img_size}x{img_size}"
                )

            axs[0].set_xlabel("Tamanho do Batch")
            axs[0].set_ylabel("FPS")
            axs[0].set_title("Desempenho (FPS) vs Tamanho do Batch")
            axs[0].grid(True)
            axs[0].legend()

            # Segundo gráfico: Amostras/segundo vs Tamanho da Imagem para diferentes tamanhos de batch
            for batch in df["batch_size"].unique():
                subset = df[df["batch_size"] == batch]
                axs[1].plot(
                    subset["image_size"],
                    subset["samples_per_second"],
                    marker="o",
                    label=f"Batch {batch}"
                )

            axs[1].set_xlabel("Tamanho da Imagem")
            axs[1].set_ylabel("Amostras/segundo")
            axs[1].set_title("Throughput vs Tamanho da Imagem")
            axs[1].grid(True)
            axs[1].legend()

            plt.tight_layout()

            # Salvar figura
            if output_path:
                plt.savefig(output_path)
                logger.info(f"Gráfico salvo em: {output_path}")
                return output_path
            else:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                default_path = f"benchmark_results_{timestamp}.png"
                plt.savefig(default_path)
                logger.info(f"Gráfico salvo em: {default_path}")
                return default_path

        except Exception as e:
            logger.error(f"Erro ao plotar resultados: {str(e)}")
            return None


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
        seed: int = 42
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
        image_files = [f for f in os.listdir(images_dir) if f.endswith(('.jpg', '.jpeg', '.png'))]

        if not image_files:
            logger.error(f"Nenhuma imagem encontrada em {images_dir}")
            return []

        # Embaralhar os dados
        np.random.seed(self.seed)
        np.random.shuffle(image_files)

        # Dividir em folds
        fold_size = len(image_files) // self.folds
        folds = [image_files[i:i + fold_size] for i in range(0, len(image_files), fold_size)]

        # Ajustar o último fold se necessário
        if len(folds) > self.folds:
            folds[self.folds-1].extend(folds[self.folds:])
            folds = folds[:self.folds]

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
                shutil.copy(
                    os.path.join(images_dir, f),
                    os.path.join(train_dir, "images", f)
                )
                label_file = f"{base_name}.txt"
                if os.path.exists(os.path.join(labels_dir, label_file)):
                    shutil.copy(
                        os.path.join(labels_dir, label_file),
                        os.path.join(train_dir, "labels", label_file)
                    )

            for f in val_files:
                base_name = os.path.splitext(f)[0]
                shutil.copy(
                    os.path.join(images_dir, f),
                    os.path.join(val_dir, "images", f)
                )
                label_file = f"{base_name}.txt"
                if os.path.exists(os.path.join(labels_dir, label_file)):
                    shutil.copy(
                        os.path.join(labels_dir, label_file),
                        os.path.join(val_dir, "labels", label_file)
                    )

            # Criar arquivo data.yaml para este fold
            yaml_path = os.path.join(fold_dir, "data.yaml")

            with open(yaml_path, "w") as f:
                yaml.dump({
                    "path": fold_dir,
                    "train": "train/images",
                    "val": "val/images",
                    "nc": 3,  # Número de classes, pode precisar ser ajustado
                    "names": ["0-levedura", "1-fungo", "2-micro-alga"]  # Nomes das classes
                }, f)

            # Treinar o modelo para este fold
            try:
                from microdetect.training.train import YOLOTrainer

                trainer = YOLOTrainer(
                    model_size=self.model_size,
                    epochs=self.epochs,
                    output_dir=os.path.join(fold_dir, "runs")
                )

                results = trainer.train(yaml_path)

                # Avaliar o modelo treinado
                evaluator = ModelEvaluator(os.path.join(fold_dir, "evaluation"))
                best_model_path = os.path.join(fold_dir, "runs", "train", "weights", "best.pt")

                if os.path.exists(best_model_path):
                    metrics = evaluator.evaluate_model(best_model_path, yaml_path)

                    # Registrar resultados deste fold
                    self.results.append({
                        "fold": fold_idx + 1,
                        "train_files": len(train_files),
                        "val_files": len(val_files),
                        "model_path": best_model_path,
                        "metrics": metrics
                    })
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
                    "seed": self.seed
                },
                "average_metrics": {
                    "map50": float(avg_map50),
                    "map50_95": float(avg_map),
                    "recall": float(avg_recall),
                    "precision": float(avg_precision),
                    "f1_score": float(avg_f1)
                },
                "std_metrics": {
                    "map50": float(std_map50)
                },
                "fold_results": self.results
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

            plt.bar(ind - width*1.5, map50, width, label='mAP50')
            plt.bar(ind - width/2, recall, width, label='Recall')
            plt.bar(ind + width/2, precision, width, label='Precision')
            plt.bar(ind + width*1.5, f1, width, label='F1-Score')

            plt.xlabel('Fold')
            plt.ylabel('Valor')
            plt.title('Métricas por Fold na Validação Cruzada')
            plt.xticks(ind, [f'Fold {i}' for i in folds])
            plt.ylim(0, 1.1)
            plt.legend(loc='lower right')
            plt.grid(axis='y', linestyle='--', alpha=0.7)

            # Adicionar média como linha horizontal
            avg_map50 = np.mean(map50)
            plt.axhline(y=avg_map50, color='r', linestyle='-', alpha=0.5)
            plt.text(len(folds)-1, avg_map50+0.02, f'Média mAP50: {avg_map50:.3f}', color='r')

            # Salvar figura
            plot_path = os.path.join(self.output_dir, "cross_validation_plot.png")
            plt.tight_layout()
            plt.savefig(plot_path)

            logger.info(f"Gráfico de validação cruzada salvo em: {plot_path}")
            return plot_path

        except Exception as e:
            logger.error(f"Erro ao plotar resultados de validação cruzada: {str(e)}")
            return None


class ResourceMonitor:
    """
    Classe para monitorar recursos durante inferência ou treinamento.
    """

    def __init__(self, interval: float = 0.5):
        """
        Inicializa o monitor de recursos.

        Args:
            interval: Intervalo de tempo entre medições (segundos)
        """
        self.interval = interval
        self.running = False
        self.monitoring_thread = None
        self.measurements = []
        self.start_time = None

    def start(self):
        """Inicia o monitoramento de recursos."""
        if self.running:
            logger.warning("Monitoramento já está em execução")
            return

        self.running = True
        self.measurements = []
        self.start_time = time.time()

        # Iniciar thread de monitoramento
        self.monitoring_thread = threading.Thread(target=self._monitor_resources)
        self.monitoring_thread.daemon = True
        self.monitoring_thread.start()

        logger.info("Monitoramento de recursos iniciado")

    def stop(self) -> Dict[str, Any]:
        """
        Para o monitoramento e retorna estatísticas.

        Returns:
            Dicionário com estatísticas de uso de recursos
        """
        if not self.running:
            logger.warning("Monitoramento não está em execução")
            return {}

        self.running = False

        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=2*self.interval)

        logger.info("Monitoramento de recursos finalizado")

        # Calcular estatísticas
        if not self.measurements:
            return {"error": "Nenhuma medição realizada"}

        df = pd.DataFrame(self.measurements)

        # Estatísticas de CPU e memória
        cpu_avg = df["cpu_percent"].mean()
        cpu_max = df["cpu_percent"].max()
        mem_avg = df["memory_percent"].mean()
        mem_max = df["memory_percent"].max()

        # Estatísticas de GPU, se disponíveis
        gpu_stats = {}
        if "gpu_memory_used" in df.columns:
            gpu_avg = df["gpu_memory_percent"].mean()
            gpu_max = df["gpu_memory_percent"].max()
            gpu_mem_avg = df["gpu_memory_used"].mean()
            gpu_mem_max = df["gpu_memory_used"].max()

            gpu_stats = {
                "gpu_percent_avg": float(gpu_avg),
                "gpu_percent_max": float(gpu_max),
                "gpu_memory_used_avg": float(gpu_mem_avg),
                "gpu_memory_used_max": float(gpu_mem_max)
            }

        return {
            "duration": time.time() - self.start_time,
            "measurements_count": len(self.measurements),
            "cpu_percent_avg": float(cpu_avg),
            "cpu_percent_max": float(cpu_max),
            "memory_percent_avg": float(mem_avg),
            "memory_percent_max": float(mem_max),
            **gpu_stats
        }

    def _monitor_resources(self):
        """Função interna para monitorar recursos continuamente."""
        import psutil

        # Tentar importar módulo para GPU (opcional)
        try:
            import torch
            has_cuda = torch.cuda.is_available()
        except ImportError:
            has_cuda = False

        while self.running:
            # Coletar estatísticas de CPU e memória
            cpu_percent = psutil.cpu_percent()
            memory = psutil.virtual_memory()

            measurement = {
                "timestamp": time.time() - self.start_time,
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_used": memory.used
            }

            # Adicionar estatísticas de GPU, se disponíveis
            if has_cuda:
                try:
                    gpu_mem_alloc = torch.cuda.memory_allocated()
                    gpu_mem_reserved = torch.cuda.memory_reserved()
                    gpu_max_mem = torch.cuda.get_device_properties(0).total_memory

                    measurement.update({
                        "gpu_memory_used": gpu_mem_alloc,
                        "gpu_memory_reserved": gpu_mem_reserved,
                        "gpu_memory_percent": 100 * gpu_mem_alloc / gpu_max_mem
                    })
                except Exception:
                    pass

            self.measurements.append(measurement)

            # Aguardar próximo intervalo
            time.sleep(self.interval)

    def plot_usage(self, output_path: str = None) -> str:
        """
        Plota gráficos de uso de recursos ao longo do tempo.

        Args:
            output_path: Caminho para salvar o gráfico (opcional)

        Returns:
            Caminho para o gráfico gerado
        """
        if not self.measurements:
            logger.warning("Não há medições para plotar")
            return None

        try:
            df = pd.DataFrame(self.measurements)

            # Criar figura
            fig, axs = plt.subplots(2, 1, figsize=(12, 10), sharex=True)

            # Gráfico de CPU
            axs[0].plot(df["timestamp"], df["cpu_percent"], label="CPU %")
            axs[0].set_ylabel("Uso de CPU (%)")
            axs[0].set_title("Uso de CPU ao Longo do Tempo")
            axs[0].grid(True)
            axs[0].set_ylim(0, 100)

            # Gráfico de Memória
            axs[1].plot(df["timestamp"], df["memory_percent"], label="Memória %")

            # Adicionar GPU, se disponível
            if "gpu_memory_percent" in df.columns:
                axs[1].plot(df["timestamp"], df["gpu_memory_percent"], label="GPU %")

            axs[1].set_xlabel("Tempo (s)")
            axs[1].set_ylabel("Uso de Memória (%)")
            axs[1].set_title("Uso de Memória ao Longo do Tempo")
            axs[1].grid(True)
            axs[1].set_ylim(0, 100)
            axs[1].legend()

            plt.tight_layout()

            # Salvar gráfico
            if output_path:
                plt.savefig(output_path)
                logger.info(f"Gráfico de uso de recursos salvo em: {output_path}")
                return output_path
            else:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                default_path = f"resource_usage_{timestamp}.png"
                plt.savefig(default_path)
                logger.info(f"Gráfico de uso de recursos salvo em: {default_path}")
                return default_path

        except Exception as e:
            logger.error(f"Erro ao plotar uso de recursos: {str(e)}")
            return None


class StatisticalAnalyzer:
    """
    Classe para realizar análises estatísticas de detecções.
    """

    def __init__(self, output_dir: str = None):
        """
        Inicializa o analisador estatístico.

        Args:
            output_dir: Diretório para salvar resultados
        """
        self.output_dir = output_dir or "analysis_results"
        os.makedirs(self.output_dir, exist_ok=True)

    def generate_density_map(
            self,
            detections: List[Dict],
            image_size: Tuple[int, int],
            output_path: Optional[str] = None,
            sigma: float = 10.0,
            by_class: bool = False
    ) -> Union[str, Dict[str, str]]:
        """
        Gera mapas de densidade a partir de detecções.

        Args:
            detections: Lista de detecções com coordenadas
            image_size: Tamanho da imagem (largura, altura)
            output_path: Caminho para salvar o mapa (opcional)
            sigma: Parâmetro de suavização para a densidade
            by_class: Se True, gera mapas separados por classe

        Returns:
            Caminho para o mapa de densidade gerado ou dicionário com caminhos por classe
        """
        if not output_path:
            output_path = os.path.join(self.output_dir, "density_map.png")

        # Se análise separada por classe for solicitada
        if by_class:
            # Obter classes únicas
            unique_classes = set(det['class'] for det in detections)
            result_paths = {}

            # Gerar um mapa para cada classe
            for cls in unique_classes:
                # Filtrar detecções para esta classe
                class_detections = [det for det in detections if det['class'] == cls]

                # Definir caminho de saída para esta classe
                class_output_path = os.path.join(
                    os.path.dirname(output_path),
                    f"density_map_class_{cls}{os.path.splitext(output_path)[1]}"
                )

                # Gerar mapa para esta classe
                result_paths[str(cls)] = self._generate_single_density_map(
                    class_detections, image_size, class_output_path, sigma, class_name=str(cls)
                )

            # Gerar mapa para todas as classes
            all_path = self._generate_single_density_map(detections, image_size, output_path, sigma)
            result_paths["all"] = all_path

            return result_paths
        else:
            # Gerar um único mapa com todas as detecções
            return self._generate_single_density_map(detections, image_size, output_path, sigma)

    def _generate_single_density_map(
            self,
            detections: List[Dict],
            image_size: Tuple[int, int],
            output_path: str,
            sigma: float,
            class_name: Optional[str] = None
    ) -> str:
        """
        Gera um único mapa de densidade para as detecções fornecidas.

        Args:
            detections: Lista de detecções
            image_size: Tamanho da imagem
            output_path: Caminho para salvar o mapa
            sigma: Parâmetro de suavização
            class_name: Nome da classe (para título)

        Returns:
            Caminho para o mapa de densidade gerado
        """
        # Inicializar mapa em branco
        density_map = np.zeros(image_size[::-1])  # Altura, largura

        # Adicionar pontos para cada detecção
        for det in detections:
            x, y = int(det['x_center'] * image_size[0]), int(det['y_center'] * image_size[1])
            if 0 <= x < image_size[0] and 0 <= y < image_size[1]:
                density_map[y, x] += 1

        # Aplicar filtro gaussiano para suavização
        density_map = gaussian_filter(density_map, sigma=sigma)

        # Normalizar para visualização
        if density_map.max() > 0:
            density_map = density_map / density_map.max()

        # Plotar e salvar
        plt.figure(figsize=(10, 8))
        plt.imshow(density_map, cmap='jet')
        plt.colorbar(label='Densidade normalizada')

        title = 'Mapa de Densidade de Detecções'
        if class_name is not None:
            title += f' - Classe {class_name}'
        plt.title(title)

        plt.tight_layout()
        plt.savefig(output_path)
        plt.close()

        logger.info(f"Mapa de densidade salvo em: {output_path}")
        return output_path

    def analyze_size_distribution(
            self,
            detections: List[Dict],
            output_dir: Optional[str] = None,
            by_class: bool = True
    ) -> Dict[str, str]:
        """
        Analisa a distribuição de tamanho dos objetos detectados.

        Args:
            detections: Lista de detecções com dimensões
            output_dir: Diretório para salvar os gráficos
            by_class: Se True, gera análise separada por classe

        Returns:
            Dicionário com caminhos para os gráficos gerados
        """
        if output_dir is None:
            output_dir = self.output_dir

        os.makedirs(output_dir, exist_ok=True)

        # Extrair dimensões
        sizes = []
        classes = []

        for det in detections:
            width = det.get('width', 0)
            height = det.get('height', 0)
            size = np.sqrt(width * height)  # Medida de tamanho (média geométrica)

            sizes.append(size)
            classes.append(det.get('class', 0))

        # Gráfico geral
        plt.figure(figsize=(10, 6))
        plt.hist(sizes, bins=30, alpha=0.7)
        plt.xlabel('Tamanho (pixels)')
        plt.ylabel('Frequência')
        plt.title('Distribuição de Tamanho de Objetos Detectados')
        plt.grid(alpha=0.3)

        all_sizes_path = os.path.join(output_dir, 'size_distribution_all.png')
        plt.savefig(all_sizes_path)
        plt.close()

        result_paths = {'all': all_sizes_path}

        # Gráficos por classe
        if by_class and len(set(classes)) > 1:
            class_names = sorted(set(classes))

            plt.figure(figsize=(12, 8))
            for cls in class_names:
                cls_sizes = [size for size, c in zip(sizes, classes) if c == cls]
                plt.hist(cls_sizes, bins=20, alpha=0.7, label=f'Classe {cls}')

            plt.xlabel('Tamanho (pixels)')
            plt.ylabel('Frequência')
            plt.title('Distribuição de Tamanho por Classe')
            plt.legend()
            plt.grid(alpha=0.3)

            by_class_path = os.path.join(output_dir, 'size_distribution_by_class.png')
            plt.savefig(by_class_path)
            plt.close()

            result_paths['by_class'] = by_class_path

            # Gráficos individuais para cada classe
            for cls in class_names:
                cls_sizes = [size for size, c in zip(sizes, classes) if c == cls]

                plt.figure(figsize=(10, 6))
                plt.hist(cls_sizes, bins=20, alpha=0.7, color=f'C{cls_names.index(cls)}')
                plt.xlabel('Tamanho (pixels)')
                plt.ylabel('Frequência')
                plt.title(f'Distribuição de Tamanho - Classe {cls}')
                plt.grid(alpha=0.3)

                class_path = os.path.join(output_dir, f'size_distribution_class_{cls}.png')
                plt.savefig(class_path)
                plt.close()

                result_paths[f'class_{cls}'] = class_path

        # Salvar dados em CSV para análise adicional
        df = pd.DataFrame({'tamanho': sizes, 'classe': classes})
        df.to_csv(os.path.join(output_dir, 'size_distribution_data.csv'), index=False)

        # Estatísticas básicas
        stats = {}
        stats['all'] = {
            'mean': np.mean(sizes),
            'median': np.median(sizes),
            'std': np.std(sizes),
            'min': np.min(sizes),
            'max': np.max(sizes),
            'count': len(sizes)
        }

        for cls in set(classes):
            cls_sizes = [size for size, c in zip(sizes, classes) if c == cls]
            stats[f'class_{cls}'] = {
                'mean': np.mean(cls_sizes),
                'median': np.median(cls_sizes),
                'std': np.std(cls_sizes),
                'min': np.min(cls_sizes),
                'max': np.max(cls_sizes),
                'count': len(cls_sizes)
            }

        # Salvar estatísticas em JSON
        stats_path = os.path.join(output_dir, 'size_stats.json')
        with open(stats_path, 'w') as f:
            json.dump(stats, f, indent=4)

        result_paths['stats'] = stats_path

        logger.info(f"Análise de distribuição de tamanho concluída. Resultados em: {output_dir}")
        return result_paths

    def analyze_spatial_relationships(
            self,
            detections: List[Dict],
            output_dir: Optional[str] = None,
            min_distance: float = 0.02,
            by_class: bool = True
    ) -> Dict[str, str]:
        """
        Analisa relações espaciais entre detecções.

        Args:
            detections: Lista de detecções com coordenadas
            output_dir: Diretório para salvar os gráficos
            min_distance: Distância mínima para considerar agrupamento
            by_class: Se True, analisa relações entre classes

        Returns:
            Dicionário com caminhos para gráficos e resultados gerados
        """
        if output_dir is None:
            output_dir = self.output_dir

        os.makedirs(output_dir, exist_ok=True)
        result_paths = {}

        # Extrair coordenadas
        coords = []
        classes = []

        for det in detections:
            coords.append([det.get('x_center', 0), det.get('y_center', 0)])
            classes.append(det.get('class', 0))

        coords = np.array(coords)

        # Verificar se há pontos suficientes para análise
        if len(coords) < 2:
            logger.warning("Número insuficiente de detecções para análise espacial")
            return {'error': 'Número insuficiente de detecções'}

        # Scatter plot geral das detecções
        plt.figure(figsize=(10, 10))
        unique_classes = sorted(set(classes))

        for cls in unique_classes:
            idx = [i for i, c in enumerate(classes) if c == cls]
            plt.scatter(coords[idx, 0], coords[idx, 1], label=f'Classe {cls}', alpha=0.7)

        plt.xlabel('Posição X')
        plt.ylabel('Posição Y')
        plt.title('Distribuição Espacial de Detecções')
        plt.legend()
        plt.grid(alpha=0.3)
        plt.xlim(0, 1)
        plt.ylim(0, 1)

        scatter_path = os.path.join(output_dir, 'spatial_scatter.png')
        plt.savefig(scatter_path)
        plt.close()

        result_paths['scatter'] = scatter_path

        # Calcular matriz de distâncias
        if len(coords) > 1:
            dist_matrix = squareform(pdist(coords))

            # Histograma de distâncias
            plt.figure(figsize=(10, 6))

            # Obter as distâncias entre pontos diferentes
            distances = dist_matrix[np.triu_indices_from(dist_matrix, k=1)]
            plt.hist(distances, bins=30, alpha=0.7)
            plt.xlabel('Distância')
            plt.ylabel('Frequência')
            plt.title('Distribuição de Distâncias entre Detecções')
            plt.grid(alpha=0.3)

            distance_hist_path = os.path.join(output_dir, 'distance_histogram.png')
            plt.savefig(distance_hist_path)
            plt.close()

            result_paths['distance_hist'] = distance_hist_path

            # Identificar agrupamentos (clusters)
            clusters = []
            visited = set()

            for i in range(len(coords)):
                if i in visited:
                    continue

                cluster = [i]
                visited.add(i)

                # Busca em largura para encontrar pontos próximos
                queue = [i]
                while queue:
                    current = queue.pop(0)

                    # Encontrar vizinhos próximos
                    neighbors = [j for j in range(len(coords)) if
                                 dist_matrix[current, j] < min_distance and j not in visited]

                    for neighbor in neighbors:
                        visited.add(neighbor)
                        cluster.append(neighbor)
                        queue.append(neighbor)

                if len(cluster) > 1:  # Ignorar pontos isolados
                    clusters.append(cluster)

            # Plotar clusters
            plt.figure(figsize=(10, 10))

            # Plotar todos os pontos em cinza claro
            plt.scatter(coords[:, 0], coords[:, 1], c='lightgray', alpha=0.3)

            # Plotar clusters com cores diferentes
            for i, cluster in enumerate(clusters):
                plt.scatter(coords[cluster, 0], coords[cluster, 1],
                            label=f'Cluster {i + 1} (n={len(cluster)})', alpha=0.7)

            plt.xlabel('Posição X')
            plt.ylabel('Posição Y')
            plt.title(f'Clusters Identificados (dist < {min_distance})')
            plt.legend()
            plt.grid(alpha=0.3)
            plt.xlim(0, 1)
            plt.ylim(0, 1)

            clusters_path = os.path.join(output_dir, 'spatial_clusters.png')
            plt.savefig(clusters_path)
            plt.close()

            result_paths['clusters'] = clusters_path

            # Análise de relações entre classes, se solicitado e se houver múltiplas classes
            if by_class and len(unique_classes) > 1:
                # Calcular matriz de co-ocorrência de classes em clusters
                cooccurrence = np.zeros((len(unique_classes), len(unique_classes)))

                for cluster in clusters:
                    cluster_classes = [classes[i] for i in cluster]
                    for i, cls1 in enumerate(unique_classes):
                        for j, cls2 in enumerate(unique_classes):
                            # Contar quantas vezes as classes co-ocorrem no mesmo cluster
                            if cls1 in cluster_classes and cls2 in cluster_classes:
                                cooccurrence[i, j] += 1

                # Normalizar a matriz
                class_counts = np.array([classes.count(cls) for cls in unique_classes])
                expected = np.outer(class_counts, class_counts) / len(detections)

                # Calcular razão de co-ocorrência observada vs. esperada
                # (Evitar divisão por zero)
                ratio = np.zeros_like(cooccurrence)
                for i in range(len(unique_classes)):
                    for j in range(len(unique_classes)):
                        if expected[i, j] > 0:
                            ratio[i, j] = cooccurrence[i, j] / expected[i, j]
                        else:
                            ratio[i, j] = 1.0

                # Plotar mapa de calor da razão de co-ocorrência
                plt.figure(figsize=(10, 8))
                plt.imshow(ratio, cmap='viridis')
                plt.colorbar(label='Razão Observada/Esperada')
                plt.title('Razão de Co-ocorrência entre Classes')
                plt.xticks(range(len(unique_classes)), [f'Classe {cls}' for cls in unique_classes])
                plt.yticks(range(len(unique_classes)), [f'Classe {cls}' for cls in unique_classes])

                class_relation_path = os.path.join(output_dir, 'class_relations.png')
                plt.savefig(class_relation_path)
                plt.close()

                result_paths['class_relations'] = class_relation_path

        # Salvar resultados em formato JSON
        analysis_data = {
            'detection_count': len(detections),
            'class_counts': {cls: classes.count(cls) for cls in unique_classes},
        }

        if len(coords) > 1:
            analysis_data.update({
                'mean_distance': float(np.mean(distances)),
                'median_distance': float(np.median(distances)),
                'min_distance': float(np.min(distances)),
                'max_distance': float(np.max(distances)),
                'cluster_count': len(clusters),
                'cluster_sizes': [len(cluster) for cluster in clusters],
            })

        data_path = os.path.join(output_dir, 'spatial_analysis.json')
        with open(data_path, 'w') as f:
            json.dump(analysis_data, f, indent=4)

        result_paths['data'] = data_path

        logger.info(f"Análise espacial concluída. Resultados em: {output_dir}")
        return result_paths

    def analyze_temporal_data(
            self,
            time_series_data: List[Dict[str, Any]],
            output_dir: Optional[str] = None,
            date_format: str = '%Y-%m-%d'
    ) -> Dict[str, str]:
        """
        Analisa mudanças ao longo do tempo nas detecções.

        Args:
            time_series_data: Lista de dicionários com dados de séries temporais
            output_dir: Diretório para salvar os gráficos
            date_format: Formato da data/hora nos dados

        Returns:
            Dicionário com caminhos para os gráficos gerados
        """
        if output_dir is None:
            output_dir = self.output_dir

        os.makedirs(output_dir, exist_ok=True)
        result_paths = {}

        # Converter para DataFrame para facilitar a análise
        df = pd.DataFrame(time_series_data)

        if 'timestamp' not in df.columns:
            logger.error("Coluna 'timestamp' não encontrada nos dados temporais")
            return {'error': 'Coluna timestamp não encontrada'}

        # Converter timestamps para datetime
        try:
            df['timestamp'] = pd.to_datetime(df['timestamp'], format=date_format)
            df = df.sort_values('timestamp')
        except Exception as e:
            logger.error(f"Erro ao converter timestamps: {str(e)}")
            return {'error': f'Erro ao converter timestamps: {str(e)}'}

        # Gráfico de contagem total ao longo do tempo
        plt.figure(figsize=(12, 6))
        plt.plot(df['timestamp'], df['count'], marker='o', linestyle='-')
        plt.xlabel('Data')
        plt.ylabel('Contagem Total')
        plt.title('Contagem de Detecções ao Longo do Tempo')
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.grid(alpha=0.3)

        total_count_path = os.path.join(output_dir, 'temporal_total_count.png')
        plt.savefig(total_count_path)
        plt.close()

        result_paths['total_count'] = total_count_path

        # Verificar se temos dados de contagem por classe
        if 'class_counts' in df.columns:
            # Gráfico com linhas separadas por classe
            plt.figure(figsize=(12, 6))

            # Obter todas as classes que aparecem nos dados
            all_classes = set()
            for counts in df['class_counts']:
                all_classes.update(counts.keys())

            all_classes = sorted(all_classes)

            for cls in all_classes:
                counts = [row['class_counts'].get(cls, 0) for _, row in df.iterrows()]
                plt.plot(df['timestamp'], counts, marker='o', linestyle='-', label=f'Classe {cls}')

            plt.xlabel('Data')
            plt.ylabel('Contagem')
            plt.title('Contagem de Detecções por Classe ao Longo do Tempo')
            plt.legend()
            plt.xticks(rotation=45)
            plt.tight_layout()
            plt.grid(alpha=0.3)

            by_class_path = os.path.join(output_dir, 'temporal_by_class.png')
            plt.savefig(by_class_path)
            plt.close()

            result_paths['by_class'] = by_class_path

            # Gráfico de área empilhada para visualizar proporções
            plt.figure(figsize=(12, 6))

            # Preparar dados para gráfico de área
            class_data = {cls: [] for cls in all_classes}

            for _, row in df.iterrows():
                for cls in all_classes:
                    class_data[cls].append(row['class_counts'].get(cls, 0))

            # Plotar gráfico de área empilhada
            plt.stackplot(df['timestamp'],
                          [class_data[cls] for cls in all_classes],
                          labels=[f'Classe {cls}' for cls in all_classes],
                          alpha=0.7)

            plt.xlabel('Data')
            plt.ylabel('Contagem')
            plt.title('Proporção de Classes ao Longo do Tempo')
            plt.legend(loc='upper left')
            plt.xticks(rotation=45)
            plt.tight_layout()

            stacked_path = os.path.join(output_dir, 'temporal_stacked.png')
            plt.savefig(stacked_path)
            plt.close()

            result_paths['stacked'] = stacked_path

        # Calcular taxa de crescimento
        if len(df) > 1:
            df['growth_rate'] = df['count'].pct_change() * 100

            plt.figure(figsize=(12, 6))
            plt.bar(df['timestamp'][1:], df['growth_rate'][1:], alpha=0.7)
            plt.axhline(y=0, color='r', linestyle='-', alpha=0.3)
            plt.xlabel('Data')
            plt.ylabel('Taxa de Crescimento (%)')
            plt.title('Taxa de Crescimento ao Longo do Tempo')
            plt.xticks(rotation=45)
            plt.tight_layout()
            plt.grid(alpha=0.3)

            growth_path = os.path.join(output_dir, 'temporal_growth_rate.png')
            plt.savefig(growth_path)
            plt.close()

            result_paths['growth_rate'] = growth_path

        # Salvar dados processados em CSV
        df.to_csv(os.path.join(output_dir, 'temporal_data.csv'), index=False)

        # Calcular estatísticas resumidas
        stats = {
            'start_date': df['timestamp'].min().strftime(date_format),
            'end_date': df['timestamp'].max().strftime(date_format),
            'timepoints': len(df),
            'total_min': int(df['count'].min()),
            'total_max': int(df['count'].max()),
            'total_mean': float(df['count'].mean()),
            'total_std': float(df['count'].std()),
        }

        if len(df) > 1:
            stats['avg_growth_rate'] = float(df['growth_rate'].mean())

        stats_path = os.path.join(output_dir, 'temporal_stats.json')
        with open(stats_path, 'w') as f:
            json.dump(stats, f, indent=4)

        result_paths['stats'] = stats_path

        logger.info(f"Análise temporal concluída. Resultados em: {output_dir}")
        return result_paths