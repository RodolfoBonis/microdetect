"""
Módulo para benchmark de velocidade e monitoramento de recursos.
"""

import logging
import os
import threading
import time
from datetime import datetime
from typing import Any, Dict, List

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from ultralytics import YOLO

logger = logging.getLogger(__name__)


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
        warmup: int = 10,
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
                    dummy_input = np.random.randint(0, 255, (batch_size, img_size, img_size, 3), dtype=np.uint8)

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
                    self.results.append(
                        {
                            "batch_size": batch_size,
                            "image_size": img_size,
                            "avg_latency_ms": avg_latency,
                            "std_latency_ms": std_latency,
                            "min_latency_ms": min_latency,
                            "max_latency_ms": max_latency,
                            "p95_latency_ms": p95_latency,
                            "fps": fps,
                            "samples_per_second": batch_size * fps,
                        }
                    )

                    logger.info(f"Resultado: Latência={avg_latency:.2f}ms, FPS={fps:.2f}, Amostras/seg={batch_size * fps:.2f}")

            return {"model": os.path.basename(self.model_path), "device": self.device or "auto", "results": self.results}

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
                axs[0].plot(subset["batch_size"], subset["fps"], marker="o", label=f"Imagem {img_size}x{img_size}")

            axs[0].set_xlabel("Tamanho do Batch")
            axs[0].set_ylabel("FPS")
            axs[0].set_title("Desempenho (FPS) vs Tamanho do Batch")
            axs[0].grid(True)
            axs[0].legend()

            # Segundo gráfico: Amostras/segundo vs Tamanho da Imagem para diferentes tamanhos de batch
            for batch in df["batch_size"].unique():
                subset = df[df["batch_size"] == batch]
                axs[1].plot(subset["image_size"], subset["samples_per_second"], marker="o", label=f"Batch {batch}")

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
            self.monitoring_thread.join(timeout=2 * self.interval)

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
                "gpu_memory_used_max": float(gpu_mem_max),
            }

        return {
            "duration": time.time() - self.start_time,
            "measurements_count": len(self.measurements),
            "cpu_percent_avg": float(cpu_avg),
            "cpu_percent_max": float(cpu_max),
            "memory_percent_avg": float(mem_avg),
            "memory_percent_max": float(mem_max),
            **gpu_stats,
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
                "memory_used": memory.used,
            }

            # Adicionar estatísticas de GPU, se disponíveis
            if has_cuda:
                try:
                    gpu_mem_alloc = torch.cuda.memory_allocated()
                    gpu_mem_reserved = torch.cuda.memory_reserved()
                    gpu_max_mem = torch.cuda.get_device_properties(0).total_memory

                    measurement.update(
                        {
                            "gpu_memory_used": gpu_mem_alloc,
                            "gpu_memory_reserved": gpu_mem_reserved,
                            "gpu_memory_percent": 100 * gpu_mem_alloc / gpu_max_mem,
                        }
                    )
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
