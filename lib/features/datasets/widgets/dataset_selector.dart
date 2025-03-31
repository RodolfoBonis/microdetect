import 'package:flutter/material.dart';
import 'package:get/get.dart';
import 'package:microdetect/design_system/app_colors.dart';
import 'package:microdetect/design_system/app_spacing.dart';
import 'package:microdetect/design_system/app_typography.dart';
import 'package:microdetect/design_system/app_borders.dart';
import 'package:microdetect/features/datasets/controllers/dataset_controller.dart';
import 'package:microdetect/features/datasets/models/dataset.dart';

/// Widget para seleção de datasets
///
/// Este widget permite selecionar um dataset a partir da lista de datasets disponíveis.
/// Pode ser usado em múltiplos módulos da aplicação, como câmera e anotação.
class DatasetSelector extends StatefulWidget {
  /// ID do dataset selecionado
  final int? datasetId;

  /// Callback quando um dataset é selecionado
  final ValueChanged<Dataset?>? onDatasetSelected;

  /// Texto de hint para exibir quando nenhum dataset está selecionado
  final String hint;

  /// Se o seletor deve ser somente leitura
  final bool readOnly;

  const DatasetSelector({
    Key? key,
    this.datasetId,
    this.onDatasetSelected,
    this.hint = 'Selecione um dataset',
    this.readOnly = false,
  }) : super(key: key);

  @override
  State<DatasetSelector> createState() => _DatasetSelectorState();
}

class _DatasetSelectorState extends State<DatasetSelector> {
  final RxBool _isControllerAvailable = true.obs;
  final RxBool _isLoading = false.obs;
  final RxBool _isRetrying = false.obs;

  final DatasetController _datasetController = Get.find<DatasetController>(tag: 'datasetController');

  /// Processa a seleção de um dataset
  void _handleDatasetSelection(int? datasetId) {
    if (datasetId == null) {
      widget.onDatasetSelected?.call(null);
      return;
    }

    final dataset = _datasetController.datasets.firstWhereOrNull((d) => d.id == datasetId);
    if (dataset != null) {
      widget.onDatasetSelected?.call(dataset);
    }
  }

