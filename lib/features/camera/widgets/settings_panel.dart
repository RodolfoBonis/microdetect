import 'package:flutter/material.dart';
import 'package:camera_access/camera_access.dart';
import 'package:get/get.dart';
import 'package:microdetect/design_system/app_colors.dart';
import 'package:microdetect/design_system/app_spacing.dart';
import 'package:microdetect/design_system/app_typography.dart';
import 'package:microdetect/design_system/app_borders.dart';
import 'package:microdetect/features/camera/widgets/camera_device_selector.dart';
import 'package:microdetect/core/services/api_service.dart';
import 'package:microdetect/features/datasets/controllers/dataset_controller.dart';
import 'package:microdetect/features/datasets/models/dataset.dart';

/// Painel de configurações para a câmera
class SettingsPanel extends StatefulWidget {
  /// Lista de câmeras disponíveis
  final List<CameraDevice> cameras;

  /// ID da câmera selecionada
  final String selectedCameraId;

  /// Resolução atual
  final String resolution;

  /// Balanço de branco atual
  final String whiteBalance;

  /// Filtro atual
  final String filter;

  /// Callback quando uma câmera é selecionada
  final ValueChanged<String> onCameraSelected;

  /// Callback para atualizar a lista de câmeras
  final VoidCallback onRefreshCameras;

  /// Callback para mudança de resolução
  final ValueChanged<String>? onResolutionChanged;

  /// Callback para mudança de balanço de branco
  final ValueChanged<String>? onWhiteBalanceChanged;

  /// Callback para mudança de filtro
  final ValueChanged<String>? onFilterChanged;

  /// ID do dataset atual (quando aberto de um dataset)
  final int? datasetId;

  /// Callback quando um dataset é selecionado
  final ValueChanged<int>? onDatasetSelected;

  const SettingsPanel({
    Key? key,
    required this.cameras,
    required this.selectedCameraId,
    this.resolution = 'hd',
    this.whiteBalance = 'auto',
    this.filter = 'normal',
    required this.onCameraSelected,
    required this.onRefreshCameras,
    this.onResolutionChanged,
    this.onWhiteBalanceChanged,
    this.onFilterChanged,
    this.datasetId,
    this.onDatasetSelected,
  }) : super(key: key);

  @override
  State<SettingsPanel> createState() => _SettingsPanelState();
}

class _SettingsPanelState extends State<SettingsPanel> {
  // Variáveis de controle para o estado da UI
  late String _resolution;
  late String _whiteBalance;
  late String _filterMode;

  final DatasetController _datasetController = Get.find();

  @override
  void initState() {
    super.initState();
    _resolution = widget.resolution;
    _whiteBalance = widget.whiteBalance;
    _filterMode = widget.filter;

    _datasetController.fetchDatasets();
  }

  @override
  void didUpdateWidget(SettingsPanel oldWidget) {
    super.didUpdateWidget(oldWidget);

    // Verificar se a resolução foi alterada externamente e atualizar a UI
    if (oldWidget.resolution != widget.resolution) {
      setState(() {
        _resolution = widget.resolution;
      });
    }

    if (oldWidget.whiteBalance != widget.whiteBalance) {
      _whiteBalance = widget.whiteBalance;
    }
    if (oldWidget.filter != widget.filter) {
      _filterMode = widget.filter;
    }

    // Verificar se mudou entre ter um dataset fixo ou não
    if (oldWidget.datasetId != widget.datasetId &&
        widget.datasetId == null &&
        widget.onDatasetSelected != null) {
      _datasetController.fetchDatasets();
    }
  }

