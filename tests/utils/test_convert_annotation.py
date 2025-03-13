"""
Testes unitários para o módulo de conversão de anotações.
"""

import csv
import json
import os
import tempfile
import unittest
import xml.etree.ElementTree as ET

import cv2
import numpy as np

from microdetect.utils import (
    yolo_to_pascal_voc,
    pascal_voc_to_yolo,
    yolo_to_coco,
    coco_to_yolo,
    yolo_to_csv,
    csv_to_yolo,
    yolo_to_absolute_coords,
    absolute_to_yolo_coords
)


class TestConvertAnnotations(unittest.TestCase):
    """
    Testes para as funções de conversão de anotações.
    """

    def setUp(self):
        """
        Configuração dos testes.
        """
        # Criar diretório temporário para testes
        self.temp_dir = tempfile.TemporaryDirectory()

        # Criar subdiretórios
        self.yolo_dir = os.path.join(self.temp_dir.name, "yolo")
        self.voc_dir = os.path.join(self.temp_dir.name, "voc")
        self.coco_dir = os.path.join(self.temp_dir.name, "coco")
        self.csv_dir = os.path.join(self.temp_dir.name, "csv")
        self.img_dir = os.path.join(self.temp_dir.name, "images")

        os.makedirs(self.yolo_dir, exist_ok=True)
        os.makedirs(self.voc_dir, exist_ok=True)
        os.makedirs(self.coco_dir, exist_ok=True)
        os.makedirs(self.csv_dir, exist_ok=True)
        os.makedirs(self.img_dir, exist_ok=True)

        # Criar imagem de teste
        self.test_image = np.ones((100, 100, 3), dtype=np.uint8) * 255  # Imagem branca
        self.test_image_path = os.path.join(self.img_dir, "test_image.jpg")
        cv2.imwrite(self.test_image_path, self.test_image)

        # Criar anotação YOLO de teste
        self.yolo_annotation = "0 0.5 0.5 0.2 0.2\n1 0.7 0.7 0.1 0.1"
        self.yolo_path = os.path.join(self.yolo_dir, "test_image.txt")
        with open(self.yolo_path, "w") as f:
            f.write(self.yolo_annotation)

        # Mapeamento de classes
        self.class_map = {
            "0": "levedura",
            "1": "fungo",
            "2": "micro-alga"
        }

        self.class_map_inverse = {
            "levedura": "0",
            "fungo": "1",
            "micro-alga": "2"
        }

    def tearDown(self):
        """
        Limpeza após os testes.
        """
        self.temp_dir.cleanup()

    def test_yolo_to_absolute_coords(self):
        """
        Testa a conversão de coordenadas YOLO para absolutas.
        """
        # Objeto central 20x20 em imagem 100x100
        yolo_box = (0.5, 0.5, 0.2, 0.2)
        img_width, img_height = 100, 100

        x1, y1, x2, y2 = yolo_to_absolute_coords(
            yolo_box, img_width, img_height
        )

        self.assertEqual(x1, 40)
        self.assertEqual(y1, 40)
        self.assertEqual(x2, 60)
        self.assertEqual(y2, 60)

    def test_absolute_to_yolo_coords(self):
        """
        Testa a conversão de coordenadas absolutas para YOLO.
        """
        # Caixa de 20x20 no centro de uma imagem 100x100
        box = (40, 40, 60, 60)
        img_width, img_height = 100, 100

        center_x, center_y, width, height = absolute_to_yolo_coords(
            box, img_width, img_height
        )

        self.assertAlmostEqual(center_x, 0.5)
        self.assertAlmostEqual(center_y, 0.5)
        self.assertAlmostEqual(width, 0.2)
        self.assertAlmostEqual(height, 0.2)

    def test_yolo_to_pascal_voc(self):
        """
        Testa a conversão de YOLO para Pascal VOC.
        """
        output_dir = os.path.join(self.temp_dir.name, "output_voc")

        count = yolo_to_pascal_voc(
            self.yolo_dir,
            self.img_dir,
            output_dir,
            self.class_map
        )

        # Verificar número de conversões
        self.assertEqual(count, 1)

        # Verificar arquivo XML
        xml_path = os.path.join(output_dir, "test_image.xml")
        self.assertTrue(os.path.exists(xml_path))

        # Analisar XML
        tree = ET.parse(xml_path)
        root = tree.getroot()

        # Verificar formato básico
        self.assertEqual(root.tag, "annotation")
        self.assertEqual(root.find("filename").text, "test_image.jpg")

        # Verificar objetos
        objects = root.findall("object")
        self.assertEqual(len(objects), 2)

        # Verificar primeiro objeto
        obj1 = objects[0]
        self.assertEqual(obj1.find("name").text, "levedura")

        bbox1 = obj1.find("bndbox")
        self.assertEqual(int(bbox1.find("xmin").text), 40)
        self.assertEqual(int(bbox1.find("ymin").text), 40)
        self.assertEqual(int(bbox1.find("xmax").text), 60)
        self.assertEqual(int(bbox1.find("ymax").text), 60)

    def test_pascal_voc_to_yolo(self):
        """
        Testa a conversão de Pascal VOC para YOLO.
        """
        # Primeiro criar arquivo VOC
        voc_xml = """
        <annotation>
            <folder>images</folder>
            <filename>test_image.jpg</filename>
            <path>test_image.jpg</path>
            <source><database>MicroDetect</database></source>
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

        voc_path = os.path.join(self.voc_dir, "test_image.xml")
        with open(voc_path, "w") as f:
            f.write(voc_xml)

        # Converter para YOLO
        output_dir = os.path.join(self.temp_dir.name, "output_yolo")

        count = pascal_voc_to_yolo(
            self.voc_dir,
            self.img_dir,
            output_dir,
            self.class_map_inverse
        )

        # Verificar número de conversões
        self.assertEqual(count, 1)

        # Verificar arquivo YOLO
        yolo_path = os.path.join(output_dir, "test_image.txt")
        self.assertTrue(os.path.exists(yolo_path))

        # Verificar conteúdo
        with open(yolo_path, "r") as f:
            lines = f.readlines()

        self.assertEqual(len(lines), 2)

        # Verificar primeira linha (objeto central)
        parts1 = lines[0].strip().split()
        self.assertEqual(parts1[0], "0")  # levedura
        self.assertAlmostEqual(float(parts1[1]), 0.5)  # center_x
        self.assertAlmostEqual(float(parts1[2]), 0.5)  # center_y
        self.assertAlmostEqual(float(parts1[3]), 0.2)  # width
        self.assertAlmostEqual(float(parts1[4]), 0.2)  # height

    def test_yolo_to_coco(self):
        """
        Testa a conversão de YOLO para COCO.
        """
        output_json = os.path.join(self.temp_dir.name, "output.json")

        coco_data = yolo_to_coco(
            self.yolo_dir,
            self.img_dir,
            output_json,
            self.class_map
        )

        # Verificar arquivo JSON
        self.assertTrue(os.path.exists(output_json))

        # Verificar estrutura COCO
        self.assertIn("images", coco_data)
        self.assertIn("annotations", coco_data)
        self.assertIn("categories", coco_data)

        # Verificar imagens
        self.assertEqual(len(coco_data["images"]), 1)
        self.assertEqual(coco_data["images"][0]["file_name"], "test_image.jpg")

        # Verificar anotações
        self.assertEqual(len(coco_data["annotations"]), 2)

        # Verificar categorias
        self.assertEqual(len(coco_data["categories"]), 3)
        self.assertEqual(coco_data["categories"][0]["name"], "levedura")

    def test_coco_to_yolo(self):
        """
        Testa a conversão de COCO para YOLO.
        """
        # Criar arquivo COCO
        coco_data = {
            "images": [
                {
                    "id": 1,
                    "file_name": "test_image.jpg",
                    "width": 100,
                    "height": 100
                }
            ],
            "annotations": [
                {
                    "id": 1,
                    "image_id": 1,
                    "category_id": 1,
                    "bbox": [40, 40, 20, 20],
                    "area": 400,
                    "segmentation": [],
                    "iscrowd": 0
                },
                {
                    "id": 2,
                    "image_id": 1,
                    "category_id": 2,
                    "bbox": [65, 65, 10, 10],
                    "area": 100,
                    "segmentation": [],
                    "iscrowd": 0
                }
            ],
            "categories": [
                {"id": 1, "name": "levedura", "supercategory": "microorganism"},
                {"id": 2, "name": "fungo", "supercategory": "microorganism"},
                {"id": 3, "name": "micro-alga", "supercategory": "microorganism"}
            ]
        }

        coco_path = os.path.join(self.coco_dir, "annotations.json")
        with open(coco_path, "w") as f:
            json.dump(coco_data, f)

        # Converter para YOLO
        output_dir = os.path.join(self.temp_dir.name, "output_yolo_from_coco")

        # Criar mapeamento de categorias COCO para YOLO
        coco_class_map = {
            1: "0",  # COCO id -> YOLO id
            2: "1",
            3: "2"
        }

        count = coco_to_yolo(
            coco_path,
            output_dir,
            coco_class_map
        )

        # Verificar número de conversões
        self.assertEqual(count, 1)

        # Verificar arquivo YOLO
        yolo_path = os.path.join(output_dir, "test_image.txt")
        self.assertTrue(os.path.exists(yolo_path))

        # Verificar conteúdo
        with open(yolo_path, "r") as f:
            lines = f.readlines()

        self.assertEqual(len(lines), 2)

        # Verificar primeira linha (objeto central)
        parts1 = lines[0].strip().split()
        self.assertEqual(parts1[0], "0")  # levedura
        self.assertAlmostEqual(float(parts1[1]), 0.5)  # center_x
        self.assertAlmostEqual(float(parts1[2]), 0.5)  # center_y
        self.assertAlmostEqual(float(parts1[3]), 0.2)  # width
        self.assertAlmostEqual(float(parts1[4]), 0.2)  # height

    def test_yolo_to_csv(self):
        """
        Testa a conversão de YOLO para CSV.
        """
        output_csv = os.path.join(self.temp_dir.name, "output.csv")

        count = yolo_to_csv(
            self.yolo_dir,
            self.img_dir,
            output_csv,
            self.class_map
        )

        # Verificar arquivo CSV
        self.assertTrue(os.path.exists(output_csv))

        # Ler arquivo CSV
        with open(output_csv, "r", newline="") as f:
            reader = csv.reader(f)
            header = next(reader)
            rows = list(reader)

        # Verificar cabeçalho
        expected_header = [
            "filename", "width", "height", "class", "class_id",
            "xmin", "ymin", "xmax", "ymax"
        ]
        self.assertEqual(header, expected_header)

        # Verificar anotações
        self.assertEqual(len(rows), 2)

        # Verificar primeira linha
        self.assertEqual(rows[0][0], "test_image.jpg")  # filename
        self.assertEqual(rows[0][3], "levedura")  # class
        self.assertEqual(rows[0][4], "0")  # class_id
        self.assertEqual(int(rows[0][5]), 40)  # xmin
        self.assertEqual(int(rows[0][6]), 40)  # ymin
        self.assertEqual(int(rows[0][7]), 60)  # xmax
        self.assertEqual(int(rows[0][8]), 60)  # ymax

    def test_csv_to_yolo(self):
        """
        Testa a conversão de CSV para YOLO.
        """
        # Criar arquivo CSV
        csv_path = os.path.join(self.csv_dir, "annotations.csv")
        with open(csv_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                "filename", "width", "height", "class", "class_id",
                "xmin", "ymin", "xmax", "ymax"
            ])
            writer.writerow([
                "test_image.jpg", 100, 100, "levedura", "0", 40, 40, 60, 60
            ])
            writer.writerow([
                "test_image.jpg", 100, 100, "fungo", "1", 65, 65, 75, 75
            ])

        # Converter para YOLO
        output_dir = os.path.join(self.temp_dir.name, "output_yolo_from_csv")

        count = csv_to_yolo(
            csv_path,
            output_dir,
            self.class_map_inverse
        )

        # Verificar número de conversões
        self.assertEqual(count, 1)

        # Verificar arquivo YOLO
        yolo_path = os.path.join(output_dir, "test_image.txt")
        self.assertTrue(os.path.exists(yolo_path))

        # Verificar conteúdo
        with open(yolo_path, "r") as f:
            lines = f.readlines()

        self.assertEqual(len(lines), 2)

        # Verificar primeira linha (objeto central)
        parts1 = lines[0].strip().split()
        self.assertEqual(parts1[0], "0")  # levedura
        self.assertAlmostEqual(float(parts1[1]), 0.5)  # center_x
        self.assertAlmostEqual(float(parts1[2]), 0.5)  # center_y
        self.assertAlmostEqual(float(parts1[3]), 0.2)  # width
        self.assertAlmostEqual(float(parts1[4]), 0.2)  # height


if __name__ == "__main__":
    unittest.main()