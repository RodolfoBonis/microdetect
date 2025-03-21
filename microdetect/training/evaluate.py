"""
Módulo para avaliação de modelos treinados.
"""

import csv
import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Tuple

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
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
        self, model_path: str, data_yaml: str, conf_threshold: float = 0.25, iou_threshold: float = 0.7
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
            results = model.val(data=data_yaml, conf=conf_threshold, iou=iou_threshold)
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
            "Precisão (mAP50)": float(results.box.map50),  # Acessando como atributo
            "Precisão (mAP50-95)": float(results.box.map),  # Acessando como atributo
            "Recall": float(results.box.mr),  # Acessando como atributo
            "Precisão": float(results.box.mp),  # Acessando como atributo
            "F1-Score": self._calculate_f1(float(results.box.mp), float(results.box.mr)),
            "Taxa de Erro": 1.0 - float(results.box.map50),  # Acessando como atributo
        }

        # Métricas por classe
        class_metrics = []
        for i, class_name in enumerate(results.names.values()):
            if i < len(results.box.ap_class_index):
                idx = results.box.ap_class_index.tolist().index(i) if i in results.box.ap_class_index else -1
                if idx >= 0:
                    # Acessando ap50 como atributo
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

            # Rodar validação com plot_confusion_matrix=True (parâmetro correto no YOLOv8)
            # O YOLOv8 não aceita 'conf_matrix', mas pode aceitar 'plot_confusion_matrix'
            # ou simplesmente gerar a matriz após a validação
            results = model.val(data=data_yaml)

            # Gerar a matriz de confusão manualmente
            from ultralytics.utils.metrics import ConfusionMatrix

            # Criar matriz de confusão usando os resultados
            conf_matrix = ConfusionMatrix(nc=len(results.names))

            # Plotar
            plt.figure(figsize=(10, 8))
            fig = conf_matrix.plot(names=list(results.names.values()))
            plt.savefig(conf_matrix_path)
            plt.close()

            logger.info(f"Matriz de confusão salva em: {conf_matrix_path}")
            return conf_matrix_path

        except Exception as e:
            logger.error(f"Erro ao gerar matriz de confusão: {str(e)}")

            # Tentar uma abordagem alternativa se a primeira falhar
            try:
                # Alguns modelos YOLOv8 podem usar uma abordagem diferente
                results = model.val(data=data_yaml)

                # Verificar se podemos acessar a matriz de confusão dos resultados
                if hasattr(results, 'confusion_matrix'):
                    cm = results.confusion_matrix
                    plt.figure(figsize=(10, 8))
                    plt.imshow(cm, interpolation='nearest', cmap=plt.cm.Blues)
                    plt.title('Matriz de Confusão')
                    plt.colorbar()

                    # Adicionar rótulos
                    classes = list(results.names.values())
                    tick_marks = np.arange(len(classes))
                    plt.xticks(tick_marks, classes, rotation=45)
                    plt.yticks(tick_marks, classes)

                    plt.ylabel('Real')
                    plt.xlabel('Previsto')
                    plt.tight_layout()
                    plt.savefig(conf_matrix_path)
                    plt.close()

                    logger.info(f"Matriz de confusão alternativa salva em: {conf_matrix_path}")
                    return conf_matrix_path
                else:
                    # Se não conseguirmos acessar diretamente, tentar calcular manualmente
                    return self._plot_confusion_matrix_manually(results, conf_matrix_path)
            except Exception as e2:
                logger.error(f"Erro na abordagem alternativa: {str(e2)}")
                return ""

        return ""

    def _plot_confusion_matrix_manually(self, results, save_path: str) -> str:
        """
        Tenta plotar a matriz de confusão manualmente a partir dos resultados.

        Args:
            results: Resultado da validação do modelo
            save_path: Caminho para salvar o gráfico

        Returns:
            Caminho para o gráfico salvo ou string vazia em caso de erro
        """
        try:
            # Coletar informações dos resultados para criar uma matriz de confusão básica
            preds = []
            targets = []

            # Tentar diferentes maneiras de obter os dados necessários
            if hasattr(results, 'pred') and hasattr(results, 'gt'):
                for pred, gt in zip(results.pred, results.gt):
                    if len(pred) > 0 and len(gt) > 0:
                        preds.extend(pred[:, -1].int().tolist())  # Supondo que a classe está na última coluna
                        targets.extend(gt[:, 0].int().tolist())  # Supondo que a classe está na primeira coluna

            # Se conseguimos dados suficientes, criar uma matriz de confusão básica
            if preds and targets:
                from sklearn.metrics import confusion_matrix
                import numpy as np

                # Criar matriz
                cm = confusion_matrix(targets, preds)

                # Normalizar
                cm_normalized = cm.astype('float') / cm.sum(axis=1)[:, np.newaxis]

                # Plotar
                plt.figure(figsize=(10, 8))
                plt.imshow(cm_normalized, interpolation='nearest', cmap=plt.cm.Blues)
                plt.title('Matriz de Confusão Normalizada (Calculada Manualmente)')
                plt.colorbar()

                # Adicionar rótulos se possível
                if hasattr(results, 'names'):
                    classes = list(results.names.values())
                    tick_marks = np.arange(len(classes))
                    plt.xticks(tick_marks, classes, rotation=45)
                    plt.yticks(tick_marks, classes)

                plt.ylabel('Real')
                plt.xlabel('Previsto')
                plt.tight_layout()
                plt.savefig(save_path)
                plt.close()

                logger.info(f"Matriz de confusão manual salva em: {save_path}")
                return save_path

            logger.warning("Dados insuficientes para criar matriz de confusão")
            return ""
        except Exception as e:
            logger.error(f"Erro ao plotar matriz de confusão manualmente: {str(e)}")
            return ""

    def optimize_threshold(
        self,
        model_path: str,
        data_yaml: str,
        metric: str = "F1-Score",
        conf_range: Tuple[float, float, float] = (0.1, 0.9, 0.1),
        iou_range: Tuple[float, float, float] = (0.5, 0.85, 0.05),
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

                    all_results.append(
                        {
                            "conf_threshold": conf,
                            "iou_threshold": iou,
                            "score": score,
                            **{k: v for k, v in metrics["metricas_gerais"].items()},
                        }
                    )

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
            "surface_plot": surface_plot_path,
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
            ax = fig.add_subplot(111, projection="3d")

            # Pivot da tabela para formato adequado
            pivot = df.pivot_table(index="conf_threshold", columns="iou_threshold", values="score")

            # Preparar dados para o gráfico
            X, Y = np.meshgrid(pivot.columns, pivot.index)
            Z = pivot.values

            # Plotar superfície
            surf = ax.plot_surface(X, Y, Z, cmap="viridis", alpha=0.8)

            # Adicionar barra de cores
            fig.colorbar(surf, ax=ax, shrink=0.5, aspect=5)

            # Configurar rótulos
            ax.set_xlabel("IoU Threshold")
            ax.set_ylabel("Confidence Threshold")
            ax.set_zlabel(metric)
            ax.set_title(f"Optimization Surface for {metric}")

            # Encontrar e marcar o ponto máximo
            max_idx = df["score"].idxmax()
            max_conf = df.loc[max_idx, "conf_threshold"]
            max_iou = df.loc[max_idx, "iou_threshold"]
            max_score = df.loc[max_idx, "score"]

            ax.scatter([max_iou], [max_conf], [max_score], color="red", s=100, label=f"Max: {max_score:.4f}")
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
        max_samples: int = 20,
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
            if hasattr(result, "boxes"):
                # Contar detecções de baixa confiança como potenciais FPs
                boxes = result.boxes
                if len(boxes) > 0:
                    low_conf_boxes = boxes[boxes.conf < 0.5]
                    error_counts["false_positives"] += len(low_conf_boxes)

        # Gerar relatório de erros
        report_path = os.path.join(output_dir, "error_analysis_report.json")
        with open(report_path, "w") as f:
            json.dump(
                {
                    "model": os.path.basename(model_path),
                    "error_counts": error_counts,
                    "conf_threshold": conf_threshold,
                    "iou_threshold": iou_threshold,
                    "timestamp": datetime.now().isoformat(),
                },
                f,
                indent=4,
            )

        logger.info(f"Análise de erros concluída, resultados salvos em: {output_dir}")

        return {"error_counts": error_counts, "report_path": report_path, "output_dir": output_dir}
