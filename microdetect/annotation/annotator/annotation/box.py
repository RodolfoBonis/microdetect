"""
Gerenciamento de bounding boxes para anotação de imagens.
"""

from microdetect.annotation.annotator.utils.constants import (
    HANDLE_NONE, HANDLE_NW, HANDLE_NE, HANDLE_SE, HANDLE_SW,
    HANDLE_N, HANDLE_E, HANDLE_S, HANDLE_W
)


class BoundingBoxManager:
    """
    Gerencia as bounding boxes para anotação de imagens.
    """

    def __init__(self):
        """Inicializa o gerenciador de bounding boxes."""
        self.boxes = []
        self.selected_idx = None
        self.resize_handle = HANDLE_NONE
        self.handle_size = 6
        self.original_box_state = None

    def add_box(self, class_id, x1, y1, x2, y2):
        """
        Adiciona uma nova bounding box.

        Args:
            class_id: ID da classe (ex: "0")
            x1, y1: Coordenadas do canto superior esquerdo
            x2, y2: Coordenadas do canto inferior direito

        Returns:
            Índice da nova bounding box
        """
        self.boxes.append((class_id, x1, y1, x2, y2))
        return len(self.boxes) - 1

    def update_box(self, idx, class_id=None, x1=None, y1=None, x2=None, y2=None):
        """
        Atualiza uma bounding box existente.

        Args:
            idx: Índice da bounding box a ser atualizada
            class_id, x1, y1, x2, y2: Valores a serem atualizados (None para manter valor atual)

        Returns:
            True se atualizado com sucesso, False caso contrário
        """
        if idx < 0 or idx >= len(self.boxes):
            return False

        current = self.boxes[idx]

        # Manter valores atuais para parâmetros não especificados
        class_id = class_id if class_id is not None else current[0]
        x1 = x1 if x1 is not None else current[1]
        y1 = y1 if y1 is not None else current[2]
        x2 = x2 if x2 is not None else current[3]
        y2 = y2 if y2 is not None else current[4]

        # Garantir que x1 < x2 e y1 < y2
        if x1 > x2:
            x1, x2 = x2, x1
        if y1 > y2:
            y1, y2 = y2, y1

        self.boxes[idx] = (class_id, x1, y1, x2, y2)
        return True

    def remove_box(self, idx):
        """
        Remove uma bounding box.

        Args:
            idx: Índice da bounding box a ser removida

        Returns:
            Tupla com (class_id, x1, y1, x2, y2) da box removida ou None se falhar
        """
        if idx < 0 or idx >= len(self.boxes):
            return None

        removed = self.boxes[idx]
        self.boxes.pop(idx)

        # Resetar a seleção se a caixa selecionada foi removida
        if self.selected_idx == idx:
            self.selected_idx = None
        # Ajustar índice selecionado se uma caixa anterior foi removida
        elif self.selected_idx and self.selected_idx > idx:
            self.selected_idx -= 1

        return removed

    def remove_last(self):
        """
        Remove a última bounding box.

        Returns:
            Tupla com (class_id, x1, y1, x2, y2) da box removida ou None se não houver boxes
        """
        if not self.boxes:
            return None

        return self.remove_box(len(self.boxes) - 1)

    def get_box(self, idx):
        """
        Obtém uma bounding box pelo índice.

        Args:
            idx: Índice da bounding box

        Returns:
            Tupla com (class_id, x1, y1, x2, y2) ou None se o índice for inválido
        """
        if idx < 0 or idx >= len(self.boxes):
            return None

        return self.boxes[idx]

    def select_box(self, idx):
        """
        Seleciona uma bounding box pelo índice.

        Args:
            idx: Índice da bounding box ou None para desselecionar

        Returns:
            True se a seleção for bem-sucedida, False caso contrário
        """
        if idx is not None and (idx < 0 or idx >= len(self.boxes)):
            return False

        self.selected_idx = idx
        return True

    def clear_all(self):
        """
        Remove todas as bounding boxes.

        Returns:
            Número de boxes removidas
        """
        count = len(self.boxes)
        self.boxes.clear()
        self.selected_idx = None
        return count

    def detect_resize_handle(self, canvas_x, canvas_y, box_idx, display_scale, scale_factor):
        """
        Detecta se o clique foi em uma alça de redimensionamento.

        Args:
            canvas_x: Coordenada X do clique no canvas
            canvas_y: Coordenada Y do clique no canvas
            box_idx: Índice da caixa a verificar
            display_scale: Escala de exibição da imagem
            scale_factor: Fator de escala atual (zoom)

        Returns:
            Identificador da alça ou HANDLE_NONE se não houver alça
        """
        if box_idx is None or box_idx >= len(self.boxes):
            return HANDLE_NONE

        # Obter coordenadas da caixa
        _, x1, y1, x2, y2 = self.boxes[box_idx]

        # Converter para coordenadas do canvas
        canvas_x1 = x1 * display_scale * scale_factor
        canvas_y1 = y1 * display_scale * scale_factor
        canvas_x2 = x2 * display_scale * scale_factor
        canvas_y2 = y2 * display_scale * scale_factor

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

    def find_box_at_position(self, canvas_x, canvas_y, display_scale, scale_factor):
        """
        Encontra uma bounding box que contém a posição fornecida.

        Args:
            canvas_x: Coordenada X no canvas
            canvas_y: Coordenada Y no canvas
            display_scale: Escala de exibição da imagem
            scale_factor: Fator de escala atual (zoom)

        Returns:
            Índice da bounding box ou None se nenhuma for encontrada
        """
        for i, (_, x1, y1, x2, y2) in enumerate(self.boxes):
            # Converter para coordenadas do canvas
            canvas_x1 = x1 * display_scale * scale_factor
            canvas_y1 = y1 * display_scale * scale_factor
            canvas_x2 = x2 * display_scale * scale_factor
            canvas_y2 = y2 * display_scale * scale_factor

            # Verificar se o ponto está dentro da caixa
            if canvas_x1 <= canvas_x <= canvas_x2 and canvas_y1 <= canvas_y <= canvas_y2:
                return i

        return None

    def get_box_count(self):
        """
        Retorna o número de bounding boxes.

        Returns:
            Número de bounding boxes
        """
        return len(self.boxes)

    def get_all_boxes(self):
        """
        Retorna todas as bounding boxes.

        Returns:
            Lista de tuplas (class_id, x1, y1, x2, y2)
        """
        return self.boxes.copy()