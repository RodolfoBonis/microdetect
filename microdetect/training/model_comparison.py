"""
Módulo para comparação de modelos de diferentes tamanhos.
"""

import json
import logging
import os
from typing import Dict, List, Any

import matplotlib.pyplot as plt
import pandas as pd

from microdetect.training import SpeedBenchmark, ModelEvaluator

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
            self,
            model_paths: List[str],
            data_yaml: str,
            conf_threshold: float = 0.25,
            iou_threshold: float = 0.7
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

            # Avaliar o modelo
            metrics = self.evaluator.evaluate_model(
                model_path, data_yaml, conf_threshold, iou_threshold
            )

            # Executar benchmark de velocidade
            benchmark = SpeedBenchmark(model_path)
            speed_results = benchmark.run(
                batch_sizes=[1, 4, 8],
                image_sizes=[640],
                iterations=10,
                warmup=2
            )

            # Extrair tamanho do arquivo do modelo
            model_size_mb = os.path.getsize(model_path) / (1024 * 1024)

            # Determinar categoria do modelo (n, s, m, l, x)
            model_category = self._determine_model_category(model_path)

            # Armazenar resultados
            results[model_name] = {
                'tamanho': model_category,
                'tamanho_arquivo': round(model_size_mb, 2),  # MB
                'metricas': {
                    'mAP50': metrics['metricas_gerais']['Precisão (mAP50)'],
                    'mAP50-95': metrics['metricas_gerais']['Precisão (mAP50-95)'],
                    'recall': metrics['metricas_gerais']['Recall'],
                    'precision': metrics['metricas_gerais']['Precisão'],
                    'f1-score': metrics['metricas_gerais']['F1-Score']
                },
                'velocidade': {
                    'fps': speed_results['results'][0]['fps'],
                    'latencia_ms': speed_results['results'][0]['avg_latency_ms']
                }
            }

        # Gerar visualizações
        self._generate_comparison_visualizations(results)

        # Salvar resultados
        self._save_comparison_results(results)

        logger.info(f"Comparação de modelos concluída, resultados em: {self.output_dir}")
        return results

    def _determine_model_category(self, model_path: str) -> str:
        """
        Determina a categoria do modelo (n, s, m, l, x) pelo nome do arquivo.

        Args:
            model_path: Caminho para o arquivo do modelo

        Returns:
            Categoria do modelo
        """
        model_name = os.path.basename(model_path).lower()

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
        else:
            return "unknown"

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
        map50_values = [results[model]['metricas']['mAP50'] for model in model_names]
        fps_values = [results[model]['velocidade']['fps'] for model in model_names]
        size_values = [results[model]['tamanho_arquivo'] for model in model_names]

        # 1. Gráfico de precisão (mAP50)
        plt.figure(figsize=(10, 6))
        bars = plt.bar(model_names, map50_values, color='skyblue')
        plt.title('Comparação de Precisão (mAP50)')
        plt.xlabel('Modelo')
        plt.ylabel('mAP50')
        plt.ylim(0, 1)
        plt.xticks(rotation=45)

        # Adicionar valores nas barras
        for bar in bars:
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width() / 2., height + 0.01,
                     f'{height:.3f}', ha='center', va='bottom')

        accuracy_path = os.path.join(self.output_dir, 'accuracy_comparison.png')
        plt.tight_layout()
        plt.savefig(accuracy_path)
        plt.close()
        visualization_paths['accuracy'] = accuracy_path

        # 2. Gráfico de velocidade (FPS)
        plt.figure(figsize=(10, 6))
        bars = plt.bar(model_names, fps_values, color='lightgreen')
        plt.title('Comparação de Velocidade (FPS)')
        plt.xlabel('Modelo')
        plt.ylabel('Frames Por Segundo')
        plt.xticks(rotation=45)

        # Adicionar valores nas barras
        for bar in bars:
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width() / 2., height + 0.5,
                     f'{height:.1f}', ha='center', va='bottom')

        speed_path = os.path.join(self.output_dir, 'speed_comparison.png')
        plt.tight_layout()
        plt.savefig(speed_path)
        plt.close()
        visualization_paths['speed'] = speed_path

        # 3. Gráfico de trade-off: Precisão vs. Velocidade
        plt.figure(figsize=(10, 8))
        plt.scatter(fps_values, map50_values, s=size_values, alpha=0.7)

        # Adicionar rótulos dos modelos
        for i, model in enumerate(model_names):
            plt.annotate(model, (fps_values[i], map50_values[i]),
                         xytext=(5, 5), textcoords='offset points')

        plt.title('Trade-off: Precisão vs. Velocidade')
        plt.xlabel('Velocidade (FPS)')
        plt.ylabel('Precisão (mAP50)')
        plt.grid(True, alpha=0.3)

        tradeoff_path = os.path.join(self.output_dir, 'accuracy_vs_speed.png')
        plt.tight_layout()
        plt.savefig(tradeoff_path)
        plt.close()
        visualization_paths['tradeoff'] = tradeoff_path

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
        json_path = os.path.join(self.output_dir, 'model_comparison_results.json')
        with open(json_path, 'w') as f:
            json.dump(results, f, indent=4)

        # Converter para formato tabular e salvar como CSV
        rows = []
        for model_name, model_data in results.items():
            row = {
                'modelo': model_name,
                'categoria': model_data['tamanho'],
                'tamanho_mb': model_data['tamanho_arquivo'],
                'map50': model_data['metricas']['mAP50'],
                'map50_95': model_data['metricas']['mAP50-95'],
                'recall': model_data['metricas']['recall'],
                'precision': model_data['metricas']['precision'],
                'f1_score': model_data['metricas']['f1-score'],
                'fps': model_data['velocidade']['fps'],
                'latencia_ms': model_data['velocidade']['latencia_ms']
            }
            rows.append(row)

        df = pd.DataFrame(rows)
        csv_path = os.path.join(self.output_dir, 'model_comparison_results.csv')
        df.to_csv(csv_path, index=False)

        return json_path