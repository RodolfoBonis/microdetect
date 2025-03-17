"""
Interface de linha de comando para o projeto MicroDetect.
"""

import argparse
import json
import logging
import os
import sys
from datetime import datetime
from getpass import getpass
from typing import List, Optional

from microdetect import __version__
from microdetect.annotation.annotator import ImageAnnotator
from microdetect.annotation.visualization import AnnotationVisualizer
from microdetect.aws import AWSSetupManager
from microdetect.data.augmentation import DataAugmenter
from microdetect.data.conversion import ImageConverter
from microdetect.data.dataset import DatasetManager
from microdetect.docs import DEFAULT_LANGUAGE, LANGUAGES
from microdetect.training.evaluate import ModelEvaluator
from microdetect.training.train import YOLOTrainer
from microdetect.utils import ColoredHelpFormatter, ColoredVersionAction, get_logo_with_name_ascii
from microdetect.utils.colors import BRIGHT, ERROR, INFO, RESET, SUCCESS, WARNING

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("microdetect.log", mode="a"),
    ],
)

logger = logging.getLogger(__name__)


def setup_convert_parser(subparsers):
    """Configurar parser para comando de conversão de imagens."""
    parser = subparsers.add_parser("convert", help="Converter imagens")
    parser.add_argument("--input_dir", required=True, help="Diretório de entrada")
    parser.add_argument("--output_dir", required=True, help="Diretório de saída")
    parser.add_argument("--use_opencv", action="store_true", help="Usar OpenCV em vez de PIL")
    parser.add_argument(
        "--delete_original",
        action="store_true",
        help="Excluir arquivos originais após conversão",
    )
    parser.add_argument("--format", default="tiff-to-png", help="Formato de conversão (ex: tiff-to-png)")


def setup_annotate_parser(subparsers):
    """Configurar parser para comando de anotação."""
    parser = subparsers.add_parser("annotate", help="Anotar imagens manualmente")
    parser.add_argument("--image_dir", required=True, help="Diretório com imagens para anotação")
    parser.add_argument("--output_dir", required=True, help="Diretório para salvar as anotações")


def setup_visualize_parser(subparsers):
    """Configurar parser para comando de visualização."""
    parser = subparsers.add_parser("visualize", help="Visualizar anotações em imagens")
    parser.add_argument("--image_dir", required=True, help="Diretório com imagens")
    parser.add_argument(
        "--label_dir",
        help="Diretório com anotações (se diferente do diretório de imagens)",
    )
    parser.add_argument("--output_dir", help="Diretório para salvar imagens anotadas")
    parser.add_argument(
        "--filter_classes",
        help='Lista separada por vírgulas de IDs de classe para exibir (ex: "0,1")',
    )


def setup_augment_parser(subparsers):
    """Configurar parser para comando de augmentação."""
    parser = subparsers.add_parser("augment", help="Aplicar augmentação em imagens e anotações")
    parser.add_argument("--image_dir", required=True, help="Diretório com imagens originais")
    parser.add_argument("--label_dir", required=True, help="Diretório com anotações originais")
    parser.add_argument("--output_image_dir", help="Diretório para salvar imagens aumentadas")
    parser.add_argument("--output_label_dir", help="Diretório para salvar anotações aumentadas")
    parser.add_argument("--factor", type=int, help="Fator de augmentação")


def setup_dataset_parser(subparsers):
    """Configurar parser para comando de preparação de dataset."""
    parser = subparsers.add_parser("dataset", help="Preparar dataset")
    parser.add_argument("--source_img_dir", required=True, help="Diretório com imagens de origem")
    parser.add_argument("--source_label_dir", required=True, help="Diretório com anotações de origem")
    parser.add_argument("--dataset_dir", help="Diretório para dataset estruturado")
    parser.add_argument("--train_ratio", type=float, help="Proporção para treinamento")
    parser.add_argument("--val_ratio", type=float, help="Proporção para validação")
    parser.add_argument("--test_ratio", type=float, help="Proporção para teste")


def setup_train_parser(subparsers):
    """Configurar parser para comando de treinamento."""
    parser = subparsers.add_parser("train", help="Treinar modelo YOLO")
    parser.add_argument("--dataset_dir", required=True, help="Diretório com dataset estruturado")
    parser.add_argument(
        "--data_yaml",
        help="Caminho para arquivo data.yaml (se não especificado, será criado)",
    )
    parser.add_argument("--model_size", choices=["n", "s", "m", "l", "x"], help="Tamanho do modelo YOLO")
    parser.add_argument("--epochs", type=int, help="Número de épocas")
    parser.add_argument("--batch_size", type=int, help="Tamanho do batch")
    parser.add_argument("--image_size", type=int, help="Tamanho da imagem")
    parser.add_argument("--output_dir", help="Diretório para resultados")
    parser.add_argument("--no_pretrained", action="store_true", help="Não usar pesos pré-treinados")
    parser.add_argument("--resume", help="Continuar de um checkpoint")
    parser.add_argument(
        "--find_hyperparams",
        action="store_true",
        help="Buscar melhores hiperparâmetros",
    )


