# Script para preparação de dados e anotação de imagens de leveduras em câmara de Neubauer
# Este script auxilia na criação do conjunto de dados para treinamento do YOLO

import os
import cv2
import numpy as np
import argparse
import glob


def annotate_image_manually(image_path, output_dir):
    """
    Tool for manually annotating yeast cells in microscopy images with custom bounding boxes.
    Instructions:
    - Click and drag to draw bounding boxes
    - Select a class before drawing each box
    - Press 'r' to reset
    - Press 'q' to quit without saving
    - Press 's' to save and go to next image
    - Press 'd' to delete the last box

    Args:
        image_path: Path to the image to be annotated
        output_dir: Directory to save the annotations
    """
    import tkinter as tk
    from PIL import Image, ImageTk

    img = cv2.imread(image_path)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    h, w = img.shape[:2]

    # Scale image if too large
    scale = min(800 / w, 600 / h)
    if scale < 1:
        new_w, new_h = int(w * scale), int(h * scale)
        img = cv2.resize(img, (new_w, new_h))
    else:
        new_w, new_h = w, h

    # Store bounding boxes as (class_id, x1, y1, x2, y2) in original image coordinates
    bounding_boxes = []
    start_x, start_y = None, None
    current_rect = None

    # Available classes for annotation
    classes = ["0-levedura", "1-fungo", "2-micro-alga"]  # Customize classes here
    current_class = "0-levedura"  # Default class

    root = tk.Tk()
    root.title("Yeast Annotation Tool")

    # Create main frame
    main_frame = tk.Frame(root)
    main_frame.pack(fill=tk.BOTH, expand=True)

    # Control panel
    control_frame = tk.Frame(main_frame)
    control_frame.pack(side=tk.TOP, fill=tk.X)

    # Class selection
    class_label = tk.Label(control_frame, text="Select class:")
    class_label.pack(side=tk.LEFT, padx=5)

    class_var = tk.StringVar(root)
    class_var.set(current_class)

    class_menu = tk.OptionMenu(control_frame, class_var, *classes)
    class_menu.pack(side=tk.LEFT, padx=5)
    class_var.trace("w", lambda *args: set_current_class(class_var.get()))

    # Convert to PhotoImage for Tkinter
    img_tk = ImageTk.PhotoImage(Image.fromarray(img))

    # Create canvas
    canvas = tk.Canvas(main_frame, width=new_w, height=new_h)
    canvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
    canvas.create_image(0, 0, anchor=tk.NW, image=img_tk)

    # Status label
    status_label = tk.Label(main_frame, text="Count: 0 | Draw by clicking and dragging")
    status_label.pack(side=tk.BOTTOM, fill=tk.X)

    def set_current_class(class_name):
        nonlocal current_class
        current_class = class_name
        status_label.config(
            text=f"Class: {current_class} | Count: {len(bounding_boxes)} | Draw by clicking and dragging")

    def on_mouse_down(event):
        nonlocal start_x, start_y, current_rect
        start_x, start_y = event.x, event.y

    def on_mouse_move(event):
        nonlocal current_rect
        if start_x is not None and start_y is not None:
            # Delete previous rectangle if exists
            if current_rect:
                canvas.delete(current_rect)
            # Draw new rectangle
            current_rect = canvas.create_rectangle(
                start_x, start_y, event.x, event.y,
                outline='green', width=2
            )

    def on_mouse_up(event):
        nonlocal start_x, start_y, current_rect
        if start_x is not None and start_y is not None:
            # Convert coordinates back to original scale
            x1 = min(start_x, event.x) / scale if scale < 1 else min(start_x, event.x)
            y1 = min(start_y, event.y) / scale if scale < 1 else min(start_y, event.y)
            x2 = max(start_x, event.x) / scale if scale < 1 else max(start_x, event.x)
            y2 = max(start_y, event.y) / scale if scale < 1 else max(start_y, event.y)

            # Get class index (format is "0-live", we need just the number)
            class_id = current_class.split('-')[0]

            # Add to bounding boxes list
            bounding_boxes.append((class_id, int(x1), int(y1), int(x2), int(y2)))

            # Add class label next to the box
            label_text = f"{current_class} #{len(bounding_boxes)}"
            canvas.create_text(
                min(start_x, event.x), min(start_y, event.y) - 5,
                text=label_text, anchor=tk.SW, fill='green', font=("Arial", 10, "bold")
            )

            # Update status
            status_label.config(
                text=f"Class: {current_class} | Count: {len(bounding_boxes)} | Draw by clicking and dragging")

            # Reset
            start_x, start_y = None, None
            current_rect = None

    def delete_last():
        if bounding_boxes:
            bounding_boxes.pop()
            redraw_all_boxes()
            status_label.config(text=f"Class: {current_class} | Count: {len(bounding_boxes)} | Last box deleted")

    def redraw_all_boxes():
        canvas.delete("all")
        canvas.create_image(0, 0, anchor=tk.NW, image=img_tk)

        for i, (class_id, x1, y1, x2, y2) in enumerate(bounding_boxes):
            # Convert back to display coordinates
            dx1 = x1 * scale if scale < 1 else x1
            dy1 = y1 * scale if scale < 1 else y1
            dx2 = x2 * scale if scale < 1 else x2
            dy2 = y2 * scale if scale < 1 else y2

            # Find class name for display
            class_name = next((c for c in classes if c.startswith(class_id)), f"{class_id}-unknown")

            # Draw rectangle
            canvas.create_rectangle(dx1, dy1, dx2, dy2, outline='green', width=2)

            # Draw label
            canvas.create_text(
                dx1, dy1 - 5, text=f"{class_name} #{i + 1}",
                anchor=tk.SW, fill='green', font=("Arial", 10, "bold")
            )

    def reset():
        bounding_boxes.clear()
        redraw_all_boxes()
        status_label.config(text=f"Class: {current_class} | Count: 0 | All boxes cleared")

    def save():
        base_name = os.path.basename(image_path)
        txt_filename = os.path.splitext(base_name)[0] + ".txt"
        txt_path = os.path.join(output_dir, txt_filename)

        with open(txt_path, "w") as f:
            for box in bounding_boxes:
                class_id, x1, y1, x2, y2 = box

                # Convert to YOLO format: class_id center_x center_y width height (normalized)
                box_w = (x2 - x1) / w
                box_h = (y2 - y1) / h
                center_x = (x1 + (x2 - x1) / 2) / w
                center_y = (y1 + (y2 - y1) / 2) / h

                f.write(f"{class_id} {center_x} {center_y} {box_w} {box_h}\n")

        print(f"Annotation saved to {txt_path}. {len(bounding_boxes)} boxes annotated.")
        root.destroy()

    def on_closing():
        root.destroy()

    # Buttons
    button_frame = tk.Frame(main_frame)
    button_frame.pack(fill=tk.X)

    tk.Button(button_frame, text="Reset (R)", command=reset).pack(side=tk.LEFT, padx=5)
    tk.Button(button_frame, text="Delete Last (D)", command=delete_last).pack(side=tk.LEFT, padx=5)
    tk.Button(button_frame, text="Save (S)", command=save).pack(side=tk.LEFT, padx=5)
    tk.Button(button_frame, text="Quit (Q)", command=on_closing).pack(side=tk.LEFT, padx=5)

    # Bind events
    canvas.bind('<ButtonPress-1>', on_mouse_down)
    canvas.bind('<B1-Motion>', on_mouse_move)
    canvas.bind('<ButtonRelease-1>', on_mouse_up)

    # Bind keyboard shortcuts
    root.bind('<r>', lambda e: reset())
    root.bind('<d>', lambda e: delete_last())
    root.bind('<s>', lambda e: save())
    root.bind('<q>', lambda e: on_closing())

    # Protocol for window closing
    root.protocol("WM_DELETE_WINDOW", on_closing)

    # Store the image reference to prevent garbage collection
    canvas.img_tk = img_tk

    root.mainloop()


