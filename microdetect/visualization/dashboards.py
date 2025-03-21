"""
Módulo para criação de dashboards interativos para exploração de dados.
"""

import json
import logging
import os
import threading
import webbrowser
from typing import Dict

import pandas as pd

logger = logging.getLogger(__name__)


class DashboardGenerator:
    """
    Classe para criar dashboards interativos para exploração de dados.
    """

    def __init__(self, output_dir: str = None):
        """
        Inicializa o gerador de dashboards.

        Args:
            output_dir: Diretório para salvar arquivos temporários
        """
        self.output_dir = output_dir or "dashboards"
        os.makedirs(self.output_dir, exist_ok=True)

    def create_detection_dashboard(self, results_dir: str, port: int = 8050, open_browser: bool = True) -> int:
        """
        Cria um dashboard interativo para explorar resultados de detecção.

        Args:
            results_dir: Diretório com resultados de detecção
            port: Porta para o servidor web
            open_browser: Se True, abre o navegador automaticamente

        Returns:
            Porta onde o dashboard está sendo executado
        """
        try:
            import dash
            import dash_bootstrap_components as dbc
            from dash import dcc, html
            from dash.dependencies import Input, Output, State
        except ImportError:
            logger.error("Dash não encontrado. Instale com: pip install dash dash-bootstrap-components")
            return 0

        # Carregar dados de detecções
        detection_data = self._load_detection_data(results_dir)
        if not detection_data:
            logger.error(f"Não foi possível carregar dados de detecção de: {results_dir}")
            return 0

        # Extrair informações para o dashboard
        images = list(detection_data.keys())

        # Criar dataframe com todas as detecções
        rows = []
        for image_name, detections in detection_data.items():
            for det in detections:
                # Verificar se a detecção está no formato esperado
                if not isinstance(det, dict):
                    continue

                # Criar um dicionário base para a linha
                row = {
                    "image": image_name,
                    "class": det.get("class", 0),
                    "class_name": det.get("class_name", f"Class {det.get('class', 0)}"),
                    "confidence": det.get("confidence", det.get("conf", 0)),
                }

                # Adicionar informações de bbox
                if "bbox" in det:
                    bbox = det["bbox"]
                    # Verificar se bbox é uma lista/tuple e tem pelo menos 4 elementos
                    if isinstance(bbox, (list, tuple)) and len(bbox) >= 4:
                        # Determinar o formato do bbox (pode ser [x1,y1,x2,y2] ou [x,y,w,h])
                        if len(bbox) == 4:
                            # Se todos os valores são < 1.0, provavelmente são coordenadas normalizadas
                            if all(isinstance(v, (int, float)) and v <= 1.0 for v in bbox):
                                # Coordenadas normalizadas, estimar valores absolutos para visualização
                                row["x1"] = bbox[0]
                                row["y1"] = bbox[1]
                                row["x2"] = bbox[0] + bbox[2] if len(bbox) == 4 else bbox[2]
                                row["y2"] = bbox[1] + bbox[3] if len(bbox) == 4 else bbox[3]
                            else:
                                # Coordenadas absolutas
                                row["x1"] = bbox[0]
                                row["y1"] = bbox[1]
                                row["x2"] = bbox[2] if len(bbox) == 4 and bbox[2] > bbox[0] else bbox[0] + bbox[2]
                                row["y2"] = bbox[3] if len(bbox) == 4 and bbox[3] > bbox[1] else bbox[1] + bbox[3]

                            # Calcular largura e altura
                            row["width"] = row["x2"] - row["x1"]
                            row["height"] = row["y2"] - row["y1"]
                            row["area"] = row["width"] * row["height"]

                rows.append(row)

        # Verificar se temos dados suficientes para o dashboard
        if not rows:
            logger.warning("Não há detecções para mostrar no dashboard")
            # Criar pelo menos uma linha para o dashboard funcionar
            rows.append({
                "image": images[0] if images else "exemplo.jpg",
                "class": 0,
                "class_name": "Sem detecções",
                "confidence": 0,
                "x1": 0, "y1": 0, "x2": 0, "y2": 0,
                "width": 0, "height": 0, "area": 0
            })

        # Criar DataFrame
        import pandas as pd
        df = pd.DataFrame(rows)

        # Limpar o DataFrame, tratando valores ausentes
        for col in df.columns:
            if pd.api.types.is_numeric_dtype(df[col]):
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

        # Obter classes únicas
        classes = sorted(df["class_name"].unique())

        # Criar aplicação Dash
        app = dash.Dash(__name__, external_stylesheets=[dbc.themes.FLATLY],
                        title="MicroDetect - Dashboard de Detecções")

        # Layout do dashboard
        app.layout = dbc.Container(
            [
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                html.H1("MicroDetect - Dashboard de Detecções", className="mb-4"),
                                html.Hr(),
                            ],
                            width=12,
                        )
                    ]
                ),
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                dbc.Card(
                                    [
                                        dbc.CardHeader("Estatísticas Gerais"),
                                        dbc.CardBody(
                                            [
                                                html.H3(f"Total de Imagens: {len(images)}"),
                                                html.H3(f"Total de Detecções: {len(df)}"),
                                                html.H3(f"Número de Classes: {len(classes)}"),
                                                html.H4(f"Confiança Média: {df['confidence'].mean():.4f}"),
                                            ]
                                        ),
                                    ],
                                    className="mb-4",
                                ),
                                dbc.Card(
                                    [
                                        dbc.CardHeader("Filtros"),
                                        dbc.CardBody(
                                            [
                                                html.Label("Limiar de Confiança:"),
                                                dcc.Slider(
                                                    id="confidence-slider",
                                                    min=0,
                                                    max=1,
                                                    step=0.05,
                                                    value=0.25,
                                                    marks={i / 10: str(i / 10) for i in range(0, 11, 1)},
                                                    className="mb-3",
                                                ),
                                                html.Label("Classes:"),
                                                dcc.Checklist(
                                                    id="class-checklist",
                                                    options=[{"label": c, "value": c} for c in classes],
                                                    value=classes,
                                                    inline=True,
                                                    className="mb-3",
                                                ),
                                                html.Label("Imagem:"),
                                                dcc.Dropdown(
                                                    id="image-dropdown",
                                                    options=[{"label": img, "value": img} for img in images],
                                                    value=images[0] if images else None,
                                                    clearable=False,
                                                    className="mb-3",
                                                ),
                                                dbc.Button(
                                                    "Atualizar Visualização",
                                                    id="update-button",
                                                    color="primary",
                                                    className="mt-2",
                                                ),
                                            ]
                                        ),
                                    ],
                                    className="mb-4",
                                ),
                            ],
                            width=4,
                        ),
                        dbc.Col(
                            [
                                dbc.Tabs(
                                    [
                                        dbc.Tab([dcc.Graph(id="detections-by-class")], label="Detecções por Classe"),
                                        dbc.Tab([dcc.Graph(id="confidence-histogram")],
                                                label="Histograma de Confiança"),
                                        dbc.Tab([dcc.Graph(id="size-scatter")], label="Tamanho x Confiança"),
                                    ]
                                ),
                                html.Div(id="filtered-stats", className="mt-4"),
                            ],
                            width=8,
                        ),
                    ]
                ),
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                html.H3("Detalhes da Imagem", className="mb-3"),
                                html.Div(id="image-display"),
                                html.Div(id="image-detections", className="mt-3"),
                            ],
                            width=12,
                        )
                    ]
                ),
            ],
            fluid=True,
        )

        # Callback para atualizar gráficos
        @app.callback(
            [
                Output("detections-by-class", "figure"),
                Output("confidence-histogram", "figure"),
                Output("size-scatter", "figure"),
                Output("filtered-stats", "children"),
                Output("image-detections", "children"),
            ],
            [Input("update-button", "n_clicks")],
            [State("confidence-slider", "value"), State("class-checklist", "value"), State("image-dropdown", "value")],
        )
        def update_graphs(n_clicks, conf_threshold, selected_classes, selected_image):
            import plotly.express as px
            import plotly.graph_objects as go

            # Filtrar DataFrame
            filtered_df = df[(df["confidence"] >= conf_threshold) & (df["class_name"].isin(selected_classes))]

            # Criar visualizações mesmo se o DataFrame estiver vazio
            if filtered_df.empty:
                empty_msg = "Nenhuma detecção encontrada com os filtros aplicados"

                # Gráfico vazio para detecções por classe
                fig1 = go.Figure()
                fig1.update_layout(
                    title="Número de Detecções por Classe",
                    annotations=[{"text": empty_msg, "showarrow": False, "font": {"size": 16}}]
                )

                # Gráfico vazio para histograma de confiança
                fig2 = go.Figure()
                fig2.update_layout(
                    title="Distribuição de Confiança por Classe",
                    annotations=[{"text": empty_msg, "showarrow": False, "font": {"size": 16}}]
                )

                # Gráfico vazio para scatter plot
                fig3 = go.Figure()
                fig3.update_layout(
                    title="Relação entre Tamanho e Confiança",
                    annotations=[{"text": empty_msg, "showarrow": False, "font": {"size": 16}}]
                )

                # Estatísticas vazias
                stats = dbc.Card(
                    [
                        dbc.CardHeader("Estatísticas Filtradas"),
                        dbc.CardBody([html.H4("Nenhuma detecção com os filtros atuais")]),
                    ]
                )

                # Detalhes da imagem vazios
                image_details = [
                    html.H4(f"Detecções em: {selected_image}"),
                    html.P("Nenhuma detecção com os filtros atuais")
                ]

                return fig1, fig2, fig3, stats, image_details

            # Gráfico 1: Detecções por Classe
            try:
                fig1 = px.bar(
                    filtered_df["class_name"].value_counts().reset_index(),
                    x="index",
                    y="class_name",
                    color="index",
                    labels={"index": "Classe", "class_name": "Contagem"},
                    title="Número de Detecções por Classe",
                )
            except Exception as e:
                fig1 = go.Figure()
                fig1.update_layout(
                    title="Erro ao gerar gráfico de detecções por classe",
                    annotations=[{"text": str(e), "showarrow": False}]
                )

            # Gráfico 2: Histograma de Confiança
            try:
                fig2 = px.histogram(
                    filtered_df,
                    x="confidence",
                    color="class_name",
                    nbins=20,
                    title="Distribuição de Confiança por Classe",
                    labels={"confidence": "Confiança", "count": "Contagem"},
                )
            except Exception as e:
                fig2 = go.Figure()
                fig2.update_layout(
                    title="Erro ao gerar histograma de confiança",
                    annotations=[{"text": str(e), "showarrow": False}]
                )

            # Gráfico 3: Scatter Plot de Tamanho vs Confiança
            try:
                if "area" in filtered_df.columns and not filtered_df["area"].isna().all():
                    fig3 = px.scatter(
                        filtered_df,
                        x="area",
                        y="confidence",
                        color="class_name",
                        size="area",
                        hover_data=["image", "class_name"],
                        title="Relação entre Tamanho e Confiança",
                        labels={"area": "Área", "confidence": "Confiança"},
                    )
                else:
                    fig3 = go.Figure()
                    fig3.update_layout(title="Dados de área não disponíveis")
            except Exception as e:
                fig3 = go.Figure()
                fig3.update_layout(
                    title="Erro ao gerar gráfico de tamanho vs confiança",
                    annotations=[{"text": str(e), "showarrow": False}]
                )

            # Estatísticas filtradas
            try:
                stats = dbc.Card(
                    [
                        dbc.CardHeader("Estatísticas Filtradas"),
                        dbc.CardBody(
                            [
                                html.H4(f"Detecções: {len(filtered_df)}"),
                                html.H4(f"Confiança Média: {filtered_df['confidence'].mean():.4f}"),
                            ]
                        ),
                    ]
                )
            except Exception as e:
                stats = dbc.Card(
                    [
                        dbc.CardHeader("Estatísticas Filtradas"),
                        dbc.CardBody([html.H4(f"Erro ao calcular estatísticas: {str(e)}")])
                    ]
                )

            # Detalhes da imagem selecionada
            try:
                image_dets = filtered_df[filtered_df["image"] == selected_image]

                if not image_dets.empty:
                    display_cols = ["class_name", "confidence"]
                    if "area" in image_dets.columns:
                        display_cols.append("area")

                    table = dbc.Table.from_dataframe(
                        image_dets[display_cols].round(4),
                        striped=True,
                        bordered=True,
                        hover=True,
                        responsive=True,
                        className="mt-3",
                    )
                else:
                    table = html.P("Nenhuma detecção para esta imagem com os filtros atuais.")

                image_details = [
                    html.H4(f"Detecções em: {selected_image}"),
                    html.P(f"Total: {len(image_dets)} detecções"),
                    table
                ]
            except Exception as e:
                image_details = [
                    html.H4(f"Detecções em: {selected_image}"),
                    html.P(f"Erro ao processar detecções: {str(e)}")
                ]

            return fig1, fig2, fig3, stats, image_details

        # Iniciar servidor
        def open_browser_tab():
            if open_browser:
                try:
                    # Verificar se estamos em ambiente WSL
                    is_wsl = False
                    try:
                        with open('/proc/version', 'r') as f:
                            if 'microsoft' in f.read().lower():
                                is_wsl = True
                    except:
                        pass

                    if is_wsl:
                        # Em WSL, tentar abrir no Windows
                        import subprocess
                        subprocess.run(['powershell.exe', 'start', f'http://localhost:{port}'],
                                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    else:
                        # Em outros ambientes, usar webbrowser
                        import webbrowser
                        webbrowser.open_new_tab(f"http://localhost:{port}")
                except Exception as e:
                    logger.warning(f"Não foi possível abrir o navegador automaticamente: {str(e)}")
                    logger.info(f"Dashboard disponível em: http://localhost:{port}")

        # Versão atualizada para compatibilidade com Dash mais recente
        try:
            threading.Timer(1, open_browser_tab).start()
            # Verificamos qual método existe na versão atual do Dash
            if hasattr(app, 'run') and callable(app.run):
                # Nova API do Dash
                app.run(debug=False, port=port, host="0.0.0.0")
            else:
                # API legada do Dash
                app.run_server(debug=False, port=port, host="0.0.0.0")
            return port
        except Exception as e:
            logger.error(f"Erro ao iniciar o dashboard: {str(e)}")
            logger.info(
                "Para visualizar dashboards, instale dash e dash-bootstrap-components: pip install dash dash-bootstrap-components")
            return 0

    def _load_detection_data(self, results_dir: str) -> Dict:
        """
        Carrega dados de detecção de arquivos no diretório de resultados.

        Args:
            results_dir: Diretório contendo resultados de detecção

        Returns:
            Dicionário com dados de detecção
        """
        import os
        import glob
        import json

        # Procurar por arquivos JSON que possam conter resultados de detecção
        json_files = glob.glob(os.path.join(results_dir, "*.json"))

        # Primeiro, verificar arquivos que tenham nomes que sugerem resultados de detecção
        detection_files = [f for f in json_files if
                           any(term in f.lower() for term in ['detect', 'result', 'detection'])]
        if not detection_files:
            detection_files = json_files  # Se não encontrar nomes específicos, usar todos os JSONs

        # Tentar carregar cada arquivo JSON e verificar se tem o formato esperado
        for json_file in detection_files:
            try:
                with open(json_file, 'r') as f:
                    data = json.load(f)

                    # Verificar se é um dicionário (formato esperado para detecções)
                    if isinstance(data, dict):
                        # Verificar se parece um resultado de detecção (keys são nomes de arquivos
                        # e values são listas de detecções)
                        if data and all(isinstance(v, list) for v in data.values()):
                            # Assumir que temos resultados válidos
                            logger.info(f"Usando dados de detecção de: {json_file}")
                            return data

            except Exception as e:
                logger.warning(f"Erro ao carregar {json_file}: {str(e)}")

        # Se não encontrou resultados, criar dados mínimos para evitar erros
        logger.warning("Não foi possível encontrar resultados de detecção. Criando dados de exemplo.")
        # Criar alguns dados mínimos de exemplo para o dashboard funcionar
        return {
            "exemplo.jpg": [
                {
                    "bbox": [100, 100, 200, 200],
                    "class": 0,
                    "class_name": "exemplo",
                    "confidence": 0.9
                }
            ]
        }

    def create_model_comparison_dashboard(
            self, comparison_results: Dict[str, Dict], port: int = 8051, open_browser: bool = True
    ) -> int:
        """
        Cria um dashboard interativo para comparar diferentes modelos.

        Args:
            comparison_results: Dicionário com resultados de comparação de modelos
            port: Porta para o servidor web
            open_browser: Se True, abre o navegador automaticamente

        Returns:
            Porta onde o dashboard está sendo executado
        """
        try:
            import dash
            import dash_bootstrap_components as dbc
            from dash import dcc, html
            from dash.dependencies import Input, Output
            import pandas as pd
            import re
        except ImportError:
            logger.error("Dash não encontrado. Instale com: pip install dash dash-bootstrap-components")
            return 0

        # Função para pré-processar os dados para garantir que todos os campos necessários existam
        def preprocess_data(results):
            processed_rows = []

            # Valores padrão para campos obrigatórios
            default_metrics = {
                "mAP50": 0.0,
                "mAP50-95": 0.0,
                "recall": 0.0,
                "precision": 0.0,
                "f1-score": 0.0,
            }

            default_speed = {
                "fps": 0.0,
                "latencia_ms": 0.0,
            }

            for model_name, model_data in results.items():
                # Extrair informações da taxa de aprendizado do nome do modelo
                lr_value = "unknown"
                try:
                    lr_match = re.search(r'lr([0-9.]+)', model_name.lower())
                    if lr_match:
                        lr_value = lr_match.group(1)
                except:
                    pass

                # Criar uma linha base com valores padrão
                row = {
                    "model": model_name,
                    # Usar a taxa de aprendizado extraída para a categoria se disponível
                    "category": lr_value if lr_value != "unknown" else model_data.get("tamanho", "unknown"),
                    "size_mb": model_data.get("tamanho_arquivo", 0.0),
                }

                # Adicionar métricas, usando valores padrão se necessário
                metrics = model_data.get("metricas", default_metrics)
                for metric_name, default_value in default_metrics.items():
                    row[metric_name] = metrics.get(metric_name, default_value)

                # Adicionar dados de velocidade, usando valores padrão se necessário
                speed = model_data.get("velocidade", default_speed)
                for speed_metric, default_value in default_speed.items():
                    row[speed_metric] = speed.get(speed_metric, default_value)

                # Adicionar quaisquer outros campos presentes nos dados
                for key, value in model_data.items():
                    if key not in ["tamanho", "tamanho_arquivo", "metricas", "velocidade"]:
                        row[key] = value

                processed_rows.append(row)

            return processed_rows

        # Pré-processar os dados para garantir consistência
        rows = preprocess_data(comparison_results)

        # Criar DataFrame
        df = pd.DataFrame(rows)

        # Verificar se há dados suficientes para criar o dashboard
        if len(df) == 0:
            logger.error("Sem dados suficientes para criar dashboard")
            return 0

        # Garantir que todas as colunas numéricas tenham valores numéricos válidos
        numeric_columns = ["size_mb", "mAP50", "mAP50-95", "recall", "precision", "f1-score", "fps", "latencia_ms"]
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)

        # Criar aplicação Dash
        app = dash.Dash(__name__, external_stylesheets=[dbc.themes.FLATLY], title="MicroDetect - Comparação de Modelos")

        # Layout do dashboard
        app.layout = dbc.Container(
            [
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                html.H1("MicroDetect - Comparação de Modelos", className="mb-4"),
                                html.Hr(),
                            ],
                            width=12,
                        )
                    ]
                ),
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                dbc.Card(
                                    [
                                        dbc.CardHeader("Modelos Comparados"),
                                        dbc.CardBody(
                                            [
                                                html.H4(f"Total de Modelos: {len(df)}"),
                                                dbc.ListGroup(
                                                    [
                                                        dbc.ListGroupItem(
                                                            f"{row['model']} (Categoria: {row['category']})",
                                                            color=["primary", "success", "info", "warning", "danger"][
                                                                i % 5],
                                                        )
                                                        for i, (_, row) in enumerate(df.iterrows())
                                                    ]
                                                ),
                                            ]
                                        ),
                                    ],
                                    className="mb-4",
                                ),
                                dbc.Card(
                                    [
                                        dbc.CardHeader("Filtros"),
                                        dbc.CardBody(
                                            [
                                                html.Label("Métrica para Visualização:"),
                                                dcc.Dropdown(
                                                    id="metric-dropdown",
                                                    options=[
                                                        {"label": "Precisão (mAP50)", "value": "mAP50"},
                                                        {"label": "Precisão (mAP50-95)", "value": "mAP50-95"},
                                                        {"label": "Recall", "value": "recall"},
                                                        {"label": "Precisão", "value": "precision"},
                                                        {"label": "F1-Score", "value": "f1-score"},
                                                        {"label": "FPS", "value": "fps"},
                                                        {"label": "Latência (ms)", "value": "latencia_ms"},
                                                    ],
                                                    value="mAP50",
                                                    clearable=False,
                                                    className="mb-3",
                                                ),
                                                html.Label("Visualização:"),
                                                dcc.RadioItems(
                                                    id="chart-type",
                                                    options=[
                                                        {"label": "Gráfico de Barras", "value": "bar"},
                                                        {"label": "Gráfico de Linha", "value": "line"},
                                                        {"label": "Gráfico de Radar", "value": "radar"},
                                                    ],
                                                    value="bar",
                                                    inline=True,
                                                    className="mb-3",
                                                ),
                                            ]
                                        ),
                                    ],
                                    className="mb-4",
                                ),
                            ],
                            width=4,
                        ),
                        dbc.Col(
                            [
                                dbc.Tabs(
                                    [
                                        dbc.Tab([dcc.Graph(id="metric-comparison")], label="Comparação por Métrica"),
                                        dbc.Tab([dcc.Graph(id="tradeoff-plot")], label="Precisão vs. Velocidade"),
                                        dbc.Tab([dcc.Graph(id="size-comparison")], label="Tamanho de Modelo"),
                                    ]
                                ),
                                html.Div(id="comparison-stats", className="mt-4"),
                            ],
                            width=8,
                        ),
                    ]
                ),
                dbc.Row(
                    [dbc.Col([html.H3("Tabela Comparativa", className="mb-3"), html.Div(id="comparison-table")],
                             width=12)]
                ),
            ],
            fluid=True,
        )

        # Definir o callback para atualizar os gráficos
        @app.callback(
            [
                Output("metric-comparison", "figure"),
                Output("tradeoff-plot", "figure"),
                Output("size-comparison", "figure"),
                Output("comparison-stats", "children"),
                Output("comparison-table", "children"),
            ],
            [Input("metric-dropdown", "value"), Input("chart-type", "value")],
        )
        def update_graphs(selected_metric, chart_type):
            import plotly.express as px
            import plotly.graph_objects as go
            import numpy as np

            # Garantir que temos dados para trabalhar
            if df.empty or selected_metric not in df.columns:
                # Criar gráficos vazios com mensagens informativas
                fig1 = go.Figure()
                fig1.update_layout(
                    title="Sem dados disponíveis para visualização",
                    annotations=[{
                        "text": "Dados insuficientes ou métrica não disponível",
                        "showarrow": False,
                        "font": {"size": 16}
                    }]
                )

                fig2 = go.Figure()
                fig2.update_layout(title="Sem dados para gráfico de trade-off")

                fig3 = go.Figure()
                fig3.update_layout(title="Sem dados para gráfico de tamanho")

                # Mostrar estatísticas de fallback
                stats = dbc.Card(
                    [
                        dbc.CardHeader("Estatísticas Comparativas"),
                        dbc.CardBody([html.H4("Dados insuficientes para análise")])
                    ]
                )

                # Mostrar tabela vazia
                table = html.Div("Sem dados disponíveis para exibição")

                return fig1, fig2, fig3, stats, table

            # Garantir que todos os valores são válidos antes de plotar
            plot_df = df.copy()
            for col in [selected_metric, 'fps', 'size_mb']:
                if col in plot_df.columns:
                    plot_df[col] = pd.to_numeric(plot_df[col], errors='coerce').fillna(0)

            # Garantir que temos categorias para trabalhar
            if 'category' not in plot_df.columns or plot_df['category'].isna().all():
                plot_df['category'] = 'default'

            # Garantir que temos o modelo para trabalhar
            if 'model' not in plot_df.columns or plot_df['model'].isna().all():
                plot_df['model'] = [f"Modelo {i + 1}" for i in range(len(plot_df))]

            # ===== GRÁFICO 1: Comparação por métrica =====
            try:
                if chart_type == "bar":
                    fig1 = px.bar(
                        plot_df,
                        x="model",
                        y=selected_metric,
                        color="category",
                        title=f"Comparação de {selected_metric}",
                        labels={"model": "Modelo", selected_metric: selected_metric.upper()},
                    )
                    # Adicionar valores numéricos nas barras
                    for i, row in enumerate(plot_df.itertuples()):
                        value = getattr(row, selected_metric, 0)
                        fig1.add_annotation(
                            x=row.model,
                            y=value,
                            text=f"{value:.4f}",
                            showarrow=False,
                            yshift=10
                        )
                elif chart_type == "line":
                    fig1 = px.line(
                        plot_df,
                        x="model",
                        y=selected_metric,
                        color="category",
                        markers=True,
                        title=f"Comparação de {selected_metric}",
                        labels={"model": "Modelo", selected_metric: selected_metric.upper()},
                    )
                else:  # radar
                    fig1 = go.Figure()

                    # Certificar-se de que temos dados para plot polar
                    if len(plot_df) > 1:  # Precisamos de pelo menos 2 pontos para um gráfico de radar
                        for category in plot_df["category"].unique():
                            category_df = plot_df[plot_df["category"] == category]
                            fig1.add_trace(
                                go.Scatterpolar(
                                    r=category_df[selected_metric],
                                    theta=category_df["model"],
                                    fill="toself",
                                    name=category
                                )
                            )

                        # Ajustar o range para o valor máximo + 10%
                        max_value = plot_df[selected_metric].max()
                        if max_value > 0:
                            range_max = max_value * 1.1
                        else:
                            range_max = 1.0  # Valor padrão se não houver valores positivos

                        fig1.update_layout(
                            polar=dict(radialaxis=dict(visible=True, range=[0, range_max])),
                            title=f"Comparação de {selected_metric}",
                        )
                    else:
                        # Se não temos dados suficientes para um gráfico radar
                        fig1.update_layout(
                            title=f"Comparação de {selected_metric} (Dados insuficientes para radar)",
                            annotations=[{"text": "Precisa de pelo menos 2 modelos", "showarrow": False}]
                        )
            except Exception as e:
                # Fallback em caso de erro
                fig1 = go.Figure()
                fig1.update_layout(
                    title=f"Erro ao gerar gráfico para {selected_metric}",
                    annotations=[{"text": str(e), "showarrow": False}]
                )

            # ===== GRÁFICO 2: Precisão vs. Velocidade =====
            try:
                if "mAP50" in plot_df.columns and "fps" in plot_df.columns:
                    # Verificar se temos valores válidos para plotar
                    valid_data = (plot_df["mAP50"] > 0) | (plot_df["fps"] > 0)
                    if valid_data.any():
                        fig2 = px.scatter(
                            plot_df[valid_data],
                            x="fps",
                            y="mAP50",
                            color="category",
                            size="size_mb",
                            hover_data=["model", "category"],
                            title="Trade-off: Precisão vs. Velocidade",
                            labels={"fps": "FPS", "mAP50": "mAP50"},
                            text="model",
                        )
                        fig2.update_traces(textposition="top right")
                    else:
                        # Criar um gráfico vazio com mensagem explicativa
                        fig2 = go.Figure()
                        fig2.update_layout(
                            title="Trade-off: Precisão vs. Velocidade (Dados indisponíveis)",
                            annotations=[{"text": "Sem valores válidos para mostrar", "showarrow": False}]
                        )
                else:
                    fig2 = go.Figure()
                    fig2.update_layout(
                        title="Dados insuficientes para gráfico de trade-off",
                        annotations=[{"text": "Precisa de valores de mAP50 e FPS", "showarrow": False}]
                    )
            except Exception as e:
                # Fallback em caso de erro
                fig2 = go.Figure()
                fig2.update_layout(
                    title="Erro ao gerar gráfico de trade-off",
                    annotations=[{"text": str(e), "showarrow": False}]
                )

            # ===== GRÁFICO 3: Tamanho do Modelo =====
            try:
                if "size_mb" in plot_df.columns and not plot_df["size_mb"].isna().all():
                    fig3 = px.bar(
                        plot_df,
                        x="model",
                        y="size_mb",
                        color="category",
                        title="Tamanho do Modelo (MB)",
                        labels={"model": "Modelo", "size_mb": "Tamanho (MB)"},
                    )
                    # Adicionar valores nas barras
                    for i, row in enumerate(plot_df.itertuples()):
                        fig3.add_annotation(
                            x=row.model,
                            y=row.size_mb,
                            text=f"{row.size_mb:.1f} MB",
                            showarrow=False,
                            yshift=10
                        )
                else:
                    fig3 = go.Figure()
                    fig3.update_layout(
                        title="Dados de tamanho indisponíveis",
                        annotations=[{"text": "Sem informações de tamanho disponíveis", "showarrow": False}]
                    )
            except Exception as e:
                # Fallback em caso de erro
                fig3 = go.Figure()
                fig3.update_layout(
                    title="Erro ao gerar gráfico de tamanho",
                    annotations=[{"text": str(e), "showarrow": False}]
                )

            # ===== ESTATÍSTICAS =====
            try:
                # Encontrar melhor modelo para métrica selecionada
                best_model = "N/A"
                best_value = 0
                if selected_metric in plot_df.columns and not plot_df[selected_metric].isna().all():
                    max_idx = plot_df[selected_metric].idxmax()
                    if not pd.isna(max_idx):
                        best_model = plot_df.loc[max_idx, 'model']
                        best_value = plot_df.loc[max_idx, selected_metric]

                # Encontrar modelo mais rápido
                fastest_model = "N/A"
                fastest_fps = 0
                if 'fps' in plot_df.columns and not plot_df['fps'].isna().all():
                    max_idx = plot_df['fps'].idxmax()
                    if not pd.isna(max_idx):
                        fastest_model = plot_df.loc[max_idx, 'model']
                        fastest_fps = plot_df.loc[max_idx, 'fps']

                # Criar estatísticas
                stats = dbc.Card(
                    [
                        dbc.CardHeader("Estatísticas Comparativas"),
                        dbc.CardBody(
                            [
                                html.H4(f"Melhor modelo para {selected_metric}: {best_model}"),
                                html.H4(f"Valor: {best_value:.4f}" if isinstance(best_value, (
                                int, float)) else f"Valor: {best_value}"),
                                html.H4(f"Modelo mais rápido: {fastest_model}"),
                                html.H4(
                                    f"FPS: {fastest_fps:.1f}" if isinstance(fastest_fps, (int, float)) else "FPS: N/A"),
                            ]
                        ),
                    ]
                )
            except Exception as e:
                # Fallback em caso de erro
                stats = dbc.Card(
                    [
                        dbc.CardHeader("Estatísticas Comparativas"),
                        dbc.CardBody([html.H4(f"Erro ao calcular estatísticas: {str(e)}")])
                    ]
                )

            # ===== TABELA COMPARATIVA =====
            try:
                # Preparar colunas para a tabela
                display_cols = []
                if "model" in plot_df.columns:
                    display_cols.append("model")
                if "category" in plot_df.columns:
                    display_cols.append("category")
                if "size_mb" in plot_df.columns:
                    display_cols.append("size_mb")

                # Adicionar outras métricas
                metric_cols = [col for col in plot_df.columns if col not in ["model", "category", "size_mb"]]
                display_cols.extend(metric_cols)

                # Criar tabela formatada
                if display_cols:
                    # Arredondar valores numéricos para melhor visualização
                    table_df = plot_df[display_cols].copy()
                    for col in table_df.columns:
                        if pd.api.types.is_numeric_dtype(table_df[col]):
                            table_df[col] = table_df[col].round(4)

                    table = dbc.Table.from_dataframe(
                        table_df,
                        striped=True,
                        bordered=True,
                        hover=True,
                        responsive=True,
                        className="mt-3"
                    )
                else:
                    table = html.Div("Não há dados para exibir na tabela")
            except Exception as e:
                # Fallback em caso de erro
                table = html.Div(f"Erro ao gerar tabela: {str(e)}")

            return fig1, fig2, fig3, stats, table

        # Iniciar servidor
        def open_browser_tab():
            if open_browser:
                try:
                    webbrowser.open_new_tab(f"http://localhost:{port}")
                except Exception as e:
                    logger.warning(f"Não foi possível abrir o navegador automaticamente: {str(e)}")
                    logger.info(f"Dashboard disponível em: http://localhost:{port}")

        # Versão atualizada para compatibilidade com Dash mais recente
        try:
            threading.Timer(1, open_browser_tab).start()
            # Verificamos qual método existe na versão atual do Dash
            if hasattr(app, 'run') and callable(app.run):
                # Nova API do Dash
                app.run(debug=False, port=port, host="0.0.0.0")
            else:
                # API legada do Dash
                app.run_server(debug=False, port=port, host="0.0.0.0")
            return port
        except Exception as e:
            logger.error(f"Erro ao iniciar o dashboard: {str(e)}")
            logger.info(
                "Para visualizar dashboards, instale dash e dash-bootstrap-components: pip install dash dash-bootstrap-components")
            return 0

    def create_metrics_dashboard(self, metrics_file: str = None, port: int = 8051, open_browser: bool = True) -> int:
        """
        Cria um dashboard interativo para visualizar métricas de avaliação.

        Args:
            metrics_file: Caminho para o arquivo de métricas (opcional)
            port: Porta para o servidor web
            open_browser: Se True, abre o navegador automaticamente

        Returns:
            Porta onde o dashboard está sendo executado
        """
        try:
            import dash
            import dash_bootstrap_components as dbc
            from dash import dcc, html
            from dash.dependencies import Input, Output
        except ImportError:
            logger.error("Dash não encontrado. Instale com: pip install dash dash-bootstrap-components")
            return 0

        # Carregar dados de métricas
        metrics_data = self._load_metrics_data(metrics_file)

        # Criar aplicação Dash
        app = dash.Dash(__name__, external_stylesheets=[dbc.themes.FLATLY], title="MicroDetect - Dashboard de Métricas")

        # Layout do dashboard
        app.layout = dbc.Container(
            [
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                html.H1("MicroDetect - Dashboard de Métricas", className="mb-4"),
                                html.Hr(),
                            ],
                            width=12,
                        )
                    ]
                ),
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                dbc.Card(
                                    [
                                        dbc.CardHeader("Informações Gerais"),
                                        dbc.CardBody(
                                            [
                                                html.H4("Métricas de Avaliação de Modelo"),
                                                html.P(
                                                    "Este dashboard apresenta uma visualização das métricas de avaliação do modelo."),
                                                html.Hr(),
                                                html.H5("Modelo:"),
                                                html.P(
                                                    metrics_data.get("model_info", {}).get("name", "Não especificado")),
                                                html.H5("Data da Avaliação:"),
                                                html.P(
                                                    metrics_data.get("model_info", {}).get("date", "Não especificada")),
                                            ]
                                        ),
                                    ],
                                    className="mb-4",
                                ),
                                dbc.Card(
                                    [
                                        dbc.CardHeader("Métricas Gerais"),
                                        dbc.CardBody(
                                            [
                                                html.Div(
                                                    [
                                                        html.H5(f"{metric}:"),
                                                        html.P(f"{value:.4f}" if isinstance(value, (
                                                        int, float)) else f"{value}")
                                                    ]
                                                )
                                                for metric, value in metrics_data.get("general_metrics", {}).items()
                                            ]
                                        ),
                                    ],
                                    className="mb-4",
                                ),
                            ],
                            width=4,
                        ),
                        dbc.Col(
                            [
                                dbc.Tabs(
                                    [
                                        dbc.Tab([dcc.Graph(id="metrics-overview")], label="Visão Geral"),
                                        dbc.Tab([dcc.Graph(id="class-metrics")], label="Métricas por Classe"),
                                        dbc.Tab([dcc.Graph(id="metrics-comparison")], label="Comparação"),
                                    ]
                                ),
                            ],
                            width=8,
                        ),
                    ]
                ),
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                html.H3("Métricas por Classe", className="mb-3"),
                                html.Div(id="class-metrics-table"),
                            ],
                            width=12,
                        )
                    ]
                ),
            ],
            fluid=True,
        )

        # Callback para preencher os gráficos
        @app.callback(
            [
                Output("metrics-overview", "figure"),
                Output("class-metrics", "figure"),
                Output("metrics-comparison", "figure"),
                Output("class-metrics-table", "children"),
            ],
            [Input("metrics-overview", "figure")]  # Gatilho de inicialização
        )
        def update_metrics_figures(trigger):
            import plotly.express as px
            import plotly.graph_objects as go
            import pandas as pd
            import numpy as np

            # Gráfico 1: Visão geral das métricas
            try:
                # Converter métricas gerais para DataFrame
                general_df = pd.DataFrame([
                    {"Métrica": metric, "Valor": value}
                    for metric, value in metrics_data.get("general_metrics", {}).items()
                    if isinstance(value, (int, float))  # Filtrar apenas valores numéricos
                ])

                if not general_df.empty:
                    fig1 = px.bar(
                        general_df,
                        x="Métrica",
                        y="Valor",
                        title="Visão Geral das Métricas",
                        color="Métrica",
                    )

                    # Ajustar range do eixo y para começar em 0 e terminar pouco acima do valor máximo
                    max_val = general_df["Valor"].max()
                    fig1.update_yaxes(range=[0, max_val * 1.1])

                    # Adicionar valores nas barras
                    for i, row in enumerate(general_df.itertuples()):
                        fig1.add_annotation(
                            x=row.Métrica,
                            y=row.Valor,
                            text=f"{row.Valor:.4f}",
                            showarrow=False,
                            yshift=10
                        )
                else:
                    fig1 = go.Figure()
                    fig1.update_layout(
                        title="Métricas Gerais",
                        annotations=[{"text": "Dados não disponíveis", "showarrow": False, "font": {"size": 16}}]
                    )
            except Exception as e:
                fig1 = go.Figure()
                fig1.update_layout(
                    title="Erro ao gerar visão geral das métricas",
                    annotations=[{"text": str(e), "showarrow": False}]
                )

            # Gráfico 2: Métricas por classe
            try:
                # Converter métricas por classe para DataFrame
                class_metrics = metrics_data.get("class_metrics", [])

                if class_metrics:
                    # Identificar métricas disponíveis (excluindo 'Classe')
                    # As colunas válidas são aquelas que contêm valores numéricos
                    metric_cols = []
                    for metric in class_metrics[0].keys():
                        if metric != "Classe":
                            # Verificar se pelo menos um valor para esta métrica é numérico
                            if any(isinstance(class_data.get(metric), (int, float)) for class_data in class_metrics):
                                metric_cols.append(metric)

                    # Criar um DataFrame com uma linha por classe-métrica combinação
                    rows = []
                    for class_data in class_metrics:
                        class_name = class_data.get("Classe", "Desconhecido")
                        for metric in metric_cols:
                            value = class_data.get(metric)
                            if isinstance(value, (int, float)):
                                rows.append({
                                    "Classe": class_name,
                                    "Métrica": metric,
                                    "Valor": value
                                })

                    class_df = pd.DataFrame(rows)

                    if not class_df.empty:
                        fig2 = px.bar(
                            class_df,
                            x="Classe",
                            y="Valor",
                            color="Métrica",
                            barmode="group",
                            title="Métricas por Classe",
                        )

                        # Ajustar range do eixo y para começar em 0 e terminar pouco acima do valor máximo
                        max_val = class_df["Valor"].max()
                        fig2.update_yaxes(range=[0, max_val * 1.1])
                    else:
                        fig2 = go.Figure()
                        fig2.update_layout(
                            title="Métricas por Classe",
                            annotations=[{"text": "Dados não disponíveis", "showarrow": False, "font": {"size": 16}}]
                        )
                else:
                    fig2 = go.Figure()
                    fig2.update_layout(
                        title="Métricas por Classe",
                        annotations=[{"text": "Dados não disponíveis", "showarrow": False, "font": {"size": 16}}]
                    )
            except Exception as e:
                fig2 = go.Figure()
                fig2.update_layout(
                    title="Erro ao gerar métricas por classe",
                    annotations=[{"text": str(e), "showarrow": False}]
                )

            # Gráfico 3: Comparação do modelo com referências (opcional)
            try:
                # Tentar extrair informações de comparação, se disponíveis
                comparison_data = metrics_data.get("comparison", {})

                if comparison_data:
                    # Converter para DataFrame
                    comparison_df = pd.DataFrame([
                        {"Modelo": modelo, "Métrica": metrica, "Valor": valor}
                        for modelo, metricas in comparison_data.items()
                        for metrica, valor in metricas.items()
                        if isinstance(valor, (int, float))
                    ])

                    if not comparison_df.empty:
                        fig3 = px.line(
                            comparison_df,
                            x="Modelo",
                            y="Valor",
                            color="Métrica",
                            markers=True,
                            title="Comparação com Outros Modelos",
                        )
                    else:
                        fig3 = go.Figure()
                        fig3.update_layout(
                            title="Comparação com Outros Modelos",
                            annotations=[{"text": "Dados de comparação não disponíveis", "showarrow": False,
                                          "font": {"size": 16}}]
                        )
                else:
                    # Tentar criar um gráfico de radar com as métricas gerais
                    general_metrics = metrics_data.get("general_metrics", {})

                    if general_metrics:
                        # Filtrar apenas valores numéricos
                        metrics_values = {k: v for k, v in general_metrics.items() if isinstance(v, (int, float))}

                        if metrics_values:
                            # Criar gráfico de radar
                            fig3 = go.Figure()

                            fig3.add_trace(go.Scatterpolar(
                                r=list(metrics_values.values()),
                                theta=list(metrics_values.keys()),
                                fill='toself',
                                name='Métricas'
                            ))

                            fig3.update_layout(
                                polar=dict(
                                    radialaxis=dict(
                                        visible=True,
                                        range=[0, max(metrics_values.values()) * 1.1]
                                    )),
                                title="Representação de Métricas em Radar"
                            )
                        else:
                            fig3 = go.Figure()
                            fig3.update_layout(
                                title="Comparação de Métricas",
                                annotations=[
                                    {"text": "Dados não disponíveis", "showarrow": False, "font": {"size": 16}}]
                            )
                    else:
                        fig3 = go.Figure()
                        fig3.update_layout(
                            title="Comparação de Métricas",
                            annotations=[{"text": "Dados não disponíveis", "showarrow": False, "font": {"size": 16}}]
                        )
            except Exception as e:
                fig3 = go.Figure()
                fig3.update_layout(
                    title="Erro ao gerar comparação de métricas",
                    annotations=[{"text": str(e), "showarrow": False}]
                )

            # Tabela de métricas por classe
            try:
                class_metrics = metrics_data.get("class_metrics", [])

                if class_metrics:
                    class_df = pd.DataFrame(class_metrics)

                    # Formatar valores numéricos
                    for col in class_df.columns:
                        if col != "Classe" and pd.api.types.is_numeric_dtype(class_df[col]):
                            class_df[col] = class_df[col].round(4)

                    table = dbc.Table.from_dataframe(
                        class_df,
                        striped=True,
                        bordered=True,
                        hover=True,
                        responsive=True,
                        className="mt-3",
                    )
                else:
                    table = html.P("Não há dados de métricas por classe disponíveis.")
            except Exception as e:
                table = html.P(f"Erro ao gerar tabela de métricas por classe: {str(e)}")

            return fig1, fig2, fig3, table

        # Iniciar servidor
        def open_browser_tab():
            if open_browser:
                try:
                    # Verificar se estamos em ambiente WSL
                    is_wsl = False
                    try:
                        with open('/proc/version', 'r') as f:
                            if 'microsoft' in f.read().lower():
                                is_wsl = True
                    except:
                        pass

                    if is_wsl:
                        # Em WSL, tentar abrir no Windows
                        import subprocess
                        subprocess.run(['powershell.exe', 'start', f'http://localhost:{port}'],
                                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    else:
                        # Em outros ambientes, usar webbrowser
                        import webbrowser
                        webbrowser.open_new_tab(f"http://localhost:{port}")
                except Exception as e:
                    logger.warning(f"Não foi possível abrir o navegador automaticamente: {str(e)}")
                    logger.info(f"Dashboard disponível em: http://localhost:{port}")

        # Versão atualizada para compatibilidade com Dash mais recente
        try:
            threading.Timer(1, open_browser_tab).start()
            # Verificamos qual método existe na versão atual do Dash
            if hasattr(app, 'run') and callable(app.run):
                # Nova API do Dash
                app.run(debug=False, port=port, host="0.0.0.0")
            else:
                # API legada do Dash
                app.run_server(debug=False, port=port, host="0.0.0.0")
            return port
        except Exception as e:
            logger.error(f"Erro ao iniciar o dashboard: {str(e)}")
            logger.info(
                "Para visualizar dashboards, instale dash e dash-bootstrap-components: pip install dash dash-bootstrap-components")
            return 0

    def _load_metrics_data(self, metrics_file: str = None) -> Dict:
        """
        Carrega dados de métricas de um arquivo ou busca no diretório.

        Args:
            metrics_file: Caminho para o arquivo de métricas (opcional)

        Returns:
            Dicionário com dados de métricas formatados para o dashboard
        """
        import os
        import glob
        import json

        # Se um arquivo específico foi fornecido, tentar carregá-lo
        if metrics_file and os.path.exists(metrics_file):
            try:
                with open(metrics_file, 'r') as f:
                    data = json.load(f)

                    # Verificar se é um arquivo de métricas
                    if isinstance(data, dict) and ("metricas_gerais" in data or "metricas_por_classe" in data):
                        return self._format_metrics_data(data)
            except Exception as e:
                logger.warning(f"Erro ao carregar arquivo de métricas {metrics_file}: {str(e)}")

        # Se não foi fornecido um arquivo ou não conseguiu carregar, procurar no diretório
        if self.output_dir and os.path.exists(self.output_dir):
            # Procurar por arquivos JSON que possam conter métricas
            json_files = glob.glob(os.path.join(self.output_dir, "*.json"))

            # Filtrar por nomes sugestivos
            metrics_files = [f for f in json_files if
                             any(term in f.lower() for term in ['metric', 'avaliacao', 'relatorio'])]

            # Se não encontrou nomes específicos, usar todos os JSONs
            if not metrics_files:
                metrics_files = json_files

            # Tentar carregar cada arquivo
            for json_file in metrics_files:
                try:
                    with open(json_file, 'r') as f:
                        data = json.load(f)

                        # Verificar se parece um arquivo de métricas
                        if isinstance(data, dict) and ("metricas_gerais" in data or "metricas_por_classe" in data):
                            logger.info(f"Usando métricas de: {json_file}")
                            return self._format_metrics_data(data)
                except Exception as e:
                    logger.warning(f"Erro ao verificar {json_file}: {str(e)}")

        # Se não encontrou nada, criar dados de exemplo
        logger.warning("Criando dados de métricas de exemplo")
        return {
            "model_info": {
                "name": "Exemplo",
                "date": "2025-03-18"
            },
            "general_metrics": {
                "Precisão (mAP50)": 0.75,
                "Recall": 0.80,
                "F1-Score": 0.77
            },
            "class_metrics": [
                {
                    "Classe": "Classe 0",
                    "Precisão": 0.82,
                    "Recall": 0.78,
                    "F1-Score": 0.80
                },
                {
                    "Classe": "Classe 1",
                    "Precisão": 0.76,
                    "Recall": 0.81,
                    "F1-Score": 0.78
                }
            ]
        }

    def _format_metrics_data(self, data: Dict) -> Dict:
        """
        Formata os dados de métricas para uso no dashboard.

        Args:
            data: Dados brutos de métricas

        Returns:
            Dados formatados para o dashboard
        """
        # Estrutura para armazenar dados formatados
        formatted_data = {
            "model_info": {},
            "general_metrics": {},
            "class_metrics": []
        }

        # Extrair informações do modelo
        if "modelo" in data:
            modelo_info = data["modelo"]
            formatted_data["model_info"] = {
                "name": modelo_info.get("nome", modelo_info.get("path", "Não especificado")),
                "date": modelo_info.get("data_avaliacao", "Não especificada")
            }

        # Métricas gerais
        if "metricas_gerais" in data:
            formatted_data["general_metrics"] = data["metricas_gerais"]

        # Métricas por classe
        if "metricas_por_classe" in data:
            formatted_data["class_metrics"] = data["metricas_por_classe"]

        return formatted_data