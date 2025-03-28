import 'dart:convert';
import 'dart:io';
import 'package:dio/dio.dart';
import 'package:get/get.dart';
import 'package:microdetect/core/services/api_service.dart';
import 'package:microdetect/core/utils/logger_util.dart';
import 'package:microdetect/features/datasets/models/dataset.dart';
import 'package:microdetect/features/datasets/models/dataset_statistics.dart';

class DatasetService extends ApiService {
  // Buscar todos os datasets
  Future<List<Dataset>> getDatasets() async {
    try {
      final response = await get('/api/v1/datasets');
      // Verificar se a resposta está no formato esperado
      if (response.data is Map && response.data.containsKey('data')) {
        final dataList = response.data['data'];
        LoggerUtil.info('Datasets carregados: ${dataList.length}');
        return dataList.map<Dataset>((json) => Dataset.fromJson(json)).toList();
      } else if (response.data is List) {
        // Formato de lista direta
        LoggerUtil.info('Datasets carregados: ${response.data.length}');
        return response.data.map<Dataset>((json) => Dataset.fromJson(json)).toList();
      } else {
        LoggerUtil.warning('Formato de resposta inesperado para datasets');
        return [];
      }
    } catch (e) {
      LoggerUtil.error('Erro ao carregar datasets', e);
      return [];
    }
  }

  // Buscar um dataset específico
  Future<Dataset?> getDataset(int id) async {
    try {
      final response = await get('/api/v1/datasets/$id');
      // Verificar se a resposta está no formato esperado
      if (response.data is Map) {
        if (response.data.containsKey('data')) {
          return Dataset.fromJson(response.data['data']);
        } else {
          return Dataset.fromJson(response.data);
        }
      } else {
        LoggerUtil.warning('Formato de resposta inesperado para dataset $id');
        return null;
      }
    } catch (e) {
      LoggerUtil.error('Erro ao carregar dataset $id', e);
      return null;
    }
  }

  // Criar um novo dataset
  Future<Dataset?> createDataset({
    required String name,
    String? description,
    List<String> classes = const [],
  }) async {
    try {
      final data = {
        'name': name,
        'description': description,
        'classes': classes,
      };

      final response = await post('/api/v1/datasets', data: data);
      LoggerUtil.info('Dataset criado: ${response.data['id']} - $name');
      return Dataset.fromJson(response.data);
    } catch (e) {
      LoggerUtil.error('Erro ao criar dataset', e);
      return null;
    }
  }

  // Atualizar um dataset existente
  Future<Dataset?> updateDataset({
    required int id,
    String? name,
    String? description,
    List<String>? classes,
  }) async {
    try {
      final data = {};

      if (name != null) data['name'] = name;
      if (description != null) data['description'] = description;
      if (classes != null) data['classes'] = classes;

      final response = await put('/api/v1/datasets/$id', data: data);
      LoggerUtil.info('Dataset atualizado: $id');
      return Dataset.fromJson(response.data);
    } catch (e) {
      LoggerUtil.error('Erro ao atualizar dataset $id', e);
      return null;
    }
  }

  // Excluir um dataset
  Future<bool> deleteDataset(int id) async {
    try {
      await delete('/api/v1/datasets/$id');
      LoggerUtil.info('Dataset excluído: $id');
      return true;
    } catch (e) {
      LoggerUtil.error('Erro ao excluir dataset $id', e);
      return false;
    }
  }

  // Adicionar uma classe a um dataset
  Future<bool> addClass(int datasetId, String className) async {
    try {
      final data = {
        "class_name": className,
      };
      final response = await post(
        '/api/v1/datasets/$datasetId/classes',
        data: jsonEncode(data),
        options: Options(
          headers: {
            Headers.contentTypeHeader: Headers.jsonContentType,
          },
        ),
      );
      LoggerUtil.info('Classe $className adicionada ao dataset $datasetId');
      return true;
    } catch (e) {
      LoggerUtil.error(
          'Erro ao adicionar classe $className ao dataset $datasetId', e);
      return false;
    }
  }

