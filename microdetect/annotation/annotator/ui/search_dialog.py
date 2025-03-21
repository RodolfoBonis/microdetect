"""
Diálogo para busca e seleção de imagens para anotação.
"""

import glob
import logging
import os
import tkinter as tk
from tkinter import messagebox
from typing import List, Optional, Tuple

from PIL import Image, ImageTk

from microdetect.annotation.annotator.ui.base import center_window, create_secure_dialog

logger = logging.getLogger(__name__)


class SearchDialog:
    """
    Diálogo para buscar e filtrar imagens para anotação.
    """

    def __init__(self, image_dir: str, output_dir: str, last_annotated_path: Optional[str] = None):
        """
        Inicializa o diálogo de busca.

        Args:
            image_dir: Diretório de imagens
            output_dir: Diretório de anotações
            last_annotated_path: Caminho da última imagem anotada (opcional)
        """
        self.image_dir = image_dir
        self.output_dir = output_dir
        self.last_annotated_path = last_annotated_path
        self.search_image_refs = {}
        self.all_images = []
        self.filtered_images = []
        self.result_images = []
        self.result_mode = 0  # 0=Continuar, 1=Reiniciar, 2=Revisar, 3=Específica
        self.start_index = 0  # Índice inicial para navegação contínua

    def get_all_images(self) -> List[str]:
        """
        Obtém todas as imagens do diretório.

        Returns:
            Lista de caminhos para as imagens
        """
        all_images = []
        for ext in ["*.jpg", "*.jpeg", "*.png"]:
            all_images.extend(glob.glob(os.path.join(self.image_dir, ext)))

        # Ordenar imagens
        all_images.sort()
        return all_images

    def show(self) -> Tuple[List[str], int]:
        """
        Exibe o diálogo de busca e retorna as imagens selecionadas.

        Returns:
            Tuple com lista de caminhos de imagem selecionados e modo de continuação
        """
        # Obter todas as imagens
        self.all_images = self.get_all_images()

        if not self.all_images:
            messagebox.showinfo("Informação", "Nenhuma imagem encontrada no diretório.")
            return [], 0

        # Limpar todas as referências de imagem
        self.search_image_refs = {}

        # Inicializar lista filtrada
        self.filtered_images = self.all_images.copy()

        # Criar janela de busca de forma segura
        search_window = create_secure_dialog()
        search_window.title("Buscar e Filtrar Imagens")
        search_window.geometry("800x650")  # Aumentado para acomodar os botões extras
        search_window.minsize(600, 450)

        # Frame principal
        main_frame = tk.Frame(search_window)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Frame de informações de progresso (se houver progresso anterior)
        if self.last_annotated_path:
            self._create_progress_frame(main_frame)

        # Frame de busca
        search_frame = tk.Frame(main_frame)
        search_frame.pack(fill=tk.X, pady=5)

        # Campo de busca
        tk.Label(search_frame, text="Buscar por nome:").pack(side=tk.LEFT, padx=5)
        search_var = tk.StringVar()
        search_entry = tk.Entry(search_frame, textvariable=search_var, width=30)
        search_entry.pack(side=tk.LEFT, padx=5)

        # Opções de filtro de busca
        filter_frame = tk.Frame(main_frame)
        filter_frame.pack(fill=tk.X, pady=5)

        # Opção para mostrar apenas imagens anotadas
        show_annotated_var = tk.BooleanVar(value=False)
        show_annotated_check = tk.Checkbutton(
            filter_frame, text="Mostrar apenas imagens anotadas", variable=show_annotated_var
        )
        show_annotated_check.pack(side=tk.LEFT, padx=5)

        # Opção para mostrar apenas imagens não anotadas
        show_unannotated_var = tk.BooleanVar(value=False)
        show_unannotated_check = tk.Checkbutton(
            filter_frame, text="Mostrar apenas imagens não anotadas", variable=show_unannotated_var
        )
        show_unannotated_check.pack(side=tk.LEFT, padx=20)

        # Frame para a lista de imagens
        list_frame = tk.Frame(main_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        # Label para contagem
        total_label = tk.Label(list_frame, text=f"Total: {len(self.all_images)} imagens", anchor="w")
        total_label.pack(fill=tk.X)

        # Lista de imagens com scrollbar
        list_subframe = tk.Frame(list_frame)
        list_subframe.pack(fill=tk.BOTH, expand=True)

        scrollbar = tk.Scrollbar(list_subframe)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        image_listbox = tk.Listbox(list_subframe, selectmode=tk.SINGLE, yscrollcommand=scrollbar.set, font=("Arial", 11))
        image_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar.config(command=image_listbox.yview)

        # Preview da imagem selecionada
        preview_frame = tk.Frame(main_frame)
        preview_frame.pack(fill=tk.X, pady=10)

        preview_label = tk.Label(preview_frame, text="Preview:")
        preview_label.pack(anchor="w")

        preview_image = tk.Label(preview_frame, text="Selecione uma imagem para visualizar")
        preview_image.pack(fill=tk.X, pady=5)

        # Função para atualizar a lista quando o usuário buscar
        def update_image_list():
            # Obter termo de busca
            search_term = search_var.get().lower().strip()
            show_annotated = show_annotated_var.get()
            show_unannotated = show_unannotated_var.get()

            # Filtrar imagens
            self.filtered_images = []
            for img_path in self.all_images:
                img_filename = os.path.basename(img_path).lower()
                base_name = os.path.splitext(os.path.basename(img_path))[0]
                annotation_path = os.path.join(self.output_dir, f"{base_name}.txt")
                is_annotated = os.path.exists(annotation_path)

                # Verificar filtros
                if search_term and search_term not in img_filename:
                    continue

                if show_annotated and not is_annotated:
                    continue

                if show_unannotated and is_annotated:
                    continue

                self.filtered_images.append(img_path)

            # Atualizar listbox
            image_listbox.delete(0, tk.END)
            for img_path in self.filtered_images:
                base_name = os.path.splitext(os.path.basename(img_path))[0]
                annotation_path = os.path.join(self.output_dir, f"{base_name}.txt")
                is_annotated = os.path.exists(annotation_path)

                display_text = f"{os.path.basename(img_path)}"
                if is_annotated:
                    display_text += " [Anotada]"

                image_listbox.insert(tk.END, display_text)

            # Atualizar contadores
            total_label.config(text=f"Total: {len(self.filtered_images)} / {len(self.all_images)} imagens")

        # Função auxiliar para impedir que os checkboxes sejam ambos selecionados
        def handle_annotated_check():
            if show_annotated_var.get() and show_unannotated_var.get():
                show_unannotated_var.set(False)
            update_image_list()

        def handle_unannotated_check():
            if show_annotated_var.get() and show_unannotated_var.get():
                show_annotated_var.set(False)
            update_image_list()

        # Configurar callbacks para os checkboxes
        show_annotated_check.config(command=handle_annotated_check)
        show_unannotated_check.config(command=handle_unannotated_check)

        # Botão de busca
        search_button = tk.Button(search_frame, text="Buscar", command=update_image_list)
        search_button.pack(side=tk.LEFT, padx=5)

        # Função para mostrar preview
        def show_preview(*args):
            # Limpar preview anterior
            preview_image.config(image="", text="Selecione uma imagem para visualizar")

            # Obter seleção
            selection = image_listbox.curselection()
            if not selection:
                return

            # Obter caminho da imagem
            index = selection[0]
            if index >= len(self.filtered_images):
                return

            img_path = self.filtered_images[index]

            try:
                # Carregar e redimensionar imagem para preview
                pil_img = Image.open(img_path)

                # Redimensionar mantendo proporção
                max_size = 300
                width, height = pil_img.size
                if width > height:
                    new_width = max_size
                    new_height = int(height * (max_size / width))
                else:
                    new_height = max_size
                    new_width = int(width * (max_size / height))

                pil_img = pil_img.resize((new_width, new_height), Image.LANCZOS)

                # Criar e armazenar a referência à imagem localmente
                key = f"preview_{os.path.basename(img_path)}"
                self.search_image_refs[key] = ImageTk.PhotoImage(pil_img)

                # Atualizar label com a imagem
                preview_image.config(image=self.search_image_refs[key], text="")

                # Obter informações do status de anotação
                base_name = os.path.splitext(os.path.basename(img_path))[0]
                annotation_path = os.path.join(self.output_dir, f"{base_name}.txt")
                is_annotated = os.path.exists(annotation_path)

                if is_annotated:
                    # Contar anotações
                    with open(annotation_path, "r") as f:
                        annotations = f.readlines()
                    preview_label.config(text=f"Preview: {os.path.basename(img_path)} - {len(annotations)} anotações")
                else:
                    preview_label.config(text=f"Preview: {os.path.basename(img_path)} - Não anotada")

            except Exception as e:
                preview_image.config(text=f"Erro ao carregar preview: {str(e)}")

        # Vincular evento de seleção para mostrar preview
        image_listbox.bind("<<ListboxSelect>>", show_preview)

        # Função para anotar imagem selecionada
        def annotate_selected():
            selection = image_listbox.curselection()

            if not selection:
                messagebox.showinfo("Informação", "Selecione uma imagem para anotar.")
                return

            # Obter imagem selecionada
            index = selection[0]
            if index >= len(self.filtered_images):
                return

            # MODIFICAÇÃO: Retornar a lista filtrada a partir do índice selecionado
            selected_image = self.filtered_images[index]
            self.start_index = index
            self.result_images = self.filtered_images
            self.result_mode = 3  # Modo especial: imagem específica selecionada

            # Log para debug
            logger.info(
                f"Selecionada imagem {os.path.basename(selected_image)} (índice {index}). "
                f"Total de {len(self.filtered_images)} imagens na lista filtrada."
            )

            search_window.destroy()

        # Botões de ação
        button_frame = tk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)

        # Botão para limpar seleção
        def clear_selection():
            image_listbox.selection_clear(0, tk.END)

        # Adicionar botões
        tk.Button(button_frame, text="Cancelar", command=search_window.destroy, width=15).pack(side=tk.RIGHT, padx=5)

        tk.Button(button_frame, text="Anotar Imagem Selecionada", command=annotate_selected, bg="lightgreen", width=25).pack(
            side=tk.RIGHT, padx=5
        )

        tk.Button(button_frame, text="Limpar Seleção", command=clear_selection, width=15).pack(side=tk.LEFT, padx=5)

        # Iniciar busca com os valores padrão
        update_image_list()

        # Configurar eventos de teclado para busca rápida
        search_entry.bind("<Return>", lambda e: update_image_list())

        # Ativar duplo clique para anotar diretamente
        image_listbox.bind("<Double-Button-1>", lambda e: annotate_selected())

        # Destacar última imagem anotada ou próxima, se houver
        if self.last_annotated_path and self.last_annotated_path in self.filtered_images:
            last_index = self.filtered_images.index(self.last_annotated_path)

            # Mostrar a próxima imagem por padrão
            if last_index < len(self.filtered_images) - 1:
                next_index = last_index + 1
                image_listbox.selection_set(next_index)
                image_listbox.see(next_index)
            else:
                # Se for a última imagem, selecionar a primeira
                image_listbox.selection_set(0)
                image_listbox.see(0)

            # Mostrar preview
            image_listbox.event_generate("<<ListboxSelect>>")

        # Centralizar janela
        center_window(search_window)

        # Tornar modal
        search_window.transient()
        search_window.grab_set()

        # Limpar recursos ao fechar
        def on_closing():
            # Limpar explicitamente todas as referências de imagem
            self.search_image_refs.clear()

            # Remover referência à janela temporária se existir
            if hasattr(search_window, "_temp_root") and search_window._temp_root:
                try:
                    search_window._temp_root.destroy()
                except:
                    pass
            search_window.destroy()

        search_window.protocol("WM_DELETE_WINDOW", on_closing)
        search_window.wait_window()

        return self.result_images, self.result_mode

    def _create_progress_frame(self, parent_frame):
        """
        Cria o frame de informações de progresso.

        Args:
            parent_frame: Frame pai onde será adicionado
        """
        progress_frame = tk.LabelFrame(parent_frame, text="Progresso de Anotação")
        progress_frame.pack(fill=tk.X, pady=10)

        # Exibir informação sobre o último arquivo anotado
        last_file_name = os.path.basename(self.last_annotated_path)
        last_index = self.all_images.index(self.last_annotated_path) if self.last_annotated_path in self.all_images else -1

        progress_info = tk.Frame(progress_frame)
        progress_info.pack(fill=tk.X, padx=5, pady=5)

        tk.Label(progress_info, text=f"Última imagem anotada: {last_file_name}", font=("Arial", 10, "bold")).pack(
            side=tk.LEFT, padx=5
        )

        # Exibir progresso total
        if last_index >= 0:
            progress_percent = (last_index + 1) / len(self.all_images) * 100
            tk.Label(progress_info, text=f"Progresso: {last_index + 1}/{len(self.all_images)} ({progress_percent:.1f}%)").pack(
                side=tk.LEFT, padx=20
            )

        # Botões de acesso rápido para opções de navegação
        quick_frame = tk.Frame(progress_frame)
        quick_frame.pack(fill=tk.X, padx=5, pady=10)

        tk.Label(quick_frame, text="Opções rápidas de navegação:", font=("Arial", 10, "bold")).pack(anchor="w", padx=5, pady=5)

        # Botões para cada opção de navegação
        button_frame = tk.Frame(quick_frame)
        button_frame.pack(fill=tk.X, padx=5, pady=5)

        # Função para continuar com uma opção específica
        def quick_continue(mode):
            self.result_mode = mode

            if mode == 0:  # Continuar de onde parou
                next_index = last_index + 1 if last_index < len(self.all_images) - 1 else 0
                # MODIFICAÇÃO: Manter toda a lista e definir o índice inicial
                self.start_index = next_index
                self.result_images = self.all_images
            elif mode == 1:  # Recomeçar do início
                # MODIFICAÇÃO: Manter toda a lista e começar do início
                self.start_index = 0
                self.result_images = self.all_images
            else:  # Revisar a última imagem
                # MODIFICAÇÃO: Manter toda a lista e definir o índice para a última imagem anotada
                self.start_index = last_index if last_index >= 0 else 0
                self.result_images = self.all_images

            # Obter a janela pai e destruir
            parent = progress_frame.master.master
            parent.destroy()

        # Continuar da próxima imagem
        tk.Button(
            button_frame,
            text="Continuar da Próxima Imagem",
            command=lambda: quick_continue(0),
            bg="lightgreen",
            padx=10,
            pady=5,
            width=25,
        ).pack(side=tk.LEFT, padx=5, pady=5)

        # Recomeçar do início
        tk.Button(
            button_frame,
            text="Recomeçar do Início",
            command=lambda: quick_continue(1),
            bg="#FFD580",  # Light orange
            padx=10,
            pady=5,
            width=25,
        ).pack(side=tk.LEFT, padx=5, pady=5)

        # Revisar última imagem
        tk.Button(
            button_frame,
            text="Revisar Última Imagem",
            command=lambda: quick_continue(2),
            bg="#ADD8E6",  # Light blue
            padx=10,
            pady=5,
            width=25,
        ).pack(side=tk.LEFT, padx=5, pady=5)

        # Adicionar separador
        tk.Frame(progress_frame, height=2, bd=1, relief=tk.SUNKEN).pack(fill=tk.X, padx=5, pady=10)

        tk.Label(progress_frame, text="Ou selecione uma imagem específica abaixo:", font=("Arial", 10)).pack(
            anchor="w", padx=5, pady=5
        )
