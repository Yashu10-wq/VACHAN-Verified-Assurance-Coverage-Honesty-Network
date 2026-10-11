import 'package:flutter/material.dart';
import '../../../core/theme/app_theme.dart';
import '../../../shared/widgets/glass_card.dart';

class QuickActionsGrid extends StatelessWidget {
  final VoidCallback? onHealthTap;
  final VoidCallback? onMyPolicyTap;
  final VoidCallback? onPolicyInfoTap;

  const QuickActionsGrid({
    super.key,
    this.onHealthTap,
    this.onMyPolicyTap,
    this.onPolicyInfoTap,
  });

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        // Card 1: Health OK
        Expanded(
          child: _buildActionCard(
            title: 'Health OK',
            icon: Icons.favorite_rounded,
            gradient: AppTheme.purpleGradient,
            onTap: onHealthTap,
          ),
        ),
        const SizedBox(width: 14),

        // Card 2: My Policy
        Expanded(
          child: _buildActionCard(
            title: 'My Policy',
            icon: Icons.description_rounded,
            gradient: AppTheme.coralGradient,
            onTap: onMyPolicyTap,
          ),
        ),
        const SizedBox(width: 14),

        // Card 3: Policy Info
        Expanded(
          child: _buildActionCard(
            title: 'Policy Info',
            icon: Icons.shield_rounded,
            gradient: AppTheme.magentaGradient,
            onTap: onPolicyInfoTap,
          ),
        ),
      ],
    );
  }

  Widget _buildActionCard({
    required String title,
    required IconData icon,
    required LinearGradient gradient,
    VoidCallback? onTap,
  }) {
    return GlassCard(
      padding: const EdgeInsets.symmetric(vertical: 18, horizontal: 8),
      borderRadius: 22,
      onTap: onTap,
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Container(
            width: 48,
            height: 48,
            decoration: BoxDecoration(
              gradient: gradient,
              borderRadius: BorderRadius.circular(16),
              boxShadow: [
                BoxShadow(
                  color: gradient.colors.first.withValues(alpha: 0.35),
                  blurRadius: 12,
                  offset: const Offset(0, 5),
                ),
              ],
            ),
            child: Center(
              child: Icon(
                icon,
                color: Colors.white,
                size: 24,
              ),
            ),
          ),
          const SizedBox(height: 12),
          Text(
            title,
            textAlign: TextAlign.center,
            style: const TextStyle(
              fontSize: 13,
              fontWeight: FontWeight.w700,
              color: AppTheme.textPrimary,
              letterSpacing: -0.2,
            ),
          ),
        ],
      ),
    );
  }
}
