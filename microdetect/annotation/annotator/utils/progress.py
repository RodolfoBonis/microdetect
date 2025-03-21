"""
Gerenciamento de progresso para anotação de imagens.
"""

import glob
import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class ProgressManager:
    """
    Gerencia o progresso de anotação de imagens.
    """

    def __init__(self, progress_file: str = ".annotation_progress.json"):
        """
        Inicializa o gerenciador de progresso.

        Args:
            progress_file: Nome do arquivo para rastrear o progresso
        """
        self.progress_file = progress_file

    def save_progress(self, output_dir: str, current_image: str, additional_data: Dict = None) -> bool:
        """
        Salva o progresso atual da anotação.

        Args:
            output_dir: Diretório onde o arquivo de progresso será salvo
            current_image: Caminho da imagem atual
            additional_data: Dados adicionais a serem salvos (opcional)

        Returns:
            True se o progresso foi salvo com sucesso, False caso contrário
        """
        try:
            progress_path = os.path.join(output_dir, self.progress_file)

            # Dados básicos de progresso
            progress_data = {
                "last_annotated": current_image,
                "timestamp": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat(),
            }

            # Adicionar dados extras se fornecidos
            if additional_data:
                progress_data.update(additional_data)

            # Verificar se já existe um arquivo de progresso
            if os.path.exists(progress_path):
                try:
                    # Carregar dados existentes
                    with open(progress_path, "r") as f:
                        existing_data = json.load(f)

                    # Manter histórico de imagens anotadas
                    if "annotation_history" not in existing_data:
                        existing_data["annotation_history"] = []

                    # Adicionar entrada atual ao histórico
                    history_entry = {"image": current_image, "timestamp": datetime.now().isoformat()}

                    # Evitar duplicatas no histórico
                    if (
                        not existing_data["annotation_history"]
                        or existing_data["annotation_history"][-1]["image"] != current_image
                    ):
                        existing_data["annotation_history"].append(history_entry)

                    # Limitar tamanho do histórico
                    if len(existing_data["annotation_history"]) > 100:
                        existing_data["annotation_history"] = existing_data["annotation_history"][-100:]

                    # Atualizar dados básicos
                    existing_data.update(progress_data)
                    progress_data = existing_data
                except Exception as e:
                    logger.warning(f"Erro ao ler arquivo de progresso existente: {e}")
                    # Continuar com dados novos

            # Salvar no arquivo
            with open(progress_path, "w") as f:
                json.dump(progress_data, f, indent=2)

            logger.info(f"Progresso salvo em {progress_path}")
            return True
        except Exception as e:
            logger.error(f"Erro ao salvar progresso: {str(e)}")
            return False

    def load_progress(self, output_dir: str) -> Optional[Dict]:
        """
        Carrega as informações de progresso.

        Args:
            output_dir: Diretório contendo o arquivo de progresso

        Returns:
            Dicionário com informações de progresso ou None se não houver
        """
        progress_path = os.path.join(output_dir, self.progress_file)

        if not os.path.exists(progress_path):
            return None

        try:
            with open(progress_path, "r") as f:
                progress_data = json.load(f)

            logger.info(f"Progresso carregado de {progress_path}")
            return progress_data
        except Exception as e:
            logger.error(f"Erro ao carregar progresso: {str(e)}")
            return None

    def get_last_annotated_image(self, output_dir: str) -> Optional[str]:
        """
        Obtém o caminho da última imagem anotada.

        Args:
            output_dir: Diretório contendo o arquivo de progresso

        Returns:
            Caminho da última imagem anotada ou None se não houver progresso
        """
        progress_data = self.load_progress(output_dir)

        if not progress_data:
            return None

        last_annotated = progress_data.get("last_annotated")

        if last_annotated and os.path.exists(last_annotated):
            logger.info(f"Última imagem anotada: {os.path.basename(last_annotated)}")
            return last_annotated

        return None

    def calculate_progress(self, image_dir: str, output_dir: str) -> Tuple[int, int, float]:
        """
        Calcula o progresso da anotação.

        Args:
            image_dir: Diretório contendo as imagens
            output_dir: Diretório contendo as anotações

        Returns:
            Tupla com (imagens anotadas, total de imagens, porcentagem)
        """
        # Contar todas as imagens
        all_images = []
        for ext in ["*.jpg", "*.jpeg", "*.png"]:
            all_images.extend(glob.glob(os.path.join(image_dir, ext)))

        total_images = len(all_images)

        if total_images == 0:
            return 0, 0, 0.0

        # Contar anotações existentes
        annotated_count = 0

        for img_path in all_images:
            base_name = os.path.splitext(os.path.basename(img_path))[0]
            annotation_path = os.path.join(output_dir, f"{base_name}.txt")

            if os.path.exists(annotation_path):
                annotated_count += 1

        # Calcular porcentagem
        percentage = (annotated_count / total_images) * 100 if total_images > 0 else 0

        return annotated_count, total_images, percentage

    def get_annotation_history(self, output_dir: str, max_entries: int = 10) -> List[Dict]:
        """
        Obtém o histórico de anotações.

        Args:
            output_dir: Diretório contendo o arquivo de progresso
            max_entries: Número máximo de entradas a retornar

        Returns:
            Lista de dicionários com informações de histórico
        """
        progress_data = self.load_progress(output_dir)

        if not progress_data or "annotation_history" not in progress_data:
            return []

        history = progress_data.get("annotation_history", [])

        # Retornar as entradas mais recentes
        return history[-max_entries:]

    def get_session_statistics(self, output_dir: str) -> Dict[str, Any]:
        """
        Obtém estatísticas da sessão atual de anotação.

        Args:
            output_dir: Diretório contendo o arquivo de progresso

        Returns:
            Dicionário com estatísticas da sessão
        """
        progress_data = self.load_progress(output_dir)

        if not progress_data:
            return {"session_active": False, "session_duration": 0, "images_annotated_session": 0}

        # Verificar se há dados de sessão
        if "session_start" not in progress_data:
            return {"session_active": False, "session_duration": 0, "images_annotated_session": 0}

        # Calcular duração da sessão
        try:
            session_start = datetime.fromisoformat(progress_data["session_start"])
            last_updated = datetime.fromisoformat(progress_data.get("last_updated", progress_data["session_start"]))

            duration_seconds = (last_updated - session_start).total_seconds()

            return {
                "session_active": True,
                "session_start": session_start.isoformat(),
                "session_duration": duration_seconds,
                "images_annotated_session": progress_data.get("images_annotated_session", 0),
            }
        except Exception as e:
            logger.error(f"Erro ao calcular estatísticas de sessão: {e}")
            return {"session_active": False, "session_duration": 0, "images_annotated_session": 0, "error": str(e)}

    def start_session(self, output_dir: str) -> bool:
        """
        Inicia uma nova sessão de anotação.

        Args:
            output_dir: Diretório para salvar o arquivo de progresso

        Returns:
            True se a sessão foi iniciada com sucesso
        """
        progress_data = self.load_progress(output_dir) or {}

        # Configurar dados da sessão
        progress_data["session_start"] = datetime.now().isoformat()
        progress_data["last_updated"] = datetime.now().isoformat()
        progress_data["images_annotated_session"] = 0

        # Salvar progresso
        progress_path = os.path.join(output_dir, self.progress_file)

        try:
            with open(progress_path, "w") as f:
                json.dump(progress_data, f, indent=2)

            logger.info(f"Nova sessão de anotação iniciada: {progress_data['session_start']}")
            return True
        except Exception as e:
            logger.error(f"Erro ao iniciar sessão: {str(e)}")
            return False

    def end_session(self, output_dir: str) -> Dict[str, Any]:
        """
        Finaliza a sessão atual e retorna estatísticas.

        Args:
            output_dir: Diretório contendo o arquivo de progresso

        Returns:
            Dicionário com estatísticas da sessão finalizada
        """
        # Obter dados de sessão atual
        session_stats = self.get_session_statistics(output_dir)

        if not session_stats["session_active"]:
            return session_stats

        # Carregar dados completos
        progress_data = self.load_progress(output_dir) or {}

        # Atualizar histórico de sessões
        if "session_history" not in progress_data:
            progress_data["session_history"] = []

        # Criar resumo da sessão
        session_summary = {
            "start_time": progress_data.get("session_start"),
            "end_time": datetime.now().isoformat(),
            "duration_seconds": session_stats["session_duration"],
            "images_annotated": progress_data.get("images_annotated_session", 0),
        }

        # Adicionar ao histórico
        progress_data["session_history"].append(session_summary)

        # Limitar tamanho do histórico de sessões
        if len(progress_data["session_history"]) > 20:
            progress_data["session_history"] = progress_data["session_history"][-20:]

        # Remover dados da sessão atual
        progress_data.pop("session_start", None)
        progress_data.pop("images_annotated_session", None)

        # Atualizar last_updated
        progress_data["last_updated"] = datetime.now().isoformat()

        # Salvar progresso atualizado
        progress_path = os.path.join(output_dir, self.progress_file)

        try:
            with open(progress_path, "w") as f:
                json.dump(progress_data, f, indent=2)

            logger.info(f"Sessão de anotação finalizada: {session_summary['end_time']}")

            # Retornar resumo da sessão
            return {"session_active": False, "session_summary": session_summary}
        except Exception as e:
            logger.error(f"Erro ao finalizar sessão: {str(e)}")
            return {"session_active": False, "error": str(e)}

    def increment_session_count(self, output_dir: str) -> bool:
        """
        Incrementa o contador de imagens anotadas na sessão atual.

        Args:
            output_dir: Diretório contendo o arquivo de progresso

        Returns:
            True se o contador foi incrementado com sucesso
        """
        progress_data = self.load_progress(output_dir)

        if not progress_data or "session_start" not in progress_data:
            # Iniciar uma nova sessão
            self.start_session(output_dir)
            progress_data = self.load_progress(output_dir) or {}

        # Incrementar contador
        progress_data["images_annotated_session"] = progress_data.get("images_annotated_session", 0) + 1
        progress_data["last_updated"] = datetime.now().isoformat()

        # Salvar progresso
        progress_path = os.path.join(output_dir, self.progress_file)

        try:
            with open(progress_path, "w") as f:
                json.dump(progress_data, f, indent=2)

            return True
        except Exception as e:
            logger.error(f"Erro ao incrementar contador de sessão: {str(e)}")
            return False
