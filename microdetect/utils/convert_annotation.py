"""
Módulo para conversão entre formatos de anotação.

Suporta conversões entre os seguintes formatos:
- YOLO
- Pascal VOC
- COCO
- CSV
"""

import csv
import glob
import json
import os
from datetime import datetime
from typing import Dict, Optional, Tuple

import cv2
# Bibliotecas seguras para processamento XML
# defusedxml fornece proteção contra ataques como XXE (XML External Entity)
import defusedxml.ElementTree as secure_ET
from defusedxml.minidom import parseString as secure_parseString

# Usando ElementTree padrão apenas para construção de XML, não para parsing de dados externos
# Isso é seguro pois não estamos analisando conteúdo externo com estas funções
import xml.etree.ElementTree as ET

# Comentário sobre nossa abordagem de segurança:
# 1. Usamos ET (ElementTree padrão) para CONSTRUIR XML
# 2. Usamos secure_ET (defusedxml) para ANALISAR XML de fontes externas
# 3. Evitamos vulnerabilidades como XXE attacks, billion laughs, quadratic blowup

from microdetect.utils.config import config


def yolo_to_absolute_coords(
    yolo_box: Tuple[float, float, float, float], img_width: int, img_height: int
) -> Tuple[int, int, int, int]:
    """
    Converte coordenadas YOLO normalizadas para coordenadas absolutas.

    Args:
        yolo_box: Tupla (center_x, center_y, width, height) em formato YOLO (valores normalizados)
        img_width: Largura da imagem
        img_height: Altura da imagem

    Returns:
        Tupla (x1, y1, x2, y2) em coordenadas absolutas de pixel
    """
    center_x, center_y, width, height = yolo_box

    # Converter para valores absolutos
    center_x *= img_width
    center_y *= img_height
    width *= img_width
    height *= img_height

    # Calcular coordenadas x1, y1, x2, y2
    x1 = int(center_x - width / 2)
    y1 = int(center_y - height / 2)
    x2 = int(center_x + width / 2)
    y2 = int(center_y + height / 2)

    return x1, y1, x2, y2


def absolute_to_yolo_coords(
    box: Tuple[int, int, int, int], img_width: int, img_height: int
) -> Tuple[float, float, float, float]:
    """
    Converte coordenadas absolutas para o formato YOLO normalizado.

    Args:
        box: Tupla (x1, y1, x2, y2) em coordenadas absolutas de pixel
        img_width: Largura da imagem
        img_height: Altura da imagem

    Returns:
        Tupla (center_x, center_y, width, height) em formato YOLO (valores normalizados)
    """
    x1, y1, x2, y2 = box

    # Calcular valores em coordenadas absolutas
    width = x2 - x1
    height = y2 - y1
    center_x = x1 + width / 2
    center_y = y1 + height / 2

    # Normalizar
    center_x /= img_width
    center_y /= img_height
    width /= img_width
    height /= img_height

    return center_x, center_y, width, height


