# Guia de Conversão de Imagens

Este guia explica como usar as ferramentas de conversão de imagens do MicroDetect para preparar imagens de microscopia para análise e detecção ideais.

## Sumário
- [Introdução](#introdução)
- [Formatos de Imagem Suportados](#formatos-de-imagem-suportados)
- [Conversão Básica de Imagens](#conversão-básica-de-imagens)
- [Opções Avançadas de Conversão](#opções-avançadas-de-conversão)
  - [Seleção de Formato](#seleção-de-formato)
  - [Configurações de Qualidade](#configurações-de-qualidade)
  - [Redimensionamento de Imagens](#redimensionamento-de-imagens)
  - [Preservação de Metadados](#preservação-de-metadados)
  - [Usando OpenCV vs PIL](#usando-opencv-vs-pil)
- [Processamento em Lote](#processamento-em-lote)
- [Conversão de 16 bits para 8 bits](#conversão-de-16-bits-para-8-bits)
- [Lidando com Formatos Especiais de Microscopia](#lidando-com-formatos-especiais-de-microscopia)
  - [Arquivos TIFF Multi-página](#arquivos-tiff-multi-página)
  - [Z-stacks](#z-stacks)
  - [Séries Temporais](#séries-temporais)
- [Integração com Pré-processamento](#integração-com-pré-processamento)
- [Configuração](#configuração)
- [Melhores Práticas](#melhores-práticas)
- [Solução de Problemas](#solução-de-problemas)

## Introdução

Imagens de microscopia frequentemente vêm em formatos especializados (como TIFF) com alta profundidade de bits que não são otimamente compatíveis com fluxos de trabalho de aprendizado profundo. O MicroDetect fornece ferramentas para converter essas imagens para formatos mais adequados para detecção de microorganismos, preservando detalhes importantes.

As ferramentas de conversão de imagem ajudam você a:
- Converter formatos especializados de microscopia para formatos padrão
- Normalizar profundidade de bits (por exemplo, de 16 bits para 8 bits)
- Otimizar a eficiência de armazenamento e processamento de imagens
- Preparar imagens para treinamento e inferência
- Aplicar pré-processamento básico durante a conversão

## Formatos de Imagem Suportados

**Formatos de Entrada**:
- TIFF (.tif, .tiff) - incluindo multi-página e alta profundidade de bits
- BMP (.bmp)
- JPEG (.jpg, .jpeg)
- PNG (.png)
- GIF (.gif)
- Vários formatos específicos de microscopia (com dependências opcionais)

**Formatos de Saída**:
- PNG (.png) - padrão, sem perdas com boa compressão
- JPEG (.jpg) - com perdas com qualidade configurável
- TIFF (.tif) - para casos onde a preservação de dados específicos é necessária

## Conversão Básica de Imagens

Para converter imagens de um formato para outro:

```bash
microdetect convert --input_dir caminho/para/imagens_entrada --output_dir caminho/para/imagens_saida
```

Este comando:
- Processa todas as imagens suportadas no diretório de entrada
- Converte-as para o formato PNG por padrão
- Salva as imagens convertidas no diretório de saída
- Preserva o nome do arquivo original com a nova extensão

## Opções Avançadas de Conversão

### Seleção de Formato

Para especificar o formato de saída:

```bash
microdetect convert --input_dir caminho/para/imagens_entrada --output_dir caminho/para/imagens_saida --format jpg
```

Valores de formato suportados:
- `png` - Formato sem perdas, bom para preservação de detalhes (padrão)
- `jpg` - Tamanho de arquivo menor, compressão com perdas
- `tif` - Para preservar camadas de dados adicionais

### Configurações de Qualidade

Para o formato JPEG, você pode definir a qualidade de compressão:

```bash
microdetect convert --input_dir caminho/para/imagens_entrada --output_dir caminho/para/imagens_saida --format jpg --quality 90
```

O parâmetro de qualidade varia de 1 (menor qualidade, menor arquivo) a 100 (maior qualidade, maior arquivo). O padrão é 95.

### Redimensionamento de Imagens

Para redimensionar imagens durante a conversão:

```bash
microdetect convert --input_dir caminho/para/imagens_entrada --output_dir caminho/para/imagens_saida --resize --max_size 1024 1024
```

Isso redimensiona as imagens para se ajustarem às dimensões especificadas, mantendo a proporção. O parâmetro `--max_size` aceita valores de largura e altura.

### Preservação de Metadados

Por padrão, o MicroDetect tenta preservar metadados EXIF durante a conversão:

```bash
microdetect convert --input_dir caminho/para/imagens_entrada --output_dir caminho/para/imagens_saida --preserve_metadata
```

Para desabilitar a preservação de metadados:

```bash
microdetect convert --input_dir caminho/para/imagens_entrada --output_dir caminho/para/imagens_saida --no-preserve_metadata
```

### Usando OpenCV vs PIL

O MicroDetect suporta dois backends de processamento de imagem:

```bash
# Usar OpenCV (melhor para imagens científicas)
microdetect convert --input_dir caminho/para/imagens_entrada --output_dir caminho/para/imagens_saida --use_opencv

# Usar PIL (Python Imaging Library)
microdetect convert --input_dir caminho/para/imagens_entrada --output_dir caminho/para/imagens_saida --no-use_opencv
```

O OpenCV geralmente fornece melhor suporte para formatos de imagem científica e conversão de profundidade de bits, enquanto o PIL pode ter melhor preservação de metadados.

## Processamento em Lote

Para grandes conjuntos de dados, o processamento em lote é automaticamente habilitado:

```bash
microdetect convert --input_dir caminho/para/imagens_entrada --output_dir caminho/para/imagens_saida --workers 4
```

O parâmetro `--workers` controla o número de processos paralelos de conversão. Por padrão, usa o número de núcleos de CPU disponíveis.

## Conversão de 16 bits para 8 bits

Muitas imagens de microscopia são armazenadas em formato de 16 bits, mas modelos de aprendizado profundo tipicamente trabalham com imagens de 8 bits. O MicroDetect lida automaticamente com esta conversão:

```bash
microdetect convert --input_dir caminho/para/imagens_16bits --output_dir caminho/para/imagens_8bits --use_opencv
```

A conversão usa escalonamento inteligente para preservar o máximo de informação possível:

1. Para imagens com intervalo normal de 16 bits, é aplicado escalonamento linear
2. Para imagens de microscopia com valores concentrados, pode ser aplicada equalização de histograma
3. Para microscopia de fluorescência com picos extremos, pode ser usado escalonamento logarítmico

Você pode especificar o método de escalonamento explicitamente:

```bash
microdetect convert --input_dir caminho/para/imagens_16bits --output_dir caminho/para/imagens_8bits --bit_conversion linear
```

Métodos disponíveis:
- `linear` - Escalonamento linear simples (padrão)
- `equalize` - Equalização de histograma
- `adaptive` - Seleciona automaticamente o melhor método
- `log` - Escalonamento logarítmico para intervalos dinâmicos extremos

## Lidando com Formatos Especiais de Microscopia

### Arquivos TIFF Multi-página

Para arquivos TIFF multi-página (comuns em z-stacks ou séries temporais de microscopia):

```bash
microdetect convert --input_dir caminho/para/tiffs_multipagina --output_dir caminho/para/imagens_saida --handle_multipage extract_all
```

Opções para `--handle_multipage`:
- `extract_all` - Extrair todas as páginas como imagens separadas
- `first_only` - Extrair apenas a primeira página (padrão)
- `max_projection` - Criar uma projeção de intensidade máxima (útil para z-stacks)

### Z-stacks

Para imagens Z-stack (volumes 3D):

```bash
microdetect convert --input_dir caminho/para/zstacks --output_dir caminho/para/imagens_saida --handle_multipage max_projection
```

Isso cria uma projeção de intensidade máxima, combinando os sinais mais fortes de todas as fatias z.

### Séries Temporais

Para dados de séries temporais:

```bash
microdetect convert --input_dir caminho/para/series_temporais --output_dir caminho/para/imagens_saida --handle_multipage extract_all --naming_pattern {basename}_t{page:03d}
```

O parâmetro `--naming_pattern` controla como as páginas extraídas são nomeadas, usando a formatação de string do Python com:
- `{basename}` - Nome do arquivo original sem extensão
- `{page}` - Número da página (começando de 0)
- `{page:03d}` - Número da página com zeros à esquerda

## Integração com Pré-processamento

A conversão de imagem pode ser combinada com pré-processamento básico:

```bash
microdetect convert --input_dir caminho/para/imagens_entrada --output_dir caminho/para/imagens_saida --normalize_contrast --normalize_brightness
```

Opções de pré-processamento disponíveis:
- `--normalize_contrast` - Melhorar contraste usando equalização de histograma
- `--normalize_brightness` - Ajustar brilho para um nível padrão
- `--remove_background` - Tentar remover fundos uniformes
- `--denoise` - Aplicar filtragem de redução de ruído

Para pré-processamento mais avançado, consulte o [Guia de Pré-processamento](preprocessing.md).

## Configuração

Você pode configurar as configurações padrão de conversão no arquivo `config.yaml`:

```yaml
conversion:
  format: png                     # Formato alvo (png, jpg)
  quality: 95                     # Qualidade para JPG
  use_opencv: true                # Usar OpenCV em vez de PIL
  delete_original: false          # Excluir arquivo original após conversão
  preserve_metadata: true         # Preservar metadados EXIF
  resize: false                   # Redimensionar imagens
  max_size: [1024, 1024]          # Tamanho máximo após redimensionamento
  bit_conversion: linear          # Método de conversão de 16 bits para 8 bits
  handle_multipage: first_only    # Como lidar com arquivos multi-página
  naming_pattern: "{basename}_p{page:03d}"  # Padrão de nomenclatura para páginas extraídas
```

## Melhores Práticas

1. **Preserve as imagens originais**: Mantenha as imagens originais como backup antes da conversão

2. **Use PNG para dados de treinamento**: PNG fornece compressão sem perdas e é bem suportado por frameworks de aprendizado profundo

3. **Processe amostras representativas primeiro**: Teste suas configurações de conversão em algumas imagens representativas antes de processar todo o conjunto de dados

4. **Verifique as imagens convertidas**: Inspecione visualmente as imagens convertidas para garantir que detalhes importantes sejam preservados

5. **Considere requisitos de resolução**: Maior resolução nem sempre é melhor para detecção; muitos modelos funcionam bem com imagens de cerca de 640-1280 pixels

6. **Use OpenCV para imagens científicas**: OpenCV fornece melhor manipulação de formatos de imagem científica e conversão de profundidade de bits

7. **Combine o pré-processamento com seus dados**: Diferentes técnicas de microscopia podem exigir diferentes abordagens de pré-processamento

8. **Documente suas configurações de conversão**: Mantenha registro de como você processou suas imagens para reprodutibilidade

## Solução de Problemas

### Problema: Imagens Convertidas Escuras ou com Baixo Contraste
**Solução**: Tente diferentes métodos de conversão de bits:
```bash
microdetect convert --input_dir caminho/para/imagens_16bits --output_dir caminho/para/imagens_8bits --bit_conversion equalize
```

### Problema: Falta de Memória com Imagens Grandes
**Solução**: Processe imagens em lotes menores ou redimensione-as durante a conversão:
```bash
microdetect convert --input_dir caminho/para/imagens_grandes --output_dir caminho/para/imagens_saida --resize --max_size 2048 2048
```

### Problema: Páginas Faltando de TIFFs Multi-página
**Solução**: Certifique-se de usar a opção correta de manipulação multi-página:
```bash
microdetect convert --input_dir caminho/para/tiffs_multipagina --output_dir caminho/para/imagens_saida --handle_multipage extract_all
```

### Problema: Conversão Muito Lenta
**Solução**: Aumente o número de processos de worker:
```bash
microdetect convert --input_dir caminho/para/imagens_entrada --output_dir caminho/para/imagens_saida --workers 8
```

### Problema: Formato de Arquivo Não Reconhecido
**Solução**: Instale dependências adicionais para formatos especializados:
```bash
pip install tifffile bioformats
```

### Problema: Perda de Informação de Escala
**Solução**: Preserve metadados e considere rastrear a resolução separadamente:
```bash
microdetect convert --input_dir caminho/para/imagens_entrada --output_dir caminho/para/imagens_saida --preserve_metadata
```

Para mais informações sobre solução de problemas, consulte o [Guia de Solução de Problemas](troubleshooting.md).