"""
Módulo para exportação e importação de anotações em diferentes formatos.
"""

import glob
import json
import logging
import os
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import List, Optional, Any

import cv2

from microdetect.utils.config import config

logger = logging.getLogger(__name__)


class AnnotationConverter:
    """
    Classe para converter anotações entre diferentes formatos.
    """

    def __init__(self, classes: List[str] = None):
        """
        Inicializa o conversor de anotações.

        Args:
            classes: Lista de classes para anotação
        """
        self.classes = classes or config.get("classes", ["0-levedura", "1-fungo", "2-micro-alga"])
        self.class_map = {cls.split('-')[0]: cls for cls in self.classes}

    def export_to_coco(self, annotations_dir: str, images_dir: str, output_path: Optional[str] = None) -> str:
        """
        Exporta anotações no formato YOLO para o formato COCO JSON.

        Args:
            annotations_dir: Diretório contendo anotações YOLO (.txt)
            images_dir: Diretório contendo as imagens relacionadas
            output_path: Caminho para salvar o arquivo JSON (opcional)

        Returns:
            Caminho para o arquivo JSON exportado
        """
        logger.info(f"Exportando anotações de {annotations_dir} para formato COCO")

        if output_path is None:
            output_path = os.path.join(annotations_dir, "annotations_coco.json")

        # Inicializar estrutura de dados COCO
        coco_data = {
            "info": {
                "description": "Exported from MicroDetect",
                "url": "",
                "version": "1.0",
                "year": datetime.now().year,
                "contributor": "MicroDetect",
                "date_created": datetime.now().isoformat()
            },
            "licenses": [
                {
                    "id": 1,
                    "name": "Unknown",
                    "url": ""
                }
            ],
            "images": [],
            "annotations": [],
            "categories": []
        }

        # Adicionar categorias
        for i, class_name in enumerate(self.classes):
            class_id = class_name.split('-')[0]
            name = class_name.split('-')[1] if '-' in class_name else class_name
            coco_data["categories"].append({
                "id": int(class_id),
                "name": name,
                "supercategory": "microorganism"
            })

        # Processar imagens e anotações
        annotation_files = glob.glob(os.path.join(annotations_dir, "*.txt"))
        annotation_id = 1

        for ann_file in annotation_files:
            base_name = os.path.splitext(os.path.basename(ann_file))[0]

            # Procurar imagem correspondente
            img_path = None
            for ext in [".jpg", ".jpeg", ".png"]:
                test_path = os.path.join(images_dir, base_name + ext)
                if os.path.exists(test_path):
                    img_path = test_path
                    break

            if img_path is None:
                logger.warning(f"Imagem não encontrada para anotação: {base_name}")
                continue

            # Obter informações da imagem
            try:
                img = cv2.imread(img_path)
                if img is None:
                    logger.warning(f"Não foi possível carregar a imagem: {img_path}")
                    continue

                height, width = img.shape[:2]

                # Adicionar entrada de imagem
                image_id = len(coco_data["images"]) + 1
                coco_data["images"].append({
                    "id": image_id,
                    "license": 1,
                    "file_name": os.path.basename(img_path),
                    "height": height,
                    "width": width,
                    "date_captured": datetime.fromtimestamp(os.path.getmtime(img_path)).isoformat()
                })

                # Ler anotações YOLO e converter para COCO
                with open(ann_file, "r") as f:
                    for line in f:
                        parts = line.strip().split()
                        if len(parts) != 5:
                            continue

                        class_id, x_center, y_center, box_w, box_h = parts

                        # Converter de normalizado para absoluto
                        x_center = float(x_center) * width
                        y_center = float(y_center) * height
                        box_w = float(box_w) * width
                        box_h = float(box_h) * height

                        # Calcular coordenadas para formato COCO (x, y, largura, altura)
                        # onde (x, y) é o canto superior esquerdo
                        x = x_center - (box_w / 2)
                        y = y_center - (box_h / 2)

                        coco_data["annotations"].append({
                            "id": annotation_id,
                            "image_id": image_id,
                            "category_id": int(class_id),
                            "bbox": [x, y, box_w, box_h],
                            "area": box_w * box_h,
                            "segmentation": [],
                            "iscrowd": 0
                        })

                        annotation_id += 1

            except Exception as e:
                logger.error(f"Erro ao processar {img_path}: {str(e)}")
                continue

        # Salvar JSON
        with open(output_path, 'w') as f:
            json.dump(coco_data, f, indent=2)

        logger.info(f"Exportação COCO concluída: {output_path}")
        return output_path

    def export_to_pascal_voc(self, annotations_dir: str, images_dir: str, output_dir: Optional[str] = None) -> str:
        """
        Exporta anotações no formato YOLO para o formato Pascal VOC (XML).

        Args:
            annotations_dir: Diretório contendo anotações YOLO (.txt)
            images_dir: Diretório contendo as imagens relacionadas
            output_dir: Diretório para salvar os arquivos XML (opcional)

        Returns:
            Diretório onde os arquivos XML foram salvos
        """
        logger.info(f"Exportando anotações de {annotations_dir} para formato Pascal VOC")

        if output_dir is None:
            output_dir = os.path.join(annotations_dir, "voc_annotations")

        os.makedirs(output_dir, exist_ok=True)

        # Processar cada arquivo de anotação
        annotation_files = glob.glob(os.path.join(annotations_dir, "*.txt"))
        exported_count = 0

        for ann_file in annotation_files:
            base_name = os.path.splitext(os.path.basename(ann_file))[0]

            # Procurar imagem correspondente
            img_path = None
            for ext in [".jpg", ".jpeg", ".png"]:
                test_path = os.path.join(images_dir, base_name + ext)
                if os.path.exists(test_path):
                    img_path = test_path
                    break

            if img_path is None:
                logger.warning(f"Imagem não encontrada para anotação: {base_name}")
                continue

            # Obter informações da imagem
            try:
                img = cv2.imread(img_path)
                if img is None:
                    logger.warning(f"Não foi possível carregar a imagem: {img_path}")
                    continue

                height, width = img.shape[:2]
                depth = 3  # Assumindo RGB

                # Criar elemento raiz XML
                annotation = ET.Element("annotation")

                # Adicionar informações da imagem
                ET.SubElement(annotation, "folder").text = os.path.basename(os.path.dirname(img_path))
                ET.SubElement(annotation, "filename").text = os.path.basename(img_path)
                ET.SubElement(annotation, "path").text = img_path

                # Adicionar informações de origem
                source = ET.SubElement(annotation, "source")
                ET.SubElement(source, "database").text = "MicroDetect"

                # Adicionar informações de tamanho
                size = ET.SubElement(annotation, "size")
                ET.SubElement(size, "width").text = str(width)
                ET.SubElement(size, "height").text = str(height)
                ET.SubElement(size, "depth").text = str(depth)

                # Adicionar flag de segmentação
                ET.SubElement(annotation, "segmented").text = "0"

                # Ler anotações YOLO e converter para VOC
                with open(ann_file, "r") as f:
                    for line in f:
                        parts = line.strip().split()
                        if len(parts) != 5:
                            continue

                        class_id, x_center, y_center, box_w, box_h = parts

                        # Converter de normalizado para absoluto
                        x_center = float(x_center) * width
                        y_center = float(y_center) * height
                        box_w = float(box_w) * width
                        box_h = float(box_h) * height

                        # Calcular coordenadas para formato VOC (xmin, ymin, xmax, ymax)
                        xmin = int(x_center - (box_w / 2))
                        ymin = int(y_center - (box_h / 2))
                        xmax = int(x_center + (box_w / 2))
                        ymax = int(y_center + (box_h / 2))

                        # Garantir que as coordenadas estão dentro dos limites da imagem
                        xmin = max(0, min(xmin, width - 1))
                        ymin = max(0, min(ymin, height - 1))
                        xmax = max(0, min(xmax, width - 1))
                        ymax = max(0, min(ymax, height - 1))

                        # Obter nome da classe
                        class_name = self.class_map.get(class_id, f"class_{class_id}")
                        if '-' in class_name:
                            class_name = class_name.split('-')[1]

                        # Adicionar objeto
                        obj = ET.SubElement(annotation, "object")
                        ET.SubElement(obj, "name").text = class_name
                        ET.SubElement(obj, "pose").text = "Unspecified"
                        ET.SubElement(obj, "truncated").text = "0"
                        ET.SubElement(obj, "difficult").text = "0"

                        bndbox = ET.SubElement(obj, "bndbox")
                        ET.SubElement(bndbox, "xmin").text = str(xmin)
                        ET.SubElement(bndbox, "ymin").text = str(ymin)
                        ET.SubElement(bndbox, "xmax").text = str(xmax)
                        ET.SubElement(bndbox, "ymax").text = str(ymax)

                # Criar XML string formatado
                xml_str = ET.tostring(annotation, encoding='utf-8')

                # Formatar XML para melhor legibilidade
                try:
                    import xml.dom.minidom
                    dom = xml.dom.minidom.parseString(xml_str)
                    xml_pretty_str = dom.toprettyxml(indent="  ")
                except:
                    xml_pretty_str = xml_str.decode('utf-8')

                # Salvar arquivo XML
                xml_path = os.path.join(output_dir, f"{base_name}.xml")
                with open(xml_path, 'w') as f:
                    f.write(xml_pretty_str)

                exported_count += 1

            except Exception as e:
                logger.error(f"Erro ao processar {img_path} para VOC: {str(e)}")
                continue

        logger.info(f"Exportação VOC concluída: {exported_count} arquivos exportados para {output_dir}")
        return output_dir

    def import_from_coco(self, coco_json_path: str, output_dir: str, images_dir: str) -> int:
        """
        Importa anotações do formato COCO JSON para o formato YOLO.

        Args:
            coco_json_path: Caminho para o arquivo JSON no formato COCO
            output_dir: Diretório para salvar as anotações no formato YOLO
            images_dir: Diretório contendo as imagens relacionadas

        Returns:
            Número de arquivos de anotação criados
        """
        logger.info(f"Importando anotações COCO de {coco_json_path}")

        os.makedirs(output_dir, exist_ok=True)

        try:
            # Carregar JSON
            with open(coco_json_path, 'r') as f:
                coco_data = json.load(f)

            # Mapear imagens por ID
            images = {img["id"]: img for img in coco_data["images"]}

            # Agrupar anotações por ID da imagem
            annotations_by_image = {}
            for ann in coco_data["annotations"]:
                image_id = ann["image_id"]
                if image_id not in annotations_by_image:
                    annotations_by_image[image_id] = []
                annotations_by_image[image_id].append(ann)

            # Processar cada imagem
            imported_count = 0

            for image_id, anns in annotations_by_image.items():
                if image_id not in images:
                    logger.warning(f"Imagem ID {image_id} não encontrada no JSON")
                    continue

                image_info = images[image_id]
                filename = image_info["file_name"]
                base_name = os.path.splitext(filename)[0]
                width = image_info["width"]
                height = image_info["height"]

                # Verificar se a imagem existe
                img_path = os.path.join(images_dir, filename)
                if not os.path.exists(img_path):
                    logger.warning(f"Imagem não encontrada: {img_path}")
                    continue

                # Criar arquivo de anotação YOLO
                yolo_path = os.path.join(output_dir, f"{base_name}.txt")

                with open(yolo_path, 'w') as f:
                    for ann in anns:
                        # Formato COCO: [x, y, width, height] onde (x, y) é o canto superior esquerdo
                        bbox = ann["bbox"]
                        x, y, w, h = bbox

                        # Converter para formato YOLO: [class_id, x_center, y_center, width, height] normalizado
                        x_center = (x + w / 2) / width
                        y_center = (y + h / 2) / height
                        norm_width = w / width
                        norm_height = h / height

                        class_id = ann["category_id"]

                        # Escrever linha no formato YOLO
                        f.write(f"{class_id} {x_center} {y_center} {norm_width} {norm_height}\n")

                imported_count += 1

            logger.info(f"Importação COCO concluída: {imported_count} arquivos de anotação criados em {output_dir}")
            return imported_count

        except Exception as e:
            logger.error(f"Erro ao importar anotações COCO: {str(e)}")
            return 0

    def import_from_pascal_voc(self, voc_dir: str, output_dir: str) -> int:
        """
        Importa anotações do formato Pascal VOC (XML) para o formato YOLO.

        Args:
            voc_dir: Diretório contendo os arquivos XML no formato Pascal VOC
            output_dir: Diretório para salvar as anotações no formato YOLO

        Returns:
            Número de arquivos de anotação criados
        """
        logger.info(f"Importando anotações Pascal VOC de {voc_dir}")

        os.makedirs(output_dir, exist_ok=True)

        # Criar mapeamento reverso de nomes de classes para IDs
        class_name_to_id = {}
        for cls in self.classes:
            parts = cls.split('-')
            if len(parts) == 2:
                class_name_to_id[parts[1].lower()] = parts[0]

        # Processar arquivos XML
        xml_files = glob.glob(os.path.join(voc_dir, "*.xml"))
        imported_count = 0

        for xml_file in xml_files:
            try:
                # Analisar XML
                tree = ET.parse(xml_file)
                root = tree.getroot()

                # Obter dimensões da imagem
                size_elem = root.find("size")
                if size_elem is None:
                    logger.warning(f"Elemento 'size' não encontrado em {xml_file}")
                    continue

                width = int(size_elem.find("width").text)
                height = int(size_elem.find("height").text)

                # Obter nome base para o arquivo de saída
                base_name = os.path.splitext(os.path.basename(xml_file))[0]
                yolo_path = os.path.join(output_dir, f"{base_name}.txt")

                # Processar objetos
                with open(yolo_path, 'w') as f:
                    for obj in root.findall("object"):
                        class_name = obj.find("name").text.lower()

                        # Obter ID da classe
                        if class_name in class_name_to_id:
                            class_id = class_name_to_id[class_name]
                        else:
                            # Tentar encontrar correspondência parcial
                            found = False
                            for name, id in class_name_to_id.items():
                                if name in class_name or class_name in name:
                                    class_id = id
                                    found = True
                                    break

                            if not found:
                                logger.warning(f"Classe '{class_name}' não encontrada no mapeamento. Usando ID '0'.")
                                class_id = "0"

                        # Obter coordenadas da bounding box
                        bbox = obj.find("bndbox")
                        xmin = float(bbox.find("xmin").text)
                        ymin = float(bbox.find("ymin").text)
                        xmax = float(bbox.find("xmax").text)
                        ymax = float(bbox.find("ymax").text)

                        # Converter para formato YOLO
                        x_center = (xmin + xmax) / 2 / width
                        y_center = (ymin + ymax) / 2 / height
                        box_width = (xmax - xmin) / width
                        box_height = (ymax - ymin) / height

                        # Escrever linha no formato YOLO
                        f.write(f"{class_id} {x_center} {y_center} {box_width} {box_height}\n")

                imported_count += 1

            except Exception as e:
                logger.error(f"Erro ao processar {xml_file}: {str(e)}")
                continue

        logger.info(f"Importação VOC concluída: {imported_count} arquivos de anotação criados em {output_dir}")
        return imported_count