def yolo_to_pascal_voc(yolo_dir: str, image_dir: str, output_dir: str, class_map: Optional[Dict[str, str]] = None) -> int:
    """
    Converte anotações do formato YOLO para Pascal VOC XML.

    Args:
        yolo_dir: Diretório contendo anotações YOLO (.txt)
        image_dir: Diretório contendo as imagens correspondentes
        output_dir: Diretório para salvar arquivos XML
        class_map: Mapeamento de IDs de classe para nomes (ex: {"0": "levedura"})

    Returns:
        Número de arquivos convertidos
    """
    os.makedirs(output_dir, exist_ok=True)

    # Obter mapeamento de classes
    if class_map is None:
        classes = config.get("classes", ["0-levedura", "1-fungo", "2-micro-alga"])
        class_map = {}
        for cls in classes:
            parts = cls.split("-", 1)
            if len(parts) == 2:
                class_map[parts[0]] = parts[1]

    converted_count = 0

    # Processar cada arquivo de anotação YOLO
    for txt_file in glob.glob(os.path.join(yolo_dir, "*.txt")):
        base_name = os.path.splitext(os.path.basename(txt_file))[0]

        # Encontrar imagem correspondente
        img_path = None
        for ext in [".jpg", ".jpeg", ".png"]:
            possible_path = os.path.join(image_dir, f"{base_name}{ext}")
            if os.path.exists(possible_path):
                img_path = possible_path
                break

        if img_path is None:
            print(f"Imagem não encontrada para {base_name}. Pulando...")
            continue

        # Ler dimensões da imagem
        img = cv2.imread(img_path)
        if img is None:
            print(f"Erro ao ler imagem {img_path}. Pulando...")
            continue

        img_height, img_width, img_depth = img.shape

        # Criar estrutura XML Pascal VOC
        annotation = ET.Element("annotation")

        # Adicionar informações do arquivo
        folder = ET.SubElement(annotation, "folder")
        folder.text = os.path.basename(os.path.dirname(img_path))

        filename = ET.SubElement(annotation, "filename")
        filename.text = os.path.basename(img_path)

        path = ET.SubElement(annotation, "path")
        path.text = img_path

        # Adicionar informações da fonte
        source = ET.SubElement(annotation, "source")
        database = ET.SubElement(source, "database")
        database.text = "MicroDetect"

        # Adicionar informações do tamanho
        size = ET.SubElement(annotation, "size")
        width = ET.SubElement(size, "width")
        width.text = str(img_width)
        height = ET.SubElement(size, "height")
        height.text = str(img_height)
        depth = ET.SubElement(size, "depth")
        depth.text = str(img_depth)

        # Adicionar flag de segmentação
        segmented = ET.SubElement(annotation, "segmented")
        segmented.text = "0"

        # Ler anotações YOLO
        with open(txt_file, "r") as f:
            lines = f.readlines()

        # Processar cada linha de anotação
        for line in lines:
            parts = line.strip().split()
            if len(parts) != 5:
                continue

            class_id, center_x, center_y, width_norm, height_norm = parts

            # Converter para float
            center_x = float(center_x)
            center_y = float(center_y)
            width_norm = float(width_norm)
            height_norm = float(height_norm)

            # Converter para coordenadas absolutas
            x1, y1, x2, y2 = yolo_to_absolute_coords((center_x, center_y, width_norm, height_norm), img_width, img_height)

            # Garantir que as coordenadas estão dentro dos limites da imagem
            x1 = max(0, min(x1, img_width - 1))
            y1 = max(0, min(y1, img_height - 1))
            x2 = max(0, min(x2, img_width - 1))
            y2 = max(0, min(y2, img_height - 1))

            # Obter nome da classe
            class_name = class_map.get(class_id, f"class_{class_id}")

            # Adicionar objeto ao XML
            obj = ET.SubElement(annotation, "object")

            name = ET.SubElement(obj, "name")
            name.text = class_name

            pose = ET.SubElement(obj, "pose")
            pose.text = "Unspecified"

            truncated = ET.SubElement(obj, "truncated")
            truncated.text = "0"

            difficult = ET.SubElement(obj, "difficult")
            difficult.text = "0"

            bndbox = ET.SubElement(obj, "bndbox")

            xmin = ET.SubElement(bndbox, "xmin")
            xmin.text = str(x1)

            ymin = ET.SubElement(bndbox, "ymin")
            ymin.text = str(y1)

            xmax = ET.SubElement(bndbox, "xmax")
            xmax.text = str(x2)

            ymax = ET.SubElement(bndbox, "ymax")
            ymax.text = str(y2)

        # Criar árvore XML e salvar
        tree = ET.ElementTree(annotation)
        xml_path = os.path.join(output_dir, f"{base_name}.xml")

        # Converter para string usando ElementTree padrão e então analisar com defusedxml
        xml_string = ET.tostring(annotation, encoding='utf-8')
        # Usar defusedxml para analisar a string XML, garantindo segurança no parsing
        xmlstr = secure_parseString(xml_string).toprettyxml(indent="    ")
        with open(xml_path, "w") as f:
            f.write(xmlstr)

        converted_count += 1

    print(f"Conversão concluída: {converted_count} arquivos convertidos para Pascal VOC XML")
    return converted_count