  // Remover uma classe de um dataset
  Future<bool> removeClass(int datasetId, String className) async {
    try {
      await delete('/api/v1/datasets/$datasetId/classes/$className');
      LoggerUtil.info('Classe $className removida do dataset $datasetId');
      return true;
    } catch (e) {
      LoggerUtil.error(
          'Erro ao remover classe $className do dataset $datasetId', e);
      return false;
    }
  }

  // Obter a distribuição de classes em um dataset
  Future<List<Map<String, dynamic>>> getClassDistribution(int datasetId) async {
    try {
      final response =
          await get('/api/v1/datasets/$datasetId/class-distribution');
      LoggerUtil.info(
          'Distribuição de classes carregada para o dataset $datasetId');
      
      // Verificar se a resposta está no formato esperado
      if (response.data is Map && response.data.containsKey('data')) {
        return List<Map<String, dynamic>>.from(response.data['data']);
      } else if (response.data is List) {
        return List<Map<String, dynamic>>.from(response.data);
      } else {
        LoggerUtil.warning('Formato de resposta inesperado para distribuição de classes');
        return [];
      }
    } catch (e) {
      LoggerUtil.error(
          'Erro ao carregar distribuição de classes para o dataset $datasetId',
          e);
      return [];
    }
  }

  // Carregar estatísticas de um dataset
  Future<DatasetStatistics?> getDatasetStatistics(int datasetId) async {
    try {
      final response = await get('/api/v1/datasets/$datasetId/stats');
      LoggerUtil.info('Estatísticas carregadas para o dataset $datasetId');
      
      // Verificar se a resposta está no formato esperado
      if (response.data is Map) {
        if (response.data.containsKey('data')) {
          return DatasetStatistics.fromJson(response.data['data']);
        } else {
          return DatasetStatistics.fromJson(response.data);
        }
      } else {
        LoggerUtil.warning('Formato de resposta inesperado para estatísticas do dataset $datasetId');
        // Retornar estatísticas vazias em vez de null para evitar erros na UI
        return DatasetStatistics(
          totalImages: 0,
          totalAnnotations: 0,
          annotatedImages: 0,
          unannotatedImages: 0,
          averageObjectsPerImage: 0,
          averageObjectDensity: 0,
        );
      }
    } catch (e) {
      LoggerUtil.error(
          'Erro ao carregar estatísticas para o dataset $datasetId', e);
      
      // Retornar estatísticas vazias em vez de null para prevenir erros na UI
      return DatasetStatistics(
        totalImages: 0,
        totalAnnotations: 0,
        annotatedImages: 0,
        unannotatedImages: 0,
        averageObjectsPerImage: 0,
        averageObjectDensity: 0,
      );
    }
  }

  // Remover uma imagem de um dataset
  Future<bool> removeImageFromDataset(int datasetId, int imageId) async {
    try {
      await delete('/api/v1/datasets/$datasetId/images/$imageId');
      LoggerUtil.info('Imagem $imageId removida do dataset $datasetId');
      return true;
    } catch (e) {
      LoggerUtil.error(
          'Erro ao remover imagem $imageId do dataset $datasetId', e);
      return false;
    }
  }

  // Vincular múltiplas imagens existentes a um dataset
  Future<int> linkExistingImagesToDataset({
    required int datasetId,
    required List<int> imageIds,
  }) async {
    try {
      final data = {
        'image_id': imageIds[0],
      };

      final response =
          await post('/api/v1/datasets/$datasetId/images', data: data);
      const int successCount = 1;
      LoggerUtil.info(
          '$successCount/${imageIds.length} imagens vinculadas ao dataset $datasetId');
      return successCount;
    } catch (e) {
      LoggerUtil.error('Erro ao vincular imagens ao dataset $datasetId', e);
      return 0;
    }
  }
}
