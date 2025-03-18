"""
Criação e configuração da janela principal da interface de anotação.
"""

import logging
import os
import tkinter as tk
from typing import List

from microdetect.annotation.annotator.ui.base import center_window
from microdetect.annotation.annotator.ui.buttons import ButtonManager

logger = logging.getLogger(__name__)


class MainWindow:
    """
    Gerencia a janela principal da interface de anotação.
    """

    def __init__(self, image_path: str, classes: List[str], callbacks=None):
        """
        Inicializa a janela principal.

        Args:
            image_path: Caminho para a imagem a ser anotada
            classes: Lista de classes disponíveis para anotação
            callbacks: Dicionário de callbacks para eventos
        """
        self.image_path = image_path
        self.classes = classes
        self.callbacks = callbacks or {}

        # Componentes da interface
        self.root = None
        self.canvas = None
        self.class_var = None
        self.status_label = None
        self.info_label = None
        self.button_manager = None

        # Limpar qualquer instância Tk anterior
        if hasattr(tk, '_default_root') and tk._default_root is not None:
            try:
                tk._default_root.destroy()
                logger.info("Janela Tk anterior destruída")
            except:
                pass

    def _call_callback(self, name, *args, **kwargs):
        """
        Chama um callback pelo nome, se existir.

        Args:
            name: Nome do callback
            *args, **kwargs: Argumentos para o callback
        """
        if name in self.callbacks and callable(self.callbacks[name]):
            return self.callbacks[name](*args, **kwargs)

    def create(self):
        """
        Cria e configura a janela principal.

        Returns:
            Tupla com (root, canvas, class_var, status_label)
        """
        # Criar um novo root limpo
        self.root = tk.Tk()
        self.root.title(f"Anotação: {os.path.basename(self.image_path)}")

        # Configurar protocolo de fechamento
        self.root.protocol("WM_DELETE_WINDOW", lambda: self._call_callback('on_closing'))

        # Criar frame principal
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Painel de controle
        control_frame = tk.Frame(main_frame)
        control_frame.pack(side=tk.TOP, fill=tk.X)

        # Seleção de classe
        class_label = tk.Label(control_frame, text="Selecionar classe:")
        class_label.pack(side=tk.LEFT, padx=5)

        self.class_var = tk.StringVar(self.root)
        self.class_var.set(self.classes[0] if self.classes else "0-desconhecido")

        class_menu = tk.OptionMenu(control_frame, self.class_var, *self.classes)
        class_menu.pack(side=tk.LEFT, padx=5)

        # Vincular alteração de classe
        self.class_var.trace("w", lambda *args: self._call_callback('set_current_class'))

        # Status label
        self.status_label = tk.Label(
            main_frame,
            text="Contagem: 0 | Desenhe clicando e arrastando",
        )
        self.status_label.pack(side=tk.BOTTOM, fill=tk.X)

        # Informações da imagem
        self.info_label = tk.Label(
            main_frame,
            text=f"Imagem: {os.path.basename(self.image_path)} | Dimensões: 0x0",
        )
        self.info_label.pack(side=tk.BOTTOM, fill=tk.X)

        # Criar canvas com barras de rolagem
        canvas_frame = tk.Frame(main_frame)
        canvas_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # Adicionar barras de rolagem
        h_scrollbar = tk.Scrollbar(canvas_frame, orient=tk.HORIZONTAL)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)

        v_scrollbar = tk.Scrollbar(canvas_frame)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.canvas = tk.Canvas(
            canvas_frame,
            width=800,
            height=600,
            xscrollcommand=h_scrollbar.set,
            yscrollcommand=v_scrollbar.set,
        )
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        h_scrollbar.config(command=self.canvas.xview)
        v_scrollbar.config(command=self.canvas.yview)

        # Gerenciador de botões
        self.button_manager = ButtonManager(main_frame, self.callbacks)
        button_frame, button_frame2 = self.button_manager.create_main_buttons()

        # Adicionar botões de sugestão
        self.button_manager.add_suggestion_buttons(button_frame, button_frame2)

        # Centralizar janela na tela
        center_window(self.root)

        return self.root, self.canvas, self.class_var, self.status_label

    def update_image_info(self, width, height):
        """
        Atualiza as informações da imagem.

        Args:
            width: Largura da imagem
            height: Altura da imagem
        """
        if self.info_label:
            self.info_label.config(
                text=f"Imagem: {os.path.basename(self.image_path)} | Dimensões: {width}x{height}"
            )

    def update_status(self, msg=None, box_count=None):
        """
        Atualiza o texto de status.

        Args:
            msg: Mensagem a ser exibida (opcional)
            box_count: Número de caixas (opcional)
        """
        if not self.status_label:
            return

        try:
            if msg:
                if box_count is not None:
                    self.status_label.config(text=f"Contagem: {box_count} | {msg}")
                else:
                    self.status_label.config(text=msg)
            elif box_count is not None:
                self.status_label.config(text=f"Contagem: {box_count} | Desenhe clicando e arrastando")
        except Exception as e:
            logger.error(f"Erro ao atualizar status: {e}")

    def get_button_manager(self):
        """
        Obtém o gerenciador de botões.

        Returns:
            ButtonManager
        """
        return self.button_manager

    def start_main_loop(self):
        """Inicia o loop principal da interface."""
        if self.root:
            self.root.mainloop()