def pascal_voc_to_yolo(xml_dir: str, image_dir: str, output_dir: str, class_map: Optional[Dict[str, str]] = None) -> int:
    """
    Converte anotações do formato Pascal VOC XML para YOLO.

    Args:
        xml_dir: Diretório contendo arquivos XML Pascal VOC
        image_dir: Diretório contendo as imagens correspondentes
        output_dir: Diretório para salvar arquivos YOLO (.txt)
        class_map: Mapeamento de nomes de classe para IDs (ex: {"levedura": "0"})

    Returns:
        Número de arquivos convertidos
    """
    os.makedirs(output_dir, exist_ok=True)

    # Criar mapeamento inverso de classes se não fornecido
    if class_map is None:
        classes = config.get("classes", ["0-levedura", "1-fungo", "2-micro-alga"])
        class_map = {}
        for cls in classes:
            parts = cls.split("-", 1)
            if len(parts) == 2:
                class_map[parts[1]] = parts[0]  # Inverso do anterior: nome -> id

    converted_count = 0

    # Processar cada arquivo XML
    for xml_file in glob.glob(os.path.join(xml_dir, "*.xml")):
        base_name = os.path.splitext(os.path.basename(xml_file))[0]

        try:
            # Ler arquivo XML usando defusedxml para segurança contra ataques
            with open(xml_file, 'rb') as f:
                xml_data = f.read()
            # Analisar de forma segura o XML usando defusedxml
            root = secure_ET.fromstring(xml_data)

            # Obter dimensões da imagem
            size_elem = root.find("size")
            if size_elem is None:
                print(f"Erro: Tag 'size' não encontrada em {xml_file}. Pulando...")
                continue

            img_width = int(size_elem.find("width").text)
            img_height = int(size_elem.find("height").text)

            # Abrir arquivo de saída YOLO
            output_file = os.path.join(output_dir, f"{base_name}.txt")
            with open(output_file, "w") as f:
                # Processar cada objeto
                for obj in root.findall("object"):
                    class_name = obj.find("name").text.strip()

                    # Obter ID da classe
                    class_id = class_map.get(class_name)
                    if class_id is None:
                        # Tentar buscar por correspondência parcial
                        for name, id_val in class_map.items():
                            if name in class_name or class_name in name:
                                class_id = id_val
                                break

                    # Se ainda não encontrou, usar um valor padrão
                    if class_id is None:
                        print(f"Aviso: Classe '{class_name}' não encontrada no mapeamento. Usando '0'.")
                        class_id = "0"

                    # Obter coordenadas da bounding box
                    bndbox = obj.find("bndbox")
                    x1 = int(bndbox.find("xmin").text)
                    y1 = int(bndbox.find("ymin").text)
                    x2 = int(bndbox.find("xmax").text)
                    y2 = int(bndbox.find("ymax").text)

                    # Converter para formato YOLO
                    center_x, center_y, width, height = absolute_to_yolo_coords((x1, y1, x2, y2), img_width, img_height)

                    # Escrever no arquivo YOLO
                    f.write(f"{class_id} {center_x:.6f} {center_y:.6f} {width:.6f} {height:.6f}\n")

            converted_count += 1

        except Exception as e:
            print(f"Erro ao processar {xml_file}: {str(e)}")

    print(f"Conversão concluída: {converted_count} arquivos convertidos para YOLO")
    return converted_count


