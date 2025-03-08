import os
import argparse
import yaml
import shutil
import random
from pathlib import Path
import cv2
import glob
import numpy as np
from ultralytics import YOLO


def create_data_yaml(dataset_path, classes, output_path='data.yaml'):
    """
    Create a YAML configuration file for the dataset.

    Args:
        dataset_path: Root path to dataset
        classes: List of class names
        output_path: Path to save the YAML file
    """
    # Convert to absolute path
    dataset_path = os.path.abspath(dataset_path)

    # Define paths
    train_path = os.path.join(dataset_path, 'train/images')
    val_path = os.path.join(dataset_path, 'val/images')
    test_path = os.path.join(dataset_path, 'test/images')

    # Verify directories exist
    for path in [train_path, val_path, test_path]:
        if not os.path.exists(path):
            raise FileNotFoundError(f"Directory not found: {path}")
        print(f"Verified path exists: {path}")

    data = {
        'train': train_path,
        'val': val_path,
        'test': test_path,
        'nc': len(classes),
        'names': classes
    }

    with open(output_path, 'w') as f:
        yaml.dump(data, f, default_flow_style=False)

    print(f"Dataset configuration saved to {output_path}")
    return output_path


def prepare_directory_structure(base_dir):
    """Create standard directory structure for YOLO training"""
    # Create directories for train/val/test splits
    for split in ['train', 'val', 'test']:
        for subdir in ['images', 'labels']:
            os.makedirs(os.path.join(base_dir, split, subdir), exist_ok=True)

    print(f"Directory structure created at {base_dir}")


def split_dataset(source_img_dir, source_label_dir, dataset_dir,
                  train_ratio=0.7, val_ratio=0.15, test_ratio=0.15, seed=42):
    """
    Split dataset into train/val/test sets and copy files accordingly.

    Args:
        source_img_dir: Directory containing source images
        source_label_dir: Directory containing source labels
        dataset_dir: Target directory for dataset structure
        train_ratio: Fraction of data for training
        val_ratio: Fraction of data for validation
        test_ratio: Fraction of data for testing
        seed: Random seed for reproducibility
    """
    assert abs(train_ratio + val_ratio + test_ratio - 1.0) < 1e-5, "Ratios must sum to 1"

    # Create directory structure
    prepare_directory_structure(dataset_dir)

    # Get all image files
    image_files = []
    for ext in ['*.jpg', '*.jpeg', '*.png']:
        image_files.extend(glob.glob(os.path.join(source_img_dir, ext)))

    if not image_files:
        raise ValueError(f"No image files found in {source_img_dir}")

    # Set random seed for reproducibility
    random.seed(seed)
    random.shuffle(image_files)

    # Calculate split sizes
    num_samples = len(image_files)
    num_train = int(train_ratio * num_samples)
    num_val = int(val_ratio * num_samples)
    num_test = num_samples - num_train - num_val

    # Split data
    train_files = image_files[:num_train]
    val_files = image_files[num_train:num_train + num_val]
    test_files = image_files[num_train + num_val:]

    # Copy files to appropriate directories
    def copy_files(files, target_split):
        for img_path in files:
            # Get base name without extension
            base_name = os.path.splitext(os.path.basename(img_path))[0]

            # Define source and destination paths
            img_dest = os.path.join(dataset_dir, target_split, 'images', os.path.basename(img_path))
            label_path = os.path.join(source_label_dir, f"{base_name}.txt")
            label_dest = os.path.join(dataset_dir, target_split, 'labels', f"{base_name}.txt")

            # Copy image file
            shutil.copy(img_path, img_dest)

            # Copy label file if it exists
            if os.path.exists(label_path):
                shutil.copy(label_path, label_dest)
            else:
                print(f"Warning: Label not found for {img_path}")

    # Copy files to each split
    copy_files(train_files, 'train')
    copy_files(val_files, 'val')
    copy_files(test_files, 'test')

    print(f"Dataset split complete: {len(train_files)} train, {len(val_files)} val, {len(test_files)} test")


