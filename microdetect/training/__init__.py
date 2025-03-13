"""
Módulo de treinamento para MicroDetect.
"""

from microdetect.training.evaluate import ModelEvaluator
from microdetect.training.train import YOLOTrainer
from microdetect.training.cross_validate import CrossValidator
from microdetect.training.benchmark import ResourceMonitor, SpeedBenchmark
from microdetect.training.model_comparison import ModelComparator

__all__ = ["YOLOTrainer", "ModelEvaluator", "CrossValidator", "ResourceMonitor", "SpeedBenchmark", "ModelComparator"]