def setup_evaluate_parser(subparsers):
    """Configurar parser para comando de avaliação."""
    parser = subparsers.add_parser("evaluate", help="Avaliar modelo treinado")
    parser.add_argument("--model_path", required=True, help="Caminho para o modelo (.pt)")
    parser.add_argument("--dataset_dir", required=True, help="Diretório do dataset")
    parser.add_argument("--data_yaml", help="Caminho para arquivo data.yaml")
    parser.add_argument("--output_dir", help="Diretório para relatórios")
    parser.add_argument("--confusion_matrix", action="store_true", help="Gerar matriz de confusão")


def setup_init_parser(subparsers):
    """Configurar parser para comando de inicialização."""
    parser = subparsers.add_parser("init", help="Inicializar ambiente de trabalho MicroDetect")
    parser.add_argument("--force", action="store_true", help="Sobrescrever arquivos existentes")
    parser.add_argument(
        "--project",
        "-p",
        default=".",
        help="Diretório para inicializar (padrão: diretório atual)",
    )


def setup_update_parser(subparsers):
    """Configurar parser para comando de atualização."""
    parser = subparsers.add_parser("update", help="Verificar e instalar atualizações")
    parser.add_argument("--force", action="store_true", help="Forçar atualização sem confirmação")
    parser.add_argument("--check-only", action="store_true", help="Apenas verificar se há atualizações")


def setup_aws_parser(subparsers):
    """Configurar parser para comando de configuração AWS."""
    parser = subparsers.add_parser("setup-aws", help="Configurar AWS CodeArtifact para atualizações")
    parser.add_argument("--domain", required=True, help="Nome do domínio AWS CodeArtifact")
    parser.add_argument("--repository", required=True, help="Nome do repositório AWS CodeArtifact")
    parser.add_argument("--domain-owner", help="ID da conta proprietária do domínio (opcional)")
    parser.add_argument("--region", help="Região AWS (padrão: us-east-1)")
    parser.add_argument("--configure-aws", action="store_true", help="Configurar credenciais AWS")
    parser.add_argument("--test", action="store_true", help="Testar conexão com AWS CodeArtifact")


def setup_docs_parser(subparsers):
    """Configurar parser para comando de documentação."""
    parser = subparsers.add_parser("docs", help="Abrir documentação no navegador")
    parser.add_argument("--port", type=int, default=8080, help="Porta para o servidor de documentação")
    parser.add_argument("--no-browser", action="store_true", help="Não abrir navegador automaticamente")
    parser.add_argument(
        "--lang", type=str, choices=list(LANGUAGES.keys()), default=DEFAULT_LANGUAGE, help="Idioma padrão para a documentação"
    )

    # Opções para execução em background
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--background", action="store_true", help="Executar servidor em background")
    group.add_argument("--stop", action="store_true", help="Parar servidor em execução em background")
    group.add_argument("--status", action="store_true", help="Verificar status do servidor em background")


def setup_install_docs_parser(subparsers):
    """Configurar o parser para o comando install-docs."""
    parser = subparsers.add_parser("install-docs", help="Instala ou atualiza a documentação local")
    parser.add_argument("--force", action="store_true", help="Força a reinstalação mesmo se a documentação já existir")
    parser.add_argument("--no-interactive", dest="interactive", action="store_false", help="Modo não interativo")
    return parser


def setup_model_comparison_parser(subparsers):
    """Configurar parser para comando de comparação de modelos."""
    parser = subparsers.add_parser("compare_models", help="Comparar diferentes modelos")
    parser.add_argument("--model_paths", required=True, help="Lista de caminhos de modelos separados por vírgula")
    parser.add_argument("--data_yaml", required=True, help="Caminho para o arquivo data.yaml")
    parser.add_argument("--output_dir", help="Diretório para salvar os resultados")
    parser.add_argument("--conf_threshold", type=float, default=0.25, help="Limiar de confiança para detecções")
    parser.add_argument("--iou_threshold", type=float, default=0.7, help="Limiar de IoU para supressão não-máxima")
    parser.add_argument("--dashboard", action="store_true", help="Gerar dashboard interativo")


def setup_batch_detect_parser(subparsers):
    """Configurar parser para comando de detecção em lote."""
    parser = subparsers.add_parser("batch_detect", help="Processar detecções em lote")
    parser.add_argument("--model_path", required=True, help="Caminho para o modelo")
    parser.add_argument("--source", required=True, help="Diretório com imagens para processar")
    parser.add_argument("--output_dir", help="Diretório para salvar resultados")
    parser.add_argument("--batch_size", type=int, default=16, help="Tamanho do batch para inferência")
    parser.add_argument("--conf_threshold", type=float, default=0.25, help="Limiar de confiança")
    parser.add_argument("--save_txt", action="store_true", help="Salvar anotações em formato YOLO")
    parser.add_argument("--save_json", action="store_true", help="Salvar resultados em JSON")
    parser.add_argument("--save_img", action="store_true", help="Salvar imagens com detecções")


