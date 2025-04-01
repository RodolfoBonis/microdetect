import 'dart:math';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:get/get.dart';
import 'package:microdetect/design_system/app_colors.dart';
import 'package:microdetect/design_system/app_typography.dart';
import 'package:microdetect/design_system/app_spacing.dart';
import 'package:microdetect/design_system/app_buttons.dart';
import 'package:microdetect/design_system/app_borders.dart';
import 'package:microdetect/features/datasets/controllers/dataset_controller.dart';
import 'package:microdetect/features/datasets/models/dataset.dart';

/// Formulário para criar/editar uma busca de hiperparâmetros
class HyperparameterSearchForm extends StatefulWidget {
  /// Parâmetros iniciais (opcional)
  final Map<String, dynamic>? initialData;

  /// Função chamada ao submeter o formulário
  final Function(Map<String, dynamic>) onSubmit;

  /// Construtor
  const HyperparameterSearchForm({
    Key? key,
    this.initialData,
    required this.onSubmit,
  }) : super(key: key);

  @override
  State<HyperparameterSearchForm> createState() => _HyperparameterSearchFormState();
}

class _HyperparameterSearchFormState extends State<HyperparameterSearchForm> {
  // Controllers para os campos de texto
  final _nameController = TextEditingController();
  final _descriptionController = TextEditingController();

  // Valores do formulário
  int? _selectedDatasetId;
  int _iterations = 5;
  String _selectedModelType = 'yolov8';
  List<String> _selectedModelSizes = ['n', 's'];
  String _device = 'auto';

  // Valores para ranges
  RangeValues _batchSizeRange = const RangeValues(8, 32);
  List<int> _selectedImageSizes = [640];
  RangeValues _learningRateRange = const RangeValues(0.001, 0.01);
  int _epochs = 10;
  List<String> _selectedOptimizers = ['Adam', 'SGD'];

  // Chave do formulário para validação
  final _formKey = GlobalKey<FormState>();

  // Lista de tamanhos de imagem disponíveis
  final List<int> _availableImageSizes = [416, 512, 640, 768, 1024];

  @override
  void initState() {
    super.initState();
    _initializeForm();
  }

  /// Inicializa o formulário com valores padrão ou dados existentes
  void _initializeForm() {
    if (widget.initialData != null) {
      final data = widget.initialData!;

      _nameController.text = data['name'] ?? '';
      _descriptionController.text = data['description'] ?? '';
      _selectedDatasetId = data['dataset_id'];
      _iterations = data['iterations'] ?? 5;

      // Espaço de busca
      if (data['search_space'] != null) {
        final searchSpace = data['search_space'] as Map<String, dynamic>;

        if (searchSpace.containsKey('model_type')) {
          _selectedModelType = searchSpace['model_type'] ?? 'yolov8';
        }

        if (searchSpace.containsKey('model_size')) {
          if (searchSpace['model_size'] is List) {
            _selectedModelSizes = List<String>.from(searchSpace['model_size']);
          } else if (searchSpace['model_size'] is String) {
            _selectedModelSizes = [searchSpace['model_size']];
          }
        }

        if (searchSpace.containsKey('device')) {
          _device = searchSpace['device'] ?? 'auto';
        }

        if (searchSpace.containsKey('batch_size')) {
          if (searchSpace['batch_size'] is Map) {
            final minBatch = searchSpace['batch_size']['min'] ?? 8;
            final maxBatch = searchSpace['batch_size']['max'] ?? 32;
            _batchSizeRange = RangeValues(minBatch.toDouble(), maxBatch.toDouble());
          } else if (searchSpace['batch_size'] is int) {
            final batchSize = searchSpace['batch_size'];
            _batchSizeRange = RangeValues(batchSize.toDouble(), batchSize.toDouble());
          }
        }

        if (searchSpace.containsKey('imgsz')) {
          if (searchSpace['imgsz'] is List) {
            _selectedImageSizes = List<int>.from(searchSpace['imgsz']);
          } else if (searchSpace['imgsz'] is int) {
            _selectedImageSizes = [searchSpace['imgsz']];
          }
        }

        if (searchSpace.containsKey('lr0')) {
          if (searchSpace['lr0'] is Map) {
            final minLr = searchSpace['lr0']['min'] ?? 0.001;
            final maxLr = searchSpace['lr0']['max'] ?? 0.01;
            _learningRateRange = RangeValues(minLr, maxLr);
          } else if (searchSpace['lr0'] is double || searchSpace['lr0'] is int) {
            final lr = searchSpace['lr0'].toDouble();
            _learningRateRange = RangeValues(lr, lr);
          }
        }

        if (searchSpace.containsKey('epochs')) {
          _epochs = searchSpace['epochs'] ?? 10;
        }

        if (searchSpace.containsKey('optimizer')) {
          if (searchSpace['optimizer'] is List) {
            _selectedOptimizers = List<String>.from(searchSpace['optimizer']);
          } else if (searchSpace['optimizer'] is String) {
            _selectedOptimizers = [searchSpace['optimizer']];
          }
        }
      }
    }
  }

