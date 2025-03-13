"""
Interface de linha de comando para o projeto MicroDetect.
"""

import argparse
import logging
import os
import sys
from getpass import getpass
from typing import List, Optional, Set, Tuple

from microdetect import __version__
from microdetect.annotation.annotator import ImageAnnotator
from microdetect.annotation.visualization import AnnotationVisualizer
from microdetect.data.augmentation import DataAugmenter
from microdetect.data.conversion import ImageConverter
from microdetect.data.dataset import DatasetManager
from microdetect.training.evaluate import ModelEvaluator
from microdetect.training.train import YOLOTrainer
from microdetect.utils import AWSSetupManager, ColoredHelpFormatter, ColoredVersionAction, get_logo_with_name_ascii
from microdetect.utils.colors import BRIGHT, ERROR, INFO, RESET, SUCCESS, WARNING
from microdetect.utils.docs_server import DEFAULT_LANGUAGE, LANGUAGES
from microdetect.utils import convert_annotation

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
    parser.add_argument("--classes", help="Lista de classes separadas por vírgula (ex: '0-levedura,1-fungo')")
    parser.add_argument("--auto_save", action="store_true", default=True, help="Ativar salvamento automático (padrão: True)")
    parser.add_argument("--auto_save_interval", type=int, default=300, help="Intervalo em segundos entre salvamentos automáticos (padrão: 300)")
    parser.add_argument("--resume", action="store_true", help="Retomar a partir da última imagem anotada")


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
    parser.add_argument("--batch", action="store_true", help="Processar em lote sem interface interativa")


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
        "--directory",
        "-d",
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


def setup_format_convert_parser(subparsers):
    """Configurar parser para comando de conversão entre formatos de anotação."""
    parser = subparsers.add_parser("format-convert", help="Converter entre formatos de anotação")
    parser.add_argument("--input_dir", required=True, help="Diretório contendo os arquivos de anotação a serem convertidos")
    parser.add_argument("--image_dir", required=True, help="Diretório contendo as imagens correspondentes")
    parser.add_argument("--output_dir", required=True, help="Diretório para salvar os arquivos convertidos")
    parser.add_argument(
        "--from_format",
        required=True,
        choices=["yolo", "pascal_voc", "coco", "csv"],
        help="Formato de origem das anotações"
    )
    parser.add_argument(
        "--to_format",
        required=True,
        choices=["yolo", "pascal_voc", "coco", "csv"],
        help="Formato de destino para as anotações"
    )
    parser.add_argument("--classes", help="Lista de classes separadas por vírgula (ex: '0-levedura,1-fungo')")


def setup_backup_parser(subparsers):
    """Configurar parser para comando de backup de anotações."""
    parser = subparsers.add_parser("backup", help="Criar backup de anotações")
    parser.add_argument("--label_dir", required=True, help="Diretório contendo os arquivos de anotação a serem copiados")
    parser.add_argument("--output_dir", help="Diretório para salvar o backup (se omitido, cria um diretório com timestamp)")