def yolo_to_coco(yolo_dir: str, image_dir: str, output_json: str, class_map: Optional[Dict[str, str]] = None) -> Dict:
    """
    Converte anotações do formato YOLO para COCO JSON.

    Args:
        yolo_dir: Diretório contendo anotações YOLO (.txt)
        image_dir: Diretório contendo as imagens correspondentes
        output_json: Caminho para o arquivo JSON COCO de saída
        class_map: Mapeamento de IDs de classe para nomes (ex: {"0": "levedura"})

    Returns:
        Dicionário COCO criado
    """
    # Obter mapeamento de classes
    if class_map is None:
        classes = config.get("classes", ["0-levedura", "1-fungo", "2-micro-alga"])
        class_map = {}
        for cls in classes:
            parts = cls.split("-", 1)
            if len(parts) == 2:
                class_map[parts[0]] = parts[1]

    # Criar estrutura COCO
    coco_json = {
        "info": {
            "description": "MicroDetect Dataset",
            "url": "",
            "version": "1.0",
            "year": datetime.now().year,
            "contributor": "MicroDetect",
            "date_created": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        },
        "licenses": [{"id": 1, "name": "Unknown", "url": ""}],
        "categories": [],
        "images": [],
        "annotations": [],
    }

    # Adicionar categorias
    categories = {}
    for class_id, class_name in class_map.items():
        cat_id = int(class_id) + 1  # COCO IDs começam em 1
        coco_json["categories"].append({"id": cat_id, "name": class_name, "supercategory": "microorganism"})
        categories[class_id] = cat_id

    image_id = 0
    annotation_id = 0

    # Processar cada arquivo de anotação YOLO
    for txt_file in glob.glob(os.path.join(yolo_dir, "*.txt")):
        base_name = os.path.splitext(os.path.basename(txt_file))[0]

        # Encontrar imagem correspondente
        img_path = None
        for ext in [".jpg", ".jpeg", ".png"]:
            possible_path = os.path.join(image_dir, f"{base_name}{ext}")
            if os.path.exists(possible_path):
                img_path = possible_path
                break

        if img_path is None:
            print(f"Imagem não encontrada para {base_name}. Pulando...")
            continue

        # Ler dimensões da imagem
        img = cv2.imread(img_path)
        if img is None:
            print(f"Erro ao ler imagem {img_path}. Pulando...")
            continue

        img_height, img_width, _ = img.shape

        # Adicionar imagem ao COCO
        image_id += 1
        coco_json["images"].append(
            {
                "id": image_id,
                "file_name": os.path.basename(img_path),
                "width": img_width,
                "height": img_height,
                "license": 1,
                "date_captured": "",
            }
        )

        # Ler anotações YOLO
        try:
            with open(txt_file, "r") as f:
                lines = f.readlines()

            for line in lines:
                parts = line.strip().split()
                if len(parts) != 5:
                    continue

                class_id, center_x, center_y, width_norm, height_norm = parts

                # Converter para float
                center_x = float(center_x)
                center_y = float(center_y)
                width_norm = float(width_norm)
                height_norm = float(height_norm)

                # Converter para coordenadas absolutas
                x1, y1, x2, y2 = yolo_to_absolute_coords((center_x, center_y, width_norm, height_norm), img_width, img_height)

                # Calcular largura e altura
                width = x2 - x1
                height = y2 - y1

                # Obter categoria COCO
                category_id = categories.get(class_id)
                if category_id is None:
                    print(f"Aviso: Classe {class_id} não encontrada no mapeamento. Pulando...")
                    continue

                # Adicionar anotação ao COCO
                annotation_id += 1
                coco_json["annotations"].append(
                    {
                        "id": annotation_id,
                        "image_id": image_id,
                        "category_id": category_id,
                        "bbox": [x1, y1, width, height],
                        "area": width * height,
                        "segmentation": [],
                        "iscrowd": 0,
                    }
                )

        except Exception as e:
            print(f"Erro ao processar {txt_file}: {str(e)}")

    # Salvar JSON COCO
    with open(output_json, "w") as f:
        json.dump(coco_json, f, indent=2)

    print(
        f"Conversão concluída: {len(coco_json['images'])} imagens e "
        f"{len(coco_json['annotations'])} anotações convertidas para COCO"
    )

    return coco_json


