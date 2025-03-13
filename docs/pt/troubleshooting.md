# Guia de Solução de Problemas

Este guia ajuda a resolver problemas comuns que você pode encontrar ao usar o MicroDetect.

## Sumário

- [Problemas de Instalação](#problemas-de-instalação)
- [Problemas de Conversão de Imagens](#problemas-de-conversão-de-imagens)
- [Problemas de Anotação](#problemas-de-anotação)
- [Problemas de Dataset](#problemas-de-dataset)
- [Problemas de Treinamento](#problemas-de-treinamento)
- [Problemas de GPU](#problemas-de-gpu)
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

### Não é possível adicionar classes às bounding boxes

**Sintomas:**
- Você pode desenhar boxes, mas elas não têm classe associada
- O menu de seleção de classe parece não funcionar

**Soluções:**
1. **Verifique a configuração de classes**:
   ```bash
   # Verifique se seu arquivo config.yaml está configurado corretamente
   # As classes devem estar no formato "ID-nome" como:
   classes:
     - "0-levedura"
     - "1-fungo"
     - "2-micro-alga"
   ```

2. **Reinicie a aplicação**:
   Saia completamente da aplicação e reinicie-a.

3. **Verifique logs**:
   Verifique os arquivos de log em `microdetect.log` para identificar erros.

### Não consigo editar (mover/redimensionar) as boxes

**Sintomas:**
- Ao tentar selecionar uma box existente, nada acontece
- O modo de edição não parece funcionar

**Soluções:**
1. **Ative o modo de edição**:
   - Certifique-se de pressionar a tecla 'E' ou clicar no botão "Modo Edição" para ativar o modo de edição
   - No modo de edição, você verá "MODO EDIÇÃO" na barra de status

2. **Usando o modo de edição**:
   - Clique em uma box para selecioná-la (ficará destacada em vermelho)
   - Clique e arraste no centro da box para movê-la
   - Clique e arraste nas alças (pequenos quadrados) nos cantos e laterais para redimensionar

3. **Verifique a escala da imagem**:
   - Se a imagem estiver muito ampliada ou reduzida, pode ser difícil selecionar boxes
   - Use 'R' para resetar o zoom e tente novamente

### As anotações não são salvas

**Sintomas:**
- Você faz alterações, clica em "Salvar" ou "Salvar e Sair", mas as mudanças não aparecem
- Ao retornar à visualização, as anotações originais ainda estão lá

**Soluções:**
1. **Verifique permissões de diretório**:
   ```bash
   # Certifique-se de que você tem permissão de escrita no diretório
   chmod -R u+w caminho/para/anotacoes
   ```

2. **Use caminhos absolutos**:
   Em vez de caminhos relativos, tente especificar caminhos absolutos:
   ```bash
   microdetect visualize --image_dir /caminho/completo/para/imagens --label_dir /caminho/completo/para/anotacoes
   ```

3. **Salve manualmente**:
   - Pressione 'S' para salvar suas alterações antes de sair
   - Ou use a combinação 'X' para salvar e sair

4. **Verifique backup**:
   - O sistema mantém backups automáticos em uma pasta `backup_annotations_TIMESTAMP`
   - Verifique se suas anotações estão sendo salvas lá

### A aplicação trava durante a edição

**Soluções:**
1. **Trate imagens grandes**:
   - Imagens muito grandes podem causar problemas de desempenho
   - Considere redimensionar imagens muito grandes antes da anotação

2. **Limpe arquivos temporários**:
   - Procure e remova arquivos `.annotation_progress.json` em seu diretório de anotações

3. **Modo simplificado**:
   - Se estiver enfrentando travamentos, tente evitar zoom e pan excessivos

## Comandos úteis para depuração

```bash
# Verificar quais anotações existem
find caminho/para/anotacoes -name "*.txt" | wc -l

# Verificar o conteúdo de uma anotação específica
cat caminho/para/anotacoes/nome_da_imagem.txt

# Limpar arquivos de progresso temporários
find caminho/para/anotacoes -name ".annotation_progress.json" -delete
```

Se os problemas persistirem, por favor, relate-os com detalhes específicos sobre sua configuração e os passos exatos para reproduzir o problema.

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

## Suporte

Se você ainda estiver enfrentando problemas:

1. Verifique as [Issues do GitHub](https://github.com/RodolfoBonis/microdetect/issues)
2. Abra uma nova issue com detalhes completos do problema
3. Entre em contato: dev@rodolfodebonis.com.br