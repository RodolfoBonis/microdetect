import 'package:flutter/material.dart';
import 'package:microdetect/design_system/app_colors.dart';
import 'package:microdetect/design_system/app_spacing.dart';
import 'package:microdetect/design_system/app_typography.dart';
import 'package:microdetect/design_system/app_borders.dart';

/// Painel de ajustes para a câmera
class AdjustmentPanel extends StatefulWidget {
  /// Valores atuais dos ajustes
  final double brightness;
  final double contrast;
  final double saturation;
  final double sharpness;
  
  /// Filtro selecionado
  final String selectedFilter;

  /// Callbacks para mudanças nos ajustes
  final ValueChanged<double> onBrightnessChanged;
  final ValueChanged<double> onContrastChanged;
  final ValueChanged<double> onSaturationChanged;
  final ValueChanged<double> onSharpnessChanged;
  
  /// Callback para mudança de filtro
  final ValueChanged<String>? onFilterChanged;

  const AdjustmentPanel({
    Key? key,
    required this.brightness,
    required this.contrast,
    required this.saturation,
    required this.sharpness,
    this.selectedFilter = 'normal',
    required this.onBrightnessChanged,
    required this.onContrastChanged,
    required this.onSaturationChanged,
    required this.onSharpnessChanged,
    this.onFilterChanged,
  }) : super(key: key);

  @override
  State<AdjustmentPanel> createState() => _AdjustmentPanelState();
}

class _AdjustmentPanelState extends State<AdjustmentPanel> {
  // Valores locais para controle da UI
  late double _brightness;
  late double _contrast;
  late double _saturation;
  late double _sharpness;
  late String _currentFilter;
  
  @override
  void initState() {
    super.initState();
    _brightness = widget.brightness;
    _contrast = widget.contrast;
    _saturation = widget.saturation;
    _sharpness = widget.sharpness;
    _currentFilter = widget.selectedFilter;
  }
  
  @override
  void didUpdateWidget(AdjustmentPanel oldWidget) {
    super.didUpdateWidget(oldWidget);
    
    // Atualizar valores locais se os valores externos mudaram
    if (oldWidget.brightness != widget.brightness) {
      setState(() => _brightness = widget.brightness);
    }
    if (oldWidget.contrast != widget.contrast) {
      setState(() => _contrast = widget.contrast);
    }
    if (oldWidget.saturation != widget.saturation) {
      setState(() => _saturation = widget.saturation);
    }
    if (oldWidget.sharpness != widget.sharpness) {
      setState(() => _sharpness = widget.sharpness);
    }
    if (oldWidget.selectedFilter != widget.selectedFilter) {
      setState(() => _currentFilter = widget.selectedFilter);
    }
  }