  @override
  void dispose() {
    _nameController.dispose();
    _descriptionController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final datasetController = Get.find<DatasetController>(tag: 'datasetController');

    return Form(
      key: _formKey,
      child: ListView(
        padding: AppSpacing.paddingMedium,
        children: [
          // Seção de informações básicas
          _buildSectionTitle(context, 'Informações Básicas'),

          // Nome da busca
          TextFormField(
            controller: _nameController,
            decoration: const InputDecoration(
              labelText: 'Nome da busca*',
              hintText: 'Ex: Busca de Hiperparâmetros YOLO-Micro',
            ),
            validator: (value) {
              if (value == null || value.isEmpty) {
                return 'Por favor, informe um nome para a busca';
              }
              return null;
            },
          ),
          const SizedBox(height: 16),

          // Descrição
          TextFormField(
            controller: _descriptionController,
            decoration: const InputDecoration(
              labelText: 'Descrição',
              hintText: 'Ex: Busca automática para encontrar melhores hiperparâmetros para detecção de micro-organismos',
            ),
            maxLines: 3,
          ),
          const SizedBox(height: 16),

          // Dataset
          Obx(() {
            if (datasetController.isLoading) {
              return const Center(
                child: Padding(
                  padding: EdgeInsets.all(16.0),
                  child: CircularProgressIndicator(),
                ),
              );
            }

            if (datasetController.datasets.isEmpty) {
              return Container(
                padding: AppSpacing.paddingMedium,
                decoration: BoxDecoration(
                  color: AppColors.errorLight,
                  borderRadius: AppBorders.medium,
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Icon(Icons.warning_amber_rounded, color: AppColors.error),
                        const SizedBox(width: 8),
                        Text(
                          'Nenhum dataset disponível',
                          style: AppTypography.labelMedium(context).copyWith(
                            color: AppColors.error,
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 8),
                    Text(
                      'Você precisa criar um dataset antes de iniciar uma busca de hiperparâmetros.',
                      style: AppTypography.bodySmall(context),
                    ),
                    const SizedBox(height: 8),
                    AppButton(
                      label: 'Criar Dataset',
                      onPressed: () => Get.toNamed('/root/datasets'),
                      type: AppButtonType.secondary,
                      prefixIcon: Icons.add,
                    ),
                  ],
                ),
              );
            }

            return DropdownButtonFormField<int>(
              decoration: const InputDecoration(
                labelText: 'Dataset*',
                hintText: 'Selecione um dataset',
              ),
              value: _selectedDatasetId,
              items: datasetController.datasets.map((Dataset dataset) {
                return DropdownMenuItem<int>(
                  value: dataset.id,
                  child: Text(dataset.name),
                );
              }).toList(),
              validator: (value) {
                if (value == null) {
                  return 'Por favor, selecione um dataset';
                }
                return null;
              },
              onChanged: (value) {
                setState(() {
                  _selectedDatasetId = value;
                });
              },
            );
          }),
          const SizedBox(height: 16),

          // Número de iterações
          TextFormField(
            decoration: const InputDecoration(
              labelText: 'Número de Iterações*',
              hintText: '5',
              helperText: 'Quantidade de modelos a serem testados',
            ),
            keyboardType: TextInputType.number,
            inputFormatters: [FilteringTextInputFormatter.digitsOnly],
            initialValue: _iterations.toString(),
            validator: (value) {
              if (value == null || value.isEmpty) {
                return 'Obrigatório';
              }
              final iterations = int.tryParse(value);
              if (iterations == null || iterations < 1) {
                return 'Min: 1';
              }
              return null;
            },
            onChanged: (value) {
              setState(() {
                _iterations = int.tryParse(value) ?? _iterations;
              });
            },
          ),
          const SizedBox(height: 24),

          // Seção de espaço de busca
          _buildSectionTitle(context, 'Espaço de Busca'),

          // Tipo de modelo
          DropdownButtonFormField<String>(
            decoration: const InputDecoration(
              labelText: 'Tipo de modelo*',
            ),
            value: _selectedModelType,
            items: const [
              DropdownMenuItem<String>(
                value: 'yolov8',
                child: Text('YOLOv8'),
              ),
            ],
            onChanged: (value) {
              setState(() {
                _selectedModelType = value!;
              });
            },
          ),
          const SizedBox(height: 16),

          // Tamanhos de modelo
          _buildMultiSelectChipField(
            context: context,
            title: 'Tamanho do Modelo*',
            helperText: 'Selecione os tamanhos a serem testados',
            options: const [
              MultiSelectOption(value: 'n', label: 'Nano (n)'),
              MultiSelectOption(value: 's', label: 'Small (s)'),
              MultiSelectOption(value: 'm', label: 'Medium (m)'),
              MultiSelectOption(value: 'l', label: 'Large (l)'),
              MultiSelectOption(value: 'x', label: 'XLarge (x)'),
            ],
            selectedValues: _selectedModelSizes,
            onChanged: (values) {
              setState(() {
                _selectedModelSizes = values;
              });
            },
          ),
          const SizedBox(height: 24),

          // Tamanho do Batch
          _buildRangeSlider(
            context: context,
            title: 'Tamanho do Batch*',
            min: 1,
            max: 64,
            divisions: 63,
            values: _batchSizeRange,
            onChanged: (values) {
              setState(() {
                _batchSizeRange = values;
              });
            },
            formatLabel: (value) => value.toInt().toString(),
            helperText: 'Intervalo: ${_batchSizeRange.start.toInt()} a ${_batchSizeRange.end.toInt()} imagens por lote',
          ),
          const SizedBox(height: 24),

          // Tamanho da Imagem
          _buildMultiSelectChipField(
            context: context,
            title: 'Tamanho da Imagem*',
            helperText: 'Selecione as resoluções a serem testadas',
            options: _availableImageSizes.map((size) {
              return MultiSelectOption(
                value: size,
                label: '$size × $size',
              );
            }).toList(),
            selectedValues: _selectedImageSizes,
            onChanged: (values) {
              setState(() {
                _selectedImageSizes = values.cast<int>();
              });
            },
          ),
          const SizedBox(height: 24),

          // Taxa de Aprendizado
          _buildRangeSlider(
            context: context,
            title: 'Taxa de Aprendizado*',
            min: 0.0001,
            max: 0.1,
            divisions: 100,
            values: _learningRateRange,
            onChanged: (values) {
              setState(() {
                _learningRateRange = values;
              });
            },
            formatLabel: (value) => value.toStringAsFixed(4),
            helperText: 'Intervalo: ${_learningRateRange.start.toStringAsFixed(4)} a ${_learningRateRange.end.toStringAsFixed(4)}',
            logarithmic: true,
          ),
          const SizedBox(height: 24),

          // Épocas
          TextFormField(
            decoration: const InputDecoration(
              labelText: 'Épocas*',
              hintText: '10',
              helperText: 'Ciclos de treinamento reduzidos para busca mais rápida',
            ),
            keyboardType: TextInputType.number,
            inputFormatters: [FilteringTextInputFormatter.digitsOnly],
            initialValue: _epochs.toString(),
            validator: (value) {
              if (value == null || value.isEmpty) {
                return 'Obrigatório';
              }
              final epochs = int.tryParse(value);
              if (epochs == null || epochs < 1) {
                return 'Min: 1';
              }
              return null;
            },
            onChanged: (value) {
              setState(() {
                _epochs = int.tryParse(value) ?? _epochs;
              });
            },
          ),
          const SizedBox(height: 24),

          // Otimizadores
          _buildMultiSelectChipField(
            context: context,
            title: 'Otimizadores*',
            helperText: 'Selecione os algoritmos de otimização a serem testados',
            options: const [
              MultiSelectOption(value: 'Adam', label: 'Adam'),
              MultiSelectOption(value: 'SGD', label: 'SGD'),
              MultiSelectOption(value: 'AdamW', label: 'AdamW'),
              MultiSelectOption(value: 'RMSProp', label: 'RMSProp'),
            ],
            selectedValues: _selectedOptimizers,
            onChanged: (values) {
              setState(() {
                _selectedOptimizers = values;
              });
            },
          ),
          const SizedBox(height: 32),

          DropdownButtonFormField<String>(
            decoration: const InputDecoration(
              labelText: 'Dispositivo*',
              helperText: 'Hardware para execução (fixo para todas as iterações)',
            ),
            value: _device,
            items: const [
              DropdownMenuItem<String>(
                value: 'auto',
                child: Text('Auto (recomendado)'),
              ),
              DropdownMenuItem<String>(
                value: 'cpu',
                child: Text('CPU'),
              ),
              DropdownMenuItem<String>(
                value: '0',
                child: Text('GPU 0'),
              ),
              // Pode adicionar mais GPUs se necessário
              DropdownMenuItem<String>(
                value: '1',
                child: Text('GPU 1'),
              ),
            ],
            onChanged: (value) {
              setState(() {
                _device = value!;
              });
            },
          ),
          const SizedBox(height: 24),

          // Botões de ação
          Row(
            mainAxisAlignment: MainAxisAlignment.end,
            children: [
              AppButton(
                label: 'Cancelar',
                onPressed: () => Navigator.of(context).pop(),
                type: AppButtonType.secondary,
              ),
              const SizedBox(width: 16),
              AppButton(
                label: 'Iniciar Busca',
                onPressed: _submitForm,
                prefixIcon: Icons.auto_fix_high,
              ),
            ],
          ),
        ],
      ),
    );
  }

