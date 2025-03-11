"""
Módulo de treinamento para MicroDetect.
"""

from microdetect.training.evaluate import ModelEvaluator
from microdetect.training.train import YOLOTrainer

__all__ = ["YOLOTrainer", "ModelEvaluator"]
