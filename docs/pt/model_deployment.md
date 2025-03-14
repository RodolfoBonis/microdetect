# Guia de Implantação de Modelos

Este guia explica como implantar seus modelos YOLOv8 treinados para detecção de microorganismos em vários ambientes, desde estações de trabalho locais até sistemas de produção.

## Visão Geral

Após treinar um modelo com sucesso, o próximo passo é implantá-lo para uso prático. O MicroDetect fornece ferramentas e utilitários para tornar a implantação de modelos simples em diferentes plataformas e ambientes, permitindo que você integre capacidades de detecção de microorganismos em seus fluxos de trabalho de pesquisa ou produção.

## Opções de Implantação

O MicroDetect suporta várias opções de implantação para seus modelos treinados:

| Tipo de Implantação | Caso de Uso | Requisitos |
|-----------------|----------|--------------|
| Python Local | Pesquisa e desenvolvimento | Ambiente Python com dependências |
| API REST | Serviço de inferência acessível por rede | Servidor com Python e frameworks web |
| Conteinerizado | Implantação portátil e isolada | Docker |
| Dispositivos Edge | Implantação no local com recursos limitados | Dispositivo edge compatível (Jetson, Raspberry Pi, etc.) |
| Móvel | Aplicações em campo | Ferramentas e bibliotecas de desenvolvimento móvel |
| Navegador Web | Aplicações web interativas | JavaScript e formatos de modelo compatíveis |

## Exportação de Modelo

### Exportando para Diferentes Formatos

Antes da implantação, você precisará exportar seu modelo para o formato apropriado:

```bash
microdetect export --model_path runs/train/yolov8_s_custom/weights/best.pt --format onnx
```

Formatos de exportação suportados:

| Formato | Descrição | Melhor Para |
|--------|-------------|----------|
| ONNX | Formato Open Neural Network Exchange | Implantação multiplataforma, integração com vários frameworks |
| TorchScript | Formato de serialização do PyTorch | Ambientes de produção PyTorch |
| TensorRT | Runtime otimizado da NVIDIA | Implantação em GPU NVIDIA com máximo desempenho |
| CoreML | Framework de aprendizado de máquina da Apple | Aplicativos iOS e macOS |
| TFLite | Formato TensorFlow Lite | Dispositivos móveis e edge |
| OpenVINO | Toolkit de otimização de inferência da Intel | Implantação em CPU/GPU Intel |
| PaddlePaddle | Plataforma de deep learning da Baidu | Integração com ecossistema PaddlePaddle |

### Opções de Linha de Comando

| Parâmetro | Descrição | Padrão |
|-----------|-------------|---------|
| `--model_path` | Caminho para o modelo treinado | |
| `--format` | Formato de exportação (onnx, torchscript, tflite, etc.) | `onnx` |
| `--img_size` | Tamanho da imagem para o modelo exportado | Tamanho de treinamento do modelo |
| `--batch_size` | Tamanho do batch para o modelo exportado | 1 |
| `--half` | Exportar em precisão FP16 | `False` |
| `--dynamic` | Exportar com eixos dinâmicos | `False` |
| `--simplify` | Simplificar o modelo ONNX | `True` |
| `--output_dir` | Diretório para salvar o modelo exportado | Mesmo diretório do model_path |

## Implantação Python Local

### Inferência Básica

O método de implantação mais simples é a inferência direta em Python:

```python
from microdetect.inference import MicroDetector

# Inicializar detector com seu modelo treinado
detector = MicroDetector(model_path="runs/train/yolov8_s_custom/weights/best.pt")

# Executar detecção em uma única imagem
results = detector.detect("caminho/para/imagem.jpg")

# Processar e visualizar resultados
detector.visualize_results(results, output_path="output.jpg")

# Obter dados de detecção
detections = detector.process_results(results)
for detection in detections:
    print(f"Classe: {detection['class_name']}, Confiança: {detection['confidence']:.2f}")
    print(f"Bounding Box: {detection['bbox']}")
```

### Processamento em Lote

Para processar múltiplas imagens:

```python
import glob
from microdetect.inference import MicroDetector

detector = MicroDetector(model_path="runs/train/yolov8_s_custom/weights/best.pt")

# Processar todas as imagens em um diretório
image_paths = glob.glob("data/test_images/*.jpg")
batch_results = detector.batch_detect(image_paths)

# Salvar resultados em um diretório
detector.batch_visualize(
    image_paths=image_paths,
    results=batch_results,
    output_dir="output/detections"
)

# Exportar dados de detecção para CSV
detector.export_detections(batch_results, "detections.csv")
```

### Otimização de Desempenho

Otimize a inferência para seu hardware específico:

```python
from microdetect.inference import MicroDetector

# Aceleração GPU com precisão FP16 para inferência mais rápida
detector = MicroDetector(
    model_path="runs/train/yolov8_s_custom/weights/best.pt",
    device="cuda:0",
    half=True,
    batch_size=4
)

# Definir limiar de confiança e parâmetros NMS para melhores resultados
detector.conf_threshold = 0.25
detector.iou_threshold = 0.45
```

## Implantação de API REST

O MicroDetect inclui uma API REST pronta para uso para inferência remota:

```bash
# Iniciar servidor API
microdetect serve --model_path runs/train/yolov8_s_custom/weights/best.pt --port 8000
```

### Endpoints da API

Uma vez que o servidor esteja em execução, os seguintes endpoints estarão disponíveis:

| Endpoint | Método | Descrição |
|----------|--------|-------------|
| `/detect` | POST | Enviar uma imagem para detecção |
| `/batch_detect` | POST | Enviar múltiplas imagens para detecção |
| `/health` | GET | Verificar saúde do servidor |
| `/info` | GET | Obter informações do modelo |

### Exemplo de Cliente

```python
import requests
import base64
import json
import cv2
import numpy as np

def encode_image(image_path):
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

# Preparar a requisição
url = "http://localhost:8000/detect"
payload = {
    "image": encode_image("caminho/para/imagem.jpg"),
    "conf_threshold": 0.25,
    "save_results": True
}

# Enviar requisição
response = requests.post(url, json=payload)
detections = response.json()

# Processar resultados
print(f"Detectados {len(detections['objects'])} microorganismos")
for obj in detections['objects']:
    print(f"Classe: {obj['class_name']}, Confiança: {obj['confidence']:.2f}")
    
# Se save_results foi True, baixar a visualização
if "result_image" in detections:
    img_data = base64.b64decode(detections["result_image"])
    with open("resultado.jpg", "wb") as f:
        f.write(img_data)
```

### Implantação Docker

Para implantação de API em contêineres:

```bash
# Construir imagem Docker
microdetect build_docker --model_path runs/train/yolov8_s_custom/weights/best.pt --tag microdetect:latest

# Executar contêiner
docker run -p 8000:8000 microdetect:latest
```

## Implantação em Dispositivos Edge

### Implantação em Raspberry Pi

```bash
# Exportar modelo otimizado para Raspberry Pi
microdetect export --model_path runs/train/yolov8_s_custom/weights/best.pt --format tflite --quantize int8 --output_dir rpi_deploy

# Copiar arquivos para Raspberry Pi
scp -r rpi_deploy pi@raspberry:/home/pi/microdetect

# No Raspberry Pi
pip install microdetect-edge
microdetect-edge run --model_path /home/pi/microdetect/model_int8.tflite
```

### Implantação em NVIDIA Jetson

```bash
# Exportar modelo otimizado para Jetson
microdetect export --model_path runs/train/yolov8_s_custom/weights/best.pt --format tensorrt --device cuda:0 --output_dir jetson_deploy

# Instalar no Jetson
# Nota: Certifique-se de ter a versão correta do JetPack instalada
pip install microdetect-edge
microdetect-edge run --model_path jetson_deploy/model_tensorrt.engine --device cuda:0
```

## Implantação em Navegador Web

O MicroDetect fornece utilitários para implantação de modelos em navegadores web usando ONNX.js ou TensorFlow.js:

```bash
# Exportar para implantação web
microdetect export_web --model_path runs/train/yolov8_s_custom/weights/best.pt --framework tfjs --output_dir web_deploy

# Isso cria um pacote de implantação completo com código de inferência JavaScript
# Sirva o diretório com qualquer servidor web
python -m http.server --directory web_deploy
```

## Integração com Sistemas Existentes

### Bibliotecas Python