  @override
  Widget build(BuildContext context) {
    // Obter o tema atual
    final theme = Theme.of(context);
    final isDarkMode = theme.brightness == Brightness.dark;

    // Adaptar cores com base no tema
    final backgroundColor =
        isDarkMode ? AppColors.backgroundDark : AppColors.white;
    final textColor = isDarkMode ? AppColors.white : AppColors.neutralDarkest;
    final cardColor = isDarkMode ? AppColors.surfaceDark : AppColors.white;
    final cardBorderColor =
        isDarkMode ? AppColors.neutralDark : AppColors.neutralLight;

    return Container(
      decoration: BoxDecoration(
        color: backgroundColor,
      ),
      child: SingleChildScrollView(
        padding: const EdgeInsets.all(AppSpacing.medium),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Seletor de datasets (apenas quando não estiver em um dataset específico)
            Obx(
              () => _buildSection(
                'Dataset',
                Icons.folder,
                _buildDatasetSelector(
                  isDarkMode,
                  cardColor,
                  cardBorderColor,
                  textColor,
                ),
                textColor,
              ),
            ),

            // Seletor de câmeras
            _buildSection(
              'Câmera',
              Icons.videocam,
              CameraDeviceSelector(
                cameras: widget.cameras,
                selectedCameraId: widget.selectedCameraId,
                onCameraSelected: widget.onCameraSelected,
                onRefreshCameras: widget.onRefreshCameras,
                isDarkMode: isDarkMode,
              ),
              textColor,
            ),

            // Seletor de resolução
            _buildSection(
              'Resolução',
              Icons.tune,
              _buildResolutionSelector(
                isDarkMode,
                cardColor,
                cardBorderColor,
                textColor,
              ),
              textColor,
            ),

            // Seletor de balanço de branco
            _buildSection(
              'Balanço de Branco',
              Icons.wb_auto,
              _buildWhiteBalanceSelector(
                isDarkMode,
                cardColor,
                cardBorderColor,
                textColor,
              ),
              textColor,
            ),

            // Filtros de imagem
            _buildSection(
              'Filtros',
              Icons.filter,
              _buildFilterSelector(
                isDarkMode,
                cardColor,
                cardBorderColor,
                textColor,
              ),
              textColor,
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildSection(
    String title,
    IconData icon,
    Widget child,
    Color textColor,
  ) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            Icon(icon, color: AppColors.primary, size: 20),
            const SizedBox(width: AppSpacing.small),
            Text(
              title,
              style: AppTypography.textTheme.titleMedium?.copyWith(
                color: textColor,
                fontWeight: FontWeight.w500,
              ),
            ),
          ],
        ),
        const SizedBox(height: AppSpacing.small),
        child,
        const SizedBox(height: AppSpacing.medium),
      ],
    );
  }

  Widget _buildResolutionSelector(
    bool isDarkMode,
    Color cardColor,
    Color borderColor,
    Color textColor,
  ) {
    return Card(
      elevation: 0,
      color: cardColor,
      margin: EdgeInsets.zero,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(AppBorders.radiusMedium),
        side: BorderSide(color: borderColor),
      ),
      child: Padding(
        padding: const EdgeInsets.all(AppSpacing.small),
        child: Column(
          children: [
            _buildResolutionOption(
                'sd', 'SD', '640x480', isDarkMode, textColor),
            _buildResolutionOption(
                'hd', 'HD', '1280x720', isDarkMode, textColor),
            _buildResolutionOption(
                'fullhd', 'Full HD', '1920x1080', isDarkMode, textColor),
          ],
        ),
      ),
    );
  }

  Widget _buildResolutionOption(
    String value,
    String label,
    String description,
    bool isDarkMode,
    Color textColor,
  ) {
    return RadioListTile<String>(
      title: Text(
        label,
        style: AppTypography.textTheme.bodyMedium?.copyWith(
          fontWeight: FontWeight.w500,
          color: textColor,
        ),
      ),
      subtitle: Text(
        description,
        style: AppTypography.textTheme.bodySmall?.copyWith(
          color: isDarkMode ? AppColors.neutralLight : AppColors.neutralDark,
        ),
      ),
      value: value,
      groupValue: _resolution,
      activeColor: AppColors.primary,
      contentPadding: const EdgeInsets.symmetric(
        horizontal: AppSpacing.small,
        vertical: 0,
      ),
      onChanged: (value) {
        if (value != null) {
          setState(() => _resolution = value);
          widget.onResolutionChanged?.call(value);
        }
      },
    );
  }

  Widget _buildWhiteBalanceSelector(
    bool isDarkMode,
    Color cardColor,
    Color borderColor,
    Color textColor,
  ) {
    final options = [
      {'value': 'auto', 'label': 'Automático'},
      {'value': 'sunny', 'label': 'Luz do dia'},
      {'value': 'cloudy', 'label': 'Nublado'},
      {'value': 'tungsten', 'label': 'Tungstênio'},
      {'value': 'fluorescent', 'label': 'Fluorescente'},
    ];

    return Card(
      elevation: 0,
      color: cardColor,
      margin: EdgeInsets.zero,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(AppBorders.radiusMedium),
        side: BorderSide(color: borderColor),
      ),
      child: DropdownButtonFormField<String>(
        value: _whiteBalance,
        decoration: InputDecoration(
          filled: true,
          fillColor: cardColor,
          border: OutlineInputBorder(
            borderRadius: BorderRadius.circular(AppBorders.radiusMedium),
            borderSide: BorderSide.none,
          ),
          contentPadding: const EdgeInsets.symmetric(
            horizontal: AppSpacing.medium,
            vertical: AppSpacing.small,
          ),
        ),
        dropdownColor: cardColor,
        icon: const Icon(Icons.keyboard_arrow_down, color: AppColors.primary),
        isExpanded: true,
        style: TextStyle(
            color: textColor,
            fontSize: 16.0,
            fontWeight: FontWeight.w500,
            fontFamily: 'Cereal'),
        itemHeight: 50,
        items: options
            .map((option) => DropdownMenuItem<String>(
                  value: option['value'],
                  child: Text(
                    option['label']!,
                    style: TextStyle(
                        color: textColor,
                        fontSize: 16.0,
                        fontWeight: FontWeight.w500,
                        fontFamily: 'Cereal'),
                  ),
                ))
            .toList(),
        onChanged: (value) {
          if (value != null) {
            setState(() => _whiteBalance = value);
            widget.onWhiteBalanceChanged?.call(value);
          }
        },
      ),
    );
  }

  Widget _buildFilterSelector(
    bool isDarkMode,
    Color cardColor,
    Color borderColor,
    Color textColor,
  ) {
    return SingleChildScrollView(
      scrollDirection: Axis.horizontal,
      child: Row(
        children: [
          _buildFilterOption(
              'normal', 'Normal', isDarkMode, borderColor, textColor),
          _buildFilterOption('grayscale', 'Preto e Branco', isDarkMode,
              borderColor, textColor),
          _buildFilterOption(
              'sepia', 'Sépia', isDarkMode, borderColor, textColor),
          _buildFilterOption(
              'invert', 'Invertido', isDarkMode, borderColor, textColor),
        ],
      ),
    );
  }

  Widget _buildFilterOption(
    String value,
    String label,
    bool isDarkMode,
    Color borderColor,
    Color textColor,
  ) {
    final isSelected = _filterMode == value;

    return Padding(
      padding: const EdgeInsets.only(right: AppSpacing.small),
      child: InkWell(
        onTap: () {
          final oldFilter = _filterMode;
          setState(() => _filterMode = value);

          // Log detalhado para debug
          print('Filtro selecionado: $value (anterior: $oldFilter)');

          // Sempre notifique mudanças, mesmo que seja para o mesmo filtro (isso ajuda a resetar)
          widget.onFilterChanged?.call(value);
        },
        borderRadius: BorderRadius.circular(AppBorders.radiusMedium),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Container(
              width: 70,
              height: 70,
              decoration: BoxDecoration(
                border: Border.all(
                  color: isSelected ? AppColors.primary : borderColor,
                  width: isSelected ? 3 : 2,
                ),
                borderRadius: BorderRadius.circular(AppBorders.radiusMedium),
              ),
              child: ClipRRect(
                borderRadius: BorderRadius.circular(
                    AppBorders.radiusMedium - (isSelected ? 3 : 2)),
                child: Stack(
                  children: [
                    ColorFiltered(
                      colorFilter: ColorFilter.matrix(
                        value == 'grayscale'
                            ? [
                                0.2126,
                                0.7152,
                                0.0722,
                                0,
                                0,
                                0.2126,
                                0.7152,
                                0.0722,
                                0,
                                0,
                                0.2126,
                                0.7152,
                                0.0722,
                                0,
                                0,
                                0,
                                0,
                                0,
                                1,
                                0,
                              ]
                            : value == 'sepia'
                                ? [
                                    0.393,
                                    0.769,
                                    0.189,
                                    0,
                                    0,
                                    0.349,
                                    0.686,
                                    0.168,
                                    0,
                                    0,
                                    0.272,
                                    0.534,
                                    0.131,
                                    0,
                                    0,
                                    0,
                                    0,
                                    0,
                                    1,
                                    0,
                                  ]
                                : value == 'invert'
                                    ? [
                                        -1,
                                        0,
                                        0,
                                        0,
                                        255,
                                        0,
                                        -1,
                                        0,
                                        0,
                                        255,
                                        0,
                                        0,
                                        -1,
                                        0,
                                        255,
                                        0,
                                        0,
                                        0,
                                        1,
                                        0,
                                      ]
                                    : [
                                        1,
                                        0,
                                        0,
                                        0,
                                        0,
                                        0,
                                        1,
                                        0,
                                        0,
                                        0,
                                        0,
                                        0,
                                        1,
                                        0,
                                        0,
                                        0,
                                        0,
                                        0,
                                        1,
                                        0,
                                      ],
                      ),
                      child: Image.asset(
                        'assets/images/filter_preview.jpg',
                        fit: BoxFit.cover,
                        errorBuilder: (context, error, stackTrace) {
                          return Container(
                            color: AppColors.neutralLight,
                            child: const Center(
                              child: Icon(
                                Icons.image,
                                color: AppColors.neutralDark,
                              ),
                            ),
                          );
                        },
                      ),
                    ),
                    if (isSelected)
                      Positioned(
                        right: 5,
                        top: 5,
                        child: Container(
                          padding: const EdgeInsets.all(2),
                          decoration: const BoxDecoration(
                            color: AppColors.primary,
                            shape: BoxShape.circle,
                          ),
                          child: const Icon(
                            Icons.check,
                            color: AppColors.white,
                            size: 16,
                          ),
                        ),
                      ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: AppSpacing.xxSmall),
            Text(
              label,
              style: AppTypography.textTheme.bodySmall?.copyWith(
                color: isSelected ? AppColors.primary : textColor,
                fontWeight: isSelected ? FontWeight.w500 : FontWeight.normal,
              ),
            ),
          ],
        ),
      ),
    );
  }

  /// Constrói o seletor de datasets
  Widget _buildDatasetSelector(
    bool isDarkMode,
    Color cardColor,
    Color borderColor,
    Color textColor,
  ) {
    // Se estiver carregando
    if (_datasetController.isLoading) {
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
              SizedBox(
                width: 20,
                height: 20,
                child: CircularProgressIndicator(
                  strokeWidth: 2,
                  valueColor: AlwaysStoppedAnimation<Color>(
                    isDarkMode ? AppColors.white : AppColors.primary,
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
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'Nenhum dataset disponível',
                style: AppTypography.textTheme.bodyMedium?.copyWith(
                  color: textColor,
                ),
              ),
              const SizedBox(height: AppSpacing.small),
              ElevatedButton.icon(
                onPressed: _datasetController.fetchDatasets,
                icon: const Icon(Icons.refresh, size: 16),
                label: const Text('Atualizar'),
                style: ElevatedButton.styleFrom(
                  backgroundColor: AppColors.primary,
                  foregroundColor: AppColors.white,
                  textStyle: const TextStyle(fontWeight: FontWeight.w500),
                  padding: const EdgeInsets.symmetric(
                    horizontal: AppSpacing.small,
                    vertical: AppSpacing.xxSmall,
                  ),
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
                  onPressed: _datasetController.fetchDatasets,
                  tooltip: 'Atualizar datasets',
                  color: AppColors.primary,
                  padding: EdgeInsets.zero,
                  constraints: const BoxConstraints(),
                ),
              ],
            ),
            const SizedBox(height: AppSpacing.small),
            DropdownButtonFormField<int>(
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
                'Selecione um dataset',
                style: AppTypography.textTheme.bodyMedium?.copyWith(
                  color: isDarkMode
                      ? AppColors.neutralLight
                      : AppColors.neutralDark,
                ),
              ),
              items: _datasetController.datasets.map((dataset) {
                return DropdownMenuItem<int>(
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
              onChanged: (datasetId) {
                if (datasetId != null) {
                  widget.onDatasetSelected?.call(datasetId);
                }
              },
            ),
          ],
        ),
      ),
    );
  }
}
