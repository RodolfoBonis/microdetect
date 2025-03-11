"""
Módulo para preparação e gerenciamento de datasets.
"""

import glob
import logging
import os
import random
import shutil
from typing import Dict, List, Optional, Tuple

import yaml

from microdetect.utils.config import config

logger = logging.getLogger(__name__)


class DatasetManager:
    """
    Classe para gerenciar a preparação, divisão e configuração de datasets.
    """

    def __init__(
        self,
        dataset_dir: str = None,
        train_ratio: float = None,
        val_ratio: float = None,
        test_ratio: float = None,
        seed: int = None,
    ):
        """
        Inicializa o gerenciador de dataset.

        Args:
            dataset_dir: Diretório base para o dataset
            train_ratio: Proporção dos dados para treinamento
            val_ratio: Proporção dos dados para validação
            test_ratio: Proporção dos dados para teste
            seed: Semente para reprodutibilidade
        """
        self.dataset_dir = dataset_dir or config.get("directories.dataset", "dataset")
        self.train_ratio = train_ratio or config.get("dataset.train_ratio", 0.7)
        self.val_ratio = val_ratio or config.get("dataset.val_ratio", 0.15)
        self.test_ratio = test_ratio or config.get("dataset.test_ratio", 0.15)
        self.seed = seed or config.get("dataset.seed", 42)
        self.classes = config.get("classes", ["0-levedura", "1-fungo", "2-micro-alga"])

        # Verificar se as proporções somam 1
        total_ratio = self.train_ratio + self.val_ratio + self.test_ratio
        if abs(total_ratio - 1.0) > 1e-5:
            logger.warning(f"As proporções do dataset não somam 1.0 (soma: {total_ratio}). Normalizando...")
            # Normalizar as proporções
            self.train_ratio /= total_ratio
            self.val_ratio /= total_ratio
            self.test_ratio /= total_ratio

    def prepare_directory_structure(self) -> None:
        """
        Cria a estrutura de diretórios padrão para treinamento YOLO.
        """
        # Criar diretórios para as divisões train/val/test
        for split in ["train", "val", "test"]:
            for subdir in ["images", "labels"]:
                os.makedirs(os.path.join(self.dataset_dir, split, subdir), exist_ok=True)

        logger.info(f"Estrutura de diretórios criada em {self.dataset_dir}")

    def split_dataset(self, source_img_dir: str, source_label_dir: str) -> Dict[str, int]:
        """
        Divide o dataset em conjuntos de treino/validação/teste e copia os arquivos.

        Args:
            source_img_dir: Diretório contendo as imagens de origem
            source_label_dir: Diretório contendo as anotações de origem

        Returns:
            Dicionário com contagens de arquivos em cada divisão
        """
        # Criar estrutura de diretórios
        self.prepare_directory_structure()

        # Obter todos os arquivos de imagem
        image_files = []
        for ext in ["*.jpg", "*.jpeg", "*.png"]:
            image_files.extend(glob.glob(os.path.join(source_img_dir, ext)))

        if not image_files:
            raise ValueError(f"Nenhum arquivo de imagem encontrado em {source_img_dir}")

        # Definir semente para reprodutibilidade
        random.seed(self.seed)
        random.shuffle(image_files)

        # Calcular tamanhos de divisão
        num_samples = len(image_files)
        num_train = int(self.train_ratio * num_samples)
        num_val = int(self.val_ratio * num_samples)
        num_test = num_samples - num_train - num_val

        # Dividir dados
        train_files = image_files[:num_train]
        val_files = image_files[num_train : num_train + num_val]
        test_files = image_files[num_train + num_val :]

        # Copiar arquivos para diretórios apropriados
        splits = {"train": train_files, "val": val_files, "test": test_files}

        split_counts = {}

        for split_name, files in splits.items():
            count = self._copy_files_to_split(files, split_name, source_label_dir)
            split_counts[split_name] = count

        total = sum(split_counts.values())
        logger.info(
            f"Divisão do dataset concluída: "
            f"{split_counts.get('train', 0)} treino, "
            f"{split_counts.get('val', 0)} validação, "
            f"{split_counts.get('test', 0)} teste"
        )

        return split_counts

    def _copy_files_to_split(self, files: List[str], target_split: str, source_label_dir: str) -> int:
        """
        Copia arquivos de imagem e anotação para um diretório de divisão específico.

        Args:
            files: Lista de caminhos de arquivo de imagem
            target_split: Nome da divisão alvo ('train', 'val', ou 'test')
            source_label_dir: Diretório contendo os arquivos de anotação

        Returns:
            Número de arquivos copiados com sucesso
        """
        success_count = 0

        for img_path in files:
            # Obter nome base sem extensão
            base_name = os.path.splitext(os.path.basename(img_path))[0]

            # Definir caminhos de origem e destino
            img_dest = os.path.join(self.dataset_dir, target_split, "images", os.path.basename(img_path))
            label_path = os.path.join(source_label_dir, f"{base_name}.txt")
            label_dest = os.path.join(self.dataset_dir, target_split, "labels", f"{base_name}.txt")

            try:
                # Copiar arquivo de imagem
                shutil.copy(img_path, img_dest)

                # Copiar arquivo de anotação se existir
                if os.path.exists(label_path):
                    shutil.copy(label_path, label_dest)
                    success_count += 1
                else:
                    logger.warning(f"Anotação não encontrada para {img_path}")
            except Exception as e:
                logger.error(f"Erro ao copiar arquivo {img_path}: {str(e)}")

        return success_count

    def create_data_yaml(self, output_path: str = None) -> str:
        """
        Cria um arquivo de configuração YAML para o dataset.

        Args:
            output_path: Caminho para salvar o arquivo YAML

        Returns:
            Caminho para o arquivo YAML criado
        """
        if output_path is None:
            output_path = os.path.join(self.dataset_dir, "data.yaml")

        # Converter para caminho absoluto
        dataset_path = os.path.abspath(self.dataset_dir)

        # Definir caminhos
        train_path = os.path.join(dataset_path, "train/images")
        val_path = os.path.join(dataset_path, "val/images")
        test_path = os.path.join(dataset_path, "test/images")

        # Verificar se diretórios existem
        for path in [train_path, val_path, test_path]:
            if not os.path.exists(path):
                logger.warning(f"Diretório não encontrado: {path}")

        data = {
            "train": train_path,
            "val": val_path,
            "test": test_path,
            "nc": len(self.classes),
            "names": self.classes,
        }

        try:
            with open(output_path, "w") as f:
                yaml.dump(data, f, default_flow_style=False)
            logger.info(f"Configuração do dataset salva em {output_path}")
        except Exception as e:
            logger.error(f"Erro ao criar arquivo YAML: {str(e)}")

        return output_path
