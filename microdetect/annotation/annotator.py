"""
Módulo para anotação manual de imagens.
Implementação com todas as funcionalidades avançadas preservando o núcleo funcional.
"""

import glob
import json
import logging
import os
import re
import shutil
import time
import tkinter as tk
from datetime import datetime
from tkinter import messagebox
from typing import Dict, List, Optional, Tuple

import cv2
import numpy as np
from PIL import Image, ImageTk

from microdetect.utils.config import config

logger = logging.getLogger(__name__)

# Constantes
KEYBOARD_SHORTCUTS = {
    "a": "Imagem anterior",
    "d": "Próxima imagem",
    "s": "Salvar anotações",
    "z": "Desfazer última ação",
    "r": "Reiniciar anotações",
    "e": "Mover/editar seleção",
    "c": "Alternar entre classes",
    "q": "Sair sem salvar",
    "p": "Ativar/desativar modo navegação",
    "x": "Salvar e sair",
    "Del": "Excluir seleção",
    "Esc": "Cancelar seleção atual",
}

DEFAULT_AUTO_SAVE = True
DEFAULT_AUTO_SAVE_INTERVAL = 300  # 5 minutos

# Constantes para alças de redimensionamento
HANDLE_NONE = 0
HANDLE_NW = 1  # Noroeste
HANDLE_NE = 2  # Nordeste
HANDLE_SE = 3  # Sudeste
HANDLE_SW = 4  # Sudoeste
HANDLE_N = 5   # Norte
HANDLE_E = 6   # Leste
HANDLE_S = 7   # Sul
HANDLE_W = 8   # Oeste


