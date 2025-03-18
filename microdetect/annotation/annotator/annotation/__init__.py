"""
Módulo para gerenciamento de anotações no anotador.
"""

from microdetect.annotation.annotator.annotation.box import BoundingBoxManager
from microdetect.annotation.annotator.annotation.storage import AnnotationStorage
from microdetect.annotation.annotator.annotation.visualizer import AnnotationVisualizer

__all__ = ['BoundingBoxManager', 'AnnotationStorage', 'AnnotationVisualizer']