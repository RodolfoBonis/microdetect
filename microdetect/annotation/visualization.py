"""
Módulo para visualização de anotações em imagens.
"""

import glob
import logging
import os
import tkinter as tk
from tkinter import messagebox
from typing import Dict, List, Optional, Set, Tuple, Union

import cv2
import numpy as np
from PIL import Image, ImageTk

from microdetect.utils.config import config

logger = logging.getLogger(__name__)

# Constantes
DEFAULT_COLORS = {
    "0": (0, 255, 0),  # Verde para levedura
    "1": (0, 0, 255),  # Vermelho para fungo
    "2": (255, 0, 0),  # Azul para micro-alga
}

DEFAULT_BOX_THICKNESS = 2
DEFAULT_TEXT_SIZE = 0.5
DEFAULT_TEXT_THICKNESS = 1

# Atalhos de teclado para visualização
KEYBOARD_SHORTCUTS = {
    "a": "Imagem anterior",
    "d": "Próxima imagem",
    "p": "Ativar/desativar modo navegação",
    "r": "Reiniciar zoom e pan",
    "0-9": "Alternar visibilidade da classe",
    "s": "Salvar imagem atual",
    "q": "Sair",
    "e": "Alternar modo de edição",
}


class AnnotationVisualizer:
    """
    Classe para visualizar anotações de bounding boxes em imagens.
    """

    def __init__(
        self,
        class_map: Dict[str, str] = None,
        color_map: Dict[str, Tuple[int, int, int]] = None,
    ):
        """
        Inicializa o visualizador de anotações.

        Args:
            class_map: Mapeamento de IDs de classe para nomes (ex: {"0": "0-levedura"})
            color_map: Mapeamento de IDs de classe para cores RGB (ex: {"0": (0, 255, 0)})
        """
        classes = config.get("classes", ["0-levedura", "1-fungo", "2-micro-alga"])

        # Criar class_map a partir das classes se não fornecido
        if class_map is None:
            self.class_map = {}
            for cls in classes:
                parts = cls.split("-", 1)
                if len(parts) == 2:
                    self.class_map[parts[0]] = cls
        else:
            self.class_map = class_map

        # Usar color_map da configuração ou o padrão
        self.color_map = color_map or config.get("color_map", DEFAULT_COLORS)

        # Carregar configurações de visualização
        annotation_config = config.get("annotation", {})
        self.box_thickness = annotation_config.get("box_thickness", DEFAULT_BOX_THICKNESS)
        self.text_size = annotation_config.get("text_size", DEFAULT_TEXT_SIZE)
        self.text_thickness = annotation_config.get("text_thickness", DEFAULT_TEXT_THICKNESS)

        # Atributos para interface Tkinter
        self.window_closed = False
        self.current_img_tk = None
        self.canvas = None
        self.display_scale = 1.0
        self.scale_factor = 1.0
        self.display_w = 0
        self.display_h = 0
        self.original_w = 0
        self.original_h = 0
        self.pan_mode = False
        self.edit_mode = False

    def _load_image(self, img_path: str) -> Optional[np.ndarray]:
        """
        Carrega uma imagem com tratamento de erro adequado.

        Args:
            img_path: Caminho para a imagem

        Returns:
            Imagem carregada ou None em caso de erro
        """
        try:
            img = cv2.imread(img_path)
            if img is None:
                raise ValueError(f"Imagem não pôde ser carregada: {img_path}")
            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            return img_rgb
        except Exception as e:
            logger.error(f"Erro ao carregar imagem {img_path}: {str(e)}")
            return None

    def _process_annotation_line(self, ann: str, w: int, h: int, class_visibility: Dict[str, bool]) -> Optional[Dict]:
        """
        Processa uma linha de anotação e retorna dados da bounding box.

        Args:
            ann: Linha de anotação no formato YOLO
            w: Largura da imagem
            h: Altura da imagem
            class_visibility: Dicionário de visibilidade de classes

        Returns:
            Dicionário com informações da bounding box ou None se a anotação for inválida
        """
        parts = ann.strip().split()
        if len(parts) != 5:  # Formato YOLO: classe x_center y_center width height
            return None

        cls, x_center, y_center, box_w, box_h = parts

        # Pular se a classe for filtrada
        if not class_visibility.get(cls, True):
            return None

        # Converter coordenadas normalizadas para valores de pixel
        x_center = float(x_center) * w
        y_center = float(y_center) * h
        box_w = float(box_w) * w
        box_h = float(box_h) * h

        # Calcular pontos de canto
        x1 = int(x_center - box_w / 2)
        y1 = int(y_center - box_h / 2)
        x2 = int(x_center + box_w / 2)
        y2 = int(y_center + box_h / 2)

        # Obter nome da classe para exibição
        class_name = self.class_map.get(cls, f"Classe {cls}")

        return {
            "class_id": cls,
            "x1": x1,
            "y1": y1,
            "x2": x2,
            "y2": y2,
            "color": self.color_map.get(cls, (0, 255, 0)),
            "class_name": class_name,
        }

    def _redraw_all_boxes(self, canvas, annotations, w, h, class_visibility):
        """
        Redesenha todas as bounding boxes no canvas.

        Args:
            canvas: Canvas do Tkinter onde desenhar
            annotations: Lista de linhas de anotação
            w: Largura da imagem
            h: Altura da imagem
            class_visibility: Dicionário de visibilidade de classes
        """
        if self.window_closed:
            return

        # Remover todos os retângulos e rótulos existentes
        canvas.delete("box")
        canvas.delete("label")

        # Contar anotações visíveis para cada classe
        class_counts = {cls_id: 0 for cls_id in self.class_map.keys()}
        total_visible = 0

        # Redesenhar as caixas
        for box_idx, ann in enumerate(annotations):
            box_data = self._process_annotation_line(ann, w, h, class_visibility)
            if box_data is None:
                continue

            # Atualizar contagens
            cls = box_data["class_id"]
            class_counts[cls] = class_counts.get(cls, 0) + 1
            total_visible += 1

            # Converter coordenadas absolutas da imagem para coordenadas do canvas
            x1 = box_data["x1"] * self.display_scale * self.scale_factor
            y1 = box_data["y1"] * self.display_scale * self.scale_factor
            x2 = box_data["x2"] * self.display_scale * self.scale_factor
            y2 = box_data["y2"] * self.display_scale * self.scale_factor

            # Determinar cor
            color_rgb = box_data["color"]
            # Converter BGR para cores Tkinter no formato #RRGGBB
            r, g, b = color_rgb
            color_hex = f"#{r:02x}{g:02x}{b:02x}"

            # Desenhar retângulo
            canvas.create_rectangle(x1, y1, x2, y2, outline=color_hex, width=self.box_thickness, tags="box")

            # Desenhar rótulo
            canvas.create_text(
                x1,
                y1 - 5,
                text=f"{box_data['class_name']} #{box_idx + 1}",
                anchor=tk.SW,
                fill=color_hex,
                font=("Arial", 10, "bold"),
                tags="label",
            )

        return total_visible, class_counts

    def _redraw_with_zoom(self, img_display):
        """
        Redesenha a imagem com o zoom atual.

        Args:
            img_display: Imagem original para exibição
        """
        if self.window_closed:
            return

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

    def visualize_annotations(
        self,
        image_dir: str,
        label_dir: Optional[str] = None,
        output_dir: Optional[str] = None,
        filter_classes: Optional[Set[str]] = None,
    ) -> None:
        """
        Desenha bounding boxes em todas as imagens em um diretório e permite navegação entre elas
        usando uma interface Tkinter similar à ferramenta de anotação.

        Args:
            image_dir: Diretório contendo as imagens
            label_dir: Diretório contendo os arquivos de anotação (se None, procura no mesmo dir que as imagens)
            output_dir: Diretório para salvar imagens anotadas (se None, não salva)
            filter_classes: Conjunto de IDs de classe para exibir (se None, mostra todas as classes)
        """
        # Obter todos os arquivos de imagem
        image_files = []
        for ext in ["*.jpg", "*.jpeg", "*.png"]:
            image_files.extend(glob.glob(os.path.join(image_dir, ext)))

        if not image_files:
            logger.warning(f"Nenhum arquivo de imagem encontrado em {image_dir}")
            return

        # Ordenar imagens para consistência
        image_files.sort()

        current_idx = 0
        total_images = len(image_files)

        # Rastrear quais classes mostrar (inicializar todas como visíveis)
        class_visibility = {cls_id: True for cls_id in self.class_map.keys()}

        if filter_classes:
            # Inicializar apenas com classes especificadas visíveis
            class_visibility = {cls_id: (cls_id in filter_classes) for cls_id in self.class_map.keys()}

        # Resetar flags de controle
        self.window_closed = False
        self.pan_mode = False
        self.edit_mode = False

        # Carregar primeira imagem
        img_path = image_files[current_idx]
        img = self._load_image(img_path)
        if img is None:
            logger.error(f"Não foi possível carregar a primeira imagem: {img_path}")
            return

        # Obter dimensões da imagem
        h, w = img.shape[:2]
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

        # Criar janela Tkinter
        root = tk.Tk()
        root.title(f"Visualização: {os.path.basename(img_path)}")

        # Criar frame principal
        main_frame = tk.Frame(root)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Painel de informações de controle
        control_frame = tk.Frame(main_frame)
        control_frame.pack(side=tk.TOP, fill=tk.X)

        # Status label
        status_label = tk.Label(
            main_frame,
            text=f"Carregando...",
        )
        status_label.pack(side=tk.BOTTOM, fill=tk.X)

        # Informações da imagem
        info_label = tk.Label(
            main_frame,
            text=f"Imagem: {os.path.basename(img_path)} | Dimensões: {w}x{h}",
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
        self.current_img_tk = img_tk

        # Variáveis para controle de navegação e filtragem
        save_current = False
        annotations = []

        def update_status():
            """Atualiza o status na interface"""
            if self.window_closed:
                return

            mode_text = " | MODO NAVEGAÇÃO" if self.pan_mode else ""
            status_text = f"Imagem {current_idx + 1}/{total_images} | {len(annotations)} anotações{mode_text}"
            try:
                status_label.config(text=status_text)
                # Atualizar também o botão de navegação
                if self.pan_mode:
                    pan_button.config(text="Modo Visualização (P)", bg="lightblue")
                else:
                    pan_button.config(text="Modo Navegação (P)", bg="SystemButtonFace")
            except tk.TclError:
                self.window_closed = True

        def load_current_image():
            """Carrega e exibe a imagem atual"""
            nonlocal annotations, img, img_display, img_path

            if self.window_closed:
                return

            # Atualizar título e informação da imagem
            try:
                img_path = image_files[current_idx]
                root.title(f"Visualização: {os.path.basename(img_path)}")
                info_label.config(
                    text=f"Imagem: {os.path.basename(img_path)} | Dimensões: {self.original_w}x{self.original_h}"
                )
            except tk.TclError:
                self.window_closed = True
                return

            # Carregar a imagem atual
            img = self._load_image(img_path)
            if img is None:
                return

            h, w = img.shape[:2]
            self.original_w, self.original_h = w, h

            # Redimensionar para exibição
            scale = min(800 / w, 600 / h)
            if scale < 1:
                self.display_w, self.display_h = int(w * scale), int(h * scale)
                img_display = cv2.resize(img, (self.display_w, self.display_h))
                self.display_scale = scale
            else:
                self.display_w, self.display_h = w, h
                img_display = img.copy()
                self.display_scale = 1.0

            # Redefinir zoom
            self.scale_factor = 1.0

            # Atualizar a imagem no canvas
            self.current_img_tk = ImageTk.PhotoImage(Image.fromarray(img_display))
            canvas.delete("all")
            canvas.create_image(0, 0, anchor=tk.NW, image=self.current_img_tk, tags="background")
            canvas.config(scrollregion=canvas.bbox(tk.ALL))

            # Encontrar arquivo de anotação correspondente
            base_name = os.path.splitext(os.path.basename(img_path))[0]
            if label_dir:
                label_path = os.path.join(label_dir, f"{base_name}.txt")
            else:
                label_path = os.path.join(os.path.dirname(img_path), f"{base_name}.txt")

            # Carregar anotações
            annotations = []
            if os.path.exists(label_path):
                with open(label_path, "r") as f:
                    annotations = f.readlines()

            # Desenhar as caixas
            total_visible, class_counts = self._redraw_all_boxes(canvas, annotations, w, h, class_visibility)

            # Exibir informações das classes
            y_offset = 30
            for cls_id, cls_name in self.class_map.items():
                count = class_counts.get(cls_id, 0)
                bg_color = "lightgreen" if class_visibility.get(cls_id, True) else "lightgray"

                if not hasattr(root, "class_labels"):
                    root.class_labels = {}

                if cls_id in root.class_labels:
                    root.class_labels[cls_id].config(text=f"{cls_name}: {count}", bg=bg_color)
                else:
                    label = tk.Label(control_frame, text=f"{cls_name}: {count}", padx=5, pady=2, bg=bg_color, relief=tk.GROOVE)
                    label.pack(side=tk.LEFT, padx=2)
                    root.class_labels[cls_id] = label

                    # Adicionar bind de clique para alternar visibilidade
                    label.bind("<Button-1>", lambda e, id=cls_id: toggle_class_visibility(id))

            update_status()

        def next_image():
            """Carrega a próxima imagem"""
            nonlocal current_idx
            current_idx = (current_idx + 1) % total_images
            load_current_image()

        def prev_image():
            """Carrega a imagem anterior"""
            nonlocal current_idx
            current_idx = (current_idx - 1) % total_images
            load_current_image()

        def toggle_pan_mode():
            """Alterna entre modo de navegação e visualização"""
            self.pan_mode = not self.pan_mode
            update_status()

        def toggle_class_visibility(cls_id):
            """Alterna a visibilidade de uma classe"""
            class_visibility[cls_id] = not class_visibility[cls_id]

            # Atualizar visual do label
            if hasattr(root, "class_labels") and cls_id in root.class_labels:
                bg_color = "lightgreen" if class_visibility[cls_id] else "lightgray"
                root.class_labels[cls_id].config(bg=bg_color)

            # Redesenhar as caixas
            self._redraw_all_boxes(canvas, annotations, self.original_w, self.original_h, class_visibility)

        def save_image():
            """Salva a imagem atual com as anotações"""
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)

                # Criar imagem OpenCV a partir da original
                img_copy = img.copy()

                # Desenhar caixas na imagem
                for ann in annotations:
                    box_data = self._process_annotation_line(ann, self.original_w, self.original_h, class_visibility)
                    if box_data is None:
                        continue

                    x1, y1, x2, y2 = box_data["x1"], box_data["y1"], box_data["x2"], box_data["y2"]
                    color = box_data["color"]
                    class_name = box_data["class_name"]

                    # Desenhar retângulo
                    cv2.rectangle(img_copy, (x1, y1), (x2, y2), color, self.box_thickness)

                    # Adicionar nome da classe
                    cv2.putText(
                        img_copy,
                        class_name,
                        (x1, y1 - 5),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        self.text_size,
                        color,
                        self.text_thickness,
                        cv2.LINE_AA,
                    )

                # Converter de RGB para BGR para salvar corretamente
                img_copy = cv2.cvtColor(img_copy, cv2.COLOR_RGB2BGR)

                # Salvar imagem
                output_path = os.path.join(output_dir, f"annotated_{os.path.basename(img_path)}")
                cv2.imwrite(output_path, img_copy)
                messagebox.showinfo("Salvo", f"Imagem salva como:\n{output_path}")
                logger.info(f"Imagem anotada salva em {output_path}")
            else:
                messagebox.showwarning(
                    "Aviso", "Nenhum diretório de saída especificado.\nDefina um diretório de saída para salvar as imagens."
                )

        def reset_zoom():
            """Reseta zoom e posição da visualização"""
            self.scale_factor = 1.0
            self._redraw_with_zoom(img_display)
            self._redraw_all_boxes(canvas, annotations, self.original_w, self.original_h, class_visibility)

        def on_closing():
            """Manipula o fechamento da janela"""
            self.window_closed = True
            root.destroy()

        # Configurar zoom
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
                self._redraw_with_zoom(img_display)
                # Redesenhar as caixas
                self._redraw_all_boxes(canvas, annotations, self.original_w, self.original_h, class_visibility)

        # Funções para pan (arrastar visualização)
        def start_pan(event):
            if self.window_closed:
                return
            canvas.scan_mark(event.x, event.y)

        def do_pan(event):
            if self.window_closed:
                return
            canvas.scan_dragto(event.x, event.y, gain=1)

        # Bindings para interface
        canvas.bind("<MouseWheel>", zoom)  # Windows
        canvas.bind("<Button-4>", zoom)  # Linux: scroll up
        canvas.bind("<Button-5>", zoom)  # Linux: scroll down

        # Pan com botão do meio
        canvas.bind("<ButtonPress-2>", start_pan)
        canvas.bind("<B2-Motion>", do_pan)

        # Pan com botão direito
        canvas.bind("<ButtonPress-3>", start_pan)
        canvas.bind("<B3-Motion>", do_pan)

        # Pan com botão esquerdo quando em modo pan
        def on_mouse_down(event):
            if self.window_closed:
                return
            if self.pan_mode:
                canvas.scan_mark(event.x, event.y)

        def on_mouse_move(event):
            if self.window_closed:
                return
            if self.pan_mode:
                canvas.scan_dragto(event.x, event.y, gain=1)

        canvas.bind("<ButtonPress-1>", on_mouse_down)
        canvas.bind("<B1-Motion>", on_mouse_move)

        # Trackpad com dois dedos (se suportado pelo sistema)
        try:
            canvas.bind("<TouchpadPan>", do_pan)
        except:
            pass  # Ignorar se o evento não for suportado

        # Botões de controle - Primeira linha
        button_frame = tk.Frame(main_frame)
        button_frame.pack(fill=tk.X)

        tk.Button(button_frame, text="Imagem Anterior (A)", command=prev_image).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Próxima Imagem (D)", command=next_image).pack(side=tk.LEFT, padx=5)
        pan_button = tk.Button(button_frame, text="Modo Navegação (P)", command=toggle_pan_mode)
        pan_button.pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Reiniciar Zoom (R)", command=reset_zoom).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Salvar Imagem (S)", command=save_image).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Sair (Q)", command=on_closing).pack(side=tk.LEFT, padx=5)

        # Atalhos de teclado
        root.bind("<r>", lambda e: reset_zoom())
        root.bind("<p>", lambda e: toggle_pan_mode())
        root.bind("<q>", lambda e: on_closing())
        root.bind("<a>", lambda e: prev_image())
        root.bind("<d>", lambda e: next_image())
        root.bind("<s>", lambda e: save_image())

        # Adicionar teclas numéricas para alternar classes
        for i in range(10):
            cls_id = str(i)
            if cls_id in self.class_map:
                root.bind(cls_id, lambda e, id=cls_id: toggle_class_visibility(id))

        # Adicionar informações de atalhos
        shortcuts_frame = tk.Frame(main_frame)
        shortcuts_frame.pack(fill=tk.X, pady=5)

        shortcuts_label = tk.Label(
            shortcuts_frame,
            text="Atalhos: "
            + ", ".join([f"{k}={v}" for k, v in KEYBOARD_SHORTCUTS.items()])
            + "\nClique no nome da classe para alternar sua visibilidade. Use a roda do mouse para zoom.",
            justify=tk.LEFT,
            anchor=tk.W,
            wraplength=780,
        )
        shortcuts_label.pack(fill=tk.X, padx=5)

        # Protocolo para fechar janela
        root.protocol("WM_DELETE_WINDOW", on_closing)

        # Centralizar janela na tela
        root.update_idletasks()
        width = root.winfo_width()
        height = root.winfo_height()
        x = (root.winfo_screenwidth() // 2) - (width // 2)
        y = (root.winfo_screenheight() // 2) - (height // 2)
        root.geometry("{}x{}+{}+{}".format(width, height, x, y))

        # Carregar a primeira imagem
        load_current_image()

        # Iniciar loop principal
        root.mainloop()

    def save_annotated_images(
        self,
        image_dir: str,
        label_dir: Optional[str] = None,
        output_dir: str = "annotated_images",
        filter_classes: Optional[Set[str]] = None,
    ) -> int:
        """
        Salva todas as imagens com suas anotações desenhadas.

        Args:
            image_dir: Diretório contendo as imagens
            label_dir: Diretório contendo os arquivos de anotação
            output_dir: Diretório para salvar as imagens anotadas
            filter_classes: Conjunto de IDs de classe para exibir

        Returns:
            Número de imagens anotadas salvas
        """
        os.makedirs(output_dir, exist_ok=True)

        # Obter todos os arquivos de imagem
        image_files = []
        for ext in ["*.jpg", "*.jpeg", "*.png"]:
            image_files.extend(glob.glob(os.path.join(image_dir, ext)))

        if not image_files:
            logger.warning(f"Nenhum arquivo de imagem encontrado em {image_dir}")
            return 0

        # Ordenar imagens para consistência
        image_files.sort()

        # Rastrear quais classes mostrar
        class_visibility = {cls_id: True for cls_id in self.class_map.keys()}
        if filter_classes:
            class_visibility = {cls_id: (cls_id in filter_classes) for cls_id in self.class_map.keys()}

        saved_count = 0

        # Configurar barra de progresso
        print(f"Salvando {len(image_files)} imagens anotadas...")

        for img_path in image_files:
            img = self._load_image(img_path)
            if img is None:
                continue

            h, w = img.shape[:2]

            # Encontrar arquivo de anotação correspondente
            base_name = os.path.splitext(os.path.basename(img_path))[0]
            if label_dir:
                label_path = os.path.join(label_dir, f"{base_name}.txt")
            else:
                label_path = os.path.join(os.path.dirname(img_path), f"{base_name}.txt")

            # Desenhar caixas se as anotações existirem
            if os.path.exists(label_path):
                with open(label_path, "r") as f:
                    annotations = f.readlines()

                # Desenhar cada anotação
                box_idx = 0
                for ann in annotations:
                    box_data = self._process_annotation_line(ann, w, h, class_visibility)
                    if box_data is None:
                        continue

                    # Extrair dados
                    x1, y1, x2, y2 = box_data["x1"], box_data["y1"], box_data["x2"], box_data["y2"]
                    color = box_data["color"]
                    class_name = box_data["class_name"]

                    # Desenhar retângulo
                    cv2.rectangle(img, (x1, y1), (x2, y2), color, self.box_thickness)

                    # Adicionar nome da classe
                    cv2.putText(
                        img,
                        f"{class_name} #{box_idx + 1}",
                        (x1, y1 - 5),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        self.text_size,
                        color,
                        self.text_thickness,
                        cv2.LINE_AA,
                    )

                    box_idx += 1

                # Converter de RGB para BGR para salvar com OpenCV
                img_bgr = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

                # Salvar imagem anotada
                output_path = os.path.join(output_dir, f"annotated_{os.path.basename(img_path)}")
                cv2.imwrite(output_path, img_bgr)
                saved_count += 1

            else:
                logger.warning(f"Arquivo de anotação não encontrado para: {img_path}")

        logger.info(f"Processo concluído: {saved_count} imagens anotadas salvas em {output_dir}")
        return saved_count