  @override
  Widget build(BuildContext context) {
    // Obter o tema atual
    final theme = Theme.of(context);
    final isDarkMode = theme.brightness == Brightness.dark;
    
    // Adaptar cores com base no tema
    final backgroundColor = isDarkMode ? AppColors.backgroundDark : AppColors.white;
    final textColor = isDarkMode ? AppColors.white : AppColors.neutralDarkest;
    final borderColor = isDarkMode ? AppColors.neutralDark : AppColors.neutralLight;
    
    return Container(
      color: backgroundColor,
      padding: const EdgeInsets.all(AppSpacing.medium),
      child: SingleChildScrollView(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _buildFilterSection(isDarkMode, textColor, borderColor),
            const SizedBox(height: AppSpacing.large),
            _buildAdjustmentSlider(
              title: 'Brilho',
              value: _brightness,
              min: -1.0,
              max: 1.0,
              icon: Icons.brightness_6,
              onChanged: (value) {
                setState(() => _brightness = value);
                widget.onBrightnessChanged(value);
              },
              textColor: textColor,
              isDarkMode: isDarkMode,
            ),
            const SizedBox(height: AppSpacing.medium),
            _buildAdjustmentSlider(
              title: 'Contraste',
              value: _contrast,
              min: -1.0,
              max: 1.0,
              icon: Icons.contrast,
              onChanged: (value) {
                setState(() => _contrast = value);
                widget.onContrastChanged(value);
              },
              textColor: textColor,
              isDarkMode: isDarkMode,
            ),
            const SizedBox(height: AppSpacing.medium),
            _buildAdjustmentSlider(
              title: 'Saturação',
              value: _saturation,
              min: -1.0,
              max: 1.0,
              icon: Icons.color_lens,
              onChanged: (value) {
                setState(() => _saturation = value);
                widget.onSaturationChanged(value);
              },
              textColor: textColor,
              isDarkMode: isDarkMode,
            ),
            const SizedBox(height: AppSpacing.medium),
            _buildAdjustmentSlider(
              title: 'Nitidez',
              value: _sharpness,
              min: 0.0,
              max: 1.0,
              icon: Icons.filter_center_focus,
              onChanged: (value) {
                setState(() => _sharpness = value);
                widget.onSharpnessChanged(value);
              },
              textColor: textColor,
              isDarkMode: isDarkMode,
            ),
            const SizedBox(height: AppSpacing.medium),
            _buildResetButton(isDarkMode),
          ],
        ),
      ),
    );
  }
  
  Widget _buildFilterSection(bool isDarkMode, Color textColor, Color borderColor) {
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
              _buildFilterOption('normal', 'Normal', isDarkMode, borderColor, textColor),
              _buildFilterOption('grayscale', 'Preto e Branco', isDarkMode, borderColor, textColor),
              _buildFilterOption('sepia', 'Sépia', isDarkMode, borderColor, textColor),
              _buildFilterOption('invert', 'Invertido', isDarkMode, borderColor, textColor),
            ],
          ),
        ),
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
    final isSelected = value == _currentFilter;
    
    return Padding(
      padding: const EdgeInsets.only(right: AppSpacing.small),
      child: InkWell(
        onTap: () {
          setState(() => _currentFilter = value);
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
                borderRadius: BorderRadius.circular(AppBorders.radiusMedium - (isSelected ? 3 : 2)),
                child: Stack(
                  children: [
                    ColorFiltered(
                      colorFilter: ColorFilter.matrix(
                        value == 'grayscale' ? [
                          0.2126, 0.7152, 0.0722, 0, 0,
                          0.2126, 0.7152, 0.0722, 0, 0,
                          0.2126, 0.7152, 0.0722, 0, 0,
                          0, 0, 0, 1, 0,
                        ] : value == 'sepia' ? [
                          0.393, 0.769, 0.189, 0, 0,
                          0.349, 0.686, 0.168, 0, 0,
                          0.272, 0.534, 0.131, 0, 0,
                          0, 0, 0, 1, 0,
                        ] : value == 'invert' ? [
                          -1, 0, 0, 0, 255,
                          0, -1, 0, 0, 255,
                          0, 0, -1, 0, 255,
                          0, 0, 0, 1, 0,
                        ] : [
                          1, 0, 0, 0, 0,
                          0, 1, 0, 0, 0,
                          0, 0, 1, 0, 0,
                          0, 0, 0, 1, 0,
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
                color: isDarkMode ? AppColors.neutralLight : AppColors.neutralDark,
              ),
            ),
          ],
        ),
        Slider(
          value: value,
          min: min,
          max: max,
          activeColor: AppColors.primary,
          inactiveColor: isDarkMode ? AppColors.neutralDark : AppColors.neutralLight,
          onChanged: onChanged,
        ),
      ],
    );
  }
  
  Widget _buildResetButton(bool isDarkMode) {
    return Center(
      child: TextButton.icon(
        onPressed: () {
          // Redefinir todos os valores para os padrões
          setState(() {
            _brightness = 0.0;
            _contrast = 0.0;
            _saturation = 0.0;
            _sharpness = 0.0;
            _currentFilter = 'normal';
          });
          
          // Chamar os callbacks para atualizar os widgets pai
          widget.onBrightnessChanged(0.0);
          widget.onContrastChanged(0.0);
          widget.onSaturationChanged(0.0);
          widget.onSharpnessChanged(0.0);
          widget.onFilterChanged?.call('normal');
        },
        icon: const Icon(Icons.refresh, color: AppColors.primary),
        label: Text(
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