"""
Testes para o módulo de exportação e importação de anotações.
"""

import json
import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest

from microdetect.annotation.export_import import AnnotationConverter, create_export_import_ui


class TestAnnotationConverter:

    @pytest.fixture
    def converter(self):
        """Cria um conversor de anotações com classes definidas."""
        classes = ["0-levedura", "1-fungo", "2-micro-alga"]
        return AnnotationConverter(classes)

    @pytest.fixture
    def temp_dirs(self):
        """Cria diretórios temporários para testes."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Criar subdiretórios
            annotations_dir = os.path.join(temp_dir, "annotations")
            images_dir = os.path.join(temp_dir, "images")
            output_dir = os.path.join(temp_dir, "output")

            os.makedirs(annotations_dir, exist_ok=True)
            os.makedirs(images_dir, exist_ok=True)
            os.makedirs(output_dir, exist_ok=True)

            yield temp_dir, annotations_dir, images_dir, output_dir

    @pytest.fixture
    def sample_annotations(self, temp_dirs):
        """Cria arquivos de anotação de amostra em formato YOLO."""
        _, annotations_dir, _, _ = temp_dirs

        # Criar arquivo de anotação
        annotation_path = os.path.join(annotations_dir, "test_image.txt")
        with open(annotation_path, "w") as f:
            # Formato YOLO: class_id x_center y_center width height
            f.write("0 0.5 0.5 0.2 0.2\n")
            f.write("1 0.7 0.7 0.1 0.1\n")

        yield annotation_path

    @pytest.fixture
    def sample_image(self, temp_dirs):
        """Cria uma imagem de amostra."""
        _, _, images_dir, _ = temp_dirs

        # Mock da imagem
        with patch("cv2.imread") as mock_imread, \
                patch("cv2.imwrite") as mock_imwrite:
            # Simular uma imagem 100x100
            mock_image = MagicMock()
            mock_image.shape = (100, 100, 3)
            mock_imread.return_value = mock_image
            mock_imwrite.return_value = True

            # Caminho da imagem
            image_path = os.path.join(images_dir, "test_image.jpg")

            # Criar arquivo vazio
            with open(image_path, "w") as f:
                f.write("dummy content")

            yield image_path

    def test_initialization(self, converter):
        """Testa a inicialização do AnnotationConverter."""
        assert converter.classes == ["0-levedura", "1-fungo", "2-micro-alga"]
        assert converter.class_map == {"0": "0-levedura", "1": "1-fungo", "2": "2-micro-alga"}

        # Testar inicialização sem classes
        with patch("microdetect.annotation.export_import.config.get") as mock_get:
            mock_get.return_value = ["0-test"]
            converter = AnnotationConverter()
            assert converter.classes == ["0-test"]

    @patch("os.path.exists")
    @patch("cv2.imread")
    def test_export_to_coco(self, mock_imread, mock_exists, converter, temp_dirs, sample_annotations):
        """Testa a exportação para formato COCO."""
        _, annotations_dir, images_dir, _ = temp_dirs

        # Configurar mocks
        mock_exists.return_value = True
        mock_image = MagicMock()
        mock_image.shape = (100, 100, 3)
        mock_imread.return_value = mock_image

        # Mock para glob
        with patch("glob.glob") as mock_glob:
            mock_glob.return_value = [os.path.join(annotations_dir, "test_image.txt")]

            # Exportar para COCO
            output_path = os.path.join(annotations_dir, "annotations_coco.json")
            result = converter.export_to_coco(annotations_dir, images_dir)

            # Verificações
            assert result == output_path
            assert mock_glob.called
            assert mock_imread.called

            # Verificar conteúdo do arquivo
            with open(output_path, "r") as f:
                coco_data = json.load(f)

            # Verificar estrutura
            assert "images" in coco_data
            assert "annotations" in coco_data
            assert "categories" in coco_data
            assert len(coco_data["categories"]) == 3
            assert len(coco_data["images"]) == 1
            assert len(coco_data["annotations"]) == 2

            # Verificar uma anotação
            annotation = coco_data["annotations"][0]
            assert annotation["category_id"] == 0
            assert "bbox" in annotation
            assert len(annotation["bbox"]) == 4

            # Testar com caminho de saída especificado
            custom_output = os.path.join(annotations_dir, "custom_output.json")
            result = converter.export_to_coco(annotations_dir, images_dir, custom_output)
            assert result == custom_output

    @patch("os.path.exists")
    @patch("cv2.imread")
    def test_export_to_pascal_voc(self, mock_imread, mock_exists, converter, temp_dirs, sample_annotations):
        """Testa a exportação para formato Pascal VOC."""
        _, annotations_dir, images_dir, _ = temp_dirs

        # Configurar mocks
        mock_exists.return_value = True
        mock_image = MagicMock()
        mock_image.shape = (100, 100, 3)
        mock_imread.return_value = mock_image

        # Mock para glob
        with patch("glob.glob") as mock_glob:
            mock_glob.return_value = [os.path.join(annotations_dir, "test_image.txt")]

            # Exportar para VOC
            result = converter.export_to_pascal_voc(annotations_dir, images_dir)

            # Verificações
            assert os.path.isdir(result)
            assert mock_glob.called
            assert mock_imread.called

            # Verificar arquivo XML
            xml_path = os.path.join(result, "test_image.xml")
            assert os.path.exists(xml_path)

            # Testar com diretório de saída especificado
            custom_output = os.path.join(annotations_dir, "custom_voc")
            result = converter.export_to_pascal_voc(annotations_dir, images_dir, custom_output)
            assert result == custom_output
            assert os.path.exists(os.path.join(custom_output, "test_image.xml"))

    @patch("os.path.exists")
    def test_import_from_coco(self, mock_exists, converter, temp_dirs):
        """Testa a importação do formato COCO."""
        temp_dir, annotations_dir, images_dir, output_dir = temp_dirs

        # Configurar mocks
        mock_exists.return_value = True

        # Criar arquivo COCO de amostra
        coco_path = os.path.join(temp_dir, "annotations_coco.json")
        coco_data = {
            "images": [
                {"id": 1, "file_name": "test_image.jpg", "width": 100, "height": 100}
            ],
            "annotations": [
                {
                    "id": 1, "image_id": 1, "category_id": 0,
                    "bbox": [40, 40, 20, 20], "area": 400
                },
                {
                    "id": 2, "image_id": 1, "category_id": 1,
                    "bbox": [65, 65, 10, 10], "area": 100
                }
            ],
            "categories": [
                {"id": 0, "name": "levedura", "supercategory": "microorganism"},
                {"id": 1, "name": "fungo", "supercategory": "microorganism"},
                {"id": 2, "name": "micro-alga", "supercategory": "microorganism"}
            ]
        }

        with open(coco_path, "w") as f:
            json.dump(coco_data, f)

        # Importar do COCO
        result = converter.import_from_coco(coco_path, output_dir, images_dir)

        # Verificações
        assert result == 1  # Uma imagem importada
        assert os.path.exists(os.path.join(output_dir, "test_image.txt"))

        # Verificar conteúdo do arquivo YOLO
        with open(os.path.join(output_dir, "test_image.txt"), "r") as f:
            lines = f.readlines()

        assert len(lines) == 2

        # Verificar primeira linha (objeto central)
        parts = lines[0].strip().split()
        assert parts[0] == "0"  # class_id
        assert abs(float(parts[1]) - 0.5) < 0.01  # center_x próximo de 0.5
        assert abs(float(parts[2]) - 0.5) < 0.01  # center_y próximo de 0.5
        assert abs(float(parts[3]) - 0.2) < 0.01  # width próximo de 0.2
        assert abs(float(parts[4]) - 0.2) < 0.01  # height próximo de 0.2

        # Testar com erro
        with patch("builtins.open", side_effect=Exception("Erro de teste")):
            result = converter.import_from_coco(coco_path, output_dir, images_dir)
            assert result == 0

    @patch("os.path.exists")
    def test_import_from_pascal_voc(self, mock_exists, converter, temp_dirs):
        """Testa a importação do formato Pascal VOC."""
        temp_dir, annotations_dir, images_dir, output_dir = temp_dirs

        # Configurar mocks
        mock_exists.return_value = True

        # Criar diretório VOC
        voc_dir = os.path.join(temp_dir, "voc")
        os.makedirs(voc_dir, exist_ok=True)

        # Criar arquivo XML de amostra
        xml_content = """
        <annotation>
            <folder>images</folder>
            <filename>test_image.jpg</filename>
            <path>test_image.jpg</path>
            <source><database>Unknown</database></source>
            <size><width>100</width><height>100</height><depth>3</depth></size>
            <segmented>0</segmented>
            <object>
                <name>levedura</name>
                <pose>Unspecified</pose>
                <truncated>0</truncated>
                <difficult>0</difficult>
                <bndbox>
                    <xmin>40</xmin>
                    <ymin>40</ymin>
                    <xmax>60</xmax>
                    <ymax>60</ymax>
                </bndbox>
            </object>
            <object>
                <name>fungo</name>
                <pose>Unspecified</pose>
                <truncated>0</truncated>
                <difficult>0</difficult>
                <bndbox>
                    <xmin>65</xmin>
                    <ymin>65</ymin>
                    <xmax>75</xmax>
                    <ymax>75</ymax>
                </bndbox>
            </object>
        </annotation>
        """

        xml_path = os.path.join(voc_dir, "test_image.xml")
        with open(xml_path, "w") as f:
            f.write(xml_content)

        # Simular ambiente para defusedxml
        with patch("microdetect.annotation.export_import.safe_ET") as mock_ET:
            # Configurar o mock para ElementTree
            mock_root = MagicMock()
            mock_size = MagicMock()
            mock_size.find.side_effect = lambda tag: MagicMock(text="100") if tag in ["width",
                                                                                      "height"] else MagicMock()
            mock_root.find.return_value = mock_size

            # Configurar objetos
            mock_obj1 = MagicMock()
            mock_obj1.find.side_effect = lambda tag: MagicMock(text="levedura") if tag == "name" else MagicMock()
            mock_bbox1 = MagicMock()
            mock_bbox1.find.side_effect = lambda tag: MagicMock(
                text={"xmin": "40", "ymin": "40", "xmax": "60", "ymax": "60"}[tag])
            mock_obj1.find.return_value = mock_bbox1

            mock_obj2 = MagicMock()
            mock_obj2.find.side_effect = lambda tag: MagicMock(text="fungo") if tag == "name" else MagicMock()
            mock_bbox2 = MagicMock()
            mock_bbox2.find.side_effect = lambda tag: MagicMock(
                text={"xmin": "65", "ymin": "65", "xmax": "75", "ymax": "75"}[tag])
            mock_obj2.find.return_value = mock_bbox2

            mock_root.findall.return_value = [mock_obj1, mock_obj2]

            mock_tree = MagicMock()
            mock_tree.getroot.return_value = mock_root
            mock_ET.parse.return_value = mock_tree

            # Mock para glob
            with patch("glob.glob") as mock_glob:
                mock_glob.return_value = [xml_path]

                # Importar do VOC
                result = converter.import_from_pascal_voc(voc_dir, output_dir)

                # Verificações
                assert result == 1  # Uma imagem importada

                # Testar com erro
                with patch("builtins.open", side_effect=Exception("Erro de teste")):
                    result = converter.import_from_pascal_voc(voc_dir, output_dir)
                    assert result == 0


class TestCreateExportImportUI:

    @patch("microdetect.annotation.export_import.tk")
    @patch("microdetect.annotation.export_import.filedialog")
    @patch("microdetect.annotation.export_import.messagebox")
    @patch("microdetect.annotation.export_import.AnnotationConverter")
    def test_create_export_import_ui(self, MockConverter, mock_messagebox, mock_filedialog, mock_tk):
        """Testa a criação da interface de exportação/importação."""
        # Configurar mocks
        mock_parent = MagicMock()
        mock_toplevel = MagicMock()
        mock_tk.Toplevel.return_value = mock_toplevel
        mock_tk.StringVar = MagicMock
        mock_tk.BooleanVar = MagicMock
        mock_tk.LabelFrame = MagicMock
        mock_tk.Frame = MagicMock
        mock_tk.Label = MagicMock
        mock_tk.Entry = MagicMock
        mock_tk.Button = MagicMock
        mock_tk.Radiobutton = MagicMock
        mock_tk.Checkbutton = MagicMock

        # Simular seleção de diretório
        mock_filedialog.askdirectory.return_value = "/selected/dir"

        # Simular exportação bem-sucedida
        mock_converter = MagicMock()
        mock_converter.export_to_coco.return_value = "/path/to/output.json"
        mock_converter.export_to_pascal_voc.return_value = "/path/to/output_voc"
        MockConverter.return_value = mock_converter

        # Criar interface
        result = create_export_import_ui(mock_parent, "/path/to/images", "/path/to/annotations")

        # Verificações
        assert MockConverter.called
        assert mock_tk.Toplevel.called
        assert mock_toplevel.title.called
        assert mock_toplevel.geometry.called
        assert mock_toplevel.transient.called
        assert mock_toplevel.grab_set.called
        assert result == mock_toplevel

        # Testar funções de callback (browse, export, import)

        # Simular browse_output
        browse_output_fn = None
        for call in mock_tk.Button.call_args_list:
            if "Procurar" in str(call) and "command" in str(call):
                browse_output_fn = call[1]["command"]
                break

        assert browse_output_fn is not None
        browse_output_fn()
        assert mock_filedialog.askdirectory.called

        # Simular export_annotations
        export_fn = None
        for call in mock_tk.Button.call_args_list:
            if "Exportar" in str(call) and "command" in str(call):
                export_fn = call[1]["command"]
                break

        assert export_fn is not None

        # Testar exportação COCO
        with patch("microdetect.annotation.export_import.os") as mock_os:
            mock_os.path.join.side_effect = os.path.join
            export_fn()
            assert mock_converter.export_to_coco.called
            assert mock_messagebox.showinfo.called

        # Testar importação
        import_fn = None
        for call in mock_tk.Button.call_args_list:
            if "Importar" in str(call) and "command" in str(call):
                import_fn = call[1]["command"]
                break

        assert import_fn is not None

        # Testar importação sem selecionar arquivo
        mock_messagebox.reset_mock()
        import_fn()
        assert mock_messagebox.showwarning.called

        # Testar importação com arquivo selecionado
        with patch.object(mock_tk.StringVar, "get") as mock_get:
            mock_get.return_value = "/path/to/import.json"
            import_fn()
            assert mock_converter.import_from_coco.called