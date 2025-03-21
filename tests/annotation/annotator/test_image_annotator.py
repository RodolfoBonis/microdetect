"""
Testes para a classe ImageAnnotator.
"""

import os
import tempfile
import time
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from microdetect.annotation.annotator.image_annotator import ImageAnnotator


class TestImageAnnotator:

    @pytest.fixture
    def temp_dir(self):
        """Cria diretórios temporários para testes."""
        with tempfile.TemporaryDirectory() as temp:
            # Criar subdiretórios para imagens e anotações
            images_dir = os.path.join(temp, "images")
            annotations_dir = os.path.join(temp, "annotations")
            os.makedirs(images_dir, exist_ok=True)
            os.makedirs(annotations_dir, exist_ok=True)

            yield temp, images_dir, annotations_dir

    @pytest.fixture
    def mock_image(self, temp_dir):
        """Cria uma imagem de teste."""
        _, images_dir, _ = temp_dir

        # Criar um arquivo de imagem de teste
        img_path = os.path.join(images_dir, "test_image.jpg")

        # Mock de gravação de imagem
        with patch("cv2.imwrite") as mock_imwrite:
            mock_imwrite.return_value = True
            yield img_path

    @pytest.fixture
    def annotator(self):
        """Cria uma instância de ImageAnnotator com mocks configurados."""
        classes = ["0-classe1", "1-classe2", "2-classe3"]

        with patch("microdetect.annotation.annotator.image_annotator.BoundingBoxManager"), patch(
            "microdetect.annotation.annotator.image_annotator.ActionHistory"
        ), patch("microdetect.annotation.annotator.image_annotator.ImageLoader"), patch(
            "microdetect.annotation.annotator.image_annotator.ImageProcessor"
        ), patch(
            "microdetect.annotation.annotator.image_annotator.AnnotationStorage"
        ), patch(
            "microdetect.annotation.annotator.image_annotator.SuggestionGenerator"
        ), patch(
            "microdetect.annotation.annotator.image_annotator.AnnotationBackup"
        ), patch(
            "microdetect.annotation.annotator.image_annotator.ProgressManager"
        ):
            annotator = ImageAnnotator(classes=classes, auto_save=True, auto_save_interval=5)

            # Atribuir mocks para testes específicos
            annotator._initialize_components()

            # Mock para verificações em métodos específicos
            annotator.update_status = MagicMock()

            yield annotator

    def test_initialization(self, annotator):
        """Testa a inicialização do ImageAnnotator."""
        # Verificar valores padrão
        assert annotator.classes == ["0-classe1", "1-classe2", "2-classe3"]
        assert annotator.auto_save is True
        assert annotator.auto_save_interval == 5

        # Verificar inicialização de componentes
        assert annotator.box_manager is not None
        assert annotator.action_history is not None
        assert annotator.image_loader is not None
        assert annotator.image_processor is not None
        assert annotator.annotation_storage is not None
        assert annotator.suggestion_generator is not None
        assert annotator.annotation_backup is not None
        assert annotator.progress_manager is not None

        # Estado inicial
        assert annotator.window_closed is False
        assert annotator.user_cancelled is False
        assert annotator.next_image_requested is False
        assert annotator.edit_mode is False
        assert annotator.pan_mode is False

    def test_create_callbacks(self, annotator):
        """Testa a criação de callbacks."""
        callbacks = annotator._create_callbacks()

        # Verificar callbacks essenciais
        assert "reset_window_closed" in callbacks
        assert "get_current_class" in callbacks
        assert "update_status" in callbacks
        assert "on_closing" in callbacks
        assert "toggle_edit_mode" in callbacks
        assert "save" in callbacks
        assert "undo" in callbacks

        # Testar callback get_current_class
        annotator.class_var = MagicMock()
        annotator.class_var.get.return_value = "0-classe1"
        assert annotator._get_current_class() == "0-classe1"

        # Testar com class_var não definido
        annotator.class_var = None
        assert annotator._get_current_class() == "0-classe1"  # Deve usar o primeiro da lista

    def test_toggle_edit_mode(self, annotator):
        """Testa a alternância do modo de edição."""
        # Configurar mocks
        mock_button_manager = MagicMock()
        mock_main_window = MagicMock()
        mock_main_window.get_button_manager.return_value = mock_button_manager
        annotator.main_window = mock_main_window
        annotator.mouse_handler = MagicMock()

        # Verificar estado inicial
        assert annotator.edit_mode is False

        # Alternar modo de edição
        annotator.toggle_edit_mode()

        # Verificar mudança de estado
        assert annotator.edit_mode is True
        assert annotator.pan_mode is False
        assert mock_button_manager.update_button_state.called
        assert annotator.mouse_handler.set_mode.called
        assert annotator.update_status.called

        # Alternar novamente
        annotator.toggle_edit_mode()

        # Verificar retorno ao estado original
        assert annotator.edit_mode is False

    def test_toggle_pan_mode(self, annotator):
        """Testa a alternância do modo de navegação."""
        # Configurar mocks
        mock_button_manager = MagicMock()
        mock_main_window = MagicMock()
        mock_main_window.get_button_manager.return_value = mock_button_manager
        annotator.main_window = mock_main_window
        annotator.mouse_handler = MagicMock()

        # Verificar estado inicial
        assert annotator.pan_mode is False

        # Alternar modo de navegação
        annotator.toggle_pan_mode()

        # Verificar mudança de estado
        assert annotator.pan_mode is True
        assert annotator.edit_mode is False  # Deve desativar edição
        assert mock_button_manager.update_button_state.called
        assert annotator.mouse_handler.set_mode.called
        assert annotator.update_status.called

        # Alternar novamente
        annotator.toggle_pan_mode()

        # Verificar retorno ao estado original
        assert annotator.pan_mode is False

    def test_check_auto_save(self, annotator):
        """Testa a funcionalidade de auto-save."""
        # Configurar mocks
        annotator.current_image_path = "/path/to/image.jpg"
        annotator.current_output_dir = "/path/to/output"
        annotator.last_save_time = time.time() - 10  # 10 segundos atrás

        # Testar auto-save
        result = annotator._check_auto_save()

        # Verificações
        assert result is True
        assert annotator.annotation_storage.save_annotations.called
        assert annotator.progress_manager.save_progress.called
        assert annotator.update_status.called

        # Testar com auto-save desativado
        annotator.auto_save = False
        result = annotator._check_auto_save()
        assert result is False

    @patch("microdetect.annotation.annotator.image_annotator.messagebox")
    def test_save(self, mock_messagebox, annotator):
        """Testa o salvamento manual de anotações."""
        # Configurar mocks
        annotator.current_image_path = "/path/to/image.jpg"
        annotator.current_output_dir = "/path/to/output"
        annotator.annotation_storage.save_annotations.return_value = "/path/to/output/image.txt"

        # Testar salvamento
        result = annotator.save()

        # Verificações
        assert result == "/path/to/output/image.txt"
        assert annotator.annotation_storage.save_annotations.called
        assert annotator.progress_manager.save_progress.called
        assert annotator.update_status.called

        # Testar com erro
        annotator.annotation_storage.save_annotations.side_effect = Exception("Erro de teste")
        result = annotator.save()
        assert result is None
        assert annotator.update_status.called

    def test_undo(self, annotator):
        """Testa a funcionalidade de desfazer (undo)."""
        # Configurar mocks
        annotator.action_history.is_empty.return_value = False
        annotator.action_history.undo.return_value = {"type": "add", "data": {"index": 0}}
        annotator.box_manager.get_box_count.return_value = 1
        annotator.canvas = MagicMock()

        # Testar undo com ação de adição
        annotator.undo()

        # Verificações
        assert annotator.action_history.undo.called
        assert annotator.box_manager.remove_box.called
        assert annotator.update_status.called

        # Testar undo com ação de movimento
        annotator.action_history.undo.return_value = {"type": "move", "data": {"index": 0, "before": ("0", 10, 10, 50, 50)}}

        annotator.undo()

        # Verificações
        assert annotator.box_manager.update_box.called

        # Testar undo com lista vazia
        annotator.action_history.is_empty.return_value = True
        annotator.undo()
        assert "Nada para desfazer" in annotator.update_status.call_args[0][0]

    @patch("microdetect.annotation.annotator.image_annotator.messagebox")
    def test_delete_selected(self, mock_messagebox, annotator):
        """Testa a exclusão de caixas selecionadas."""
        # Configurar mocks
        annotator.box_manager.selected_idx = 0
        annotator.box_manager.get_box.return_value = ("0", 10, 10, 50, 50)
        annotator.canvas = MagicMock()
        annotator.edit_mode = True

        # Testar exclusão de caixa selecionada
        annotator.delete_selected()

        # Verificações
        assert annotator.action_history.add.called
        assert annotator.box_manager.remove_box.called
        assert annotator.update_status.called

        # Testar exclusão sem seleção (remove última caixa)
        annotator.box_manager.selected_idx = None
        annotator.box_manager.get_box_count.return_value = 1

        annotator.delete_selected()

        # Verificações
        assert annotator.box_manager.remove_box.call_count == 2

        # Testar quando não há caixas para excluir
        annotator.box_manager.get_box_count.return_value = 0

        annotator.delete_selected()

        # Verificações
        assert "Nenhuma caixa para excluir" in annotator.update_status.call_args[0][0]

    @patch("microdetect.annotation.annotator.image_annotator.messagebox")
    def test_reset_boxes(self, mock_messagebox, annotator):
        """Testa a limpeza de todas as caixas."""
        # Configurar mocks
        annotator.box_manager.get_box_count.return_value = 2
        annotator.box_manager.get_all_boxes.return_value = [("0", 10, 10, 50, 50), ("1", 20, 20, 60, 60)]
        mock_messagebox.askyesno.return_value = True  # Usuário confirma
        annotator.canvas = MagicMock()

        # Testar reset
        annotator.reset_boxes()

        # Verificações
        assert mock_messagebox.askyesno.called
        assert annotator.action_history.add.call_count == 2  # Uma vez para cada caixa
        assert annotator.box_manager.clear_all.called
        assert annotator.update_status.called

        # Testar quando usuário cancela
        mock_messagebox.askyesno.return_value = False
        annotator.reset_boxes()

        # Verificações
        assert annotator.box_manager.clear_all.call_count == 1  # Não chamado novamente

        # Testar quando não há caixas
        annotator.box_manager.get_box_count.return_value = 0
        annotator.reset_boxes()

        # Verificações
        assert "Nenhuma caixa para limpar" in annotator.update_status.call_args[0][0]

    def test_reset_zoom(self, annotator):
        """Testa o reset do zoom."""
        # Configurar mocks
        annotator.scale_factor = 2.0
        annotator._redraw_with_zoom = MagicMock()

        # Testar reset de zoom
        annotator.reset_zoom()

        # Verificações
        assert annotator.scale_factor == 1.0
        assert annotator._redraw_with_zoom.called
        assert annotator.update_status.called

    def test_cycle_classes(self, annotator):
        """Testa a alternância entre classes."""
        # Configurar mocks
        mock_class_var = MagicMock()
        mock_class_var.get.return_value = "0-classe1"
        annotator.class_var = mock_class_var

        # Testar ciclo de classes
        annotator.cycle_classes()

        # Verificações
        assert mock_class_var.set.called
        assert mock_class_var.set.call_args[0][0] == "1-classe2"  # Próxima classe
        assert annotator.update_status.called

        # Testar ciclo completo
        mock_class_var.get.return_value = "2-classe3"
        annotator.cycle_classes()

        # Verificações
        assert mock_class_var.set.call_args[0][0] == "0-classe1"  # Volta para a primeira

    @patch("microdetect.annotation.annotator.image_annotator.messagebox")
    def test_on_closing(self, mock_messagebox, annotator):
        """Testa o comportamento ao fechar a janela."""
        # Configurar mocks
        annotator.box_manager.get_box_count.return_value = 1
        mock_messagebox.askyesno.return_value = True  # Usuário decide salvar
        annotator.save = MagicMock()
        annotator.image_loader = MagicMock()
        annotator.root = MagicMock()
        annotator._cleanup_timers = MagicMock()

        # Testar fechamento com salvamento
        annotator.on_closing()

        # Verificações
        assert mock_messagebox.askyesno.called
        assert annotator.save.called
        assert annotator._cleanup_timers.called
        assert annotator.window_closed is True
        assert annotator.user_cancelled is True
        assert annotator.root.destroy.called

        # Testar com cancelamento
        annotator.window_closed = False
        annotator.user_cancelled = False
        mock_messagebox.askyesno.return_value = False

        annotator.on_closing()

        # Verificações
        assert annotator.window_closed is True
        assert annotator.user_cancelled is True

    def test_toggle_suggestion_mode(self, annotator):
        """Testa a alternância do modo de sugestão."""
        # Configurar mocks
        annotator.suggestion_mode = False
        annotator.current_image_path = "/path/to/image.jpg"
        annotator.suggestion_generator.generate_suggestions.return_value = [("0", 10, 10, 50, 50)]
        annotator.canvas = MagicMock()
        mock_button_manager = MagicMock()
        mock_main_window = MagicMock()
        mock_main_window.get_button_manager.return_value = mock_button_manager
        annotator.main_window = mock_main_window

        # Simular root para atualização do cursor
        mock_root = MagicMock()
        mock_root.config.return_value = "normal"
        annotator.root = mock_root

        # Testar ativação do modo de sugestão
        annotator.toggle_suggestion_mode()

        # Verificações
        assert annotator.suggestion_mode is True
        assert annotator.suggestion_generator.generate_suggestions.called
        assert len(annotator.suggested_boxes) == 1
        assert annotator.update_status.called
        assert mock_button_manager.update_button_state.called

        # Testar desativação
        annotator.toggle_suggestion_mode()

        # Verificações
        assert annotator.suggestion_mode is False
        assert annotator.canvas.delete.called
        assert len(annotator.suggested_boxes) == 0
        assert mock_button_manager.update_button_state.called

    def test_apply_suggested_annotations(self, annotator):
        """Testa a aplicação de sugestões de anotação."""
        # Configurar mocks
        annotator.suggested_boxes = [("0", 10, 10, 50, 50), ("1", 20, 20, 60, 60)]
        annotator.box_manager.add_box.side_effect = [0, 1]  # Índices retornados
        annotator.canvas = MagicMock()
        mock_button_manager = MagicMock()
        mock_main_window = MagicMock()
        mock_main_window.get_button_manager.return_value = mock_button_manager
        annotator.main_window = mock_main_window

        # Testar aplicação de sugestões
        result = annotator.apply_suggested_annotations()

        # Verificações
        assert result is True
        assert annotator.box_manager.add_box.call_count == 2
        assert annotator.action_history.add.call_count == 2
        assert annotator.canvas.delete.called
        assert len(annotator.suggested_boxes) == 0
        assert annotator.update_status.called
        assert mock_button_manager.update_button_state.called

        # Testar quando não há sugestões
        annotator.suggested_boxes = []
        result = annotator.apply_suggested_annotations()

        # Verificações
        assert result is False
        assert "Não há sugestões para aplicar" in annotator.update_status.call_args[0][0]

    @patch("microdetect.annotation.annotator.image_annotator.StatisticsDialog")
    def test_show_statistics(self, MockStatisticsDialog, annotator):
        """Testa a exibição de estatísticas."""
        # Configurar mocks
        annotator.current_image_path = "/path/to/image.jpg"
        annotator.progress_manager.get_session_statistics.return_value = {"session_active": True}
        annotator.progress_manager.calculate_progress.return_value = (10, 20, 50.0)  # 10 anotadas, 20 total, 50%
        mock_stats_dialog = MagicMock()
        MockStatisticsDialog.return_value = mock_stats_dialog

        # Testar exibição de estatísticas
        annotator.show_statistics()

        # Verificações
        assert MockStatisticsDialog.called
        assert mock_stats_dialog.show.called

        # Testar sem diretório disponível
        annotator.current_image_path = None
        annotator.show_statistics()

        # Verificações
        assert "não disponível" in annotator.update_status.call_args[0][0]

    def test_enhance_image(self, annotator):
        """Testa o aprimoramento de imagem."""
        # Configurar mocks
        annotator.current_image_path = "/path/to/image.jpg"
        annotator.image_loader.load_image.return_value = (np.zeros((100, 100, 3), dtype=np.uint8), 100, 100)
        annotator.image_processor.resize_image.return_value = (np.zeros((50, 50, 3), dtype=np.uint8), 0.5)
        annotator.image_processor.denoise_image.return_value = np.zeros((50, 50, 3), dtype=np.uint8)
        annotator.image_processor.apply_brightness_contrast.return_value = np.zeros((50, 50, 3), dtype=np.uint8)
        annotator.image_processor.apply_sharpen.return_value = np.zeros((50, 50, 3), dtype=np.uint8)
        annotator.canvas = MagicMock()

        # Testar melhoria de imagem
        result = annotator.enhance_image(brightness=10, contrast=20, sharpen=5, denoise=True)

        # Verificações
        assert result is True
        assert annotator.image_loader.load_image.called
        assert annotator.image_processor.resize_image.called
        assert annotator.image_processor.denoise_image.called
        assert annotator.image_processor.apply_brightness_contrast.called
        assert annotator.image_processor.apply_sharpen.called
        assert annotator.image_loader.create_tkinter_image.called
        assert annotator.canvas.delete.called
        assert annotator.canvas.create_image.called
        assert annotator.update_status.called

        # Testar com erro
        annotator.image_loader.load_image.side_effect = Exception("Erro de teste")
        result = annotator.enhance_image()

        # Verificações
        assert result is False
        assert "Erro" in annotator.update_status.call_args[0][0]

    def test_enhance_for_microscopy(self, annotator):
        """Testa o aprimoramento específico para microscopia."""
        # Configurar mocks
        annotator.current_image_path = "/path/to/image.jpg"
        annotator.image_loader.load_image.return_value = (np.zeros((100, 100, 3), dtype=np.uint8), 100, 100)
        annotator.image_processor.resize_image.return_value = (np.zeros((50, 50, 3), dtype=np.uint8), 0.5)
        annotator.image_processor.enhance_contrast_for_microscopy.return_value = np.zeros((50, 50, 3), dtype=np.uint8)
        annotator.image_processor.apply_sharpen.return_value = np.zeros((50, 50, 3), dtype=np.uint8)
        annotator.canvas = MagicMock()

        # Testar melhoria para microscopia
        result = annotator.enhance_for_microscopy()

        # Verificações
        assert result is True
        assert annotator.image_loader.load_image.called
        assert annotator.image_processor.resize_image.called
        assert annotator.image_processor.enhance_contrast_for_microscopy.called
        assert annotator.image_processor.apply_sharpen.called
        assert annotator.image_loader.create_tkinter_image.called
        assert annotator.canvas.delete.called
        assert annotator.canvas.create_image.called
        assert annotator.update_status.called

        # Testar com erro
        annotator.image_loader.load_image.side_effect = Exception("Erro de teste")
        result = annotator.enhance_for_microscopy()

        # Verificações
        assert result is False
        assert "Erro" in annotator.update_status.call_args[0][0]

    @patch("microdetect.annotation.annotator.image_annotator.filedialog")
    def test_select_yolo_model(self, mock_filedialog, annotator):
        """Testa a seleção de modelo YOLO."""
        # Configurar mocks
        mock_filedialog.askopenfilename.return_value = "/path/to/model.pt"
        annotator.suggestion_generator.set_model_path.return_value = True
        mock_button_manager = MagicMock()
        mock_main_window = MagicMock()
        mock_main_window.get_button_manager.return_value = mock_button_manager
        annotator.main_window = mock_main_window

        # Testar seleção de modelo
        annotator.select_yolo_model()

        # Verificações
        assert mock_filedialog.askopenfilename.called
        assert annotator.suggestion_generator.set_model_path.called
        assert annotator.yolo_model_path == "/path/to/model.pt"
        assert annotator.update_status.called
        assert mock_button_manager.update_button_state.called

        # Testar falha ao carregar modelo
        annotator.suggestion_generator.set_model_path.return_value = False
        annotator.select_yolo_model()

        # Verificações
        assert "Falha" in annotator.update_status.call_args[0][0]

    def test_toggle_cv_fallback(self, annotator):
        """Testa a alternância do fallback de visão computacional."""
        # Configurar mocks
        annotator.suggestion_generator.use_cv_fallback = True
        mock_button_manager = MagicMock()
        mock_main_window = MagicMock()
        mock_main_window.get_button_manager.return_value = mock_button_manager
        annotator.main_window = mock_main_window

        # Testar desativação
        annotator.toggle_cv_fallback(False)

        # Verificações
        assert annotator.suggestion_generator.toggle_cv_fallback.called
        assert annotator.update_status.called
        assert mock_button_manager.update_button_state.called

        # Testar ativação
        annotator.toggle_cv_fallback(True)

        # Verificações
        assert annotator.suggestion_generator.toggle_cv_fallback.call_count == 2
        assert annotator.update_status.call_count == 2

    @patch("microdetect.annotation.annotator.image_annotator.time")
    def test_monitor_window_state(self, mock_time, annotator):
        """Testa o monitoramento do estado da janela."""
        # Configurar mocks
        annotator.window_closed = True
        annotator.root = MagicMock()
        annotator.root.winfo_exists.return_value = True
        annotator.root.after.return_value = 123

        # Testar correção de inconsistência
        annotator._monitor_window_state()

        # Verificações
        assert annotator.window_closed is False
        assert annotator.root.after.called
        assert 123 in annotator.active_timer_ids

        # Testar quando winfo_exists levanta exceção
        annotator.root.winfo_exists.side_effect = Exception("Janela fechada")
        annotator._monitor_window_state()

        # Verificações
        assert annotator.window_closed is True

    @patch("microdetect.annotation.annotator.image_annotator.create_export_import_ui")
    def test_show_export_import(self, mock_create_ui, annotator):
        """Testa a exibição do diálogo de exportação/importação."""
        # Configurar mocks
        annotator.current_image_path = "/path/to/image.jpg"
        annotator.current_output_dir = "/path/to/output"
        annotator.root = MagicMock()

        # Testar exibição do diálogo
        annotator._show_export_import()

        # Verificações
        assert mock_create_ui.called

        # Testar sem caminho de imagem
        annotator.current_image_path = None
        annotator._show_export_import()

        # Verificações
        assert mock_create_ui.call_count == 1  # Não chamado novamente
