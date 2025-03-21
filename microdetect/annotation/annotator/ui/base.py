"""
Funções base de UI para o módulo de anotação.
"""

import logging
import tkinter as tk

logger = logging.getLogger(__name__)


def create_secure_dialog() -> tk.Toplevel:
    """
    Cria uma janela de diálogo segura que não terá problemas com referências de imagens.

    Returns:
        A janela de diálogo Toplevel
    """
    try:
        # Verificar se já temos uma instância Tk ativa
        root = None

        # Verificar se tk._default_root existe antes de tentar acessá-lo
        if hasattr(tk, "_default_root") and tk._default_root is not None:
            # Usar a janela raiz existente
            for widget in tk._default_root.winfo_children():
                if isinstance(widget, tk.Toplevel) and widget.winfo_exists():
                    root = widget
                    break

            if root is None:
                # Se não encontrou um Toplevel, usar o _default_root diretamente
                root = tk._default_root

        # Se não encontrou nenhuma janela, criar uma nova
        if root is None:
            # Criar uma nova janela raiz e escondê-la
            temp_root = tk.Tk()
            temp_root.withdraw()
            dialog = tk.Toplevel(temp_root)
            # Guardar referência para destruir depois
            dialog._temp_root = temp_root
        else:
            # Usar a janela existente como pai
            dialog = tk.Toplevel(root)
            dialog.transient(root)

        return dialog
    except Exception as e:
        # Fallback: criar um novo Toplevel simples
        logger.error(f"Erro ao criar diálogo seguro: {e}")
        root = tk.Tk()
        root.withdraw()
        dialog = tk.Toplevel(root)
        dialog._temp_root = root
        return dialog


def is_window_valid(widget=None):
    """
    Verifica se uma janela/widget Tkinter ainda é válida.
    Retorna False apenas se confirmado que a janela foi destruída.

    Args:
        widget: Widget Tkinter a ser verificado (opcional)

    Returns:
        bool: True se a janela parece válida, False se confirmado que foi destruída
    """
    # Se nenhum widget fornecido, assumir que a janela está OK
    if widget is None:
        return True

    try:
        # Tentar acessar uma propriedade qualquer do widget
        # Isso gerará exceção se o widget foi destruído
        widget.winfo_exists()
        return True
    except tk.TclError as e:
        # Verificar se a exceção indica que a janela foi realmente destruída
        error_msg = str(e).lower()
        if "application has been destroyed" in error_msg or "invalid command name" in error_msg:
            return False
        # Outros erros Tkinter não significam necessariamente que a janela foi fechada
        logger.warning(f"Aviso: Erro Tkinter não fatal: {e}")
        return True


def center_window(window):
    """
    Centraliza uma janela na tela.

    Args:
        window: Janela Tkinter a ser centralizada
    """
    window.update_idletasks()
    width = window.winfo_width()
    height = window.winfo_height()
    x = (window.winfo_screenwidth() // 2) - (width // 2)
    y = (window.winfo_screenheight() // 2) - (height // 2)
    window.geometry(f"{width}x{height}+{x}+{y}")


def configure_window_close(window, callback):
    """
    Configura o protocolo de fechamento de uma janela.

    Args:
        window: Janela Tkinter
        callback: Função a ser chamada quando a janela for fechada
    """
    window.protocol("WM_DELETE_WINDOW", callback)
