"""
Módulo de treinamento para MicroDetect.
"""

from microdetect.training.train import YOLOTrainer
from microdetect.training.evaluate import ModelEvaluator

__all__ = ['YOLOTrainer', 'ModelEvaluator']