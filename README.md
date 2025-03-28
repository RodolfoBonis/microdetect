# microdetect

Microdetect Project

## Getting Started

This project is a starting point for a Flutter application.

A few resources to get you started if this is your first Flutter project:

- [Lab: Write your first Flutter app](https://docs.flutter.dev/get-started/codelab)
- [Cookbook: Useful Flutter samples](https://docs.flutter.dev/cookbook)

For help getting started with Flutter development, view the
[online documentation](https://docs.flutter.dev/), which offers tutorials,
samples, guidance on mobile development, and a full API reference.

## MicroDetect

### Integração Câmera com API

A integração do módulo de câmera com a API foi implementada para permitir o armazenamento e gerenciamento das imagens no backend, com os seguintes benefícios:

1. **Armazenamento centralizado**: As imagens capturadas são enviadas diretamente para o servidor, permitindo acesso de qualquer dispositivo.
2. **Metadados avançados**: Informações como ajustes de imagem, configurações da câmera e outras propriedades são armazenadas junto com a imagem.
3. **Integração com datasets**: As imagens podem ser associadas a datasets específicos para análise e processamento posterior.

#### Componentes Principais

1. **ApiService**: Serviço que gerencia a comunicação com a API do backend, fornecendo métodos para upload, download e gerenciamento de imagens.
2. **CameraService**: Serviço específico para a câmera que utiliza o ApiService para salvar imagens e gerenciar a galeria.
3. **GalleryImage**: Modelo que representa uma imagem na galeria, com metadados e informações de armazenamento.
4. **CameraImage**: Modelo que representa uma imagem capturada pela câmera, com informações sobre ajustes e configurações.

#### Fluxo de Captura e Armazenamento

1. O usuário captura uma imagem com a câmera.
2. A imagem é processada localmente se necessário (ajustes de brilho, contraste, etc.).
3. A imagem processada é enviada para o backend via API.
4. O backend armazena a imagem e seus metadados no banco de dados.
5. A imagem aparece na galeria e pode ser acessada posteriormente.

#### Modificações no Backend

1. Atualização do modelo `Image` para incluir campos adicionais (URL, metadados, etc.).
2. Endpoint `/api/v1/images` modificado para aceitar metadados junto com a imagem.
3. Serviço `ImageService` adaptado para processar e armazenar metadados.

#### Como Usar

```dart
// Capturar uma imagem
final cameraImage = await captureImage();

// Salvar a imagem via API
final galleryImage = await cameraService.saveImage(
  imageBytes: cameraImage.bytes!,
  metadata: cameraImage.toMap(),
  datasetId: currentDatasetId,
);

// Carregar imagens da galeria
final images = await cameraService.loadGalleryImages(
  datasetId: currentDatasetId,
);
```

#### Próximos Passos

1. Implementar processamento de imagem no backend (detecção, classificação, etc.).
2. Adicionar suporte para organização de imagens em coleções e álbuns.
3. Integrar com serviços de backup em nuvem.
