import 'package:flutter/material.dart';
import 'package:camera_access/camera_access.dart';
import 'package:microdetect/design_system/app_colors.dart';
import 'package:microdetect/design_system/app_spacing.dart';
import 'package:microdetect/design_system/app_typography.dart';
import 'package:microdetect/design_system/app_borders.dart';
import 'package:microdetect/design_system/app_buttons.dart';

/// Widget para seleção de dispositivos de câmera
class CameraDeviceSelector extends StatefulWidget {
  /// Lista de câmeras disponíveis
  final List<CameraDevice> cameras;
  
  /// ID da câmera selecionada
  final String selectedCameraId;
  
  /// Callback quando uma câmera é selecionada
  final ValueChanged<String> onCameraSelected;
  
  /// Callback para atualizar a lista de câmeras
  final VoidCallback onRefreshCameras;

  final bool isDarkMode;
  
  const CameraDeviceSelector({
    Key? key,
    required this.cameras,
    required this.selectedCameraId,
    required this.onCameraSelected,
    required this.onRefreshCameras,
    required this.isDarkMode,
  }) : super(key: key);

  @override
  State<CameraDeviceSelector> createState() => _CameraDeviceSelectorState();
}

class _CameraDeviceSelectorState extends State<CameraDeviceSelector> {

  @override
  Widget build(BuildContext context) {
    final titleColor = widget.isDarkMode ? AppColors.neutralLightest : AppColors.neutralDarkest;
    return Card(
      elevation: 0,
      margin: EdgeInsets.zero,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(AppBorders.radiusMedium),
        side: const BorderSide(color: AppColors.neutralLight),
      ),
      child: Padding(
        padding: const EdgeInsets.all(AppSpacing.small),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Padding(
              padding: const EdgeInsets.all(AppSpacing.small),
              child: Text(
                'Dispositivos disponíveis',
                style: AppTypography.textTheme.titleMedium?.copyWith(
                  color: titleColor,
                  fontWeight: FontWeight.w500,
                ),
              ),
            ),
            const Divider(height: 1, color: AppColors.neutralLight),
            
            // Lista de câmeras
            if (widget.cameras.isEmpty)
              _buildEmptyState()
            else
              _buildCameraList(),
              
            // Botão para atualizar lista
            const SizedBox(height: AppSpacing.small),
            AppButton(
              label: 'Atualizar dispositivos',
              onPressed: widget.onRefreshCameras,
              type: AppButtonType.secondary,
              size: AppButtonSize.small,
              isFullWidth: true,
              prefixIcon: Icons.refresh,
            ),
          ],
        ),
      ),
    );
  }
  
  Widget _buildEmptyState() {
    return Container(
      padding: const EdgeInsets.all(AppSpacing.medium),
      alignment: Alignment.center,
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          const Icon(Icons.videocam_off,
            size: 48, 
            color: AppColors.neutralLight
          ),
          const SizedBox(height: AppSpacing.small),
          Text(
            'Nenhuma câmera encontrada',
            style: AppTypography.textTheme.bodyMedium?.copyWith(
              color: AppColors.neutralDark,
            ),
            textAlign: TextAlign.center,
          ),
        ],
      ),
    );
  }
  
  Widget _buildCameraList() {
    return ListView.separated(
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      itemCount: widget.cameras.length,
      separatorBuilder: (context, index) => 
          const Divider(height: 1, color: AppColors.neutralLight),
      itemBuilder: (context, index) {
        final camera = widget.cameras[index];
        final isSelected = camera.id == widget.selectedCameraId;
        
        return _buildCameraListItem(
          camera: camera,
          isSelected: isSelected,
          onTap: () => widget.onCameraSelected(camera.id),
        );
      },
    );
  }
  
  Widget _buildCameraListItem({
    required CameraDevice camera,
    required bool isSelected,
    required VoidCallback onTap,
  }) {
    // Determinar o ícone com base na posição da câmera
    IconData cameraIcon;
    switch (camera.position) {
      case CameraPosition.front:
        cameraIcon = Icons.camera_front;
        break;
      case CameraPosition.back:
        cameraIcon = Icons.camera_rear;
        break;
      case CameraPosition.external:
        cameraIcon = Icons.usb;
        break;
      default:
        cameraIcon = Icons.camera_alt;
    }

    final titleColor = widget.isDarkMode ? AppColors.neutralLightest : AppColors.neutralDarkest;
    final subtitleColor = widget.isDarkMode ? AppColors.neutralLight : AppColors.neutralDark;

    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(AppBorders.radiusSmall),
      child: Container(
        padding: const EdgeInsets.all(AppSpacing.medium),
        decoration: BoxDecoration(
          color: isSelected ? AppColors.primaryDark.withValues(alpha: 0.4) : Colors.transparent,
          borderRadius: BorderRadius.circular(AppBorders.radiusSmall),
        ),
        child: Row(
          children: [
            Container(
              width: 40,
              height: 40,
              decoration: BoxDecoration(
                color: isSelected ? AppColors.primary : AppColors.neutralLight,
                shape: BoxShape.circle,
              ),
              child: Icon(
                cameraIcon,
                color: isSelected ? AppColors.white : AppColors.neutralDarkest,
                size: 20,
              ),
            ),
            const SizedBox(width: AppSpacing.medium),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    camera.name,
                    style: AppTypography.textTheme.bodyMedium?.copyWith(
                      fontWeight: FontWeight.w500,
                      color: titleColor,
                    ),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                  Text(
                    _getCameraPositionText(camera.position),
                    style: AppTypography.textTheme.bodySmall?.copyWith(
                      color: subtitleColor,
                    ),
                  ),
                ],
              ),
            ),
            if (isSelected)
              const Icon(
                Icons.check_circle,
                color: AppColors.primary,
                size: 20,
              ),
          ],
        ),
      ),
    );
  }
  
  String _getCameraPositionText(CameraPosition position) {
    switch (position) {
      case CameraPosition.front:
        return 'Câmera Frontal';
      case CameraPosition.back:
        return 'Câmera Traseira';
      case CameraPosition.external:
        return 'Câmera Externa';
      default:
        return 'Posição Desconhecida';
    }
  }
} 