"""
Módulo de interface de usuário para o anotador de imagens.
"""

from microdetect.annotation.annotator.ui.base import center_window, create_secure_dialog, is_window_valid
from microdetect.annotation.annotator.ui.buttons import ButtonManager
from microdetect.annotation.annotator.ui.main_window import MainWindow
from microdetect.annotation.annotator.ui.search_dialog import SearchDialog
from microdetect.annotation.annotator.ui.statistics_dialog import StatisticsDialog

__all__ = [
    "create_secure_dialog",
    "is_window_valid",
    "center_window",
    "ButtonManager",
    "MainWindow",
    "SearchDialog",
    "StatisticsDialog",
]