def create_export_import_ui(parent: Any, image_dir: str, annotation_dir: str) -> Any:
    """
    Cria uma interface gráfica para exportação e importação de anotações.

    Args:
        parent: Widget pai (Tkinter)
        image_dir: Diretório de imagens
        annotation_dir: Diretório de anotações

    Returns:
        Frame Tkinter contendo a interface
    """
    import tkinter as tk
    from tkinter import messagebox, filedialog

    converter = AnnotationConverter()

    # Criar frame principal
    frame = tk.Toplevel(parent)
    frame.title("Exportar/Importar Anotações")
    frame.geometry("600x400")
    frame.resizable(True, True)

    # Tornar modal
    frame.transient(parent)
    frame.grab_set()

    # Frame para exportação
    export_frame = tk.LabelFrame(frame, text="Exportar Anotações", padx=10, pady=10)
    export_frame.pack(fill=tk.X, padx=10, pady=10)

    # Opções de exportação
    export_format_var = tk.StringVar(value="coco")
    tk.Label(export_frame, text="Formato de exportação:").grid(row=0, column=0, sticky=tk.W)

    formats_frame = tk.Frame(export_frame)
    formats_frame.grid(row=0, column=1, sticky=tk.W)

    tk.Radiobutton(formats_frame, text="COCO JSON", variable=export_format_var, value="coco").pack(side=tk.LEFT)
    tk.Radiobutton(formats_frame, text="Pascal VOC", variable=export_format_var, value="voc").pack(side=tk.LEFT)

    # Diretório de saída
    output_dir_var = tk.StringVar(value=annotation_dir)

    tk.Label(export_frame, text="Diretório de saída:").grid(row=1, column=0, sticky=tk.W)
    output_entry = tk.Entry(export_frame, textvariable=output_dir_var, width=50)
    output_entry.grid(row=1, column=1, sticky=tk.EW)

    # Botão para escolher diretório
    def browse_output():
        directory = filedialog.askdirectory(initialdir=output_dir_var.get())
        if directory:
            output_dir_var.set(directory)

    browse_button = tk.Button(export_frame, text="Procurar...", command=browse_output)
    browse_button.grid(row=1, column=2, padx=5)

    # Botão de exportação
    def export_annotations():
        export_format = export_format_var.get()
        output_dir = output_dir_var.get()

        try:
            if export_format == "coco":
                output_path = converter.export_to_coco(annotation_dir, image_dir,
                                                       os.path.join(output_dir, "annotations_coco.json"))
                messagebox.showinfo("Exportação Concluída",
                                    f"Anotações exportadas com sucesso para:\n{output_path}")
            elif export_format == "voc":
                output_path = converter.export_to_pascal_voc(annotation_dir, image_dir,
                                                             os.path.join(output_dir, "voc_annotations"))
                messagebox.showinfo("Exportação Concluída",
                                    f"Anotações exportadas com sucesso para:\n{output_path}")
        except Exception as e:
            messagebox.showerror("Erro na Exportação", f"Ocorreu um erro durante a exportação:\n{str(e)}")

    export_button = tk.Button(export_frame, text="Exportar Anotações", command=export_annotations,
                              bg="lightblue", padx=10, pady=5)
    export_button.grid(row=2, column=0, columnspan=3, pady=10)

    # Frame para importação
    import_frame = tk.LabelFrame(frame, text="Importar Anotações", padx=10, pady=10)
    import_frame.pack(fill=tk.X, padx=10, pady=10)

    # Opções de importação
    import_format_var = tk.StringVar(value="coco")
    tk.Label(import_frame, text="Formato de importação:").grid(row=0, column=0, sticky=tk.W)

    import_formats_frame = tk.Frame(import_frame)
    import_formats_frame.grid(row=0, column=1, sticky=tk.W)

    tk.Radiobutton(import_formats_frame, text="COCO JSON", variable=import_format_var, value="coco").pack(side=tk.LEFT)
    tk.Radiobutton(import_formats_frame, text="Pascal VOC", variable=import_format_var, value="voc").pack(side=tk.LEFT)

    # Caminho do arquivo/diretório a importar
    import_path_var = tk.StringVar()

    tk.Label(import_frame, text="Arquivo/Diretório:").grid(row=1, column=0, sticky=tk.W)
    import_entry = tk.Entry(import_frame, textvariable=import_path_var, width=50)
    import_entry.grid(row=1, column=1, sticky=tk.EW)

    # Botão para escolher arquivo/diretório
    def browse_import():
        import_format = import_format_var.get()
        if import_format == "coco":
            # Para COCO, escolher arquivo JSON
            file_path = filedialog.askopenfilename(
                initialdir=annotation_dir,
                filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")]
            )
            if file_path:
                import_path_var.set(file_path)
        else:
            # Para VOC, escolher diretório com XMLs
            directory = filedialog.askdirectory(initialdir=annotation_dir)
            if directory:
                import_path_var.set(directory)

    browse_import_button = tk.Button(import_frame, text="Procurar...", command=browse_import)
    browse_import_button.grid(row=1, column=2, padx=5)

    # Diretório de saída para importação
    import_output_var = tk.StringVar(value=annotation_dir)

    tk.Label(import_frame, text="Diretório de saída:").grid(row=2, column=0, sticky=tk.W)
    import_output_entry = tk.Entry(import_frame, textvariable=import_output_var, width=50)
    import_output_entry.grid(row=2, column=1, sticky=tk.EW)

    # Botão para escolher diretório de saída
    def browse_import_output():
        directory = filedialog.askdirectory(initialdir=import_output_var.get())
        if directory:
            import_output_var.set(directory)

    browse_import_output_button = tk.Button(import_frame, text="Procurar...", command=browse_import_output)
    browse_import_output_button.grid(row=2, column=2, padx=5)

    # Botão de importação
    def import_annotations():
        import_format = import_format_var.get()
        import_path = import_path_var.get()
        output_dir = import_output_var.get()

        if not import_path:
            messagebox.showwarning("Aviso", "Por favor, selecione um arquivo ou diretório para importar.")
            return

        try:
            if import_format == "coco":
                count = converter.import_from_coco(import_path, output_dir, image_dir)
                messagebox.showinfo("Importação Concluída",
                                    f"{count} arquivos de anotação importados com sucesso para:\n{output_dir}")
            elif import_format == "voc":
                count = converter.import_from_pascal_voc(import_path, output_dir)
                messagebox.showinfo("Importação Concluída",
                                    f"{count} arquivos de anotação importados com sucesso para:\n{output_dir}")
        except Exception as e:
            messagebox.showerror("Erro na Importação", f"Ocorreu um erro durante a importação:\n{str(e)}")

    import_button = tk.Button(import_frame, text="Importar Anotações", command=import_annotations,
                              bg="lightgreen", padx=10, pady=5)
    import_button.grid(row=3, column=0, columnspan=3, pady=10)

    # Botões de fechamento
    close_button = tk.Button(frame, text="Fechar", command=frame.destroy, padx=10, pady=5)
    close_button.pack(pady=10)

    # Centralizar na tela
    frame.update_idletasks()
    width = frame.winfo_width()
    height = frame.winfo_height()
    x = (frame.winfo_screenwidth() // 2) - (width // 2)
    y = (frame.winfo_screenheight() // 2) - (height // 2)
    frame.geometry(f"{width}x{height}+{x}+{y}")

    return frame