"""
Módulo para geração de relatórios de análise e resultados.
"""

import csv
import logging
import os
from datetime import datetime
from typing import Dict, List, Optional, Any

import jinja2
import pandas as pd

logger = logging.getLogger(__name__)


class ReportGenerator:
    """
    Classe para gerar relatórios em vários formatos (PDF, CSV, JSON).
    """

    def __init__(self, output_dir: str = None):
        """
        Inicializa o gerador de relatórios.

        Args:
            output_dir: Diretório para salvar os relatórios
        """
        self.output_dir = output_dir or "reports"
        os.makedirs(self.output_dir, exist_ok=True)

    def generate_pdf_report(
            self,
            metrics: Dict[str, Any],
            model_path: str,
            output_file: Optional[str] = None,
            include_images: List[str] = None,
            template_path: Optional[str] = None
    ) -> str:
        """
        Gera um relatório PDF detalhado com métricas de avaliação.

        Args:
            metrics: Dicionário com métricas de desempenho
            model_path: Caminho para o modelo avaliado
            output_file: Caminho para o arquivo PDF de saída
            include_images: Lista de caminhos de imagens para incluir no relatório
            template_path: Caminho para o template HTML personalizado

        Returns:
            Caminho para o arquivo PDF gerado
        """
        try:
            import pdfkit
        except ImportError:
            logger.error("pdfkit não encontrado. Instale com: pip install pdfkit")
            logger.error("Nota: pdfkit requer wkhtmltopdf instalado no sistema")
            return None

        # Definir caminho de saída
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = os.path.join(self.output_dir, f"relatorio_avaliacao_{timestamp}.pdf")

        # Garantir que o diretório de saída existe
        os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)

        # Preparar dados para o template
        report_data = {
            "model_name": os.path.basename(model_path),
            "model_path": model_path,
            "date": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            "general_metrics": metrics.get("metricas_gerais", {}),
            "class_metrics": metrics.get("metricas_por_classe", []),
            "images": include_images or []
        }

        # Carregar template
        if template_path and os.path.exists(template_path):
            with open(template_path, "r") as f:
                template_str = f.read()
        else:
            # Template HTML padrão
            template_str = """
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <title>Relatório de Avaliação - {{ model_name }}</title>
                <style>
                    body {
                        font-family: Arial, sans-serif;
                        margin: 20px;
                        color: #333;
                    }
                    h1, h2, h3 {
                        color: #2c3e50;
                    }
                    .header {
                        text-align: center;
                        margin-bottom: 30px;
                    }
                    .section {
                        margin-bottom: 20px;
                    }
                    table {
                        width: 100%;
                        border-collapse: collapse;
                        margin-bottom: 20px;
                    }
                    th, td {
                        border: 1px solid #ddd;
                        padding: 8px;
                        text-align: center;
                    }
                    th {
                        background-color: #f2f2f2;
                    }
                    tr:nth-child(even) {
                        background-color: #f9f9f9;
                    }
                    .footer {
                        text-align: center;
                        margin-top: 30px;
                        font-size: 12px;
                        color: #777;
                    }
                    .image-container {
                        text-align: center;
                        margin: 20px 0;
                    }
                    .image-container img {
                        max-width: 100%;
                        max-height: 400px;
                    }
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>Relatório de Avaliação de Modelo</h1>
                    <p>Modelo: {{ model_name }}</p>
                    <p>Data: {{ date }}</p>
                </div>

                <div class="section">
                    <h2>Informações do Modelo</h2>
                    <table>
                        <tr>
                            <th>Parâmetro</th>
                            <th>Valor</th>
                        </tr>
                        <tr>
                            <td>Nome do Modelo</td>
                            <td>{{ model_name }}</td>
                        </tr>
                        <tr>
                            <td>Caminho do Modelo</td>
                            <td>{{ model_path }}</td>
                        </tr>
                    </table>
                </div>

                <div class="section">
                    <h2>Métricas Gerais</h2>
                    <table>
                        <tr>
                            <th>Métrica</th>
                            <th>Valor</th>
                        </tr>
                        {% for metric, value in general_metrics.items() %}
                        <tr>
                            <td>{{ metric }}</td>
                            <td>{{ "%.4f"|format(value) }}</td>
                        </tr>
                        {% endfor %}
                    </table>
                </div>

                <div class="section">
                    <h2>Métricas por Classe</h2>
                    {% if class_metrics %}
                    <table>
                        <tr>
                            <th>Classe</th>
                            <th>Precisão (AP50)</th>
                            <th>Recall</th>
                            <th>Precisão</th>
                            <th>F1-Score</th>
                        </tr>
                        {% for metric in class_metrics %}
                        <tr>
                            <td>{{ metric.Classe }}</td>
                            <td>{{ "%.4f"|format(metric["Precisão (AP50)"]) }}</td>
                            <td>{{ "%.4f"|format(metric.Recall) }}</td>
                            <td>{{ "%.4f"|format(metric.Precisão) }}</td>
                            <td>{{ "%.4f"|format(metric["F1-Score"]) }}</td>
                        </tr>
                        {% endfor %}
                    </table>
                    {% else %}
                    <p>Não há métricas por classe disponíveis.</p>
                    {% endif %}
                </div>

                {% if images %}
                <div class="section">
                    <h2>Imagens de Exemplo</h2>
                    {% for image in images %}
                    <div class="image-container">
                        <img src="{{ image }}" alt="Imagem de exemplo">
                        <p>{{ image }}</p>
                    </div>
                    {% endfor %}
                </div>
                {% endif %}

                <div class="footer">
                    <p>Gerado por MicroDetect em {{ date }}</p>
                </div>
            </body>
            </html>
            """

        # Renderizar template
        template = jinja2.Template(template_str)
        html_content = template.render(**report_data)

        # Salvar versão HTML do relatório (para debug)
        html_path = output_file.replace(".pdf", ".html")
        with open(html_path, "w") as f:
            f.write(html_content)

        # Converter HTML para PDF
        try:
            pdfkit.from_string(html_content, output_file)
            logger.info(f"Relatório PDF gerado: {output_file}")
            return output_file
        except Exception as e:
            logger.error(f"Erro ao gerar PDF: {str(e)}")
            return html_path  # Retorna o caminho HTML como fallback

    def generate_csv_report(
            self,
            metrics: Dict[str, Any],
            output_file: Optional[str] = None
    ) -> str:
        """
        Gera um relatório CSV com métricas de avaliação.

        Args:
            metrics: Dicionário com métricas de desempenho
            output_file: Caminho para o arquivo CSV de saída

        Returns:
            Caminho para o arquivo CSV gerado
        """
        # Definir caminho de saída
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = os.path.join(self.output_dir, f"metricas_{timestamp}.csv")

        # Garantir que o diretório de saída existe
        os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)

        # Extrair métricas
        general_metrics = metrics.get("metricas_gerais", {})
        class_metrics = metrics.get("metricas_por_classe", [])

        # Salvar métricas gerais
        with open(output_file, "w", newline="") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["Tipo", "Métrica", "Valor"])

            # Métricas gerais
            for metric, value in general_metrics.items():
                writer.writerow(["Geral", metric, f"{value:.4f}"])

            writer.writerow([])  # Linha em branco

            # Métricas por classe
            if class_metrics:
                writer.writerow(["Classe", "Precisão (AP50)", "Recall", "Precisão", "F1-Score"])

                for metric in class_metrics:
                    writer.writerow([
                        metric["Classe"],
                        f"{metric['Precisão (AP50)']:.4f}",
                        f"{metric['Recall']:.4f}",
                        f"{metric['Precisão']:.4f}",
                        f"{metric['F1-Score']:.4f}"
                    ])

        logger.info(f"Relatório CSV gerado: {output_file}")
        return output_file

    def export_detections_to_csv(
            self,
            detections: Dict[str, List[Dict[str, Any]]],
            output_file: Optional[str] = None
    ) -> str:
        """
        Exporta resultados de detecção para CSV.

        Args:
            detections: Dicionário com detecções por imagem
            output_file: Caminho para o arquivo CSV de saída

        Returns:
            Caminho para o arquivo CSV gerado
        """
        # Definir caminho de saída
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = os.path.join(self.output_dir, f"deteccoes_{timestamp}.csv")

        # Garantir que o diretório de saída existe
        os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)

        # Preparar linhas para CSV
        rows = []
        for image_name, image_detections in detections.items():
            for det in image_detections:
                row = {
                    "imagem": image_name,
                    "classe": det.get("class", ""),
                    "classe_nome": det.get("class_name", ""),
                    "confianca": det.get("confidence", 0),
                    "x1": det.get("bbox", [0, 0, 0, 0])[0],
                    "y1": det.get("bbox", [0, 0, 0, 0])[1],
                    "x2": det.get("bbox", [0, 0, 0, 0])[2],
                    "y2": det.get("bbox", [0, 0, 0, 0])[3]
                }
                rows.append(row)

        # Criar DataFrame e salvar
        df = pd.DataFrame(rows)
        df.to_csv(output_file, index=False)

        logger.info(f"Detecções exportadas para CSV: {output_file}")
        return output_file

    def export_to_yolo_format(
            self,
            detections: Dict[str, List[Dict[str, Any]]],
            output_dir: Optional[str] = None
    ) -> str:
        """
        Exporta resultados de detecção para o formato YOLO (arquivos .txt).

        Args:
            detections: Dicionário com detecções por imagem
            output_dir: Diretório para salvar os arquivos de anotação

        Returns:
            Caminho para o diretório de anotações
        """
        # Definir diretório de saída
        if output_dir is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_dir = os.path.join(self.output_dir, f"yolo_labels_{timestamp}")

        # Criar diretório de saída
        os.makedirs(output_dir, exist_ok=True)

        # Processar cada imagem
        for image_name, image_detections in detections.items():
            # Nome do arquivo de anotação
            base_name = os.path.splitext(image_name)[0]
            txt_path = os.path.join(output_dir, f"{base_name}.txt")

            # Salvar anotações
            with open(txt_path, "w") as f:
                for det in image_detections:
                    # Extrair informações
                    cls = det.get("class", 0)
                    bbox = det.get("bbox_normalized", None)

                    # Se não tiver bbox normalizado, converter de absoluto para normalizado
                    if bbox is None and "bbox" in det:
                        if len(det["bbox"]) == 4:
                            x1, y1, x2, y2 = det["bbox"]

                            # Verificar se são valores normalizados ou absolutos
                            if all(isinstance(val, float) and val <= 1.0 for val in det["bbox"]):
                                # Já normalizado, mas no formato xyxy
                                center_x = (x1 + x2) / 2
                                center_y = (y1 + y2) / 2
                                width = x2 - x1
                                height = y2 - y1
                            else:
                                # Valores absolutos, converter para normalizados
                                # Assume-se que a imagem tenha dimensões 1.0 x 1.0
                                logger.warning(
                                    f"Usando dimensões padrão para {image_name}. Resultados podem ser imprecisos.")
                                center_x = (x1 + x2) / 2 / 1.0
                                center_y = (y1 + y2) / 2 / 1.0
                                width = (x2 - x1) / 1.0
                                height = (y2 - y1) / 1.0

                            bbox = [center_x, center_y, width, height]

                    # Escrever anotação no formato YOLO
                    if bbox:
                        line = f"{cls} {bbox[0]:.6f} {bbox[1]:.6f} {bbox[2]:.6f} {bbox[3]:.6f}\n"
                        f.write(line)

        logger.info(f"Detecções exportadas para o formato YOLO: {output_dir}")
        return output_dir