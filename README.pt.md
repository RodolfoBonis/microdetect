# MicroDetect

<div align="center">

![MicroDetect Logo](https://img.shields.io/badge/MicroDetect-Detecção%20de%20Microorganismos-blue?style=for-the-badge&logo=data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IiNmZmZmZmYiIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIj48Y2lyY2xlIGN4PSIxMiIgY3k9IjEyIiByPSIxMCIvPjxjaXJjbGUgY3g9IjEyIiBjeT0iMTIiIHI9IjYiLz48L3N2Zz4=)

[![Versão](https://img.shields.io/badge/versão-1.0.0-blue.svg)](https://github.com/RodolfoBonis/microdetect)
[![Python](https://img.shields.io/badge/python-3.9%20%7C%203.10%20%7C%203.11%20%7C%203.12-blue.svg)](https://www.python.org/)
[![Licença](https://img.shields.io/badge/licença-MIT-green.svg)](LICENSE)
[![Documentação](https://img.shields.io/badge/docs-disponível-brightgreen.svg)](docs/en/index.md)

*Read in [English](README.md)*

</div>

## Visão Geral

**MicroDetect** é um kit de ferramentas completo para detecção e classificação de microorganismos em imagens de microscopia usando YOLOv8. Ele simplifica todo o processo, desde a preparação de imagens até a avaliação de modelos.

<div align="center">
<img src="https://img.shields.io/badge/YOLOv8-Powered-blue?style=for-the-badge" alt="Powered by YOLOv8"/>
</div>

## 🔑 Recursos Principais

- 📷 **Conversão de Imagens** - Transforme imagens TIFF de microscopia em formatos otimizados
- 🏷️ **Anotação Inteligente** - Interface amigável com sessões que podem ser retomadas
- 📊 **Gerenciamento de Dados** - Organize e prepare seus datasets de forma eficiente
- 🔄 **Augmentação de Dados** - Melhore datasets com técnicas avançadas de transformação
- 🧠 **Treinamento de Modelos** - Treine modelos YOLOv8 personalizados com gestão de checkpoints
- 📈 **Avaliação de Desempenho** - Métricas e visualizações abrangentes
- 🔄 **Atualizações Automáticas** - Atualizações transparentes via AWS CodeArtifact

## 🦠 Microorganismos Suportados

- **Leveduras**
- **Fungos**
- **Micro-algas**
- **Classes Customizadas** - Facilmente configurável para outros tipos de microorganismos

## 📋 Início Rápido

### Instalação

```bash
# Clone o repositório
git clone https://github.com/RodolfoBonis/microdetect.git
cd microdetect

# Instale com o script (recomendado)
chmod +x scripts/install_production.sh
./scripts/install_production.sh --virtual-env
```

### Inicializar Projeto

```bash
mkdir meu_projeto
cd meu_projeto
microdetect init
```

### Fluxo de Trabalho Básico

```bash
# Converter imagens TIFF para PNG
microdetect convert --input_dir data/imagens_raw --output_dir data/images --use_opencv

# Anotar imagens
microdetect annotate --image_dir data/images --output_dir data/labels

# Preparar dataset
microdetect dataset --source_img_dir data/images --source_label_dir data/labels

# Treinar modelo
microdetect train --dataset_dir dataset --model_size s --epochs 100

# Avaliar modelo
microdetect evaluate --model_path runs/train/yolov8_s_custom/weights/best.pt --dataset_dir dataset
```

## 📚 Documentação

Para informações detalhadas, consulte nossa documentação:

- [Guia de Instalação](docs/pt/installation_guide.md) - Instruções detalhadas de instalação
- [Solução de Problemas](docs/en/troubleshooting.md) - Soluções para problemas comuns
- [Configuração Avançada](docs/en/advanced_configuration.md) - Personalize o MicroDetect para suas necessidades
- [Guia de Desenvolvimento](docs/en/development_guide.md) - Contribua com o MicroDetect

Navegue por toda a documentação com o servidor de documentação integrado:

```bash
microdetect docs
```

## 🛠️ Estrutura do Projeto

```
microdetect/
├── annotation/        # Ferramentas de anotação de imagens
├── data/              # Módulos de processamento de dados
├── training/          # Treinamento e avaliação de modelos
└── utils/             # Funções utilitárias e configuração
```

## 🧪 Testes

Execute a suite de testes abrangente:

```bash
# Instale as dependências de teste
pip install pytest pytest-cov

# Execute os testes com relatório de cobertura
pytest --cov=microdetect
```

## 🙏 Contribuindo

Contribuições são bem-vindas! Veja [CONTRIBUTING.md](CONTRIBUTING.md) para diretrizes.

## 📄 Licença

Este projeto está licenciado sob a Licença MIT - veja o arquivo [LICENSE](LICENSE) para detalhes.

## 📞 Contato e Suporte

- GitHub Issues: [https://github.com/RodolfoBonis/microdetect/issues](https://github.com/RodolfoBonis/microdetect/issues)
- Email: dev@rodolfodebonis.com.br