def augment_data(input_image_dir, input_label_dir, output_image_dir, output_label_dir, augmentation_factor=5):
    """
    Applies data augmentation techniques to images and their annotations.

    Args:
        input_image_dir: Directory with original images
        input_label_dir: Directory with original annotations
        output_image_dir: Directory to save augmented images
        output_label_dir: Directory to save augmented annotations
        augmentation_factor: Number of variations to generate for each image
    """
    import cv2
    import glob
    import numpy as np

    os.makedirs(output_image_dir, exist_ok=True)
    os.makedirs(output_label_dir, exist_ok=True)

    image_files = glob.glob(os.path.join(input_image_dir, "*.jpg")) + \
                  glob.glob(os.path.join(input_image_dir, "*.png"))

    total_original = len(image_files)
    total_augmented = 0

    for img_path in image_files:
        # Load image
        img = cv2.imread(img_path)
        if img is None:
            print(f"Could not load image {img_path}")
            continue

        h, w = img.shape[:2]

        # Load annotations
        base_name = os.path.basename(img_path)
        label_path = os.path.join(input_label_dir, os.path.splitext(base_name)[0] + ".txt")

        if not os.path.exists(label_path):
            print(f"Annotation file not found for {img_path}")
            continue

        with open(label_path, 'r') as f:
            annotations = f.readlines()

        # Generate augmentations
        for i in range(augmentation_factor):
            # 1. Brightness and contrast variation
            alpha = np.random.uniform(0.8, 1.2)  # Contrast
            beta = np.random.uniform(-30, 30)  # Brightness
            img_aug = cv2.convertScaleAbs(img, alpha=alpha, beta=beta)

            # 2. Horizontal flip
            if np.random.random() > 0.5:
                img_aug = cv2.flip(img_aug, 1)

                # Adjust annotations for horizontal flip
                flipped_annotations = []
                for ann in annotations:
                    parts = ann.strip().split()
                    if len(parts) == 5:  # YOLO format: class x_center y_center width height
                        cls, x, y, w_box, h_box = parts
                        # Invert x coordinate for horizontal flip
                        x_flipped = 1.0 - float(x)
                        flipped_annotations.append(f"{cls} {x_flipped} {y} {w_box} {h_box}\n")
                annotations_aug = flipped_annotations
            else:
                annotations_aug = annotations

            # 3. Slight rotation
            if np.random.random() > 0.5:
                angle = np.random.uniform(-15, 15)
                M = cv2.getRotationMatrix2D((w / 2, h / 2), angle, 1.0)
                img_aug = cv2.warpAffine(img_aug, M, (w, h))

                # Simplifying by keeping original annotations for small rotations

            # 4. Gaussian noise
            if np.random.random() > 0.7:
                noise = np.random.normal(0, 10, img_aug.shape).astype(np.uint8)
                img_aug = cv2.add(img_aug, noise)

            # Save augmented image and annotation
            aug_filename = f"{os.path.splitext(base_name)[0]}_aug{i}{os.path.splitext(base_name)[1]}"
            aug_img_path = os.path.join(output_image_dir, aug_filename)
            aug_label_path = os.path.join(output_label_dir, os.path.splitext(aug_filename)[0] + ".txt")

            cv2.imwrite(aug_img_path, img_aug)
            with open(aug_label_path, 'w') as f:
                f.writelines(annotations_aug)

            total_augmented += 1

    print(f"Data augmentation complete: {total_augmented} new images generated")


def train_yolo(data_yaml, model_size='m', epochs=100, batch_size=16, image_size=640,
               pretrained=True, output_dir='runs/train'):
    """
    Train a YOLO model on the dataset.

    Args:
        data_yaml: Path to data configuration YAML
        model_size: Model size ('n', 's', 'm', 'l', 'x')
        epochs: Number of training epochs
        batch_size: Batch size
        image_size: Input image size
        pretrained: Whether to use pretrained weights
        output_dir: Directory to save training results
    """
    # Select model based on size
    model_name = f"yolov8{model_size}.pt" if pretrained else f"yolov8{model_size}.yaml"

    # Initialize model
    model = YOLO(model_name)

    # Determine device - use MPS if available on Apple Silicon
    import torch
    if torch.backends.mps.is_available():
        device = 'mps'
        print("Training on Apple GPU (MPS)")
    elif torch.cuda.is_available():
        device = '0'  # First CUDA device
        print("Training on NVIDIA GPU (CUDA)")
    else:
        device = 'cpu'
        print("Training on CPU (no GPU acceleration available)")

    # Start training
    results = model.train(
        data=data_yaml,
        epochs=epochs,
        batch=batch_size,
        imgsz=image_size,
        project=output_dir,
        name=f"yolov8_{model_size}_custom",
        patience=20,
        save=True,
        device=device
    )

    # Export the model to ONNX format for deployment
    model.export(format='onnx')

    return results

