"""
Módulo para anotação manual de imagens.
"""

import glob
import logging
import os
import tkinter as tk
from datetime import datetime
from typing import List, Tuple, Optional

import cv2
from PIL import Image, ImageTk

from microdetect.utils.config import config

logger = logging.getLogger(__name__)


class ImageAnnotator:
    """
    Ferramenta para anotação manual de imagens de microorganismos.
    """

    def __init__(self, classes: List[str] = None):
        """
        Inicializa o anotador de imagens.

        Args:
            classes: Lista de classes para anotação
        """
        self.classes = classes or config.get('classes', ["0-levedura", "1-fungo", "2-micro-alga"])
        self.progress_file = ".annotation_progress.json"

    def annotate_image(self, image_path: str, output_dir: str) -> Optional[str]:
        """
        Ferramenta para anotar manualmente células de levedura em imagens de microscopia com bounding boxes.
        Instruções:
        - Clique e arraste para desenhar bounding boxes
        - Selecione uma classe antes de desenhar cada caixa
        - Pressione 'r' para reiniciar
        - Pressione 'q' para sair sem salvar
        - Pressione 's' para salvar e ir para a próxima imagem
        - Pressione 'd' para excluir a última caixa
        - Pressione 'e' para sair e salvar progresso

        Args:
            image_path: Caminho para a imagem a ser anotada
            output_dir: Diretório para salvar as anotações

        Returns:
            Caminho para o arquivo de anotação criado ou None se cancelado
        """
        # Assegurar que o diretório de saída existe
        os.makedirs(output_dir, exist_ok=True)

        img = cv2.imread(image_path)
        if img is None:
            logger.error(f"Não foi possível carregar a imagem: {image_path}")
            return None

        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        h, w = img.shape[:2]

        # Dimensionar imagem se muito grande
        scale = min(800 / w, 600 / h)
        if scale < 1:
            new_w, new_h = int(w * scale), int(h * scale)
            img_display = cv2.resize(img, (new_w, new_h))
        else:
            new_w, new_h = w, h
            img_display = img

        # Armazenar bounding boxes como (class_id, x1, y1, x2, y2) em coordenadas da imagem original
        bounding_boxes = []

        # Verificar se já existem anotações para esta imagem
        base_name = os.path.splitext(os.path.basename(image_path))[0]
        existing_annotation_path = os.path.join(output_dir, f"{base_name}.txt")

        if os.path.exists(existing_annotation_path):
            logger.info(f"Carregando anotações existentes de {existing_annotation_path}")

            # Carregar anotações existentes
            with open(existing_annotation_path, 'r') as f:
                for line in f:
                    parts = line.strip().split()
                    if len(parts) == 5:  # formato YOLO: class x_center y_center width height
                        class_id, x_center, y_center, box_w, box_h = parts

                        # Converter de YOLO para pixel
                        x_center = float(x_center) * w
                        y_center = float(y_center) * h
                        box_w = float(box_w) * w
                        box_h = float(box_h) * h

                        # Calcular coordenadas absolutas (x1, y1, x2, y2)
                        x1 = int(x_center - box_w / 2)
                        y1 = int(y_center - box_h / 2)
                        x2 = int(x_center + box_w / 2)
                        y2 = int(y_center + box_h / 2)

                        # Adicionar à lista de bounding boxes
                        bounding_boxes.append((class_id, x1, y1, x2, y2))

        start_x, start_y = None, None
        current_rect = None

        # Classe padrão
        current_class = self.classes[0] if self.classes else "0-levedura"

        # Criar janela Tkinter
        root = tk.Tk()
        root.title(f"Anotação: {os.path.basename(image_path)}")

        # Criar frame principal
        main_frame = tk.Frame(root)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Painel de controle
        control_frame = tk.Frame(main_frame)
        control_frame.pack(side=tk.TOP, fill=tk.X)

        # Seleção de classe
        class_label = tk.Label(control_frame, text="Selecionar classe:")
        class_label.pack(side=tk.LEFT, padx=5)

        class_var = tk.StringVar(root)
        class_var.set(current_class)

        class_menu = tk.OptionMenu(control_frame, class_var, *self.classes)
        class_menu.pack(side=tk.LEFT, padx=5)

        # Status label
        status_label = tk.Label(main_frame, text=f"Contagem: {len(bounding_boxes)} | Desenhe clicando e arrastando")
        status_label.pack(side=tk.BOTTOM, fill=tk.X)

        # Informações da imagem
        info_label = tk.Label(main_frame, text=f"Imagem: {os.path.basename(image_path)} | Dimensões: {w}x{h}")
        info_label.pack(side=tk.BOTTOM, fill=tk.X)

        # Converter para PhotoImage para o Tkinter
        img_tk = ImageTk.PhotoImage(Image.fromarray(img_display))

        # Criar canvas
        canvas = tk.Canvas(main_frame, width=new_w, height=new_h)
        canvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        canvas.create_image(0, 0, anchor=tk.NW, image=img_tk)

        # Resultado da anotação
        annotation_path = None
        exit_requested = False

        def set_current_class(event=None):
            nonlocal current_class
            current_class = class_var.get()
            status_label.config(
                text=f"Classe: {current_class} | Contagem: {len(bounding_boxes)} | Desenhe clicando e arrastando")

        def on_mouse_down(event):
            nonlocal start_x, start_y, current_rect
            start_x, start_y = event.x, event.y

        def on_mouse_move(event):
            nonlocal current_rect
            if start_x is not None and start_y is not None:
                # Excluir retângulo anterior se existir
                if current_rect:
                    canvas.delete(current_rect)
                # Desenhar novo retângulo
                current_rect = canvas.create_rectangle(
                    start_x, start_y, event.x, event.y,
                    outline='green', width=2
                )

        def on_mouse_up(event):
            nonlocal start_x, start_y, current_rect
            if start_x is not None and start_y is not None:
                # Converter coordenadas de volta para escala original
                x1 = min(start_x, event.x) / scale if scale < 1 else min(start_x, event.x)
                y1 = min(start_y, event.y) / scale if scale < 1 else min(start_y, event.y)
                x2 = max(start_x, event.x) / scale if scale < 1 else max(start_x, event.x)
                y2 = max(start_y, event.y) / scale if scale < 1 else max(start_y, event.y)

                # Obter índice da classe (formato é "0-levedura", precisamos apenas do número)
                class_id = current_class.split('-')[0]

                # Adicionar à lista de bounding boxes
                bounding_boxes.append((class_id, int(x1), int(y1), int(x2), int(y2)))

                # Adicionar rótulo de classe ao lado da caixa
                label_text = f"{current_class} #{len(bounding_boxes)}"
                canvas.create_text(
                    min(start_x, event.x), min(start_y, event.y) - 5,
                    text=label_text, anchor=tk.SW, fill='green', font=("Arial", 10, "bold")
                )

                # Atualizar status
                status_label.config(
                    text=f"Classe: {current_class} | Contagem: {len(bounding_boxes)} | Desenhe clicando e arrastando")

                # Reiniciar
                start_x, start_y = None, None
                current_rect = None

        def delete_last():
            if bounding_boxes:
                bounding_boxes.pop()
                redraw_all_boxes()
                status_label.config(
                    text=f"Classe: {current_class} | Contagem: {len(bounding_boxes)} | Última caixa excluída")

        def redraw_all_boxes():
            canvas.delete("all")
            canvas.create_image(0, 0, anchor=tk.NW, image=img_tk)

            for i, (class_id, x1, y1, x2, y2) in enumerate(bounding_boxes):
                # Converter de volta para coordenadas de exibição
                dx1 = x1 * scale if scale < 1 else x1
                dy1 = y1 * scale if scale < 1 else y1
                dx2 = x2 * scale if scale < 1 else x2
                dy2 = y2 * scale if scale < 1 else y2

                # Encontrar nome da classe para exibição
                class_name = next((c for c in self.classes if c.startswith(class_id)), f"{class_id}-desconhecido")

                # Desenhar retângulo
                canvas.create_rectangle(dx1, dy1, dx2, dy2, outline='green', width=2)

                # Desenhar rótulo
                canvas.create_text(
                    dx1, dy1 - 5, text=f"{class_name} #{i + 1}",
                    anchor=tk.SW, fill='green', font=("Arial", 10, "bold")
                )

        def reset():
            bounding_boxes.clear()
            redraw_all_boxes()
            status_label.config(text=f"Classe: {current_class} | Contagem: 0 | Todas as caixas limpas")

        def save():
            nonlocal annotation_path
            base_name = os.path.basename(image_path)
            txt_filename = os.path.splitext(base_name)[0] + ".txt"
            txt_path = os.path.join(output_dir, txt_filename)

            with open(txt_path, "w") as f:
                for box in bounding_boxes:
                    class_id, x1, y1, x2, y2 = box

                    # Converter para formato YOLO: class_id center_x center_y width height (normalizado)
                    box_w = (x2 - x1) / w
                    box_h = (y2 - y1) / h
                    center_x = (x1 + (x2 - x1) / 2) / w
                    center_y = (y1 + (y2 - y1) / 2) / h

                    f.write(f"{class_id} {center_x} {center_y} {box_w} {box_h}\n")

            logger.info(f"Anotação salva em {txt_path}. {len(bounding_boxes)} caixas anotadas.")
            annotation_path = txt_path
            root.destroy()

        def on_closing():
            nonlocal exit_requested
            exit_requested = True
            root.destroy()

        def exit_and_save():
            nonlocal exit_requested
            if len(bounding_boxes) > 0:
                save()
            exit_requested = True
            root.destroy()

        # Rastreamento da classe selecionada
        class_var.trace("w", lambda *args: set_current_class())

        # Botões
        button_frame = tk.Frame(main_frame)
        button_frame.pack(fill=tk.X)

        tk.Button(button_frame, text="Reiniciar (R)", command=reset).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Excluir Última (D)", command=delete_last).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Salvar (S)", command=save).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Sair (Q)", command=on_closing).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Salvar e Sair (E)", command=exit_and_save).pack(side=tk.LEFT, padx=5)

        # Vincular eventos
        canvas.bind('<ButtonPress-1>', on_mouse_down)
        canvas.bind('<B1-Motion>', on_mouse_move)
        canvas.bind('<ButtonRelease-1>', on_mouse_up)

        # Vincular atalhos de teclado
        root.bind('<r>', lambda e: reset())
        root.bind('<d>', lambda e: delete_last())
        root.bind('<s>', lambda e: save())
        root.bind('<q>', lambda e: on_closing())
        root.bind('<e>', lambda e: exit_and_save())

        # Protocolo para fechar janela
        root.protocol("WM_DELETE_WINDOW", on_closing)

        # Armazenar a referência da imagem para evitar coleta de lixo
        canvas.img_tk = img_tk

        # Centralizar janela na tela
        root.update_idletasks()
        width = root.winfo_width()
        height = root.winfo_height()
        x = (root.winfo_screenwidth() // 2) - (width // 2)
        y = (root.winfo_screenheight() // 2) - (height // 2)
        root.geometry('{}x{}+{}+{}'.format(width, height, x, y))

        # Desenhar as bounding boxes existentes
        if bounding_boxes:
            redraw_all_boxes()

        # Iniciar loop principal
        root.mainloop()

        # Se o usuário solicitou sair, retorne None para interromper o batch_annotate
        if exit_requested:
            return None

        return annotation_path

    def batch_annotate(self, image_dir: str, output_dir: str) -> Tuple[int, int]:
        """
        Anota uma pasta de imagens em lote.

        Args:
            image_dir: Diretório contendo imagens para anotação
            output_dir: Diretório para salvar as anotações

        Returns:
            Tupla com (total de imagens, total de imagens anotadas)
        """
        import json
        import os.path as osp

        os.makedirs(output_dir, exist_ok=True)

        # Obter todos os arquivos de imagem
        image_files = []
        for ext in ['*.jpg', '*.jpeg', '*.png']:
            image_files.extend(glob.glob(os.path.join(image_dir, ext)))

        if not image_files:
            logger.warning(f"Nenhum arquivo de imagem encontrado em {image_dir}")
            return 0, 0

        # Ordenar imagens para consistência
        image_files.sort()

        # Verificar se há progresso salvo
        progress_path = os.path.join(output_dir, self.progress_file)
        start_index = 0

        if os.path.exists(progress_path):
            try:
                with open(progress_path, 'r') as f:
                    progress_data = json.load(f)

                last_annotated = progress_data.get('last_annotated', '')
                if last_annotated in image_files:
                    start_index = image_files.index(last_annotated) + 1
                    if start_index < len(image_files):
                        logger.info(f"Retomando anotação a partir de: {os.path.basename(image_files[start_index])}")
                        retomar = input(f"Última imagem anotada: {os.path.basename(last_annotated)}. "
                                        f"Retomar da próxima imagem? (s/n): ").lower()
                        if retomar != 's':
                            start_index = 0
                    else:
                        logger.info("Todas as imagens já foram anotadas.")
            except Exception as e:
                logger.warning(f"Erro ao carregar progresso: {str(e)}")

        total_annotated = 0
        imagens_existentes = 0

        # Contar anotações já existentes antes do ponto de retomada
        for i in range(start_index):
            img_path = image_files[i]
            base_name = os.path.splitext(os.path.basename(img_path))[0]
            existing_annotation = os.path.join(output_dir, f"{base_name}.txt")
            if os.path.exists(existing_annotation):
                imagens_existentes += 1

        # Processar imagens a partir do ponto de retomada
        for i in range(start_index, len(image_files)):
            img_path = image_files[i]
            logger.info(f"Anotando: {os.path.basename(img_path)} ({i + 1}/{len(image_files)})")

            # Verificar se já existe anotação
            base_name = os.path.splitext(os.path.basename(img_path))[0]
            existing_annotation = os.path.join(output_dir, f"{base_name}.txt")

            if os.path.exists(existing_annotation):
                should_skip = input(f"A anotação para {base_name} já existe. O que deseja fazer? "
                                    f"(p)ular, (e)ditar, (s)obrescrever: ").lower()
                if should_skip == 'p':
                    logger.info(f"Pulando {base_name}")
                    imagens_existentes += 1

                    # Salvar progresso após cada imagem
                    self._save_progress(progress_path, img_path)
                    continue
                elif should_skip != 'e':
                    # Para 's' ou qualquer outra entrada, continuamos normalmente (sobrescrever)
                    logger.info(f"Sobrescrevendo anotação existente para {base_name}")

            # Anotar imagem
            annotation_path = self.annotate_image(img_path, output_dir)

            if annotation_path:
                total_annotated += 1
                logger.info(f"Concluído {total_annotated}/{len(image_files) - start_index} imagens nesta sessão")

                # Salvar progresso após cada imagem
                self._save_progress(progress_path, img_path)
            else:
                logger.info("Anotação cancelada. Progresso salvo.")
                break

        logger.info(
            f"Anotação em lote concluída: {total_annotated + imagens_existentes}/{len(image_files)} imagens anotadas no total")
        return len(image_files), total_annotated + imagens_existentes

    def _save_progress(self, progress_path: str, current_image: str) -> None:
        """
        Salva o progresso atual da anotação.

        Args:
            progress_path: Caminho para o arquivo de progresso
            current_image: Caminho da imagem atual
        """
        import json

        try:
            progress_data = {
                'last_annotated': current_image,
                'timestamp': datetime.now().isoformat()
            }

            with open(progress_path, 'w') as f:
                json.dump(progress_data, f)

        except Exception as e:
            logger.warning(f"Não foi possível salvar o progresso: {str(e)}")