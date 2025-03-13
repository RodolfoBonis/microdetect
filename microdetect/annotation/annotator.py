"""
Módulo para anotação manual de imagens.
"""

import glob
import logging
import os
import time
import tkinter as tk
from datetime import datetime
from tkinter import messagebox  # Importação explícita do messagebox
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

# Constantes para identificar alças de redimensionamento
HANDLE_NONE = 0
HANDLE_NW = 1  # Noroeste (canto superior esquerdo)
HANDLE_NE = 2  # Nordeste (canto superior direito)
HANDLE_SE = 3  # Sudeste (canto inferior direito)
HANDLE_SW = 4  # Sudoeste (canto inferior esquerdo)
HANDLE_N = 5  # Norte (meio superior)
HANDLE_E = 6  # Leste (meio direito)
HANDLE_S = 7  # Sul (meio inferior)
HANDLE_W = 8  # Oeste (meio esquerdo)


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
        self.canvas = None
        self.current_img_tk = None

        # Atributos para controle de estado
        self.window_closed = False
        self.bounding_boxes = []
        self.pan_mode = False
        self.user_cancelled = False  # Flag para indicar se o usuário cancelou explicitamente o processo

        # Novos atributos para histórico e redimensionamento
        self.action_history = []  # Lista para armazenar o histórico de ações
        self.max_history = 50  # Limitar o tamanho do histórico
        self.resize_handle = HANDLE_NONE  # Para controlar qual alça de redimensionamento está ativa
        self.handle_size = 6  # Tamanho das alças de redimensionamento
        self.original_box_state = None  # Para armazenar estado original de uma caixa antes de mover/redimensionar

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
        # Limitar o tamanho do histórico
        if len(self.action_history) >= self.max_history:
            self.action_history.pop(0)

        self.action_history.append({"type": action_type, "data": data})

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

    def _redraw_all_boxes(self, highlight_idx=None):
        """
        Redesenha todas as caixas delimitadoras no canvas com
        opcional destaque para a caixa selecionada.

        Args:
            highlight_idx: Índice da caixa a ser destacada (opcional)
        """
        if self.window_closed:
            return

        try:
            # Remover todos os retângulos, rótulos e alças existentes
            self.canvas.delete("box")
            self.canvas.delete("label")
            self.canvas.delete("handle")

            # Se não houver bounding_boxes, estamos provavelmente em outro contexto
            if not self.bounding_boxes:
                return

            # Redesenhar as caixas
            for i, (class_id, x1, y1, x2, y2) in enumerate(self.bounding_boxes):
                # Converter coordenadas absolutas da imagem para coordenadas do canvas
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
                self.canvas.create_rectangle(
                    canvas_x1, canvas_y1, canvas_x2, canvas_y2, outline=outline_color, width=outline_width, tags="box"
                )

                # Desenhar rótulo
                self.canvas.create_text(
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
                    self.canvas.create_rectangle(
                        canvas_x1 - handle_size,
                        canvas_y1 - handle_size,
                        canvas_x1 + handle_size,
                        canvas_y1 + handle_size,
                        fill=outline_color,
                        tags="handle",
                    )
                    # NE (Nordeste)
                    self.canvas.create_rectangle(
                        canvas_x2 - handle_size,
                        canvas_y1 - handle_size,
                        canvas_x2 + handle_size,
                        canvas_y1 + handle_size,
                        fill=outline_color,
                        tags="handle",
                    )
                    # SE (Sudeste)
                    self.canvas.create_rectangle(
                        canvas_x2 - handle_size,
                        canvas_y2 - handle_size,
                        canvas_x2 + handle_size,
                        canvas_y2 + handle_size,
                        fill=outline_color,
                        tags="handle",
                    )
                    # SO (Sudoeste)
                    self.canvas.create_rectangle(
                        canvas_x1 - handle_size,
                        canvas_y2 - handle_size,
                        canvas_x1 + handle_size,
                        canvas_y2 + handle_size,
                        fill=outline_color,
                        tags="handle",
                    )

                    # Desenhar alças nos lados
                    # Norte
                    self.canvas.create_rectangle(
                        mid_x - handle_size,
                        canvas_y1 - handle_size,
                        mid_x + handle_size,
                        canvas_y1 + handle_size,
                        fill=outline_color,
                        tags="handle",
                    )
                    # Leste
                    self.canvas.create_rectangle(
                        canvas_x2 - handle_size,
                        mid_y - handle_size,
                        canvas_x2 + handle_size,
                        mid_y + handle_size,
                        fill=outline_color,
                        tags="handle",
                    )
                    # Sul
                    self.canvas.create_rectangle(
                        mid_x - handle_size,
                        canvas_y2 - handle_size,
                        mid_x + handle_size,
                        canvas_y2 + handle_size,
                        fill=outline_color,
                        tags="handle",
                    )
                    # Oeste
                    self.canvas.create_rectangle(
                        canvas_x1 - handle_size,
                        mid_y - handle_size,
                        canvas_x1 + handle_size,
                        mid_y + handle_size,
                        fill=outline_color,
                        tags="handle",
                    )
        except tk.TclError:
            self.window_closed = True

    def _redraw_with_zoom(self, img_display):
        """
        Redesenha a imagem com o zoom atual.

        Args:
            img_display: Imagem original para exibição
        """
        # Calcular novas dimensões
        new_w = int(self.display_w * self.scale_factor)
        new_h = int(self.display_h * self.scale_factor)

        # Redimensionar imagem
        img_resized = cv2.resize(img_display, (new_w, new_h))
        self.current_img_tk = ImageTk.PhotoImage(Image.fromarray(img_resized))

        # Atualizar imagem no canvas
        self.canvas.delete("background")
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.current_img_tk, tags="background")
        self.canvas.config(scrollregion=self.canvas.bbox(tk.ALL))

    def _cycle_class_selection(self, class_var):
        """
        Alterna entre as classes disponíveis.

        Args:
            class_var: Variável Tkinter que armazena a classe atual
        """
        current_class = class_var.get()
        idx = self.classes.index(current_class) if current_class in self.classes else 0
        next_idx = (idx + 1) % len(self.classes)
        class_var.set(self.classes[next_idx])

    def annotate_image(self, image_path: str, output_dir: str) -> Optional[str]:
        """
        Ferramenta para anotar manualmente células de levedura em imagens de microscopia com bounding boxes.
        Instruções:
        - Clique e arraste para desenhar bounding boxes
        - Selecione uma classe antes de desenhar cada caixa
        - Pressione 'r' para reiniciar
        - Pressione 'q' para sair sem salvar
        - Pressione 's' para salvar
        - Pressione 'z' para desfazer a última ação
        - Pressione 'e' para alternar modo edição
        - Pressione 'p' para alternar modo navegação
        - Pressione 'x' para salvar e sair
        - Use scroll do mouse para zoom
        - Navegue pela imagem usando trackpad, botão direito ou modo navegação
        - 'c' para alternar entre classes

        Args:
            image_path: Caminho para a imagem a ser anotada
            output_dir: Diretório para salvar as anotações

        Returns:
            Caminho para o arquivo de anotação criado ou None se cancelado
        """
        # Assegurar que o diretório de saída existe
        os.makedirs(output_dir, exist_ok=True)

        # Resetar flag de cancelamento do usuário
        self.user_cancelled = False

        # Limpar histórico de ações
        self.action_history = []
        self.resize_handle = HANDLE_NONE
        self.original_box_state = None

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

        # Armazenar bounding boxes como (class_id, x1, y1, x2, y2) em coordenadas da imagem original
        self.bounding_boxes = []

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
        start_x = None
        start_y = None
        current_rect = None
        selected_box_idx = None

        # Classe padrão
        current_class = self.classes[0] if self.classes else "0-levedura"

        # Modo de edição
        edit_mode = False
        self.pan_mode = False

        # Flag para controlar se a janela já foi destruída
        self.window_closed = False

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

        # Converter para PhotoImage para o Tkinter
        img_tk = ImageTk.PhotoImage(Image.fromarray(img_display))

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

        # Criar imagem no canvas
        canvas.create_image(0, 0, anchor=tk.NW, image=img_tk, tags="background")
        canvas.config(scrollregion=canvas.bbox(tk.ALL))

        # Configurar zoom e pan
        self.canvas = canvas
        self.scale_factor = 1.0

        # Resultado da anotação
        annotation_path = None

        def set_current_class(event=None):
            nonlocal current_class
            current_class = class_var.get()
            update_status()

        def update_status(msg=None):
            if self.window_closed:
                return

            status_text = msg if msg else f"Classe: {current_class} | Contagem: {len(self.bounding_boxes)}"
            if edit_mode:
                status_text += " | MODO EDIÇÃO: Selecione uma caixa para mover/redimensionar"
            elif self.pan_mode:
                status_text += " | MODO NAVEGAÇÃO: Arraste para movimentar a imagem"
            else:
                status_text += " | Desenhe clicando e arrastando"

            try:
                status_label.config(text=status_text)
                # Atualizar também o botão de navegação
                if self.pan_mode:
                    pan_button.config(text="Modo Desenho (P)", bg="lightblue")
                else:
                    pan_button.config(text="Modo Navegação (P)", bg="SystemButtonFace")
            except tk.TclError:
                self.window_closed = True

        def on_mouse_down(event):
            nonlocal start_x, start_y, current_rect, selected_box_idx
            if self.window_closed:
                return

            # Em modo de navegação, iniciar o pan
            if self.pan_mode:
                canvas.scan_mark(event.x, event.y)
                return

            canvas_x = canvas.canvasx(event.x)
            canvas_y = canvas.canvasy(event.y)

            if edit_mode:
                # Em modo de edição, verificar primeiro se clicou em uma alça de redimensionamento
                if selected_box_idx is not None:
                    self.resize_handle = self._detect_resize_handle(canvas_x, canvas_y, selected_box_idx)
                    if self.resize_handle != HANDLE_NONE:
                        # Salvamos o estado original para o histórico
                        start_x, start_y = canvas_x, canvas_y
                        # Guardar estado original para histórico
                        if selected_box_idx < len(self.bounding_boxes):
                            # MUDANÇA: Usar tuple() em vez de .copy() para tuplas
                            self.original_box_state = tuple(self.bounding_boxes[selected_box_idx])
                            update_status(f"Redimensionando caixa {selected_box_idx + 1}")
                        return

                # Se não clicou em uma alça, procurar por uma caixa para selecionar
                selected_box_idx = None

                # Obter todas as coordenadas das caixas em coordenadas do canvas (considerando zoom)
                for i, (_, x1, y1, x2, y2) in enumerate(self.bounding_boxes):
                    # Converter coordenadas absolutas da imagem para coordenadas do canvas
                    canvas_x1 = x1 * self.display_scale * self.scale_factor
                    canvas_y1 = y1 * self.display_scale * self.scale_factor
                    canvas_x2 = x2 * self.display_scale * self.scale_factor
                    canvas_y2 = y2 * self.display_scale * self.scale_factor

                    # Verificar se o clique está dentro da caixa
                    if canvas_x1 <= canvas_x <= canvas_x2 and canvas_y1 <= canvas_y <= canvas_y2:
                        selected_box_idx = i
                        start_x, start_y = canvas_x, canvas_y

                        # Guardar estado original para histórico
                        # MUDANÇA: Usar tuple() em vez de .copy() para tuplas
                        self.original_box_state = tuple(self.bounding_boxes[selected_box_idx])

                        update_status(f"Caixa {i + 1} selecionada para edição")
                        self._redraw_all_boxes(highlight_idx=selected_box_idx)
                        break
            else:
                # Em modo de desenho normal
                start_x, start_y = canvas_x, canvas_y

        def on_mouse_move(event):
            nonlocal start_x, start_y, current_rect, selected_box_idx
            if self.window_closed:
                return

            # Em modo de navegação, mover o canvas
            if self.pan_mode:
                canvas.scan_dragto(event.x, event.y, gain=1)
                return

            if start_x is None or start_y is None:
                return

            canvas_x = canvas.canvasx(event.x)
            canvas_y = canvas.canvasy(event.y)

            if edit_mode and selected_box_idx is not None:
                # Verificar se estamos redimensionando
                if self.resize_handle != HANDLE_NONE:
                    # Obter caixa atual
                    cls_id, x1, y1, x2, y2 = self.bounding_boxes[selected_box_idx]

                    # Calcular diferença em coordenadas originais
                    orig_dx = (canvas_x - start_x) / (self.display_scale * self.scale_factor)
                    orig_dy = (canvas_y - start_y) / (self.display_scale * self.scale_factor)

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

                    # Garantir que x1 < x2 e y1 < y2
                    if x1 > x2:
                        x1, x2 = x2, x1
                        # Atualizar handle para o canto oposto se necessário
                        if self.resize_handle == HANDLE_NW:
                            self.resize_handle = HANDLE_NE
                        elif self.resize_handle == HANDLE_NE:
                            self.resize_handle = HANDLE_NW
                        elif self.resize_handle == HANDLE_SE:
                            self.resize_handle = HANDLE_SW
                        elif self.resize_handle == HANDLE_SW:
                            self.resize_handle = HANDLE_SE

                    if y1 > y2:
                        y1, y2 = y2, y1
                        # Atualizar handle para o canto oposto se necessário
                        if self.resize_handle == HANDLE_NW:
                            self.resize_handle = HANDLE_SW
                        elif self.resize_handle == HANDLE_NE:
                            self.resize_handle = HANDLE_SE
                        elif self.resize_handle == HANDLE_SE:
                            self.resize_handle = HANDLE_NE
                        elif self.resize_handle == HANDLE_SW:
                            self.resize_handle = HANDLE_NW

                    # Garantir que a caixa esteja dentro dos limites da imagem
                    x1 = max(0, min(x1, self.original_w))
                    y1 = max(0, min(y1, self.original_h))
                    x2 = max(0, min(x2, self.original_w))
                    y2 = max(0, min(y2, self.original_h))

                    # Atualizar a caixa
                    self.bounding_boxes[selected_box_idx] = (cls_id, x1, y1, x2, y2)

                    # Atualizar posição inicial para próximo movimento
                    start_x, start_y = canvas_x, canvas_y

                    # Redesenhar
                    self._redraw_all_boxes(highlight_idx=selected_box_idx)
                else:
                    # Modo de edição normal: mover a caixa selecionada
                    dx = canvas_x - start_x
                    dy = canvas_y - start_y

                    # Atualizar a posição inicial para o próximo movimento
                    start_x, start_y = canvas_x, canvas_y

                    # Obter a caixa selecionada
                    cls_id, x1, y1, x2, y2 = self.bounding_boxes[selected_box_idx]

                    # Converter o deslocamento para coordenadas originais da imagem
                    orig_dx = dx / (self.display_scale * self.scale_factor)
                    orig_dy = dy / (self.display_scale * self.scale_factor)

                    # Mover a caixa
                    x1 += orig_dx
                    y1 += orig_dy
                    x2 += orig_dx
                    y2 += orig_dy

                    # Garantir que a caixa esteja dentro dos limites da imagem
                    x1 = max(0, min(x1, self.original_w))
                    y1 = max(0, min(y1, self.original_h))
                    x2 = max(0, min(x2, self.original_w))
                    y2 = max(0, min(y2, self.original_h))

                    # Atualizar a caixa na lista
                    self.bounding_boxes[selected_box_idx] = (cls_id, x1, y1, x2, y2)

                    # Redesenhar todas as caixas
                    self._redraw_all_boxes(highlight_idx=selected_box_idx)
            elif not edit_mode:
                # Modo de desenho: criar ou atualizar o retângulo atual
                if current_rect:
                    canvas.delete(current_rect)
                current_rect = canvas.create_rectangle(start_x, start_y, canvas_x, canvas_y, outline="green", width=2)

        def on_mouse_up(event):
            nonlocal start_x, start_y, current_rect, selected_box_idx
            if self.window_closed or self.pan_mode:
                return

            if start_x is None or start_y is None:
                return

            canvas_x = canvas.canvasx(event.x)
            canvas_y = canvas.canvasy(event.y)

            if edit_mode:
                # Em modo de edição, finalizar a movimentação ou redimensionamento
                if selected_box_idx is not None:
                    # Se foi redimensionamento
                    if self.resize_handle != HANDLE_NONE:
                        # Registrar ação no histórico
                        if self.original_box_state:
                            # MUDANÇA: Usar tuple() em vez de .copy() para tuplas
                            current_box = tuple(self.bounding_boxes[selected_box_idx])
                            self._add_to_history(
                                "resize", {"index": selected_box_idx, "before": self.original_box_state, "after": current_box}
                            )

                        update_status(f"Caixa {selected_box_idx + 1} redimensionada")
                        self.resize_handle = HANDLE_NONE
                    else:
                        # Foi movimento simples
                        if self.original_box_state:
                            # MUDANÇA: Usar tuple() em vez de .copy() para tuplas
                            current_box = tuple(self.bounding_boxes[selected_box_idx])
                            self._add_to_history(
                                "move", {"index": selected_box_idx, "before": self.original_box_state, "after": current_box}
                            )

                        update_status(f"Caixa {selected_box_idx + 1} reposicionada")

                    # Não resetar o selected_box_idx para permitir continuar editando
                    # Apenas resetamos state para novas ações
                    self.original_box_state = None

        def toggle_edit_mode():
            nonlocal edit_mode, selected_box_idx
            if self.window_closed:
                return

            edit_mode = not edit_mode
            self.pan_mode = False  # Desativar modo navegação ao ativar edição
            selected_box_idx = None
            self.resize_handle = HANDLE_NONE

            # Atualizar o texto do botão
            try:
                if edit_mode:
                    edit_button.config(text="Modo Desenho (E)")
                    update_status("Modo de edição ativado. Selecione uma caixa para mover/redimensionar.")
                else:
                    edit_button.config(text="Modo Edição (E)")
                    update_status("Modo de desenho ativado.")
            except tk.TclError:
                self.window_closed = True
                return

            self._redraw_all_boxes()

        def toggle_pan_mode():
            if self.window_closed:
                return

            self.pan_mode = not self.pan_mode
            nonlocal edit_mode
            if self.pan_mode:
                edit_mode = False  # Desativar edição ao ativar navegação
                edit_button.config(text="Modo Edição (E)")

            update_status()

        def undo():
            """
            Desfaz a última ação (adicionar, mover, redimensionar ou excluir).
            """
            if self.window_closed or not self.action_history:
                return

            # Obter última ação
            last_action = self.action_history.pop()
            action_type = last_action["type"]
            data = last_action["data"]

            # Processar baseado no tipo de ação
            if action_type == "add":
                # Remover a caixa adicionada
                if data["index"] < len(self.bounding_boxes):
                    self.bounding_boxes.pop(data["index"])
                    update_status("Desfez: Adição de caixa")

            elif action_type == "move" or action_type == "resize":
                # Restaurar caixa para posição original
                if data["index"] < len(self.bounding_boxes):
                    self.bounding_boxes[data["index"]] = data["before"]
                    update_status(f"Desfez: {'Movimentação' if action_type == 'move' else 'Redimensionamento'} de caixa")

            elif action_type == "delete":
                # Restaurar caixa excluída
                self.bounding_boxes.insert(data["index"], data["box"])
                update_status("Desfez: Exclusão de caixa")

            # Redesenhar todas as caixas
            self._redraw_all_boxes(highlight_idx=selected_box_idx)

        def delete_last():
            if self.window_closed:
                return

            if self.bounding_boxes:
                # Guardar a caixa antes de remover para o histórico
                removed_box = self.bounding_boxes[-1]  # Já é uma tupla, não precisa de .copy()
                removed_index = len(self.bounding_boxes) - 1

                self._add_to_history("delete", {"index": removed_index, "box": removed_box})

                self.bounding_boxes.pop()
                self._redraw_all_boxes()
                update_status(f"Última caixa excluída. Restantes: {len(self.bounding_boxes)}")

        def reset():
            if self.window_closed:
                return

            # Registrar todas as caixas no histórico antes de limpar
            for i, box in enumerate(self.bounding_boxes):
                self._add_to_history("delete", {"index": i, "box": box})

            self.bounding_boxes.clear()
            self._redraw_all_boxes()
            update_status(f"Todas as caixas limpas")

        def safe_destroy():
            if not self.window_closed:
                try:
                    root.destroy()
                    self.window_closed = True
                except tk.TclError:
                    self.window_closed = True

        def save():
            nonlocal annotation_path
            annotation_path = self._save_annotations(self.bounding_boxes, output_dir, base_name)
            # Sempre definir user_cancelled como True quando salvar ao sair
            self.user_cancelled = True
            safe_destroy()

        def on_closing():
            if self.window_closed:
                return

            # Perguntar ao usuário se quer salvar antes de sair
            try:
                if len(self.bounding_boxes) > 0:
                    save_before_exit = messagebox.askyesno("Sair", "Deseja salvar as anotações antes de sair?")
                    if save_before_exit:
                        save()  # Agora define self.user_cancelled = True e destroi a janela
                        return

                # Se não salvar ou não houver nada para salvar
                self.user_cancelled = True
                safe_destroy()
            except tk.TclError:
                self.window_closed = True
                self.user_cancelled = True
                return

        def exit_and_save():
            if self.window_closed:
                return

            # Sempre definir user_cancelled como True, independentemente de ter algo para salvar
            self.user_cancelled = True

            if len(self.bounding_boxes) > 0:
                save()  # Isso vai salvar e também definir user_cancelled = True
            else:
                safe_destroy()

        def cycle_classes(event=None):
            if self.window_closed:
                return

            self._cycle_class_selection(class_var)
            set_current_class()

        # Configurar zoom e pan
        def zoom(event):
            if self.window_closed:
                return

            # Determinar o ponto central do zoom (posição do mouse)
            x = canvas.canvasx(event.x)
            y = canvas.canvasy(event.y)

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
                new_w = int(self.display_w * self.scale_factor)
                new_h = int(self.display_h * self.scale_factor)
                img_resized = cv2.resize(img_display, (new_w, new_h))

                try:
                    # Atualizar a imagem no canvas
                    canvas.img_tk = ImageTk.PhotoImage(Image.fromarray(img_resized))
                    canvas.delete("background")
                    canvas.create_image(0, 0, anchor=tk.NW, image=canvas.img_tk, tags="background")
                    canvas.config(scrollregion=canvas.bbox(tk.ALL))

                    # Redesenhar as caixas com o novo zoom
                    self._redraw_all_boxes(highlight_idx=selected_box_idx)
                except tk.TclError:
                    self.window_closed = True

        def start_pan(event):
            if self.window_closed:
                return
            canvas.scan_mark(event.x, event.y)

        def do_pan(event):
            if self.window_closed:
                return
            canvas.scan_dragto(event.x, event.y, gain=1)

        # Bindings para zoom e pan
        canvas.bind("<MouseWheel>", zoom)  # Windows
        canvas.bind("<Button-4>", zoom)  # Linux: scroll up
        canvas.bind("<Button-5>", zoom)  # Linux: scroll down

        # Pan com botão do meio e direito
        canvas.bind("<ButtonPress-2>", start_pan)
        canvas.bind("<B2-Motion>", do_pan)

        canvas.bind("<ButtonPress-3>", start_pan)
        canvas.bind("<B3-Motion>", do_pan)

        # Suporte para trackpad em modo de navegação
        canvas.bind("<ButtonPress-1>", on_mouse_down)  # Também usado para pan quando self.pan_mode=True
        canvas.bind("<B1-Motion>", on_mouse_move)  # Também usado para pan quando self.pan_mode=True
        canvas.bind("<ButtonRelease-1>", on_mouse_up)

        # Trackpad com dois dedos (se suportado pelo sistema)
        try:
            # Tentar vincular eventos de trackpad específicos (funciona em alguns sistemas)
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

        # Segunda linha de botões
        button_frame2 = tk.Frame(main_frame)
        button_frame2.pack(fill=tk.X)

        tk.Button(button_frame2, text="Alternar Classe (C)", command=cycle_classes).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame2, text="Sair (Q)", command=on_closing).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame2, text="Salvar e Sair (X)", command=exit_and_save).pack(side=tk.LEFT, padx=5)

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
        root.bind("<x>", lambda e: exit_and_save())  # Atalho para salvar e sair
        root.bind("<Delete>", lambda e: delete_last())
        root.bind("<Escape>", lambda e: select_none())

        # Protocolo para fechar janela
        root.protocol("WM_DELETE_WINDOW", on_closing)

        # Selecionar nenhuma caixa
        def select_none():
            nonlocal selected_box_idx
            if self.window_closed:
                return

            selected_box_idx = None
            self._redraw_all_boxes()
            update_status()

        # Centralizar janela na tela
        root.update_idletasks()
        width = root.winfo_width()
        height = root.winfo_height()
        x = (root.winfo_screenwidth() // 2) - (width // 2)
        y = (root.winfo_screenheight() // 2) - (height // 2)
        root.geometry("{}x{}+{}+{}".format(width, height, x, y))

        # Desenhar as bounding boxes existentes
        if self.bounding_boxes:
            self._redraw_all_boxes()

        # Iniciar loop principal
        root.mainloop()

        # Se o usuário cancelou, retorne None para interromper o batch_annotate
        if self.user_cancelled:
            return annotation_path  # Retorna annotation_path mesmo se cancelado

        return annotation_path

    def batch_annotate(self, image_dir: str, output_dir: str) -> Tuple[int, int]:
        """
        Anota uma pasta de imagens em lote.

        Args:
            image_dir: Diretório contendo imagens para anotação
            output_dir: Diretório para salvar as anotações

        Returns:
            Tupla com (total de imagens, total de imagens anotadas)
        """
        import json
        import os.path as osp

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

    def _save_progress(self, progress_path: str, current_image: str) -> None:
        """
        Salva o progresso atual da anotação.

        Args:
            progress_path: Caminho para o arquivo de progresso
            current_image: Caminho da imagem atual
        """
        import json

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
        import os
        import re
        import shutil
        import time

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
