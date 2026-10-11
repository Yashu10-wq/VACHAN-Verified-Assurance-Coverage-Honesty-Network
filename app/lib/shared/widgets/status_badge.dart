import 'package:flutter/material.dart';
import '../../core/theme/app_theme.dart';

class StatusBadge extends StatelessWidget {
  final String label;
  final Color color;
  final Color? backgroundColor;
  final IconData? icon;

  const StatusBadge({
    super.key,
    required this.label,
    required this.color,
    this.backgroundColor,
    this.icon,
  });

  factory StatusBadge.fromStatus(String status) {
    Color badgeColor;
    switch (status.toUpperCase()) {
      case 'ACTIVE':
      case 'CONFIRMED':
        badgeColor = AppTheme.success;
        break;
      case 'PENDING_VERIFICATION':
      case 'PENDING_APPROVAL':
      case 'AWAITING_CUSTOMER_CONFIRMATION':
        badgeColor = AppTheme.warning;
        break;
      case 'SUSPENDED':
      case 'REJECTED':
      case 'DECLINED':
        badgeColor = AppTheme.error;
        break;
      default:
        badgeColor = AppTheme.gradientSkyBlue;
    }

    return StatusBadge(
      label: status.replaceAll('_', ' '),
      color: badgeColor,
    );
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
      decoration: BoxDecoration(
        color: backgroundColor ?? color.withValues(alpha: 0.12),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: color.withValues(alpha: 0.24),
          width: 1,
        ),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          if (icon != null) ...[
            Icon(icon, size: 13, color: color),
            const SizedBox(width: 4),
          ] else ...[
            Container(
              width: 6,
              height: 6,
              decoration: BoxDecoration(
                color: color,
                shape: BoxShape.circle,
              ),
            ),
            const SizedBox(width: 6),
          ],
          Text(
            label,
            style: TextStyle(
              fontSize: 12,
              fontWeight: FontWeight.w600,
              color: color,
            ),
          ),
        ],
      ),
    );
  }
}
