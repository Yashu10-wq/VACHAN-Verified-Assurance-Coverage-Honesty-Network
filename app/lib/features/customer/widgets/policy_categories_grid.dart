import 'package:flutter/material.dart';
import '../../../core/theme/app_theme.dart';
import '../../../shared/widgets/glass_card.dart';
import '../models/customer_policy_model.dart';

class PolicyCategoriesGrid extends StatelessWidget {
  final List<DetailedPolicyModel> policies;
  final ValueChanged<String>? onCategorySelected;
  final VoidCallback? onViewAll;

  const PolicyCategoriesGrid({
    super.key,
    required this.policies,
    this.onCategorySelected,
    this.onViewAll,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // Section Header
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            const Text(
              'Explore Coverage',
              style: TextStyle(
                fontSize: 18,
                fontWeight: FontWeight.w800,
                color: AppTheme.textPrimary,
                letterSpacing: -0.3,
              ),
            ),
            GestureDetector(
              onTap: onViewAll,
              child: const Row(
                children: [
                  Text(
                    'View All',
                    style: TextStyle(
                      fontSize: 13,
                      fontWeight: FontWeight.w600,
                      color: AppTheme.gradientSkyBlue,
                    ),
                  ),
                  SizedBox(width: 2),
                  Icon(
                    Icons.chevron_right_rounded,
                    size: 18,
                    color: AppTheme.gradientSkyBlue,
                  ),
                ],
              ),
            ),
          ],
        ),

        const SizedBox(height: 14),

        // Grid of 4 Policy Categories
        Row(
          children: [
            Expanded(
              child: _buildCategoryCard(
                categoryKey: 'MOTOR',
                title: 'Motor Insurance',
                subtitle: 'for Individuals',
                icon: Icons.directions_car_rounded,
                iconColor: const Color(0xFF8B5CF6),
                bgColor: const Color(0xFFF3E8FF),
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: _buildCategoryCard(
                categoryKey: 'HEALTH',
                title: 'Health Insurance',
                subtitle: 'for Families & SMEs',
                icon: Icons.health_and_safety_rounded,
                iconColor: const Color(0xFF0284C7),
                bgColor: const Color(0xFFE0F2FE),
              ),
            ),
          ],
        ),
        const SizedBox(height: 12),
        Row(
          children: [
            Expanded(
              child: _buildCategoryCard(
                categoryKey: 'TRAVEL',
                title: 'Travel Insurance',
                subtitle: 'Worldwide trips',
                icon: Icons.flight_takeoff_rounded,
                iconColor: const Color(0xFF0D9488),
                bgColor: const Color(0xFFCCFBF1),
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: _buildCategoryCard(
                categoryKey: 'LIFE',
                title: 'Medical & Life',
                subtitle: 'Critical coverage',
                icon: Icons.medical_services_rounded,
                iconColor: const Color(0xFFEA580C),
                bgColor: const Color(0xFFFFEDD5),
              ),
            ),
          ],
        ),
      ],
    );
  }

  Widget _buildCategoryCard({
    required String categoryKey,
    required String title,
    required String subtitle,
    required IconData icon,
    required Color iconColor,
    required Color bgColor,
  }) {
    // Count real matching policies from backend if any
    final count = policies.where((p) => p.category.toUpperCase().contains(categoryKey)).length;

    return GlassCard(
      padding: const EdgeInsets.all(14),
      borderRadius: 20,
      onTap: () => onCategorySelected?.call(categoryKey),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            width: 38,
            height: 38,
            decoration: BoxDecoration(
              color: bgColor,
              borderRadius: BorderRadius.circular(12),
            ),
            child: Icon(icon, color: iconColor, size: 20),
          ),
          const SizedBox(width: 10),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  title,
                  style: const TextStyle(
                    fontSize: 13,
                    fontWeight: FontWeight.w700,
                    color: AppTheme.textPrimary,
                    letterSpacing: -0.2,
                  ),
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
                const SizedBox(height: 2),
                Text(
                  subtitle,
                  style: const TextStyle(
                    fontSize: 11,
                    color: AppTheme.textSecondary,
                  ),
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
                if (count > 0) ...[
                  const SizedBox(height: 4),
                  Text(
                    '$count available',
                    style: const TextStyle(
                      fontSize: 10,
                      fontWeight: FontWeight.w600,
                      color: AppTheme.gradientSkyBlue,
                    ),
                  ),
                ],
              ],
            ),
          ),
        ],
      ),
    );
  }
}
