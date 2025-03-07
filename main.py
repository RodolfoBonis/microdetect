# Script para preparação de dados e anotação de imagens de leveduras em câmara de Neubauer
# Este script auxilia na criação do conjunto de dados para treinamento do YOLO

import os
import cv2
import numpy as np
import argparse
import glob


def annotate_image_manually(image_path, output_dir):
    """
    Ferramenta simples para anotação manual de leveduras em imagens de microscopia.
    Instruções:
    - Clique nas leveduras para marcá-las
    - Pressione 'r' para resetar
    - Pressione 'q' para sair sem salvar
    - Pressione 's' para salvar e ir para a próxima imagem

    Args:
        image_path: Caminho para a imagem a ser anotada
        output_dir: Diretório para salvar as anotações
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

    points = []

    root = tk.Tk()
    root.title("Anotação de Leveduras")

    # Convert to PhotoImage for Tkinter
    img_tk = ImageTk.PhotoImage(Image.fromarray(img))

    # Create canvas
    canvas = tk.Canvas(root, width=new_w, height=new_h)
    canvas.pack()
    canvas.create_image(0, 0, anchor=tk.NW, image=img_tk)

    # Status label
    status_label = tk.Label(root, text="Contagem: 0")
    status_label.pack()

    def on_click(event):
        x, y = event.x, event.y
        # Convert coordinates back to original scale
        orig_x = int(x / scale) if scale < 1 else x
        orig_y = int(y / scale) if scale < 1 else y
        points.append((orig_x, orig_y))

        # Draw point
        canvas.create_oval(x - 3, y - 3, x + 3, y + 3, fill='green')
        status_label.config(text=f"Contagem: {len(points)}")

    def reset():
        canvas.delete("all")
        canvas.create_image(0, 0, anchor=tk.NW, image=img_tk)
        points.clear()
        status_label.config(text="Contagem: 0")

    def save():
        base_name = os.path.basename(image_path)
        txt_filename = os.path.splitext(base_name)[0] + ".txt"
        txt_path = os.path.join(output_dir, txt_filename)

        with open(txt_path, "w") as f:
            for point in points:
                x, y = point
                box_w, box_h = 0.03, 0.03
                x_center = x / w
                y_center = y / h
                f.write(f"0 {x_center} {y_center} {box_w} {box_h}\n")

        print(f"Anotação salva em {txt_path}. {len(points)} leveduras marcadas.")
        root.quit()

    # Buttons
    button_frame = tk.Frame(root)
    button_frame.pack(fill=tk.X)

    tk.Button(button_frame, text="Reset (R)", command=reset).pack(side=tk.LEFT, padx=5)
    tk.Button(button_frame, text="Save (S)", command=save).pack(side=tk.LEFT, padx=5)
    tk.Button(button_frame, text="Quit (Q)", command=root.quit).pack(side=tk.LEFT, padx=5)

    # Bind keyboard shortcuts
    root.bind('<r>', lambda e: reset())
    root.bind('<s>', lambda e: save())
    root.bind('<q>', lambda e: root.quit())
    canvas.bind('<Button-1>', on_click)

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