class ImageAnnotator:
    """
    Ferramenta para anotação manual de imagens de microorganismos.
    """

    def __init__(
        self,
        classes: List[str] = None,
        auto_save: bool = DEFAULT_AUTO_SAVE,
        auto_save_interval: int = DEFAULT_AUTO_SAVE_INTERVAL,
    ):
        """
        Inicializa o anotador de imagens.

        Args:
            classes: Lista de classes para anotação
            auto_save: Se True, salva automaticamente as anotações
            auto_save_interval: Intervalo em segundos entre salvamentos automáticos
        """
        self.classes = classes or config.get("classes", ["0-levedura", "1-fungo", "2-micro-alga"])
        self.progress_file = ".annotation_progress.json"
        self.auto_save = auto_save
        self.auto_save_interval = auto_save_interval
        self.last_save_time = time.time()

        # Inicializar variáveis utilizadas nas funções
        self.original_w = 0
        self.original_h = 0
        self.display_w = 0
        self.display_h = 0
        self.display_scale = 1.0
        self.scale_factor = 1.0
        self.user_cancelled = False
        self.canvas = None
        self.current_img_tk = None

        # Lista para armazenar bounding boxes
        self.bounding_boxes = []

        # Histórico para desfazer ações
        self.action_history = []

        # Estado para redimensionamento
        self.resize_handle = HANDLE_NONE
        self.handle_size = 6
        self.original_box_state = None

        # Controle de modos
        self.pan_mode = False
        self.window_closed = False

    def _is_window_valid(self, widget=None):
        """
        Verifica se uma janela/widget Tkinter ainda é válida.
        Retorna False apenas se confirmado que a janela foi destruída.

        Args:
            widget: Widget Tkinter a ser verificado (opcional)

        Returns:
            bool: True se a janela parece válida, False se confirmado que foi destruída
        """
        # Se já sabemos que a janela foi fechada, retornar False
        if self.window_closed:
            return False

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
                self.window_closed = True
                return False
            # Outros erros Tkinter não significam necessariamente que a janela foi fechada
            print(f"Aviso: Erro Tkinter não fatal: {e}")
            return True

    def _load_image(self, image_path: str) -> Optional[Tuple[np.ndarray, int, int]]:
        """
        Carrega uma imagem com tratamento de erro adequado.

        Args:
            image_path: Caminho para a imagem

        Returns:
            Tuple com imagem carregada, largura e altura ou None em caso de erro
        """
        try:
            img = cv2.imread(image_path)
            if img is None:
                raise ValueError(f"Imagem não pôde ser carregada: {image_path}")
            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            h, w = img_rgb.shape[:2]
            return img_rgb, w, h
        except Exception as e:
            logger.error(f"Erro ao carregar imagem {image_path}: {str(e)}")
            return None, 0, 0

    def _check_auto_save(self, bounding_boxes, output_dir, base_name) -> bool:
        """
        Verifica se é hora de auto-salvar e salva se necessário.

        Args:
            bounding_boxes: Lista de bounding boxes para salvar
            output_dir: Diretório de saída
            base_name: Nome base do arquivo

        Returns:
            True se o salvamento automático foi realizado
        """
        if not self.auto_save:
            return False

        current_time = time.time()
        if current_time - self.last_save_time > self.auto_save_interval:
            self._save_annotations(bounding_boxes, output_dir, base_name)
            self.last_save_time = current_time
            return True
        return False

    def _save_annotations(self, bounding_boxes, output_dir, base_name) -> str:
        """
        Salva as anotações no formato YOLO.

        Args:
            bounding_boxes: Lista de bounding boxes para salvar
            output_dir: Diretório de saída
            base_name: Nome base do arquivo

        Returns:
            Caminho para o arquivo de anotação salvo
        """
        txt_filename = f"{base_name}.txt"
        txt_path = os.path.join(output_dir, txt_filename)

        with open(txt_path, "w") as f:
            for box in bounding_boxes:
                class_id, x1, y1, x2, y2 = box

                # Converter para formato YOLO: class_id center_x center_y width height (normalizado)
                box_w = (x2 - x1) / self.original_w
                box_h = (y2 - y1) / self.original_h
                center_x = (x1 + (x2 - x1) / 2) / self.original_w
                center_y = (y1 + (y2 - y1) / 2) / self.original_h

                f.write(f"{class_id} {center_x} {center_y} {box_w} {box_h}\n")

        logger.info(f"Anotação salva em {txt_path}. {len(bounding_boxes)} caixas anotadas.")
        return txt_path

    def _add_to_history(self, action_type, data):
        """
        Adiciona uma ação ao histórico para suportar desfazer (undo).

        Args:
            action_type: Tipo da ação ('add', 'move', 'resize', 'delete')
            data: Dados específicos da ação
        """
        self.action_history.append({"type": action_type, "data": data})
        # Limitar tamanho do histórico
        if len(self.action_history) > 50:
            self.action_history.pop(0)

    def _detect_resize_handle(self, canvas_x, canvas_y, box_idx):
        """
        Detecta se o clique foi em uma alça de redimensionamento.

        Args:
            canvas_x: Coordenada X do clique no canvas
            canvas_y: Coordenada Y do clique no canvas
            box_idx: Índice da caixa selecionada

        Returns:
            Identificador da alça ou HANDLE_NONE se não houver alça
        """
        if box_idx is None or box_idx >= len(self.bounding_boxes):
            return HANDLE_NONE

        # Obter coordenadas da caixa
        _, x1, y1, x2, y2 = self.bounding_boxes[box_idx]

        # Converter para coordenadas do canvas
        canvas_x1 = x1 * self.display_scale * self.scale_factor
        canvas_y1 = y1 * self.display_scale * self.scale_factor
        canvas_x2 = x2 * self.display_scale * self.scale_factor
        canvas_y2 = y2 * self.display_scale * self.scale_factor

        # Calcular pontos médios
        mid_x = (canvas_x1 + canvas_x2) / 2
        mid_y = (canvas_y1 + canvas_y2) / 2

        # Distância de detecção (um pouco maior que o tamanho da alça)
        detect_distance = self.handle_size * 1.5

        # Verificar cantos
        if abs(canvas_x - canvas_x1) <= detect_distance and abs(canvas_y - canvas_y1) <= detect_distance:
            return HANDLE_NW
        if abs(canvas_x - canvas_x2) <= detect_distance and abs(canvas_y - canvas_y1) <= detect_distance:
            return HANDLE_NE
        if abs(canvas_x - canvas_x2) <= detect_distance and abs(canvas_y - canvas_y2) <= detect_distance:
            return HANDLE_SE
        if abs(canvas_x - canvas_x1) <= detect_distance and abs(canvas_y - canvas_y2) <= detect_distance:
            return HANDLE_SW

        # Verificar lados
        if abs(canvas_x - mid_x) <= detect_distance and abs(canvas_y - canvas_y1) <= detect_distance:
            return HANDLE_N
        if abs(canvas_x - canvas_x2) <= detect_distance and abs(canvas_y - mid_y) <= detect_distance:
            return HANDLE_E
        if abs(canvas_x - mid_x) <= detect_distance and abs(canvas_y - canvas_y2) <= detect_distance:
            return HANDLE_S
        if abs(canvas_x - canvas_x1) <= detect_distance and abs(canvas_y - mid_y) <= detect_distance:
            return HANDLE_W

        return HANDLE_NONE

    def _redraw_with_zoom(self, img_display, canvas):
        """
        Redesenha a imagem com o zoom atual.

        Args:
            img_display: Imagem original para exibição
            canvas: Canvas onde a imagem será desenhada
        """
        # Verificar se a janela ainda é válida
        if not self._is_window_valid(canvas):
            return

        try:
            # Calcular novas dimensões
            new_w = int(self.display_w * self.scale_factor)
            new_h = int(self.display_h * self.scale_factor)

            # Redimensionar imagem
            img_resized = cv2.resize(img_display, (new_w, new_h))
            self.current_img_tk = ImageTk.PhotoImage(Image.fromarray(img_resized))

            # Atualizar imagem no canvas
            canvas.delete("background")
            canvas.create_image(0, 0, anchor=tk.NW, image=self.current_img_tk, tags="background")
            canvas.config(scrollregion=canvas.bbox(tk.ALL))
        except Exception as e:
            logger.error(f"Erro ao redesenhar imagem com zoom: {e}")
            # Não definir window_closed aqui, apenas logar o erro

    def annotate_image(self, image_path: str, output_dir: str) -> Optional[str]:
        """
        Ferramenta para anotar manualmente células de levedura em imagens de microscopia com bounding boxes.

        Args:
            image_path: Caminho para a imagem a ser anotada
            output_dir: Diretório para salvar as anotações

        Returns:
            Caminho para o arquivo de anotação criado ou None se cancelado
        """
        # Assegurar que o diretório de saída existe
        os.makedirs(output_dir, exist_ok=True)

        # Resetar flags e estado
        self.user_cancelled = False
        self.window_closed = False
        self.bounding_boxes = []
        self.action_history = []
        self.resize_handle = HANDLE_NONE
        self.original_box_state = None
        self.pan_mode = False

        # Carregar imagem
        loaded_data = self._load_image(image_path)
        if loaded_data[0] is None:
            return None

        img, w, h = loaded_data
        self.original_w, self.original_h = w, h

        # Dimensionar imagem se muito grande
        scale = min(800 / w, 600 / h)
        if scale < 1:
            self.display_w, self.display_h = int(w * scale), int(h * scale)
            img_display = cv2.resize(img, (self.display_w, self.display_h))
            self.display_scale = scale
        else:
            self.display_w, self.display_h = w, h
            img_display = img.copy()
            self.display_scale = 1.0

        # Reiniciar scale factor
        self.scale_factor = 1.0

        # Verificar se já existem anotações para esta imagem
        base_name = os.path.splitext(os.path.basename(image_path))[0]
        existing_annotation_path = os.path.join(output_dir, f"{base_name}.txt")

        if os.path.exists(existing_annotation_path):
            logger.info(f"Carregando anotações existentes de {existing_annotation_path}")

            # Carregar anotações existentes
            with open(existing_annotation_path, "r") as f:
                for line in f:
                    parts = line.strip().split()
                    if len(parts) == 5:  # formato YOLO: class x_center y_center width height
                        class_id, x_center, y_center, box_w, box_h = parts

                        # Converter de YOLO para pixel
                        x_center = float(x_center) * w
                        y_center = float(y_center) * h
                        box_w = float(box_w) * w
                        box_h = float(box_h) * h

                        # Calcular coordenadas absolutas (x1, y1, x2, y2)
                        x1 = int(x_center - box_w / 2)
                        y1 = int(y_center - box_h / 2)
                        x2 = int(x_center + box_w / 2)
                        y2 = int(y_center + box_h / 2)

                        # Adicionar à lista de bounding boxes
                        self.bounding_boxes.append((class_id, x1, y1, x2, y2))

        # Variáveis para a sessão de anotação atual
        start_x, start_y = None, None
        current_rect = None
        selected_box_idx = None

        # Classe padrão
        current_class = self.classes[0] if self.classes else "0-levedura"

        # Modo de edição
        edit_mode = False

        # Criar janela Tkinter
        root = tk.Tk()
        root.title(f"Anotação: {os.path.basename(image_path)}")

        # Criar frame principal
        main_frame = tk.Frame(root)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Painel de controle
        control_frame = tk.Frame(main_frame)
        control_frame.pack(side=tk.TOP, fill=tk.X)

        # Seleção de classe
        class_label = tk.Label(control_frame, text="Selecionar classe:")
        class_label.pack(side=tk.LEFT, padx=5)

        class_var = tk.StringVar(root)
        class_var.set(current_class)

        class_menu = tk.OptionMenu(control_frame, class_var, *self.classes)
        class_menu.pack(side=tk.LEFT, padx=5)

        # Status label
        status_label = tk.Label(
            main_frame,
            text=f"Contagem: {len(self.bounding_boxes)} | Desenhe clicando e arrastando",
        )
        status_label.pack(side=tk.BOTTOM, fill=tk.X)

        # Informações da imagem
        info_label = tk.Label(
            main_frame,
            text=f"Imagem: {os.path.basename(image_path)} | Dimensões: {w}x{h}",
        )
        info_label.pack(side=tk.BOTTOM, fill=tk.X)

        # Criar canvas com barras de rolagem
        canvas_frame = tk.Frame(main_frame)
        canvas_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # Adicionar barras de rolagem
        h_scrollbar = tk.Scrollbar(canvas_frame, orient=tk.HORIZONTAL)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)

        v_scrollbar = tk.Scrollbar(canvas_frame)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        canvas = tk.Canvas(
            canvas_frame,
            width=min(self.display_w, 800),
            height=min(self.display_h, 600),
            xscrollcommand=h_scrollbar.set,
            yscrollcommand=v_scrollbar.set,
        )
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        h_scrollbar.config(command=canvas.xview)
        v_scrollbar.config(command=canvas.yview)

        # Converter para PhotoImage para o Tkinter
        img_tk = ImageTk.PhotoImage(Image.fromarray(img_display))

        # Criar imagem no canvas
        canvas.create_image(0, 0, anchor=tk.NW, image=img_tk, tags="background")
        canvas.config(scrollregion=canvas.bbox(tk.ALL))

        # Armazenar referências
        self.canvas = canvas
        self.current_img_tk = img_tk

        # Resultado da anotação
        annotation_path = None

        def reset_window_closed():
            """Reseta o flag window_closed para False e verifica estado do canvas."""
            # Apenas resetar se a janela realmente existir
            try:
                if canvas.winfo_exists():
                    self.window_closed = False
                    return True
            except:
                pass

            print("Não foi possível resetar window_closed - a janela parece inválida")
            return False

        def set_current_class(event=None):
            nonlocal current_class
            current_class = class_var.get()
            update_status()

        def update_status(msg=None):
            """Atualiza o status na interface com proteção contra erros."""
            # Verificar se a janela ainda é válida
            if not self._is_window_valid(status_label):
                return

            try:
                status_text = msg if msg else f"Classe: {current_class} | Contagem: {len(self.bounding_boxes)}"
                if edit_mode:
                    status_text += " | MODO EDIÇÃO: Selecione uma caixa para mover/redimensionar"
                elif self.pan_mode:
                    status_text += " | MODO NAVEGAÇÃO: Arraste para movimentar a imagem"
                else:
                    status_text += " | Desenhe clicando e arrastando"

                status_label.config(text=status_text)

                # Atualizar também os botões de modo
                if edit_mode:
                    edit_button.config(text="Modo Desenho (E)", bg="lightblue")
                else:
                    edit_button.config(text="Modo Edição (E)", bg="#f0f0f0")  # Substituir "SystemButtonFace"

                if self.pan_mode:
                    pan_button.config(text="Modo Desenho (P)", bg="lightblue")
                else:
                    pan_button.config(text="Modo Navegação (P)", bg="#f0f0f0")
            except Exception as e:
                logger.error(f"Erro ao atualizar status: {e}")
                # Não definir window_closed aqui

        def redraw_all_boxes(highlight_idx=None):
            """Redesenha todas as bounding boxes no canvas"""
            # Verificar se a janela ainda é válida
            if not self._is_window_valid(canvas):
                return

            try:
                # Limpar o canvas
                canvas.delete("all")

                # Redesenhar a imagem de fundo
                canvas.create_image(0, 0, anchor=tk.NW, image=self.current_img_tk, tags="background")

                # Redesenhar todas as boxes
                for i, (class_id, x1, y1, x2, y2) in enumerate(self.bounding_boxes):
                    # Converter para coordenadas do canvas
                    canvas_x1 = x1 * self.display_scale * self.scale_factor
                    canvas_y1 = y1 * self.display_scale * self.scale_factor
                    canvas_x2 = x2 * self.display_scale * self.scale_factor
                    canvas_y2 = y2 * self.display_scale * self.scale_factor

                    # Determinar cor (destacar se selecionado)
                    outline_color = "red" if i == highlight_idx else "green"
                    outline_width = 3 if i == highlight_idx else 2

                    # Encontrar nome da classe para exibição
                    class_name = next(
                        (c for c in self.classes if c.startswith(class_id)),
                        f"{class_id}-desconhecido",
                    )

                    # Desenhar retângulo
                    canvas.create_rectangle(
                        canvas_x1, canvas_y1, canvas_x2, canvas_y2,
                        outline=outline_color, width=outline_width, tags="box"
                    )

                    # Desenhar rótulo
                    canvas.create_text(
                        canvas_x1,
                        canvas_y1 - 5,
                        text=f"{class_name} #{i + 1}",
                        anchor=tk.SW,
                        fill=outline_color,
                        font=("Arial", 10, "bold"),
                        tags="label",
                    )

                    # Se esta caixa estiver selecionada, adicionar alças de redimensionamento
                    if i == highlight_idx:
                        # Calcular pontos médios
                        mid_x = (canvas_x1 + canvas_x2) / 2
                        mid_y = (canvas_y1 + canvas_y2) / 2

                        # Tamanho das alças
                        handle_size = self.handle_size

                        # Desenhar alças nos cantos
                        # NO (Noroeste)
                        canvas.create_rectangle(
                            canvas_x1 - handle_size,
                            canvas_y1 - handle_size,
                            canvas_x1 + handle_size,
                            canvas_y1 + handle_size,
                            fill=outline_color,
                            tags="handle",
                        )
                        # NE (Nordeste)
                        canvas.create_rectangle(
                            canvas_x2 - handle_size,
                            canvas_y1 - handle_size,
                            canvas_x2 + handle_size,
                            canvas_y1 + handle_size,
                            fill=outline_color,
                            tags="handle",
                        )
                        # SE (Sudeste)
                        canvas.create_rectangle(
                            canvas_x2 - handle_size,
                            canvas_y2 - handle_size,
                            canvas_x2 + handle_size,
                            canvas_y2 + handle_size,
                            fill=outline_color,
                            tags="handle",
                        )
                        # SO (Sudoeste)
                        canvas.create_rectangle(
                            canvas_x1 - handle_size,
                            canvas_y2 - handle_size,
                            canvas_x1 + handle_size,
                            canvas_y2 + handle_size,
                            fill=outline_color,
                            tags="handle",
                        )

                        # Desenhar alças nos lados
                        # Norte
                        canvas.create_rectangle(
                            mid_x - handle_size,
                            canvas_y1 - handle_size,
                            mid_x + handle_size,
                            canvas_y1 + handle_size,
                            fill=outline_color,
                            tags="handle",
                        )
                        # Leste
                        canvas.create_rectangle(
                            canvas_x2 - handle_size,
                            mid_y - handle_size,
                            canvas_x2 + handle_size,
                            mid_y + handle_size,
                            fill=outline_color,
                            tags="handle",
                        )
                        # Sul
                        canvas.create_rectangle(
                            mid_x - handle_size,
                            canvas_y2 - handle_size,
                            mid_x + handle_size,
                            canvas_y2 + handle_size,
                            fill=outline_color,
                            tags="handle",
                        )
                        # Oeste
                        canvas.create_rectangle(
                            canvas_x1 - handle_size,
                            mid_y - handle_size,
                            canvas_x1 + handle_size,
                            mid_y + handle_size,
                            fill=outline_color,
                            tags="handle",
                        )
            except Exception as e:
                logger.error(f"Erro ao redesenhar caixas: {e}")
                # Não definir window_closed aqui

        def on_mouse_down(event):
            """Função chamada quando o botão do mouse é pressionado."""
            # Verificar se a janela ainda é válida
            if not self._is_window_valid(canvas):
                return

            nonlocal start_x, start_y, current_rect, selected_box_idx

            try:
                # Modo de navegação: iniciar o pan
                if self.pan_mode:
                    canvas.scan_mark(event.x, event.y)
                    return

                # Limpar qualquer retângulo temporário existente
                if current_rect:
                    canvas.delete(current_rect)
                    current_rect = None

                # Obter coordenadas do canvas
                canvas_x = canvas.canvasx(event.x)
                canvas_y = canvas.canvasy(event.y)

                # Resetar o estado de resize
                self.resize_handle = HANDLE_NONE

                # Modo de edição
                if edit_mode:
                    # Verificar se clicou em uma alça de redimensionamento
                    if selected_box_idx is not None:
                        self.resize_handle = self._detect_resize_handle(canvas_x, canvas_y, selected_box_idx)
                        if self.resize_handle != HANDLE_NONE:
                            # Salvar posição inicial para histórico
                            start_x, start_y = canvas_x, canvas_y

                            if selected_box_idx < len(self.bounding_boxes):
                                self.original_box_state = tuple(self.bounding_boxes[selected_box_idx])
                                update_status(f"Redimensionando caixa {selected_box_idx + 1}")
                            return

                    # Procurar se clicou em uma caixa para selecionar
                    found_box = False
                    for i, (_, x1, y1, x2, y2) in enumerate(self.bounding_boxes):
                        # Converter para coordenadas do canvas
                        canvas_x1 = x1 * self.display_scale * self.scale_factor
                        canvas_y1 = y1 * self.display_scale * self.scale_factor
                        canvas_x2 = x2 * self.display_scale * self.scale_factor
                        canvas_y2 = y2 * self.display_scale * self.scale_factor

                        # Verificar se o clique está dentro da caixa
                        if canvas_x1 <= canvas_x <= canvas_x2 and canvas_y1 <= canvas_y <= canvas_y2:
                            selected_box_idx = i
                            start_x, start_y = canvas_x, canvas_y
                            self.original_box_state = tuple(self.bounding_boxes[selected_box_idx])
                            update_status(f"Caixa {i + 1} selecionada para edição")
                            redraw_all_boxes(highlight_idx=selected_box_idx)
                            found_box = True
                            break

                    # Se não selecionou nenhuma caixa, desselecionar
                    if not found_box:
                        selected_box_idx = None
                        redraw_all_boxes()
                        # Importante: ainda salvar as coordenadas iniciais mesmo no modo de edição
                        start_x, start_y = canvas_x, canvas_y
                else:
                    # Modo de desenho normal - salvar posição inicial
                    start_x, start_y = canvas_x, canvas_y

                # CRUCIAL: Garantir que window_closed está como False
                reset_window_closed()
            except Exception as e:
                logger.error(f"Erro em on_mouse_down: {e}")
                # Não definir window_closed aqui

        def on_mouse_move(event):
            """Função chamada quando o mouse é movido com o botão pressionado."""
            # Verificar se a janela ainda é válida
            if not self._is_window_valid(canvas):
                return

            nonlocal start_x, start_y, current_rect, selected_box_idx

            try:
                # Pan mode
                if self.pan_mode:
                    canvas.scan_dragto(event.x, event.y, gain=1)
                    return

                # Precisamos ter uma posição inicial
                if start_x is None or start_y is None:
                    return

                # Obter coordenadas do canvas
                canvas_x = canvas.canvasx(event.x)
                canvas_y = canvas.canvasy(event.y)

                # Modo de edição com caixa selecionada
                if edit_mode and selected_box_idx is not None:
                    # Obter caixa atual
                    cls_id, x1, y1, x2, y2 = self.bounding_boxes[selected_box_idx]

                    # Converter diferença para coordenadas originais
                    orig_dx = (canvas_x - start_x) / (self.display_scale * self.scale_factor)
                    orig_dy = (canvas_y - start_y) / (self.display_scale * self.scale_factor)

                    # Redimensionamento
                    if self.resize_handle != HANDLE_NONE:
                        # Atualizar coordenadas baseado na alça selecionada
                        if self.resize_handle == HANDLE_NW:
                            x1 += orig_dx
                            y1 += orig_dy
                        elif self.resize_handle == HANDLE_NE:
                            x2 += orig_dx
                            y1 += orig_dy
                        elif self.resize_handle == HANDLE_SE:
                            x2 += orig_dx
                            y2 += orig_dy
                        elif self.resize_handle == HANDLE_SW:
                            x1 += orig_dx
                            y2 += orig_dy
                        elif self.resize_handle == HANDLE_N:
                            y1 += orig_dy
                        elif self.resize_handle == HANDLE_E:
                            x2 += orig_dx
                        elif self.resize_handle == HANDLE_S:
                            y2 += orig_dy
                        elif self.resize_handle == HANDLE_W:
                            x1 += orig_dx
                    else:
                        # Movimentação normal
                        x1 += orig_dx
                        y1 += orig_dy
                        x2 += orig_dx
                        y2 += orig_dy

                    # Garantir que x1 < x2 e y1 < y2
                    if x1 > x2:
                        x1, x2 = x2, x1
                    if y1 > y2:
                        y1, y2 = y2, y1

                    # Garantir limites da imagem
                    x1 = max(0, min(x1, self.original_w))
                    y1 = max(0, min(y1, self.original_h))
                    x2 = max(0, min(x2, self.original_w))
                    y2 = max(0, min(y2, self.original_h))

                    # Atualizar a caixa
                    self.bounding_boxes[selected_box_idx] = (cls_id, x1, y1, x2, y2)

                    # Atualizar posição inicial
                    start_x, start_y = canvas_x, canvas_y

                    # Redesenhar
                    redraw_all_boxes(highlight_idx=selected_box_idx)
                else:
                    # Desenhar retângulo temporário
                    if current_rect:
                        canvas.delete(current_rect)
                    current_rect = canvas.create_rectangle(
                        start_x, start_y, canvas_x, canvas_y,
                        outline="green", width=2
                    )

                # CRUCIAL: Garantir que window_closed está como False
                reset_window_closed()
            except Exception as e:
                logger.error(f"Erro em on_mouse_move: {e}")
                # Não definir window_closed aqui

        def on_mouse_up(event):
            """Função chamada quando o botão do mouse é solto."""
            # Verificar se a janela ainda é válida
            if not self._is_window_valid(canvas):
                return

            nonlocal start_x, start_y, current_rect, selected_box_idx

            try:
                # Verificações iniciais
                if self.pan_mode:
                    return

                # Precisamos ter uma posição inicial
                if start_x is None or start_y is None:
                    return

                # Obter coordenadas do canvas
                canvas_x = canvas.canvasx(event.x)
                canvas_y = canvas.canvasy(event.y)

                # CASO 1: Modo de edição com uma caixa selecionada
                if edit_mode and selected_box_idx is not None:
                    # Finalizar redimensionamento ou movimentação
                    if self.resize_handle != HANDLE_NONE:
                        # Registrar ação no histórico
                        if self.original_box_state:
                            current_box = tuple(self.bounding_boxes[selected_box_idx])
                            self._add_to_history(
                                "resize",
                                {"index": selected_box_idx, "before": self.original_box_state, "after": current_box}
                            )
                        update_status(f"Caixa {selected_box_idx + 1} redimensionada")
                        self.resize_handle = HANDLE_NONE
                    else:
                        # Foi movimento simples
                        if self.original_box_state:
                            current_box = tuple(self.bounding_boxes[selected_box_idx])
                            self._add_to_history(
                                "move",
                                {"index": selected_box_idx, "before": self.original_box_state, "after": current_box}
                            )
                        update_status(f"Caixa {selected_box_idx + 1} reposicionada")

                    # Reset estado para novas ações
                    self.original_box_state = None
                # CASO 2: Modo de desenho ou edição sem caixa selecionada - criar nova caixa
                elif abs(start_x - canvas_x) > 5 and abs(start_y - canvas_y) > 5:
                    # Converter para coordenadas originais
                    x1 = min(start_x, canvas_x) / (self.display_scale * self.scale_factor)
                    y1 = min(start_y, canvas_y) / (self.display_scale * self.scale_factor)
                    x2 = max(start_x, canvas_x) / (self.display_scale * self.scale_factor)
                    y2 = max(start_y, canvas_y) / (self.display_scale * self.scale_factor)

                    # Garantir limites da imagem
                    x1 = max(0, min(x1, self.original_w))
                    y1 = max(0, min(y1, self.original_h))
                    x2 = max(0, min(x2, self.original_w))
                    y2 = max(0, min(y2, self.original_h))

                    # Obter índice da classe
                    current_class_str = class_var.get()
                    class_id = current_class_str.split("-")[0]

                    # Adicionar à lista de bounding boxes
                    self.bounding_boxes.append((class_id, int(x1), int(y1), int(x2), int(y2)))

                    # Adicionar ao histórico
                    self._add_to_history("add", {"index": len(self.bounding_boxes) - 1})

                    # Atualizar status
                    update_status(f"Box adicionada: {current_class_str}")

                    # Auto-save se necessário
                    if self.auto_save:
                        if self._check_auto_save(self.bounding_boxes, output_dir, base_name):
                            update_status("Auto-save realizado")

                # Limpar o retângulo temporário
                if current_rect:
                    canvas.delete(current_rect)
                    current_rect = None

                # Redesenhar todas as caixas
                redraw_all_boxes(highlight_idx=selected_box_idx if edit_mode else None)

                # CRUCIAL: Redefinir os pontos iniciais para permitir novas boxes
                start_x = None
                start_y = None

                # CRUCIAL: Garantir que window_closed está como False
                reset_window_closed()
            except Exception as e:
                logger.error(f"Erro em on_mouse_up: {e}")
                # Não definir window_closed aqui

        def toggle_edit_mode():
            """Alterna entre os modos de edição e desenho."""
            # Verificar se a janela ainda é válida
            if not self._is_window_valid(canvas):
                return

            nonlocal edit_mode, selected_box_idx, start_x, start_y, current_rect

            edit_mode = not edit_mode
            self.pan_mode = False  # Desativar navegação ao ativar edição

            # Resetar estado para novas ações
            selected_box_idx = None
            self.resize_handle = HANDLE_NONE

            # Limpar qualquer retângulo temporário
            if current_rect:
                canvas.delete(current_rect)
                current_rect = None

            # Redefinir pontos iniciais
            start_x = None
            start_y = None

            try:
                # Atualizar a aparência do botão
                edit_button.config(
                    text="Modo Desenho (E)" if edit_mode else "Modo Edição (E)",
                    bg="lightblue" if edit_mode else "#f0f0f0"
                )

                update_status()
                redraw_all_boxes()
            except Exception as e:
                logger.error(f"Erro ao alternar modo de edição: {e}")
                # Não definir window_closed aqui

            # CRUCIAL: Garantir que window_closed está como False
            reset_window_closed()

        def toggle_pan_mode():
            """Alterna entre o modo de navegação e desenho/edição."""
            # Verificar se a janela ainda é válida
            if not self._is_window_valid(canvas):
                return

            nonlocal edit_mode

            self.pan_mode = not self.pan_mode

            if self.pan_mode:
                edit_mode = False  # Desativar edição ao ativar navegação

            try:
                # Atualizar a aparência do botão
                pan_button.config(
                    text="Modo Desenho (P)" if self.pan_mode else "Modo Navegação (P)",
                    bg="lightblue" if self.pan_mode else "#f0f0f0"
                )

                update_status()
            except Exception as e:
                logger.error(f"Erro ao alternar modo de navegação: {e}")
                # Não definir window_closed aqui

            # CRUCIAL: Garantir que window_closed está como False
            reset_window_closed()

        def undo():
            """Desfaz a última ação."""
            if not self._is_window_valid(canvas):
                return

            if not self.action_history:
                update_status("Nada para desfazer.")
                return

            try:
                last_action = self.action_history.pop()
                action_type = last_action.get("type")
                data = last_action.get("data", {})

                if action_type == "add":
                    if data.get("index") < len(self.bounding_boxes):
                        self.bounding_boxes.pop(data.get("index"))
                        update_status("Desfez: Adição de caixa")
                elif action_type == "move" or action_type == "resize":
                    if data.get("index") < len(self.bounding_boxes):
                        self.bounding_boxes[data.get("index")] = data.get("before")
                        update_status(f"Desfez: {'Movimentação' if action_type == 'move' else 'Redimensionamento'} de caixa")
                elif action_type == "delete":
                    self.bounding_boxes.insert(data.get("index"), data.get("box"))
                    update_status("Desfez: Exclusão de caixa")

                redraw_all_boxes(highlight_idx=selected_box_idx if edit_mode else None)

                # CRUCIAL: Garantir que window_closed está como False
                reset_window_closed()
            except Exception as e:
                logger.error(f"Erro ao desfazer ação: {e}")
                # Não definir window_closed aqui

        def delete_selected():
            """Remove a caixa selecionada ou a última caixa."""
            if not self._is_window_valid(canvas):
                return

            nonlocal selected_box_idx

            try:
                # Remover caixa selecionada ou a última
                if edit_mode and selected_box_idx is not None:
                    # Guardar para histórico
                    removed_box = self.bounding_boxes[selected_box_idx]
                    removed_index = selected_box_idx
                    self._add_to_history("delete", {"index": removed_index, "box": removed_box})

                    # Remover caixa
                    self.bounding_boxes.pop(selected_box_idx)
                    update_status(f"Caixa {selected_box_idx + 1} excluída")

                    # Resetar seleção
                    selected_box_idx = None
                elif self.bounding_boxes:
                    # Remover última caixa
                    removed_box = self.bounding_boxes[-1]
                    removed_index = len(self.bounding_boxes) - 1
                    self._add_to_history("delete", {"index": removed_index, "box": removed_box})

                    # Remover caixa
                    self.bounding_boxes.pop()
                    update_status(f"Última caixa excluída. Restantes: {len(self.bounding_boxes)}")
                else:
                    update_status("Nenhuma caixa para excluir")
                    return

                # Redesenhar
                redraw_all_boxes(highlight_idx=selected_box_idx if edit_mode else None)

                # CRUCIAL: Garantir que window_closed está como False
                reset_window_closed()
            except Exception as e:
                logger.error(f"Erro ao excluir caixa: {e}")
                # Não definir window_closed aqui

        def reset():
            """Remove todas as caixas."""
            if not self._is_window_valid(canvas):
                return

            if not self.bounding_boxes:
                update_status("Nenhuma caixa para limpar.")
                return

            try:
                # Confirmar reset
                if not messagebox.askyesno("Confirmação", "Tem certeza que deseja remover TODAS as caixas?"):
                    return

                # Guardar todas para histórico
                for i, box in enumerate(self.bounding_boxes.copy()):
                    self._add_to_history("delete", {"index": i, "box": box})

                # Limpar lista
                self.bounding_boxes.clear()

                # Atualizar interface
                nonlocal selected_box_idx
                selected_box_idx = None
                redraw_all_boxes()
                update_status("Todas as caixas foram removidas.")

                # CRUCIAL: Garantir que window_closed está como False
                reset_window_closed()
            except Exception as e:
                logger.error(f"Erro ao resetar anotações: {e}")
                # Não definir window_closed aqui

        def save():
            """Salva as anotações."""
            if not self._is_window_valid(canvas):
                return

            nonlocal annotation_path

            try:
                annotation_path = self._save_annotations(self.bounding_boxes, output_dir, base_name)
                update_status(f"Anotações salvas em {annotation_path}")
                self.last_save_time = time.time()  # Atualizar timestamp de último salvamento

                # CRUCIAL: Garantir que window_closed está como False
                reset_window_closed()
            except Exception as e:
                logger.error(f"Erro ao salvar anotações: {e}")
                # Não definir window_closed aqui

        def save_and_exit():
            """Salva as anotações e sai."""
            if not self._is_window_valid(canvas):
                return

            try:
                save()
                self.user_cancelled = True
                root.destroy()
            except Exception as e:
                logger.error(f"Erro ao salvar e sair: {e}")
                self.window_closed = True
                self.user_cancelled = True
                try:
                    root.destroy()
                except:
                    pass

        def on_closing():
            """Manipula o evento de fechamento da janela."""
            try:
                if len(self.bounding_boxes) > 0:
                    if messagebox.askyesno("Sair", "Deseja salvar as anotações antes de sair?"):
                        save()
            except:
                pass  # Ignorar erros durante o fechamento

            # Definir flags de saída
            self.window_closed = True
            self.user_cancelled = True

            # Fechar a janela
            try:
                root.destroy()
            except:
                pass  # Ignorar erros durante a destruição da janela

        def cycle_classes():
            """Alterna entre as classes disponíveis."""
            if not self._is_window_valid(canvas):
                return

            try:
                current_idx = self.classes.index(class_var.get()) if class_var.get() in self.classes else 0
                next_idx = (current_idx + 1) % len(self.classes)
                class_var.set(self.classes[next_idx])

                # CRUCIAL: Garantir que window_closed está como False
                reset_window_closed()
            except Exception as e:
                logger.error(f"Erro ao alternar classes: {e}")
                # Não definir window_closed aqui

        def select_none():
            """Desseleciona qualquer caixa selecionada."""
            if not self._is_window_valid(canvas):
                return

            nonlocal selected_box_idx

            try:
                selected_box_idx = None
                redraw_all_boxes()
                update_status()

                # CRUCIAL: Garantir que window_closed está como False
                reset_window_closed()
            except Exception as e:
                logger.error(f"Erro ao desselecionar caixa: {e}")
                # Não definir window_closed aqui

        def zoom(event):
            """Manipula eventos de zoom com a roda do mouse."""
            if not self._is_window_valid(canvas):
                return

            try:
                # Calcular o novo fator de escala
                old_scale = self.scale_factor
                if event.delta > 0 or event.num == 4:  # Zoom in
                    self.scale_factor *= 1.1
                elif event.delta < 0 or event.num == 5:  # Zoom out
                    self.scale_factor /= 1.1

                # Limitar zoom
                self.scale_factor = min(max(0.5, self.scale_factor), 5.0)

                # Aplicar zoom apenas se houve alteração
                if old_scale != self.scale_factor:
                    # Redimensionar a imagem
                    self._redraw_with_zoom(img_display, canvas)
                    # Redesenhar as caixas com o novo zoom
                    redraw_all_boxes(highlight_idx=selected_box_idx if edit_mode else None)

                # CRUCIAL: Garantir que window_closed está como False
                reset_window_closed()
            except Exception as e:
                logger.error(f"Erro ao aplicar zoom: {e}")
                # Não definir window_closed aqui

        def start_pan(event):
            """Inicia o movimento de arrastar."""
            if not self._is_window_valid(canvas):
                return

            try:
                canvas.scan_mark(event.x, event.y)

                # CRUCIAL: Garantir que window_closed está como False
                reset_window_closed()
            except Exception as e:
                logger.error(f"Erro ao iniciar pan: {e}")
                # Não definir window_closed aqui

        def do_pan(event):
            """Executa o movimento de arrastar."""
            if not self._is_window_valid(canvas):
                return

            try:
                canvas.scan_dragto(event.x, event.y, gain=1)

                # CRUCIAL: Garantir que window_closed está como False
                reset_window_closed()
            except Exception as e:
                logger.error(f"Erro ao realizar pan: {e}")
                # Não definir window_closed aqui

        def reset_zoom():
            """Reinicia o zoom para escala normal."""
            if not self._is_window_valid(canvas):
                return

            try:
                self.scale_factor = 1.0
                self._redraw_with_zoom(img_display, canvas)
                redraw_all_boxes(highlight_idx=selected_box_idx if edit_mode else None)
                update_status("Zoom reiniciado")

                # CRUCIAL: Garantir que window_closed está como False
                reset_window_closed()
            except Exception as e:
                logger.error(f"Erro ao reiniciar zoom: {e}")
                # Não definir window_closed aqui

        def monitor_window_state():
            """Monitora periodicamente o estado da janela e corrige se necessário."""
            try:
                if self.window_closed and root.winfo_exists():
                    print("ALERTA: Detectada inconsistência - window_closed é True, mas a janela existe!")
                    self.window_closed = False

                # Continuar monitorando se a janela ainda existir
                if root.winfo_exists():
                    root.after(1000, monitor_window_state)  # Verificar a cada segundo
            except:
                # Se falhar, a janela provavelmente já foi fechada
                self.window_closed = True

        # Bindings para zoom e pan
        canvas.bind("<MouseWheel>", zoom)  # Windows
        canvas.bind("<Button-4>", zoom)    # Linux: scroll up
        canvas.bind("<Button-5>", zoom)    # Linux: scroll down

        # Pan com botão do meio e direito
        canvas.bind("<ButtonPress-2>", start_pan)
        canvas.bind("<B2-Motion>", do_pan)
        canvas.bind("<ButtonPress-3>", start_pan)
        canvas.bind("<B3-Motion>", do_pan)

        # Eventos de mouse principais
        canvas.bind("<ButtonPress-1>", on_mouse_down)
        canvas.bind("<B1-Motion>", on_mouse_move)
        canvas.bind("<ButtonRelease-1>", on_mouse_up)

        # Trackpad com dois dedos (se suportado)
        try:
            canvas.bind("<TouchpadPan>", do_pan)
        except:
            pass  # Ignorar se o evento não for suportado

        # Rastreamento da classe selecionada
        class_var.trace("w", lambda *args: set_current_class())

        # Botões - Primeira linha
        button_frame = tk.Frame(main_frame)
        button_frame.pack(fill=tk.X)

        tk.Button(button_frame, text="Reiniciar (R)", command=reset).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Desfazer (Z)", command=undo).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Salvar (S)", command=save).pack(side=tk.LEFT, padx=5)
        edit_button = tk.Button(button_frame, text="Modo Edição (E)", command=toggle_edit_mode)
        edit_button.pack(side=tk.LEFT, padx=5)
        pan_button = tk.Button(button_frame, text="Modo Navegação (P)", command=toggle_pan_mode)
        pan_button.pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Reset Zoom (W)", command=reset_zoom).pack(side=tk.LEFT, padx=5)

        # Segunda linha de botões
        button_frame2 = tk.Frame(main_frame)
        button_frame2.pack(fill=tk.X)

        tk.Button(button_frame2, text="Alternar Classe (C)", command=cycle_classes).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame2, text="Sair (Q)", command=on_closing).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame2, text="Salvar e Sair (X)", command=save_and_exit).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame2, text="Excluir Seleção (Del)", command=delete_selected).pack(side=tk.LEFT, padx=5)

        # Adicionar informações de atalhos
        shortcuts_frame = tk.Frame(main_frame)
        shortcuts_frame.pack(fill=tk.X, pady=5)

        shortcuts_label = tk.Label(
            shortcuts_frame,
            text="Atalhos: "
            + ", ".join([f"{k}={v}" for k, v in KEYBOARD_SHORTCUTS.items()])
            + "\nNo modo Edição: Arraste as alças para redimensionar caixas, clique e arraste no centro para mover",
            justify=tk.LEFT,
            anchor=tk.W,
            wraplength=780,
        )
        shortcuts_label.pack(fill=tk.X, padx=5)

        # Vincular atalhos de teclado
        root.bind("<r>", lambda e: reset())
        root.bind("<z>", lambda e: undo())
        root.bind("<s>", lambda e: save())
        root.bind("<q>", lambda e: on_closing())
        root.bind("<e>", lambda e: toggle_edit_mode())
        root.bind("<p>", lambda e: toggle_pan_mode())
        root.bind("<c>", lambda e: cycle_classes())
        root.bind("<x>", lambda e: save_and_exit())
        root.bind("<Delete>", lambda e: delete_selected())
        root.bind("<Escape>", lambda e: select_none())
        root.bind("<w>", lambda e: reset_zoom())

        # Protocolo para fechar janela
        root.protocol("WM_DELETE_WINDOW", on_closing)

        # Centralizar janela na tela
        root.update_idletasks()
        width = root.winfo_width()
        height = root.winfo_height()
        x = (root.winfo_screenwidth() // 2) - (width // 2)
        y = (root.winfo_screenheight() // 2) - (height // 2)
        root.geometry("{}x{}+{}+{}".format(width, height, x, y))

        # Desenhar as bounding boxes existentes
        redraw_all_boxes()

        # Iniciar o monitoramento do estado da janela
        root.after(1000, monitor_window_state)

        # Auto-save timer
        if self.auto_save:
            def check_auto_save():
                if self.window_closed:
                    return
                if self._check_auto_save(self.bounding_boxes, output_dir, base_name):
                    update_status("Auto-save realizado")
                try:
                    root.after(10000, check_auto_save)  # Verificar a cada 10 segundos
                except tk.TclError:
                    pass  # Janela fechada

            # Iniciar o timer de auto-save
            root.after(10000, check_auto_save)

        # Iniciar loop principal
        root.mainloop()

        return annotation_path

    def _save_progress(self, progress_path: str, current_image: str) -> None:
        """
        Salva o progresso atual da anotação.

        Args:
            progress_path: Caminho para o arquivo de progresso
            current_image: Caminho da imagem atual
        """
        try:
            progress_data = {
                "last_annotated": current_image,
                "timestamp": datetime.now().isoformat(),
            }

            with open(progress_path, "w") as f:
                json.dump(progress_data, f)

        except Exception as e:
            logger.warning(f"Não foi possível salvar o progresso: {str(e)}")

    def backup_annotations(self, label_dir: str) -> Optional[str]:
        """
        Cria um backup com timestamp das anotações atuais e mantém apenas os 5 mais recentes.

        Args:
            label_dir: Diretório contendo os arquivos de anotação

        Returns:
            Caminho para o diretório de backup ou None se falhar
        """
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        parent_dir = os.path.dirname(f"{label_dir}/backups")
        backup_dir = os.path.join(parent_dir, f"backup_annotations_{timestamp}")

        try:
            if os.path.exists(label_dir):
                os.makedirs(backup_dir, exist_ok=True)
                count = 0

                for file in glob.glob(os.path.join(label_dir, "*.txt")):
                    if os.path.basename(file) != self.progress_file:
                        shutil.copy2(file, backup_dir)
                        count += 1

                if count > 0:
                    logger.info(f"Backup criado em {backup_dir} com {count} arquivos de anotação")

                    # Limitar para manter apenas os 5 backups mais recentes
                    # Encontrar diretórios de backup existentes
                    backup_pattern = re.compile(r"backup_annotations_\d{8}_\d{6}$")
                    backup_dirs = []

                    for dirname in os.listdir(parent_dir):
                        dir_path = os.path.join(parent_dir, dirname)
                        if os.path.isdir(dir_path) and backup_pattern.match(dirname):
                            backup_dirs.append(dir_path)

                    # Ordenar por timestamp no nome (mais recentes primeiro)
                    backup_dirs.sort(reverse=True)

                    # Manter apenas os 5 mais recentes, excluir os demais
                    if len(backup_dirs) > 5:
                        for old_backup in backup_dirs[5:]:
                            try:
                                shutil.rmtree(old_backup)
                                logger.info(f"Removido backup antigo: {os.path.basename(old_backup)}")
                            except Exception as e:
                                logger.warning(
                                    f"Não foi possível remover backup antigo {os.path.basename(old_backup)}: {str(e)}"
                                )

                    return backup_dir
                else:
                    os.rmdir(backup_dir)
                    logger.info("Nenhum arquivo de anotação encontrado para backup")

        except Exception as e:
            logger.error(f"Erro ao criar backup: {str(e)}")

        return None

    def batch_annotate(self, image_dir: str, output_dir: str) -> Tuple[int, int]:
        """
        Anota uma pasta de imagens em lote.

        Args:
            image_dir: Diretório contendo imagens para anotação
            output_dir: Diretório para salvar as anotações

        Returns:
            Tupla com (total de imagens, total de imagens anotadas)
        """
        os.makedirs(output_dir, exist_ok=True)

        # Obter todos os arquivos de imagem
        image_files = []
        for ext in ["*.jpg", "*.jpeg", "*.png"]:
            image_files.extend(glob.glob(os.path.join(image_dir, ext)))

        if not image_files:
            logger.warning(f"Nenhum arquivo de imagem encontrado em {image_dir}")
            return 0, 0

        # Ordenar imagens para consistência
        image_files.sort()

        # Criar backup antes de iniciar a anotação
        self.backup_annotations(output_dir)

        # Verificar se há progresso salvo
        progress_path = os.path.join(output_dir, self.progress_file)
        start_index = 0
        total_annotated = 0
        imagens_existentes = 0

        if os.path.exists(progress_path):
            try:
                with open(progress_path, "r") as f:
                    progress_data = json.load(f)

                last_annotated = progress_data.get("last_annotated", "")
                if last_annotated in image_files:
                    last_index = image_files.index(last_annotated)

                    # Mostrar informações sobre o progresso
                    logger.info(f"Anotação anterior encontrada. Última imagem anotada: {os.path.basename(last_annotated)}")

                    if last_index < len(image_files) - 1:
                        # Perguntar onde o usuário quer começar
                        print("\nOpções:")
                        print("1. Continuar de onde parou (próxima imagem)")
                        print("2. Recomeçar do início")
                        print("3. Revisar a última imagem anotada")

                        opcao = input("\nEscolha uma opção (1, 2 ou 3) [1]: ").strip()

                        if opcao == "2":
                            # Recomeçar do início
                            start_index = 0
                            logger.info("Reiniciando anotação do início.")
                        elif opcao == "3":
                            # Revisar a última imagem
                            start_index = last_index
                            logger.info(f"Revisando a última imagem anotada: {os.path.basename(last_annotated)}")
                        else:
                            # Opção padrão: continuar da próxima
                            start_index = last_index + 1
                            next_image = os.path.basename(image_files[start_index])
                            logger.info(f"Continuando anotação a partir de: {next_image}")
                    else:
                        logger.info("Todas as imagens já foram anotadas. Reiniciando do início.")
                        start_index = 0
            except Exception as e:
                logger.warning(f"Erro ao carregar progresso: {str(e)}")
                logger.info("Iniciando anotação do início.")

        # Contar anotações já existentes antes do ponto de retomada
        for i in range(start_index):
            img_path = image_files[i]
            base_name = os.path.splitext(os.path.basename(img_path))[0]
            existing_annotation = os.path.join(output_dir, f"{base_name}.txt")
            if os.path.exists(existing_annotation):
                imagens_existentes += 1

        # Processar imagens a partir do ponto de retomada
        for i in range(start_index, len(image_files)):
            img_path = image_files[i]
            base_name = os.path.splitext(os.path.basename(img_path))[0]
            existing_annotation = os.path.join(output_dir, f"{base_name}.txt")

            logger.info(f"Anotando: {os.path.basename(img_path)} ({i + 1}/{len(image_files)})")

            # Verificar se já existe anotação
            if os.path.exists(existing_annotation):
                print(f"\nA imagem '{os.path.basename(img_path)}' já possui anotação.")
                print("Opções:")
                print("p - Pular esta imagem (manter anotação existente)")
                print("e - Editar a anotação existente")
                print("s - Sobrescrever (criar nova anotação)")

                should_skip = input("\nO que deseja fazer? (p/e/s) [e]: ").lower() or "e"

                if should_skip == "p":
                    logger.info(f"Mantendo anotação existente para {base_name}")
                    imagens_existentes += 1

                    # Salvar progresso após cada imagem
                    self._save_progress(progress_path, img_path)
                    continue
                elif should_skip == "e":
                    logger.info(f"Editando anotação existente para {base_name}")
                else:
                    logger.info(f"Sobrescrevendo anotação existente para {base_name}")

            # Resetar window_closed antes de anotar cada imagem
            self.window_closed = False

            # Anotar imagem
            annotation_path = self.annotate_image(img_path, output_dir)

            # Verificar se o usuário cancelou
            if self.user_cancelled:  # Confiar na flag user_cancelled
                logger.info("Anotação cancelada pelo usuário. Encerrando processo.")
                break  # Interrompe todo o processo

            # Se tiver salvo, conta como anotado
            if annotation_path:
                total_annotated += 1
                logger.info(f"Anotação salva para {os.path.basename(img_path)}")

            # Salvar progresso após cada imagem
            self._save_progress(progress_path, img_path)

        # Exibir resumo final
        print("\n" + "=" * 50)
        print("RESUMO DA ANOTAÇÃO:")
        print(f"Total de imagens: {len(image_files)}")
        print(f"Imagens anotadas: {total_annotated + imagens_existentes}")
        print(f"Imagens anotadas nesta sessão: {total_annotated}")
        print(f"Imagens restantes: {len(image_files) - (total_annotated + imagens_existentes)}")
        print("=" * 50)

        return len(image_files), total_annotated + imagens_existentes