  @override
  Widget build(BuildContext context) {
    // Obter o tema atual
    final theme = Theme.of(context);
    final isDarkMode = theme.brightness == Brightness.dark;

    // Adaptar cores com base no tema
    final textColor = isDarkMode ? AppColors.white : AppColors.neutralDarkest;
    final cardColor = isDarkMode ? AppColors.surfaceDark : AppColors.white;
    final borderColor = isDarkMode ? AppColors.neutralDark : AppColors.neutralLight;

    return Obx(() {
      // Se o controlador não estiver disponível ou estiver retentando
      if (!_isControllerAvailable.value && _isRetrying.value) {
        return Card(
          elevation: 0,
          color: cardColor,
          margin: EdgeInsets.zero,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(AppBorders.radiusMedium),
            side: BorderSide(color: borderColor),
          ),
          child: Padding(
            padding: const EdgeInsets.all(AppSpacing.medium),
            child: Row(
              children: [
                const SizedBox(
                  width: 20,
                  height: 20,
                  child: CircularProgressIndicator(
                    strokeWidth: 2,
                    valueColor: AlwaysStoppedAnimation<Color>(
                      AppColors.primary,
                    ),
                  ),
                ),
                const SizedBox(width: AppSpacing.small),
                Text(
                  'Recuperando lista de datasets...',
                  style: AppTypography.textTheme.bodyMedium?.copyWith(
                    color: textColor,
                  ),
                ),
              ],
            ),
          ),
        );
      }

      // Se estiver carregando
      if (_isLoading.value) {
        return Card(
          elevation: 0,
          color: cardColor,
          margin: EdgeInsets.zero,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(AppBorders.radiusMedium),
            side: BorderSide(color: borderColor),
          ),
          child: Padding(
            padding: const EdgeInsets.all(AppSpacing.medium),
            child: Row(
              children: [
                const SizedBox(
                  width: 20,
                  height: 20,
                  child: CircularProgressIndicator(
                    strokeWidth: 2,
                    valueColor: AlwaysStoppedAnimation<Color>(
                      AppColors.primary,
                    ),
                  ),
                ),
                const SizedBox(width: AppSpacing.small),
                Text(
                  'Carregando datasets...',
                  style: AppTypography.textTheme.bodyMedium?.copyWith(
                    color: textColor,
                  ),
                ),
              ],
            ),
          ),
        );
      }

      // Se não houver datasets
      if (_datasetController.datasets.isEmpty) {
        return Card(
          elevation: 0,
          color: cardColor,
          margin: EdgeInsets.zero,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(AppBorders.radiusMedium),
            side: BorderSide(color: borderColor),
          ),
          child: Padding(
            padding: const EdgeInsets.all(AppSpacing.medium),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.center,
              children: [
                Icon(
                  Icons.folder_off,
                  size: 36,
                  color: AppColors.neutralLight,
                ),
                const SizedBox(height: AppSpacing.small),
                Text(
                  'Nenhum dataset disponível',
                  style: AppTypography.textTheme.titleSmall?.copyWith(
                    color: textColor,
                    fontWeight: FontWeight.w500,
                  ),
                  textAlign: TextAlign.center,
                ),
                const SizedBox(height: AppSpacing.xxSmall),
                Text(
                  'Crie um dataset na tela de Datasets ou atualize para verificar novamente.',
                  style: AppTypography.textTheme.bodySmall?.copyWith(
                    color: isDarkMode ? AppColors.neutralLight : AppColors.neutralDark,
                  ),
                  textAlign: TextAlign.center,
                ),
                const SizedBox(height: AppSpacing.medium),
                FilledButton.icon(
                  onPressed: _datasetController.fetchDatasets,
                  icon: const Icon(Icons.refresh, size: 18),
                  label: const Text('Atualizar Lista'),
                  style: FilledButton.styleFrom(
                    backgroundColor: AppColors.primary,
                    foregroundColor: AppColors.white,
                    minimumSize: const Size(200, 40),
                  ),
                ),
              ],
            ),
          ),
        );
      }

      // Usar um dropdown para seleção de datasets
      return Card(
        elevation: 0,
        color: cardColor,
        margin: EdgeInsets.zero,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(AppBorders.radiusMedium),
          side: BorderSide(color: borderColor),
        ),
        child: Padding(
          padding: const EdgeInsets.all(AppSpacing.medium),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text(
                    'Selecione um dataset:',
                    style: AppTypography.textTheme.bodyMedium?.copyWith(
                      color: textColor,
                      fontWeight: FontWeight.w500,
                    ),
                  ),
                  IconButton(
                    icon: const Icon(Icons.refresh, size: 18),
                    onPressed: widget.readOnly ? null : _datasetController.fetchDatasets,
                    tooltip: 'Atualizar datasets',
                    color: widget.readOnly ? AppColors.neutralLight : AppColors.primary,
                    padding: EdgeInsets.zero,
                    constraints: const BoxConstraints(),
                  ),
                ],
              ),
              const SizedBox(height: AppSpacing.small),
              DropdownButtonFormField<int?>(
                decoration: InputDecoration(
                  filled: true,
                  fillColor: cardColor,
                  contentPadding: const EdgeInsets.symmetric(
                    horizontal: AppSpacing.small,
                    vertical: AppSpacing.xxSmall,
                  ),
                  border: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(AppBorders.radiusSmall),
                    borderSide: BorderSide(color: borderColor),
                  ),
                  enabledBorder: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(AppBorders.radiusSmall),
                    borderSide: BorderSide(color: borderColor),
                  ),
                ),
                isExpanded: true,
                value: widget.datasetId,
                icon: const Icon(Icons.arrow_drop_down, color: AppColors.primary),
                dropdownColor: cardColor,
                hint: Text(
                  widget.hint,
                  style: AppTypography.textTheme.bodyMedium?.copyWith(
                    color: isDarkMode ? AppColors.neutralLight : AppColors.neutralDark,
                  ),
                ),
                items: [
                  // Opção para remover a seleção
                  if (!widget.readOnly)
                    DropdownMenuItem<int?>(
                      value: null,
                      child: Text(
                        'Nenhum dataset',
                        style: AppTypography.textTheme.bodyMedium?.copyWith(
                          color: isDarkMode ? AppColors.neutralLight : AppColors.neutralDark,
                          fontStyle: FontStyle.italic,
                        ),
                      ),
                    ),
                  // Lista de datasets disponíveis
                  ..._datasetController.datasets.map((dataset) {
                    return DropdownMenuItem<int?>(
                      value: dataset.id,
                      child: Text(
                        dataset.name + (' (${dataset.imagesCount} imagens)'),
                        style: AppTypography.textTheme.bodyMedium?.copyWith(
                          color: textColor,
                        ),
                        overflow: TextOverflow.ellipsis,
                      ),
                    );
                  }).toList(),
                ],
                onChanged: widget.readOnly ? null : _handleDatasetSelection,
              ),
            ],
          ),
        ),
      );
    });
  }
}
