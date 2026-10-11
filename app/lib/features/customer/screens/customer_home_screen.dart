import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../core/theme/app_theme.dart';
import '../../../shared/widgets/glass_card.dart';
import '../../../shared/widgets/status_badge.dart';
import '../models/customer_policy_model.dart';
import '../providers/customer_provider.dart';
import '../widgets/claims_center_banner.dart';
import '../widgets/customer_bottom_nav.dart';
import '../widgets/home_header.dart';
import '../widgets/policy_categories_grid.dart';
import '../widgets/quick_actions_grid.dart';
import '../widgets/renew_plan_card.dart';

class CustomerHomeScreen extends ConsumerStatefulWidget {
  const CustomerHomeScreen({super.key});

  @override
  ConsumerState<CustomerHomeScreen> createState() => _CustomerHomeScreenState();
}

class _CustomerHomeScreenState extends ConsumerState<CustomerHomeScreen> {
  final _searchController = TextEditingController();

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final dashboardState = ref.watch(customerDashboardProvider);

    return Scaffold(
      backgroundColor: AppTheme.background,
      body: SafeArea(
        child: RefreshIndicator(
          color: AppTheme.gradientSkyBlue,
          onRefresh: () async {
            await ref.read(customerDashboardProvider.notifier).fetchDashboardData();
          },
          child: SingleChildScrollView(
            physics: const AlwaysScrollableScrollPhysics(),
            padding: const EdgeInsets.symmetric(horizontal: 20.0, vertical: 12.0),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // Top Header with brand, avatar, search, greeting
                HomeHeader(
                  searchController: _searchController,
                  onSearchChanged: (val) {
                    // Quick search
                  },
                  onFilterTap: () {
                    context.go('/policies');
                  },
                ),

                const SizedBox(height: 20),

                // Offline or Error Notice if applicable
                if (dashboardState.isOffline) ...[
                  Container(
                    margin: const EdgeInsets.only(bottom: 16),
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: AppTheme.warning.withValues(alpha: 0.12),
                      borderRadius: BorderRadius.circular(16),
                      border: Border.all(color: AppTheme.warning.withValues(alpha: 0.3)),
                    ),
                    child: const Row(
                      children: [
                        Icon(Icons.wifi_off_rounded, color: AppTheme.warning, size: 20),
                        SizedBox(width: 10),
                        Expanded(
                          child: Text(
                            'Offline mode: Connecting to local cache. Pull to retry.',
                            style: TextStyle(
                              color: Color(0xFF92400E),
                              fontSize: 12,
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                ],

                // 3 Quick Action Cards: Health OK, My Policy, Policy Info
                QuickActionsGrid(
                  onHealthTap: () => _showQuickActionDetail(
                    context,
                    title: 'Health OK Coverage',
                    description: 'Your health and medical parameters are active with zero pending compliance notices.',
                  ),
                  onMyPolicyTap: () => context.go('/policies'),
                  onPolicyInfoTap: () => _showPolicyInfoModal(context, dashboardState),
                ),

                const SizedBox(height: 18),

                // Dark Teal "Renew Your Plan" Pill Card
                RenewPlanCard(
                  onRenewTap: () {
                    ScaffoldMessenger.of(context).showSnackBar(
                      const SnackBar(
                        content: Text('All policies are currently in good standing. No renewals required immediately.'),
                        backgroundColor: AppTheme.darkTeal,
                      ),
                    );
                  },
                ),

                const SizedBox(height: 20),

                // Real Confirmed/Pending Policy Registrations from Backend
                if (dashboardState.registrations.isNotEmpty) ...[
                  _buildActiveRegistrationsSection(dashboardState.registrations),
                  const SizedBox(height: 20),
                ],

                // Real Recent Claims Summary if any
                if (dashboardState.recentClaims.isNotEmpty) ...[
                  _buildRecentClaimsSection(dashboardState),
                  const SizedBox(height: 20),
                ],

                // Explore Coverage / Policy Categories
                PolicyCategoriesGrid(
                  policies: dashboardState.policies,
                  onCategorySelected: (cat) {
                    context.go('/policies');
                  },
                  onViewAll: () {
                    context.go('/policies');
                  },
                ),

                const SizedBox(height: 20),

                // Claims Center Cyan Gradient Banner
                ClaimsCenterBanner(
                  onClaimsTap: () {
                    context.go('/claims');
                  },
                ),

                const SizedBox(height: 24),
              ],
            ),
          ),
        ),
      ),
      bottomNavigationBar: const CustomerBottomNav(currentIndex: 0),
    );
  }

  Widget _buildActiveRegistrationsSection(List<CustomerRegistrationModel> regs) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            const Text(
              'Your Enrolled Policies',
              style: TextStyle(
                fontSize: 18,
                fontWeight: FontWeight.w800,
                color: AppTheme.textPrimary,
                letterSpacing: -0.3,
              ),
            ),
            GestureDetector(
              onTap: () => context.go('/policies'),
              child: const Text(
                'See All',
                style: TextStyle(
                  fontSize: 13,
                  fontWeight: FontWeight.w700,
                  color: AppTheme.gradientSkyBlue,
                ),
              ),
            ),
          ],
        ),
        const SizedBox(height: 12),
        ListView.separated(
          shrinkWrap: true,
          physics: const NeverScrollableScrollPhysics(),
          itemCount: regs.length > 3 ? 3 : regs.length,
          separatorBuilder: (_, __) => const SizedBox(height: 10),
          itemBuilder: (context, index) {
            final reg = regs[index];
            final shortPolicyId = reg.policyId.length > 8 ? reg.policyId.substring(0, 8) : reg.policyId;

            return GlassCard(
              padding: const EdgeInsets.all(16),
              onTap: () => context.push('/policy-detail/${reg.policyId}'),
              child: Row(
                children: [
                  Container(
                    width: 42,
                    height: 42,
                    decoration: BoxDecoration(
                      color: AppTheme.gradientSkyBlue.withValues(alpha: 0.15),
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: const Icon(
                      Icons.shield_outlined,
                      color: AppTheme.gradientSkyBlue,
                      size: 22,
                    ),
                  ),
                  const SizedBox(width: 14),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          'Policy #$shortPolicyId',
                          style: const TextStyle(
                            fontSize: 14,
                            fontWeight: FontWeight.w700,
                            color: AppTheme.textPrimary,
                          ),
                        ),
                        const SizedBox(height: 2),
                        Text(
                          reg.isConfirmed ? 'Active Verifiable Contract' : 'Awaiting Consent Confirmation',
                          style: const TextStyle(
                            fontSize: 12,
                            color: AppTheme.textSecondary,
                          ),
                        ),
                      ],
                    ),
                  ),
                  StatusBadge.fromStatus(reg.status),
                ],
              ),
            );
          },
        ),
      ],
    );
  }

  Widget _buildRecentClaimsSection(CustomerDashboardState state) {
    final claims = state.recentClaims;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            const Text(
              'Recent Claims',
              style: TextStyle(
                fontSize: 18,
                fontWeight: FontWeight.w800,
                color: AppTheme.textPrimary,
                letterSpacing: -0.3,
              ),
            ),
            GestureDetector(
              onTap: () => context.go('/claims'),
              child: const Text(
                'View All',
                style: TextStyle(
                  fontSize: 13,
                  fontWeight: FontWeight.w700,
                  color: AppTheme.gradientSkyBlue,
                ),
              ),
            ),
          ],
        ),
        const SizedBox(height: 12),
        ListView.separated(
          shrinkWrap: true,
          physics: const NeverScrollableScrollPhysics(),
          itemCount: claims.length > 2 ? 2 : claims.length,
          separatorBuilder: (_, __) => const SizedBox(height: 10),
          itemBuilder: (context, index) {
            final claim = claims[index];
            return GlassCard(
              padding: const EdgeInsets.all(14),
              onTap: () => context.push('/claim-detail/${claim.id}'),
              child: Row(
                children: [
                  Container(
                    width: 38,
                    height: 38,
                    decoration: BoxDecoration(
                      color: AppTheme.darkTeal.withValues(alpha: 0.1),
                      borderRadius: BorderRadius.circular(10),
                    ),
                    child: const Icon(Icons.receipt_long_rounded, color: AppTheme.darkTeal, size: 20),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          'Claim ${claim.claimNumber}',
                          style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w700, color: AppTheme.textPrimary),
                        ),
                        const SizedBox(height: 2),
                        Text(
                          '${claim.claimCategory} • \$${claim.requestedAmount}',
                          style: const TextStyle(fontSize: 11, color: AppTheme.textSecondary),
                        ),
                      ],
                    ),
                  ),
                  StatusBadge.fromStatus(claim.status),
                ],
              ),
            );
          },
        ),
      ],
    );
  }

  void _showQuickActionDetail(
    BuildContext context, {
    required String title,
    required String description,
  }) {
    showModalBottomSheet(
      context: context,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(28)),
      ),
      backgroundColor: Colors.white,
      builder: (context) {
        return Padding(
          padding: const EdgeInsets.all(24.0),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Center(
                child: Container(
                  width: 40,
                  height: 4,
                  decoration: BoxDecoration(
                    color: Colors.grey.shade300,
                    borderRadius: BorderRadius.circular(2),
                  ),
                ),
              ),
              const SizedBox(height: 20),
              Text(
                title,
                style: const TextStyle(
                  fontSize: 20,
                  fontWeight: FontWeight.w800,
                  color: AppTheme.textPrimary,
                ),
              ),
              const SizedBox(height: 10),
              Text(
                description,
                style: const TextStyle(
                  fontSize: 14,
                  color: AppTheme.textSecondary,
                  height: 1.4,
                ),
              ),
              const SizedBox(height: 24),
              ElevatedButton(
                onPressed: () => Navigator.pop(context),
                style: ElevatedButton.styleFrom(
                  minimumSize: const Size(double.infinity, 50),
                  backgroundColor: AppTheme.darkTeal,
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(18)),
                ),
                child: const Text('Close'),
              ),
            ],
          ),
        );
      },
    );
  }

  void _showPolicyInfoModal(BuildContext context, CustomerDashboardState state) {
    _showQuickActionDetail(
      context,
      title: 'Policy Transparency & Audit Guarantee',
      description:
          'InsureChain VoiceGuard guarantees that all policy statements made during sales calls match published underwriting terms. SHA-256 state roots are periodically anchored to the Ethereum Sepolia blockchain.',
    );
  }
}
