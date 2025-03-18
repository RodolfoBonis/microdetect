"""
Visualização de anotações no canvas.
"""

import logging
import tkinter as tk

logger = logging.getLogger(__name__)


class AnnotationVisualizer:
    """
    Responsável por desenhar as anotações no canvas.
    """

    def __init__(self, canvas, classes, handle_size=6):
        """
        Inicializa o visualizador de anotações.

        Args:
            canvas: Objeto canvas do Tkinter onde serão desenhadas as anotações
            classes: Lista de classes disponíveis para anotação
            handle_size: Tamanho das alças de redimensionamento
        """
        self.canvas = canvas
        self.classes = classes
        self.handle_size = handle_size

    def get_class_name(self, class_id):
        """
        Obtém o nome completo da classe a partir do ID.

        Args:
            class_id: ID da classe (ex: "0")

        Returns:
            Nome completo da classe (ex: "0-levedura")
        """
        return next((c for c in self.classes if c.startswith(class_id)), f"{class_id}-desconhecido")

    def draw_bounding_boxes(self, boxes, highlight_idx=None, display_scale=1.0, scale_factor=1.0):
        """
        Desenha todas as bounding boxes no canvas.

        Args:
            boxes: Lista de bounding boxes no formato [(class_id, x1, y1, x2, y2), ...]
            highlight_idx: Índice da caixa a ser destacada (opcional)
            display_scale: Escala de exibição da imagem
            scale_factor: Fator de escala atual (zoom)

        Returns:
            True se as caixas foram redesenhadas com sucesso, False caso contrário
        """
        try:
            # Limpar o canvas de elementos anteriores
            self.canvas.delete("box")
            self.canvas.delete("label")
            self.canvas.delete("handle")

            # Redesenhar todas as boxes
            for i, (class_id, x1, y1, x2, y2) in enumerate(boxes):
                # Converter para coordenadas do canvas
                canvas_x1 = x1 * display_scale * scale_factor
                canvas_y1 = y1 * display_scale * scale_factor
                canvas_x2 = x2 * display_scale * scale_factor
                canvas_y2 = y2 * display_scale * scale_factor

                # Determinar cor (destacar se selecionado)
                outline_color = "red" if i == highlight_idx else "green"
                outline_width = 3 if i == highlight_idx else 2

                # Encontrar nome da classe para exibição
                class_name = self.get_class_name(class_id)

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
                    self._draw_resize_handles(canvas_x1, canvas_y1, canvas_x2, canvas_y2, outline_color)

            return True
        except Exception as e:
            logger.error(f"Erro ao redesenhar caixas: {e}")
            return False

    def _draw_resize_handles(self, x1, y1, x2, y2, color):
        """
        Desenha as alças de redimensionamento para uma bounding box.

        Args:
            x1, y1: Coordenadas do canto superior esquerdo
            x2, y2: Coordenadas do canto inferior direito
            color: Cor das alças
        """
        # Calcular pontos médios
        mid_x = (x1 + x2) / 2
        mid_y = (y1 + y2) / 2

        handle_size = self.handle_size

        # Desenhar alças nos cantos
        # NO (Noroeste)
        self.canvas.create_rectangle(
            x1 - handle_size,
            y1 - handle_size,
            x1 + handle_size,
            y1 + handle_size,
            fill=color,
            tags="handle",
        )
        # NE (Nordeste)
        self.canvas.create_rectangle(
            x2 - handle_size,
            y1 - handle_size,
            x2 + handle_size,
            y1 + handle_size,
            fill=color,
            tags="handle",
        )
        # SE (Sudeste)
        self.canvas.create_rectangle(
            x2 - handle_size,
            y2 - handle_size,
            x2 + handle_size,
            y2 + handle_size,
            fill=color,
            tags="handle",
        )
        # SO (Sudoeste)
        self.canvas.create_rectangle(
            x1 - handle_size,
            y2 - handle_size,
            x1 + handle_size,
            y2 + handle_size,
            fill=color,
            tags="handle",
        )

        # Desenhar alças nos lados
        # Norte
        self.canvas.create_rectangle(
            mid_x - handle_size,
            y1 - handle_size,
            mid_x + handle_size,
            y1 + handle_size,
            fill=color,
            tags="handle",
        )
        # Leste
        self.canvas.create_rectangle(
            x2 - handle_size,
            mid_y - handle_size,
            x2 + handle_size,
            mid_y + handle_size,
            fill=color,
            tags="handle",
        )
        # Sul
        self.canvas.create_rectangle(
            mid_x - handle_size,
            y2 - handle_size,
            mid_x + handle_size,
            y2 + handle_size,
            fill=color,
            tags="handle",
        )
        # Oeste
        self.canvas.create_rectangle(
            x1 - handle_size,
            mid_y - handle_size,
            x1 + handle_size,
            mid_y + handle_size,
            fill=color,
            tags="handle",
        )

    def draw_temporary_box(self, start_x, start_y, end_x, end_y, temp_id=None):
        """
        Desenha um retângulo temporário durante a criação de uma bounding box.

        Args:
            start_x, start_y: Coordenadas iniciais
            end_x, end_y: Coordenadas finais
            temp_id: ID do retângulo temporário anterior (para substituição)

        Returns:
            ID do retângulo temporário criado
        """
        # Remover retângulo temporário anterior se existir
        if temp_id:
            self.canvas.delete(temp_id)

        # Criar novo retângulo temporário
        return self.canvas.create_rectangle(start_x, start_y, end_x, end_y, outline="green", width=2, tags="temp_box")

    def draw_suggestions(self, suggestions, display_scale, scale_factor):
        """
        Desenha as sugestões de anotação no canvas.

        Args:
            suggestions: Lista de sugestões no formato [(class_id, x1, y1, x2, y2), ...]
            display_scale: Escala de exibição da imagem
            scale_factor: Fator de escala atual (zoom)
        """
        # Limpar sugestões anteriores
        self.canvas.delete("suggestion")
        self.canvas.delete("suggestion_label")

        # Desenhar cada sugestão
        for i, (class_id, x1, y1, x2, y2) in enumerate(suggestions):
            # Converter para coordenadas do canvas
            canvas_x1 = x1 * display_scale * scale_factor
            canvas_y1 = y1 * display_scale * scale_factor
            canvas_x2 = x2 * display_scale * scale_factor
            canvas_y2 = y2 * display_scale * scale_factor

            # Usar cor distinta para sugestões (laranja)
            outline_color = "orange"

            # Encontrar nome da classe para exibição
            class_name = self.get_class_name(class_id)

            # Desenhar retângulo tracejado para indicar que é uma sugestão
            self.canvas.create_rectangle(
                canvas_x1,
                canvas_y1,
                canvas_x2,
                canvas_y2,
                outline=outline_color,
                width=2,
                dash=(5, 3),  # Linha tracejada
                tags="suggestion",
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

    def clear_all(self):
        """Limpa todas as anotações do canvas."""
        self.canvas.delete("box")
        self.canvas.delete("label")
        self.canvas.delete("handle")
        self.canvas.delete("suggestion")
        self.canvas.delete("suggestion_label")
        self.canvas.delete("temp_box")