def augment_data(input_image_dir, input_label_dir, output_image_dir, output_label_dir, augmentation_factor=5):
    """
    Aplica técnicas de augmentação de dados nas imagens e suas anotações.

    Args:
        input_image_dir: Diretório com as imagens originais
        input_label_dir: Diretório com as anotações originais
        output_image_dir: Diretório para salvar as imagens aumentadas
        output_label_dir: Diretório para salvar as anotações aumentadas
        augmentation_factor: Número de variações a serem geradas para cada imagem
    """
    os.makedirs(output_image_dir, exist_ok=True)
    os.makedirs(output_label_dir, exist_ok=True)

    image_files = glob.glob(os.path.join(input_image_dir, "*.jpg")) + \
                  glob.glob(os.path.join(input_image_dir, "*.png"))

    for img_path in image_files:
        # Carregar imagem
        img = cv2.imread(img_path)
        h, w = img.shape[:2]

        # Carregar anotações
        base_name = os.path.basename(img_path)
        label_path = os.path.join(input_label_dir, os.path.splitext(base_name)[0] + ".txt")

        if not os.path.exists(label_path):
            print(f"Arquivo de anotação não encontrado para {img_path}")
            continue

        with open(label_path, 'r') as f:
            annotations = f.readlines()

        # Copiar original
        output_img_path = os.path.join(output_image_dir, base_name)
        output_label_path = os.path.join(output_label_dir, os.path.splitext(base_name)[0] + ".txt")

        cv2.imwrite(output_img_path, img)
        with open(output_label_path, 'w') as f:
            f.writelines(annotations)

        # Gerar augmentações
        for i in range(augmentation_factor):
            # 1. Variação de brilho e contraste
            alpha = np.random.uniform(0.8, 1.2)  # Contraste
            beta = np.random.uniform(-30, 30)  # Brilho
            img_aug = cv2.convertScaleAbs(img, alpha=alpha, beta=beta)

            # 2. Flip horizontal
            if np.random.random() > 0.5:
                img_aug = cv2.flip(img_aug, 1)

                # Ajustar anotações para o flip
                flipped_annotations = []
                for ann in annotations:
                    parts = ann.strip().split()
                    if len(parts) == 5:  # formato YOLO: class x_center y_center width height
                        cls, x, y, w_box, h_box = parts
                        # Inverter coordenada x para flip horizontal
                        x_flipped = 1.0 - float(x)
                        flipped_annotations.append(f"{cls} {x_flipped} {y} {w_box} {h_box}\n")
                annotations_aug = flipped_annotations
            else:
                annotations_aug = annotations

            # 3. Rotação leve
            if np.random.random() > 0.5:
                angle = np.random.uniform(-15, 15)
                M = cv2.getRotationMatrix2D((w / 2, h / 2), angle, 1.0)
                img_aug = cv2.warpAffine(img_aug, M, (w, h))

                # Ajustar anotações para a rotação é mais complexo e requer cálculos adicionais
                # Para simplificar, mantemos as anotações originais para pequenas rotações

            # 4. Ruído gaussiano
            if np.random.random() > 0.7:
                noise = np.random.normal(0, 10, img_aug.shape).astype(np.uint8)
                img_aug = cv2.add(img_aug, noise)

            # Salvar imagem e anotação aumentadas
            aug_filename = f"{os.path.splitext(base_name)[0]}_aug{i}{os.path.splitext(base_name)[1]}"
            aug_img_path = os.path.join(output_image_dir, aug_filename)
            aug_label_path = os.path.join(output_label_dir, os.path.splitext(aug_filename)[0] + ".txt")

            cv2.imwrite(aug_img_path, img_aug)
            with open(aug_label_path, 'w') as f:
                f.writelines(annotations_aug)

        print(f"Geradas {augmentation_factor} augmentações para {base_name}")