```python
# Integração com OpenCV para processamento de vídeo
import cv2
from microdetect.inference import MicroDetector

detector = MicroDetector(model_path="runs/train/yolov8_s_custom/weights/best.pt")

cap = cv2.VideoCapture(0)  # Abrir webcam
while True:
    ret, frame = cap.read()
    if not ret:
        break
        
    # Detectar microorganismos
    results = detector.detect(frame)
    
    # Desenhar detecções
    annotated_frame = detector.draw_results(frame, results)
    
    # Exibir
    cv2.imshow("MicroDetect", annotated_frame)
    if cv2.waitKey(1) == ord('q'):
        break
        
cap.release()
cv2.destroyAllWindows()
```

### Integração com Sistemas de Gerenciamento de Informações Laboratoriais (LIMS)

```python
from microdetect.inference import MicroDetector
from microdetect.integrations import LIMSConnector

# Inicializar detector
detector = MicroDetector(model_path="runs/train/yolov8_s_custom/weights/best.pt")

# Configurar conector LIMS (ajuste com base na API do seu LIMS)
lims = LIMSConnector(
    api_url="https://seu-sistema-lims.com/api",
    api_key="sua-chave-api"
)

# Processar amostra e atualizar LIMS
def processar_amostra(sample_id, image_path):
    # Detectar microorganismos
    results = detector.detect(image_path)
    detections = detector.process_results(results)
    
    # Preparar dados para LIMS
    counts = {}
    for det in detections:
        class_name = det['class_name']
        counts[class_name] = counts.get(class_name, 0) + 1
    
    # Atualizar LIMS
    lims.update_sample(
        sample_id=sample_id,
        detection_results=counts,
        image_path=image_path
    )
    
    return counts

# Exemplo de uso
contagem_amostra = processar_amostra("S12345", "caminho/para/amostra/imagem.jpg")
print(f"Análise de amostra completa: {contagem_amostra}")
```

## Monitoramento e Otimização de Desempenho

### Benchmark de Implantação

```bash
microdetect benchmark --model_path runs/train/yolov8_s_custom/weights/best.pt --batch_sizes 1,4,8 --img_sizes 640,1280
```

Isso fornece métricas detalhadas sobre:
- Tempo de inferência por imagem
- Uso de memória
- Utilização de CPU/GPU
- Throughput (imagens por segundo)

### Monitoramento em Tempo Real

Para implantações em produção:

```python
from microdetect.inference import MicroDetector
from microdetect.monitoring import PerformanceMonitor

detector = MicroDetector(model_path="runs/train/yolov8_s_custom/weights/best.pt")
monitor = PerformanceMonitor(log_dir="logs/performance")

# Monitorar desempenho durante inferência
with monitor.track_inference():
    results = detector.detect("caminho/para/imagem.jpg")

# Obter métricas de desempenho
metrics = monitor.get_metrics()
print(f"Tempo de inferência: {metrics['inference_time_ms']:.2f} ms")
print(f"Uso de memória: {metrics['memory_mb']:.2f} MB")
```

## Solução de Problemas

### Problemas Comuns de Implantação

| Problema | Solução |
|----------|---------|
| Inferência lenta | Tente resolução mais baixa, processamento em lote ou precisão FP16 |
| Erros de memória insuficiente | Reduza o tamanho do batch ou exporte para um formato mais otimizado |
| Erros CUDA | Certifique-se de que os drivers CUDA correspondem à versão usada para exportação |
| Compatibilidade de formato de modelo | Verifique se o ambiente de destino suporta o formato exportado |
| Resultados diferentes após exportação | Valide o modelo exportado em comparação com o original usando imagens de teste |

### Checklist de Implantação

Antes de implantar em produção:

1. Faça benchmark do modelo no hardware de destino
2. Valide a precisão do modelo com o dataset de teste
3. Defina limiares de confiança apropriados
4. Implemente tratamento de erros e logging
5. Configure monitoramento para problemas de desempenho
6. Crie caminhos de inferência de backup para sistemas críticos

## Próximos Passos

Após implantar seu modelo com sucesso:

- [Guia de Monitoramento de Modelos](model_monitoring.md) - Monitore o desempenho do modelo em produção
- [Guia de Atualização de Modelos](model_updating.md) - Atualize modelos implantados sem interrupção de serviço
- [Guia de Integração de Sistemas](systems_integration.md) - Integre com outros sistemas laboratoriais