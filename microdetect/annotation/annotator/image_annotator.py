"""
Classe principal para anotação manual de imagens.
Orquestra todos os componentes do sistema de anotação.
"""

import os
import glob
import logging
import time
import tkinter as tk
from tkinter import messagebox
from typing import List, Optional, Tuple, Dict, Any, Callable

from microdetect.annotation.export_import import create_export_import_ui
from microdetect.utils.config import config

from microdetect.annotation.annotator.ui import (
    MainWindow, SearchDialog, StatisticsDialog, is_window_valid
)
from microdetect.annotation.annotator.handlers import (
    ActionHistory, KeyboardHandler, MouseHandler
)
from microdetect.annotation.annotator.image import (
    ImageLoader, ImageProcessor
)
from microdetect.annotation.annotator.annotation import (
    BoundingBoxManager, AnnotationStorage, AnnotationVisualizer
)
from microdetect.annotation.annotator.suggestions import SuggestionGenerator
from microdetect.annotation.annotator.utils import (
    DEFAULT_AUTO_SAVE, DEFAULT_AUTO_SAVE_INTERVAL,
    AnnotationBackup, ProgressManager
)

logger = logging.getLogger(__name__)

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
        self.current_output_dir = None  # Diretório de saída para as anotações
        self.classes = classes or config.get("classes", ["0-levedura", "1-fungo", "2-micro-alga"])
        self.progress_file = ".annotation_progress.json"
        self.auto_save = auto_save
        self.auto_save_interval = auto_save_interval
        self.last_save_time = time.time()

        # Estado para controle de fluxo
        self.window_closed = False
        self.user_cancelled = False
        self.next_image_requested = False


        # Estado para controle de fluxo
        self.window_closed = False
        self.user_cancelled = False
        self.next_image_requested = False

        # Dimensões e escalas
        self.original_w = 0
        self.original_h = 0
        self.display_w = 0
        self.display_h = 0
        self.display_scale = 1.0
        self.scale_factor = 1.0

        # Componentes que serão inicializados durante a anotação
        self.box_manager = None
        self.action_history = None
        self.image_loader = None
        self.image_processor = None
        self.annotation_storage = None
        self.suggestion_generator = None
        self.annotation_backup = None
        self.progress_manager = None

        # Interface
        self.main_window = None
        self.canvas = None
        self.root = None
        self.class_var = None
        self.mouse_handler = None
        self.keyboard_handler = None

        # Estado de sugestões
        self.suggestion_mode = False
        self.suggested_boxes = []

        # Controle de modos
        self.edit_mode = False
        self.pan_mode = False

        # Lista para rastrear timers ativos
        self.active_timer_ids = []

    def _initialize_components(self):
        """Inicializa todos os componentes necessários para a anotação."""
        # Componentes de dados e lógica
        self.box_manager = BoundingBoxManager()
        self.action_history = ActionHistory()
        self.image_loader = ImageLoader()
        self.image_processor = ImageProcessor()
        self.annotation_storage = AnnotationStorage(self.progress_file)
        self.suggestion_generator = SuggestionGenerator(self.classes)
        self.annotation_backup = AnnotationBackup(self.progress_file)
        self.progress_manager = ProgressManager(self.progress_file)

        # Reset de estados
        self.window_closed = False
        self.user_cancelled = False
        self.next_image_requested = False
        self.edit_mode = False
        self.pan_mode = False

    def _create_callbacks(self) -> Dict[str, Callable]:
        """
        Cria dicionário de callbacks para os diversos componentes.

        Returns:
            Dicionário de callbacks
        """
        return {
            # Estados e modos
            'reset_window_closed': self._reset_window_closed,
            'get_current_class': self._get_current_class,
            'set_current_class': self._set_current_class,
            'toggle_edit_mode': self.toggle_edit_mode,
            'toggle_pan_mode': self.toggle_pan_mode,
            'select_none': self._select_none,

            # Ações de edição
            'undo': self.undo,
            'delete_selected': self.delete_selected,
            'reset': self.reset_boxes,
            'add_to_history': self._add_to_history,

            # Ações de zoom e visualização
            'reset_zoom': self.reset_zoom,
            'redraw_with_zoom': self._redraw_with_zoom,

            # Salvamento
            'save': self.save,
            'save_and_exit': self.save_and_exit,
            'save_and_next': self.save_and_next,
            'check_auto_save': self._check_auto_save,

            # Navegação de classes
            'cycle_classes': self.cycle_classes,

            # Diálogos
            'show_statistics': self.show_statistics,
            'show_search_dialog': self._show_search_dialog,
            'show_export_import': self._show_export_import,

            # Sugestões automáticas
            'toggle_suggestion_mode': self.toggle_suggestion_mode,
            'apply_suggestions': self.apply_suggested_annotations,

            # Interface
            'update_status': self.update_status,
            'on_closing': self.on_closing
        }

    def _reset_window_closed(self):
        """Reseta o flag window_closed para False."""
        if self.canvas and is_window_valid(self.canvas):
            self.window_closed = False
            return True
        return False

    def _get_current_class(self):
        """
        Obtém a classe atual selecionada.

        Returns:
            String representando a classe atual
        """
        if self.class_var:
            return self.class_var.get()
        return self.classes[0] if self.classes else "0-levedura"

    def _set_current_class(self, event=None):
        """Atualiza a interface quando a classe atual é alterada."""
        self.update_status()

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

        os.makedirs(output_dir, exist_ok=True)

        # Inicializar componentes
        self._initialize_components()

        # Armazenar referências à imagem atual e diretório de saída
        self.current_image_path = image_path
        self.current_output_dir = output_dir  # Armazenar diretório de saída

        # Iniciar sessão de anotação
        self.progress_manager.start_session(output_dir)

        # Armazenar referência à imagem atual
        self.current_image_path = image_path

        # Carregar imagem
        img, w, h = self.image_loader.load_image(image_path)
        if img is None:
            logger.error(f"Não foi possível carregar a imagem: {image_path}")
            return None

        self.original_w, self.original_h = w, h

        # Dimensionar imagem se muito grande
        img_display, scale = self.image_processor.resize_image(img)
        self.display_w, self.display_h = img_display.shape[1], img_display.shape[0]
        self.display_scale = scale
        self.scale_factor = 1.0  # Reset do fator de zoom

        # Verificar se já existem anotações para esta imagem
        base_name = os.path.splitext(os.path.basename(image_path))[0]

        # Carregar anotações existentes
        boxes = self.annotation_storage.load_annotations(
            os.path.join(output_dir, f"{base_name}.txt"),
            self.original_w,
            self.original_h
        )

        # Adicionar as caixas carregadas ao gerenciador
        for box in boxes:
            self.box_manager.add_box(*box)

        # Criar callbacks para componentes
        callbacks = self._create_callbacks()

        # Criar a janela principal
        self.main_window = MainWindow(image_path, self.classes, callbacks)
        self.root, self.canvas, self.class_var, status_label = self.main_window.create()

        # Atualizar informações da imagem na interface
        self.main_window.update_image_info(w, h)

        # Criar e configurar manipuladores de eventos
        self.mouse_handler = MouseHandler(
            self.canvas,
            self.box_manager,
            AnnotationVisualizer(self.canvas, self.classes),
            callbacks
        )

        # Configurar escalas no manipulador de mouse
        self.mouse_handler.set_config(self.display_scale, self.scale_factor, self.original_w, self.original_h)

        # Configurar atalhos de teclado
        self.keyboard_handler = KeyboardHandler(self.root, callbacks)

        # Converter a imagem para formato Tkinter e desenhar no canvas
        self.image_loader.create_tkinter_image(img_display)
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.image_loader.current_img_tk, tags="background")
        self.canvas.config(scrollregion=self.canvas.bbox(tk.ALL))

        # Desenhar as bounding boxes existentes
        redraw = AnnotationVisualizer(self.canvas, self.classes)
        redraw.draw_bounding_boxes(
            self.box_manager.get_all_boxes(),
            display_scale=self.display_scale,
            scale_factor=self.scale_factor
        )

        # Atualizar contador na interface
        self.update_status(box_count=self.box_manager.get_box_count())

        # Resultado da anotação (será definido durante o processo)
        annotation_path = None

        # Iniciar timers para monitoramento e auto-save
        timer_id = self.root.after(1000, self._monitor_window_state)
        self.active_timer_ids.append(timer_id)

        if self.auto_save:
            timer_id = self.root.after(10000, self._auto_save_timer)
            self.active_timer_ids.append(timer_id)

        # Iniciar loop principal
        self.main_window.start_main_loop()

        # Garantir limpeza de timers ao sair
        self._cleanup_timers()

        # Finalizar sessão e registrar estatísticas
        if not self.user_cancelled:
            self.progress_manager.increment_session_count(output_dir)
        session_stats = self.progress_manager.end_session(output_dir)

        # Retornar o caminho da anotação se existir
        if os.path.exists(os.path.join(output_dir, f"{base_name}.txt")):
            return os.path.join(output_dir, f"{base_name}.txt")

        return None

    def _monitor_window_state(self):
        """Monitora periodicamente o estado da janela e corrige se necessário."""
        try:
            if self.window_closed and self.root and self.root.winfo_exists():
                logger.debug("Detectada inconsistência - window_closed é True, mas a janela existe!")
                self.window_closed = False

            # Continuar monitorando se a janela ainda existir
            if self.root and self.root.winfo_exists():
                timer_id = self.root.after(1000, self._monitor_window_state)
                self.active_timer_ids.append(timer_id)
        except:
            # Se falhar, a janela provavelmente já foi fechada
            self.window_closed = True

    def _auto_save_timer(self):
        """Verifica periodicamente se é hora de auto-salvar."""
        if self.window_closed:
            return

        try:
            self._check_auto_save()

            if self.root and self.root.winfo_exists():
                timer_id = self.root.after(10000, self._auto_save_timer)
                self.active_timer_ids.append(timer_id)
        except Exception as e:
            # Em caso de erro, apenas logar e continuar
            logger.error(f"Erro no auto-save: {e}")
            # Tentar programar o próximo auto-save mesmo com erro
            try:
                if self.root and self.root.winfo_exists():
                    timer_id = self.root.after(10000, self._auto_save_timer)
                    self.active_timer_ids.append(timer_id)
            except:
                pass

    def _cleanup_timers(self):
        """Cancela todos os timers pendentes da interface."""
        try:
            for timer_id in self.active_timer_ids[:]:
                try:
                    if self.root and self.root.winfo_exists():
                        self.root.after_cancel(timer_id)
                    self.active_timer_ids.remove(timer_id)
                except Exception as e:
                    logger.debug(f"Erro ao cancelar timer: {e}")
                    # Continuar mesmo com erro
        except Exception as e:
            logger.debug(f"Erro ao limpar timers: {e}")

    def _check_auto_save(self):
        """
        Verifica se é hora de auto-salvar e salva se necessário.

        Returns:
            True se o salvamento automático foi realizado
        """
        if not self.auto_save:
            return False

        current_time = time.time()
        if current_time - self.last_save_time > self.auto_save_interval:
            # Obter nome base do arquivo
            base_name = os.path.splitext(os.path.basename(self.current_image_path))[0]

            # Usar o diretório de saída correto
            output_dir = self.current_output_dir
            if not output_dir:  # Fallback para diretório da imagem se não estiver definido
                output_dir = os.path.dirname(self.current_image_path)
                logger.warning(f"Auto-save: Diretório de saída não definido, usando diretório da imagem: {output_dir}")

            # Salvar anotações
            self.annotation_storage.save_annotations(
                self.box_manager.get_all_boxes(),
                output_dir,
                base_name,
                self.original_w,
                self.original_h
            )

            # Registrar progresso
            self.progress_manager.save_progress(
                output_dir,
                self.current_image_path,
                {"last_auto_save": current_time}
            )

            self.last_save_time = current_time
            self.update_status("Auto-save realizado")
            return True
        return False

    def _add_to_history(self, action_type, data):
        """
        Adiciona uma ação ao histórico para suportar desfazer (undo).

        Args:
            action_type: Tipo da ação ('add', 'move', 'resize', 'delete')
            data: Dados específicos da ação
        """
        self.action_history.add(action_type, data)

    def update_status(self, msg=None, box_count=None):
        """
        Atualiza o status na interface com proteção contra erros.

        Args:
            msg: Mensagem a ser exibida (opcional)
            box_count: Número de caixas (opcional)
        """
        # Se box_count não for fornecido, usar contagem atual
        if box_count is None and hasattr(self, 'box_manager'):
            box_count = self.box_manager.get_box_count()

        # Atualizar interface
        if hasattr(self, 'main_window'):
            self.main_window.update_status(msg, box_count)

    def toggle_edit_mode(self):
        """Alterna entre os modos de edição e desenho."""
        self.edit_mode = not self.edit_mode
        self.pan_mode = False  # Desativar navegação ao ativar edição

        # Resetar estado
        if hasattr(self, 'box_manager'):
            self.box_manager.select_box(None)
            self.box_manager.resize_handle = 0

        # Atualizar interface
        button_manager = self.main_window.get_button_manager()
        button_manager.update_button_state(
            'edit_mode',
            text="Modo Desenho (E)" if self.edit_mode else "Modo Edição (E)",
            bg="lightblue" if self.edit_mode else "#f0f0f0"
        )

        # Atualizar modo no manipulador de mouse
        if hasattr(self, 'mouse_handler'):
            self.mouse_handler.set_mode(self.edit_mode, self.pan_mode)

        self.update_status()

        # Redesenhar caixas
        if hasattr(self, 'canvas') and hasattr(self, 'box_manager'):
            visualizer = AnnotationVisualizer(self.canvas, self.classes)
            visualizer.draw_bounding_boxes(
                self.box_manager.get_all_boxes(),
                display_scale=self.display_scale,
                scale_factor=self.scale_factor
            )

    def toggle_pan_mode(self):
        """Alterna entre o modo de navegação e desenho/edição."""
        self.pan_mode = not self.pan_mode

        if self.pan_mode:
            self.edit_mode = False  # Desativar edição ao ativar navegação

        # Atualizar interface
        button_manager = self.main_window.get_button_manager()
        button_manager.update_button_state(
            'pan_mode',
            text="Modo Desenho (P)" if self.pan_mode else "Modo Navegação (P)",
            bg="lightblue" if self.pan_mode else "#f0f0f0"
        )

        # Atualizar modo no manipulador de mouse
        if hasattr(self, 'mouse_handler'):
            self.mouse_handler.set_mode(self.edit_mode, self.pan_mode)

        self.update_status()

    def _select_none(self, event=None):
        """Desseleciona qualquer caixa selecionada."""
        if hasattr(self, 'box_manager') and hasattr(self, 'canvas'):
            self.box_manager.select_box(None)

            # Redesenhar
            visualizer = AnnotationVisualizer(self.canvas, self.classes)
            visualizer.draw_bounding_boxes(
                self.box_manager.get_all_boxes(),
                display_scale=self.display_scale,
                scale_factor=self.scale_factor
            )

            self.update_status()

    def cycle_classes(self, event=None):
        """Alterna entre as classes disponíveis."""
        if hasattr(self, 'class_var') and self.classes:
            current_idx = self.classes.index(self.class_var.get()) if self.class_var.get() in self.classes else 0
            next_idx = (current_idx + 1) % len(self.classes)
            self.class_var.set(self.classes[next_idx])
            self.update_status(f"Classe selecionada: {self.classes[next_idx]}")

    def undo(self, event=None):
        """Desfaz a última ação."""
        if not hasattr(self, 'action_history') or not hasattr(self, 'box_manager'):
            return

        if self.action_history.is_empty():
            self.update_status("Nada para desfazer.")
            return

        last_action = self.action_history.undo()
        if not last_action:
            return

        action_type = last_action.get("type")
        data = last_action.get("data", {})

        if action_type == "add":
            if data.get("index") < self.box_manager.get_box_count():
                self.box_manager.remove_box(data.get("index"))
                self.update_status("Desfez: Adição de caixa")
        elif action_type == "move" or action_type == "resize":
            if data.get("index") < self.box_manager.get_box_count():
                before_box = data.get("before")
                if before_box:
                    self.box_manager.update_box(
                        data.get("index"),
                        before_box[0], before_box[1], before_box[2], before_box[3], before_box[4]
                    )
                    self.update_status(
                        f"Desfez: {'Movimentação' if action_type == 'move' else 'Redimensionamento'} de caixa"
                    )
        elif action_type == "delete":
            box = data.get("box")
            if box:
                idx = self.box_manager.add_box(*box) if isinstance(box, tuple) else -1
                if idx >= 0:
                    self.update_status("Desfez: Exclusão de caixa")

        # Redesenhar
        if hasattr(self, 'canvas'):
            visualizer = AnnotationVisualizer(self.canvas, self.classes)
            visualizer.draw_bounding_boxes(
                self.box_manager.get_all_boxes(),
                highlight_idx=self.box_manager.selected_idx if self.edit_mode else None,
                display_scale=self.display_scale,
                scale_factor=self.scale_factor
            )

    def delete_selected(self, event=None):
        """Remove a caixa selecionada ou a última caixa."""
        if not hasattr(self, 'box_manager'):
            return

        # Remover caixa selecionada ou a última
        if self.edit_mode and self.box_manager.selected_idx is not None:
            # Guardar para histórico
            removed_box = self.box_manager.get_box(self.box_manager.selected_idx)
            removed_index = self.box_manager.selected_idx

            if removed_box:
                self._add_to_history("delete", {"index": removed_index, "box": removed_box})

                # Remover caixa
                self.box_manager.remove_box(removed_index)
                self.update_status(f"Caixa {removed_index + 1} excluída")
        elif self.box_manager.get_box_count() > 0:
            # Remover última caixa
            removed_index = self.box_manager.get_box_count() - 1
            removed_box = self.box_manager.get_box(removed_index)

            if removed_box:
                self._add_to_history("delete", {"index": removed_index, "box": removed_box})

                # Remover caixa
                self.box_manager.remove_box(removed_index)
                self.update_status(f"Última caixa excluída. Restantes: {self.box_manager.get_box_count()}")
        else:
            self.update_status("Nenhuma caixa para excluir")
            return

        # Redesenhar
        if hasattr(self, 'canvas'):
            visualizer = AnnotationVisualizer(self.canvas, self.classes)
            visualizer.draw_bounding_boxes(
                self.box_manager.get_all_boxes(),
                highlight_idx=self.box_manager.selected_idx if self.edit_mode else None,
                display_scale=self.display_scale,
                scale_factor=self.scale_factor
            )

    def reset_boxes(self):
        """Remove todas as caixas."""
        if not hasattr(self, 'box_manager'):
            return

        if self.box_manager.get_box_count() == 0:
            self.update_status("Nenhuma caixa para limpar.")
            return

        # Confirmar reset
        if not messagebox.askyesno("Confirmação", "Tem certeza que deseja remover TODAS as caixas?"):
            return

        # Guardar todas para histórico
        for i, box in enumerate(self.box_manager.get_all_boxes()):
            self._add_to_history("delete", {"index": i, "box": box})

        # Limpar lista
        self.box_manager.clear_all()

        # Atualizar interface
        if hasattr(self, 'canvas'):
            visualizer = AnnotationVisualizer(self.canvas, self.classes)
            visualizer.clear_all()

        self.update_status("Todas as caixas foram removidas.")

    def reset_zoom(self, event=None):
        """Reinicia o zoom para escala normal."""
        if not hasattr(self, 'image_processor') or not hasattr(self, 'canvas'):
            return

        self.scale_factor = 1.0
        self._redraw_with_zoom(self.scale_factor)
        self.update_status("Zoom reiniciado")

    def _redraw_with_zoom(self, scale_factor):
        """
        Redesenha a imagem e as anotações com novo fator de zoom.

        Args:
            scale_factor: Novo fator de escala
        """
        if not hasattr(self, 'canvas') or not hasattr(self, 'image_loader'):
            return

        # Atualizar variável de instância
        self.scale_factor = scale_factor

        # Obter imagem original
        img, _, _ = self.image_loader.load_image(self.current_image_path)
        if img is None:
            return

        # Redimensionar para display inicial
        img_display, _ = self.image_processor.resize_image(img)

        # Aplicar zoom
        img_zoomed = self.image_processor.apply_zoom(img_display, scale_factor)

        # Redesenhar no canvas
        new_w, new_h = img_zoomed.shape[1], img_zoomed.shape[0]
        self.image_loader.create_tkinter_image(img_zoomed, key="zoomed_image")

        # Atualizar imagem no canvas
        self.canvas.delete("background")
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.image_loader.current_img_tk, tags="background")
        self.canvas.config(scrollregion=self.canvas.bbox(tk.ALL))

        # Atualizar manipulador de mouse com novas escalas
        if hasattr(self, 'mouse_handler'):
            self.mouse_handler.set_config(self.display_scale, self.scale_factor, self.original_w, self.original_h)

        # Redesenhar caixas
        visualizer = AnnotationVisualizer(self.canvas, self.classes)
        visualizer.draw_bounding_boxes(
            self.box_manager.get_all_boxes(),
            highlight_idx=self.box_manager.selected_idx if self.edit_mode else None,
            display_scale=self.display_scale,
            scale_factor=self.scale_factor
        )

        # Redesenhar sugestões se necessário
        if self.suggestion_mode and self.suggested_boxes:
            visualizer.draw_suggestions(
                self.suggested_boxes,
                self.display_scale,
                self.scale_factor
            )

    def save(self, event=None):
        """Salva as anotações."""
        if not hasattr(self, 'box_manager') or not hasattr(self, 'current_image_path'):
            return

        try:
            base_name = os.path.splitext(os.path.basename(self.current_image_path))[0]

            # Usar o diretório de saída correto definido no método annotate_image
            output_dir = self.current_output_dir
            if not output_dir:  # Fallback para diretório da imagem se não estiver definido
                output_dir = os.path.dirname(self.current_image_path)
                logger.warning(f"Diretório de saída não definido, usando diretório da imagem: {output_dir}")

            # Salvar anotações
            annotation_path = self.annotation_storage.save_annotations(
                self.box_manager.get_all_boxes(),
                output_dir,
                base_name,
                self.original_w,
                self.original_h
            )

            # Registrar progresso com dados adicionais
            self.progress_manager.save_progress(
                output_dir,
                self.current_image_path,
                {
                    "last_save": time.time(),
                    "box_count": self.box_manager.get_box_count()
                }
            )

            self.last_save_time = time.time()
            self.update_status(f"Anotações salvas em {annotation_path}")

            return annotation_path
        except Exception as e:
            logger.error(f"Erro ao salvar anotações: {e}")
            self.update_status(f"Erro ao salvar: {str(e)}")
            return None

    def save_and_exit(self, event=None):
        """Salva as anotações e sai."""
        try:
            self.save()
            self._cleanup_timers()  # Limpar timers antes de fechar
            self.user_cancelled = False  # Não queremos cancelar, apenas sair normalmente
            self.window_closed = True

            # Finalizar sessão e registrar estatísticas
            self.progress_manager.end_session(os.path.dirname(self.current_image_path))

            if hasattr(self, 'root') and self.root:
                self.root.destroy()
        except Exception as e:
            logger.error(f"Erro ao salvar e sair: {e}")
            self.window_closed = True
            self.user_cancelled = False

            try:
                self._cleanup_timers()  # Limpar timers como última tentativa
                if hasattr(self, 'root') and self.root:
                    self.root.destroy()
            except:
                pass

    def save_and_next(self, event=None):
        """Salva as anotações e sinaliza para avançar para a próxima imagem."""
        try:
            # Salvar anotações
            self.save()

            # Registrar progresso
            if hasattr(self, 'progress_manager'):
                self.progress_manager.increment_session_count(os.path.dirname(self.current_image_path))

            # Definir flags - FUNDAMENTAL para o funcionamento correto
            self.next_image_requested = True
            self.user_cancelled = False

            # Log para depuração
            logger.info("save_and_next: Definiu next_image_requested=True, fechando janela...")

            # Cancelar todos os timers pendentes
            self._cleanup_timers()

            # Limpar referências de imagem
            if hasattr(self, 'image_loader'):
                self.image_loader.cleanup_references()

            # Fechar a janela - CRÍTICO: fechar a janela, não o programa
            if hasattr(self, 'root') and self.root:
                self.root.destroy()

            logger.info("save_and_next: Janela fechada com sucesso!")

        except Exception as e:
            logger.error(f"Erro ao salvar e avançar: {str(e)}")
            # Mesmo com erro, tentar definir flags para continuar
            self.next_image_requested = True
            self.user_cancelled = False

            # Tentar fechar as janelas
            try:
                if hasattr(self, 'root') and self.root:
                    self.root.destroy()
            except:
                pass

    def on_closing(self, event=None):
        """Manipula o evento de fechamento da janela."""
        try:
            if hasattr(self, 'box_manager') and self.box_manager.get_box_count() > 0:
                if messagebox.askyesno("Sair", "Deseja salvar as anotações antes de sair?"):
                    self.save()

            # Limpar referências de imagem
            if hasattr(self, 'image_loader'):
                self.image_loader.cleanup_references()
        except:
            pass  # Ignorar erros durante o fechamento

        # Limpar timers antes de fechar
        self._cleanup_timers()

        # Definir flags de saída
        self.window_closed = True
        self.user_cancelled = True

        # Fechar a janela
        try:
            if hasattr(self, 'root') and self.root:
                self.root.destroy()
        except:
            pass

    def toggle_suggestion_mode(self):
        """
        Alterna o modo de sugestão automática.
        """
        self.suggestion_mode = not self.suggestion_mode

        if self.suggestion_mode:
            # Gerar sugestões para a imagem atual
            if hasattr(self, 'current_image_path') and self.current_image_path:
                self.suggested_boxes = self.suggestion_generator.generate_suggestions(self.current_image_path)

                # Mostrar as sugestões na interface
                if hasattr(self, 'canvas'):
                    visualizer = AnnotationVisualizer(self.canvas, self.classes)
                    visualizer.draw_suggestions(
                        self.suggested_boxes,
                        self.display_scale,
                        self.scale_factor
                    )

                self.update_status(f"Modo de sugestão ativado: {len(self.suggested_boxes)} sugestões disponíveis")

                # Habilitar botão de aplicar
                if hasattr(self, 'main_window'):
                    button_manager = self.main_window.get_button_manager()
                    button_manager.update_button_state('apply_suggestions', state=tk.NORMAL)
                    button_manager.update_button_state('suggestion',
                                                      bg="lightblue",
                                                      text="Desativar Sugestões (G)")
            else:
                self.update_status("Não foi possível gerar sugestões: imagem não encontrada")
                self.suggestion_mode = False
        else:
            # Limpar sugestões
            self.suggested_boxes = []

            # Remover visualização das sugestões
            if hasattr(self, 'canvas'):
                self.canvas.delete("suggestion")
                self.canvas.delete("suggestion_label")

                # Redesenhar as caixas normais
                visualizer = AnnotationVisualizer(self.canvas, self.classes)
                visualizer.draw_bounding_boxes(
                    self.box_manager.get_all_boxes(),
                    highlight_idx=self.box_manager.selected_idx if self.edit_mode else None,
                    display_scale=self.display_scale,
                    scale_factor=self.scale_factor
                )

            self.update_status("Modo de sugestão desativado")

            # Desabilitar botão de aplicar
            if hasattr(self, 'main_window'):
                button_manager = self.main_window.get_button_manager()
                button_manager.update_button_state('apply_suggestions', state=tk.DISABLED)
                button_manager.update_button_state('suggestion',
                                                   bg="#f0f0f0",
                                                   text="Sugestões Automáticas (G)")

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
            box_idx = self.box_manager.add_box(class_id, x1, y1, x2, y2)

            # Adicionar ao histórico
            self._add_to_history("add", {"index": box_idx})

        # Limpar as sugestões após aplicar
        suggestions_count = len(self.suggested_boxes)
        self.suggested_boxes = []

        # Atualizar interface
        if hasattr(self, 'canvas'):
            # Limpar sugestões visuais
            self.canvas.delete("suggestion")
            self.canvas.delete("suggestion_label")

            # Redesenhar todas as caixas
            visualizer = AnnotationVisualizer(self.canvas, self.classes)
            visualizer.draw_bounding_boxes(
                self.box_manager.get_all_boxes(),
                highlight_idx=self.box_manager.selected_idx if self.edit_mode else None,
                display_scale=self.display_scale,
                scale_factor=self.scale_factor
            )

        self.update_status(f"{suggestions_count} sugestões aplicadas com sucesso")

        # Desabilitar botão de aplicar
        if hasattr(self, 'main_window'):
            button_manager = self.main_window.get_button_manager()
            button_manager.update_button_state('apply_suggestions', state=tk.DISABLED)

        return True

    def show_statistics(self, output_dir=None):
        """
        Exibe um dashboard com estatísticas das anotações.

        Args:
            output_dir: Diretório contendo as anotações (usa diretório da imagem atual se None)
        """
        # Se output_dir não for fornecido, usar diretório da imagem atual
        if output_dir is None and hasattr(self, 'current_image_path'):
            output_dir = os.path.dirname(self.current_image_path)

        if not output_dir:
            self.update_status("Diretório de anotações não disponível.")
            return

        # Obter dados de progresso para as estatísticas
        progress_data = {}
        if hasattr(self, 'progress_manager'):
            stats = self.progress_manager.get_session_statistics(output_dir)
            annotated, total, percentage = self.progress_manager.calculate_progress(
                os.path.dirname(output_dir), output_dir
            )
            progress_data = {
                "session_stats": stats,
                "annotated_count": annotated,
                "total_images": total,
                "percentage": percentage
            }

        # Criar e mostrar o diálogo de estatísticas
        stats_dialog = StatisticsDialog(output_dir, self.classes, self.progress_file)
        stats_dialog.show()

    def _show_search_dialog(self):
        """
        Abre a interface de busca/filtro de imagens e permite navegar para uma imagem selecionada.
        """
        if not hasattr(self, 'current_image_path'):
            return

        # Armazenar referência à janela atual para depois
        current_window = self.root if hasattr(self, 'root') else None
        current_image_path = self.current_image_path

        # Verificar se há anotações não salvas na janela atual
        has_unsaved_annotations = False
        if hasattr(self, 'box_manager') and self.box_manager.get_box_count() > 0:
            has_unsaved_annotations = True

        # Obter imagens selecionadas
        image_dir = os.path.dirname(current_image_path)
        output_dir = self.current_output_dir or image_dir

        # Carregar último progresso
        last_annotated_path = None
        if hasattr(self, 'progress_manager'):
            last_annotated_path = self.progress_manager.get_last_annotated_image(output_dir)

        search_dialog = SearchDialog(image_dir, output_dir, last_annotated_path or current_image_path)
        selected_images, mode = search_dialog.show()

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
                    if should_save:
                        self.save()
                    else:
                        # Mesmo não salvando, finalizar sessão corretamente
                        if hasattr(self, 'progress_manager'):
                            self.progress_manager.end_session(output_dir)

                    # CRÍTICO: Cancelar todos os timers ativos antes de fechar a janela
                    self._cleanup_timers()

                    # IMPORTANTE: Salvar o caminho selecionado em uma variável local
                    # para evitar problemas de referência após destruir a janela
                    path_to_open = selected_path

                    # Limpar referências antes de fechar a janela atual
                    if hasattr(self, 'image_loader'):
                        self.image_loader.cleanup_references()

                    # Definir flag para encerrar a anotação atual
                    self.user_cancelled = True

                    # IMPORTANTE: Não queremos continuar para a próxima imagem automaticamente
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

    def _show_export_import(self):
        """
        Abre o diálogo de exportação/importação de anotações.
        """
        if not hasattr(self, 'current_image_path') or not hasattr(self, 'root'):
            return

        # Obter diretórios
        image_dir = os.path.dirname(self.current_image_path)
        output_dir = self.current_output_dir or image_dir

        # Abrir diálogo de exportação/importação
        create_export_import_ui(self.root, image_dir, output_dir)

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

        # Inicializar componentes
        self._initialize_components()

        # Verificar se há progresso salvo
        last_annotated_path = self.progress_manager.get_last_annotated_image(output_dir)

        # Criar backup antes de iniciar a anotação
        self.annotation_backup.create_backup(output_dir)

        # Iniciar nova sessão de anotação em lote
        self.progress_manager.start_session(output_dir)

        # Chamar o método de busca e filtro com o caminho da última imagem anotada
        search_dialog = SearchDialog(image_dir, output_dir, last_annotated_path)
        filtered_images, continuation_mode = search_dialog.show()

        if not filtered_images:
            logger.info("Nenhuma imagem selecionada para anotação. Encerrando.")
            self.progress_manager.end_session(output_dir)
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

                # Incrementar contador na sessão
                self.progress_manager.increment_session_count(output_dir)

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

        # Finalizar a sessão e obter estatísticas
        session_stats = self.progress_manager.end_session(output_dir)

        # Contar anotações por classe e obter total de objetos
        class_counts, total_objetos = self.annotation_storage.count_annotations_by_class(output_dir, self.classes)

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

        # Mostrar estatísticas de sessão, se disponíveis
        if 'session_summary' in session_stats:
            summary = session_stats['session_summary']
            print(f"\nTempo da sessão: {summary.get('duration_seconds', 0) // 60} minutos")
            print(f"Início: {summary.get('start_time', 'N/A')}")
            print(f"Término: {summary.get('end_time', 'N/A')}")

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

    def enhance_image(self, brightness=0, contrast=0, sharpen=0, denoise=False):
        """
        Aplica melhorias à imagem atual.

        Args:
            brightness: Ajuste de brilho (-100 a 100)
            contrast: Ajuste de contraste (-100 a 100)
            sharpen: Nível de nitidez (0 a 10)
            denoise: Se True, aplica redução de ruído

        Returns:
            True se as melhorias foram aplicadas com sucesso
        """
        if not hasattr(self, 'image_processor') or not hasattr(self, 'image_loader'):
            return False

        try:
            # Obter imagem original
            img, _, _ = self.image_loader.load_image(self.current_image_path)
            if img is None:
                return False

            # Redimensionar para exibição
            img_display, _ = self.image_processor.resize_image(img)

            # Aplicar filtros solicitados
            if denoise:
                img_display = self.image_processor.denoise_image(img_display)

            if brightness != 0 or contrast != 0:
                img_display = self.image_processor.apply_brightness_contrast(img_display, brightness, contrast)

            if sharpen > 0:
                img_display = self.image_processor.apply_sharpen(img_display, sharpen / 5.0)  # Normalizar para 0-2

            # Aplicar zoom atual
            if self.scale_factor != 1.0:
                img_display = self.image_processor.apply_zoom(img_display, self.scale_factor)

            # Atualizar imagem no canvas
            self.image_loader.create_tkinter_image(img_display)

            if hasattr(self, 'canvas'):
                self.canvas.delete("background")
                self.canvas.create_image(0, 0, anchor=tk.NW, image=self.image_loader.current_img_tk, tags="background")

                # Redesenhar caixas
                visualizer = AnnotationVisualizer(self.canvas, self.classes)
                visualizer.draw_bounding_boxes(
                    self.box_manager.get_all_boxes(),
                    highlight_idx=self.box_manager.selected_idx if self.edit_mode else None,
                    display_scale=self.display_scale,
                    scale_factor=self.scale_factor
                )

                # Redesenhar sugestões se necessário
                if self.suggestion_mode and self.suggested_boxes:
                    visualizer.draw_suggestions(
                        self.suggested_boxes,
                        self.display_scale,
                        self.scale_factor
                    )

            self.update_status("Imagem aprimorada aplicada")
            return True

        except Exception as e:
            logger.error(f"Erro ao aplicar melhorias à imagem: {e}")
            self.update_status(f"Erro ao aprimorar imagem: {str(e)}")
            return False

    def enhance_for_microscopy(self):
        """
        Aplica melhorias específicas para imagens de microscopia.

        Returns:
            True se as melhorias foram aplicadas com sucesso
        """
        if not hasattr(self, 'image_processor') or not hasattr(self, 'image_loader'):
            return False

        try:
            # Obter imagem original
            img, _, _ = self.image_loader.load_image(self.current_image_path)
            if img is None:
                return False

            # Redimensionar para exibição
            img_display, _ = self.image_processor.resize_image(img)

            # Aplicar melhorias para microscopia
            img_display = self.image_processor.enhance_contrast_for_microscopy(img_display)

            # Aplicar um pouco de nitidez
            img_display = self.image_processor.apply_sharpen(img_display, 0.8)

            # Aplicar zoom atual
            if self.scale_factor != 1.0:
                img_display = self.image_processor.apply_zoom(img_display, self.scale_factor)

            # Atualizar imagem no canvas
            self.image_loader.create_tkinter_image(img_display)

            if hasattr(self, 'canvas'):
                self.canvas.delete("background")
                self.canvas.create_image(0, 0, anchor=tk.NW, image=self.image_loader.current_img_tk, tags="background")

                # Redesenhar caixas
                visualizer = AnnotationVisualizer(self.canvas, self.classes)
                visualizer.draw_bounding_boxes(
                    self.box_manager.get_all_boxes(),
                    highlight_idx=self.box_manager.selected_idx if self.edit_mode else None,
                    display_scale=self.display_scale,
                    scale_factor=self.scale_factor
                )

                # Redesenhar sugestões se necessário
                if self.suggestion_mode and self.suggested_boxes:
                    visualizer.draw_suggestions(
                        self.suggested_boxes,
                        self.display_scale,
                        self.scale_factor
                    )

            self.update_status("Melhoria para microscopia aplicada")
            return True

        except Exception as e:
            logger.error(f"Erro ao aplicar melhorias para microscopia: {e}")
            self.update_status(f"Erro ao aprimorar imagem: {str(e)}")
            return False