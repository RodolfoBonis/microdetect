"""
Módulo de utilidades para o anotador de imagens.
"""

from microdetect.annotation.annotator.utils.backup import AnnotationBackup
from microdetect.annotation.annotator.utils.constants import (
    DEFAULT_AUTO_SAVE,
    DEFAULT_AUTO_SAVE_INTERVAL,
    HANDLE_E,
    HANDLE_N,
    HANDLE_NE,
    HANDLE_NONE,
    HANDLE_NW,
    HANDLE_S,
    HANDLE_SE,
    HANDLE_SW,
    HANDLE_W,
    KEYBOARD_SHORTCUTS,
)
from microdetect.annotation.annotator.utils.progress import ProgressManager

__all__ = [
    "DEFAULT_AUTO_SAVE",
    "DEFAULT_AUTO_SAVE_INTERVAL",
    "HANDLE_NONE",
    "HANDLE_NW",
    "HANDLE_NE",
    "HANDLE_SE",
    "HANDLE_SW",
    "HANDLE_N",
    "HANDLE_E",
    "HANDLE_S",
    "HANDLE_W",
    "KEYBOARD_SHORTCUTS",
    "AnnotationBackup",
    "ProgressManager",
]