def evaluate_and_report(model_path, data_yaml, output_dir='reports'):
    """
    Avalia o modelo treinado e gera um relatório detalhado com métricas de desempenho.

    Args:
        model_path: Caminho para o modelo treinado (.pt)
        data_yaml: Caminho para o arquivo de configuração do dataset
        output_dir: Diretório para salvar o relatório
    """
    import pandas as pd
    import matplotlib.pyplot as plt
    from datetime import datetime
    import json
    import csv

    # Cria diretório de saída
    os.makedirs(output_dir, exist_ok=True)

    # Carrega o modelo
    model = YOLO(model_path)

    # Avalia o modelo no conjunto de teste
    print("Avaliando modelo no conjunto de teste...")
    results = model.val(data=data_yaml)

    # Extrai métricas
    metrics = {
        "Precisão (mAP50)": float(results.box.map50),
        "Precisão (mAP50-95)": float(results.box.map),
        "Recall": float(results.box.recall),
        "Precisão": float(results.box.precision),
        "F1-Score": 2 * (float(results.box.precision) * float(results.box.recall)) /
                    (float(results.box.precision) + float(results.box.recall) + 1e-10),
        "Taxa de Erro": 1.0 - float(results.box.map50)
    }

    # Métricas por classe
    class_metrics = []
    for i, class_name in enumerate(results.names.values()):
        if i < len(results.box.ap_class_index):
            idx = results.box.ap_class_index.tolist().index(i) if i in results.box.ap_class_index else -1
            if idx >= 0:
                class_metrics.append({
                    "Classe": class_name,
                    "Precisão (AP50)": float(results.box.ap50[idx]),
                    "Recall": float(results.box.r[idx]),
                    "Precisão": float(results.box.p[idx]),
                    "F1-Score": 2 * (float(results.box.p[idx]) * float(results.box.r[idx])) /
                                (float(results.box.p[idx]) + float(results.box.r[idx]) + 1e-10),
                })

    # Salva resultados em CSV
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_path = os.path.join(output_dir, f"relatorio_metricas_{timestamp}.csv")

    with open(csv_path, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["Métrica", "Valor"])
        for key, value in metrics.items():
            writer.writerow([key, f"{value:.4f}"])

        writer.writerow([])
        writer.writerow(["Classe", "Precisão (AP50)", "Recall", "Precisão", "F1-Score"])
        for item in class_metrics:
            writer.writerow([
                item["Classe"],
                f"{item['Precisão (AP50)']:.4f}",
                f"{item['Recall']:.4f}",
                f"{item['Precisão']:.4f}",
                f"{item['F1-Score']:.4f}"
            ])

    # Salva resultados em JSON
    json_path = os.path.join(output_dir, f"relatorio_metricas_{timestamp}.json")
    with open(json_path, 'w') as f:
        json.dump({
            "metricas_gerais": metrics,
            "metricas_por_classe": class_metrics
        }, f, indent=4)

    # Gera gráficos
    plt.figure(figsize=(12, 10))

    # Gráfico de barras para métricas gerais
    plt.subplot(2, 1, 1)
    bars = plt.bar(metrics.keys(), metrics.values())
    plt.title("Métricas Gerais do Modelo")
    plt.xticks(rotation=45)
    plt.ylim(0, 1)
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width() / 2., height + 0.01,
                 f'{height:.4f}', ha='center', va='bottom')

    # Gráfico de barras para precisão por classe
    if class_metrics:
        plt.subplot(2, 1, 2)
        classes = [m["Classe"] for m in class_metrics]
        ap_values = [m["Precisão (AP50)"] for m in class_metrics]
        bars = plt.bar(classes, ap_values)
        plt.title("Precisão (AP50) por Classe")
        plt.ylim(0, 1)
        for bar in bars:
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width() / 2., height + 0.01,
                     f'{height:.4f}', ha='center', va='bottom')

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, f"metricas_grafico_{timestamp}.png"))

    # Matriz de confusão
    conf_matrix_path = os.path.join(output_dir, f"confusion_matrix_{timestamp}.png")
    results.confusion_matrix.plot(save_dir=output_dir, names=results.names)

    print(f"Relatório salvo em {output_dir}")
    print(f"Arquivo CSV: relatorio_metricas_{timestamp}.csv")
    print(f"Arquivo JSON: relatorio_metricas_{timestamp}.json")
    print(f"Gráficos: metricas_grafico_{timestamp}.png")
    print(f"Matriz de confusão: confusion_matrix_{timestamp}.png")

    return metrics, class_metrics

