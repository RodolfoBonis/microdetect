# Guia de Solução de Problemas

Este guia ajuda a resolver problemas comuns que você pode encontrar ao usar o MicroDetect.

## Sumário

- [Problemas de Instalação](#problemas-de-instalação)
- [Problemas de Conversão de Imagens](#problemas-de-conversão-de-imagens)
- [Problemas de Anotação](#problemas-de-anotação)
- [Problemas de Visualização](#problemas-de-visualização)
- [Problemas de Dataset](#problemas-de-dataset)
- [Problemas de Treinamento](#problemas-de-treinamento)
- [Problemas de GPU](#problemas-de-gpu)
- [Problemas de Avaliação](#problemas-de-avaliação)
- [Problemas de Análise de Erros](#problemas-de-análise-de-erros)
- [Problemas de Visualização e Dashboard](#problemas-de-visualização-e-dashboard)
- [Problemas de Análise Estatística](#problemas-de-análise-estatística)
- [Problemas de Validação Cruzada](#problemas-de-validação-cruzada)
- [Problemas de Benchmarking](#problemas-de-benchmarking)
- [Problemas de Atualização](#problemas-de-atualização)
- [Erros Comuns e Soluções](#erros-comuns-e-soluções)
- [Logs e Diagnóstico](#logs-e-diagnóstico)

## Problemas de Instalação

### Erro: "No module named 'microdetect'"

**Sintomas:**
```
ImportError: No module named 'microdetect'
```

**Soluções:**
1. Verifique se o pacote está instalado:
   ```bash
   pip list | grep microdetect
   ```

2. Reinstale o pacote:
   ```bash
   pip install -e .
   ```

3. Verifique se está no ambiente virtual correto:
   ```bash
   # Ver ambiente ativo
   which python  # Linux/macOS
   where python  # Windows
   ```

### Erro: Incompatibilidade de Versões

**Sintomas:**
```
ERROR: pip's dependency resolver does not support this constraint
```

**Soluções:**
1. Atualizar pip:
   ```bash
   pip install --upgrade pip
   ```

2. Instalar com `--no-deps` e depois as dependências:
   ```bash
   pip install --no-deps -e .
   pip install -r requirements.txt
   ```

### Erro: Compilação de Extensões

**Sintomas:**
```
error: Microsoft Visual C++ 14.0 or greater is required.
```

**Soluções:**
1. Instale o Microsoft C++ Build Tools (Windows)
2. Instale ferramentas de desenvolvimento essenciais (Linux):
   ```bash
   sudo apt-get install build-essential python3-dev
   ```
3. Use uma versão pré-compilada:
   ```bash
   pip install --only-binary=:all: -r requirements.txt
   ```

## Problemas de Conversão de Imagens

### Erro: Imagem TIFF não Reconhecida

**Sintomas:**
```
ERROR: Erro ao converter image.tiff: Image format not recognized
```

**Soluções:**
1. Use a opção OpenCV:
   ```bash
   microdetect convert --input_dir data/raw_images --output_dir data/images --use_opencv
   ```

2. Verifique se a imagem TIFF está corrompida:
   ```bash
   identify -verbose image.tiff  # requer ImageMagick
   ```

3. Tente converter com outras ferramentas:
   ```bash
   # Usando ImageMagick
   convert image.tiff image.png
   ```

### Erro: Imagens de 16 bits

**Sintomas:**
Imagem convertida fica muito escura ou com cores incorretas.

**Soluções:**
1. Use a opção OpenCV para normalização:
   ```bash
   microdetect convert --input_dir data/raw_images --output_dir data/images --use_opencv
   ```

2. Se ainda tiver problemas, faça um pré-processamento manual:
   ```python
   import cv2
   import numpy as np
   
   # Carregar imagem de 16 bits
   img = cv2.imread('image.tiff', cv2.IMREAD_UNCHANGED)
   
   # Normalizar para 8 bits
   img_norm = cv2.normalize(img, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
   
   # Salvar
   cv2.imwrite('image.png', img_norm)
   ```

## Problemas de Anotação

### Erro: Interface de Anotação não Abre

**Sintomas:**
```
No module named 'tkinter'
```

**Soluções:**
1. Instale o Tkinter:
   ```bash
   # Ubuntu/Debian
   sudo apt-get install python3-tk
   
   # Fedora
   sudo dnf install python3-tkinter
   
   # macOS (Homebrew)
   brew install python-tk
   ```

2. Para Python 3.12 no macOS, use:
   ```bash
   # Instalar uma versão alternativa do Python com Tkinter
   brew install python@3.11
   ```

### Erro: Não Salva Anotações

**Sintomas:**
Anotações não são salvas ou aparecem em locais incorretos.

**Soluções:**
1. Verifique as permissões do diretório:
   ```bash
   chmod 755 data/labels
   ```

2. Use caminhos absolutos:
   ```bash
   microdetect annotate --image_dir $(pwd)/data/images --output_dir $(pwd)/data/labels
   ```

3. Verifique o arquivo de progresso:
   ```bash
   cat data/labels/.annotation_progress.json
   ```

### Erro: Imagens Grandes Causam Problemas

**Sintomas:**
A interface trava ou fica lenta com imagens muito grandes.

**Soluções:**
1. Redimensione as imagens para um tamanho gerenciável:
   ```bash
   # Usando o ImageMagick
   mogrify -resize 1024x1024\> data/images/*.png
   ```

## Problemas de Visualização

### Erro: Interface de Visualização não Abre

**Sintomas:**
Nenhuma janela aparece ou mensagem de erro sobre o display.

**Soluções:**
1. Instale o Tkinter:
   ```bash
   sudo apt-get install python3-tk
   ```

2. Verifique se você está em um ambiente com suporte a display:
   ```bash
   # Defina a variável de display se necessário
   export DISPLAY=:0
   ```

### Erro: Anotações Não Visíveis

**Sintomas:**
As imagens são exibidas, mas as anotações não aparecem.

**Soluções:**
1. Verifique os caminhos dos arquivos de anotação:
   ```bash
   # Verifique se os arquivos de anotação existem
   ls caminho/para/anotacoes/*.txt
   ```

2. Verifique o formato do arquivo de anotação:
   ```bash
   # Veja o conteúdo de um arquivo de anotação
   cat caminho/para/anotacoes/nome_da_imagem.txt
   # Deve conter linhas como: class_id center_x center_y width height
   ```

3. Use um diretório de anotação explícito:
   ```bash
   microdetect visualize --image_dir caminho/para/imagens --label_dir caminho/para/anotacoes
   ```

### Erro: Problemas de Desempenho com Imagens Grandes

**Sintomas:**
A visualização fica lenta ou trava com imagens grandes.

**Soluções:**
1. Use o modo em lote para grandes coleções:
   ```bash
   microdetect visualize --image_dir caminho/para/imagens --label_dir caminho/para/anotacoes --batch --output_dir caminho/para/saida
   ```

2. Redimensione as imagens apenas para visualização:
   ```bash
   # Em Python
   from PIL import Image
   Image.open('imagem_grande.jpg').resize((1024, 768)).save('imagem_redimensionada.jpg')
   ```

## Problemas de Dataset

### Erro: Divisão do Dataset Desequilibrada

**Sintomas:**
O dataset não está sendo dividido corretamente entre treino/validação/teste.

**Soluções:**
1. Especifique proporções manualmente:
   ```bash
   microdetect dataset --source_img_dir data/images --source_label_dir data/labels --dataset_dir dataset --train_ratio 0.7 --val_ratio 0.15 --test_ratio 0.15
   ```

2. Verifique a estrutura de diretórios:
   ```bash
   find dataset -type f | sort | head -n 20
   ```

### Erro: arquivo data.yaml

**Sintomas:**
```
ERROR: data.yaml not found
```

**Soluções:**
1. Verifique o caminho correto:
   ```bash
   ls -la dataset/data.yaml
   ```

2. Gere o arquivo manualmente:
   ```bash
   microdetect dataset --source_img_dir data/images --source_label_dir data/labels --dataset_dir dataset
   ```

3. Certifique-se de que as classes estão definidas em config.yaml:
   ```bash
   cat config.yaml | grep -A5 classes
   ```

## Problemas de Treinamento

### Erro: CUDA out of memory

**Sintomas:**
```
RuntimeError: CUDA out of memory.
```

**Soluções:**
1. Reduza o tamanho do batch:
   ```bash
   microdetect train --dataset_dir dataset --model_size s --batch_size 8
   ```

2. Reduza o tamanho da imagem:
   ```bash
   microdetect train --dataset_dir dataset --model_size s --image_size 480
   ```

3. Use um modelo menor:
   ```bash
   microdetect train --dataset_dir dataset --model_size n
   ```

### Erro: Queda na Performance

**Sintomas:**
O modelo converge e depois a performance cai drasticamente.

**Soluções:**
1. Ative early stopping aumentando a paciência:
   ```bash
   python -m microdetect.training.train --dataset_dir dataset --patience 30
   ```

2. Reduza a taxa de aprendizado:
   ```python
   # Use diretamente o módulo ultralytics com parâmetros personalizados
   from ultralytics import YOLO
   model = YOLO('yolov8s.pt')
   model.train(data='dataset/data.yaml', epochs=100, lr0=0.001)
   ```

### Erro: Treinamento lento

**Sintomas:**
O treinamento está demorando muito mais do que o esperado.

**Soluções:**
1. Verifique se está usando GPU:
   ```bash
   python -c "import torch; print(torch.cuda.is_available())"
   ```

2. Otimize o carregamento de dados:
   ```bash
   microdetect train --dataset_dir dataset --batch_size 32 --workers 4
   ```

3. Em macOS com chip Apple Silicon, ative a aceleração MPS:
   ```python
   import torch
   print(f"MPS disponível: {torch.backends.mps.is_available()}")
   ```

## Problemas de GPU

### Erro: CUDA não disponível

**Sintomas:**
```
CUDA not available, using CPU
```

**Soluções:**
1. Verifique a instalação CUDA:
   ```bash
   nvidia-smi
   ```

2. Verifique a compatibilidade PyTorch-CUDA:
   ```bash
   python -c "import torch; print(f'PyTorch: {torch.__version__}, CUDA: {torch.version.cuda}')"
   ```

3. Reinstale PyTorch com suporte CUDA:
   ```bash
   pip uninstall torch torchvision
   pip install torch torchvision --extra-index-url https://download.pytorch.org/whl/cu118
   ```

### Erro: Mac MPS não disponível

**Sintomas:**
```
MPS não disponível em macOS com chip Apple Silicon
```

**Soluções:**
1. Atualize o macOS para versão 12.3+
2. Atualize o PyTorch:
   ```bash
   pip install torch==2.6.0 torchvision==0.21.0
   ```

## Problemas de Avaliação

### Erro: Métricas de avaliação não correspondem às expectativas

**Sintomas:**
Métricas como mAP50 são muito mais baixas do que o esperado com base nas métricas de treinamento.

**Soluções:**
1. Verifique se está usando o conjunto de dados de teste correto:
   ```bash
   # Certifique-se de que o conjunto de teste tenha anotações apropriadas
   ls -la dataset/test/labels/
   ```

2. Verifique os limiares de detecção:
   ```bash
   # Experimente diferentes limiares de confiança
   microdetect evaluate --model_path model.pt --dataset_dir dataset --conf_threshold 0.25
   ```

3. Examine o arquivo de melhores pesos do modelo:
   ```bash
   # Certifique-se de que está usando os melhores pesos, não os últimos
   microdetect evaluate --model_path runs/train/exp/weights/best.pt --dataset_dir dataset
   ```

### Erro: Falha na geração da matriz de confusão

**Sintomas:**
```
ERROR: Could not generate confusion matrix
```

**Soluções:**
1. Verifique se o conjunto de dados de teste tem amostras suficientes:
   ```bash
   # Certifique-se de que você tem amostras suficientes por classe
   ls -la dataset/test/labels/ | wc -l
   ```

2. Tente desativar a matriz de confusão:
   ```bash
   microdetect evaluate --model_path model.pt --dataset_dir dataset --confusion_matrix False
   ```

## Problemas de Análise de Erros

### Erro: Nenhum erro encontrado apesar do baixo desempenho

**Sintomas:**
A análise de erros mostra poucos ou nenhum erro apesar do baixo desempenho do modelo.

**Soluções:**
1. Diminua o limiar de confiança:
   ```bash
   microdetect analyze_errors --model_path model.pt --dataset_dir dataset --conf_threshold 0.1
   ```

2. Verifique os caminhos do conjunto de dados de teste:
   ```bash
   # Verifique a estrutura do conjunto de teste
   ls -la dataset/test/images/
   ls -la dataset/test/labels/
   ```

3. Certifique-se de que os nomes dos arquivos de imagem e rótulo correspondam.

### Erro: Visualização ausente para alguns tipos de erro

**Sintomas:**
Algumas pastas de erro estão vazias (por exemplo, sem erros de classificação).

**Soluções:**
1. Isso pode ser normal se seu modelo não comete esses tipos de erro
2. Tente um conjunto de teste maior para capturar erros mais diversos
3. Verifique se o formato de anotação corresponde ao formato de saída de detecção

### Erro: Problemas de memória durante análise de erros

**Sintomas:**
```
ERROR: Out of memory during error analysis
```

**Soluções:**
1. Processe menos imagens:
   ```bash
   # Limite o número máximo de amostras 
   microdetect analyze_errors --model_path model.pt --dataset_dir dataset --max_samples 10
   ```

2. Use um modelo menor ou reduza o tamanho da imagem para análise

## Problemas de Visualização e Dashboard

### Erro: Dashboards não carregam no navegador

**Sintomas:**
O servidor de dashboard inicia, mas nada aparece no navegador.

**Soluções:**
1. Verifique se a porta já está em uso:
   ```bash
   # Verifique se a porta está em uso (Linux/macOS)
   lsof -i :8050
   
   # Windows
   netstat -ano | findstr :8050
   ```

2. Tente uma porta diferente:
   ```bash
   microdetect dashboard --results_dir results --port 8051
   ```

3. Instale dependências de dashboard ausentes:
   ```bash
   pip install dash dash-bootstrap-components
   ```

### Erro: Falha na geração de relatório PDF

**Sintomas:**
```
ERROR: Failed to generate PDF report
```

**Soluções:**
1. Certifique-se de que wkhtmltopdf está instalado:
   ```bash
   # Para Ubuntu/Debian
   sudo apt-get install wkhtmltopdf
   
   # Para macOS
   brew install wkhtmltopdf
   ```

2. Tente gerar um relatório HTML primeiro:
   ```bash
   microdetect generate_report --results_dir results --format html
   ```

### Erro: Imagens ausentes na visualização

**Sintomas:**
Caixas delimitadoras aparecem, mas não as imagens subjacentes.

**Soluções:**
1. Verifique os caminhos das imagens:
   ```bash
   # Certifique-se de que os caminhos são absolutos ou relativos ao diretório atual
   microdetect visualize_detections --model_path model.pt --source $(pwd)/images
   ```

2. Verifique o suporte ao formato de imagem:
   ```bash
   # Certifique-se de que as imagens estão em formatos suportados
   find images -type f | grep -v -E '\.(jpg|jpeg|png|bmp)$'
   ```

## Problemas de Análise Estatística

### Erro: Mapas de densidade não mostram padrões

**Sintomas:**
Mapas de densidade estão em branco ou uniformemente coloridos.

**Soluções:**
1. Ajuste o parâmetro de suavização:
   ```bash
   microdetect analyze_distribution --model_path model.pt --source images --sigma 5.0
   ```

2. Verifique se as detecções foram encontradas:
   ```bash
   # Verifique se seu modelo está detectando objetos
   microdetect batch_detect --model_path model.pt --source images --save_json
   ```

### Erro: Análise de tamanho mostra resultados inesperados

**Sintomas:**
Histogramas de distribuição de tamanho mostram valores irrealistas.

**Soluções:**
1. Verifique a normalização da caixa delimitadora:
   ```bash
   # Se estiver usando código personalizado, certifique-se de que os valores estão normalizados corretamente
   # O formato YOLO usa coordenadas normalizadas (0-1)
   ```

2. Filtre pequenas detecções:
   ```bash
   # Defina um limiar de confiança mínimo
   microdetect analyze_size --model_path model.pt --source images --conf_threshold 0.5
   ```

### Erro: Análise de cluster não encontra clusters

**Sintomas:**
Análise espacial não mostra clusters apesar de grupos visualmente aparentes.

**Soluções:**
1. Ajuste o parâmetro de distância mínima:
   ```bash
   microdetect analyze_spatial --model_path model.pt --source images --min_distance 0.05
   ```

2. Verifique o sistema de coordenadas:
   ```bash
   # Certifique-se de que as coordenadas estão normalizadas (0-1)
   ```

## Problemas de Validação Cruzada

### Erro: Validação cruzada leva muito tempo

**Sintomas:**
O processo de validação cruzada é extremamente lento ou parece travado.

**Soluções:**
1. Reduza o número de épocas para validação:
   ```python
   validator = CrossValidator(
       base_dataset_dir="dataset",
       output_dir="cv_results",
       model_size="s",
       epochs=20,  # Menos épocas
       folds=5
   )
   ```

2. Use um tamanho de modelo menor:
   ```python
   validator = CrossValidator(
       base_dataset_dir="dataset",
       output_dir="cv_results",
       model_size="n",  # Modelo nano
       epochs=50,
       folds=5
   )
   ```

3. Reduza o número de folds:
   ```python
   validator = CrossValidator(
       base_dataset_dir="dataset",
       output_dir="cv_results",
       model_size="m",
       epochs=100,
       folds=3  # Menos folds
   )
   ```

### Erro: Memória insuficiente durante validação cruzada

**Sintomas:**
```
CUDA out of memory
```

**Soluções:**
1. Processe um fold de cada vez:
   ```python
   # Em vez de validator.run(), execute cada fold individualmente
   for fold in range(1, 6):
       # Configure o fold manualmente
       # Treine e avalie
   ```

2. Reduza o tamanho do batch:
   ```python
   # Configure o treinador com tamanho de batch menor
   trainer = YOLOTrainer(
       model_size="m",
       batch_size=8,  # Tamanho de batch pequeno
       epochs=100
   )
   ```

### Erro: Grande desvio padrão nos resultados de validação cruzada

**Sintomas:**
Os resultados de validação cruzada mostram desvio padrão muito alto entre folds.

**Soluções:**
1. Aumente o número de folds:
   ```python
   validator = CrossValidator(
       base_dataset_dir="dataset",
       output_dir="cv_results",
       model_size="m",
       epochs=100,
       folds=10  # Mais folds para melhor estimativa
   )
   ```

2. Verifique o desequilíbrio de dados:
   ```bash
   # Conte arquivos em cada classe
   ls dataset/labels | grep -c "classe1"
   ls dataset/labels | grep -c "classe2"
   ```

3. Estratifique os folds manualmente para garantir equilíbrio de classes

## Problemas de Benchmarking

### Erro: Resultados de benchmark inconsistentes

**Sintomas:**
Os resultados de benchmarking variam significativamente entre execuções.

**Soluções:**
1. Aumente as iterações e o aquecimento:
   ```python
   benchmark = SpeedBenchmark(model_path="model.pt")
   results = benchmark.run(
       batch_sizes=[1, 4, 8],
       image_sizes=[640],
       iterations=100,  # Mais iterações
       warmup=20  # Mais iterações de aquecimento
   )
   ```

2. Feche outros aplicativos usando recursos de GPU

3. Fixe a frequência da CPU/GPU:
   ```bash
   # No Linux, defina o governador de CPU para performance
   echo performance | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor
   
   # Para GPUs NVIDIA, bloqueie a frequência do clock
   sudo nvidia-smi --lock-gpu-clocks=1000,1500
   ```

### Erro: Monitor de recursos não mostra uso de GPU

**Sintomas:**
```
No GPU usage recorded during monitoring
```

**Soluções:**
1. Verifique a detecção de GPU:
   ```python
   import torch
   print(f"CUDA disponível: {torch.cuda.is_available()}")
   print(f"Contagem de GPU: {torch.cuda.device_count()}")
   print(f"Nome da GPU: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'Nenhuma'}")
   ```

2. Instale pacotes de monitoramento necessários:
   ```bash
   pip install gputil nvidia-ml-py3
   ```

3. Para Apple Silicon, verifique disponibilidade do MPS:
   ```python
   import torch
   print(f"MPS disponível: {torch.backends.mps.is_available()}")
   ```

### Erro: Falha na visualização de benchmark

**Sintomas:**
```
ERROR: Could not generate benchmark visualization
```

**Soluções:**
1. Instale matplotlib:
   ```bash
   pip install matplotlib
   ```

2. Verifique se os dados de resultados são válidos:
   ```python
   # Salve resultados brutos para inspeção
   import json
   with open('benchmark_results_raw.json', 'w') as f:
       json.dump(results, f, indent=4)
   ```

## Problemas de Atualização

### Erro: Falha na Conexão com AWS CodeArtifact

**Sintomas:**
```
ERROR: Não foi possível obter token do AWS CodeArtifact
```

**Soluções:**
1. Verifique as credenciais AWS:
   ```bash
   aws sts get-caller-identity
   ```

2. Verifique se o domínio e repositório existem:
   ```bash
   aws codeartifact list-repositories --domain seu-dominio
   ```

3. Configure novamente:
   ```bash
   microdetect setup-aws --domain seu-dominio --repository seu-repositorio --configure-aws
   ```

### Erro: Falha ao Instalar Atualização

**Sintomas:**
```
ERROR: Failed to update to version X.Y.Z
```

**Soluções:**
1. Tente atualizar manualmente:
   ```bash
   pip install --upgrade microdetect --index-url <url_do_repositorio>
   ```

2. Verifique o log para erros específicos:
   ```bash
   export MICRODETECT_LOG_LEVEL=DEBUG
   microdetect update
   ```

3. Limpe o cache pip:
   ```bash
   pip cache purge
   ```

## Erros Comuns e Soluções

### Erro: "ModuleNotFoundError: No module named 'cv2'"

**Solução:**
```bash
pip install opencv-python
```

### Erro: "AttributeError: module 'numpy' has no attribute 'float'"

**Solução:**
```bash
pip uninstall numpy
pip install numpy==1.23.5
```

### Erro: "Cannot import name 'PILLOW_VERSION' from 'PIL'"

**Solução:**
```bash
pip uninstall pillow
pip install pillow
```

### Erro: "FileNotFoundError: [Errno 2] No such file or directory: 'scripts/setup.sh'"

**Solução:**
```bash
# Certifique-se de que está no diretório raiz do projeto
cd microdetect
# Ou especifique o caminho completo
/caminho/para/microdetect/scripts/setup.sh
```

### Erro: "JSONDecodeError: Expecting value: line 1 column 1"

**Solução:**
```bash
# Limpar arquivos de cache
find . -name "*.json" -size 0 -delete
```

### Erro: "YOLO model not found"

**Solução:**
```bash
# Crie um diretório no cache do Ultralytics
mkdir -p ~/.cache/ultralytics/
# Ou especifique o modelo completo
microdetect train --dataset_dir dataset --model_size s --model_path yolov8s.pt
```

### Erro: "Permission denied"

**Solução:**
```bash
# Linux/macOS
chmod +x scripts/*.sh

# Windows - Certifique-se de executar como administrador
```

### Erro: "File [filename] doesn't match the expected format"

**Solução:**
```bash
# Verifique se as anotações estão no formato YOLO
cat data/labels/image_name.txt
# Deve conter: class_id center_x center_y width height
```

### Erro: "No module named 'dash'"

**Solução:**
```bash
pip install dash dash-bootstrap-components
```

### Erro: "matplotlib.pyplot not found"

**Solução:**
```bash
pip install matplotlib
```

## Logs e Diagnóstico

Para diagnosticar problemas mais complexos, ative o modo de debug:

```bash
# Exportar variável de ambiente para logging detalhado
export MICRODETECT_LOG_LEVEL=DEBUG

# Executar o comando com saída detalhada
microdetect comando --args > debug.log 2>&1

# Analisar o log
cat debug.log
```

Para logging específico de componentes:

```bash
# Ativar logging detalhado para módulos específicos
python -c "import logging; logging.getLogger('microdetect.training').setLevel(logging.DEBUG)"

# Ou editar a configuração de logging no código
```

## Suporte

Se você ainda estiver enfrentando problemas:

1. Verifique as [Issues do GitHub](https://github.com/RodolfoBonis/microdetect/issues)
2. Abra uma nova issue com detalhes completos do problema
3. Entre em contato: dev@rodolfodebonis.com.br