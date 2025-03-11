# Documentação do MicroDetect

Bem-vindo ao portal de documentação do MicroDetect. Este site fornece informações abrangentes sobre instalação, uso e desenvolvimento do pacote MicroDetect.

## O que é o MicroDetect?

MicroDetect é uma ferramenta completa para detecção e classificação de microorganismos em imagens de microscopia utilizando YOLOv8. Este projeto fornece uma pipeline completa desde a conversão de imagens, anotação manual com sistema de retomada, augmentação de dados, treinamento com checkpoints até avaliação de modelos.

## Começando

Se você é novo no MicroDetect, recomendamos começar com os seguintes guias:

- [Guia de Instalação](installation_guide.md) - Instruções para instalar o MicroDetect
- [Tutorial de Início Rápido](troubleshooting.md) - Comece a usar o MicroDetect rapidamente

## Principais Recursos

- **Conversão de Imagens**: Converte imagens TIFF para formatos adequados ao processamento
- **Anotação Manual**: Interface gráfica para marcação de microorganismos com capacidade de retomada
- **Visualização**: Visualiza anotações existentes em imagens
- **Augmentação de Dados**: Melhora seu conjunto de dados com técnicas de augmentação
- **Preparação de Dataset**: Divide e organiza dados para treinamento/validação/teste
- **Treinamento de Modelos**: Treina modelos YOLOv8 personalizados com sistema de checkpoints
- **Avaliação**: Avalia modelos com métricas detalhadas e relatórios visuais
- **Atualizações Automáticas**: Verifica e instala atualizações a partir do AWS CodeArtifact

## Estrutura da Documentação

A documentação está organizada nas seguintes seções:

### Começando
Informações básicas para começar com o MicroDetect, incluindo instalação e solução de problemas.

### Atualizações
Informações sobre o sistema de atualização, configuração do AWS CodeArtifact e modelo de releases.

### Configuração
Opções avançadas de configuração para personalizar o comportamento do MicroDetect.

### Desenvolvimento
Guias para desenvolvedores que desejam contribuir com o projeto MicroDetect.

## Interface de Linha de Comando

O MicroDetect fornece uma interface de linha de comando abrangente. Aqui estão alguns comandos comuns:

```bash
# Inicializar um novo projeto
microdetect init

# Converter imagens TIFF para PNG
microdetect convert --input_dir data/raw_images --output_dir data/images

# Anotar imagens
microdetect annotate --image_dir data/images --output_dir data/labels

# Preparar dataset
microdetect dataset --source_img_dir data/images --source_label_dir data/labels

# Treinar modelo
microdetect train --dataset_dir dataset --model_size s --epochs 100

# Verificar atualizações
microdetect update --check-only

# Mostrar esta documentação
microdetect docs
```

Para informações mais detalhadas sobre cada comando, consulte as respectivas páginas de documentação ou use a flag `--help` com qualquer comando.

## Suporte

Se você encontrar algum problema ou tiver dúvidas não abordadas na documentação, por favor:

1. Consulte o guia de [Solução de Problemas](troubleshooting.md)
2. Abra uma issue no [GitHub](https://github.com/RodolfoBonis/microdetect/issues)
3. Entre em contato conosco pelo e-mail dev@rodolfodebonis.com.br