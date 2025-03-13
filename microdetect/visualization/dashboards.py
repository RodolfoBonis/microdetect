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

    def create_detection_dashboard(
            self,
            results_dir: str,
            port: int = 8050,
            open_browser: bool = True
    ) -> int:
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
            from dash import dcc, html
            import dash_bootstrap_components as dbc
            from dash.dependencies import Input, Output, State
        except ImportError:
            logger.error("Dash não encontrado. Instale com: pip install dash dash-bootstrap-components")
            return 0

        # Carregar dados de detecções
        json_files = [f for f in os.listdir(results_dir) if f.endswith('.json')]
        if not json_files:
            logger.error(f"Nenhum arquivo JSON encontrado em: {results_dir}")
            return 0

        # Procurar por resultados de detecção
        detection_file = None
        for f in json_files:
            if "detection" in f.lower() or "result" in f.lower():
                detection_file = os.path.join(results_dir, f)
                break

        if not detection_file:
            detection_file = os.path.join(results_dir, json_files[0])

        # Carregar dados
        try:
            with open(detection_file, 'r') as f:
                detection_data = json.load(f)
        except Exception as e:
            logger.error(f"Erro ao carregar dados: {str(e)}")
            return 0

        # Extrair informações para o dashboard
        images = list(detection_data.keys())

        # Criar dataframe com todas as detecções
        rows = []
        for image_name, detections in detection_data.items():
            for det in detections:
                row = {
                    "image": image_name,
                    "class": det.get("class", 0),
                    "class_name": det.get("class_name", f"Class {det.get('class', 0)}"),
                    "confidence": det.get("confidence", 0),
                }

                # Adicionar informações de bbox
                if "bbox" in det:
                    bbox = det["bbox"]
                    if len(bbox) == 4:
                        row["x1"] = bbox[0]
                        row["y1"] = bbox[1]
                        row["x2"] = bbox[2] if len(bbox) == 4 else bbox[0] + bbox[2]
                        row["y2"] = bbox[3] if len(bbox) == 4 else bbox[1] + bbox[3]
                        row["width"] = row["x2"] - row["x1"]
                        row["height"] = row["y2"] - row["y1"]
                        row["area"] = row["width"] * row["height"]

                rows.append(row)

        df = pd.DataFrame(rows)

        # Criar aplicação Dash
        app = dash.Dash(
            __name__,
            external_stylesheets=[dbc.themes.FLATLY],
            title="MicroDetect - Dashboard de Detecções"
        )

        # Obter classes únicas
        classes = sorted(df["class_name"].unique())

        # Layout do dashboard
        app.layout = dbc.Container([
            dbc.Row([
                dbc.Col([
                    html.H1("MicroDetect - Dashboard de Detecções", className="mb-4"),
                    html.Hr(),
                ], width=12)
            ]),

            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("Estatísticas Gerais"),
                        dbc.CardBody([
                            html.H3(f"Total de Imagens: {len(images)}"),
                            html.H3(f"Total de Detecções: {len(df)}"),
                            html.H3(f"Número de Classes: {len(classes)}"),
                            html.H4(f"Confiança Média: {df['confidence'].mean():.4f}")
                        ])
                    ], className="mb-4"),

                    dbc.Card([
                        dbc.CardHeader("Filtros"),
                        dbc.CardBody([
                            html.Label("Limiar de Confiança:"),
                            dcc.Slider(
                                id="confidence-slider",
                                min=0,
                                max=1,
                                step=0.05,
                                value=0.25,
                                marks={i / 10: str(i / 10) for i in range(0, 11, 1)},
                                className="mb-3"
                            ),

                            html.Label("Classes:"),
                            dcc.Checklist(
                                id="class-checklist",
                                options=[{"label": c, "value": c} for c in classes],
                                value=classes,
                                inline=True,
                                className="mb-3"
                            ),

                            html.Label("Imagem:"),
                            dcc.Dropdown(
                                id="image-dropdown",
                                options=[{"label": img, "value": img} for img in images],
                                value=images[0] if images else None,
                                clearable=False,
                                className="mb-3"
                            ),

                            dbc.Button(
                                "Atualizar Visualização",
                                id="update-button",
                                color="primary",
                                className="mt-2"
                            )
                        ])
                    ], className="mb-4")
                ], width=4),

                dbc.Col([
                    dbc.Tabs([
                        dbc.Tab([
                            dcc.Graph(id="detections-by-class")
                        ], label="Detecções por Classe"),

                        dbc.Tab([
                            dcc.Graph(id="confidence-histogram")
                        ], label="Histograma de Confiança"),

                        dbc.Tab([
                            dcc.Graph(id="size-scatter")
                        ], label="Tamanho x Confiança")
                    ]),

                    html.Div(id="filtered-stats", className="mt-4")
                ], width=8)
            ]),

            dbc.Row([
                dbc.Col([
                    html.H3("Detalhes da Imagem", className="mb-3"),
                    html.Div(id="image-display"),
                    html.Div(id="image-detections", className="mt-3")
                ], width=12)
            ])
        ], fluid=True)

        # Callback para atualizar gráficos
        @app.callback(
            [
                Output("detections-by-class", "figure"),
                Output("confidence-histogram", "figure"),
                Output("size-scatter", "figure"),
                Output("filtered-stats", "children"),
                Output("image-detections", "children")
            ],
            [Input("update-button", "n_clicks")],
            [
                State("confidence-slider", "value"),
                State("class-checklist", "value"),
                State("image-dropdown", "value")
            ]
        )
        def update_graphs(n_clicks, conf_threshold, selected_classes, selected_image):
            import plotly.express as px
            import plotly.graph_objects as go

            # Filtrar DataFrame
            filtered_df = df[
                (df["confidence"] >= conf_threshold) &
                (df["class_name"].isin(selected_classes))
                ]

            # Gráfico 1: Detecções por Classe
            fig1 = px.bar(
                filtered_df["class_name"].value_counts().reset_index(),
                x="index",
                y="class_name",
                color="index",
                labels={"index": "Classe", "class_name": "Contagem"},
                title="Número de Detecções por Classe"
            )

            # Gráfico 2: Histograma de Confiança
            fig2 = px.histogram(
                filtered_df,
                x="confidence",
                color="class_name",
                nbins=20,
                title="Distribuição de Confiança por Classe",
                labels={"confidence": "Confiança", "count": "Contagem"}
            )

            # Gráfico 3: Scatter Plot de Tamanho vs Confiança
            if "area" in filtered_df.columns:
                fig3 = px.scatter(
                    filtered_df,
                    x="area",
                    y="confidence",
                    color="class_name",
                    size="area",
                    hover_data=["image", "class_name"],
                    title="Relação entre Tamanho e Confiança",
                    labels={"area": "Área", "confidence": "Confiança"}
                )
            else:
                fig3 = go.Figure()
                fig3.update_layout(title="Dados de área não disponíveis")

            # Estatísticas filtradas
            stats = dbc.Card([
                dbc.CardHeader("Estatísticas Filtradas"),
                dbc.CardBody([
                    html.H4(f"Detecções: {len(filtered_df)}"),
                    html.H4(f"Confiança Média: {filtered_df['confidence'].mean():.4f}")
                ])
            ])

            # Detalhes da imagem selecionada
            image_dets = filtered_df[filtered_df["image"] == selected_image]

            image_table = dbc.Table.from_dataframe(
                image_dets[["class_name", "confidence"]].round(4),
                striped=True,
                bordered=True,
                hover=True,
                responsive=True,
                className="mt-3"
            ) if not image_dets.empty else html.P("Nenhuma detecção para esta imagem com os filtros atuais.")

            return fig1, fig2, fig3, stats, [
                html.H4(f"Detecções em: {selected_image}"),
                html.P(f"Total: {len(image_dets)} detecções"),
                image_table
            ]

        # Iniciar servidor
        def open_browser_tab():
            if open_browser:
                webbrowser.open_new_tab(f"http://localhost:{port}")

        threading.Timer(1, open_browser_tab).start()

        # Iniciar aplicação
        app.run_server(debug=False, port=port)
        return port

    def create_model_comparison_dashboard(
            self,
            comparison_results: Dict[str, Dict],
            port: int = 8051,
            open_browser: bool = True
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
            from dash import dcc, html
            import dash_bootstrap_components as dbc
            from dash.dependencies import Input, Output
        except ImportError:
            logger.error("Dash não encontrado. Instale com: pip install dash dash-bootstrap-components")
            return 0

        # Converter para DataFrame
        rows = []
        for model_name, model_data in comparison_results.items():
            row = {
                "model": model_name,
                "category": model_data.get("tamanho", "unknown"),
                "size_mb": model_data.get("tamanho_arquivo", 0),
            }

            # Adicionar métricas
            if "metricas" in model_data:
                for metric, value in model_data["metricas"].items():
                    row[metric] = value

            # Adicionar velocidade
            if "velocidade" in model_data:
                for speed_metric, value in model_data["velocidade"].items():
                    row[speed_metric] = value

            rows.append(row)

        df = pd.DataFrame(rows)

        # Criar aplicação Dash
        app = dash.Dash(
            __name__,
            external_stylesheets=[dbc.themes.FLATLY],
            title="MicroDetect - Comparação de Modelos"
        )

        # Layout do dashboard
        app.layout = dbc.Container([
            dbc.Row([
                dbc.Col([
                    html.H1("MicroDetect - Comparação de Modelos", className="mb-4"),
                    html.Hr(),
                ], width=12)
            ]),

            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("Modelos Comparados"),
                        dbc.CardBody([
                            html.H4(f"Total de Modelos: {len(df)}"),
                            dbc.ListGroup([
                                dbc.ListGroupItem(
                                    f"{row['model']} (Categoria: {row['category']})",
                                    color=["primary", "success", "info", "warning", "danger"][i % 5]
                                )
                                for i, (_, row) in enumerate(df.iterrows())
                            ])
                        ])
                    ], className="mb-4"),

                    dbc.Card([
                        dbc.CardHeader("Filtros"),
                        dbc.CardBody([
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
                                className="mb-3"
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
                                className="mb-3"
                            )
                        ])
                    ], className="mb-4")
                ], width=4),

                dbc.Col([
                    dbc.Tabs([
                        dbc.Tab([
                            dcc.Graph(id="metric-comparison")
                        ], label="Comparação por Métrica"),

                        dbc.Tab([
                            dcc.Graph(id="tradeoff-plot")
                        ], label="Precisão vs. Velocidade"),

                        dbc.Tab([
                            dcc.Graph(id="size-comparison")
                        ], label="Tamanho de Modelo")
                    ]),

                    html.Div(id="comparison-stats", className="mt-4")
                ], width=8)
            ]),

            dbc.Row([
                dbc.Col([
                    html.H3("Tabela Comparativa", className="mb-3"),
                    html.Div(id="comparison-table")
                ], width=12)
            ])
        ], fluid=True)

        # Callback para atualizar gráficos
        @app.callback(
            [
                Output("metric-comparison", "figure"),
                Output("tradeoff-plot", "figure"),
                Output("size-comparison", "figure"),
                Output("comparison-stats", "children"),
                Output("comparison-table", "children")
            ],
            [
                Input("metric-dropdown", "value"),
                Input("chart-type", "value")
            ]
        )
        def update_graphs(selected_metric, chart_type):
            import plotly.express as px
            import plotly.graph_objects as go

            # Gráfico 1: Comparação por métrica
            if chart_type == "bar":
                fig1 = px.bar(
                    df,
                    x="model",
                    y=selected_metric,
                    color="category",
                    title=f"Comparação de {selected_metric}",
                    labels={"model": "Modelo", selected_metric: selected_metric.upper()}
                )
            elif chart_type == "line":
                fig1 = px.line(
                    df,
                    x="model",
                    y=selected_metric,
                    color="category",
                    markers=True,
                    title=f"Comparação de {selected_metric}",
                    labels={"model": "Modelo", selected_metric: selected_metric.upper()}
                )
            else:  # radar
                fig1 = go.Figure()

                for category in df["category"].unique():
                    category_df = df[df["category"] == category]
                    fig1.add_trace(go.Scatterpolar(
                        r=category_df[selected_metric],
                        theta=category_df["model"],
                        fill="toself",
                        name=category
                    ))

                fig1.update_layout(
                    polar=dict(
                        radialaxis=dict(
                            visible=True,
                            range=[0, max(df[selected_metric]) * 1.1]
                        )
                    ),
                    title=f"Comparação de {selected_metric}"
                )

            # Gráfico 2: Precisão vs. Velocidade
            if "mAP50" in df.columns and "fps" in df.columns:
                fig2 = px.scatter(
                    df,
                    x="fps",
                    y="mAP50",
                    color="category",
                    size="size_mb",
                    hover_data=["model", "category"],
                    title="Trade-off: Precisão vs. Velocidade",
                    labels={"fps": "FPS", "mAP50": "mAP50"},
                    text="model"
                )
                fig2.update_traces(textposition="top right")
            else:
                fig2 = go.Figure()
                fig2.update_layout(title="Dados insuficientes para gráfico de trade-off")

            # Gráfico 3: Tamanho do Modelo
            fig3 = px.bar(
                df,
                x="model",
                y="size_mb",
                color="category",
                title="Tamanho do Modelo (MB)",
                labels={"model": "Modelo", "size_mb": "Tamanho (MB)"}
            )

            # Estatísticas
            stats = dbc.Card([
                dbc.CardHeader("Estatísticas Comparativas"),
                dbc.CardBody([
                    html.H4(f"Melhor modelo para {selected_metric}: {df.loc[df[selected_metric].idxmax(), 'model']}"),
                    html.H4(f"Valor: {df[selected_metric].max():.4f}"),
                    html.H4(
                        f"Modelo mais rápido: {df.loc[df['fps'].idxmax(), 'model'] if 'fps' in df.columns else 'N/A'}"),
                    html.H4(f"FPS: {df['fps'].max():.1f if 'fps' in df.columns else 'N/A'}")
                ])
            ])

            # Tabela comparativa
            display_cols = ["model", "category", "size_mb"]
            metric_cols = [col for col in df.columns if col not in ["model", "category", "size_mb"]]
            display_cols.extend(metric_cols)

            table = dbc.Table.from_dataframe(
                df[display_cols].round(4),
                striped=True,
                bordered=True,
                hover=True,
                responsive=True,
                className="mt-3"
            )

            return fig1, fig2, fig3, stats, table

        # Iniciar servidor
        def open_browser_tab():
            if open_browser:
                webbrowser.open_new_tab(f"http://localhost:{port}")

        threading.Timer(1, open_browser_tab).start()

        # Iniciar aplicação
        app.run_server(debug=False, port=port)
        return port