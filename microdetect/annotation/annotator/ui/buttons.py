"""
Configuração de botões da interface de anotação.
"""

import logging
import tkinter as tk

logger = logging.getLogger(__name__)


class ButtonManager:
    """
    Gerencia os botões da interface de anotação.
    """

    def __init__(self, parent_frame, callbacks=None):
        """
        Inicializa o gerenciador de botões.

        Args:
            parent_frame: Frame pai onde os botões serão adicionados
            callbacks: Dicionário de callbacks para os botões
        """
        self.parent = parent_frame
        self.callbacks = callbacks or {}
        self.buttons = {}

    def _call_callback(self, name, *args, **kwargs):
        """
        Chama um callback pelo nome, se existir.

        Args:
            name: Nome do callback
            *args, **kwargs: Argumentos para o callback
        """
        if name in self.callbacks and callable(self.callbacks[name]):
            return self.callbacks[name](*args, **kwargs)

    def create_main_buttons(self):
        """
        Cria os botões principais da interface.

        Returns:
            (button_frame, button_frame2): Tupla com os dois frames de botões
        """
        # Botões - Primeira linha
        button_frame = tk.Frame(self.parent)
        button_frame.pack(fill=tk.X)

        self.buttons["reset"] = tk.Button(button_frame, text="Reiniciar (R)", command=lambda: self._call_callback("reset"))
        self.buttons["reset"].pack(side=tk.LEFT, padx=5)

        self.buttons["undo"] = tk.Button(button_frame, text="Desfazer (Z)", command=lambda: self._call_callback("undo"))
        self.buttons["undo"].pack(side=tk.LEFT, padx=5)

        self.buttons["save"] = tk.Button(button_frame, text="Salvar (S)", command=lambda: self._call_callback("save"))
        self.buttons["save"].pack(side=tk.LEFT, padx=5)

        self.buttons["edit_mode"] = tk.Button(
            button_frame, text="Modo Edição (E)", command=lambda: self._call_callback("toggle_edit_mode")
        )
        self.buttons["edit_mode"].pack(side=tk.LEFT, padx=5)

        self.buttons["pan_mode"] = tk.Button(
            button_frame, text="Modo Navegação (P)", command=lambda: self._call_callback("toggle_pan_mode")
        )
        self.buttons["pan_mode"].pack(side=tk.LEFT, padx=5)

        self.buttons["reset_zoom"] = tk.Button(
            button_frame, text="Reset Zoom (W)", command=lambda: self._call_callback("reset_zoom")
        )
        self.buttons["reset_zoom"].pack(side=tk.LEFT, padx=5)

        # Segunda linha de botões
        button_frame2 = tk.Frame(self.parent)
        button_frame2.pack(fill=tk.X)

        self.buttons["cycle_class"] = tk.Button(
            button_frame2, text="Alternar Classe (C)", command=lambda: self._call_callback("cycle_classes")
        )
        self.buttons["cycle_class"].pack(side=tk.LEFT, padx=5)

        self.buttons["exit"] = tk.Button(button_frame2, text="Sair (Q)", command=lambda: self._call_callback("on_closing"))
        self.buttons["exit"].pack(side=tk.LEFT, padx=5)

        self.buttons["save_exit"] = tk.Button(
            button_frame2, text="Salvar e Sair (X)", command=lambda: self._call_callback("save_and_exit")
        )
        self.buttons["save_exit"].pack(side=tk.LEFT, padx=5)

        self.buttons["delete"] = tk.Button(
            button_frame2, text="Excluir Seleção (Del)", command=lambda: self._call_callback("delete_selected")
        )
        self.buttons["delete"].pack(side=tk.LEFT, padx=5)

        # Adicionar novo botão para salvar e avançar
        self.buttons["next"] = tk.Button(
            button_frame2,
            text="Salvar e Próxima (N)",
            command=lambda: self._call_callback("save_and_next"),
            bg="lightgreen",  # Destaque visual para o botão
        )
        self.buttons["next"].pack(side=tk.LEFT, padx=5)

        self.buttons["stats"] = tk.Button(
            button_frame2, text="Estatísticas (S)", command=lambda: self._call_callback("show_statistics")
        )
        self.buttons["stats"].pack(side=tk.LEFT, padx=5)

        # Adicionar botão de busca/filtro
        self.buttons["search"] = tk.Button(
            button_frame2, text="Buscar Imagens (B)", command=lambda: self._call_callback("show_search_dialog")
        )
        self.buttons["search"].pack(side=tk.LEFT, padx=5)

        # Botão para exportar/importar anotações
        self.buttons["export_import"] = tk.Button(
            button_frame2, text="Exportar/Importar (I)", command=lambda: self._call_callback("show_export_import")
        )
        self.buttons["export_import"].pack(side=tk.LEFT, padx=5)

        return button_frame, button_frame2

    def add_suggestion_buttons(self, button_frame, button_frame2):
        """
        Adiciona botões para sugestão automática.

        Args:
            button_frame: Frame para botões principais
            button_frame2: Frame para botões secundários
        """
        # Adicionar botão para ativar/desativar sugestões automáticas
        self.buttons["suggestion"] = tk.Button(
            button_frame,
            text="Sugestões Automáticas (G)",
            command=lambda: self._call_callback("toggle_suggestion_mode"),
            bg="#f0f0f0",  # Cor padrão
        )
        self.buttons["suggestion"].pack(side=tk.LEFT, padx=5)

        # Adicionar botão para aplicar todas as sugestões
        self.buttons["apply_suggestions"] = tk.Button(
            button_frame2,
            text="Aplicar Sugestões (F)",
            command=lambda: self._call_callback("apply_suggestions"),
            state=tk.DISABLED,  # Inicialmente desabilitado
        )
        self.buttons["apply_suggestions"].pack(side=tk.LEFT, padx=5)

    def update_button_state(self, button_name, **kwargs):
        """
        Atualiza o estado de um botão.

        Args:
            button_name: Nome do botão
            **kwargs: Argumentos para configuração (text, state, bg, fg, etc.)
        """
        if button_name in self.buttons:
            try:
                self.buttons[button_name].config(**kwargs)
            except Exception as e:
                logger.error(f"Erro ao atualizar botão '{button_name}': {e}")

    def get_button(self, button_name):
        """
        Obtém um botão pelo nome.

        Args:
            button_name: Nome do botão

        Returns:
            Botão ou None se não existir
        """
        return self.buttons.get(button_name)
