"""
Módulo para anotação manual de imagens.
"""

import glob
import logging
import os
import time
import tkinter as tk
from tkinter import messagebox  # Importação explícita do messagebox
from datetime import datetime
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
    "z": "Desfazer última anotação",
    "r": "Reiniciar anotações",
    "e": "Mover/editar seleção",
    "c": "Alternar entre classes",
    "q": "Sair sem salvar",
    "Del": "Excluir seleção",
    "Esc": "Cancelar seleção atual"
}

DEFAULT_AUTO_SAVE = True
DEFAULT_AUTO_SAVE_INTERVAL = 300  # 5 minutos


class ImageAnnotator:
    """
    Ferramenta para anotação manual de imagens de microorganismos.
    """

    def __init__(
        self,
        classes: List[str] = None,
        auto_save: bool = DEFAULT_AUTO_SAVE,
        auto_save_interval: int = DEFAULT_AUTO_SAVE_INTERVAL
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

    def _setup_zoom_pan(self, canvas, img_display):
        """
        Configura funcionalidades de zoom e pan para o canvas.

        Args:
            canvas: Canvas do Tkinter onde a imagem é exibida
            img_display: Imagem exibida
        """
        self.scale_factor = 1.0
        self.canvas = canvas

        def zoom(event):
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
                self._redraw_with_zoom(img_display)
                redraw_all_boxes()

        def start_pan(event):
            canvas.scan_mark(event.x, event.y)

        def do_pan(event):
            canvas.scan_dragto(event.x, event.y, gain=1)

        # Bindings para zoom e pan
        canvas.bind("<MouseWheel>", zoom)  # Windows
        canvas.bind("<Button-4>", zoom)    # Linux: scroll up
        canvas.bind("<Button-5>", zoom)    # Linux: scroll down
        canvas.bind("<ButtonPress-2>", start_pan)  # Botão do meio para pan
        canvas.bind("<B2-Motion>", do_pan)

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
        - Pressione 's' para salvar e ir para a próxima imagem
        - Pressione 'z' para excluir a última caixa (antes era 'd')
        - Pressione 'e' para sair e salvar progresso
        - Use scroll do mouse para zoom
        - Botão do meio para arrastar (pan)
        - 'c' para alternar entre classes
        - 'a' para anterior, 'd' para próxima (conforme documentação)

        Args:
            image_path: Caminho para a imagem a ser anotada
            output_dir: Diretório para salvar as anotações

        Returns:
            Caminho para o arquivo de anotação criado ou None se cancelado
        """
        # Assegurar que o diretório de saída existe
        os.makedirs(output_dir, exist_ok=True)

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
        bounding_boxes = []

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
                        bounding_boxes.append((class_id, x1, y1, x2, y2))

        # Variáveis para a sessão de anotação atual
        start_x = None
        start_y = None
        current_rect = None
        selected_box_idx = None

        # Classe padrão
        current_class = self.classes[0] if self.classes else "0-levedura"

        # Modo de edição
        edit_mode = False

        # Flag para controlar se a janela já foi destruída
        window_closed = False

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
            text=f"Contagem: {len(bounding_boxes)} | Desenhe clicando e arrastando",
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
            yscrollcommand=v_scrollbar.set
        )
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        h_scrollbar.config(command=canvas.xview)
        v_scrollbar.config(command=canvas.yview)

        # Criar imagem no canvas
        canvas.create_image(0, 0, anchor=tk.NW, image=img_tk, tags="background")
        canvas.config(scrollregion=canvas.bbox(tk.ALL))

        # Configurar zoom e pan
        self.scale_factor = 1.0

        # Resultado da anotação
        annotation_path = None
        exit_requested = False

        def set_current_class(event=None):
            nonlocal current_class
            current_class = class_var.get()
            update_status()

        def update_status(msg=None):
            nonlocal window_closed
            if window_closed:
                return

            status_text = msg if msg else f"Classe: {current_class} | Contagem: {len(bounding_boxes)}"
            if edit_mode:
                status_text += " | MODO EDIÇÃO: Selecione uma caixa para mover"
            else:
                status_text += " | Desenhe clicando e arrastando"

            try:
                status_label.config(text=status_text)
            except tk.TclError:
                window_closed = True

        def on_mouse_down(event):
            nonlocal start_x, start_y, current_rect, selected_box_idx
            if window_closed:
                return

            canvas_x = canvas.canvasx(event.x)
            canvas_y = canvas.canvasy(event.y)

            if edit_mode:
                # Em modo de edição, procurar por uma caixa para selecionar
                selected_box_idx = None

                # Obter todas as coordenadas das caixas em coordenadas do canvas (considerando zoom)
                for i, (_, x1, y1, x2, y2) in enumerate(bounding_boxes):
                    # Converter coordenadas absolutas da imagem para coordenadas do canvas
                    canvas_x1 = x1 * self.display_scale * self.scale_factor
                    canvas_y1 = y1 * self.display_scale * self.scale_factor
                    canvas_x2 = x2 * self.display_scale * self.scale_factor
                    canvas_y2 = y2 * self.display_scale * self.scale_factor

                    # Verificar se o clique está dentro da caixa
                    if canvas_x1 <= canvas_x <= canvas_x2 and canvas_y1 <= canvas_y <= canvas_y2:
                        selected_box_idx = i
                        start_x, start_y = canvas_x, canvas_y
                        update_status(f"Caixa {i+1} selecionada para edição")
                        redraw_all_boxes(highlight_idx=selected_box_idx)
                        break
            else:
                # Em modo de desenho normal
                start_x, start_y = canvas_x, canvas_y

        def on_mouse_move(event):
            nonlocal start_x, start_y, current_rect, selected_box_idx
            if window_closed:
                return

            if start_x is None or start_y is None:
                return

            canvas_x = canvas.canvasx(event.x)
            canvas_y = canvas.canvasy(event.y)

            if edit_mode and selected_box_idx is not None:
                # Modo de edição: mover a caixa selecionada
                dx = canvas_x - start_x
                dy = canvas_y - start_y

                # Atualizar a posição inicial para o próximo movimento
                start_x, start_y = canvas_x, canvas_y

                # Obter a caixa selecionada
                cls_id, x1, y1, x2, y2 = bounding_boxes[selected_box_idx]

                # Converter o deslocamento para coordenadas originais da imagem
                orig_dx = dx / (self.display_scale * self.scale_factor)
                orig_dy = dy / (self.display_scale * self.scale_factor)

                # Mover a caixa
                x1 += orig_dx
                y1 += orig_dy
                x2 += orig_dx
                y2 += orig_dy

                # Atualizar a caixa na lista
                bounding_boxes[selected_box_idx] = (cls_id, x1, y1, x2, y2)

                # Redesenhar todas as caixas
                redraw_all_boxes(highlight_idx=selected_box_idx)
            elif not edit_mode:
                # Modo de desenho: criar ou atualizar o retângulo atual
                if current_rect:
                    canvas.delete(current_rect)
                current_rect = canvas.create_rectangle(
                    start_x, start_y, canvas_x, canvas_y, outline="green", width=2
                )

        def on_mouse_up(event):
            nonlocal start_x, start_y, current_rect, selected_box_idx
            if window_closed:
                return

            if start_x is None or start_y is None:
                return

            canvas_x = canvas.canvasx(event.x)
            canvas_y = canvas.canvasy(event.y)

            if edit_mode:
                # Em modo de edição, finalizar a movimentação da caixa
                if selected_box_idx is not None:
                    update_status(f"Caixa {selected_box_idx+1} reposicionada")
                    selected_box_idx = None
            else:
                # Em modo de desenho, finalizar a caixa
                # Converter coordenadas para a escala original
                orig_start_x = start_x / (self.display_scale * self.scale_factor)
                orig_start_y = start_y / (self.display_scale * self.scale_factor)
                orig_end_x = canvas_x / (self.display_scale * self.scale_factor)
                orig_end_y = canvas_y / (self.display_scale * self.scale_factor)

                # Verificar se a caixa tem um tamanho mínimo
                min_size = 5 / (self.display_scale * self.scale_factor)
                if abs(orig_end_x - orig_start_x) > min_size and abs(orig_end_y - orig_start_y) > min_size:
                    # Obter coordenadas em ordem (x1 < x2, y1 < y2)
                    x1 = min(orig_start_x, orig_end_x)
                    y1 = min(orig_start_y, orig_end_y)
                    x2 = max(orig_start_x, orig_end_x)
                    y2 = max(orig_start_y, orig_end_y)

                    # Garantir que as coordenadas estão dentro dos limites da imagem
                    x1 = max(0, min(x1, w))
                    y1 = max(0, min(y1, h))
                    x2 = max(0, min(x2, w))
                    y2 = max(0, min(y2, h))

                    # Obter índice da classe
                    class_id = current_class.split("-")[0]

                    # Adicionar à lista de bounding boxes
                    bounding_boxes.append((class_id, int(x1), int(y1), int(x2), int(y2)))

                    # Verificar auto-save
                    auto_saved = self._check_auto_save(bounding_boxes, output_dir, base_name)
                    if auto_saved:
                        update_status(f"Auto-save: {len(bounding_boxes)} caixas salvas")

                    # Redesenhar todas as caixas
                    redraw_all_boxes()

                # Limpar o retângulo atual
                if current_rect:
                    canvas.delete(current_rect)

            # Reiniciar o rastreamento
            start_x, start_y = None, None
            current_rect = None

        def toggle_edit_mode():
            nonlocal edit_mode, selected_box_idx
            if window_closed:
                return

            edit_mode = not edit_mode
            selected_box_idx = None

            # Atualizar o texto do botão
            try:
                if edit_mode:
                    edit_button.config(text="Modo Desenho (E)")
                    update_status("Modo de edição ativado. Selecione uma caixa para mover.")
                else:
                    edit_button.config(text="Modo Edição (E)")
                    update_status("Modo de desenho ativado.")
            except tk.TclError:
                window_closed = True
                return

            redraw_all_boxes()

        def delete_last():
            if window_closed:
                return

            if bounding_boxes:
                bounding_boxes.pop()
                redraw_all_boxes()
                update_status(f"Última caixa excluída. Restantes: {len(bounding_boxes)}")

        def redraw_all_boxes(highlight_idx=None):
            if window_closed:
                return

            try:
                # Remover todos os retângulos e rótulos existentes
                canvas.delete("box")
                canvas.delete("label")

                # Redesenhar as caixas
                for i, (class_id, x1, y1, x2, y2) in enumerate(bounding_boxes):
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
                    canvas.create_rectangle(
                        canvas_x1, canvas_y1, canvas_x2, canvas_y2,
                        outline=outline_color,
                        width=outline_width,
                        tags="box"
                    )

                    # Desenhar rótulo
                    canvas.create_text(
                        canvas_x1, canvas_y1 - 5,
                        text=f"{class_name} #{i + 1}",
                        anchor=tk.SW,
                        fill=outline_color,
                        font=("Arial", 10, "bold"),
                        tags="label"
                    )
            except tk.TclError:
                global window_closed
                window_closed = True

        def reset():
            if window_closed:
                return

            bounding_boxes.clear()
            redraw_all_boxes()
            update_status(f"Todas as caixas limpas")

        def safe_destroy():
            nonlocal window_closed
            if not window_closed:
                try:
                    root.destroy()
                    window_closed = True
                except tk.TclError:
                    window_closed = True

        def save():
            nonlocal annotation_path, window_closed
            annotation_path = self._save_annotations(bounding_boxes, output_dir, base_name)
            safe_destroy()

        def on_closing():
            nonlocal exit_requested, window_closed

            if window_closed:
                return

            # Perguntar ao usuário se quer salvar antes de sair
            try:
                if len(bounding_boxes) > 0:
                    save_before_exit = messagebox.askyesno(
                        "Sair", "Deseja salvar as anotações antes de sair?"
                    )
                    if save_before_exit:
                        save()
                        return  # Já destruímos a janela em save()
            except tk.TclError:
                window_closed = True
                exit_requested = True
                return

            exit_requested = True
            safe_destroy()

        def exit_and_save():
            nonlocal exit_requested
            if window_closed:
                return

            if len(bounding_boxes) > 0:
                save()
            else:
                exit_requested = True
                safe_destroy()

        def cycle_classes(event=None):
            if window_closed:
                return

            self._cycle_class_selection(class_var)
            set_current_class()

        # Configurar zoom e pan
        def zoom(event):
            if window_closed:
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
                    redraw_all_boxes()
                except tk.TclError:
                    nonlocal window_closed
                    window_closed = True

        def start_pan(event):
            if window_closed:
                return
            canvas.scan_mark(event.x, event.y)

        def do_pan(event):
            if window_closed:
                return
            canvas.scan_dragto(event.x, event.y, gain=1)

        # Bindings para zoom e pan
        canvas.bind("<MouseWheel>", zoom)  # Windows
        canvas.bind("<Button-4>", zoom)    # Linux: scroll up
        canvas.bind("<Button-5>", zoom)    # Linux: scroll down
        canvas.bind("<ButtonPress-2>", start_pan)  # Botão do meio para pan
        canvas.bind("<B2-Motion>", do_pan)

        # Rastreamento da classe selecionada
        class_var.trace("w", lambda *args: set_current_class())

        # Botões
        button_frame = tk.Frame(main_frame)
        button_frame.pack(fill=tk.X)

        # Primeira linha de botões
        tk.Button(button_frame, text="Reiniciar (R)", command=reset).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Desfazer (Z)", command=delete_last).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Salvar (S)", command=save).pack(side=tk.LEFT, padx=5)
        edit_button = tk.Button(button_frame, text="Modo Edição (E)", command=toggle_edit_mode)
        edit_button.pack(side=tk.LEFT, padx=5)

        # Segunda linha de botões
        button_frame2 = tk.Frame(main_frame)
        button_frame2.pack(fill=tk.X)

        tk.Button(button_frame2, text="Alternar Classe (C)", command=cycle_classes).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame2, text="Sair (Q)", command=on_closing).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame2, text="Salvar e Sair (E)", command=exit_and_save).pack(side=tk.LEFT, padx=5)

        # Adicionar informações de atalhos
        shortcuts_frame = tk.Frame(main_frame)
        shortcuts_frame.pack(fill=tk.X, pady=5)

        shortcuts_label = tk.Label(
            shortcuts_frame,
            text="Atalhos: " + ", ".join([f"{k}={v}" for k, v in KEYBOARD_SHORTCUTS.items()]),
            justify=tk.LEFT,
            anchor=tk.W,
            wraplength=780
        )
        shortcuts_label.pack(fill=tk.X, padx=5)

        # Vincular eventos
        canvas.bind("<ButtonPress-1>", on_mouse_down)
        canvas.bind("<B1-Motion>", on_mouse_move)
        canvas.bind("<ButtonRelease-1>", on_mouse_up)

        # Vincular atalhos de teclado
        root.bind("<r>", lambda e: reset())
        root.bind("<z>", lambda e: delete_last())
        root.bind("<s>", lambda e: save())
        root.bind("<q>", lambda e: on_closing())
        root.bind("<e>", lambda e: toggle_edit_mode())
        root.bind("<c>", lambda e: cycle_classes())
        root.bind("<Delete>", lambda e: delete_last())
        root.bind("<Escape>", lambda e: select_none())

        # Protocolo para fechar janela
        root.protocol("WM_DELETE_WINDOW", on_closing)

        # Selecionar nenhuma caixa
        def select_none():
            nonlocal selected_box_idx
            if window_closed:
                return

            selected_box_idx = None
            redraw_all_boxes()
            update_status()

        # Centralizar janela na tela
        root.update_idletasks()
        width = root.winfo_width()
        height = root.winfo_height()
        x = (root.winfo_screenwidth() // 2) - (width // 2)
        y = (root.winfo_screenheight() // 2) - (height // 2)
        root.geometry("{}x{}+{}+{}".format(width, height, x, y))

        # Desenhar as bounding boxes existentes
        if bounding_boxes:
            redraw_all_boxes()

        # Iniciar loop principal
        root.mainloop()

        # Se o usuário solicitou sair, retorne None para interromper o batch_annotate
        if exit_requested:
            return None

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

            if annotation_path:
                total_annotated += 1
                logger.info(f"Anotação salva para {os.path.basename(img_path)}")

                # Salvar progresso após cada imagem
                self._save_progress(progress_path, img_path)
            else:
                logger.info("Anotação cancelada pelo usuário. Progresso salvo.")
                break

        # Exibir resumo final
        print("\n" + "="*50)
        print("RESUMO DA ANOTAÇÃO:")
        print(f"Total de imagens: {len(image_files)}")
        print(f"Imagens anotadas: {total_annotated + imagens_existentes}")
        print(f"Imagens anotadas nesta sessão: {total_annotated}")
        print(f"Imagens restantes: {len(image_files) - (total_annotated + imagens_existentes)}")
        print("="*50)

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
        Cria um backup com timestamp das anotações atuais.

        Args:
            label_dir: Diretório contendo os arquivos de anotação

        Returns:
            Caminho para o diretório de backup ou None se falhar
        """
        import time
        import shutil

        timestamp = time.strftime("%Y%m%d_%H%M%S")
        backup_dir = os.path.join(os.path.dirname(label_dir), f"backup_annotations_{timestamp}")

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
                    return backup_dir
                else:
                    os.rmdir(backup_dir)
                    logger.info("Nenhum arquivo de anotação encontrado para backup")
        except Exception as e:
            logger.error(f"Erro ao criar backup: {str(e)}")

        return None