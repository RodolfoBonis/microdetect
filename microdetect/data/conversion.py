"""
Módulo para conversão de formatos de imagem.
"""

import glob
import logging
import os
from typing import List, Tuple

import cv2
import numpy as np
from PIL import Image
from tqdm import tqdm

logger = logging.getLogger(__name__)


class ImageConverter:
    """
    Classe para converter imagens entre diferentes formatos.
    Atualmente suporta conversão de TIFF para PNG.
    """

    @staticmethod
    def convert_tiff_to_png(
            input_dir: str,
            output_dir: str,
            use_opencv: bool = False,
            delete_original: bool = False
    ) -> Tuple[int, int, List[str]]:
        """
        Converte todas as imagens TIFF em um diretório para o formato PNG.

        Args:
            input_dir: Diretório contendo as imagens TIFF
            output_dir: Diretório para salvar as imagens PNG
            use_opencv: Se deve usar OpenCV (True) ou PIL (False) para conversão
            delete_original: Se deve excluir os arquivos TIFF originais após a conversão

        Returns:
            Tupla com (número de sucessos, número de falhas, lista de erros)
        """
        # Criar diretório de saída se não existir
        os.makedirs(output_dir, exist_ok=True)

        # Obter todos os arquivos TIFF
        tiff_files = []
        for ext in ['*.tif', '*.tiff']:
            tiff_files.extend(glob.glob(os.path.join(input_dir, ext)))

        if not tiff_files:
            logger.warning(f"Nenhum arquivo TIFF encontrado em {input_dir}")
            return 0, 0, ["Nenhum arquivo TIFF encontrado"]

        logger.info(f"Encontrados {len(tiff_files)} arquivos TIFF para conversão")

        # Configurar barra de progresso
        progress_bar = tqdm(total=len(tiff_files), desc="Convertendo TIFF para PNG")

        errors = 0
        success = 0
        error_messages = []

        # Converter cada arquivo
        for tiff_path in tiff_files:
            base_name = os.path.basename(tiff_path)
            name_without_ext = os.path.splitext(base_name)[0]
            png_path = os.path.join(output_dir, f"{name_without_ext}.png")

            try:
                if use_opencv:
                    # Abordagem OpenCV
                    img = cv2.imread(tiff_path, cv2.IMREAD_UNCHANGED)
                    if img is None:
                        error_msg = f"Falha ao ler {tiff_path} com OpenCV"
                        error_messages.append(error_msg)
                        logger.error(error_msg)
                        errors += 1
                        progress_bar.update(1)
                        continue

                    # Normalizar se necessário (para imagens de 16 bits)
                    if img.dtype == np.uint16:
                        img = cv2.normalize(img, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)

                    cv2.imwrite(png_path, img)
                else:
                    # Abordagem PIL
                    with Image.open(tiff_path) as img:
                        img.save(png_path, "PNG")

                # Excluir arquivo TIFF original se solicitado
                if delete_original:
                    os.remove(tiff_path)
                    logger.debug(f"Arquivo original excluído: {tiff_path}")

                success += 1
                logger.debug(f"Convertido: {tiff_path} -> {png_path}")

            except Exception as e:
                error_msg = f"Erro ao converter {tiff_path}: {str(e)}"
                error_messages.append(error_msg)
                logger.error(error_msg)
                errors += 1

            # Atualizar barra de progresso
            progress_bar.update(1)

        # Fechar barra de progresso
        progress_bar.close()

        logger.info(f"Conversão concluída: {success} arquivos convertidos com sucesso, {errors} erros")
        return success, errors, error_messages

    @staticmethod
    def batch_convert(
            input_dir: str,
            output_dir: str,
            source_format: str,
            target_format: str,
            use_opencv: bool = False,
            delete_original: bool = False
    ) -> Tuple[int, int, List[str]]:
        """
        Converte imagens de um formato para outro.

        Args:
            input_dir: Diretório contendo as imagens de origem
            output_dir: Diretório para salvar as imagens convertidas
            source_format: Formato de origem (ex: 'tif', 'jpg')
            target_format: Formato de destino (ex: 'png', 'jpg')
            use_opencv: Se deve usar OpenCV para conversão
            delete_original: Se deve excluir os arquivos originais após a conversão

        Returns:
            Tupla com (número de sucessos, número de falhas, lista de erros)
        """
        # Atualmente, só implementamos conversão de TIFF para PNG
        if source_format.lower() in ['tif', 'tiff'] and target_format.lower() == 'png':
            return ImageConverter.convert_tiff_to_png(
                input_dir, output_dir, use_opencv, delete_original
            )
        else:
            msg = f"Conversão de {source_format} para {target_format} não implementada"
            logger.error(msg)
            return 0, 1, [msg]