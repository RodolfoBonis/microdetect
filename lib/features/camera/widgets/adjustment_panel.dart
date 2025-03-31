import 'package:flutter/material.dart';
import 'package:get/get.dart';
import 'package:microdetect/design_system/app_colors.dart';
import 'package:microdetect/design_system/app_spacing.dart';
import 'package:microdetect/design_system/app_typography.dart';
import 'package:microdetect/design_system/app_borders.dart';
import 'package:microdetect/features/camera/controllers/camera_controller.dart';

/// Painel de ajustes para a câmera
class AdjustmentPanel extends StatelessWidget {
  final CameraController _controller = Get.find<CameraController>();

  AdjustmentPanel({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    final isDarkMode = Get.isDarkMode;

    // Adaptar cores com base no tema
    final backgroundColor =
        isDarkMode ? AppColors.backgroundDark : AppColors.white;
    final textColor = isDarkMode ? AppColors.white : AppColors.neutralDarkest;
    final borderColor =
        isDarkMode ? AppColors.neutralDark : AppColors.neutralLight;

    return Container(
      color: backgroundColor,
      padding: const EdgeInsets.all(AppSpacing.medium),
      child: SingleChildScrollView(
        child: Obx(() {
          return Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              _buildFilterSection(isDarkMode, textColor, borderColor),
              const SizedBox(height: AppSpacing.large),
              _buildWhiteBalanceSelector(
                isDarkMode,
                backgroundColor,
                borderColor,
                textColor,
              ),
              const SizedBox(height: AppSpacing.large),
              _buildAdjustmentSlider(
                title: 'Brilho',
                value: _controller.brightness,
                min: -1.0,
                max: 1.0,
                icon: Icons.brightness_6,
                onChanged: (value) {
                  _controller.applyBrightness(value);
                },
                textColor: textColor,
                isDarkMode: isDarkMode,
              ),
              const SizedBox(height: AppSpacing.medium),
              _buildAdjustmentSlider(
                title: 'Contraste',
                value: _controller.contrast,
                min: -1.0,
                max: 1.0,
                icon: Icons.contrast,
                onChanged: (value) {
                  _controller.applyContrast(value);
                },
                textColor: textColor,
                isDarkMode: isDarkMode,
              ),
              const SizedBox(height: AppSpacing.medium),
              _buildAdjustmentSlider(
                title: 'Saturação',
                value: _controller.saturation,
                min: -1.0,
                max: 1.0,
                icon: Icons.color_lens,
                onChanged: (value) {
                  _controller.applySaturation(value);
                },
                textColor: textColor,
                isDarkMode: isDarkMode,
              ),
              const SizedBox(height: AppSpacing.medium),
              _buildAdjustmentSlider(
                title: 'Nitidez',
                value: _controller.sharpness,
                min: 0.0,
                max: 1.0,
                icon: Icons.filter_center_focus,
                onChanged: (value) {
                  _controller.applySharpness(value);
                },
                textColor: textColor,
                isDarkMode: isDarkMode,
              ),
              const SizedBox(height: AppSpacing.medium),
              _buildResetButton(isDarkMode),
            ],
          );
        }),
      ),
    );
  }

  Widget _buildFilterSection(
      bool isDarkMode, Color textColor, Color borderColor) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            const Icon(Icons.filter, color: AppColors.primary, size: 20),
            const SizedBox(width: AppSpacing.small),
            Text(
              'Filtros',
              style: AppTypography.textTheme.titleMedium?.copyWith(
                color: textColor,
                fontWeight: FontWeight.w500,
              ),
            ),
          ],
        ),
        const SizedBox(height: AppSpacing.small),
        SingleChildScrollView(
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
        ),
      ],
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

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            const Icon(Icons.wb_auto, color: AppColors.primary, size: 20),
            const SizedBox(width: AppSpacing.small),
            Text(
              "Balanço de Branco",
              style: AppTypography.textTheme.titleMedium?.copyWith(
                color: textColor,
                fontWeight: FontWeight.w500,
              ),
            ),
          ],
        ),
        const SizedBox(height: AppSpacing.small),
        Card(
          elevation: 0,
          color: cardColor,
          margin: EdgeInsets.zero,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(AppBorders.radiusMedium),
            side: BorderSide(color: borderColor),
          ),
          child: DropdownButtonFormField<String>(
            value: _controller.selectedWhiteBalance,
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
            icon:
                const Icon(Icons.keyboard_arrow_down, color: AppColors.primary),
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
                _controller.handleWhiteBalanceChanged(value);
              }
            },
          ),
        ),
        const SizedBox(height: AppSpacing.medium),
      ],
    );
  }

  Widget _buildFilterOption(
    String value,
    String label,
    bool isDarkMode,
    Color borderColor,
    Color textColor,
  ) {
    final isSelected = value == _controller.selectedFilter;

    return Padding(
      padding: const EdgeInsets.only(right: AppSpacing.small),
      child: InkWell(
        onTap: () {
          _controller.handleFilterChanged(value);
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

  Widget _buildAdjustmentSlider({
    required String title,
    required double value,
    required double min,
    required double max,
    required IconData icon,
    required Function(double) onChanged,
    required Color textColor,
    required bool isDarkMode,
  }) {
    // Determinar valor formatado para exibição
    String displayValue;
    if (min == -1.0 && max == 1.0) {
      // Para ajustes com -1.0 a 1.0, exibir como porcentagem
      final percentage = ((value + 1.0) / 2.0 * 100).round();
      displayValue = '${percentage.toString()}%';
    } else {
      // Para outros ajustes, exibir o valor numérico com 2 casas decimais
      displayValue = value.toStringAsFixed(2);
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            Icon(icon, color: AppColors.primary, size: 18),
            const SizedBox(width: AppSpacing.xSmall),
            Text(
              title,
              style: AppTypography.textTheme.bodyMedium?.copyWith(
                color: textColor,
                fontWeight: FontWeight.w500,
              ),
            ),
            const Spacer(),
            Text(
              displayValue,
              style: AppTypography.textTheme.bodySmall?.copyWith(
                color:
                    isDarkMode ? AppColors.neutralLight : AppColors.neutralDark,
              ),
            ),
          ],
        ),
        Slider(
          value: value,
          min: min,
          max: max,
          activeColor: AppColors.primary,
          inactiveColor:
              isDarkMode ? AppColors.neutralDark : AppColors.neutralLight,
          onChanged: onChanged,
        ),
      ],
    );
  }

  Widget _buildResetButton(bool isDarkMode) {
    return Center(
      child: TextButton.icon(
        onPressed: () {
          // Chamar os callbacks para atualizar os widgets pai
          _controller.applyBrightness(0.0);
          _controller.applyContrast(0.0);
          _controller.applySaturation(0.0);
          _controller.applySharpness(0.0);
          _controller.handleFilterChanged('normal');
        },
        icon: const Icon(Icons.refresh, color: AppColors.primary),
        label: const Text(
          'Redefinir ajustes',
          style: TextStyle(
            color: AppColors.primary,
            fontWeight: FontWeight.w500,
          ),
        ),
      ),
    );
  }
}
