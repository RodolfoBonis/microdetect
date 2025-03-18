"""
Diálogo para exibição de estatísticas de anotação.
"""

import tkinter as tk
import logging
import glob
import os
from typing import List

from microdetect.annotation.annotator.ui.base import create_secure_dialog, center_window

logger = logging.getLogger(__name__)


class StatisticsDialog:
    """
    Diálogo para exibição de estatísticas de anotação.
    """

    def __init__(self, output_dir, classes, progress_file=".annotation_progress.json"):
        """
        Inicializa o diálogo de estatísticas.

        Args:
            output_dir: Diretório contendo as anotações
            classes: Lista de classes disponíveis para anotação
            progress_file: Nome do arquivo de progresso
        """
        self.output_dir = output_dir
        self.classes = classes
        self.progress_file = progress_file

        # Importar matplotlib aqui para evitar dependência desnecessária se não for usado
        try:
            import matplotlib.pyplot as plt
            from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
            from matplotlib.figure import Figure
            self.mpl_available = True
            self.Figure = Figure
            self.FigureCanvasTkAgg = FigureCanvasTkAgg
        except ImportError:
            logger.warning("Matplotlib não disponível, gráficos não serão exibidos")
            self.mpl_available = False

    def _get_class_name(self, class_id):
        """
        Obtém o nome completo da classe a partir do ID.

        Args:
            class_id: ID da classe (ex: "0")

        Returns:
            Nome completo da classe (ex: "0-levedura")
        """
        return next((c for c in self.classes if c.startswith(class_id)), f"Classe {class_id}")

    def _count_annotations_by_class(self):
        """
        Conta o número de anotações por classe.

        Returns:
            Tupla com (dicionário de contagem por classe, total de anotações)
        """
        # Inicializar contagem de classes com todas as classes conhecidas
        class_counts = {class_id.split('-')[0]: 0 for class_id in self.classes}
        total_boxes = 0

        # Percorrer todos os arquivos de anotação
        annotation_files = glob.glob(os.path.join(self.output_dir, "*.txt"))
        for ann_file in annotation_files:
            if os.path.basename(ann_file) == self.progress_file:
                continue  # Pular o arquivo de progresso

            with open(ann_file, "r") as f:
                for line in f:
                    parts = line.strip().split()
                    if len(parts) >= 5:  # formato YOLO: class x_center y_center width height
                        class_id = parts[0]
                        class_counts[class_id] = class_counts.get(class_id, 0) + 1
                        total_boxes += 1

        return class_counts, total_boxes

    def show(self):
        """Exibe o diálogo de estatísticas."""
        try:
            # Calcular estatísticas
            class_counts, total_objetos = self._count_annotations_by_class()

            # Contar arquivos de anotação
            annotation_files = [f for f in glob.glob(os.path.join(self.output_dir, "*.txt"))
                                if os.path.basename(f) != self.progress_file]
            total_imagens_anotadas = len(annotation_files)

            # Criar janela para o dashboard de forma segura
            stats_window = create_secure_dialog()
            stats_window.title("Dashboard de Estatísticas de Anotação")
            stats_window.geometry("800x600")
            stats_window.minsize(600, 400)

            # Frame principal
            main_frame = tk.Frame(stats_window)
            main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

            # Título
            tk.Label(
                main_frame,
                text="Estatísticas de Anotação",
                font=("Arial", 16, "bold")
            ).pack(pady=10)

            # Frame para estatísticas gerais
            stats_frame = tk.Frame(main_frame)
            stats_frame.pack(fill=tk.X, pady=10)

            # Estatísticas gerais
            tk.Label(
                stats_frame,
                text=f"Total de imagens anotadas: {total_imagens_anotadas}",
                font=("Arial", 12)
            ).pack(anchor="w")

            tk.Label(
                stats_frame,
                text=f"Total de objetos anotados: {total_objetos}",
                font=("Arial", 12)
            ).pack(anchor="w")

            # Média de objetos por imagem
            avg_objects = total_objetos / total_imagens_anotadas if total_imagens_anotadas > 0 else 0
            tk.Label(
                stats_frame,
                text=f"Média de objetos por imagem: {avg_objects:.2f}",
                font=("Arial", 12)
            ).pack(anchor="w")

            # Frame para gráficos
            graph_frame = tk.Frame(main_frame)
            graph_frame.pack(fill=tk.BOTH, expand=True, pady=10)

            # Preparar dados para o gráfico
            classes = []
            counts = []
            colors = ['#4CAF50', '#2196F3', '#FFC107', '#F44336', '#9C27B0', '#00BCD4', '#FF9800', '#795548']

            for i, (class_id, count) in enumerate(sorted(class_counts.items())):
                if count > 0:
                    classes.append(self._get_class_name(class_id))
                    counts.append(count)

            # Adicionar gráficos se matplotlib estiver disponível
            if self.mpl_available and classes and counts:
                # Criar figura para gráficos
                figure = self.Figure(figsize=(8, 4), dpi=100)

                # Gráfico de distribuição de classes
                ax1 = figure.add_subplot(121)  # 1 linha, 2 colunas, posição 1

                # Criar gráfico de barras
                ax1.bar(classes, counts, color=colors[:len(classes)])
                ax1.set_title('Distribuição de Classes')
                ax1.set_ylabel('Quantidade')
                ax1.tick_params(axis='x', rotation=45)

                # Gráfico de pizza com porcentagens
                ax2 = figure.add_subplot(122)  # 1 linha, 2 colunas, posição 2

                # Calcular porcentagens
                if sum(counts) > 0:
                    percentages = [count / sum(counts) * 100 for count in counts]
                    ax2.pie(percentages, labels=classes, autopct='%1.1f%%',
                            startangle=90, colors=colors[:len(classes)])
                    ax2.set_title('Porcentagem por Classe')

                figure.tight_layout()

                # Incorporar o gráfico no tkinter
                canvas = self.FigureCanvasTkAgg(figure, graph_frame)
                canvas.draw()
                canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
            else:
                # Exibir mensagem se não houver matplotlib ou dados
                if not self.mpl_available:
                    msg = "Matplotlib não disponível. Instale matplotlib para visualizar gráficos."
                elif not classes or not counts:
                    msg = "Não há dados suficientes para gerar gráficos."
                else:
                    msg = "Não foi possível gerar gráficos."

                tk.Label(graph_frame, text=msg, font=("Arial", 12)).pack(pady=20)

            # Frame para detalhes por classe
            details_frame = tk.Frame(main_frame)
            details_frame.pack(fill=tk.X, pady=10)

            # Título da seção
            tk.Label(
                details_frame,
                text="Detalhes por Classe",
                font=("Arial", 12, "bold")
            ).pack(anchor="w", pady=5)

            # Tabela de detalhes
            class_details = tk.Frame(details_frame)
            class_details.pack(fill=tk.X)

            # Cabeçalhos
            tk.Label(
                class_details,
                text="Classe",
                width=20,
                font=("Arial", 10, "bold"),
                relief=tk.RIDGE
            ).grid(row=0, column=0, sticky="ew")

            tk.Label(
                class_details,
                text="Quantidade",
                width=10,
                font=("Arial", 10, "bold"),
                relief=tk.RIDGE
            ).grid(row=0, column=1, sticky="ew")

            tk.Label(
                class_details,
                text="Porcentagem",
                width=15,
                font=("Arial", 10, "bold"),
                relief=tk.RIDGE
            ).grid(row=0, column=2, sticky="ew")

            # Preencher dados da tabela
            for i, (class_name, count) in enumerate(zip(classes, counts)):
                percentage = count / total_objetos * 100 if total_objetos > 0 else 0

                tk.Label(
                    class_details,
                    text=class_name,
                    width=20,
                    anchor="w",
                    relief=tk.RIDGE
                ).grid(row=i + 1, column=0, sticky="ew")

                tk.Label(
                    class_details,
                    text=str(count),
                    width=10,
                    relief=tk.RIDGE
                ).grid(row=i + 1, column=1, sticky="ew")

                tk.Label(
                    class_details,
                    text=f"{percentage:.1f}%",
                    width=15,
                    relief=tk.RIDGE
                ).grid(row=i + 1, column=2, sticky="ew")

            # Botão para fechar
            tk.Button(
                main_frame,
                text="Fechar",
                command=stats_window.destroy,
                width=10
            ).pack(pady=10)

            # Centralizar janela
            center_window(stats_window)

            # Tornar modal
            stats_window.transient()
            stats_window.grab_set()

            # Limpar recursos ao fechar
            def on_closing():
                # Remover referência à janela temporária se existir
                if hasattr(stats_window, '_temp_root') and stats_window._temp_root:
                    try:
                        stats_window._temp_root.destroy()
                    except:
                        pass
                stats_window.destroy()

            stats_window.protocol("WM_DELETE_WINDOW", on_closing)
            stats_window.wait_window()

        except Exception as e:
            logger.error(f"Erro ao exibir estatísticas: {e}")
            tk.messagebox.showerror("Erro", f"Não foi possível exibir as estatísticas: {str(e)}")