def setup_visualize_detections_parser(subparsers):
    """Configurar parser para comando de visualização de detecções."""
    parser = subparsers.add_parser("visualize_detections", help="Visualizar detecções interativamente")
    parser.add_argument("--model_path", required=True, help="Caminho para o modelo")
    parser.add_argument("--source", required=True, help="Diretório com imagens para visualizar")
    parser.add_argument("--conf_threshold", type=float, default=0.25, help="Limiar de confiança inicial")


def setup_analyze_errors_parser(subparsers):
    """Configurar parser para comando de análise de erros."""
    parser = subparsers.add_parser("analyze_errors", help="Analisar erros de detecção")
    parser.add_argument("--model_path", required=True, help="Caminho para o modelo")
    parser.add_argument("--data_yaml", required=True, help="Caminho para o arquivo data.yaml")
    parser.add_argument("--dataset_dir", required=True, help="Diretório do dataset")
    parser.add_argument("--output_dir", help="Diretório para salvar análises")
    parser.add_argument(
        "--error_type",
        choices=["all", "false_positives", "false_negatives", "classification_errors", "localization_errors"],
        default="all",
        help="Tipo de erro para analisar",
    )


def setup_generate_report_parser(subparsers):
    """Configurar parser para comando de geração de relatórios."""
    parser = subparsers.add_parser("generate_report", help="Gerar relatório de avaliação")
    parser.add_argument("--results_dir", required=True, help="Diretório com resultados de avaliação")
    parser.add_argument("--output_file", help="Caminho para o arquivo de saída")
    parser.add_argument("--format", choices=["pdf", "csv", "json"], default="pdf", help="Formato do relatório")
    parser.add_argument(
        "--include_images", help="Lista de caminhos de imagens para incluir no relatório, separados por vírgula"
    )


def setup_dashboard_parser(subparsers):
    """Configurar parser para comando de dashboard."""
    parser = subparsers.add_parser("dashboard", help="Iniciar dashboard interativo")
    parser.add_argument("--results_dir", required=True, help="Diretório com resultados de detecção")
    parser.add_argument("--port", type=int, default=8050, help="Porta para o servidor web")
    parser.add_argument("--no_browser", action="store_true", help="Não abrir navegador automaticamente")


def handle_install_docs(args):
    """
    Manipula o comando de instalação de documentação.
    Copia os arquivos da documentação para a pasta do usuário (.microdetect/docs).
    """
    import shutil
    from pathlib import Path

    # Diretório home do usuário
    user_docs_dir = Path.home() / ".microdetect" / "docs"

    # Criar os diretórios se não existirem
    user_docs_dir.parent.mkdir(exist_ok=True)

    # Se o diretório de documentação já existir, perguntar se deseja sobrescrever
    if user_docs_dir.exists() and not args.force:
        if args.interactive:
            print(f"O diretório de documentação já existe em {user_docs_dir}.")
            response = input("Deseja sobrescrever? [s/N]: ").strip().lower()
            if response != "s" and response != "sim":
                print("Instalação de documentação cancelada.")
                return
        else:
            print(f"O diretório de documentação já existe em {user_docs_dir}. Use --force para sobrescrever.")
            return

    # Tentar encontrar os arquivos de documentação
    from microdetect.docs.docs_server import find_docs_dir

    source_docs_dir = find_docs_dir()

    # Verificar se a fonte é um diretório temporário (o que significa que não encontrou docs)
    if "microdetect_docs_" in str(source_docs_dir) and "temp" in str(source_docs_dir).lower():
        print("Não foi possível encontrar a documentação original.")
        print("Verifique se o pacote foi instalado corretamente com os arquivos de documentação.")
        return

    try:
        # Remover diretório existente se necessário
        if user_docs_dir.exists():
            shutil.rmtree(user_docs_dir)

        # Copiar os arquivos de documentação
        shutil.copytree(source_docs_dir, user_docs_dir)

        print(f"Documentação instalada com sucesso em {user_docs_dir}")
        print("Use 'microdetect docs' para visualizar a documentação.")
    except Exception as e:
        print(f"Erro ao instalar a documentação: {str(e)}")
        return


def handle_docs(args):
    """Manipular comando de documentação."""
    try:
        from microdetect.docs import (
            check_server_status,
            start_docs_server,
            start_server_in_background,
            stop_background_server,
        )

        # Verificar se queremos parar o servidor
        if args.stop:
            stop_background_server()
            return

        # Verificar status do servidor
        if args.status:
            status = check_server_status()
            if status["status"] == "running":
                logger.info(f"Documentation server is running (PID: {status['pid']})")
                logger.info(f"Server URL: {status['url']}")
            else:
                logger.info("Documentation server is not running")
            return

        # Configurar opções globais (se necessário)
        if args.port != 8080:
            import microdetect.docs.docs_server as docs_server

            docs_server.PORT = args.port

        if args.no_browser:

            def do_nothing(url):
                print(f"Servidor de documentação iniciado em {url}")
                print("Acesse o URL acima no seu navegador para ver a documentação.")
                print("Pressione Ctrl+C para parar o servidor.")

            import microdetect.docs.docs_server as docs_server

            docs_server.open_browser = do_nothing

        # Iniciar servidor em background ou foreground
        if args.background:
            start_server_in_background(args.port, args.lang)
        else:
            # Iniciar servidor em primeiro plano
            start_docs_server(args.lang)
    except ImportError as e:
        logger.error(f"Erro ao carregar o servidor de documentação: {str(e)}")
        logger.info("Tente instalar as dependências necessárias: pip install markdown pygments")
    except Exception as e:
        logger.error(f"Erro ao iniciar o servidor de documentação: {str(e)}")


