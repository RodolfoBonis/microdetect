"""
Manipuladores de eventos de teclado para a interface de anotação.
"""

import logging

from microdetect.annotation.annotator.ui.base import is_window_valid

logger = logging.getLogger(__name__)


class KeyboardHandler:
    """
    Gerencia eventos de teclado na interface de anotação.
    """

    def __init__(self, root, callbacks=None):
        """
        Inicializa o manipulador de teclado.

        Args:
            root: Janela principal Tkinter
            callbacks: Dicionário de callbacks para eventos específicos
        """
        self.root = root
        self.callbacks = callbacks or {}

        # Configurar eventos de teclado
        self._setup_keyboard_shortcuts()

    def _call_callback(self, name, *args, **kwargs):
        """
        Chama um callback pelo nome, se existir.

        Args:
            name: Nome do callback
            *args, **kwargs: Argumentos para o callback
        """
        if name in self.callbacks and callable(self.callbacks[name]):
            return self.callbacks[name](*args, **kwargs)

    def _setup_keyboard_shortcuts(self):
        """Configura os atalhos de teclado."""
        if not is_window_valid(self.root):
            return

        try:
            # Navegação e visualização
            self.root.bind("<r>", lambda e: self._call_callback("reset_zoom"))
            self.root.bind("<p>", lambda e: self._call_callback("toggle_pan_mode"))
            self.root.bind("<w>", lambda e: self._call_callback("reset_zoom"))

            # Edição
            self.root.bind("<e>", lambda e: self._call_callback("toggle_edit_mode"))
            self.root.bind("<z>", lambda e: self._call_callback("undo"))
            self.root.bind("<Delete>", lambda e: self._call_callback("delete_selected"))
            self.root.bind("<Escape>", lambda e: self._call_callback("select_none"))
            self.root.bind("<c>", lambda e: self._call_callback("cycle_classes"))

            # Salvamento
            self.root.bind("<s>", lambda e: self._call_callback("save"))
            self.root.bind("<x>", lambda e: self._call_callback("save_and_exit"))
            self.root.bind("<n>", lambda e: self._call_callback("save_and_next"))

            # Ferramentas
            self.root.bind("<S>", lambda e: self._call_callback("show_statistics"))
            self.root.bind("<b>", lambda e: self._call_callback("show_search_dialog"))
            self.root.bind("<i>", lambda e: self._call_callback("show_export_import"))

            # Sugestões automáticas
            self.root.bind("<g>", lambda e: self._call_callback("toggle_suggestion_mode"))
            self.root.bind("<f>", lambda e: self._call_callback("apply_suggestions"))

            # Sair
            self.root.bind("<q>", lambda e: self._call_callback("on_closing"))

        except Exception as e:
            logger.error(f"Erro ao configurar atalhos de teclado: {e}")

    def update_root(self, root):
        """
        Atualiza a referência à janela principal.

        Args:
            root: Nova janela principal
        """
        self.root = root
        self._setup_keyboard_shortcuts()