  /// Constrói o título de uma seção
  Widget _buildSectionTitle(BuildContext context, String title) {
    final isDark = Theme.of(context).brightness == Brightness.dark;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          title,
          style: AppTypography.titleMedium(context),
        ),
        const SizedBox(height: 8),
        Divider(
          color: isDark ? AppColors.neutralDark : AppColors.neutralLight,
          thickness: 1,
        ),
        const SizedBox(height: 16),
      ],
    );
  }

  /// Constrói um slider de intervalo
  Widget _buildRangeSlider({
    required BuildContext context,
    required String title,
    required double min,
    required double max,
    required int divisions,
    required RangeValues values,
    required ValueChanged<RangeValues> onChanged,
    required String Function(double) formatLabel,
    required String helperText,
    bool logarithmic = false,
  }) {
    // Conversão para escala logarítmica (para UI)
    RangeValues displayValues = values;
    if (logarithmic) {
      displayValues = RangeValues(
        _logScale(values.start, min, max),
        _logScale(values.end, min, max),
      );
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          title,
          style: AppTypography.labelMedium(context),
        ),
        const SizedBox(height: 8),
        Row(
          children: [
            Text(
              formatLabel(values.start),
              style: AppTypography.bodySmall(context),
            ),
            Expanded(
              child: RangeSlider(
                values: displayValues,
                min: logarithmic ? 0.0 : min,
                max: logarithmic ? 1.0 : max,
                divisions: divisions,
                labels: RangeLabels(
                  formatLabel(values.start),
                  formatLabel(values.end),
                ),
                onChanged: (newValues) {
                  if (logarithmic) {
                    // Conversão de volta para escala real
                    onChanged(RangeValues(
                      _expScale(newValues.start, min, max),
                      _expScale(newValues.end, min, max),
                    ));
                  } else {
                    onChanged(newValues);
                  }
                },
              ),
            ),
            Text(
              formatLabel(values.end),
              style: AppTypography.bodySmall(context),
            ),
          ],
        ),
        const SizedBox(height: 4),
        Text(
          helperText,
          style: AppTypography.bodySmall(context).copyWith(
            color: ThemeColors.textSecondary(context),
          ),
        ),
      ],
    );
  }

  /// Constrói um campo de seleção múltipla com chips
  Widget _buildMultiSelectChipField<T>({
    required BuildContext context,
    required String title,
    required String helperText,
    required List<MultiSelectOption<T>> options,
    required List<T> selectedValues,
    required ValueChanged<List<T>> onChanged,
  }) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          title,
          style: AppTypography.labelMedium(context),
        ),
        const SizedBox(height: 8),
        Wrap(
          spacing: 8,
          runSpacing: 8,
          children: options.map((option) {
            final isSelected = selectedValues.contains(option.value);
            return FilterChip(
              label: Text(option.label),
              selected: isSelected,
              onSelected: (selected) {
                final List<T> newValues = List.from(selectedValues);
                if (selected) {
                  if (!newValues.contains(option.value)) {
                    newValues.add(option.value);
                  }
                } else {
                  newValues.remove(option.value);
                }
                onChanged(newValues);
              },
              selectedColor: AppColors.primary.withOpacity(0.2),
              checkmarkColor: AppColors.primary,
            );
          }).toList(),
        ),
        const SizedBox(height: 4),
        Text(
          helperText,
          style: AppTypography.bodySmall(context).copyWith(
            color: ThemeColors.textSecondary(context),
          ),
        ),
      ],
    );
  }

  /// Submete o formulário
  void _submitForm() {
    if (_formKey.currentState?.validate() ?? false) {
      // Construir dados da busca
      final searchData = {
        'name': _nameController.text,
        'description': _descriptionController.text,
        'dataset_id': _selectedDatasetId,
        'iterations': _iterations,
        'search_space': {
          'model_type': _selectedModelType,
          'model_size': _selectedModelSizes,
          'batch_size': {
            'min': _batchSizeRange.start.toInt(),
            'max': _batchSizeRange.end.toInt(),
          },
          'imgsz': _selectedImageSizes,
          'epochs': _epochs,
          'optimizer': _selectedOptimizers,
          'lr0': {
            'min': _learningRateRange.start,
            'max': _learningRateRange.end,
          },
          'device': _device,
        },
      };

      // Chamar a função de callback
      widget.onSubmit(searchData);
    }
  }

  /// Converte valor para escala logarítmica (para UI)
  double _logScale(double value, double min, double max) {
    // Evitar log(0)
    if (value <= 0) value = min;

    // Converter para 0-1 na escala log
    final minLog = log10(min);
    final maxLog = log10(max);
    final valueLog = log10(value);

    return (valueLog - minLog) / (maxLog - minLog);
  }

  /// Converte valor de escala logarítmica para escala real
  double _expScale(double value, double min, double max) {
    // Converter de 0-1 para escala real
    final minLog = log10(min);
    final maxLog = log10(max);
    final valueLog = minLog + value * (maxLog - minLog);

    return pow10(valueLog);
  }

  /// Calcula log base 10
  double log10(double x) => log(x) / log(10);

  /// Calcula 10^x
  double pow10(double x) => pow(10, x).toDouble();
}

/// Opção para seleção múltipla
class MultiSelectOption<T> {
  final T value;
  final String label;

  const MultiSelectOption({
    required this.value,
    required this.label,
  });
}