def main():
    parser = argparse.ArgumentParser(description='Ferramentas para preparação de dados de leveduras')
    subparsers = parser.add_subparsers(dest='command')

    # Subcomando para anotação manual
    annotate_parser = subparsers.add_parser('annotate', help='Anotar imagens manualmente')
    annotate_parser.add_argument('--image_dir', required=True, help='Diretório com imagens para anotação')
    annotate_parser.add_argument('--output_dir', required=True, help='Diretório para salvar as anotações')

    # Subcomando para augmentação
    augment_parser = subparsers.add_parser('augment', help='Aplicar augmentação em imagens e anotações')
    augment_parser.add_argument('--image_dir', required=True, help='Diretório com imagens originais')
    augment_parser.add_argument('--label_dir', required=True, help='Diretório com anotações originais')
    augment_parser.add_argument('--output_image_dir', required=True, help='Diretório para salvar imagens aumentadas')
    augment_parser.add_argument('--output_label_dir', required=True, help='Diretório para salvar anotações aumentadas')
    augment_parser.add_argument('--factor', type=int, default=5, help='Fator de augmentação (padrão: 5)')

    args = parser.parse_args()

    if args.command == 'annotate':
        os.makedirs(args.output_dir, exist_ok=True)
        image_files = glob.glob(os.path.join(args.image_dir, "*.jpg")) + \
                      glob.glob(os.path.join(args.image_dir, "*.png"))

        for img_path in image_files:
            print(f"Anotando: {os.path.basename(img_path)}")
            annotate_image_manually(img_path, args.output_dir)

    elif args.command == 'augment':
        augment_data(args.image_dir, args.label_dir,
                     args.output_image_dir, args.output_label_dir,
                     args.factor)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()