def coco_to_yolo(coco_json: str, output_dir: str, class_map: Optional[Dict[int, str]] = None) -> int:
    """
    Converte anotações do formato COCO JSON para YOLO.

    Args:
        coco_json: Caminho para o arquivo JSON COCO ou dicionário COCO
        output_dir: Diretório para salvar arquivos YOLO (.txt)
        class_map: Mapeamento de IDs COCO para IDs YOLO (ex: {1: "0"})

    Returns:
        Número de imagens processadas
    """
    os.makedirs(output_dir, exist_ok=True)

    # Carregar JSON COCO
    if isinstance(coco_json, str):
        with open(coco_json, "r") as f:
            coco_data = json.load(f)
    else:
        coco_data = coco_json

    # Criar mapeamento de categorias se não fornecido
    if class_map is None:
        class_map = {}
        for category in coco_data["categories"]:
            # Converter IDs COCO (que começam em 1) para IDs YOLO (geralmente começam em 0)
            class_map[category["id"]] = str(category["id"] - 1)

    # Criar mapeamento de imagens por ID
    images_by_id = {}
    for image in coco_data["images"]:
        images_by_id[image["id"]] = image

    # Agrupar anotações por imagem
    annotations_by_image = {}
    for ann in coco_data["annotations"]:
        image_id = ann["image_id"]
        if image_id not in annotations_by_image:
            annotations_by_image[image_id] = []
        annotations_by_image[image_id].append(ann)

    # Processar cada imagem
    processed_count = 0
    for image_id, annotations in annotations_by_image.items():
        image = images_by_id.get(image_id)
        if image is None:
            continue

        image_width = image["width"]
        image_height = image["height"]

        # Nome base do arquivo
        file_name = os.path.splitext(image["file_name"])[0]
        output_file = os.path.join(output_dir, f"{file_name}.txt")

        with open(output_file, "w") as f:
            for ann in annotations:
                # Obter categoria e converter para ID YOLO
                coco_category_id = ann["category_id"]
                class_id = class_map.get(coco_category_id)

                if class_id is None:
                    print(f"Aviso: Categoria COCO {coco_category_id} não encontrada no mapeamento. Pulando...")
                    continue

                # Obter bounding box no formato COCO [x, y, width, height]
                x, y, width, height = ann["bbox"]

                # Converter para formato YOLO
                x1, y1 = x, y
                x2, y2 = x + width, y + height

                center_x, center_y, width_norm, height_norm = absolute_to_yolo_coords(
                    (x1, y1, x2, y2), image_width, image_height
                )

                # Escrever no arquivo YOLO
                f.write(f"{class_id} {center_x:.6f} {center_y:.6f} {width_norm:.6f} {height_norm:.6f}\n")

        processed_count += 1

    print(f"Conversão concluída: {processed_count} imagens convertidas para YOLO")
    return processed_count
    print(f"Conversão concluída: {processed_count} imagens convertidas para YOLO")
    return processed_count


def yolo_to_csv(yolo_dir: str, image_dir: str, output_csv: str, class_map: Optional[Dict[str, str]] = None) -> int:
    """
    Converte anotações do formato YOLO para CSV.

    Args:
        yolo_dir: Diretório contendo anotações YOLO (.txt)
        image_dir: Diretório contendo as imagens correspondentes
        output_csv: Caminho para o arquivo CSV de saída
        class_map: Mapeamento de IDs de classe para nomes (ex: {"0": "levedura"})

    Returns:
        Número de anotações convertidas
    """
    # Obter mapeamento de classes
    if class_map is None:
        classes = config.get("classes", ["0-levedura", "1-fungo", "2-micro-alga"])
        class_map = {}
        for cls in classes:
            parts = cls.split("-", 1)
            if len(parts) == 2:
                class_map[parts[0]] = parts[1]

    # Criar arquivo CSV
    with open(output_csv, "w", newline="") as csvfile:
        csv_writer = csv.writer(csvfile)

        # Escrever cabeçalho
        csv_writer.writerow(["filename", "width", "height", "class", "class_id", "xmin", "ymin", "xmax", "ymax"])

        # Processar cada arquivo de anotação YOLO
        annotation_count = 0
        for txt_file in glob.glob(os.path.join(yolo_dir, "*.txt")):
            base_name = os.path.splitext(os.path.basename(txt_file))[0]

            # Encontrar imagem correspondente
            img_path = None
            for ext in [".jpg", ".jpeg", ".png"]:
                possible_path = os.path.join(image_dir, f"{base_name}{ext}")
                if os.path.exists(possible_path):
                    img_path = possible_path
                    break

            if img_path is None:
                print(f"Imagem não encontrada para {base_name}. Pulando...")
                continue

            # Ler dimensões da imagem
            img = cv2.imread(img_path)
            if img is None:
                print(f"Erro ao ler imagem {img_path}. Pulando...")
                continue

            img_height, img_width, _ = img.shape

            # Ler anotações YOLO
            try:
                with open(txt_file, "r") as f:
                    lines = f.readlines()

                for line in lines:
                    parts = line.strip().split()
                    if len(parts) != 5:
                        continue

                    class_id, center_x, center_y, width_norm, height_norm = parts

                    # Converter para float
                    center_x = float(center_x)
                    center_y = float(center_y)
                    width_norm = float(width_norm)
                    height_norm = float(height_norm)

                    # Converter para coordenadas absolutas
                    x1, y1, x2, y2 = yolo_to_absolute_coords(
                        (center_x, center_y, width_norm, height_norm), img_width, img_height
                    )

                    # Obter nome da classe
                    class_name = class_map.get(class_id, f"class_{class_id}")

                    # Escrever no CSV
                    csv_writer.writerow(
                        [os.path.basename(img_path), img_width, img_height, class_name, class_id, x1, y1, x2, y2]
                    )

                    annotation_count += 1

            except Exception as e:
                print(f"Erro ao processar {txt_file}: {str(e)}")

    print(f"Conversão concluída: {annotation_count} anotações convertidas para CSV")
    return annotation_count


