"""
Manipuladores de eventos de mouse para a interface de anotação.
"""

import logging

from microdetect.annotation.annotator.ui.base import is_window_valid
from microdetect.annotation.annotator.utils.constants import HANDLE_NONE

logger = logging.getLogger(__name__)


class MouseHandler:
    """
    Gerencia eventos de mouse na interface de anotação.
    """

    def __init__(self, canvas, box_manager, annotation_visualizer, callbacks=None):
        """
        Inicializa o manipulador de mouse.

        Args:
            canvas: Canvas do Tkinter
            box_manager: Gerenciador de bounding boxes
            annotation_visualizer: Visualizador de anotações
            callbacks: Dicionário de callbacks para eventos específicos
        """
        self.canvas = canvas
        self.box_manager = box_manager
        self.visualizer = annotation_visualizer

        # Configurações de estado
        self.start_x = None
        self.start_y = None
        self.current_rect_id = None
        self.edit_mode = False
        self.pan_mode = False

        # Configurações de escala
        self.display_scale = 1.0
        self.scale_factor = 1.0
        self.original_w = 0
        self.original_h = 0

        # Callbacks externos
        self.callbacks = callbacks or {}

        # Atribuir manipuladores de eventos
        self._setup_event_handlers()

    def _setup_event_handlers(self):
        """Configura os manipuladores de eventos de mouse."""
        self.canvas.bind("<ButtonPress-1>", self.on_mouse_down)
        self.canvas.bind("<B1-Motion>", self.on_mouse_move)
        self.canvas.bind("<ButtonRelease-1>", self.on_mouse_up)

        # Eventos para zoom
        self.canvas.bind("<MouseWheel>", self.on_mouse_wheel)  # Windows
        self.canvas.bind("<Button-4>", self.on_mouse_wheel)  # Linux: scroll up
        self.canvas.bind("<Button-5>", self.on_mouse_wheel)  # Linux: scroll down

        # Eventos para pan
        self.canvas.bind("<ButtonPress-2>", self.on_middle_press)
        self.canvas.bind("<B2-Motion>", self.on_middle_drag)
        self.canvas.bind("<ButtonPress-3>", self.on_right_press)
        self.canvas.bind("<B3-Motion>", self.on_right_drag)

    def set_config(self, display_scale, scale_factor, original_w, original_h):
        """
        Atualiza as configurações de escala.

        Args:
            display_scale: Escala de exibição inicial
            scale_factor: Fator de escala atual (zoom)
            original_w: Largura original da imagem
            original_h: Altura original da imagem
        """
        self.display_scale = display_scale
        self.scale_factor = scale_factor
        self.original_w = original_w
        self.original_h = original_h

    def set_mode(self, edit_mode, pan_mode):
        """
        Define os modos de operação.

        Args:
            edit_mode: Se True, ativa o modo de edição
            pan_mode: Se True, ativa o modo de navegação (pan)
        """
        self.edit_mode = edit_mode
        self.pan_mode = pan_mode

    def _call_callback(self, name, *args, **kwargs):
        """
        Chama um callback pelo nome, se existir.

        Args:
            name: Nome do callback
            *args, **kwargs: Argumentos para o callback
        """
        if name in self.callbacks and callable(self.callbacks[name]):
            return self.callbacks[name](*args, **kwargs)

    def reset(self):
        """Reseta o estado do manipulador."""
        self.start_x = None
        self.start_y = None
        if self.current_rect_id:
            try:
                self.canvas.delete(self.current_rect_id)
            except:
                pass
        self.current_rect_id = None

    def on_mouse_down(self, event):
        """
        Função chamada quando o botão do mouse é pressionado.

        Args:
            event: Evento de mouse
        """
        if not is_window_valid(self.canvas):
            return

        try:
            # Modo de navegação: iniciar o pan
            if self.pan_mode:
                self.canvas.scan_mark(event.x, event.y)
                return

            # Limpar qualquer retângulo temporário existente
            if self.current_rect_id:
                self.canvas.delete(self.current_rect_id)
                self.current_rect_id = None

            # Obter coordenadas do canvas
            canvas_x = self.canvas.canvasx(event.x)
            canvas_y = self.canvas.canvasy(event.y)

            # Resetar o estado de resize
            self.box_manager.resize_handle = HANDLE_NONE

            # Modo de edição
            if self.edit_mode:
                selected_idx = self.box_manager.selected_idx

                # Verificar se clicou em uma alça de redimensionamento
                if selected_idx is not None:
                    resize_handle = self.box_manager.detect_resize_handle(
                        canvas_x, canvas_y, selected_idx,
                        self.display_scale, self.scale_factor
                    )

                    if resize_handle != HANDLE_NONE:
                        # Salvar posição inicial para histórico
                        self.start_x, self.start_y = canvas_x, canvas_y

                        self.box_manager.resize_handle = resize_handle
                        if selected_idx < self.box_manager.get_box_count():
                            self.box_manager.original_box_state = self.box_manager.get_box(selected_idx)
                            self._call_callback('update_status', f"Redimensionando caixa {selected_idx + 1}")
                        return

                # Procurar se clicou em uma caixa para selecionar
                box_idx = self.box_manager.find_box_at_position(
                    canvas_x, canvas_y, self.display_scale, self.scale_factor
                )

                if box_idx is not None:
                    self.box_manager.select_box(box_idx)
                    self.start_x, self.start_y = canvas_x, canvas_y
                    self.box_manager.original_box_state = self.box_manager.get_box(box_idx)
                    self._call_callback('update_status', f"Caixa {box_idx + 1} selecionada para edição")
                    self.visualizer.draw_bounding_boxes(
                        self.box_manager.get_all_boxes(),
                        highlight_idx=box_idx,
                        display_scale=self.display_scale,
                        scale_factor=self.scale_factor
                    )
                else:
                    # Se não selecionou nenhuma caixa, desselecionar
                    self.box_manager.select_box(None)
                    self.visualizer.draw_bounding_boxes(
                        self.box_manager.get_all_boxes(),
                        display_scale=self.display_scale,
                        scale_factor=self.scale_factor
                    )
                    # Importante: ainda salvar as coordenadas iniciais mesmo no modo de edição
                    self.start_x, self.start_y = canvas_x, canvas_y
            else:
                # Modo de desenho normal - salvar posição inicial
                self.start_x, self.start_y = canvas_x, canvas_y

            self._call_callback('reset_window_closed')
        except Exception as e:
            logger.error(f"Erro em on_mouse_down: {e}")

    def on_mouse_move(self, event):
        """
        Função chamada quando o mouse é movido com o botão pressionado.

        Args:
            event: Evento de mouse
        """
        if not is_window_valid(self.canvas):
            return

        try:
            # Pan mode
            if self.pan_mode:
                self.canvas.scan_dragto(event.x, event.y, gain=1)
                return

            # Precisamos ter uma posição inicial
            if self.start_x is None or self.start_y is None:
                return

            # Obter coordenadas do canvas
            canvas_x = self.canvas.canvasx(event.x)
            canvas_y = self.canvas.canvasy(event.y)

            # Modo de edição com caixa selecionada
            if self.edit_mode and self.box_manager.selected_idx is not None:
                # Obter caixa atual
                box_idx = self.box_manager.selected_idx
                box = self.box_manager.get_box(box_idx)
                if not box:
                    return

                cls_id, x1, y1, x2, y2 = box

                # Converter diferença para coordenadas originais
                orig_dx = (canvas_x - self.start_x) / (self.display_scale * self.scale_factor)
                orig_dy = (canvas_y - self.start_y) / (self.display_scale * self.scale_factor)

                # Redimensionamento
                if self.box_manager.resize_handle != HANDLE_NONE:
                    # Atualizar coordenadas baseado na alça selecionada
                    self._handle_resize(cls_id, x1, y1, x2, y2, orig_dx, orig_dy)
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
                self.box_manager.update_box(box_idx, cls_id, x1, y1, x2, y2)

                # Atualizar posição inicial
                self.start_x, self.start_y = canvas_x, canvas_y

                # Redesenhar
                self.visualizer.draw_bounding_boxes(
                    self.box_manager.get_all_boxes(),
                    highlight_idx=box_idx,
                    display_scale=self.display_scale,
                    scale_factor=self.scale_factor
                )
            else:
                # Desenhar retângulo temporário
                self.current_rect_id = self.visualizer.draw_temporary_box(
                    self.start_x, self.start_y, canvas_x, canvas_y,
                    temp_id=self.current_rect_id
                )

            self._call_callback('reset_window_closed')
        except Exception as e:
            logger.error(f"Erro em on_mouse_move: {e}")

    def _handle_resize(self, cls_id, x1, y1, x2, y2, dx, dy):
        """
        Manipula o redimensionamento de uma caixa.

        Args:
            cls_id: ID da classe
            x1, y1, x2, y2: Coordenadas atuais da caixa
            dx, dy: Deslocamento nas coordenadas
        """
        resize_handle = self.box_manager.resize_handle

        # Atualizar coordenadas baseado na alça selecionada
        if resize_handle == 1:  # HANDLE_NW
            x1 += dx
            y1 += dy
        elif resize_handle == 2:  # HANDLE_NE
            x2 += dx
            y1 += dy
        elif resize_handle == 3:  # HANDLE_SE
            x2 += dx
            y2 += dy
        elif resize_handle == 4:  # HANDLE_SW
            x1 += dx
            y2 += dy
        elif resize_handle == 5:  # HANDLE_N
            y1 += dy
        elif resize_handle == 6:  # HANDLE_E
            x2 += dx
        elif resize_handle == 7:  # HANDLE_S
            y2 += dy
        elif resize_handle == 8:  # HANDLE_W
            x1 += dx

    def on_mouse_up(self, event):
        """
        Função chamada quando o botão do mouse é solto.

        Args:
            event: Evento de mouse
        """
        if not is_window_valid(self.canvas):
            return

        try:
            # Verificações iniciais
            if self.pan_mode:
                return

            # Precisamos ter uma posição inicial
            if self.start_x is None or self.start_y is None:
                return

            # Obter coordenadas do canvas
            canvas_x = self.canvas.canvasx(event.x)
            canvas_y = self.canvas.canvasy(event.y)

            # CASO 1: Modo de edição com uma caixa selecionada
            if self.edit_mode and self.box_manager.selected_idx is not None:
                box_idx = self.box_manager.selected_idx

                # Finalizar redimensionamento ou movimentação
                if self.box_manager.resize_handle != HANDLE_NONE:
                    # Registrar ação no histórico
                    if self.box_manager.original_box_state:
                        current_box = self.box_manager.get_box(box_idx)
                        self._call_callback(
                            'add_to_history',
                            "resize",
                            {"index": box_idx, "before": self.box_manager.original_box_state, "after": current_box}
                        )
                    self._call_callback('update_status', f"Caixa {box_idx + 1} redimensionada")
                    self.box_manager.resize_handle = HANDLE_NONE
                else:
                    # Foi movimento simples
                    if self.box_manager.original_box_state:
                        current_box = self.box_manager.get_box(box_idx)
                        self._call_callback(
                            'add_to_history',
                            "move",
                            {"index": box_idx, "before": self.box_manager.original_box_state, "after": current_box}
                        )
                    self._call_callback('update_status', f"Caixa {box_idx + 1} reposicionada")

                # Reset estado para novas ações
                self.box_manager.original_box_state = None

            # CASO 2: Modo de desenho ou edição sem caixa selecionada - criar nova caixa
            elif abs(self.start_x - canvas_x) > 5 and abs(self.start_y - canvas_y) > 5:
                # Converter para coordenadas originais
                x1 = min(self.start_x, canvas_x) / (self.display_scale * self.scale_factor)
                y1 = min(self.start_y, canvas_y) / (self.display_scale * self.scale_factor)
                x2 = max(self.start_x, canvas_x) / (self.display_scale * self.scale_factor)
                y2 = max(self.start_y, canvas_y) / (self.display_scale * self.scale_factor)

                # Garantir limites da imagem
                x1 = max(0, min(x1, self.original_w))
                y1 = max(0, min(y1, self.original_h))
                x2 = max(0, min(x2, self.original_w))
                y2 = max(0, min(y2, self.original_h))

                # Obter índice da classe
                current_class = self._call_callback('get_current_class')
                if current_class:
                    class_id = current_class.split("-")[0]

                    # Adicionar à lista de bounding boxes
                    box_idx = self.box_manager.add_box(class_id, int(x1), int(y1), int(x2), int(y2))

                    # Adicionar ao histórico
                    self._call_callback('add_to_history', "add", {"index": box_idx})

                    # Atualizar status
                    self._call_callback('update_status', f"Box adicionada: {current_class}")

                    # Auto-save se necessário
                    self._call_callback('check_auto_save')

            # Limpar o retângulo temporário
            if self.current_rect_id:
                self.canvas.delete(self.current_rect_id)
                self.current_rect_id = None

            # Redesenhar todas as caixas
            self.visualizer.draw_bounding_boxes(
                self.box_manager.get_all_boxes(),
                highlight_idx=self.box_manager.selected_idx if self.edit_mode else None,
                display_scale=self.display_scale,
                scale_factor=self.scale_factor
            )

            # Redefinir os pontos iniciais para permitir novas boxes
            self.start_x = None
            self.start_y = None

            self._call_callback('reset_window_closed')
        except Exception as e:
            logger.error(f"Erro em on_mouse_up: {e}")

    def on_mouse_wheel(self, event):
        """
        Manipula eventos de zoom com a roda do mouse.

        Args:
            event: Evento de mouse
        """
        if not is_window_valid(self.canvas):
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
                # Solicitar redimensionamento da imagem
                self._call_callback('redraw_with_zoom', self.scale_factor)

                # Redesenhar as caixas com o novo zoom
                self.visualizer.draw_bounding_boxes(
                    self.box_manager.get_all_boxes(),
                    highlight_idx=self.box_manager.selected_idx if self.edit_mode else None,
                    display_scale=self.display_scale,
                    scale_factor=self.scale_factor
                )

            self._call_callback('reset_window_closed')
        except Exception as e:
            logger.error(f"Erro ao aplicar zoom: {e}")

    def on_middle_press(self, event):
        """
        Inicia o movimento de arrastar com o botão do meio.

        Args:
            event: Evento de mouse
        """
        if not is_window_valid(self.canvas):
            return

        try:
            self.canvas.scan_mark(event.x, event.y)
            self._call_callback('reset_window_closed')
        except Exception as e:
            logger.error(f"Erro ao iniciar pan: {e}")

    def on_middle_drag(self, event):
        """
        Executa o movimento de arrastar com o botão do meio.

        Args:
            event: Evento de mouse
        """
        if not is_window_valid(self.canvas):
            return

        try:
            self.canvas.scan_dragto(event.x, event.y, gain=1)
            self._call_callback('reset_window_closed')
        except Exception as e:
            logger.error(f"Erro ao realizar pan: {e}")

    def on_right_press(self, event):
        """
        Inicia o movimento de arrastar com o botão direito.

        Args:
            event: Evento de mouse
        """
        self.on_middle_press(event)

    def on_right_drag(self, event):
        """
        Executa o movimento de arrastar com o botão direito.

        Args:
            event: Evento de mouse
        """
        self.on_middle_drag(event)