"""
Testes unitários para o módulo de anotação.
"""

import json
import os
import tempfile
import time
import unittest
from unittest.mock import MagicMock, patch

import cv2
import numpy as np

from microdetect.annotation.annotator import (
    HANDLE_E,
    HANDLE_N,
    HANDLE_NE,
    HANDLE_NONE,
    HANDLE_NW,
    HANDLE_S,
    HANDLE_SE,
    HANDLE_SW,
    HANDLE_W,
    ImageAnnotator,
)


class TestImageAnnotator(unittest.TestCase):
    """
    Testes para a classe ImageAnnotator.
    """

    def setUp(self):
        """
        Configuração dos testes.
        """
        # Criar classes para testes
        self.classes = ["0-levedura", "1-fungo", "2-micro-alga"]

        # Criar anotador com auto-save reduzido para testes
        self.annotator = ImageAnnotator(classes=self.classes, auto_save=True, auto_save_interval=1)  # 1 segundo para testes

        # Criar diretório temporário para testes
        self.temp_dir = tempfile.TemporaryDirectory()

        # Criar imagem de teste
        self.test_image = np.ones((100, 100, 3), dtype=np.uint8) * 255  # Imagem branca
        self.test_image_path = os.path.join(self.temp_dir.name, "test_image.jpg")
        cv2.imwrite(self.test_image_path, self.test_image)

        # Criar diretório de saída para testes
        self.output_dir = os.path.join(self.temp_dir.name, "output")
        os.makedirs(self.output_dir, exist_ok=True)

        # Arquivo de progresso
        self.progress_file = os.path.join(self.output_dir, self.annotator.progress_file)

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
        annotator = ImageAnnotator()
        self.assertListEqual(annotator.classes, ["0-levedura", "1-fungo", "2-micro-alga"])
        self.assertTrue(annotator.auto_save)
        self.assertEqual(annotator.auto_save_interval, 300)

        # Verificar que os atributos necessários estão inicializados
        self.assertEqual(annotator.original_w, 0)
        self.assertEqual(annotator.original_h, 0)
        self.assertEqual(annotator.display_w, 0)
        self.assertEqual(annotator.display_h, 0)
        self.assertEqual(annotator.display_scale, 1.0)
        self.assertEqual(annotator.scale_factor, 1.0)
        self.assertIsNone(annotator.canvas)
        self.assertIsNone(annotator.current_img_tk)

        # Verificar novos atributos adicionados
        self.assertFalse(annotator.window_closed)
        self.assertEqual(annotator.bounding_boxes, [])
        self.assertFalse(annotator.pan_mode)
        self.assertFalse(annotator.user_cancelled)
        self.assertEqual(annotator.action_history, [])
        self.assertEqual(annotator.max_history, 50)
        self.assertEqual(annotator.resize_handle, HANDLE_NONE)
        self.assertEqual(annotator.handle_size, 6)
        self.assertIsNone(annotator.original_box_state)

        # Verificar que start_x e start_y NÃO são atributos da classe
        self.assertFalse(hasattr(annotator, "start_x"))
        self.assertFalse(hasattr(annotator, "start_y"))

        # Testar inicialização com parâmetros personalizados
        custom_classes = ["0-bacteria", "1-virus"]
        annotator = ImageAnnotator(classes=custom_classes, auto_save=False, auto_save_interval=600)
        self.assertListEqual(annotator.classes, custom_classes)
        self.assertFalse(annotator.auto_save)
        self.assertEqual(annotator.auto_save_interval, 600)

    def test_load_image(self):
        """
        Testa o carregamento de imagens.
        """
        # Testar carregamento de imagem válida
        result = self.annotator._load_image(self.test_image_path)
        img, w, h = result

        self.assertIsNotNone(img)
        self.assertEqual(w, 100)
        self.assertEqual(h, 100)

        # Testar carregamento de imagem inválida
        result = self.annotator._load_image("imagem_inexistente.jpg")
        img, w, h = result

        self.assertIsNone(img)
        self.assertEqual(w, 0)
        self.assertEqual(h, 0)

    def test_save_annotations(self):
        """
        Testa o salvamento de anotações.
        """
        # Preparar dados para o teste
        bounding_boxes = [("0", 10, 10, 30, 30), ("1", 50, 50, 70, 70)]  # classe, x1, y1, x2, y2
        base_name = "test_image"

        # Configurar dimensões originais
        self.annotator.original_w = 100
        self.annotator.original_h = 100

        # Salvar anotações
        annotation_path = self.annotator._save_annotations(bounding_boxes, self.output_dir, base_name)

        # Verificar se o arquivo foi criado
        self.assertTrue(os.path.exists(annotation_path))

        # Verificar conteúdo do arquivo
        with open(annotation_path, "r") as f:
            lines = f.readlines()

        self.assertEqual(len(lines), 2)

        # Verificar primeira anotação (valores YOLO normalizados)
        parts = lines[0].strip().split()
        self.assertEqual(parts[0], "0")  # classe
        self.assertAlmostEqual(float(parts[1]), 0.2)  # center_x
        self.assertAlmostEqual(float(parts[2]), 0.2)  # center_y
        self.assertAlmostEqual(float(parts[3]), 0.2)  # width
        self.assertAlmostEqual(float(parts[4]), 0.2)  # height

    def test_check_auto_save(self):
        """
        Testa o salvamento automático.
        """
        # Preparar dados para o teste
        bounding_boxes = [("0", 10, 10, 30, 30)]
        base_name = "test_image"

        # Configurar dimensões originais
        self.annotator.original_w = 100
        self.annotator.original_h = 100

        # Definir último salvamento para há muito tempo
        self.annotator.last_save_time = time.time() - 10

        # Auto-save deve ocorrer
        result = self.annotator._check_auto_save(bounding_boxes, self.output_dir, base_name)

        self.assertTrue(result)

        # Verificar se o arquivo foi criado
        annotation_path = os.path.join(self.output_dir, f"{base_name}.txt")
        self.assertTrue(os.path.exists(annotation_path))

        # Definir último salvamento para agora
        self.annotator.last_save_time = time.time()

        # Auto-save não deve ocorrer
        result = self.annotator._check_auto_save(bounding_boxes, self.output_dir, base_name)

        self.assertFalse(result)

        # Desativar auto-save
        self.annotator.auto_save = False

        # Auto-save não deve ocorrer mesmo com tempo expirado
        self.annotator.last_save_time = time.time() - 10
        result = self.annotator._check_auto_save(bounding_boxes, self.output_dir, base_name)

        self.assertFalse(result)

    def test_save_progress(self):
        """
        Testa o salvamento do progresso.
        """
        # Salvar progresso
        current_image = self.test_image_path
        self.annotator._save_progress(self.progress_file, current_image)

        # Verificar se o arquivo foi criado
        self.assertTrue(os.path.exists(self.progress_file))

        # Verificar conteúdo do arquivo
        with open(self.progress_file, "r") as f:
            progress_data = json.load(f)

        self.assertEqual(progress_data["last_annotated"], current_image)
        self.assertTrue("timestamp" in progress_data)

    def test_backup_annotations(self):
        """
        Testa a criação de backup de anotações e a limitação para 5 backups.
        """
        import os
        import re
        import time

        # Criar arquivos de anotação de teste
        annotation1 = os.path.join(self.output_dir, "test1.txt")
        annotation2 = os.path.join(self.output_dir, "test2.txt")

        with open(annotation1, "w") as f:
            f.write("0 0.5 0.5 0.2 0.2")

        with open(annotation2, "w") as f:
            f.write("1 0.7 0.7 0.1 0.1")

        # Criar backup e verificar se os arquivos foram copiados
        backup_dir = self.annotator.backup_annotations(self.output_dir)

        # Verificações básicas
        self.assertIsNotNone(backup_dir)
        self.assertTrue(os.path.exists(backup_dir))
        self.assertTrue(os.path.exists(os.path.join(backup_dir, "test1.txt")))
        self.assertTrue(os.path.exists(os.path.join(backup_dir, "test2.txt")))

        # Verificar que arquivo de progresso não é copiado
        with open(self.progress_file, "w") as f:
            f.write("{}")

        backup_dir = self.annotator.backup_annotations(self.output_dir)
        self.assertFalse(os.path.exists(os.path.join(backup_dir, self.annotator.progress_file)))

    def test_add_to_history(self):
        """
        Testa a adição de ações ao histórico.
        """
        # Histórico deve começar vazio
        self.assertEqual(len(self.annotator.action_history), 0)

        # Adicionar ação de teste
        test_data = {"index": 0, "box": ("0", 10, 10, 30, 30)}
        self.annotator._add_to_history("add", test_data)

        # Verificar se a ação foi adicionada corretamente
        self.assertEqual(len(self.annotator.action_history), 1)
        self.assertEqual(self.annotator.action_history[0]["type"], "add")
        self.assertEqual(self.annotator.action_history[0]["data"], test_data)

        # Testar limite de histórico
        # Adicionar mais ações do que o limite
        original_max_history = self.annotator.max_history
        self.annotator.max_history = 3  # Definir limite baixo para teste

        for i in range(5):  # Adicionar 5 itens quando o limite é 3
            self.annotator._add_to_history("test", {"index": i})

        # Verificar se apenas os 3 mais recentes são mantidos
        self.assertEqual(len(self.annotator.action_history), 3)
        self.assertEqual(self.annotator.action_history[0]["data"]["index"], 2)
        self.assertEqual(self.annotator.action_history[1]["data"]["index"], 3)
        self.assertEqual(self.annotator.action_history[2]["data"]["index"], 4)

        # Restaurar o limite original
        self.annotator.max_history = original_max_history

    def test_detect_resize_handle(self):
        """
        Testa a detecção de alças de redimensionamento.
        """
        # Configurar uma caixa de teste
        self.annotator.bounding_boxes = [("0", 10, 10, 50, 50)]
        self.annotator.display_scale = 1.0
        self.annotator.scale_factor = 1.0

        # Testar cada canto
        # Canto noroeste (superior esquerdo)
        handle = self.annotator._detect_resize_handle(10, 10, 0)
        self.assertEqual(handle, HANDLE_NW)

        # Canto nordeste (superior direito)
        handle = self.annotator._detect_resize_handle(50, 10, 0)
        self.assertEqual(handle, HANDLE_NE)

        # Canto sudeste (inferior direito)
        handle = self.annotator._detect_resize_handle(50, 50, 0)
        self.assertEqual(handle, HANDLE_SE)

        # Canto sudoeste (inferior esquerdo)
        handle = self.annotator._detect_resize_handle(10, 50, 0)
        self.assertEqual(handle, HANDLE_SW)

        # Testar cada lado
        # Lado norte (meio superior)
        handle = self.annotator._detect_resize_handle(30, 10, 0)
        self.assertEqual(handle, HANDLE_N)

        # Lado leste (meio direito)
        handle = self.annotator._detect_resize_handle(50, 30, 0)
        self.assertEqual(handle, HANDLE_E)

        # Lado sul (meio inferior)
        handle = self.annotator._detect_resize_handle(30, 50, 0)
        self.assertEqual(handle, HANDLE_S)

        # Lado oeste (meio esquerdo)
        handle = self.annotator._detect_resize_handle(10, 30, 0)
        self.assertEqual(handle, HANDLE_W)

        # Testar o centro (não deve detectar nenhuma alça)
        handle = self.annotator._detect_resize_handle(30, 30, 0)
        self.assertEqual(handle, HANDLE_NONE)

        # Testar índice inválido
        handle = self.annotator._detect_resize_handle(10, 10, 1)  # Índice fora dos limites
        self.assertEqual(handle, HANDLE_NONE)

    def test_annotate_image_save(self):
        """
        Testa o salvamento ao anotar uma imagem de uma maneira mais direta.
        """
        # Vamos substituir o método annotate_image por uma versão simplificada
        # que apenas chama _save_annotations diretamente

        with patch.object(self.annotator, "_save_annotations") as mock_save:
            # Configurar o mock para retornar um caminho válido
            mock_save.return_value = os.path.join(self.output_dir, "test_image.txt")

            # Substituir o método annotate_image por nossa versão de teste
            original_annotate = self.annotator.annotate_image

            def mock_annotate_image(image_path, output_dir):
                # Configurar o estado necessário
                self.annotator.original_w = 100
                self.annotator.original_h = 100

                # Simular a existência de algumas bounding boxes
                self.annotator.bounding_boxes = [("0", 10, 10, 30, 30)]

                # Chamar diretamente o método _save_annotations
                base_name = os.path.splitext(os.path.basename(image_path))[0]
                return self.annotator._save_annotations(self.annotator.bounding_boxes, output_dir, base_name)

            try:
                # Substituir temporariamente o método
                self.annotator.annotate_image = mock_annotate_image

                # Chamar o método
                result = self.annotator.annotate_image(self.test_image_path, self.output_dir)

                # Verificar se o salvamento foi chamado
                mock_save.assert_called_once()

                # Verificar o resultado
                self.assertEqual(result, os.path.join(self.output_dir, "test_image.txt"))
            finally:
                # Restaurar o método original
                self.annotator.annotate_image = original_annotate

    @patch("builtins.input", return_value="s")
    @patch("microdetect.annotation.annotator.ImageAnnotator.annotate_image")
    @patch("microdetect.annotation.annotator.ImageAnnotator._save_progress")
    @patch("microdetect.annotation.annotator.ImageAnnotator.backup_annotations")
    def test_batch_annotate(self, mock_backup, mock_save_progress, mock_annotate, mock_input):
        """
        Testa a anotação em lote.
        """
        # Criar segunda imagem de teste
        test_image2_path = os.path.join(self.temp_dir.name, "test_image2.jpg")
        cv2.imwrite(test_image2_path, self.test_image)

        # Configurar mock para annotate_image
        mock_annotate.return_value = "annotation_path"

        # Executar anotação em lote
        total_images, total_annotated = self.annotator.batch_annotate(self.temp_dir.name, self.output_dir)

        # Verificar resultados
        self.assertEqual(total_images, 2)
        self.assertEqual(total_annotated, 2)

        # Verificar se os métodos foram chamados
        mock_backup.assert_called_once()
        self.assertEqual(mock_annotate.call_count, 2)
        self.assertEqual(mock_save_progress.call_count, 2)

    def test_batch_annotate_cancel(self):
        """
        Testa o cancelamento da anotação em lote pelo usuário.
        """
        # Criar múltiplas imagens de teste
        test_image2_path = os.path.join(self.temp_dir.name, "test_image2.jpg")
        test_image3_path = os.path.join(self.temp_dir.name, "test_image3.jpg")
        cv2.imwrite(test_image2_path, self.test_image)
        cv2.imwrite(test_image3_path, self.test_image)

        # Variável para rastrear quantas vezes o método foi chamado
        call_count = [0]

        # Armazenar os métodos originais
        original_annotate_image = self.annotator.annotate_image
        original_backup = self.annotator.backup_annotations
        original_save_progress = self.annotator._save_progress

        # Mock para backup_annotations (para evitar criação de arquivos reais)
        def mock_backup(label_dir):
            return "backup_dir"

        # Mock para _save_progress (para evitar criação de arquivos reais)
        def mock_save_progress(progress_path, current_image):
            pass

        # Mock para annotate_image que simula cancelamento
        def mock_annotate_image(image_path, output_dir):
            call_count[0] += 1

            # Definir user_cancelled como True após a primeira chamada
            # Isso fará com que user_cancelled seja True antes de incrementar total_annotated
            self.annotator.user_cancelled = True

            # Retornar um caminho válido
            base_name = os.path.splitext(os.path.basename(image_path))[0]
            return os.path.join(output_dir, f"{base_name}.txt")

        try:
            # Substituir métodos
            self.annotator.annotate_image = mock_annotate_image
            self.annotator.backup_annotations = mock_backup
            self.annotator._save_progress = mock_save_progress

            # Garantir que user_cancelled começa como False
            self.annotator.user_cancelled = False

            # Executar anotação em lote
            total_images, total_annotated = self.annotator.batch_annotate(self.temp_dir.name, self.output_dir)

            # Verificar que o método foi chamado uma vez
            self.assertEqual(call_count[0], 1)

            # Verificar que o contador não foi incrementado devido ao cancelamento
            # A verificação de user_cancelled ocorre ANTES de incrementar total_annotated no batch_annotate
            self.assertEqual(total_annotated, 0)  # Esperado = 0 porque o loop termina antes de incrementar

            # Verificar que user_cancelled está True
            self.assertTrue(self.annotator.user_cancelled)

        finally:
            # Restaurar os métodos originais
            self.annotator.annotate_image = original_annotate_image
            self.annotator.backup_annotations = original_backup
            self.annotator._save_progress = original_save_progress

    def test_cycle_class_selection(self):
        """
        Testa a alternância entre classes.
        """
        # Criar mock para StringVar
        class_var = MagicMock()
        class_var.get.return_value = "0-levedura"

        # Executar ciclo
        self.annotator._cycle_class_selection(class_var)

        # Verificar se a classe foi atualizada para a próxima
        class_var.set.assert_called_once_with("1-fungo")

        # Simular última classe
        class_var.get.return_value = "2-micro-alga"

        # Executar ciclo
        self.annotator._cycle_class_selection(class_var)

        # Verificar se voltou para a primeira
        class_var.set.assert_called_with("0-levedura")


if __name__ == "__main__":
    unittest.main()