def handle_install_docs(args):
    """
    Manipula o comando de instalação de documentação.
    Copia os arquivos da documentação para a pasta do usuário (.microdetect/docs).
    """
    import shutil
    import sys
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
    from microdetect.utils.docs_server import find_docs_dir

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
        from microdetect.utils.docs_server import (
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
            import microdetect.utils.docs_server as docs_server

            docs_server.PORT = args.port

        if args.no_browser:

            def do_nothing(url):
                print(f"Servidor de documentação iniciado em {url}")
                print("Acesse o URL acima no seu navegador para ver a documentação.")
                print("Pressione Ctrl+C para parar o servidor.")

            import microdetect.utils.docs_server as docs_server

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
    from microdetect.utils.updater import UpdateManager

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

    target_dir = os.path.abspath(args.directory)
    logger.info(f"Inicializando ambiente MicroDetect em: {target_dir}")

    # Verificar/criar o diretório
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)
        logger.info(f"Diretório criado: {target_dir}")

    # Caminho para o arquivo de configuração
    config_path = os.path.join(target_dir, "config.yaml")

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
        os.path.join(target_dir, "data", "images"),
        os.path.join(target_dir, "data", "labels"),
        os.path.join(target_dir, "dataset"),
        os.path.join(target_dir, "runs", "train"),
        os.path.join(target_dir, "reports"),
    ]

    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            logger.info(f"Diretório criado: {directory}")

    logger.info(
        f"""
Ambiente MicroDetect inicializado com sucesso!

Para começar:

1. Adicione suas imagens em:        {os.path.join(target_dir, 'data', 'images')}
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

    # Validar diretórios
    if not os.path.isdir(args.image_dir):
        logger.error(f"Diretório de imagens não encontrado: {args.image_dir}")
        sys.exit(1)

    os.makedirs(args.output_dir, exist_ok=True)

    # Processar classes se fornecidas
    classes = None
    if args.classes:
        classes = args.classes.split(",")

    # Criar anotador
    annotator = ImageAnnotator(
        classes=classes,
        auto_save=args.auto_save,
        auto_save_interval=args.auto_save_interval
    )

    # Executar anotação em lote
    total_images, total_annotated = annotator.batch_annotate(
        args.image_dir,
        args.output_dir
    )

    # Exibir resumo
    logger.info(f"Anotação concluída: {total_annotated}/{total_images} imagens")


def handle_visualize(args):
    """Manipular comando de visualização."""
    logger.info(f"Iniciando visualização de anotações para imagens em {args.image_dir}")

    # Validar diretórios
    if not os.path.isdir(args.image_dir):
        logger.error(f"Diretório de imagens não encontrado: {args.image_dir}")
        sys.exit(1)

    if args.label_dir and not os.path.isdir(args.label_dir):
        logger.error(f"Diretório de anotações não encontrado: {args.label_dir}")
        sys.exit(1)

    # Processar filtro de classes se fornecido
    filter_classes = None
    if args.filter_classes:
        filter_classes = set(args.filter_classes.split(","))

    # Criar visualizador
    visualizer = AnnotationVisualizer()

    # Executar visualização
    if args.batch or args.output_dir:
        # Modo batch - salvar imagens
        out_dir = args.output_dir or "annotated_images"
        os.makedirs(out_dir, exist_ok=True)

        saved_count = visualizer.save_annotated_images(
            args.image_dir,
            args.label_dir,
            out_dir,
            filter_classes
        )

        logger.info(f"Visualização em lote concluída: {saved_count} imagens salvas em {out_dir}")
    else:
        # Modo interativo
        visualizer.visualize_annotations(
            args.image_dir,
            args.label_dir,
            None,
            filter_classes
        )

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


def handle_format_convert(args):
    """Manipular comando de conversão entre formatos de anotação."""
    logger.info(f"Iniciando conversão de anotações de {args.from_format} para {args.to_format}")

    # Validar diretórios
    if not os.path.isdir(args.input_dir):
        logger.error(f"Diretório de entrada não encontrado: {args.input_dir}")
        sys.exit(1)

    if not os.path.isdir(args.image_dir):
        logger.error(f"Diretório de imagens não encontrado: {args.image_dir}")
        sys.exit(1)

    os.makedirs(args.output_dir, exist_ok=True)

    # Processar classes se fornecidas
    class_map = None
    if args.classes:
        class_list = args.classes.split(",")
        class_map = {}
        for cls in class_list:
            parts = cls.split("-", 1)
            if len(parts) == 2:
                class_map[parts[0]] = parts[1]

    # Executar conversão
    try:
        if args.from_format == "yolo":
            if args.to_format == "pascal_voc":
                count = convert_annotation.yolo_to_pascal_voc(
                    args.input_dir,
                    args.image_dir,
                    args.output_dir,
                    class_map
                )
                logger.info(f"Conversão concluída: {count} arquivos convertidos de YOLO para Pascal VOC")

            elif args.to_format == "coco":
                output_json = os.path.join(args.output_dir, "annotations.json")
                coco_data = convert_annotation.yolo_to_coco(
                    args.input_dir,
                    args.image_dir,
                    output_json,
                    class_map
                )
                logger.info(f"Conversão concluída: {len(coco_data['images'])} imagens convertidas de YOLO para COCO")

            elif args.to_format == "csv":
                output_csv = os.path.join(args.output_dir, "annotations.csv")
                count = convert_annotation.yolo_to_csv(
                    args.input_dir,
                    args.image_dir,
                    output_csv,
                    class_map
                )
                logger.info(f"Conversão concluída: {count} anotações convertidas de YOLO para CSV")

        elif args.from_format == "pascal_voc":
            if args.to_format == "yolo":
                count = convert_annotation.pascal_voc_to_yolo(
                    args.input_dir,
                    args.image_dir,
                    args.output_dir,
                    class_map
                )
                logger.info(f"Conversão concluída: {count} arquivos convertidos de Pascal VOC para YOLO")

        elif args.from_format == "coco":
            if args.to_format == "yolo":
                # Procurar arquivo JSON no diretório de entrada
                json_files = [f for f in os.listdir(args.input_dir) if f.endswith('.json')]
                if not json_files:
                    logger.error("Nenhum arquivo JSON encontrado no diretório de entrada")
                    sys.exit(1)

                json_file = os.path.join(args.input_dir, json_files[0])
                count = convert_annotation.coco_to_yolo(
                    json_file,
                    args.output_dir,
                    class_map
                )
                logger.info(f"Conversão concluída: {count} imagens convertidas de COCO para YOLO")

        elif args.from_format == "csv":
            if args.to_format == "yolo":
                # Procurar arquivo CSV no diretório de entrada
                csv_files = [f for f in os.listdir(args.input_dir) if f.endswith('.csv')]
                if not csv_files:
                    logger.error("Nenhum arquivo CSV encontrado no diretório de entrada")
                    sys.exit(1)

                csv_file = os.path.join(args.input_dir, csv_files[0])
                count = convert_annotation.csv_to_yolo(
                    csv_file,
                    args.output_dir,
                    class_map
                )
                logger.info(f"Conversão concluída: {count} imagens convertidas de CSV para YOLO")

        else:
            logger.error(f"Conversão de {args.from_format} para {args.to_format} não suportada")
            sys.exit(1)
    except Exception as e:
        logger.error(f"Erro durante a conversão: {str(e)}")
        sys.exit(1)


def handle_backup(args):
    """Manipular comando de backup de anotações."""
    logger.info(f"Iniciando backup de anotações em {args.label_dir}")

    # Validar diretório
    if not os.path.isdir(args.label_dir):
        logger.error(f"Diretório de anotações não encontrado: {args.label_dir}")
        sys.exit(1)

    # Criar anotador (apenas para usar a função de backup)
    annotator = ImageAnnotator()

    # Configurar diretório de saída se especificado
    output_dir = args.output_dir

    # Executar backup
    backup_dir = annotator.backup_annotations(args.label_dir)

    if backup_dir:
        logger.info(f"Backup criado com sucesso em: {backup_dir}")
    else:
        logger.error("Falha ao criar backup")
        sys.exit(1)


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
    setup_format_convert_parser(subparsers)
    setup_backup_parser(subparsers)

    # Adicionar versão e ajuda
    parser.add_argument(
        "--version", action=ColoredVersionAction, version=__version__, help="mostrar versão do programa e sair"
    )

    # Analisar argumentos
    parsed_args = parser.parse_args(args)

    if parsed_args.command not in ["update", "setup-aws"]:
        from microdetect.utils.updater import UpdateManager

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
        elif parsed_args.command == "format-convert":
            handle_format_convert(parsed_args)
        elif parsed_args.command == "backup":
            handle_backup(parsed_args)
        else:
            parser.print_help()
            return

    except KeyboardInterrupt:
        logger.info("Operação interrompida pelo usuário")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Erro: {str(e)}", exc_info=True)
        sys.exit(1)