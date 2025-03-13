"""
Testes unitários para o módulo de visualização.
"""

import os
import tempfile
import unittest
from unittest.mock import MagicMock, patch

import cv2
import numpy as np
import tkinter as tk

from microdetect.annotation.visualization import AnnotationVisualizer


class TestAnnotationVisualizer(unittest.TestCase):
    """
    Testes para a classe AnnotationVisualizer.
    """

    def setUp(self):
        """
        Configuração dos testes.
        """
        # Criar mapeamentos para testes
        self.class_map = {
            "0": "0-levedura",
            "1": "1-fungo",
            "2": "2-micro-alga"
        }

        self.color_map = {
            "0": (0, 255, 0),  # Verde
            "1": (0, 0, 255),  # Vermelho
            "2": (255, 0, 0)  # Azul
        }

        # Criar visualizador com mapeamentos personalizados
        self.visualizer = AnnotationVisualizer(
            class_map=self.class_map,
            color_map=self.color_map
        )

        # Criar diretório temporário para testes
        self.temp_dir = tempfile.TemporaryDirectory()

        # Criar imagem de teste
        self.test_image = np.ones((100, 100, 3), dtype=np.uint8) * 255  # Imagem branca
        self.test_image_path = os.path.join(self.temp_dir.name, "test_image.jpg")
        cv2.imwrite(self.test_image_path, self.test_image)

        # Criar arquivo de anotação de teste
        self.test_label = "0 0.5 0.5 0.2 0.2\n1 0.7 0.7 0.1 0.1"  # Dois objetos
        self.test_label_path = os.path.join(self.temp_dir.name, "test_image.txt")
        with open(self.test_label_path, "w") as f:
            f.write(self.test_label)

    def tearDown(self):
        """
        Limpeza após os testes.
        """
        self.temp_dir.cleanup()

    def test_init(self):
        """
        Testa a inicialização da classe.
        """
        # Testar inicialização padrão
        visualizer = AnnotationVisualizer()
        self.assertIsNotNone(visualizer.class_map)
        self.assertIsNotNone(visualizer.color_map)

        # Testar inicialização com mapeamentos personalizados
        self.assertEqual(self.visualizer.class_map, self.class_map)
        self.assertEqual(self.visualizer.color_map, self.color_map)

    def test_load_image(self):
        """
        Testa o carregamento de imagens.
        """
        # Testar carregamento de imagem válida
        img = self.visualizer._load_image(self.test_image_path)
        self.assertIsNotNone(img)
        self.assertEqual(img.shape, (100, 100, 3))

        # Testar carregamento de imagem inválida
        img = self.visualizer._load_image("imagem_inexistente.jpg")
        self.assertIsNone(img)

    def test_process_annotation_line(self):
        """
        Testa o processamento de linhas de anotação.
        """
        # Testar linha válida
        annotation = "0 0.5 0.5 0.2 0.2"
        class_visibility = {"0": True, "1": True, "2": True}
        box_data = self.visualizer._process_annotation_line(
            annotation, 100, 100, class_visibility
        )

        self.assertIsNotNone(box_data)
        self.assertEqual(box_data["class_id"], "0")
        self.assertEqual(box_data["class_name"], "0-levedura")
        self.assertEqual(box_data["color"], (0, 255, 0))

        # Coordenadas esperadas (objeto central com 20x20)
        self.assertEqual(box_data["x1"], 40)
        self.assertEqual(box_data["y1"], 40)
        self.assertEqual(box_data["x2"], 60)
        self.assertEqual(box_data["y2"], 60)

        # Testar linha inválida
        annotation = "0 0.5"  # Incompleta
        box_data = self.visualizer._process_annotation_line(
            annotation, 100, 100, class_visibility
        )
        self.assertIsNone(box_data)

        # Testar classe filtrada
        annotation = "0 0.5 0.5 0.2 0.2"
        class_visibility = {"0": False, "1": True, "2": True}
        box_data = self.visualizer._process_annotation_line(
            annotation, 100, 100, class_visibility
        )
        self.assertIsNone(box_data)

    @patch("cv2.imwrite")
    def test_save_annotated_images(self, mock_imwrite):
        """
        Testa o salvamento de imagens anotadas em lote.
        """
        # Configurar mock para retornar True (sucesso ao salvar)
        mock_imwrite.return_value = True

        # Testar salvamento
        output_dir = os.path.join(self.temp_dir.name, "output")
        saved_count = self.visualizer.save_annotated_images(
            self.temp_dir.name,
            None,  # Usar mesmo diretório das imagens
            output_dir
        )

        # Verificar se o método foi chamado para a imagem de teste
        self.assertEqual(saved_count, 1)
        mock_imwrite.assert_called_once()

        # Testar com filtro de classes
        mock_imwrite.reset_mock()
        saved_count = self.visualizer.save_annotated_images(
            self.temp_dir.name,
            None,
            output_dir,
            filter_classes={"1"}  # Apenas fungo
        )

        # Ainda deve salvar a imagem, mas com apenas uma anotação
        self.assertEqual(saved_count, 1)
        mock_imwrite.assert_called_once()

    @patch("tkinter.Tk")
    @patch("PIL.ImageTk.PhotoImage")
    def test_visualize_annotations_tkinter(self, mock_photo_image, mock_tk):
        """
        Testa a visualização interativa de anotações usando Tkinter.
        Este teste substitui o antigo teste que usava cv2.imshow.
        """
        # Configurar mocks
        mock_root = MagicMock()
        mock_tk.return_value = mock_root
        mock_root.winfo_screenwidth.return_value = 1920
        mock_root.winfo_screenheight.return_value = 1080

        # Simular fechamento imediato da janela
        def destroy_window(*args, **kwargs):
            self.visualizer.window_closed = True
            return None

        # Aplicar o comportamento simulado
        mock_root.mainloop.side_effect = destroy_window

        # Testar visualização em modo interativo
        self.visualizer.visualize_annotations(
            self.temp_dir.name,
            None  # Usar mesmo diretório das imagens
        )

        # Verificar se o Tkinter foi inicializado e a janela principal criada
        mock_tk.assert_called_once()
        mock_root.mainloop.assert_called_once()

        # Verificar se houve uma tentativa de criar uma imagem para exibição
        mock_photo_image.assert_called()

    def test_redraw_all_boxes(self):
        """
        Testa o redesenho de todas as caixas no canvas.
        """
        # Criar mock para o canvas
        mock_canvas = MagicMock()

        # Configurar visualizador para teste
        self.visualizer.display_scale = 1.0
        self.visualizer.scale_factor = 1.0

        # Dados de teste
        annotations = ["0 0.5 0.5 0.2 0.2", "1 0.7 0.7 0.1 0.1"]
        w, h = 100, 100
        class_visibility = {"0": True, "1": True, "2": True}

        # Chamar o método
        results = self.visualizer._redraw_all_boxes(mock_canvas, annotations, w, h, class_visibility)

        # Verificar se o canvas foi manipulado
        mock_canvas.delete.assert_called()
        mock_canvas.create_rectangle.assert_called()
        mock_canvas.create_text.assert_called()

        # Verificar que o método retornou contagens corretas
        self.assertIsNotNone(results)
        total_visible, class_counts = results
        self.assertEqual(total_visible, 2)
        self.assertEqual(class_counts["0"], 1)
        self.assertEqual(class_counts["1"], 1)


if __name__ == "__main__":
    unittest.main()