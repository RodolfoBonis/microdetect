"""
Módulo para gerenciamento de configuração do projeto.
"""

import importlib.resources
import logging
import os
from typing import Any, Dict, List, Optional

import yaml

logger = logging.getLogger(__name__)

# Lista de locais onde procurar o config.yaml, em ordem de prioridade
CONFIG_SEARCH_PATHS = [
    os.path.join(os.getcwd(), "config.yaml"),  # Diretório atual
    os.path.expanduser("~/.microdetect/config.yaml"),  # Diretório do usuário
]

DEFAULT_CONFIG_PATH = None  # Será configurado para o caminho do pacote


class Config:
    """Classe para carregar e acessar configurações do projeto."""

    def __init__(self, config_path: Optional[str] = None):
        """
        Inicializa o objeto de configuração.

        Args:
            config_path: Caminho para o arquivo de configuração. Se None, busca em locais padrão.
        """
        self.config_path = config_path
        self.config_data = self._load_config()

    def _find_config(self) -> Optional[str]:
        """
        Busca o arquivo de configuração em locais padrão.

        Returns:
            Caminho para o arquivo de configuração ou None
        """
        if self.config_path and os.path.exists(self.config_path):
            return self.config_path

        # Verifica locais padrão
        for path in CONFIG_SEARCH_PATHS:
            if os.path.exists(path):
                return path

        return None

    def _load_config(self) -> Dict[str, Any]:
        """
        Carrega o arquivo de configuração YAML.

        Returns:
            Dict contendo as configurações carregadas
        """
        try:
            config_path = self._find_config()

            if config_path:
                with open(config_path, "r", encoding="utf-8") as f:
                    config = yaml.safe_load(f)
                    logger.info(f"Configuração carregada de: {config_path}")
                    self.config_path = config_path
                    return config
            else:
                # Se nenhum arquivo foi encontrado, carrega o padrão do pacote
                logger.warning(
                    "Arquivo de configuração não encontrado. "
                    "Execute 'microdetect init' para criar uma configuração no diretório atual "
                    "ou use valores padrão."
                )
                return self._get_default_config()

        except Exception as e:
            logger.error(f"Erro ao carregar configuração: {e}")
            logger.info("Usando valores padrão.")
            return self._get_default_config()

    def _get_default_config(self) -> Dict[str, Any]:
        """
        Carrega a configuração padrão do pacote.

        Returns:
            Dict com valores padrão de configuração
        """
        try:
            # Tentar carregar do pacote usando importlib.resources (moderna)
            try:
                # Para Python 3.9+
                import importlib.resources as resources

                try:
                    # Modern approach for Python 3.9+
                    with resources.files("microdetect").joinpath("default_config.yaml").open("r") as f:
                        logger.info(f"Configuração padrão carregada do pacote")
                        return yaml.safe_load(f)
                except (ImportError, FileNotFoundError, AttributeError):
                    # Fallback for Python 3.7-3.8
                    default_config_text = resources.read_text("microdetect", "default_config.yaml")
                    logger.info(f"Configuração padrão carregada do pacote")
                    return yaml.safe_load(default_config_text)
            except (ImportError, FileNotFoundError) as e:
                # Further fallback - look for file directly
                try:
                    import microdetect

                    pkg_path = os.path.dirname(microdetect.__file__)
                    default_config_path = os.path.join(pkg_path, "default_config.yaml")
                    if os.path.exists(default_config_path):
                        with open(default_config_path, "r", encoding="utf-8") as f:
                            logger.info(f"Configuração padrão carregada do caminho: {default_config_path}")
                            return yaml.safe_load(f)
                except Exception as pkg_error:
                    logger.warning(f"Erro ao localizar pacote: {pkg_error}")

                logger.warning(f"Não foi possível carregar default_config.yaml: {e}")
        except Exception as e:
            logger.warning(f"Erro ao carregar configuração padrão: {e}")

        # Valores fixos como fallback
        logger.info("Usando valores de configuração padrão codificados")
        return {
            "directories": {
                "dataset": "dataset",
                "images": "data/images",
                "labels": "data/labels",
                "output": "runs/train",
                "reports": "reports",
            },
            "classes": ["0-levedura", "1-fungo", "2-micro-alga"],
            "color_map": {"0": [0, 255, 0], "1": [0, 0, 255], "2": [255, 0, 0]},
            "training": {
                "model_size": "s",
                "epochs": 50,
                "batch_size": 32,
                "image_size": 640,
                "pretrained": True,
            },
            "dataset": {
                "train_ratio": 0.7,
                "val_ratio": 0.15,
                "test_ratio": 0.15,
                "seed": 42,
            },
            "augmentation": {
                "factor": 20,
                "brightness_range": [0.8, 1.2],
                "contrast_range": [-30, 30],
                "flip_probability": 0.5,
                "rotation_range": [-15, 15],
                "noise_probability": 0.3,
            },
        }

    def get(self, key: str, default: Any = None) -> Any:
        """
        Obtém um valor de configuração.

        Args:
            key: Caminho da configuração usando notação de ponto (ex: 'training.model_size')
            default: Valor padrão a retornar se a chave não for encontrada

        Returns:
            Valor da configuração ou o valor padrão
        """
        keys = key.split(".")
        result = self.config_data

        try:
            for k in keys:
                result = result[k]
            return result
        except (KeyError, TypeError):
            logger.debug(f"Configuração não encontrada: {key}. Usando valor padrão: {default}")
            return default

    def save(self, config_path: Optional[str] = None) -> None:
        """
        Salva a configuração atual em um arquivo YAML.

        Args:
            config_path: Caminho para salvar o arquivo de configuração
        """
        save_path = config_path or self.config_path or os.path.join(os.getcwd(), "config.yaml")
        try:
            with open(save_path, "w", encoding="utf-8") as f:
                yaml.dump(self.config_data, f, default_flow_style=False)
            logger.info(f"Configuração salva em: {save_path}")
        except Exception as e:
            logger.error(f"Erro ao salvar configuração: {e}")


# Instância global para uso em outros módulos
config = Config()