def handle_setup_aws(args):
    """Manipular comando de configuração AWS."""
    # Verificar e instalar AWS CLI se necessário
    if not AWSSetupManager.check_aws_cli():
        print(f"{INFO}AWS CLI não encontrado. Iniciando instalação...{RESET}")
        if not AWSSetupManager.install_aws_cli():
            print(f"{ERROR}Falha ao instalar AWS CLI. Por favor, instale manualmente.{RESET}")
            return

    # Configurar credenciais AWS se solicitado
    aws_access_key = None
    aws_secret_key = None
    region = args.region or "us-east-1"

    if args.configure_aws:
        print(f"\n{BRIGHT}{INFO}=== Configuração de Credenciais AWS ==={RESET}")
        print(f"{INFO}Essas credenciais serão usadas para acessar o AWS CodeArtifact.{RESET}")

        print(f"{BRIGHT}AWS Access Key ID: {RESET}", end="")
        aws_access_key = input()
        print(f"{BRIGHT}AWS Secret Access Key: {RESET}", end="")
        aws_secret_key = getpass("")
        if not args.region:
            print(f"{BRIGHT}AWS Region [{region}]: {RESET}", end="")
            region = input() or region

    # Configurar AWS e variáveis de ambiente para o CodeArtifact
    success = AWSSetupManager.configure_aws(
        domain=args.domain,
        repository=args.repository,
        domain_owner=args.domain_owner,
        aws_access_key=aws_access_key,
        aws_secret_key=aws_secret_key,
        aws_region=region,
    )

    if not success:
        print(f"{ERROR}Falha ao configurar AWS CodeArtifact.{RESET}")
        return

    # Testar conexão
    if args.test or args.configure_aws:
        success, message = AWSSetupManager.test_codeartifact_login()
        if success:
            print(f"{SUCCESS}Teste de conexão: {message}{RESET}")
        else:
            print(f"{ERROR}Teste de conexão falhou: {message}{RESET}")

    print(f"\n{BRIGHT}{SUCCESS}=== Configuração concluída! ==={RESET}")
    print(f"{INFO}Agora você pode usar o comando '{BRIGHT}microdetect update{RESET}{INFO}' para atualizar a aplicação.{RESET}")
    print(f"{INFO}Todas as vezes que executar comandos microdetect, o sistema verificará{RESET}")
    print(f"{INFO}automaticamente se há atualizações disponíveis.{RESET}")


def handle_update(args):
    """Manipular comando de atualização."""
    from microdetect.updater import UpdateManager

    if args.check_only:
        update_info = UpdateManager.check_for_updates()
        if "error" in update_info:
            print(f"{ERROR}{update_info['error']}{RESET}")
            return

        current_version = update_info["current"]
        latest_version = update_info["latest"]
        needs_update = update_info["needs_update"]

        if needs_update:
            print(
                f"{INFO}Nova versão disponível: {SUCCESS}{latest_version} {INFO}(atual: {WARNING}{current_version}{INFO}){RESET}"
            )
            print(f"{INFO}Para atualizar, execute: {BRIGHT}microdetect update{RESET}")
        else:
            print(f"{SUCCESS}MicroDetect já está na versão mais recente {BRIGHT}({current_version}){RESET}")
    else:
        UpdateManager.update_package(args.force)