def csv_to_yolo(csv_file: str, output_dir: str, class_map: Optional[Dict[str, str]] = None) -> int:
    """
    Converte anotações do formato CSV para YOLO.

    Args:
        csv_file: Caminho para o arquivo CSV contendo anotações
        output_dir: Diretório para salvar arquivos YOLO (.txt)
        class_map: Mapeamento de nomes de classe para IDs (ex: {"levedura": "0"})

    Returns:
        Número de imagens processadas
    """
    os.makedirs(output_dir, exist_ok=True)

    # Criar mapeamento inverso de classes se não fornecido
    if class_map is None:
        classes = config.get("classes", ["0-levedura", "1-fungo", "2-micro-alga"])
        class_map = {}
        for cls in classes:
            parts = cls.split("-", 1)
            if len(parts) == 2:
                class_map[parts[1]] = parts[0]  # Inverso do anterior: nome -> id

    # Agrupar anotações por arquivo
    annotations_by_file = {}
    image_dimensions = {}

    with open(csv_file, "r", newline="") as csvfile:
        csv_reader = csv.DictReader(csvfile)

        for row in csv_reader:
            filename = row["filename"]

            # Armazenar dimensões da imagem
            if filename not in image_dimensions:
                image_dimensions[filename] = (int(row["width"]), int(row["height"]))

            # Agrupar anotações por arquivo
            if filename not in annotations_by_file:
                annotations_by_file[filename] = []

            # Obter ID da classe
            class_id = row.get("class_id")
            if class_id is None or class_id == "":
                class_name = row["class"]
                class_id = class_map.get(class_name)
                if class_id is None:
                    print(f"Aviso: Classe '{class_name}' não encontrada no mapeamento. Usando '0'.")
                    class_id = "0"

            # Adicionar anotação
            annotations_by_file[filename].append(
                {
                    "class_id": class_id,
                    "xmin": int(row["xmin"]),
                    "ymin": int(row["ymin"]),
                    "xmax": int(row["xmax"]),
                    "ymax": int(row["ymax"]),
                }
            )

    # Processar cada arquivo
    processed_count = 0
    for filename, annotations in annotations_by_file.items():
        # Obter dimensões da imagem
        img_width, img_height = image_dimensions[filename]

        # Nome base do arquivo
        base_name = os.path.splitext(filename)[0]
        output_file = os.path.join(output_dir, f"{base_name}.txt")

        with open(output_file, "w") as f:
            for ann in annotations:
                # Obter coordenadas da bounding box
                x1 = ann["xmin"]
                y1 = ann["ymin"]
                x2 = ann["xmax"]
                y2 = ann["ymax"]

                # Converter para formato YOLO
                center_x, center_y, width, height = absolute_to_yolo_coords((x1, y1, x2, y2), img_width, img_height)

                # Escrever no arquivo YOLO
                f.write(f"{ann['class_id']} {center_x:.6f} {center_y:.6f} {width:.6f} {height:.6f}\n")

        processed_count += 1

    print(f"Conversão concluída: {processed_count} imagens convertidas para YOLO")
    return processed_count
