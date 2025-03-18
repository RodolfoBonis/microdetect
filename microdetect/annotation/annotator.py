"""
Módulo para anotação manual de imagens.
Implementação com todas as funcionalidades avançadas preservando o núcleo funcional.
"""

import glob
import json
import logging
import os
import random
import re
import shutil
import time
import tkinter as tk
from datetime import datetime
from tkinter import messagebox
from typing import List, Optional, Tuple

import cv2
import numpy as np
from PIL import Image, ImageTk

from microdetect.annotation.export_import import create_export_import_ui
from microdetect.utils.config import config

logger = logging.getLogger(__name__)

DEFAULT_AUTO_SAVE = True
DEFAULT_AUTO_SAVE_INTERVAL = 20  # 5 minutos

# Constantes para alças de redimensionamento
HANDLE_NONE = 0
HANDLE_NW = 1  # Noroeste
HANDLE_NE = 2  # Nordeste
HANDLE_SE = 3  # Sudeste
HANDLE_SW = 4  # Sudoeste
HANDLE_N = 5  # Norte
HANDLE_E = 6  # Leste
HANDLE_S = 7  # Sul
HANDLE_W = 8  # Oeste

# Atalhos de teclado para anotação
KEYBOARD_SHORTCUTS = {
    "a": "Imagem anterior",
    "d": "Próxima imagem",
    "p": "Ativar/desativar modo navegação",
    "r": "Reiniciar zoom e pan",
    "0-9": "Alternar visibilidade da classe",
    "s": "Salvar anotações",
    "S": "Mostrar estatísticas",
    "b": "Buscar imagens",
    "q": "Sair",
    "e": "Alternar modo de edição",
    "z": "Desfazer última ação",
    "x": "Salvar e sair",
    "n": "Salvar e próxima imagem",
    "i": "Abrir diálogo de exportação/importação",
    "g": "Ativar/desativar sugestões automáticas",
    "f": "Aplicar sugestões automáticas"
}


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
        self.current_image_path = None
        self.suggestion_mode = False
        self.suggested_boxes = []
        self.classes = classes or config.get("classes", ["0-levedura", "1-fungo", "2-micro-alga"])
        self.progress_file = ".annotation_progress.json"
        self.auto_save = auto_save
        self.auto_save_interval = auto_save_interval
        self.last_save_time = time.time()

        # Armazenar referências a objetos PhotoImage para evitar coleta de lixo prematura
        self.image_references = {}

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
        self.root = None  # Referência para a janela principal

        # Flag para controlar a navegação para a próxima imagem
        self.next_image_requested = False

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

    def _create_secure_dialog(self) -> tk.Toplevel:
        """
        Cria uma janela de diálogo segura que não terá problemas com referências de imagens.

        Returns:
            A janela de diálogo Toplevel
        """
        try:
            # Verificar se já temos uma instância Tk ativa
            root = None

            # Verificar se tk._default_root existe antes de tentar acessá-lo
            if hasattr(tk, '_default_root') and tk._default_root is not None:
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

    def _cleanup_image_references(self):
        """
        Limpa referências a imagens que não são mais necessárias.
        Chamado quando uma imagem é fechada ou quando a aplicação é encerrada.
        """
        try:
            # Manter apenas a referência atual, se houver
            current_key = None
            for key, img in self.image_references.items():
                if img is self.current_img_tk:
                    current_key = key
                    break

            # Nova lista de referências
            new_refs = {}
            if current_key:
                new_refs[current_key] = self.image_references[current_key]

            # Substituir o dicionário
            self.image_references = new_refs
        except Exception as e:
            logger.error(f"Erro ao limpar referências de imagem: {e}")

    def suggest_annotations(self, image_path: str, confidence: float = 0.5) -> List[Tuple[str, int, int, int, int]]:
        """
        Sugere anotações automáticas usando um modelo básico de detecção.

        Args:
            image_path: Caminho para a imagem
            confidence: Limiar de confiança para detecções

        Returns:
            Lista de bounding boxes sugeridas no formato [(class_id, x1, y1, x2, y2), ...]
        """
        try:
            logger.info(f"Gerando sugestões automáticas para {os.path.basename(image_path)}")

            # Carregar a imagem
            img = cv2.imread(image_path)
            if img is None:
                logger.error(f"Não foi possível carregar a imagem: {image_path}")
                return []

            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            h, w = img_rgb.shape[:2]

            # Em um cenário real, aqui você carregaria e usaria um modelo de ML
            # Por exemplo:
            # modelo = tf.keras.models.load_model("model/microorganisms_detector.h5")
            # predictions = modelo.predict(preprocess_image(img_rgb))
            # boxes = process_predictions(predictions, confidence)

            # Para este exemplo, vamos simular algumas detecções aleatórias
            # apenas para demonstrar como a função seria utilizada
            suggested_boxes = []

            # Simulação: gerar algumas caixas aleatórias
            # Em um projeto real, isso seria substituído por detecções reais
            num_suggestions = random.randint(3, 8)  # Número aleatório de sugestões

            for _ in range(num_suggestions):
                # Escolher classe aleatoriamente
                class_id = random.choice([c.split('-')[0] for c in self.classes])

                # Gerar coordenadas aleatórias
                box_w = random.randint(w // 10, w // 3)
                box_h = random.randint(h // 10, h // 3)

                x1 = random.randint(0, w - box_w)
                y1 = random.randint(0, h - box_h)
                x2 = x1 + box_w
                y2 = y1 + box_h

                # Adicionar à lista de sugestões
                suggested_boxes.append((class_id, x1, y1, x2, y2))

            logger.info(f"{len(suggested_boxes)} sugestões geradas para {os.path.basename(image_path)}")
            return suggested_boxes

        except Exception as e:
            logger.error(f"Erro ao gerar sugestões automáticas: {str(e)}")
            return []

    def apply_suggested_annotations(self):
        """
        Aplica as sugestões automáticas à imagem atual.
        Chamada quando o usuário aceita as sugestões.
        """
        if not hasattr(self, 'suggested_boxes') or not self.suggested_boxes:
            self.update_status("Não há sugestões para aplicar")
            return False

        # Adicionar cada caixa sugerida à lista de bounding boxes
        for class_id, x1, y1, x2, y2 in self.suggested_boxes:
            self.bounding_boxes.append((class_id, x1, y1, x2, y2))

            # Adicionar ao histórico
            self._add_to_history("add", {"index": len(self.bounding_boxes) - 1})

        # Limpar as sugestões após aplicar
        suggestions_count = len(self.suggested_boxes)
        self.suggested_boxes = []

        # Atualizar interface
        self.redraw_all_boxes()
        self.update_status(f"{suggestions_count} sugestões aplicadas com sucesso")

        # Desabilitar botão de aplicar
        if hasattr(self, 'apply_suggestions_button'):
            self.apply_suggestions_button.config(state=tk.DISABLED)

        return True

    def toggle_suggestion_mode(self):
        """
        Alterna o modo de sugestão automática.
        """
        if not hasattr(self, 'suggestion_mode'):
            self.suggestion_mode = False

        self.suggestion_mode = not self.suggestion_mode

        if self.suggestion_mode:
            # Gerar sugestões para a imagem atual
            if hasattr(self, 'current_image_path') and self.current_image_path:
                img_path = self.current_image_path
            else:
                # Se não tiver o atributo, usar a variável local do método annotate_image
                img_path = getattr(self, 'img_path', None)

            if img_path:
                self.suggested_boxes = self.suggest_annotations(img_path)

                # Mostrar as sugestões na interface
                self.show_suggestions()
                self.update_status(f"Modo de sugestão ativado: {len(self.suggested_boxes)} sugestões disponíveis")

                # Habilitar botão de aplicar
                if hasattr(self, 'apply_suggestions_button'):
                    self.apply_suggestions_button.config(state=tk.NORMAL)

                # Atualizar botão de sugestão
                if hasattr(self, 'suggestion_button'):
                    self.suggestion_button.config(bg="lightblue", text="Desativar Sugestões (G)")
            else:
                self.update_status("Não foi possível gerar sugestões: imagem não encontrada")
                self.suggestion_mode = False
        else:
            # Limpar sugestões
            self.suggested_boxes = []
            self.redraw_all_boxes()  # Remover visualização das sugestões
            self.update_status("Modo de sugestão desativado")

            # Desabilitar botão de aplicar
            if hasattr(self, 'apply_suggestions_button'):
                self.apply_suggestions_button.config(state=tk.DISABLED)

            # Atualizar botão de sugestão
            if hasattr(self, 'suggestion_button'):
                self.suggestion_button.config(bg="#f0f0f0", text="Sugestões Automáticas (G)")

    def show_suggestions(self):
        """
        Exibe visualmente as sugestões na interface.
        """
        if not hasattr(self, 'suggested_boxes') or not self.suggested_boxes:
            return

        # Garantir que temos acesso ao canvas
        if not hasattr(self, 'canvas') or not self.canvas:
            logger.error("Canvas não disponível para mostrar sugestões")
            return

        try:
            # Limpar sugestões anteriores
            self.canvas.delete("suggestion")
            self.canvas.delete("suggestion_label")

            # Desenhar cada sugestão
            for i, (class_id, x1, y1, x2, y2) in enumerate(self.suggested_boxes):
                # Converter para coordenadas do canvas
                canvas_x1 = x1 * self.display_scale * self.scale_factor
                canvas_y1 = y1 * self.display_scale * self.scale_factor
                canvas_x2 = x2 * self.display_scale * self.scale_factor
                canvas_y2 = y2 * self.display_scale * self.scale_factor

                # Usar cor distinta para sugestões (laranja)
                outline_color = "orange"

                # Encontrar nome da classe para exibição
                class_name = next(
                    (c for c in self.classes if c.startswith(class_id)),
                    f"{class_id}-desconhecido",
                )

                # Desenhar retângulo tracejado para indicar que é uma sugestão
                self.canvas.create_rectangle(
                    canvas_x1, canvas_y1, canvas_x2, canvas_y2,
                    outline=outline_color, width=2, dash=(5, 3),  # Linha tracejada
                    tags="suggestion"
                )

                # Desenhar rótulo
                self.canvas.create_text(
                    canvas_x1,
                    canvas_y1 - 5,
                    text=f"{class_name} (sugestão #{i + 1})",
                    anchor=tk.SW,
                    fill=outline_color,
                    font=("Arial", 10, "bold"),
                    tags="suggestion_label",
                )
        except Exception as e:
            logger.error(f"Erro ao mostrar sugestões: {str(e)}")

    def _add_suggestion_controls(self, button_frame, button_frame2):
        """
        Adiciona controles para sugestão automática.

        Args:
            button_frame: Frame para botões principais
            button_frame2: Frame para botões secundários
        """
        # Adicionar botão para ativar/desativar sugestões automáticas
        self.suggestion_button = tk.Button(
            button_frame,
            text="Sugestões Automáticas (G)",
            command=self.toggle_suggestion_mode,
            bg="#f0f0f0"  # Cor padrão
        )
        self.suggestion_button.pack(side=tk.LEFT, padx=5)

        # Adicionar botão para aplicar todas as sugestões
        self.apply_suggestions_button = tk.Button(
            button_frame2,
            text="Aplicar Sugestões (F)",
            command=self.apply_suggested_annotations,
            state=tk.DISABLED  # Inicialmente desabilitado
        )
        self.apply_suggestions_button.pack(side=tk.LEFT, padx=5)

        # Atalhos são definidos no método annotate_image, pois precisamos do root
        # que só é disponível nesse contexto

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

            # Converter para PIL Image
            pil_img = Image.fromarray(img_resized)

            # Criar nova instância de PhotoImage
            # MODIFICAÇÃO CRÍTICA: Usar um nome de chave consistente e verificar duplicações
            key = "zoomed_image"

            # Remover a referência anterior se existir
            if key in self.image_references:
                del self.image_references[key]

            # Criar nova referência
            self.image_references[key] = ImageTk.PhotoImage(pil_img)
            self.current_img_tk = self.image_references[key]

            # Atualizar imagem no canvas
            canvas.delete("background")
            canvas.create_image(0, 0, anchor=tk.NW, image=self.current_img_tk, tags="background")
            canvas.config(scrollregion=canvas.bbox(tk.ALL))
        except Exception as e:
            logger.error(f"Erro ao redesenhar imagem com zoom: {e}")

    def _count_annotations_by_class(self, output_dir: str) -> Tuple[dict, int]:
        """
        Conta o número de anotações por classe em todos os arquivos de anotação.

        Args:
            output_dir: Diretório contendo os arquivos de anotação

        Returns:
            Tupla com (dicionário de contagem por classe, total de anotações)
        """
        # Inicializar contagem de classes com todas as classes conhecidas
        class_counts = {class_id.split('-')[0]: 0 for class_id in self.classes}
        total_boxes = 0

        # Percorrer todos os arquivos de anotação
        annotation_files = glob.glob(os.path.join(output_dir, "*.txt"))
        for ann_file in annotation_files:
            if os.path.basename(ann_file) == self.progress_file:
                continue  # Pular o arquivo de progresso

            with open(ann_file, "r") as f:
                for line in f:
                    parts = line.strip().split()
                    if len(parts) >= 5:  # formato YOLO: class x_center y_center width height
                        class_id = parts[0]
                        class_counts[class_id] = class_counts.get(class_id, 0) + 1
                        total_boxes += 1

        return class_counts, total_boxes

    def _get_class_name(self, class_id: str) -> str:
        """
        Obtém o nome completo da classe a partir do ID.

        Args:
            class_id: ID da classe (ex: "0")

        Returns:
            Nome completo da classe (ex: "0-levedura")
        """
        return next((c for c in self.classes if c.startswith(class_id)), f"Classe {class_id}")

    def update_status(self, msg=None):
        """
        Atualiza o status na interface com proteção contra erros.

        Args:
            msg: Mensagem a ser exibida (opcional)
        """
        # Verificar se a janela ainda é válida e se temos o status_label
        if not hasattr(self, 'status_label') or not self._is_window_valid(getattr(self, 'status_label', None)):
            return

        try:
            if msg:
                self.status_label.config(text=msg)
        except Exception as e:
            logger.error(f"Erro ao atualizar status: {e}")

    def redraw_all_boxes(self, highlight_idx=None):
        """
        Redesenha todas as bounding boxes no canvas.

        Args:
            highlight_idx: Índice da caixa a ser destacada (opcional)

        Returns:
            True se as caixas foram redesenhadas com sucesso, False caso contrário
        """
        # Verificar se a janela ainda é válida
        if not self._is_window_valid(self.canvas):
            return False

        try:
            # Limpar o canvas
            self.canvas.delete("all")

            # Redesenhar a imagem de fundo
            self.canvas.create_image(0, 0, anchor=tk.NW, image=self.current_img_tk, tags="background")

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
                self.canvas.create_rectangle(
                    canvas_x1, canvas_y1, canvas_x2, canvas_y2,
                    outline=outline_color, width=outline_width, tags="box"
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

            # Reexibir sugestões se o modo de sugestão estiver ativo
            if hasattr(self, 'suggestion_mode') and self.suggestion_mode and hasattr(self, 'suggested_boxes'):
                self.show_suggestions()

            return True
        except Exception as e:
            logger.error(f"Erro ao redesenhar caixas: {e}")
            return False

    def search_and_filter_images(self, image_dir: str, output_dir: str, last_annotated_path: Optional[str] = None) -> \
    Tuple[List[str], int]:
        """
        Abre um diálogo para buscar e filtrar imagens para anotação.
        Também permite escolher como continuar quando há progresso anterior.

        Args:
            image_dir: Diretório de imagens
            output_dir: Diretório de anotações
            last_annotated_path: Caminho da última imagem anotada (opcional)

        Returns:
            Tuple[List[str], int]: Lista de caminhos de imagem selecionados e modo de continuação
            Modos: 0 = Continuar de onde parou, 1 = Recomeçar do início, 2 = Revisar a última imagem
        """
        # Obter todas as imagens
        all_images = []
        for ext in ["*.jpg", "*.jpeg", "*.png"]:
            all_images.extend(glob.glob(os.path.join(image_dir, ext)))

        # Ordenar imagens
        all_images.sort()

        if not all_images:
            messagebox.showinfo("Informação", "Nenhuma imagem encontrada no diretório.")
            return [], 0

        # Limpar todas as referências de imagem para evitar problemas de memória
        if hasattr(self, 'image_references'):
            self.image_references.clear()

        # Criar janela de busca de forma segura
        search_window = self._create_secure_dialog()
        search_window.title("Buscar e Filtrar Imagens")
        search_window.geometry("800x650")  # Aumentado para acomodar os botões extras
        search_window.minsize(600, 450)

        # Criar um dicionário local para armazenar referências a imagens desta janela
        search_image_refs = {}

        # Variáveis para armazenar resultados
        filtered_images = all_images.copy()
        result_images = []  # Para retornar
        result_mode = 0  # Modo de continuação (padrão: continuar de onde parou)

        # Frame principal
        main_frame = tk.Frame(search_window)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Frame de informações de progresso (se houver progresso anterior)
        if last_annotated_path:
            progress_frame = tk.LabelFrame(main_frame, text="Progresso de Anotação")
            progress_frame.pack(fill=tk.X, pady=10)

            # Exibir informação sobre o último arquivo anotado
            last_file_name = os.path.basename(last_annotated_path)
            last_index = all_images.index(last_annotated_path) if last_annotated_path in all_images else -1

            progress_info = tk.Frame(progress_frame)
            progress_info.pack(fill=tk.X, padx=5, pady=5)

            tk.Label(
                progress_info,
                text=f"Última imagem anotada: {last_file_name}",
                font=("Arial", 10, "bold")
            ).pack(side=tk.LEFT, padx=5)

            # Exibir progresso total
            if last_index >= 0:
                progress_percent = (last_index + 1) / len(all_images) * 100
                tk.Label(
                    progress_info,
                    text=f"Progresso: {last_index + 1}/{len(all_images)} ({progress_percent:.1f}%)"
                ).pack(side=tk.LEFT, padx=20)

            # Variável para armazenar a opção de continuação (mesmo que não use radio buttons)
            continuation_mode = tk.IntVar(value=0)  # Padrão: continuar de onde parou

            # Botões de acesso rápido para opções de navegação
            quick_frame = tk.Frame(progress_frame)
            quick_frame.pack(fill=tk.X, padx=5, pady=10)

            tk.Label(
                quick_frame,
                text="Opções rápidas de navegação:",
                font=("Arial", 10, "bold")
            ).pack(anchor="w", padx=5, pady=5)

            # Botões para cada opção de navegação
            button_frame = tk.Frame(quick_frame)
            button_frame.pack(fill=tk.X, padx=5, pady=5)

            # Função para continuar com uma opção específica
            def quick_continue(mode):
                nonlocal result_images, result_mode
                result_mode = mode

                if mode == 0:  # Continuar de onde parou
                    next_index = last_index + 1 if last_index < len(all_images) - 1 else 0
                    result_images = [all_images[next_index]]
                elif mode == 1:  # Recomeçar do início
                    result_images = [all_images[0]]
                else:  # Revisar a última imagem
                    result_images = [last_annotated_path]

                search_window.destroy()

            # Continuar da próxima imagem
            tk.Button(
                button_frame,
                text="Continuar da Próxima Imagem",
                command=lambda: quick_continue(0),
                bg="lightgreen",
                padx=10,
                pady=5,
                width=25
            ).pack(side=tk.LEFT, padx=5, pady=5)

            # Recomeçar do início
            tk.Button(
                button_frame,
                text="Recomeçar do Início",
                command=lambda: quick_continue(1),
                bg="#FFD580",  # Light orange
                padx=10,
                pady=5,
                width=25
            ).pack(side=tk.LEFT, padx=5, pady=5)

            # Revisar última imagem
            tk.Button(
                button_frame,
                text="Revisar Última Imagem",
                command=lambda: quick_continue(2),
                bg="#ADD8E6",  # Light blue
                padx=10,
                pady=5,
                width=25
            ).pack(side=tk.LEFT, padx=5, pady=5)

            # Adicionar separador
            tk.Frame(
                progress_frame,
                height=2,
                bd=1,
                relief=tk.SUNKEN
            ).pack(fill=tk.X, padx=5, pady=10)

            tk.Label(
                progress_frame,
                text="Ou selecione uma imagem específica abaixo:",
                font=("Arial", 10)
            ).pack(anchor="w", padx=5, pady=5)
        else:
            # Se não houver progresso anterior, definir o modo padrão
            continuation_mode = tk.IntVar(value=0)

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
        show_annotated_check = tk.Checkbutton(filter_frame, text="Mostrar apenas imagens anotadas",
                                              variable=show_annotated_var)
        show_annotated_check.pack(side=tk.LEFT, padx=5)

        # Opção para mostrar apenas imagens não anotadas
        show_unannotated_var = tk.BooleanVar(value=False)
        show_unannotated_check = tk.Checkbutton(filter_frame, text="Mostrar apenas imagens não anotadas",
                                                variable=show_unannotated_var)
        show_unannotated_check.pack(side=tk.LEFT, padx=20)

        # Botão de busca
        search_button = tk.Button(search_frame, text="Buscar", command=lambda: update_image_list())
        search_button.pack(side=tk.LEFT, padx=5)

        # Função para atualizar a lista quando o usuário buscar
        def update_image_list():
            nonlocal filtered_images

            # Obter termo de busca
            search_term = search_var.get().lower().strip()
            show_annotated = show_annotated_var.get()
            show_unannotated = show_unannotated_var.get()

            # Filtrar imagens
            filtered_images = []
            for img_path in all_images:
                img_filename = os.path.basename(img_path).lower()
                base_name = os.path.splitext(os.path.basename(img_path))[0]
                annotation_path = os.path.join(output_dir, f"{base_name}.txt")
                is_annotated = os.path.exists(annotation_path)

                # Verificar filtros
                if search_term and search_term not in img_filename:
                    continue

                if show_annotated and not is_annotated:
                    continue

                if show_unannotated and is_annotated:
                    continue

                filtered_images.append(img_path)

            # Atualizar listbox
            image_listbox.delete(0, tk.END)
            for img_path in filtered_images:
                base_name = os.path.splitext(os.path.basename(img_path))[0]
                annotation_path = os.path.join(output_dir, f"{base_name}.txt")
                is_annotated = os.path.exists(annotation_path)

                display_text = f"{os.path.basename(img_path)}"
                if is_annotated:
                    display_text += " [Anotada]"

                image_listbox.insert(tk.END, display_text)

            # Atualizar contadores
            total_label.config(text=f"Total: {len(filtered_images)} / {len(all_images)} imagens")

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

        # Frame para a lista de imagens
        list_frame = tk.Frame(main_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        # Label para contagem
        total_label = tk.Label(list_frame, text=f"Total: {len(all_images)} imagens", anchor="w")
        total_label.pack(fill=tk.X)

        # Lista de imagens com scrollbar
        list_subframe = tk.Frame(list_frame)
        list_subframe.pack(fill=tk.BOTH, expand=True)

        scrollbar = tk.Scrollbar(list_subframe)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        image_listbox = tk.Listbox(list_subframe, selectmode=tk.SINGLE, yscrollcommand=scrollbar.set,
                                   font=("Arial", 11))
        image_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar.config(command=image_listbox.yview)

        # Preencher a lista inicialmente
        for img_path in all_images:
            base_name = os.path.splitext(os.path.basename(img_path))[0]
            annotation_path = os.path.join(output_dir, f"{base_name}.txt")
            is_annotated = os.path.exists(annotation_path)

            display_text = f"{os.path.basename(img_path)}"
            if is_annotated:
                display_text += " [Anotada]"

            image_listbox.insert(tk.END, display_text)

        # Preview da imagem selecionada
        preview_frame = tk.Frame(main_frame)
        preview_frame.pack(fill=tk.X, pady=10)

        preview_label = tk.Label(preview_frame, text="Preview:")
        preview_label.pack(anchor="w")

        preview_image = tk.Label(preview_frame, text="Selecione uma imagem para visualizar")
        preview_image.pack(fill=tk.X, pady=5)

        # Função para mostrar preview
        def show_preview(*args):
            # Limpar preview anterior
            preview_image.config(image='', text="Selecione uma imagem para visualizar")

            # Obter seleção
            selection = image_listbox.curselection()
            if not selection:
                return

            # Obter caminho da imagem
            index = selection[0]
            if index >= len(filtered_images):
                return

            img_path = filtered_images[index]

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
                search_image_refs[key] = ImageTk.PhotoImage(pil_img)

                # Atualizar label com a imagem
                preview_image.config(image=search_image_refs[key], text='')

                # Obter informações do status de anotação
                base_name = os.path.splitext(os.path.basename(img_path))[0]
                annotation_path = os.path.join(output_dir, f"{base_name}.txt")
                is_annotated = os.path.exists(annotation_path)

                if is_annotated:
                    # Contar anotações
                    with open(annotation_path, 'r') as f:
                        annotations = f.readlines()
                    preview_label.config(text=f"Preview: {os.path.basename(img_path)} - {len(annotations)} anotações")
                else:
                    preview_label.config(text=f"Preview: {os.path.basename(img_path)} - Não anotada")

            except Exception as e:
                preview_image.config(text=f"Erro ao carregar preview: {str(e)}")

        # Vincular evento de seleção para mostrar preview
        image_listbox.bind('<<ListboxSelect>>', show_preview)

        # Botões de ação
        button_frame = tk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)

        # Função para anotar imagem selecionada
        def annotate_selected():
            nonlocal result_images, result_mode
            selection = image_listbox.curselection()

            if not selection:
                messagebox.showinfo("Informação", "Selecione uma imagem para anotar.")
                return

            # Obter imagem selecionada
            index = selection[0]
            if index >= len(filtered_images):
                return

            result_images = [filtered_images[index]]
            result_mode = 3  # Modo especial: imagem específica selecionada
            search_window.destroy()

        # Botão para selecionar todas
        def select_all():
            image_listbox.selection_set(0, tk.END)

        # Botão para limpar seleção
        def clear_selection():
            image_listbox.selection_clear(0, tk.END)

        # Adicionar botões
        tk.Button(
            button_frame,
            text="Cancelar",
            command=search_window.destroy,
            width=15
        ).pack(side=tk.RIGHT, padx=5)

        tk.Button(
            button_frame,
            text="Anotar Imagem Selecionada",
            command=annotate_selected,
            bg="lightgreen",
            width=25
        ).pack(side=tk.RIGHT, padx=5)

        tk.Button(
            button_frame,
            text="Limpar Seleção",
            command=clear_selection,
            width=15
        ).pack(side=tk.LEFT, padx=5)

        # Iniciar busca com os valores padrão
        update_image_list()

        # Configurar eventos de teclado para busca rápida
        search_entry.bind("<Return>", lambda e: update_image_list())

        # Ativar duplo clique para anotar diretamente
        image_listbox.bind("<Double-Button-1>", lambda e: annotate_selected())

        # Destacar última imagem anotada ou próxima, se houver
        if last_annotated_path and last_annotated_path in filtered_images:
            last_index = filtered_images.index(last_annotated_path)

            # Mostrar a próxima imagem por padrão
            if last_index < len(filtered_images) - 1:
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
        search_window.update_idletasks()
        width = search_window.winfo_width()
        height = search_window.winfo_height()
        x = (search_window.winfo_screenwidth() // 2) - (width // 2)
        y = (search_window.winfo_screenheight() // 2) - (height // 2)
        search_window.geometry(f"{width}x{height}+{x}+{y}")

        # Tornar modal
        search_window.transient()
        search_window.grab_set()

        # Limpar recursos ao fechar
        def on_closing():
            nonlocal search_image_refs
            # Limpar explicitamente todas as referências de imagem
            search_image_refs.clear()

            # Remover referência à janela temporária se existir
            if hasattr(search_window, '_temp_root') and search_window._temp_root:
                try:
                    search_window._temp_root.destroy()
                except:
                    pass
            search_window.destroy()

        search_window.protocol("WM_DELETE_WINDOW", on_closing)
        search_window.wait_window()

        return result_images, result_mode

    def _show_search_dialog(self, image_dir: str, output_dir: str):
        """
        Abre a interface de busca/filtro de imagens e permite navegar para uma imagem selecionada.

        Args:
            image_dir: Diretório de imagens
            output_dir: Diretório de anotações
        """
        # Armazenar referência à janela atual para depois
        current_window = self.root if hasattr(self, 'root') else None
        current_image_path = self.current_image_path if hasattr(self, 'current_image_path') else None

        # Verificar se há anotações não salvas na janela atual
        has_unsaved_annotations = False
        if hasattr(self, 'bounding_boxes') and self.bounding_boxes:
            has_unsaved_annotations = True

        # Obter imagens selecionadas
        selected_images, _ = self.search_and_filter_images(image_dir, output_dir)

        # Log para depuração
        logger.info(f"_show_search_dialog: selected_images={selected_images}")

        # Se o usuário selecionou uma imagem, perguntar se deseja navegar para ela
        if selected_images and len(selected_images) == 1:
            selected_path = selected_images[0]

            # Log para depuração
            logger.info(f"_show_search_dialog: selected_path={selected_path}")

            # Se a imagem selecionada for a mesma que já está aberta, não faz nada
            if current_image_path and os.path.normpath(selected_path) == os.path.normpath(current_image_path):
                messagebox.showinfo("Informação", "A imagem selecionada já está aberta.")
                return

            try:
                # Verificar se há anotações não salvas e perguntar se deseja salvar
                should_save = False
                should_continue = True

                if has_unsaved_annotations:
                    # Perguntar se deseja salvar a imagem atual antes de fechar
                    response = messagebox.askyesnocancel(
                        "Salvar Anotações",
                        f"Deseja salvar as anotações da imagem atual antes de abrir:\n{os.path.basename(selected_path)}?",
                    )

                    if response is None:  # Cancelou
                        should_continue = False
                    elif response is True:  # Sim, salvar
                        should_save = True
                        should_continue = True
                    else:  # Não, não salvar
                        should_save = False
                        should_continue = True

                if should_continue:
                    # Se escolheu salvar, faz isso primeiro
                    if should_save and hasattr(self, '_save_annotations') and current_image_path:
                        base_name = os.path.splitext(os.path.basename(current_image_path))[0]
                        self._save_annotations(self.bounding_boxes, output_dir, base_name)
                        logger.info(f"_show_search_dialog: salvou anotações para {base_name}")

                    # CRÍTICO: Cancelar todos os timers ativos antes de fechar a janela
                    # Isso evita os erros "invalid command name"
                    if hasattr(self, 'root') and self.root:
                        try:
                            # Encontrar todos os possíveis timers e cancelá-los
                            for timer_id in self.root.tk.call('after', 'info'):
                                try:
                                    self.root.after_cancel(timer_id)
                                except:
                                    pass
                            logger.info("_show_search_dialog: cancelou todos os timers ativos")
                        except Exception as e:
                            logger.error(f"Erro ao cancelar timers: {e}")

                    # IMPORTANTE: Salvar o caminho selecionado em uma variável local
                    # para evitar problemas de referência após destruir a janela
                    path_to_open = selected_path

                    # Limpar referências antes de fechar a janela atual
                    if hasattr(self, 'image_references'):
                        self.image_references.clear()

                    # Definir flag para encerrar a anotação atual
                    if hasattr(self, 'user_cancelled'):
                        self.user_cancelled = True

                    # IMPORTANTE: Não queremos continuar para a próxima imagem automaticamente
                    if hasattr(self, 'next_image_requested'):
                        self.next_image_requested = False

                    # Fechar a janela atual explicitamente
                    if current_window:
                        try:
                            current_window.destroy()
                        except Exception as e:
                            logger.error(f"Erro ao destruir janela atual: {e}")

                    # Pequena pausa para garantir que recursos sejam liberados
                    import time
                    time.sleep(0.2)

                    # Abrir a nova janela com a imagem selecionada
                    # IMPORTANTE: Imediatamente abrir a nova imagem para não perder o controle
                    result = self.annotate_image(path_to_open, output_dir)
                    logger.info(f"_show_search_dialog: resultado de annotate_image = {result}")

            except Exception as e:
                # Logar qualquer erro para depuração
                logger.error(f"Erro ao processar imagem selecionada: {e}", exc_info=True)

                # Tentar mostrar uma mensagem para o usuário
                try:
                    messagebox.showerror("Erro", f"Não foi possível abrir a imagem selecionada:\n{str(e)}")
                except:
                    pass

    def annotate_image(self, image_path: str, output_dir: str) -> Optional[str]:
        """
        Ferramenta para anotar manualmente células de levedura em imagens de microscopia com bounding boxes.

        Args:
            image_path: Caminho para a imagem a ser anotada
            output_dir: Diretório para salvar as anotações

        Returns:
            Caminho para o arquivo de anotação criado ou None se cancelado
        """
        # Log para depuração
        logger.info(f"annotate_image: Iniciando anotação de {os.path.basename(image_path)}")

        # Assegurar que o diretório de saída existe
        os.makedirs(output_dir, exist_ok=True)

        # CRÍTICO: Resetar TODAS as flags e estados
        self.user_cancelled = False
        self.window_closed = False
        self.next_image_requested = False  # Resetar flag para próxima imagem
        self.bounding_boxes = []
        self.action_history = []
        self.resize_handle = HANDLE_NONE
        self.original_box_state = None
        self.pan_mode = False
        self.current_image_path = image_path  # Armazenar referência à imagem atual

        # Garantir limpeza das referências de imagem
        if hasattr(self, 'image_references'):
            self.image_references = {}
        else:
            self.image_references = {}

        # Lista para rastrear timers ativos
        active_timer_ids = []

        # Carregar imagem
        loaded_data = self._load_image(image_path)
        if loaded_data[0] is None:
            logger.error(f"Não foi possível carregar a imagem: {image_path}")
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

        # MODIFICAÇÃO: Limpar qualquer instância Tk anterior
        if hasattr(tk, '_default_root') and tk._default_root is not None:
            try:
                tk._default_root.destroy()
                logger.info("Janela Tk anterior destruída")
            except:
                pass

        # Criar um novo root limpo
        root = tk.Tk()
        root.title(f"Anotação: {os.path.basename(image_path)}")
        self.root = root  # Armazenar referência

        # Configurar protocolo de fechamento para garantir limpeza adequada
        def on_window_close():
            try:
                if len(self.bounding_boxes) > 0:
                    if messagebox.askyesno("Sair", "Deseja salvar as anotações antes de sair?"):
                        save()

                # Limpar referências explicitamente
                self.image_references.clear()
                self.current_img_tk = None

                # Cancelar timers ativos
                for timer_id in active_timer_ids:
                    try:
                        root.after_cancel(timer_id)
                    except:
                        pass
                active_timer_ids.clear()

                # Definir flags
                self.window_closed = True
                self.user_cancelled = True
            except:
                pass
            finally:
                # Garantir que a janela seja destruída
                try:
                    root.destroy()
                except:
                    pass

        root.protocol("WM_DELETE_WINDOW", on_window_close)

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
        self.status_label = tk.Label(
            main_frame,
            text=f"Contagem: {len(self.bounding_boxes)} | Desenhe clicando e arrastando",
        )
        self.status_label.pack(side=tk.BOTTOM, fill=tk.X)

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

        # MODIFICAÇÃO CRÍTICA: Criar e armazenar a imagem usando Image.fromarray uma única vez
        pil_image = Image.fromarray(img_display)
        img_tk = ImageTk.PhotoImage(pil_image)

        # Armazenar essa referência na classe e no dicionário para garantir que não seja coletada
        self.current_img_tk = img_tk
        self.image_references["main"] = img_tk

        # Criar imagem no canvas usando apenas a referência armazenada
        canvas.create_image(0, 0, anchor=tk.NW, image=self.current_img_tk, tags="background")
        canvas.config(scrollregion=canvas.bbox(tk.ALL))

        # Armazenar referência ao canvas
        self.canvas = canvas

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
            self.update_status()

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
                                self.update_status(f"Redimensionando caixa {selected_box_idx + 1}")
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
                            self.update_status(f"Caixa {i + 1} selecionada para edição")
                            self.redraw_all_boxes(highlight_idx=selected_box_idx)
                            found_box = True
                            break

                    # Se não selecionou nenhuma caixa, desselecionar
                    if not found_box:
                        selected_box_idx = None
                        self.redraw_all_boxes()
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
                    self.redraw_all_boxes(highlight_idx=selected_box_idx)
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
                        self.update_status(f"Caixa {selected_box_idx + 1} redimensionada")
                        self.resize_handle = HANDLE_NONE
                    else:
                        # Foi movimento simples
                        if self.original_box_state:
                            current_box = tuple(self.bounding_boxes[selected_box_idx])
                            self._add_to_history(
                                "move",
                                {"index": selected_box_idx, "before": self.original_box_state, "after": current_box}
                            )
                        self.update_status(f"Caixa {selected_box_idx + 1} reposicionada")

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
                    self.update_status(f"Box adicionada: {current_class_str}")

                    # Auto-save se necessário
                    if self.auto_save:
                        if self._check_auto_save(self.bounding_boxes, output_dir, base_name):
                            self.update_status("Auto-save realizado")

                # Limpar o retângulo temporário
                if current_rect:
                    canvas.delete(current_rect)
                    current_rect = None

                # Redesenhar todas as caixas
                self.redraw_all_boxes(highlight_idx=selected_box_idx if edit_mode else None)

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

                self.update_status()
                self.redraw_all_boxes()
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

                self.update_status()
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
                self.update_status("Nada para desfazer.")
                return

            try:
                last_action = self.action_history.pop()
                action_type = last_action.get("type")
                data = last_action.get("data", {})

                if action_type == "add":
                    if data.get("index") < len(self.bounding_boxes):
                        self.bounding_boxes.pop(data.get("index"))
                        self.update_status("Desfez: Adição de caixa")
                elif action_type == "move" or action_type == "resize":
                    if data.get("index") < len(self.bounding_boxes):
                        self.bounding_boxes[data.get("index")] = data.get("before")
                        self.update_status(
                            f"Desfez: {'Movimentação' if action_type == 'move' else 'Redimensionamento'} de caixa")
                elif action_type == "delete":
                    self.bounding_boxes.insert(data.get("index"), data.get("box"))
                    self.update_status("Desfez: Exclusão de caixa")

                self.redraw_all_boxes(highlight_idx=selected_box_idx if edit_mode else None)

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
                    self.update_status(f"Caixa {selected_box_idx + 1} excluída")

                    # Resetar seleção
                    selected_box_idx = None
                elif self.bounding_boxes:
                    # Remover última caixa
                    removed_box = self.bounding_boxes[-1]
                    removed_index = len(self.bounding_boxes) - 1
                    self._add_to_history("delete", {"index": removed_index, "box": removed_box})

                    # Remover caixa
                    self.bounding_boxes.pop()
                    self.update_status(f"Última caixa excluída. Restantes: {len(self.bounding_boxes)}")
                else:
                    self.update_status("Nenhuma caixa para excluir")
                    return

                # Redesenhar
                self.redraw_all_boxes(highlight_idx=selected_box_idx if edit_mode else None)

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
                self.update_status("Nenhuma caixa para limpar.")
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
                self.redraw_all_boxes()
                self.update_status("Todas as caixas foram removidas.")

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
                self.update_status(f"Anotações salvas em {annotation_path}")
                self.last_save_time = time.time()  # Atualizar timestamp de último salvamento

                # CRUCIAL: Garantir que window_closed está como False
                reset_window_closed()

            except Exception as e:
                logger.error(f"Erro ao salvar anotações: {e}")
                # Não definir window_closed aqui

        def save_and_exit():
            """Salva as anotações e sai."""
            try:
                save()
                cleanup_timers()  # Limpar timers antes de fechar
                self.user_cancelled = False  # Não queremos cancelar, apenas sair normalmente
                root.destroy()
            except Exception as e:
                logger.error(f"Erro ao salvar e sair: {e}")
                self.window_closed = True
                self.user_cancelled = False
                try:
                    cleanup_timers()  # Limpar timers como última tentativa
                    root.destroy()
                except:
                    pass

        def save_and_next():
            """Salva as anotações e sinaliza para avançar para a próxima imagem."""
            try:
                # Salvar anotações
                nonlocal annotation_path
                annotation_path = self._save_annotations(self.bounding_boxes, output_dir, base_name)
                self.update_status(f"Anotações salvas em {annotation_path}")
                self.last_save_time = time.time()

                # Definir flags - FUNDAMENTAL para o funcionamento correto
                self.next_image_requested = True
                self.user_cancelled = False

                # Log para depuração
                logger.info("save_and_next: Definiu next_image_requested=True, fechando janela...")

                # Cancelar todos os timers pendentes
                for timer_id in active_timer_ids:
                    try:
                        root.after_cancel(timer_id)
                    except:
                        pass
                active_timer_ids.clear()

                # Limpar referências de imagem
                self._cleanup_image_references()

                # Fechar a janela - CRÍTICO: fechar a janela, não o programa
                try:
                    root.destroy()
                except:
                    pass

                logger.info("save_and_next: Janela fechada com sucesso!")

            except Exception as e:
                logger.error(f"Erro ao salvar e avançar: {str(e)}")
                # Mesmo com erro, tentar definir flags para continuar
                self.next_image_requested = True
                self.user_cancelled = False

                # Tentar fechar as janelas
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

                # Limpar referências de imagem
                self._cleanup_image_references()
            except:
                pass  # Ignorar erros durante o fechamento

            # Limpar timers antes de fechar
            cleanup_timers()

            # Definir flags de saída
            self.window_closed = True
            self.user_cancelled = True

            # Fechar a janela
            try:
                root.destroy()
            except:
                pass

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
                self.redraw_all_boxes()
                self.update_status()

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
                    self.redraw_all_boxes(highlight_idx=selected_box_idx if edit_mode else None)

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
                self.redraw_all_boxes(highlight_idx=selected_box_idx if edit_mode else None)
                self.update_status("Zoom reiniciado")

                # CRUCIAL: Garantir que window_closed está como False
                reset_window_closed()
            except Exception as e:
                logger.error(f"Erro ao reiniciar zoom: {e}")
                # Não definir window_closed aqui

        def monitor_window_state():
            """Monitora periodicamente o estado da janela e corrige se necessário."""
            try:
                if self.window_closed and root.winfo_exists():
                    logger.debug("Detectada inconsistência - window_closed é True, mas a janela existe!")
                    self.window_closed = False

                # Continuar monitorando se a janela ainda existir
                if root.winfo_exists():
                    timer_id = root.after(1000, monitor_window_state)
                    active_timer_ids.append(timer_id)
            except:
                # Se falhar, a janela provavelmente já foi fechada
                self.window_closed = True

        def check_auto_save():
            """Verifica periodicamente se é hora de auto-salvar."""
            if self.window_closed:
                return

            try:
                if self._check_auto_save(self.bounding_boxes, output_dir, base_name):
                    self.update_status("Auto-save realizado")

                if root.winfo_exists():
                    timer_id = root.after(10000, check_auto_save)
                    active_timer_ids.append(timer_id)
            except Exception as e:
                # Em caso de erro, apenas logar e continuar
                logger.error(f"Erro no auto-save: {e}")
                # Tentar programar o próximo auto-save mesmo com erro
                try:
                    if root.winfo_exists():
                        timer_id = root.after(10000, check_auto_save)
                        active_timer_ids.append(timer_id)
                except:
                    pass

        def cleanup_timers():
            """Cancela todos os timers pendentes da interface."""
            try:
                for timer_id in active_timer_ids[:]:
                    try:
                        if root.winfo_exists():
                            root.after_cancel(timer_id)
                        active_timer_ids.remove(timer_id)
                    except Exception as e:
                        logger.debug(f"Erro ao cancelar timer: {e}")
                        # Continuar mesmo com erro
            except Exception as e:
                logger.debug(f"Erro ao limpar timers: {e}")
                # Continuar mesmo com erro - garantir que não interrompa o fluxo

            # Bindings para zoom e pan

        canvas.bind("<MouseWheel>", zoom)  # Windows
        canvas.bind("<Button-4>", zoom)  # Linux: scroll up
        canvas.bind("<Button-5>", zoom)  # Linux: scroll down

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

        # Adicionar novo botão para salvar e avançar
        next_button = tk.Button(
            button_frame2,
            text="Salvar e Próxima (N)",
            command=save_and_next,
            bg="lightgreen"  # Destaque visual para o botão
        )
        next_button.pack(side=tk.LEFT, padx=5)

        stats_button = tk.Button(
            button_frame2,
            text="Estatísticas (S)",
            command=lambda: self.show_statistics(output_dir)
        )
        stats_button.pack(side=tk.LEFT, padx=5)

        # Adicionar botão de busca/filtro
        search_button = tk.Button(
            button_frame2,
            text="Buscar Imagens (B)",
            command=lambda: self._show_search_dialog(os.path.dirname(image_path), output_dir)
        )
        search_button.pack(side=tk.LEFT, padx=5)

        # Adicionar controles de sugestão automática e armazenar o caminho da imagem
        self.suggested_boxes = []
        self.suggestion_mode = False
        self.current_image_path = image_path
        self._add_suggestion_controls(button_frame, button_frame2)

        # Botão para exportar/importar anotações
        exportimport_button = tk.Button(
            button_frame2,
            text="Exportar/Importar (I)",
            command=lambda: create_export_import_ui(root, os.path.dirname(image_path), output_dir)
        )
        exportimport_button.pack(side=tk.LEFT, padx=5)

        # Vincular atalhos de teclado
        root.bind("<r>", lambda e: reset())
        root.bind("<z>", lambda e: undo())
        root.bind("<s>", lambda e: save())
        root.bind("<q>", lambda e: on_closing())
        root.bind("<e>", lambda e: toggle_edit_mode())
        root.bind("<p>", lambda e: toggle_pan_mode())
        root.bind("<c>", lambda e: cycle_classes())
        root.bind("<x>", lambda e: save_and_exit())
        root.bind("<n>", lambda e: save_and_next())
        root.bind("<Delete>", lambda e: delete_selected())
        root.bind("<Escape>", lambda e: select_none())
        root.bind("<w>", lambda e: reset_zoom())
        root.bind("<i>", lambda e: create_export_import_ui(root, os.path.dirname(image_path), output_dir))
        root.bind("<g>", lambda e: self.toggle_suggestion_mode())
        root.bind("<f>", lambda e: self.apply_suggested_annotations())
        root.bind("<S>", lambda e: self.show_statistics(output_dir))
        root.bind("<b>", lambda e: self._show_search_dialog(os.path.dirname(image_path), output_dir))

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
        self.redraw_all_boxes()

        # Iniciar o monitoramento do estado da janela e auto-save
        # Armazenar IDs dos timers para poder cancelá-los depois
        timer_id = root.after(1000, monitor_window_state)
        active_timer_ids.append(timer_id)

        # Auto-save timer
        if self.auto_save:
            timer_id = root.after(10000, check_auto_save)
            active_timer_ids.append(timer_id)

        # Iniciar loop principal
        root.mainloop()

        # Garantir que todos os timers sejam limpos ao sair
        cleanup_timers()

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
        os.makedirs(output_dir, exist_ok=True)

        # Obter todos os arquivos de imagem
        all_image_files = []
        for ext in ["*.jpg", "*.jpeg", "*.png"]:
            all_image_files.extend(glob.glob(os.path.join(image_dir, ext)))

        if not all_image_files:
            logger.warning(f"Nenhum arquivo de imagem encontrado em {image_dir}")
            return 0, 0

        # Ordenar imagens para consistência
        all_image_files.sort()

        # Verificar se há progresso salvo
        progress_path = os.path.join(output_dir, self.progress_file)
        last_annotated_path = None

        if os.path.exists(progress_path):
            try:
                with open(progress_path, "r") as f:
                    progress_data = json.load(f)

                last_annotated = progress_data.get("last_annotated", "")
                if last_annotated in all_image_files:
                    last_annotated_path = last_annotated
                    logger.info(f"Progresso encontrado. Última imagem anotada: {os.path.basename(last_annotated)}")
            except Exception as e:
                logger.warning(f"Erro ao carregar progresso: {str(e)}")
                logger.info("Iniciando anotação do início.")

        # Criar backup antes de iniciar a anotação
        self.backup_annotations(output_dir)

        # Chamar o método de busca e filtro com o caminho da última imagem anotada
        filtered_images, continuation_mode = self.search_and_filter_images(
            image_dir, output_dir, last_annotated_path
        )

        if not filtered_images:
            logger.info("Nenhuma imagem selecionada para anotação. Encerrando.")
            return 0, 0

        # Usar apenas as imagens filtradas/selecionadas pelo usuário
        image_files = filtered_images
        logger.info(f"Usando {len(image_files)} imagens selecionadas para anotação")

        # Determinar o índice inicial com base no modo de continuação e última imagem anotada
        start_index = 0
        total_annotated = 0
        imagens_existentes = 0

        if last_annotated_path and last_annotated_path in image_files:
            last_index = image_files.index(last_annotated_path)

            if continuation_mode == 0:  # Continuar de onde parou
                start_index = last_index + 1 if last_index < len(image_files) - 1 else 0
            elif continuation_mode == 1:  # Recomeçar do início
                start_index = 0
            else:  # Revisar a última imagem anotada
                start_index = last_index

        # Contar anotações já existentes antes do ponto de retomada
        for i in range(start_index):
            img_path = image_files[i]
            base_name = os.path.splitext(os.path.basename(img_path))[0]
            existing_annotation = os.path.join(output_dir, f"{base_name}.txt")
            if os.path.exists(existing_annotation):
                imagens_existentes += 1

        # Processar imagens a partir do ponto de retomada
        i = start_index
        continue_annotating = True

        # LOOP PRINCIPAL DE ANOTAÇÃO
        while continue_annotating and i < len(image_files):
            # Evita índices inválidos
            if i >= len(image_files):
                logger.warning("Índice de imagem inválido. Encerrando.")
                break

            img_path = image_files[i]
            base_name = os.path.splitext(os.path.basename(img_path))[0]
            self.current_image_path = img_path  # Armazenar para referência

            logger.info(f"Anotando: {os.path.basename(img_path)} ({i + 1}/{len(image_files)})")

            # Verificar se já existe anotação
            existing_annotation = os.path.join(output_dir, f"{base_name}.txt")
            if os.path.exists(existing_annotation) and i != start_index:
                option_selected = messagebox.askyesnocancel(
                    f"Imagem Existente: {os.path.basename(img_path)}",
                    "Esta imagem já possui anotação. O que deseja fazer?\n\n"
                    "Sim = Editar a anotação existente\n"
                    "Não = Pular esta imagem\n"
                    "Cancelar = Interromper a anotação"
                )

                if option_selected is None:  # Cancelar
                    logger.info("Anotação cancelada pelo usuário.")
                    break
                elif option_selected is False:  # Pular
                    logger.info(f"Pulando imagem com anotação existente: {os.path.basename(img_path)}")
                    i += 1
                    continue
                # else: continua para editar

            # Resetar flags antes de anotar cada imagem
            self.window_closed = False
            self.next_image_requested = False
            self.user_cancelled = False

            # Anotar a imagem atual
            annotation_path = self.annotate_image(img_path, output_dir)

            # Log de depuração para verificar flags
            logger.info(
                f"Após annotate_image: next_image_requested={self.next_image_requested}, user_cancelled={self.user_cancelled}")

            # Se o usuário cancelou, interromper
            if self.user_cancelled:
                logger.info("Usuário cancelou a anotação. Interrompendo processo.")
                break

            # Se foi salvo, atualizar contador e progresso
            if annotation_path:
                total_annotated += 1
                logger.info(f"Anotação salva em: {annotation_path}")
                last_annotated_path = img_path

                # Salvar progresso
                self._save_progress(progress_path, img_path)

            # CRÍTICO: Verificar flag para avançar para próxima imagem
            if self.next_image_requested:
                logger.info(f"Usuário solicitou próxima imagem (flag next_image_requested=True)")
                i += 1  # Avançar para próxima imagem

                # Se chegou ao final, avisar usuário
                if i >= len(image_files):
                    logger.info("Chegou ao final da lista de imagens selecionadas.")
                    messagebox.showinfo(
                        "Anotação Completa",
                        "Todas as imagens selecionadas foram anotadas!"
                    )
                    break
            else:
                # Usuário não pediu para ir para próxima, então sair do loop
                logger.info("Usuário não solicitou próxima imagem. Encerrando sessão.")
                break

        # Contar anotações por classe e obter total de objetos
        class_counts, total_objetos = self._count_annotations_by_class(output_dir)

        # Calcular quantas imagens ainda faltam anotar
        imagens_anotadas = total_annotated + imagens_existentes

        # Exibir resumo das anotações
        print("\n" + "=" * 60)
        print(" " * 20 + "RESUMO DA ANOTAÇÃO")
        print("=" * 60)
        print(f"Total de imagens: {len(all_image_files)}")
        print(f"Imagens selecionadas: {len(image_files)}")
        print(f"Imagens anotadas: {imagens_anotadas}")
        print(f"Imagens anotadas nesta sessão: {total_annotated}")

        # Imprimir contagem por classe
        print("\nQuantidade de anotações por classe:")
        for class_id, count in sorted(class_counts.items()):
            if count > 0:  # Mostrar apenas classes que foram usadas
                class_name = self._get_class_name(class_id)
                print(f"  - {class_name}: {count}")

        print(f"\nTotal de objetos anotados: {total_objetos}")
        print("=" * 60)

        # Mostrar estatísticas apenas se houve anotações realizadas
        if total_annotated > 0:
            try:
                # Perguntar ao usuário se deseja ver as estatísticas
                show_stats = messagebox.askyesno(
                    "Anotação Concluída",
                    f"Anotação finalizada!\n\n"
                    f"Total de imagens anotadas: {imagens_anotadas}\n"
                    f"Total de objetos anotados: {total_objetos}\n\n"
                    f"Deseja visualizar o dashboard de estatísticas?"
                )

                if show_stats:
                    # Mostrar estatísticas em janela gráfica
                    self.show_statistics(output_dir)
            except Exception as e:
                # Em caso de erro com a interface gráfica, apenas logar o erro
                logger.error(f"Erro ao exibir diálogo de estatísticas: {e}")

        return len(image_files), imagens_anotadas


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
        Os backups são armazenados em uma pasta 'backups' dentro do diretório de labels.

        Args:
            label_dir: Diretório contendo os arquivos de anotação

        Returns:
            Caminho para o diretório de backup ou None se falhar
        """
        timestamp = time.strftime("%Y%m%d_%H%M%S")

        # Criar diretório de backups (filho do diretório de labels)
        backups_dir = os.path.join(label_dir, "backups")
        os.makedirs(backups_dir, exist_ok=True)

        # Criar diretório específico para este backup
        backup_dir = os.path.join(backups_dir, f"backup_annotations_{timestamp}")

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

                    for dirname in os.listdir(backups_dir):
                        dir_path = os.path.join(backups_dir, dirname)
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


    def show_statistics(self, output_dir: str):
        """
        Exibe um dashboard com estatísticas das anotações.

        Args:
            output_dir: Diretório contendo as anotações
        """
        try:
            # Importar matplotlib aqui para evitar dependência desnecessária se não for usado
            import matplotlib.pyplot as plt
            from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
            from matplotlib.figure import Figure

            # Calcular estatísticas
            class_counts, total_objetos = self._count_annotations_by_class(output_dir)

            # Contar arquivos de anotação
            annotation_files = [f for f in glob.glob(os.path.join(output_dir, "*.txt"))
                                if os.path.basename(f) != self.progress_file]
            total_imagens_anotadas = len(annotation_files)

            # Criar janela para o dashboard de forma segura
            stats_window = self._create_secure_dialog()
            stats_window.title("Dashboard de Estatísticas de Anotação")
            stats_window.geometry("800x600")
            stats_window.minsize(600, 400)

            # Frame principal
            main_frame = tk.Frame(stats_window)
            main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

            # Título
            tk.Label(main_frame, text="Estatísticas de Anotação",
                     font=("Arial", 16, "bold")).pack(pady=10)

            # Frame para estatísticas gerais
            stats_frame = tk.Frame(main_frame)
            stats_frame.pack(fill=tk.X, pady=10)

            # Estatísticas gerais
            tk.Label(stats_frame, text=f"Total de imagens anotadas: {total_imagens_anotadas}",
                     font=("Arial", 12)).pack(anchor="w")
            tk.Label(stats_frame, text=f"Total de objetos anotados: {total_objetos}",
                     font=("Arial", 12)).pack(anchor="w")

            # Média de objetos por imagem
            avg_objects = total_objetos / total_imagens_anotadas if total_imagens_anotadas > 0 else 0
            tk.Label(stats_frame, text=f"Média de objetos por imagem: {avg_objects:.2f}",
                     font=("Arial", 12)).pack(anchor="w")

            # Frame para gráficos
            graph_frame = tk.Frame(main_frame)
            graph_frame.pack(fill=tk.BOTH, expand=True, pady=10)

            # Criar figura para gráficos
            figure = Figure(figsize=(8, 4), dpi=100)

            # Gráfico de distribuição de classes
            ax1 = figure.add_subplot(121)  # 1 linha, 2 colunas, posição 1

            # Preparar dados para o gráfico
            classes = []
            counts = []
            colors = ['#4CAF50', '#2196F3', '#FFC107', '#F44336', '#9C27B0', '#00BCD4', '#FF9800', '#795548']

            for i, (class_id, count) in enumerate(sorted(class_counts.items())):
                if count > 0:
                    classes.append(self._get_class_name(class_id))
                    counts.append(count)

            # Criar gráfico de barras
            ax1.bar(classes, counts, color=colors[:len(classes)])
            ax1.set_title('Distribuição de Classes')
            ax1.set_ylabel('Quantidade')
            ax1.tick_params(axis='x', rotation=45)

            # Gráfico de pizza com porcentagens
            ax2 = figure.add_subplot(122)  # 1 linha, 2 colunas, posição 2

            # Calcular porcentagens
            if sum(counts) > 0:
                percentages = [count / sum(counts) * 100 for count in counts]
                ax2.pie(percentages, labels=classes, autopct='%1.1f%%',
                        startangle=90, colors=colors[:len(classes)])
                ax2.set_title('Porcentagem por Classe')

            figure.tight_layout()

            # Incorporar o gráfico no tkinter
            canvas = FigureCanvasTkAgg(figure, graph_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

            # Frame para detalhes por classe
            details_frame = tk.Frame(main_frame)
            details_frame.pack(fill=tk.X, pady=10)

            # Título da seção
            tk.Label(details_frame, text="Detalhes por Classe",
                     font=("Arial", 12, "bold")).pack(anchor="w", pady=5)

            # Tabela de detalhes
            class_details = tk.Frame(details_frame)
            class_details.pack(fill=tk.X)

            # Cabeçalhos
            tk.Label(class_details, text="Classe", width=20, font=("Arial", 10, "bold"),
                     relief=tk.RIDGE).grid(row=0, column=0, sticky="ew")
            tk.Label(class_details, text="Quantidade", width=10, font=("Arial", 10, "bold"),
                     relief=tk.RIDGE).grid(row=0, column=1, sticky="ew")
            tk.Label(class_details, text="Porcentagem", width=15, font=("Arial", 10, "bold"),
                     relief=tk.RIDGE).grid(row=0, column=2, sticky="ew")

            # Preencher dados da tabela
            for i, (class_name, count) in enumerate(zip(classes, counts)):
                percentage = count / total_objetos * 100 if total_objetos > 0 else 0

                tk.Label(class_details, text=class_name, width=20, anchor="w",
                         relief=tk.RIDGE).grid(row=i + 1, column=0, sticky="ew")
                tk.Label(class_details, text=str(count), width=10,
                         relief=tk.RIDGE).grid(row=i + 1, column=1, sticky="ew")
                tk.Label(class_details, text=f"{percentage:.1f}%", width=15,
                         relief=tk.RIDGE).grid(row=i + 1, column=2, sticky="ew")

            # Botão para fechar
            tk.Button(main_frame, text="Fechar", command=stats_window.destroy,
                      width=10).pack(pady=10)

            # Centralizar janela
            stats_window.update_idletasks()
            width = stats_window.winfo_width()
            height = stats_window.winfo_height()
            x = (stats_window.winfo_screenwidth() // 2) - (width // 2)
            y = (stats_window.winfo_screenheight() // 2) - (height // 2)
            stats_window.geometry(f"{width}x{height}+{x}+{y}")

            # Tornar modal
            stats_window.transient()
            stats_window.grab_set()

            # Limpar recursos ao fechar
            def on_closing():
                # Remover referência à janela temporária se existir
                if hasattr(stats_window, '_temp_root') and stats_window._temp_root:
                    try:
                        stats_window._temp_root.destroy()
                    except:
                        pass
                stats_window.destroy()

            stats_window.protocol("WM_DELETE_WINDOW", on_closing)
            stats_window.wait_window()

        except Exception as e:
            logger.error(f"Erro ao exibir estatísticas: {e}")
            messagebox.showerror("Erro", f"Não foi possível exibir as estatísticas: {str(e)}")