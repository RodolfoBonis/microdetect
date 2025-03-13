# Guia de Pré-processamento de Imagens

Este guia aborda as técnicas de pré-processamento disponíveis no MicroDetect para otimizar imagens de microscopia antes da detecção e classificação.

## Visão Geral

O pré-processamento de imagens é uma etapa crucial no fluxo de trabalho de detecção de microorganismos. Imagens de microscopia frequentemente vêm em formatos especializados com características particulares que precisam ser padronizadas antes de poderem ser efetivamente utilizadas para treinar modelos de aprendizado profundo.

## Principais Funcionalidades de Pré-processamento

### Conversão de Formato de Imagem

O MicroDetect fornece ferramentas para converter de formatos especializados de microscopia (como TIFF, particularmente TIFFs de 16 bits) para formatos otimizados para aprendizado profundo:

```bash
microdetect convert --input_dir data/imagens_raw --output_dir data/imagens_processadas --use_opencv
```

#### Parâmetros de Conversão

| Parâmetro | Descrição |
|-----------|-------------|
| `--input_dir` | Diretório contendo imagens de origem |
| `--output_dir` | Diretório onde as imagens processadas serão salvas |
| `--use_opencv` | Usar OpenCV para processamento (recomendado para a maioria dos casos) |
| `--format` | Formato de saída (padrão: png) |
| `--bit_depth` | Profundidade de bits de saída (padrão: 8) |
| `--normalize` | Habilitar normalização para conversão de 16 bits para 8 bits |

### Normalização

Ao converter de imagens de 16 bits para 8 bits, a normalização adequada é essencial para preservar os detalhes visíveis:

```bash
microdetect convert --input_dir data/imagens_raw --output_dir data/imagens_processadas --normalize
```

O MicroDetect oferece múltiplas estratégias de normalização:

- **Escala Min-Max**: Escala a faixa dinâmica completa para 0-255
- **Baseada em Percentil**: Aplica normalização baseada em valores de percentil (robusta a outliers)
- **Equalização de Histograma**: Melhora o contraste redistribuindo valores de intensidade

### Melhoria de Contraste

Melhore o contraste em imagens de microscopia com baixo contraste:

```bash
microdetect enhance --input_dir data/imagens --output_dir data/melhoradas --method clahe
```

Métodos de melhoria disponíveis:
- `clahe`: Equalização de Histograma Adaptativa com Limite de Contraste
- `stretch`: Esticamento simples de contraste
- `gamma`: Correção gamma (use com `--gamma_value`)

### Redução de Ruído

Imagens de microscopia frequentemente contêm ruído que pode afetar a precisão da detecção:

```bash
microdetect denoise --input_dir data/imagens --output_dir data/sem_ruido --method bilateral
```

Métodos de desruidificação disponíveis:
- `bilateral`: Preserva bordas enquanto reduz ruído
- `gaussian`: Desfoque gaussiano (mais rápido, mas preserva menos as bordas)
- `nlm`: Médias não-locais (maior qualidade, mas mais lento)

### Processamento em Lote

Processe múltiplas imagens com configurações consistentes:

```bash
microdetect batch_process --input_dir data/imagens_raw --output_dir data/processadas \
                          --operations "normalize,denoise,enhance" \
                          --params "method=bilateral,strength=10"
```

## Pré-processamento Avançado

### Pipeline de Pré-processamento Personalizado

Crie um pipeline de pré-processamento personalizado em Python:

```python
from microdetect.preprocessing import ImageProcessor

processor = ImageProcessor()
processor.add_step("normalize", method="percentile", low=2, high=98)
processor.add_step("denoise", method="bilateral", d=5, sigma_color=75, sigma_space=75)
processor.add_step("enhance", method="clahe", clip_limit=2.0, tile_grid_size=(8, 8))

# Processar uma única imagem
processor.process_image("entrada.tif", "saida.png")

# Processar um diretório
processor.process_directory("dir_entrada", "dir_saida")
```

### Preservação de Metadados

Quando necessário, o MicroDetect pode preservar metadados importantes durante a conversão:

```bash
microdetect convert --input_dir data/imagens_raw --output_dir data/imagens_processadas --preserve_metadata
```

## Melhores Práticas

### Para Imagens de Microscopia de Luz

- Use normalização com recorte de percentil (2-98%)
- Aplique desruidificação suave com filtro bilateral
- Considere melhoria leve com CLAHE se o contraste for baixo

```bash
microdetect batch_process --input_dir microscopia_luz --output_dir processadas \
                          --operations "normalize,denoise,enhance" \
                          --params "normalize_method=percentile,low=2,high=98,denoise_method=bilateral,enhance_method=clahe,clip_limit=1.5"
```

### Para Microscopia de Fluorescência

- Use normalização min-max (geralmente melhor para fluorescência)
- Aplique desruidificação mais agressiva
- Potencialmente aplique operações específicas por canal para imagens multicanal

```bash
microdetect batch_process --input_dir fluorescencia --output_dir processadas \
                          --operations "normalize,denoise" \
                          --params "normalize_method=minmax,denoise_method=nlm"
```

### Para Microscopia de Contraste de Fase

- Use equalização de histograma para melhor contraste
- Aplique realce de borda
- Considere subtração de fundo

```bash
microdetect batch_process --input_dir contraste_fase --output_dir processadas \
                          --operations "normalize,enhance,denoise" \
                          --params "normalize_method=equalize,enhance_method=edge,denoise_method=bilateral"
```

## Considerações de Desempenho

- Processar imagens grandes pode exigir muita memória
- Para processamento em lote de muitas imagens, considere usar o parâmetro `--workers` para utilizar múltiplos núcleos da CPU
- Aceleração GPU está disponível para algumas operações ao usar a flag `--use_gpu`

## Solução de Problemas

### Problemas Comuns

| Problema | Solução |
|----------|---------|
| Imagens muito claras/escuras após conversão | Ajuste os parâmetros de normalização |
| Imagens borradas após desruidificação | Reduza a força do filtro ou escolha um método diferente |
| Falha ao processar imagens muito grandes | Use o parâmetro `--max_size` para redimensionar durante o processamento |
| Detalhes perdidos nas imagens convertidas | Tente diferentes métodos de tratamento de profundidade de bits |

Para problemas mais específicos, consulte o [Guia de Solução de Problemas](troubleshooting.md).

## Próximos Passos

Após pré-processar suas imagens, você pode prosseguir para:

- [Guia de Anotação](annotation_guide.md) - Anotar suas imagens pré-processadas
- [Guia de Gerenciamento de Dataset](dataset_management.md) - Preparar suas imagens anotadas para treinamento