def main():
    parser = argparse.ArgumentParser(description='Train YOLO model for microorganism detection')
    parser.add_argument('--source_img_dir', help='Source directory containing all images')
    parser.add_argument('--source_label_dir', help='Source directory containing all labels')
    parser.add_argument('--dataset_dir', required=True, help='Directory for the structured dataset')
    parser.add_argument('--output_dir', default='runs/train', help='Directory to save training results')
    parser.add_argument('--model_size', default='m', choices=['n', 's', 'm', 'l', 'x'],
                        help='YOLO model size (n=nano, s=small, m=medium, l=large, x=xlarge)')
    parser.add_argument('--epochs', type=int, default=100, help='Number of training epochs')
    parser.add_argument('--batch_size', type=int, default=16, help='Training batch size')
    parser.add_argument('--image_size', type=int, default=640, help='Input image size')
    parser.add_argument('--no_pretrained', action='store_true', help='Don\'t use pretrained weights')
    parser.add_argument('--augment', action='store_true', help='Apply data augmentation')
    parser.add_argument('--augment_factor', type=int, default=5, help='Augmentation factor per original image')
    parser.add_argument('--train_ratio', type=float, default=0.7, help='Ratio of data for training')
    parser.add_argument('--val_ratio', type=float, default=0.15, help='Ratio of data for validation')
    parser.add_argument('--test_ratio', type=float, default=0.15, help='Ratio of data for testing')
    parser.add_argument('--seed', type=int, default=42, help='Random seed for data splitting')
    parser.add_argument('--train', action='store_true', help='Start training after data preparation or augmentation')
    parser.add_argument('--evaluate', action='store_true', help='Evaluate model and generate report')
    parser.add_argument('--model_path', help='Path to trained model for evaluation')

    args = parser.parse_args()

    # Define the classes from the annotation tool
    classes = ["0-levedura", "1-fungo", "2-micro-alga"]

    # If source directories are provided, split the dataset
    if args.source_img_dir and args.source_label_dir:
        split_dataset(
            args.source_img_dir,
            args.source_label_dir,
            args.dataset_dir,
            args.train_ratio,
            args.val_ratio,
            args.test_ratio,
            args.seed
        )
    else:
        # Make sure the dataset has the right structure
        prepare_directory_structure(args.dataset_dir)

    # Apply data augmentation to training set only
    if args.augment:
        train_img_dir = os.path.join(args.dataset_dir, 'train', 'images')
        train_label_dir = os.path.join(args.dataset_dir, 'train', 'labels')

        print(f"Performing data augmentation with factor {args.augment_factor}...")
        augment_data(
            train_img_dir,
            train_label_dir,
            train_img_dir,  # Augmented images go to same directory
            train_label_dir,  # Augmented labels go to same directory
            args.augment_factor
        )

    # Create dataset configuration
    data_yaml = create_data_yaml(args.dataset_dir, classes)

    if args.evaluate and args.model_path:
        print(f"Evaluating model {args.model_path}...")
        evaluate_and_report(args.model_path, data_yaml)
    elif args.train:
        print(f"Starting training with YOLOv8 {args.model_size} model")
        print(f"Dataset: {args.dataset_dir}")
        print(f"Classes: {classes}")

        # Start training
        train_yolo(
            data_yaml=data_yaml,
            model_size=args.model_size,
            epochs=args.epochs,
            batch_size=args.batch_size,
            image_size=args.image_size,
            pretrained=not args.no_pretrained,
            output_dir=args.output_dir
        )

        print("Training complete!")


if __name__ == "__main__":
    main()