import 'package:flutter/material.dart';
import 'package:get/get.dart';
import 'package:microdetect/design_system/app_borders.dart';
import 'package:microdetect/design_system/app_colors.dart';
import 'package:microdetect/design_system/app_spacing.dart';
import 'package:microdetect/design_system/app_typography.dart';
import 'package:microdetect/features/camera/controllers/camera_controller.dart';
import 'package:microdetect/features/camera/widgets/camera_device_selector.dart';
import 'package:microdetect/features/datasets/widgets/dataset_selector.dart';

/// Painel de configurações para a câmera
class SettingsPanel extends StatelessWidget {
  final CameraController _controller = Get.find<CameraController>();

  SettingsPanel({super.key});

  @override
  Widget build(BuildContext context) {
    final isDarkMode = Get.isDarkMode;

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
            _buildSection(
              'Dataset',
              Icons.folder,
              Obx(() => DatasetSelector(
                datasetId: _controller.selectedDatasetId,
                onDatasetSelected: _controller.handleDatasetSelected,
              )),
              textColor,
            ),

            // Seletor de câmeras
            _buildSection(
              'Câmera',
              Icons.videocam,
              Obx(() {
                return CameraDeviceSelector(
                  cameras: _controller.availableCameras,
                  selectedCameraId: _controller.selectedCameraId,
                  onCameraSelected: _controller.changeCamera,
                  onRefreshCameras: _controller.refreshCameras,
                  isDarkMode: isDarkMode,
                );
              }),
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
          ],
        ),
      ),
    );
  }

  Widget _buildSection(String title,
      IconData icon,
      Widget child,
      Color textColor,) {
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

  Widget _buildResolutionSelector(bool isDarkMode,
      Color cardColor,
      Color borderColor,
      Color textColor,) {
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
    return Obx(() {
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
      groupValue: _controller.selectedResolution,
      value: value,
      activeColor: AppColors.primary,
      contentPadding: const EdgeInsets.symmetric(
        horizontal: AppSpacing.small,
        vertical: 0,
      ),
      onChanged: (value) {
        if (value != null) {
          _controller.handleResolutionChanged(value);
        }
      },
    );
    });
  }
}
