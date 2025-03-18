"""
Funções de backup para anotações.
"""

import glob
import logging
import os
import re
import shutil
import time
from typing import Optional

logger = logging.getLogger(__name__)


class AnnotationBackup:
    """
    Gerencia backups de anotações.
    """

    def __init__(self, progress_file=".annotation_progress.json", max_backups=5):
        """
        Inicializa o gerenciador de backups.

        Args:
            progress_file: Nome do arquivo de progresso a ser excluído do backup
            max_backups: Número máximo de backups a serem mantidos
        """
        self.progress_file = progress_file
        self.max_backups = max_backups

    def create_backup(self, label_dir: str) -> Optional[str]:
        """
        Cria um backup com timestamp das anotações atuais e mantém apenas
        os N mais recentes (definido por max_backups).
        Os backups são armazenados em uma pasta 'backups' dentro do diretório de labels.

        Args:
            label_dir: Diretório contendo os arquivos de anotação

        Returns:
            Caminho para o diretório de backup ou None se falhar
        """
        timestamp = time.strftime("%Y%m%d_%H%M%S")

        # Criar diretório de backups (filho do diretório de labels)
        backups_dir = os.path.join(label_dir, "backups")
        os.makedirs(backups_dir, exist_ok=True)

        # Criar diretório específico para este backup
        backup_dir = os.path.join(backups_dir, f"backup_annotations_{timestamp}")

        try:
            if os.path.exists(label_dir):
                os.makedirs(backup_dir, exist_ok=True)
                count = 0

                for file in glob.glob(os.path.join(label_dir, "*.txt")):
                    if os.path.basename(file) != self.progress_file:
                        shutil.copy2(file, backup_dir)
                        count += 1

                if count > 0:
                    logger.info(f"Backup criado em {backup_dir} com {count} arquivos de anotação")

                    # Limitar para manter apenas os backups mais recentes
                    self._cleanup_old_backups(backups_dir)

                    return backup_dir
                else:
                    os.rmdir(backup_dir)
                    logger.info("Nenhum arquivo de anotação encontrado para backup")

        except Exception as e:
            logger.error(f"Erro ao criar backup: {str(e)}")

        return None

    def _cleanup_old_backups(self, backups_dir):
        """
        Limpa backups antigos, mantendo apenas os N mais recentes.

        Args:
            backups_dir: Diretório contendo os backups
        """
        try:
            # Encontrar diretórios de backup existentes
            backup_pattern = re.compile(r"backup_annotations_\d{8}_\d{6}$")
            backup_dirs = []

            for dirname in os.listdir(backups_dir):
                dir_path = os.path.join(backups_dir, dirname)
                if os.path.isdir(dir_path) and backup_pattern.match(dirname):
                    backup_dirs.append(dir_path)

            # Ordenar por timestamp no nome (mais recentes primeiro)
            backup_dirs.sort(reverse=True)

            # Manter apenas os N mais recentes, excluir os demais
            if len(backup_dirs) > self.max_backups:
                for old_backup in backup_dirs[self.max_backups :]:
                    try:
                        shutil.rmtree(old_backup)
                        logger.info(f"Removido backup antigo: {os.path.basename(old_backup)}")
                    except Exception as e:
                        logger.warning(f"Não foi possível remover backup antigo {os.path.basename(old_backup)}: {str(e)}")
        except Exception as e:
            logger.error(f"Erro ao limpar backups antigos: {str(e)}")
