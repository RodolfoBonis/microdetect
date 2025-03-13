"""
Módulo para análises estatísticas de detecções.
"""

import json
import logging
import os
from typing import Any, Dict, List, Optional, Tuple, Union

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.ndimage import gaussian_filter
from scipy.spatial.distance import pdist, squareform

logger = logging.getLogger(__name__)


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
        by_class: bool = False,
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
            unique_classes = set(det["class"] for det in detections)
            result_paths = {}

            # Gerar um mapa para cada classe
            for cls in unique_classes:
                # Filtrar detecções para esta classe
                class_detections = [det for det in detections if det["class"] == cls]

                # Definir caminho de saída para esta classe
                class_output_path = os.path.join(
                    os.path.dirname(output_path), f"density_map_class_{cls}{os.path.splitext(output_path)[1]}"
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
        class_name: Optional[str] = None,
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
            x, y = int(det["x_center"] * image_size[0]), int(det["y_center"] * image_size[1])
            if 0 <= x < image_size[0] and 0 <= y < image_size[1]:
                density_map[y, x] += 1

        # Aplicar filtro gaussiano para suavização
        density_map = gaussian_filter(density_map, sigma=sigma)

        # Normalizar para visualização
        if density_map.max() > 0:
            density_map = density_map / density_map.max()

        # Plotar e salvar
        plt.figure(figsize=(10, 8))
        plt.imshow(density_map, cmap="jet")
        plt.colorbar(label="Densidade normalizada")

        title = "Mapa de Densidade de Detecções"
        if class_name is not None:
            title += f" - Classe {class_name}"
        plt.title(title)

        plt.tight_layout()
        plt.savefig(output_path)
        plt.close()

        logger.info(f"Mapa de densidade salvo em: {output_path}")
        return output_path

    def analyze_size_distribution(
        self, detections: List[Dict], output_dir: Optional[str] = None, by_class: bool = True, cls_names=None
    ) -> Dict[str, str]:
        """
        Analisa a distribuição de tamanho dos objetos detectados.

        Args:
            detections: Lista de detecções com dimensões
            output_dir: Diretório para salvar os gráficos
            by_class: Se True, gera análise separada por classe
            cls_names: Lista de nomes de classes (opcional)
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
            width = det.get("width", 0)
            height = det.get("height", 0)
            size = np.sqrt(width * height)  # Medida de tamanho (média geométrica)

            sizes.append(size)
            classes.append(det.get("class", 0))

        # Gráfico geral
        plt.figure(figsize=(10, 6))
        plt.hist(sizes, bins=30, alpha=0.7)
        plt.xlabel("Tamanho (pixels)")
        plt.ylabel("Frequência")
        plt.title("Distribuição de Tamanho de Objetos Detectados")
        plt.grid(alpha=0.3)

        all_sizes_path = os.path.join(output_dir, "size_distribution_all.png")
        plt.savefig(all_sizes_path)
        plt.close()

        result_paths = {"all": all_sizes_path}

        # Gráficos por classe
        if by_class and len(set(classes)) > 1:
            class_names = sorted(set(classes))

            plt.figure(figsize=(12, 8))
            for cls in class_names:
                cls_sizes = [size for size, c in zip(sizes, classes) if c == cls]
                plt.hist(cls_sizes, bins=20, alpha=0.7, label=f"Classe {cls}")

            plt.xlabel("Tamanho (pixels)")
            plt.ylabel("Frequência")
            plt.title("Distribuição de Tamanho por Classe")
            plt.legend()
            plt.grid(alpha=0.3)

            by_class_path = os.path.join(output_dir, "size_distribution_by_class.png")
            plt.savefig(by_class_path)
            plt.close()

            result_paths["by_class"] = by_class_path

            # Gráficos individuais para cada classe
            for cls in class_names:
                cls_sizes = [size for size, c in zip(sizes, classes) if c == cls]

                plt.figure(figsize=(10, 6))
                plt.hist(cls_sizes, bins=20, alpha=0.7, color=f"C{cls_names.index(cls)}")
                plt.xlabel("Tamanho (pixels)")
                plt.ylabel("Frequência")
                plt.title(f"Distribuição de Tamanho - Classe {cls}")
                plt.grid(alpha=0.3)

                class_path = os.path.join(output_dir, f"size_distribution_class_{cls}.png")
                plt.savefig(class_path)
                plt.close()

                result_paths[f"class_{cls}"] = class_path

        # Salvar dados em CSV para análise adicional
        df = pd.DataFrame({"tamanho": sizes, "classe": classes})
        df.to_csv(os.path.join(output_dir, "size_distribution_data.csv"), index=False)

        # Estatísticas básicas
        stats = {}
        stats["all"] = {
            "mean": np.mean(sizes),
            "median": np.median(sizes),
            "std": np.std(sizes),
            "min": np.min(sizes),
            "max": np.max(sizes),
            "count": len(sizes),
        }

        for cls in set(classes):
            cls_sizes = [size for size, c in zip(sizes, classes) if c == cls]
            stats[f"class_{cls}"] = {
                "mean": np.mean(cls_sizes),
                "median": np.median(cls_sizes),
                "std": np.std(cls_sizes),
                "min": np.min(cls_sizes),
                "max": np.max(cls_sizes),
                "count": len(cls_sizes),
            }

        # Salvar estatísticas em JSON
        stats_path = os.path.join(output_dir, "size_stats.json")
        with open(stats_path, "w") as f:
            json.dump(stats, f, indent=4)

        result_paths["stats"] = stats_path

        logger.info(f"Análise de distribuição de tamanho concluída. Resultados em: {output_dir}")
        return result_paths

    def analyze_spatial_relationships(
        self, detections: List[Dict], output_dir: Optional[str] = None, min_distance: float = 0.02, by_class: bool = True
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
            coords.append([det.get("x_center", 0), det.get("y_center", 0)])
            classes.append(det.get("class", 0))

        coords = np.array(coords)

        # Verificar se há pontos suficientes para análise
        if len(coords) < 2:
            logger.warning("Número insuficiente de detecções para análise espacial")
            return {"error": "Número insuficiente de detecções"}

        # Scatter plot geral das detecções
        plt.figure(figsize=(10, 10))
        unique_classes = sorted(set(classes))

        for cls in unique_classes:
            idx = [i for i, c in enumerate(classes) if c == cls]
            plt.scatter(coords[idx, 0], coords[idx, 1], label=f"Classe {cls}", alpha=0.7)

        plt.xlabel("Posição X")
        plt.ylabel("Posição Y")
        plt.title("Distribuição Espacial de Detecções")
        plt.legend()
        plt.grid(alpha=0.3)
        plt.xlim(0, 1)
        plt.ylim(0, 1)

        scatter_path = os.path.join(output_dir, "spatial_scatter.png")
        plt.savefig(scatter_path)
        plt.close()

        result_paths["scatter"] = scatter_path

        # Calcular matriz de distâncias
        if len(coords) > 1:
            dist_matrix = squareform(pdist(coords))

            # Histograma de distâncias
            plt.figure(figsize=(10, 6))

            # Obter as distâncias entre pontos diferentes
            distances = dist_matrix[np.triu_indices_from(dist_matrix, k=1)]
            plt.hist(distances, bins=30, alpha=0.7)
            plt.xlabel("Distância")
            plt.ylabel("Frequência")
            plt.title("Distribuição de Distâncias entre Detecções")
            plt.grid(alpha=0.3)

            distance_hist_path = os.path.join(output_dir, "distance_histogram.png")
            plt.savefig(distance_hist_path)
            plt.close()

            result_paths["distance_hist"] = distance_hist_path

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
                    neighbors = [j for j in range(len(coords)) if dist_matrix[current, j] < min_distance and j not in visited]

                    for neighbor in neighbors:
                        visited.add(neighbor)
                        cluster.append(neighbor)
                        queue.append(neighbor)

                if len(cluster) > 1:  # Ignorar pontos isolados
                    clusters.append(cluster)

            # Plotar clusters
            plt.figure(figsize=(10, 10))

            # Plotar todos os pontos em cinza claro
            plt.scatter(coords[:, 0], coords[:, 1], c="lightgray", alpha=0.3)

            # Plotar clusters com cores diferentes
            for i, cluster in enumerate(clusters):
                plt.scatter(coords[cluster, 0], coords[cluster, 1], label=f"Cluster {i + 1} (n={len(cluster)})", alpha=0.7)

            plt.xlabel("Posição X")
            plt.ylabel("Posição Y")
            plt.title(f"Clusters Identificados (dist < {min_distance})")
            plt.legend()
            plt.grid(alpha=0.3)
            plt.xlim(0, 1)
            plt.ylim(0, 1)

            clusters_path = os.path.join(output_dir, "spatial_clusters.png")
            plt.savefig(clusters_path)
            plt.close()

            result_paths["clusters"] = clusters_path

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
                plt.imshow(ratio, cmap="viridis")
                plt.colorbar(label="Razão Observada/Esperada")
                plt.title("Razão de Co-ocorrência entre Classes")
                plt.xticks(range(len(unique_classes)), [f"Classe {cls}" for cls in unique_classes])
                plt.yticks(range(len(unique_classes)), [f"Classe {cls}" for cls in unique_classes])

                class_relation_path = os.path.join(output_dir, "class_relations.png")
                plt.savefig(class_relation_path)
                plt.close()

                result_paths["class_relations"] = class_relation_path

        # Salvar resultados em formato JSON
        analysis_data = {
            "detection_count": len(detections),
            "class_counts": {cls: classes.count(cls) for cls in unique_classes},
        }

        if len(coords) > 1:
            analysis_data.update(
                {
                    "mean_distance": float(np.mean(distances)),
                    "median_distance": float(np.median(distances)),
                    "min_distance": float(np.min(distances)),
                    "max_distance": float(np.max(distances)),
                    "cluster_count": len(clusters),
                    "cluster_sizes": [len(cluster) for cluster in clusters],
                }
            )

        data_path = os.path.join(output_dir, "spatial_analysis.json")
        with open(data_path, "w") as f:
            json.dump(analysis_data, f, indent=4)

        result_paths["data"] = data_path

        logger.info(f"Análise espacial concluída. Resultados em: {output_dir}")
        return result_paths

    def analyze_temporal_data(
        self, time_series_data: List[Dict[str, Any]], output_dir: Optional[str] = None, date_format: str = "%Y-%m-%d"
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

        if "timestamp" not in df.columns:
            logger.error("Coluna 'timestamp' não encontrada nos dados temporais")
            return {"error": "Coluna timestamp não encontrada"}

        # Converter timestamps para datetime
        try:
            df["timestamp"] = pd.to_datetime(df["timestamp"], format=date_format)
            df = df.sort_values("timestamp")
        except Exception as e:
            logger.error(f"Erro ao converter timestamps: {str(e)}")
            return {"error": f"Erro ao converter timestamps: {str(e)}"}

        # Gráfico de contagem total ao longo do tempo
        plt.figure(figsize=(12, 6))
        plt.plot(df["timestamp"], df["count"], marker="o", linestyle="-")
        plt.xlabel("Data")
        plt.ylabel("Contagem Total")
        plt.title("Contagem de Detecções ao Longo do Tempo")
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.grid(alpha=0.3)

        total_count_path = os.path.join(output_dir, "temporal_total_count.png")
        plt.savefig(total_count_path)
        plt.close()

        result_paths["total_count"] = total_count_path

        # Verificar se temos dados de contagem por classe
        if "class_counts" in df.columns:
            # Gráfico com linhas separadas por classe
            plt.figure(figsize=(12, 6))

            # Obter todas as classes que aparecem nos dados
            all_classes = set()
            for counts in df["class_counts"]:
                all_classes.update(counts.keys())

            all_classes = sorted(all_classes)

            for cls in all_classes:
                counts = [row["class_counts"].get(cls, 0) for _, row in df.iterrows()]
                plt.plot(df["timestamp"], counts, marker="o", linestyle="-", label=f"Classe {cls}")

            plt.xlabel("Data")
            plt.ylabel("Contagem")
            plt.title("Contagem de Detecções por Classe ao Longo do Tempo")
            plt.legend()
            plt.xticks(rotation=45)
            plt.tight_layout()
            plt.grid(alpha=0.3)

            by_class_path = os.path.join(output_dir, "temporal_by_class.png")
            plt.savefig(by_class_path)
            plt.close()

            result_paths["by_class"] = by_class_path

            # Gráfico de área empilhada para visualizar proporções
            plt.figure(figsize=(12, 6))

            # Preparar dados para gráfico de área
            class_data = {cls: [] for cls in all_classes}

            for _, row in df.iterrows():
                for cls in all_classes:
                    class_data[cls].append(row["class_counts"].get(cls, 0))

            # Plotar gráfico de área empilhada
            plt.stackplot(
                df["timestamp"],
                [class_data[cls] for cls in all_classes],
                labels=[f"Classe {cls}" for cls in all_classes],
                alpha=0.7,
            )

            plt.xlabel("Data")
            plt.ylabel("Contagem")
            plt.title("Proporção de Classes ao Longo do Tempo")
            plt.legend(loc="upper left")
            plt.xticks(rotation=45)
            plt.tight_layout()

            stacked_path = os.path.join(output_dir, "temporal_stacked.png")
            plt.savefig(stacked_path)
            plt.close()

            result_paths["stacked"] = stacked_path

        # Calcular taxa de crescimento
        if len(df) > 1:
            df["growth_rate"] = df["count"].pct_change() * 100

            plt.figure(figsize=(12, 6))
            plt.bar(df["timestamp"][1:], df["growth_rate"][1:], alpha=0.7)
            plt.axhline(y=0, color="r", linestyle="-", alpha=0.3)
            plt.xlabel("Data")
            plt.ylabel("Taxa de Crescimento (%)")
            plt.title("Taxa de Crescimento ao Longo do Tempo")
            plt.xticks(rotation=45)
            plt.tight_layout()
            plt.grid(alpha=0.3)

            growth_path = os.path.join(output_dir, "temporal_growth_rate.png")
            plt.savefig(growth_path)
            plt.close()

            result_paths["growth_rate"] = growth_path

        # Salvar dados processados em CSV
        df.to_csv(os.path.join(output_dir, "temporal_data.csv"), index=False)

        # Calcular estatísticas resumidas
        stats = {
            "start_date": df["timestamp"].min().strftime(date_format),
            "end_date": df["timestamp"].max().strftime(date_format),
            "timepoints": len(df),
            "total_min": int(df["count"].min()),
            "total_max": int(df["count"].max()),
            "total_mean": float(df["count"].mean()),
            "total_std": float(df["count"].std()),
        }

        if len(df) > 1:
            stats["avg_growth_rate"] = float(df["growth_rate"].mean())

        stats_path = os.path.join(output_dir, "temporal_stats.json")
        with open(stats_path, "w") as f:
            json.dump(stats, f, indent=4)

        result_paths["stats"] = stats_path

        logger.info(f"Análise temporal concluída. Resultados em: {output_dir}")
        return result_paths
