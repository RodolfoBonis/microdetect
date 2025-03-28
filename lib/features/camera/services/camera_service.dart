import 'dart:async';
import 'dart:convert';
import 'dart:ui' as ui;

import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';
import 'package:microdetect/core/services/api_service.dart';
import 'package:microdetect/core/utils/logger_util.dart';
import 'package:path/path.dart' as path;

import '../models/gallery_image.dart';

/// Serviço para gerenciar a integração entre o módulo de câmera e a API
class CameraService extends ApiService {

  /// Carrega as imagens da galeria
  Future<List<GalleryImage>> loadGalleryImages({
    int? datasetId,
    int limit = 50,
    int skip = 0,
  }) async {
    try {
      if (!isApiInitialized) {
        LoggerUtil.warning('API não inicializada, não é possível carregar imagens');
        return [];
      }

      final queryParams = {
        'limit': limit.toString(),
        'skip': skip.toString(),
        if (datasetId != null) 'dataset_id': datasetId.toString(),
      };

      final response = await get(
        '/api/v1/images/',
        queryParameters: queryParams,
      );

      if (response.statusCode == 200) {
        // Verificar se a resposta está no formato esperado
        List<dynamic> imageData;
        if (response.data is Map && response.data.containsKey('data')) {
          imageData = response.data['data'];
          LoggerUtil.info('Imagens carregadas: ${imageData.length}');
        } else if (response.data is List) {
          imageData = response.data;
          LoggerUtil.info('Imagens carregadas: ${imageData.length}');
        } else {
          LoggerUtil.warning('Formato de resposta inesperado para imagens');
          return [];
        }

        final List<GalleryImage> images = imageData.map((item) => GalleryImage.fromJson(item)).toList();

        // Ordenar por data de criação (mais recentes primeiro)
        images.sort((a, b) => b.createdAt.compareTo(a.createdAt));

        return images;
      } else {
        LoggerUtil.warning('Falha ao obter imagens: ${response.statusCode}');
        return [];
      }
    } catch (e) {
      LoggerUtil.error('Erro ao carregar imagens da galeria: $e');
      return [];
    }
  }

  /// Faz upload de uma imagem para a API
  Future<GalleryImage> saveImage({
    required Uint8List imageBytes,
    required String fileName,
    int? datasetId,
    Map<String, dynamic>? metadata,
    int? width,
    int? height,
  }) async {
    if (!isApiInitialized) {
      throw Exception('API não inicializada, não é possível salvar imagens');
    }

    try {
      // Extract image dimensions if not provided (directly on main isolate)
      if (width == null || height == null) {
        LoggerUtil.debug('Extraindo dimensões da imagem automaticamente');

        // Process on main isolate instead of using compute
        final codec = await ui.instantiateImageCodec(imageBytes);
        final frame = await codec.getNextFrame();
        final image = frame.image;
        width = width ?? image.width;
        height = height ?? image.height;

        LoggerUtil.debug('Dimensões detectadas: ${width}x$height');
      }

      final String ext = path.extension(fileName).toLowerCase();
      final String mimeType = ext == '.png' ? 'image/png' : 'image/jpeg';
      // Prepare FormData for upload
      final formData = FormData.fromMap({
        'file': MultipartFile.fromBytes(
          imageBytes,
          filename: fileName,
          contentType: DioMediaType.parse(mimeType),
        ),
        'width': width.toString(),
        'height': height.toString(),
      });

      // Add optional fields
      if (metadata != null) {
        formData.fields.add(MapEntry('metadata', json.encode(metadata)));
      }

      if (datasetId != null) {
        formData.fields.add(MapEntry('dataset_id', datasetId.toString()));
      }

      // Perform upload
      final response = await upload(
        '/api/v1/images/',
        formData: formData,
      );

      if (response.statusCode == 200 || response.statusCode == 201) {
        return GalleryImage.fromJson(response.data);
      } else {
        throw Exception('Falha ao fazer upload: ${response.statusCode} - ${response.statusMessage}');
      }
    } catch (e) {
      LoggerUtil.error('Erro ao fazer upload de imagem: $e');
      rethrow;
    }
  }

  /// Deleta uma imagem da galeria
  Future<bool> deleteImage(GalleryImage image) async {
    try {
      // Se for imagem na API
      if (isApiInitialized && image.id > 0) {
        final response = await delete('/api/v1/images/${image.id}/');
        return response.statusCode == 200 || response.statusCode == 204;
      }

      return false;
    } catch (e) {
      LoggerUtil.error('Erro ao excluir imagem: $e');
      return false;
    }
  }

  /// Carrega informações completas de uma imagem
  Future<GalleryImage?> loadImageDetails(int imageId) async {
    try {
      if (!isApiInitialized) {
        return null;
      }

      final response = await get('/api/v1/images/$imageId/');

      if (response.statusCode == 200) {
        // Verificar se a resposta está no formato esperado
        if (response.data is Map) {
          if (response.data.containsKey('data')) {
            return GalleryImage.fromJson(response.data['data']);
          } else {
            return GalleryImage.fromJson(response.data);
          }
        } else {
          LoggerUtil.warning('Formato de resposta inesperado para detalhes da imagem');
          return null;
        }
      }

      return null;
    } catch (e) {
      LoggerUtil.error('Erro ao carregar detalhes da imagem: $e');
      return null;
    }
  }

  /// Obtém os bytes da imagem a partir da URL
  Future<Uint8List?> getImageBytes(String url) async {
    try {
      if (!isApiInitialized) {
        return null;
      }

      final response = await get(
        url,
        options: Options(responseType: ResponseType.bytes),
      );

      if (response.statusCode == 200) {
        return Uint8List.fromList(response.data);
      }

      return null;
    } catch (e) {
      LoggerUtil.error('Erro ao obter bytes da imagem: $e');
      return null;
    }
  }

  /// Adiciona uma imagem a um dataset
  Future<bool> addImageToDataset(int imageId, int datasetId) async {
    try {
      if (!isApiInitialized) {
        return false;
      }

      final response = await post(
        '/api/v1/datasets/$datasetId/images/',
        data: {'image_id': imageId},
        options: Options(contentType: 'application/json'),
      );

      return response.statusCode == 200 || response.statusCode == 201;
    } catch (e) {
      LoggerUtil.error('Erro ao adicionar imagem ao dataset: $e');
      return false;
    }
  }

  /// Remove uma imagem de um dataset
  Future<bool> removeImageFromDataset(int imageId, int datasetId) async {
    try {
      if (!isApiInitialized) {
        return false;
      }

      final response = await delete('/api/v1/datasets/$datasetId/images/$imageId/');
      return response.statusCode == 200 || response.statusCode == 204;
    } catch (e) {
      LoggerUtil.error('Erro ao remover imagem do dataset: $e');
      return false;
    }
  }
}