def handle_init(args):
    """
    Manipular comando de inicialização.
    Cria estrutura de diretórios e arquivo de configuração no diretório especificado.
    """
    import os
    import shutil

    import pkg_resources
    import yaml

    target_project = os.path.abspath(args.project)
    logger.info(f"Inicializando ambiente MicroDetect em: {target_project}")

    # Verificar/criar o diretório
    if not os.path.exists(target_project):
        os.makedirs(target_project)
        logger.info(f"Diretório criado: {target_project}")

    # Caminho para o arquivo de configuração
    config_path = os.path.join(target_project, "config.yaml")

    # Verificar se o arquivo já existe
    if os.path.exists(config_path) and not args.force:
        logger.warning(f"Arquivo config.yaml já existe. Use --force para sobrescrever.")
    else:
        # Tentar copiar o arquivo de configuração padrão do pacote
        try:
            # Primeira tentativa: usar pkg_resources
            try:
                default_config_path = pkg_resources.resource_filename("microdetect", "default_config.yaml")
                if os.path.exists(default_config_path):
                    shutil.copy(default_config_path, config_path)
                    logger.info(f"Arquivo config.yaml criado em: {config_path}")
                else:
                    raise FileNotFoundError("Arquivo de configuração padrão não encontrado no pacote")
            except (ImportError, FileNotFoundError):
                # Segunda tentativa: criar o arquivo diretamente
                logger.warning("Não foi possível localizar o arquivo default_config.yaml no pacote. Criando um novo.")

                # Configuração padrão
                default_config = {
                    "directories": {
                        "dataset": "./dataset",
                        "images": "./data/images",
                        "labels": "./data/labels",
                        "output": "./runs/train",
                        "reports": "./reports",
                    },
                    "classes": ["0-levedura", "1-fungo", "2-micro-alga"],
                    "color_map": {"0": [0, 255, 0], "1": [0, 0, 255], "2": [255, 0, 0]},
                    "training": {
                        "model_size": "m",
                        "epochs": 100,
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

                # Salvar arquivo
                with open(config_path, "w") as f:
                    yaml.dump(default_config, f, default_flow_style=False)
                logger.info(f"Arquivo config.yaml criado em: {config_path}")

        except Exception as e:
            logger.error(f"Erro ao criar arquivo de configuração: {str(e)}")
            return

    # Criar estrutura de diretórios
    directories = [
        os.path.join(target_project, "data", "images"),
        os.path.join(target_project, "data", "labels"),
        os.path.join(target_project, "dataset"),
        os.path.join(target_project, "runs", "train"),
        os.path.join(target_project, "reports"),
    ]

    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            logger.info(f"Diretório criado: {directory}")

    logger.info(
        f"""
Ambiente MicroDetect inicializado com sucesso!

Para começar:

1. Adicione suas imagens em:        {os.path.join(target_project, 'data', 'images')}
2. Anote as imagens:                microdetect annotate
3. Prepare o dataset:               microdetect dataset
4. Treine o modelo:                 microdetect train
5. Avalie o modelo:                 microdetect evaluate

Ou use o Makefile para passos automáticos (se disponível).
"""
    )


def handle_convert(args):
    """Manipular comando de conversão de imagens."""
    logger.info(f"Iniciando conversão de imagens de {args.input_dir} para {args.output_dir}")

    converter = ImageConverter()

    if args.format == "tiff-to-png":
        success, errors, error_messages = converter.convert_tiff_to_png(
            args.input_dir, args.output_dir, args.use_opencv, args.delete_original
        )
    else:
        source_format, target_format = args.format.split("-to-")
        success, errors, error_messages = converter.batch_convert(
            args.input_dir,
            args.output_dir,
            source_format,
            target_format,
            args.use_opencv,
            args.delete_original,
        )

    logger.info(f"Conversão concluída: {success} sucessos, {errors} erros")
    if error_messages:
        logger.warning(
            f"Erros durante a conversão: {', '.join(error_messages[:5])}"
            + (f" e mais {len(error_messages) - 5} erros" if len(error_messages) > 5 else "")
        )


def handle_annotate(args):
    """Manipular comando de anotação."""
    logger.info(f"Iniciando anotação manual de imagens em {args.image_dir}")

    annotator = ImageAnnotator()
    total, annotated = annotator.batch_annotate(args.image_dir, args.output_dir)

    logger.info(f"Anotação concluída: {annotated}/{total} imagens anotadas")


def handle_visualize(args):
    """Manipular comando de visualização."""
    logger.info(f"Iniciando visualização de anotações para imagens em {args.image_dir}")

    filter_classes = None
    if args.filter_classes:
        filter_classes = set(args.filter_classes.split(","))

    visualizer = AnnotationVisualizer()

    if args.output_dir:
        # Modo de salvamento batch
        count = visualizer.save_annotated_images(args.image_dir, args.label_dir, args.output_dir, filter_classes)
        logger.info(f"Visualização em batch concluída: {count} imagens anotadas salvas")
    else:
        # Modo interativo
        visualizer.visualize_annotations(args.image_dir, args.label_dir, args.output_dir, filter_classes)
        logger.info("Visualização interativa concluída")


def handle_augment(args):
    """Manipular comando de augmentação."""
    logger.info(f"Iniciando augmentação de imagens em {args.image_dir}")

    augmenter = DataAugmenter()
    original, augmented = augmenter.augment_data(
        args.image_dir,
        args.label_dir,
        args.output_image_dir,
        args.output_label_dir,
        args.factor,
    )

    logger.info(f"Augmentação concluída: {augmented} novas imagens geradas a partir de {original} originais")


def handle_dataset(args):
    """Manipular comando de preparação de dataset."""
    logger.info(f"Iniciando preparação de dataset a partir de {args.source_img_dir}")

    manager = DatasetManager(args.dataset_dir, args.train_ratio, args.val_ratio, args.test_ratio)

    split_counts = manager.split_dataset(args.source_img_dir, args.source_label_dir)

    # Criar arquivo YAML
    yaml_path = manager.create_data_yaml()

    logger.info(
        f"Preparação de dataset concluída:"
        f" {split_counts.get('train', 0)} treino,"
        f" {split_counts.get('val', 0)} validação,"
        f" {split_counts.get('test', 0)} teste"
    )
    logger.info(f"Arquivo de configuração criado: {yaml_path}")


def handle_train(args):
    """Manipular comando de treinamento."""
    logger.info(f"Iniciando treinamento com dados de {args.dataset_dir}")

    # Preparar data.yaml se não fornecido
    data_yaml = args.data_yaml
    if not data_yaml:
        manager = DatasetManager(args.dataset_dir)
        data_yaml = manager.create_data_yaml()

    trainer = YOLOTrainer(
        model_size=args.model_size,
        epochs=args.epochs,
        batch_size=args.batch_size,
        image_size=args.image_size,
        pretrained=not args.no_pretrained,
        output_dir=args.output_dir,
    )

    # Treinar o modelo
    if args.resume:
        logger.info(f"Retomando treinamento a partir de {args.resume}")
        results = trainer.resume_training(args.resume, data_yaml)
    elif args.find_hyperparams:
        logger.info("Iniciando busca por hiperparâmetros")
        best_config = trainer.find_best_hyperparameters(data_yaml)
        logger.info(f"Melhores hiperparâmetros encontrados: {best_config}")
    else:
        results = trainer.train(data_yaml)

    logger.info("Treinamento concluído")


def handle_evaluate(args):
    """Manipular comando de avaliação."""
    logger.info(f"Iniciando avaliação do modelo {args.model_path}")

    # Preparar data.yaml se não fornecido
    data_yaml = args.data_yaml
    if not data_yaml:
        data_yaml = os.path.join(args.dataset_dir, "data.yaml")
        if not os.path.exists(data_yaml):
            manager = DatasetManager(args.dataset_dir)
            data_yaml = manager.create_data_yaml()

    evaluator = ModelEvaluator(args.output_dir)

    # Avaliar modelo
    metrics = evaluator.evaluate_model(args.model_path, data_yaml)

    # Gerar relatórios
    report_paths = evaluator.generate_report(metrics, args.model_path)

    # Gerar matriz de confusão se solicitado
    if args.confusion_matrix:
        conf_matrix_path = evaluator.confusion_matrix(args.model_path, data_yaml)
        if conf_matrix_path:
            report_paths["confusion_matrix"] = conf_matrix_path

    logger.info(f"Avaliação concluída. Precisão (mAP50): {metrics['metricas_gerais']['Precisão (mAP50)']:.4f}")
    logger.info(f"Relatórios salvos em: {args.output_dir or evaluator.output_dir}")


def handle_model_comparison(args):
    """Manipular comando de comparação de modelos."""
    logger.info(f"Iniciando comparação de modelos: {args.model_paths}")

    # Separar lista de modelos
    model_paths = args.model_paths.split(",")

    # Validar que os modelos existem
    for model_path in model_paths:
        if not os.path.exists(model_path):
            logger.error(f"Modelo não encontrado: {model_path}")
            return

    # Verificar arquivo data.yaml
    if not os.path.exists(args.data_yaml):
        logger.error(f"Arquivo data.yaml não encontrado: {args.data_yaml}")
        return

    # Criar diretório de saída se fornecido
    output_dir = args.output_dir or os.path.join("reports", "model_comparison", datetime.now().strftime("%Y%m%d_%H%M%S"))
    os.makedirs(output_dir, exist_ok=True)

    try:
        # Instanciar comparador de modelos
        from microdetect.training.model_comparison import ModelComparator

        comparator = ModelComparator(output_dir)

        # Executar comparação
        results = comparator.compare_models(
            model_paths=model_paths,
            data_yaml=args.data_yaml,
            conf_threshold=args.conf_threshold,
            iou_threshold=args.iou_threshold,
        )

        # Gerar dashboard interativo se solicitado
        if args.dashboard:
            from microdetect.visualization.dashboards import DashboardGenerator

            dashboard = DashboardGenerator(output_dir)
            port = dashboard.create_model_comparison_dashboard(results)

            logger.info(f"Dashboard iniciado em: http://localhost:{port}")

        logger.info(f"Comparação de modelos concluída. Resultados salvos em: {output_dir}")

    except Exception as e:
        logger.error(f"Erro durante a comparação de modelos: {str(e)}")


def handle_batch_detect(args):
    """Manipular comando de detecção em lote."""
    logger.info(f"Iniciando processamento em lote com modelo: {args.model_path}")

    # Verificar se o modelo existe
    if not os.path.exists(args.model_path):
        logger.error(f"Modelo não encontrado: {args.model_path}")
        return

    # Verificar diretório de origem
    if not os.path.exists(args.source):
        logger.error(f"Diretório de origem não encontrado: {args.source}")
        return

    # Definir diretório de saída
    output_dir = args.output_dir or os.path.join("runs", "detect", datetime.now().strftime("%Y%m%d_%H%M%S"))

    try:
        # Instanciar processador em lote
        from microdetect.analysis.batch_processing import BatchProcessor

        processor = BatchProcessor()

        # Executar processamento em lote
        results = processor.process_batch(
            model_path=args.model_path,
            source_dir=args.source,
            output_dir=output_dir,
            batch_size=args.batch_size,
            conf_threshold=args.conf_threshold,
            save_txt=args.save_txt,
            save_img=args.save_img,
            save_json=args.save_json,
        )

        logger.info(f"Processamento em lote concluído: {results['processed']}/{results['total']} imagens processadas")
        logger.info(f"Resultados salvos em: {output_dir}")

    except Exception as e:
        logger.error(f"Erro durante o processamento em lote: {str(e)}")


def handle_visualize_detections(args):
    """Manipular comando de visualização interativa de detecções."""
    logger.info(f"Iniciando visualização interativa com modelo: {args.model_path}")

    # Verificar se o modelo existe
    if not os.path.exists(args.model_path):
        logger.error(f"Modelo não encontrado: {args.model_path}")
        return

    # Verificar diretório de origem
    if not os.path.exists(args.source):
        logger.error(f"Diretório de imagens não encontrado: {args.source}")
        return

    try:
        # Instanciar visualizador de detecções
        from microdetect.visualization.detection_viz import DetectionVisualizer

        visualizer = DetectionVisualizer()

        # Iniciar visualização interativa
        visualizer.visualize_interactive(model_path=args.model_path, image_dir=args.source, conf_threshold=args.conf_threshold)

        logger.info("Visualização interativa finalizada")

    except Exception as e:
        logger.error(f"Erro durante a visualização interativa: {str(e)}")


def handle_analyze_errors(args):
    """Manipular comando de análise de erros."""
    logger.info(f"Iniciando análise de erros para o modelo: {args.model_path}")

    # Verificar se o modelo existe
    if not os.path.exists(args.model_path):
        logger.error(f"Modelo não encontrado: {args.model_path}")
        return

    # Verificar arquivo data.yaml
    if not os.path.exists(args.data_yaml):
        logger.error(f"Arquivo data.yaml não encontrado: {args.data_yaml}")
        return

    # Verificar diretório do dataset
    if not os.path.exists(args.dataset_dir):
        logger.error(f"Diretório do dataset não encontrado: {args.dataset_dir}")
        return

    # Definir diretório de saída
    output_dir = args.output_dir or os.path.join("reports", "error_analysis", datetime.now().strftime("%Y%m%d_%H%M%S"))

    try:
        # Instanciar analisador de erros
        from microdetect.analysis.error_analysis import ErrorAnalyzer

        analyzer = ErrorAnalyzer(output_dir)

        # Executar análise de erros
        results = analyzer.analyze_errors(
            model_path=args.model_path,
            data_yaml=args.data_yaml,
            dataset_dir=args.dataset_dir,
            error_type=args.error_type,
        )

        # Exibir resultados
        for error_type, count in results["error_counts"].items():
            logger.info(f"{error_type.replace('_', ' ').title()}: {count}")

        logger.info(f"Análise de erros concluída. Resultados salvos em: {output_dir}")

    except Exception as e:
        logger.error(f"Erro durante a análise de erros: {str(e)}")


def handle_generate_report(args):
    """Manipular comando de geração de relatórios."""
    logger.info(f"Iniciando geração de relatório para os resultados em: {args.results_dir}")

    # Verificar diretório de resultados
    if not os.path.exists(args.results_dir):
        logger.error(f"Diretório de resultados não encontrado: {args.results_dir}")
        return

    # Definir arquivo de saída
    if not args.output_file:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        extension = ".pdf" if args.format == "pdf" else f".{args.format}"
        args.output_file = os.path.join("reports", f"report_{timestamp}{extension}")

    # Criar diretório de saída se necessário
    os.makedirs(os.path.dirname(os.path.abspath(args.output_file)), exist_ok=True)

    try:
        # Instanciar gerador de relatórios
        from microdetect.visualization.reporting import ReportGenerator

        # Preparar lista de imagens para incluir no relatório
        include_images = []
        if args.include_images:
            include_images = args.include_images.split(",")
            # Verificar se as imagens existem
            for img_path in include_images:
                if not os.path.exists(img_path):
                    logger.warning(f"Imagem não encontrada: {img_path}")

        # Carregar métricas do arquivo JSON
        metrics_file = None
        for file in os.listdir(args.results_dir):
            if file.endswith(".json") and ("metrics" in file or "report" in file):
                metrics_file = os.path.join(args.results_dir, file)
                break

        if not metrics_file:
            logger.error("Arquivo de métricas não encontrado no diretório de resultados")
            return

        with open(metrics_file, "r") as f:
            metrics = json.load(f)

        # Determinar caminho do modelo (pode estar no arquivo JSON)
        model_path = metrics.get("modelo", {}).get("caminho", "unknown_model")

        # Gerar relatório no formato solicitado
        generator = ReportGenerator(os.path.dirname(args.output_file))

        if args.format == "pdf":
            report_path = generator.generate_pdf_report(
                metrics=metrics, model_path=model_path, output_file=args.output_file, include_images=include_images
            )
        elif args.format == "csv":
            report_path = generator.generate_csv_report(metrics=metrics, output_file=args.output_file)
        else:  # json
            # Copiar o arquivo JSON existente com eventuais modificações
            with open(args.output_file, "w") as f:
                json.dump(metrics, f, indent=4)
            report_path = args.output_file

        logger.info(f"Relatório gerado com sucesso: {report_path}")

    except Exception as e:
        logger.error(f"Erro durante a geração do relatório: {str(e)}")


def handle_dashboard(args):
    """Manipular comando de dashboard interativo."""
    logger.info(f"Iniciando dashboard para os resultados em: {args.results_dir}")

    # Verificar diretório de resultados
    if not os.path.exists(args.results_dir):
        logger.error(f"Diretório de resultados não encontrado: {args.results_dir}")
        return

    # Verificar se há arquivos JSON no diretório
    json_files = [f for f in os.listdir(args.results_dir) if f.endswith(".json")]
    if not json_files:
        logger.error(f"Nenhum arquivo JSON encontrado em: {args.results_dir}")
        return

    try:
        # Instanciar gerador de dashboard
        from microdetect.visualization.dashboards import DashboardGenerator

        generator = DashboardGenerator(args.results_dir)

        # Iniciar o dashboard
        port = generator.create_detection_dashboard(
            results_dir=args.results_dir, port=args.port, open_browser=not args.no_browser
        )

        logger.info(f"Dashboard iniciado em: http://localhost:{port}")
        logger.info("Pressione Ctrl+C para encerrar o dashboard")

        # O dashboard já está rodando em um servidor, só precisamos manter o programa rodando
        # até o usuário interromper com Ctrl+C
        try:
            # Aguardar indefinidamente (até Ctrl+C)
            import signal

            signal.pause()
        except (KeyboardInterrupt, SystemExit):
            logger.info("Dashboard encerrado pelo usuário")

    except Exception as e:
        logger.error(f"Erro ao iniciar o dashboard: {str(e)}")


def main(args: Optional[List[str]] = None):
    """
    Ponto de entrada principal para o CLI.

    Args:
        args: Lista de argumentos da linha de comando (opcional)
    """
    # Criar parser principal
    parser = argparse.ArgumentParser(
        description=f"{BRIGHT}{INFO}MicroDetect{RESET}: Detecção de Microorganismos com YOLOv8",
        formatter_class=ColoredHelpFormatter,
        epilog=get_logo_with_name_ascii(),
    )
    subparsers = parser.add_subparsers(dest="command", help="Comandos disponíveis")

    # Registrar parsers para cada comando
    setup_init_parser(subparsers)
    setup_convert_parser(subparsers)
    setup_annotate_parser(subparsers)
    setup_visualize_parser(subparsers)
    setup_augment_parser(subparsers)
    setup_dataset_parser(subparsers)
    setup_train_parser(subparsers)
    setup_evaluate_parser(subparsers)
    setup_update_parser(subparsers)
    setup_aws_parser(subparsers)
    setup_docs_parser(subparsers)
    setup_install_docs_parser(subparsers)
    # Adicionar os novos parsers
    setup_model_comparison_parser(subparsers)
    setup_batch_detect_parser(subparsers)
    setup_visualize_detections_parser(subparsers)
    setup_analyze_errors_parser(subparsers)
    setup_generate_report_parser(subparsers)
    setup_dashboard_parser(subparsers)

    # Adicionar versão e ajuda
    parser.add_argument(
        "--version", action=ColoredVersionAction, version=__version__, help="mostrar versão do programa e sair"
    )

    # Analisar argumentos
    parsed_args = parser.parse_args(args)

    if parsed_args.command not in ["update", "setup-aws"]:
        from microdetect.updater import UpdateManager

        # Verificar se há atualizações disponíveis
        update_result = UpdateManager.check_for_updates_before_command()

        # Se uma atualização foi instalada, podemos encerrar
        if update_result:
            return

    try:
        if parsed_args.command == "init":
            handle_init(parsed_args)
        elif parsed_args.command == "convert":
            handle_convert(parsed_args)
        elif parsed_args.command == "annotate":
            handle_annotate(parsed_args)
        elif parsed_args.command == "visualize":
            handle_visualize(parsed_args)
        elif parsed_args.command == "augment":
            handle_augment(parsed_args)
        elif parsed_args.command == "dataset":
            handle_dataset(parsed_args)
        elif parsed_args.command == "train":
            handle_train(parsed_args)
        elif parsed_args.command == "evaluate":
            handle_evaluate(parsed_args)
        elif parsed_args.command == "update":
            handle_update(parsed_args)
        elif parsed_args.command == "setup-aws":
            handle_setup_aws(parsed_args)
        elif parsed_args.command == "docs":
            handle_docs(parsed_args)
        elif parsed_args.command == "install-docs":
            handle_install_docs(parsed_args)
        # Adicionar os novos handlers
        elif parsed_args.command == "compare_models":
            handle_model_comparison(parsed_args)
        elif parsed_args.command == "batch_detect":
            handle_batch_detect(parsed_args)
        elif parsed_args.command == "visualize_detections":
            handle_visualize_detections(parsed_args)
        elif parsed_args.command == "analyze_errors":
            handle_analyze_errors(parsed_args)
        elif parsed_args.command == "generate_report":
            handle_generate_report(parsed_args)
        elif parsed_args.command == "dashboard":
            handle_dashboard(parsed_args)
        else:
            parser.print_help()
            return

    except KeyboardInterrupt:
        logger.info("Operação interrompida pelo usuário")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Erro: {str(e)}", exc_info=True)
        sys.exit(1)
