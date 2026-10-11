import 'package:flutter/material.dart';
import '../../core/theme/app_theme.dart';

enum AppButtonVariant { primaryGradient, darkTeal, outlined, text }

class AppButton extends StatelessWidget {
  final String label;
  final VoidCallback? onPressed;
  final bool isLoading;
  final Widget? icon;
  final AppButtonVariant variant;
  final double? width;
  final double height;
  final double borderRadius;

  const AppButton({
    super.key,
    required this.label,
    required this.onPressed,
    this.isLoading = false,
    this.icon,
    this.variant = AppButtonVariant.primaryGradient,
    this.width,
    this.height = 54,
    this.borderRadius = 22,
  });

  @override
  Widget build(BuildContext context) {
    if (variant == AppButtonVariant.primaryGradient) {
      return Container(
        width: width ?? double.infinity,
        height: height,
        decoration: BoxDecoration(
          gradient: onPressed == null || isLoading ? null : AppTheme.primaryGradient,
          color: onPressed == null || isLoading ? Colors.grey.shade300 : null,
          borderRadius: BorderRadius.circular(borderRadius),
          boxShadow: onPressed == null || isLoading ? null : AppTheme.glowShadow,
        ),
        child: Material(
          color: Colors.transparent,
          child: InkWell(
            borderRadius: BorderRadius.circular(borderRadius),
            onTap: isLoading ? null : onPressed,
            child: Center(child: _buildContent(Colors.white)),
          ),
        ),
      );
    }

    if (variant == AppButtonVariant.darkTeal) {
      return Container(
        width: width ?? double.infinity,
        height: height,
        decoration: BoxDecoration(
          color: onPressed == null || isLoading ? Colors.grey.shade400 : AppTheme.darkTeal,
          borderRadius: BorderRadius.circular(borderRadius),
          boxShadow: onPressed == null || isLoading ? null : AppTheme.softCardShadow,
        ),
        child: Material(
          color: Colors.transparent,
          child: InkWell(
            borderRadius: BorderRadius.circular(borderRadius),
            onTap: isLoading ? null : onPressed,
            child: Center(child: _buildContent(Colors.white)),
          ),
        ),
      );
    }

    if (variant == AppButtonVariant.outlined) {
      return SizedBox(
        width: width ?? double.infinity,
        height: height,
        child: OutlinedButton(
          onPressed: isLoading ? null : onPressed,
          style: OutlinedButton.styleFrom(
            side: const BorderSide(color: AppTheme.borderLight, width: 1.5),
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(borderRadius),
            ),
            backgroundColor: Colors.white,
          ),
          child: _buildContent(AppTheme.textPrimary),
        ),
      );
    }

    // Text button
    return TextButton(
      onPressed: isLoading ? null : onPressed,
      child: _buildContent(AppTheme.gradientSkyBlue),
    );
  }

  Widget _buildContent(Color textColor) {
    if (isLoading) {
      return SizedBox(
        width: 22,
        height: 22,
        child: CircularProgressIndicator(
          strokeWidth: 2.5,
          valueColor: AlwaysStoppedAnimation<Color>(textColor),
        ),
      );
    }

    if (icon != null) {
      return Row(
        mainAxisSize: MainAxisSize.min,
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          icon!,
          const SizedBox(width: 10),
          Text(
            label,
            style: TextStyle(
              color: textColor,
              fontSize: 16,
              fontWeight: FontWeight.w600,
              letterSpacing: 0.1,
            ),
          ),
        ],
      );
    }

    return Text(
      label,
      style: TextStyle(
        color: textColor,
        fontSize: 16,
        fontWeight: FontWeight.w600,
        letterSpacing: 0.1,
      ),
    );
  }
}
