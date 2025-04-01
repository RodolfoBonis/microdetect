// ignore_for_file: constant_identifier_names

part of 'app_pages.dart';

abstract class AppRoutes {
  static const backendMonitor = '/backend-monitor';
  static final root = _Paths.root.path;
  static final home = root + _Paths.home.path;
  static final settings = root + _Paths.settings.path;
  static final datasets = root + _Paths.datasets.path;
  static final camera = root + _Paths.camera.path;
  static final annotations = root + _Paths.annotations.path;
  static final training = root + _Paths.training.path;
  static final trainingCreate = training + _Paths.trainingCreate.path;
  static final trainingDetails = training + _Paths.trainingDetails.path;
  static final hyperparameters = training + _Paths.hyperparameters.path;
  static final hyperparameterDetails = hyperparameters + _Paths.hyperparameterDetails.path;
  static final inference = root + _Paths.inference.path;
  static final analysis = root + _Paths.analysis.path;
  static final notFound = root + _Paths.notFound.path;

  static String getTitlePage(String route) {
    if (route == home) return _Paths.home.title;
    if (route == settings) return _Paths.settings.title;
    if (route == datasets) return _Paths.datasets.title;
    if (route == camera) return _Paths.camera.title;
    if (route == annotations) return _Paths.annotations.title;
    if (route == training) return _Paths.training.title;
    if (route == inference) return _Paths.inference.title;
    if (route == analysis) return _Paths.analysis.title;
    if (route == notFound) return _Paths.notFound.title;
    return 'MicroDetect';
  }
}

abstract class _Paths {
  static const root = AppPathsModel(path: '/root', title: '');
  static const backendMonitor = AppPathsModel(path: '/backend-monitor', title: 'Monitoramento do Backend');
  static const home = AppPathsModel(path: '/home', title: 'Dashboard');
  static const settings = AppPathsModel(path: '/settings', title: 'Configurações');
  static const datasets = AppPathsModel(path: '/datasets', title: 'Datasets');
  static const datasetDetail = AppPathsModel(path: '/:id', title: 'Detalhes do Dataset');
  static const camera = AppPathsModel(path: '/camera', title: 'Câmera');
  static const annotations = AppPathsModel(path: '/annotations', title: 'Anotações');
  static const training = AppPathsModel(path: '/training', title: 'Treinamento');
  static const trainingCreate = AppPathsModel(path: '/create', title: 'Novo Treinamento');
  static const trainingDetails = AppPathsModel(path: '/details', title: 'Detalhes do Treinamento');
  static const hyperparameters = AppPathsModel(path: '/hyperparameters', title: 'Hiperparâmetros');
  static const hyperparameterDetails = AppPathsModel(path: '/details', title: 'Detalhes do Hiperparâmetro');
  static const inference = AppPathsModel(path: '/inference', title: 'Inferência');
  static const analysis = AppPathsModel(path: '/analysis', title: 'Análise');
  static const notFound = AppPathsModel(path: '/not-found', title: 'Não Encontrado');
}