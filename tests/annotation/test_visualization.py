"""
Testes unitários para o módulo de visualização.
"""

import os
import tempfile
import unittest
from unittest.mock import MagicMock, patch

import cv2
import numpy as np

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

    def test_draw_annotation_box(self):
        """
        Testa o desenho de caixas de anotação.
        """
        # Preparar imagem e dados de caixa
        img = np.ones((100, 100, 3), dtype=np.uint8) * 255
        box_data = {
            "class_id": "0",
            "x1": 40, "y1": 40, "x2": 60, "y2": 60,
            "color": (0, 255, 0),
            "class_name": "0-levedura"
        }

        # Desenhar caixa
        self.visualizer._draw_annotation_box(img, box_data, 0)

        # Verificar se a caixa foi desenhada (algum pixel deve ser verde)
        self.assertTrue(np.any(img[:, :, 1] == 255) and np.any(img[:, :, 0] == 0) and np.any(img[:, :, 2] == 0))

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

    @patch("cv2.imshow")
    @patch("cv2.waitKey")
    @patch("cv2.destroyAllWindows")
    def test_visualize_annotations(self, mock_destroy, mock_waitkey, mock_imshow):
        """
        Testa a visualização interativa de anotações.
        """
        # Configurar mock para simular pressionar tecla 'q' (sair)
        mock_waitkey.return_value = ord("q")

        # Testar visualização
        self.visualizer.visualize_annotations(
            self.temp_dir.name,
            None  # Usar mesmo diretório das imagens
        )

        # Verificar se os métodos foram chamados
        mock_imshow.assert_called()
        mock_waitkey.assert_called_once()
        mock_destroy.assert_called_once()


if __name__ == "__main__":
    unittest.main()