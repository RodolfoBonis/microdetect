import 'package:get/get.dart';
import 'package:microdetect/core/services/api_service.dart';
import 'package:microdetect/core/utils/logger_util.dart';
import 'package:microdetect/features/annotation/models/annotation.dart';
import 'package:microdetect/features/datasets/models/dataset.dart';
import 'package:dio/dio.dart' as http;

/// Serviço para gerenciar anotações através da API
class AnnotationService extends ApiService {
  // Singleton pattern
  static AnnotationService get to => Get.find<AnnotationService>();

  /// Obter todas as imagens de um dataset com suas anotações
  Future<List<AnnotatedImage>> getDatasetImages(int datasetId) async {
    try {
      final response = await get<Map<String, dynamic>>(
        '/api/v1/images',
        queryParameters: {
          'dataset_id': datasetId,
          'with_annotations': true,
        },
      );

      if (response.statusCode == 200 && response.data != null) {
        final data = response.data!;
        if (data['success'] == true && data['data'] != null) {
          return (data['data'] as List)
              .map((e) => AnnotatedImage.fromJson(e))
              .toList();
        }
      }
      return [];
    } catch (e) {
      LoggerUtil.error('Erro ao buscar imagens do dataset: $e');
      return [];
    }
  }

  /// Obter todas as anotações de uma imagem específica
  Future<List<Annotation>> getImageAnnotations(int imageId) async {
    try {
      final response = await get<Map<String, dynamic>>(
        '/api/v1/images/$imageId',
        queryParameters: {'with_annotations': true},
      );

      if (response.statusCode == 200 && response.data != null) {
        final data = response.data!;
        if (data['success'] == true && data['data'] != null) {
          // Agora as anotações vêm diretamente com a imagem
          final imageData = data['data'];
          if (imageData['annotations'] != null) {
            return (imageData['annotations'] as List)
                .map((e) => Annotation.fromJson(e))
                .toList();
          }
        }
      }
      return [];
    } catch (e) {
      LoggerUtil.error('Erro ao buscar anotações: $e');
      return [];
    }
  }

  /// Obter todas as anotações de um dataset específico
  Future<List<Annotation>> getDatasetAnnotations(int datasetId) async {
    try {
      final response = await get<Map<String, dynamic>>(
        '/api/v1/annotations',
        queryParameters: {'dataset_id': datasetId},
      );

      if (response.statusCode == 200 && response.data != null) {
        final data = response.data!;
        if (data['success'] == true && data['data'] != null) {
          return (data['data'] as List)
              .map((e) => Annotation.fromJson(e))
              .toList();
        }
      }
      return [];
    } catch (e) {
      LoggerUtil.error('Erro ao buscar anotações do dataset: $e');
      return [];
    }
  }

  /// Criar uma nova anotação
  Future<Annotation?> createAnnotation(Annotation annotation) async {
    try {
      final response = await post<Map<String, dynamic>>(
        '/api/v1/annotations',
        data: annotation.toJson(),
      );

      if (response.statusCode == 200 && response.data != null) {
        final data = response.data!;
        if (data['success'] == true && data['data'] != null) {
          return Annotation.fromJson(data['data']);
        }
      }
      return null;
    } catch (e) {
      LoggerUtil.error('Erro ao criar anotação: $e');
      return null;
    }
  }

  /// Criar múltiplas anotações em lote
  Future<List<Annotation>> createAnnotationsBatch(
      int imageId, int? datasetId, List<Annotation> annotations) async {
    try {
      final data = {
        'image_id': imageId,
        'dataset_id': datasetId,
        'annotations': annotations
            .map((a) => {
                  'class_name': a.className,
                  'class_id': a.classId,
                  'x': a.x,
                  'y': a.y,
                  'width': a.width,
                  'height': a.height,
                  'confidence': a.confidence,
                })
            .toList(),
      };

      final response = await post<Map<String, dynamic>>(
        '/api/v1/annotations/batch',
        data: data,
      );

      if (response.statusCode == 200 && response.data != null) {
        final responseData = response.data!;
        if (responseData['success'] == true && responseData['data'] != null) {
          return (responseData['data'] as List)
              .map((e) => Annotation.fromJson(e))
              .toList();
        }
      }
      return [];
    } catch (e) {
      LoggerUtil.error('Erro ao criar anotações em lote: $e');
      return [];
    }
  }

  /// Atualizar uma anotação existente
  Future<Annotation?> updateAnnotation(Annotation annotation) async {
    if (annotation.id == null) {
      LoggerUtil.error('Tentativa de atualizar anotação sem ID');
      return null;
    }

    try {
      final response = await put<Map<String, dynamic>>(
        '/api/v1/annotations/${annotation.id}',
        data: annotation.toJson(),
      );

      if (response.statusCode == 200 && response.data != null) {
        final data = response.data!;
        if (data['success'] == true && data['data'] != null) {
          return Annotation.fromJson(data['data']);
        }
      }
      return null;
    } catch (e) {
      LoggerUtil.error('Erro ao atualizar anotação: $e');
      return null;
    }
  }

  /// Excluir uma anotação
  Future<bool> deleteAnnotation(int annotationId) async {
    try {
      final response = await delete<Map<String, dynamic>>(
        '/api/v1/annotations/$annotationId',
      );

      if (response.statusCode == 200 && response.data != null) {
        final data = response.data!;
        return data['success'] == true;
      }
      return false;
    } catch (e) {
      LoggerUtil.error('Erro ao excluir anotação: $e');
      return false;
    }
  }

  /// Obter lista de classes de um dataset
  Future<List<String>> getDatasetClasses(int datasetId) async {
    try {
      final response = await get<Map<String, dynamic>>(
        '/api/v1/annotations/dataset/$datasetId/classes',
      );

      if (response.statusCode == 200 && response.data != null) {
        final data = response.data!;
        if (data['success'] == true && data['data'] != null) {
          final classes = (data['data'] as List)
              .map((e) => e['class_name'] as String)
              .toList();
          return classes;
        }
      }
      return [];
    } catch (e) {
      LoggerUtil.error('Erro ao buscar classes do dataset: $e');
      return [];
    }
  }

  /// Converter anotações para formato YOLO
  Future<Map<String, dynamic>> convertToYolo(int datasetId) async {
    try {
      final response = await post<Map<String, dynamic>>(
        '/api/v1/annotations/dataset/$datasetId/convert-to-yolo',
      );

      if (response.statusCode == 200 && response.data != null) {
        final data = response.data!;
        if (data['success'] == true && data['data'] != null) {
          return data['data'];
        }
      }
      return {};
    } catch (e) {
      LoggerUtil.error('Erro ao converter dataset para YOLO: $e');
      return {};
    }
  }
} 