"""
Módulo para comparação de modelos de diferentes tamanhos.
"""

import json
import logging
import os
from typing import Any, Dict, List, re

import matplotlib.pyplot as plt
import pandas as pd

from microdetect.training import ModelEvaluator, SpeedBenchmark

logger = logging.getLogger(__name__)


class ModelComparator:
    """
    Classe para comparar modelos de diferentes tamanhos e configurações.
    """

    def __init__(self, output_dir: str = None):
        """
        Inicializa o comparador de modelos.

        Args:
            output_dir: Diretório para salvar os resultados da comparação
        """
        self.output_dir = output_dir or "model_comparison"
        os.makedirs(self.output_dir, exist_ok=True)
        self.evaluator = ModelEvaluator(self.output_dir)

    def compare_models(
            self, model_paths: List[str], data_yaml: str, conf_threshold: float = 0.25, iou_threshold: float = 0.7
    ) -> Dict[str, Any]:
        """
        Compara vários modelos usando o mesmo dataset e configurações.

        Args:
            model_paths: Lista de caminhos para os modelos a serem comparados
            data_yaml: Caminho para o arquivo de configuração do dataset
            conf_threshold: Limiar de confiança para detecções
            iou_threshold: Limiar de IoU para supressão não-máxima

        Returns:
            Dicionário com resultados da comparação
        """
        logger.info(f"Iniciando comparação de {len(model_paths)} modelos")

        results = {}
        for model_path in model_paths:
            model_name = os.path.basename(model_path)
            logger.info(f"Avaliando modelo: {model_name}")

            try:
                # Avaliar o modelo
                metrics = self.evaluator.evaluate_model(model_path, data_yaml, conf_threshold, iou_threshold)

                # Executar benchmark de velocidade
                benchmark = SpeedBenchmark(model_path)
                speed_results = benchmark.run(batch_sizes=[1, 4, 8], image_sizes=[640], iterations=10, warmup=2)

                # Extrair tamanho do arquivo do modelo
                model_size_mb = os.path.getsize(model_path) / (1024 * 1024)

                # Determinar categoria do modelo (n, s, m, l, x)
                model_category = self._determine_model_category(model_path)

                # Obter valores de benchmark de forma segura
                fps = 0
                latencia_ms = 0
                if "error" not in speed_results and "results" in speed_results and len(speed_results["results"]) > 0:
                    benchmark_result = speed_results["results"][0]
                    fps = benchmark_result.get("fps", 0)
                    latencia_ms = benchmark_result.get("avg_latency_ms", 0)

                # Armazenar resultados
                results[model_name] = {
                    "tamanho": model_category,
                    "tamanho_arquivo": round(model_size_mb, 2),  # MB
                    "metricas": {
                        "mAP50": metrics["metricas_gerais"]["Precisão (mAP50)"],
                        "mAP50-95": metrics["metricas_gerais"]["Precisão (mAP50-95)"],
                        "recall": metrics["metricas_gerais"]["Recall"],
                        "precision": metrics["metricas_gerais"]["Precisão"],
                        "f1-score": metrics["metricas_gerais"]["F1-Score"],
                    },
                    "velocidade": {
                        "fps": fps,
                        "latencia_ms": latencia_ms,
                    },
                }
            except Exception as e:
                logger.error(f"Erro ao avaliar modelo {model_name}: {str(e)}")
                # Incluir resultados parciais mesmo com erro
                results[model_name] = {
                    "tamanho": self._determine_model_category(model_path),
                    "tamanho_arquivo": round(os.path.getsize(model_path) / (1024 * 1024), 2),
                    "metricas": {
                        "mAP50": 0,
                        "mAP50-95": 0,
                        "recall": 0,
                        "precision": 0,
                        "f1-score": 0,
                    },
                    "velocidade": {
                        "fps": 0,
                        "latencia_ms": 0,
                    },
                    "error": str(e)
                }

        # Gerar visualizações - apenas se houver resultados válidos
        if results:
            self._generate_comparison_visualizations(results)

            # Salvar resultados
            self._save_comparison_results(results)

        logger.info(f"Comparação de modelos concluída, resultados em: {self.output_dir}")
        return results

    def _determine_model_category(self, model_path: str) -> str:
        """
        Determina a categoria do modelo YOLOv8 a partir do nome do arquivo ou
        extrai informações a partir do nome do arquivo para outros formatos.

        Args:
            model_path: Caminho para o arquivo do modelo

        Returns:
            Categoria do modelo
        """
        model_name = os.path.basename(model_path).lower()

        # Tentar detectar o tamanho do modelo YOLOv8 padrão
        if "yolov8n" in model_name:
            return "n"
        elif "yolov8s" in model_name:
            return "s"
        elif "yolov8m" in model_name:
            return "m"
        elif "yolov8l" in model_name:
            return "l"
        elif "yolov8x" in model_name:
            return "x"

        # Para os modelos com o formato b8_lr{taxa}.pt, extrair a taxa de aprendizado
        # para usar como categoria
        if "lr" in model_name:
            try:
                # Extrair a taxa de aprendizado do nome do modelo
                # Exemplo: b8_lr0.01.pt -> lr=0.01
                lr_match = re.search(r'lr([0-9.]+)', model_name)
                if lr_match:
                    lr_value = lr_match.group(1)
                    return f"LR {lr_value}"
            except:
                pass

        # Para qualquer outro tipo de modelo, tente extrair alguma informação útil
        try:
            # Se o modelo tem o formato batch{N}_outras_infos.pt
            batch_match = re.search(r'b(atch)?[_-]?(\d+)', model_name)
            if batch_match:
                batch_value = batch_match.group(2)
                return f"Batch {batch_value}"

            # Se não conseguimos extrair informação específica,
            # use os primeiros caracteres do nome (sem a extensão)
            return model_name.split('.')[0][:10]
        except:
            # Como último recurso
            return "custom"

    def _generate_comparison_visualizations(self, results: Dict[str, Dict]) -> Dict[str, str]:
        """
        Gera visualizações comparativas entre os modelos.

        Args:
            results: Dicionário com resultados da comparação

        Returns:
            Dicionário com caminhos para as visualizações geradas
        """
        visualization_paths = {}

        # Extrair dados para os gráficos
        model_names = list(results.keys())
        map50_values = [results[model]["metricas"]["mAP50"] for model in model_names]
        fps_values = [results[model]["velocidade"]["fps"] for model in model_names]
        size_values = [results[model]["tamanho_arquivo"] for model in model_names]

        # 1. Gráfico de precisão (mAP50)
        plt.figure(figsize=(10, 6))
        bars = plt.bar(model_names, map50_values, color="skyblue")
        plt.title("Comparação de Precisão (mAP50)")
        plt.xlabel("Modelo")
        plt.ylabel("mAP50")
        plt.ylim(0, 1)
        plt.xticks(rotation=45)

        # Adicionar valores nas barras
        for bar in bars:
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width() / 2.0, height + 0.01, f"{height:.3f}", ha="center", va="bottom")

        accuracy_path = os.path.join(self.output_dir, "accuracy_comparison.png")
        plt.tight_layout()
        plt.savefig(accuracy_path)
        plt.close()
        visualization_paths["accuracy"] = accuracy_path

        # 2. Gráfico de velocidade (FPS)
        plt.figure(figsize=(10, 6))
        bars = plt.bar(model_names, fps_values, color="lightgreen")
        plt.title("Comparação de Velocidade (FPS)")
        plt.xlabel("Modelo")
        plt.ylabel("Frames Por Segundo")
        plt.xticks(rotation=45)

        # Adicionar valores nas barras
        for bar in bars:
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width() / 2.0, height + 0.5, f"{height:.1f}", ha="center", va="bottom")

        speed_path = os.path.join(self.output_dir, "speed_comparison.png")
        plt.tight_layout()
        plt.savefig(speed_path)
        plt.close()
        visualization_paths["speed"] = speed_path

        # 3. Gráfico de trade-off: Precisão vs. Velocidade
        plt.figure(figsize=(10, 8))
        plt.scatter(fps_values, map50_values, s=size_values, alpha=0.7)

        # Adicionar rótulos dos modelos
        for i, model in enumerate(model_names):
            plt.annotate(model, (fps_values[i], map50_values[i]), xytext=(5, 5), textcoords="offset points")

        plt.title("Trade-off: Precisão vs. Velocidade")
        plt.xlabel("Velocidade (FPS)")
        plt.ylabel("Precisão (mAP50)")
        plt.grid(True, alpha=0.3)

        tradeoff_path = os.path.join(self.output_dir, "accuracy_vs_speed.png")
        plt.tight_layout()
        plt.savefig(tradeoff_path)
        plt.close()
        visualization_paths["tradeoff"] = tradeoff_path

        return visualization_paths

    def _save_comparison_results(self, results: Dict[str, Dict]) -> str:
        """
        Salva os resultados da comparação em formato JSON e CSV.

        Args:
            results: Dicionário com resultados da comparação

        Returns:
            Caminho para o arquivo JSON gerado
        """
        # Salvar como JSON
        json_path = os.path.join(self.output_dir, "model_comparison_results.json")
        with open(json_path, "w") as f:
            json.dump(results, f, indent=4)

        # Converter para formato tabular e salvar como CSV
        rows = []
        for model_name, model_data in results.items():
            row = {
                "modelo": model_name,
                "categoria": model_data["tamanho"],
                "tamanho_mb": model_data["tamanho_arquivo"],
                "map50": model_data["metricas"]["mAP50"],
                "map50_95": model_data["metricas"]["mAP50-95"],
                "recall": model_data["metricas"]["recall"],
                "precision": model_data["metricas"]["precision"],
                "f1_score": model_data["metricas"]["f1-score"],
                "fps": model_data["velocidade"]["fps"],
                "latencia_ms": model_data["velocidade"]["latencia_ms"],
            }
            rows.append(row)

        df = pd.DataFrame(rows)
        csv_path = os.path.join(self.output_dir, "model_comparison_results.csv")
        df.to_csv(csv_path, index=False)

        return json_path
