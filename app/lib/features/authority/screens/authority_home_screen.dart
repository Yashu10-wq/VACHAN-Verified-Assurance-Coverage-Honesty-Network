import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../core/theme/app_theme.dart';
import '../../../shared/widgets/glass_card.dart';
import '../../../shared/widgets/status_badge.dart';
import '../../auth/providers/auth_provider.dart';
import '../../customer/models/claim_model.dart';
import '../providers/authority_provider.dart';

class AuthorityHomeScreen extends ConsumerStatefulWidget {
  const AuthorityHomeScreen({super.key});

  @override
  ConsumerState<AuthorityHomeScreen> createState() => _AuthorityHomeScreenState();
}

class _AuthorityHomeScreenState extends ConsumerState<AuthorityHomeScreen> {
  final _searchController = TextEditingController();
  String _selectedFilter = 'ALL';

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final authState = ref.watch(authProvider);
    final user = authState.user;
    final claimsState = ref.watch(authorityClaimsProvider);

    return Scaffold(
      backgroundColor: AppTheme.background,
      appBar: AppBar(
        title: const Text('Authority Claims Queue'),
        automaticallyImplyLeading: false,
        actions: [
          IconButton(
            icon: const Icon(Icons.hub_rounded, color: AppTheme.gradientSkyBlue),
            tooltip: 'Blockchain Integrity',
            onPressed: () => context.push('/integrity'),
          ),
          IconButton(
            icon: const Icon(Icons.refresh_rounded),
            onPressed: () {
              ref.read(authorityClaimsProvider.notifier).fetchClaims(status: _selectedFilter);
            },
          ),
          IconButton(
            icon: const Icon(Icons.logout_rounded, color: AppTheme.error),
            onPressed: () async {
              final confirm = await showDialog<bool>(
                context: context,
                builder: (ctx) => AlertDialog(
                  title: const Text('Sign Out'),
                  content: const Text('Sign out from Approval Authority session?'),
                  actions: [
                    TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text('Cancel')),
                    ElevatedButton(
                      onPressed: () => Navigator.pop(ctx, true),
                      style: ElevatedButton.styleFrom(backgroundColor: AppTheme.error),
                      child: const Text('Sign Out'),
                    ),
                  ],
                ),
              );
              if (confirm == true) {
                await ref.read(authProvider.notifier).logout();
                if (context.mounted) context.go('/login');
              }
            },
          ),
        ],
      ),
      body: SafeArea(
        child: RefreshIndicator(
          color: AppTheme.gradientSkyBlue,
          onRefresh: () async {
            await ref.read(authorityClaimsProvider.notifier).fetchClaims(status: _selectedFilter);
          },
          child: SingleChildScrollView(
            physics: const AlwaysScrollableScrollPhysics(),
            padding: const EdgeInsets.symmetric(horizontal: 20.0, vertical: 12.0),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // Authority Profile Header
                GlassCard(
                  padding: const EdgeInsets.all(20),
                  child: Row(
                    children: [
                      Container(
                        width: 52,
                        height: 52,
                        decoration: BoxDecoration(
                          color: AppTheme.darkTeal,
                          borderRadius: BorderRadius.circular(16),
                        ),
                        child: const Center(
                          child: Icon(Icons.gavel_rounded, color: Colors.white, size: 28),
                        ),
                      ),
                      const SizedBox(width: 16),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              user?.fullName.isNotEmpty == true ? user!.fullName : 'Approval Authority',
                              style: const TextStyle(
                                fontSize: 17,
                                fontWeight: FontWeight.w800,
                                color: AppTheme.textPrimary,
                              ),
                            ),
                            const SizedBox(height: 2),
                            Text(
                              user?.email ?? '',
                              style: const TextStyle(fontSize: 12, color: AppTheme.textSecondary),
                            ),
                            const SizedBox(height: 6),
                            Container(
                              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                              decoration: BoxDecoration(
                                color: AppTheme.darkTeal.withValues(alpha: 0.1),
                                borderRadius: BorderRadius.circular(8),
                              ),
                              child: const Text(
                                'STATUTORY CLAIMS ADJUDICATOR',
                                style: TextStyle(
                                  fontSize: 10,
                                  fontWeight: FontWeight.w800,
                                  color: AppTheme.darkTeal,
                                ),
                              ),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                ),

                const SizedBox(height: 20),

                // Real Metrics Grid
                Row(
                  children: [
                    Expanded(
                      child: _buildMetricTile(
                        label: 'New Queue',
                        value: '${claimsState.submittedCount}',
                        color: AppTheme.gradientSkyBlue,
                        icon: Icons.inbox_rounded,
                      ),
                    ),
                    const SizedBox(width: 10),
                    Expanded(
                      child: _buildMetricTile(
                        label: 'In Review',
                        value: '${claimsState.inReviewCount}',
                        color: AppTheme.warning,
                        icon: Icons.pending_actions_rounded,
                      ),
                    ),
                    const SizedBox(width: 10),
                    Expanded(
                      child: _buildMetricTile(
                        label: 'Evidence Req',
                        value: '${claimsState.evidenceRequestedCount}',
                        color: const Color(0xFFD97706),
                        icon: Icons.rule_folder_rounded,
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 10),
                Row(
                  children: [
                    Expanded(
                      child: _buildMetricTile(
                        label: 'Approved',
                        value: '${claimsState.approvedCount}',
                        color: AppTheme.success,
                        icon: Icons.check_circle_outline_rounded,
                      ),
                    ),
                    const SizedBox(width: 10),
                    Expanded(
                      child: _buildMetricTile(
                        label: 'Paid (Settled)',
                        value: '${claimsState.paidCount}',
                        color: const Color(0xFF0D9488),
                        icon: Icons.payments_outlined,
                      ),
                    ),
                    const SizedBox(width: 10),
                    Expanded(
                      child: _buildMetricTile(
                        label: 'Rejected',
                        value: '${claimsState.rejectedCount}',
                        color: AppTheme.error,
                        icon: Icons.highlight_off_rounded,
                      ),
                    ),
                  ],
                ),

                const SizedBox(height: 24),

                // Search Bar
                Container(
                  height: 48,
                  decoration: BoxDecoration(
                    color: Colors.white,
                    borderRadius: BorderRadius.circular(24),
                    border: Border.all(color: AppTheme.borderLight),
                  ),
                  child: Row(
                    children: [
                      const SizedBox(width: 14),
                      const Icon(Icons.search_rounded, color: AppTheme.textMuted, size: 20),
                      const SizedBox(width: 10),
                      Expanded(
                        child: TextField(
                          controller: _searchController,
                          onChanged: (val) {
                            ref.read(authorityClaimsProvider.notifier).setSearchQuery(val.trim());
                          },
                          decoration: const InputDecoration(
                            hintText: 'Search claim ID, customer, or category...',
                            border: InputBorder.none,
                            enabledBorder: InputBorder.none,
                            focusedBorder: InputBorder.none,
                            contentPadding: EdgeInsets.zero,
                          ),
                        ),
                      ),
                      if (_searchController.text.isNotEmpty) ...[
                        IconButton(
                          icon: const Icon(Icons.clear_rounded, size: 18),
                          onPressed: () {
                            _searchController.clear();
                            ref.read(authorityClaimsProvider.notifier).setSearchQuery('');
                          },
                        ),
                      ],
                    ],
                  ),
                ),

                const SizedBox(height: 12),

                // Status Filter Chips
                SingleChildScrollView(
                  scrollDirection: Axis.horizontal,
                  child: Row(
                    children: [
                      _buildFilterChip('ALL', 'All Claims (${claimsState.claims.length})'),
                      const SizedBox(width: 8),
                      _buildFilterChip('SUBMITTED', 'Submitted (${claimsState.submittedCount})'),
                      const SizedBox(width: 8),
                      _buildFilterChip('IN_REVIEW', 'In Review (${claimsState.inReviewCount})'),
                      const SizedBox(width: 8),
                      _buildFilterChip('EVIDENCE_REQUESTED', 'Evidence Req (${claimsState.evidenceRequestedCount})'),
                      const SizedBox(width: 8),
                      _buildFilterChip('APPROVED', 'Approved (${claimsState.approvedCount})'),
                      const SizedBox(width: 8),
                      _buildFilterChip('PAID', 'Paid (${claimsState.paidCount})'),
                      const SizedBox(width: 8),
                      _buildFilterChip('REJECTED', 'Rejected (${claimsState.rejectedCount})'),
                    ],
                  ),
                ),

                const SizedBox(height: 16),

                // Claims List
                if (claimsState.isLoading) ...[
                  const Center(
                    child: Padding(
                      padding: EdgeInsets.all(32.0),
                      child: CircularProgressIndicator(
                        valueColor: AlwaysStoppedAnimation<Color>(AppTheme.gradientSkyBlue),
                      ),
                    ),
                  ),
                ] else if (claimsState.errorMessage != null) ...[
                  Center(
                    child: Padding(
                      padding: const EdgeInsets.all(24.0),
                      child: Column(
                        children: [
                          const Icon(Icons.error_outline_rounded, color: AppTheme.error, size: 36),
                          const SizedBox(height: 10),
                          Text(claimsState.errorMessage!, textAlign: TextAlign.center),
                          const SizedBox(height: 12),
                          ElevatedButton(
                            onPressed: () {
                              ref.read(authorityClaimsProvider.notifier).fetchClaims(status: _selectedFilter);
                            },
                            child: const Text('Retry'),
                          ),
                        ],
                      ),
                    ),
                  ),
                ] else if (claimsState.filteredClaims.isEmpty) ...[
                  GlassCard(
                    padding: const EdgeInsets.all(28),
                    child: Center(
                      child: Column(
                        children: [
                          const Icon(Icons.fact_check_outlined, size: 40, color: AppTheme.textMuted),
                          const SizedBox(height: 12),
                          const Text(
                            'No Claims Found',
                            style: TextStyle(fontSize: 16, fontWeight: FontWeight.w700, color: AppTheme.textPrimary),
                          ),
                          const SizedBox(height: 4),
                          Text(
                            _selectedFilter == 'ALL'
                                ? 'No claims are currently filed in the system.'
                                : 'No claims currently in "$_selectedFilter" status.',
                            style: const TextStyle(fontSize: 12, color: AppTheme.textSecondary),
                          ),
                        ],
                      ),
                    ),
                  ),
                ] else ...[
                  ...claimsState.filteredClaims.map((claim) => _buildClaimCard(claim)),
                ],

                const SizedBox(height: 36),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildMetricTile({
    required String label,
    required String value,
    required Color color,
    required IconData icon,
  }) {
    return GlassCard(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 12),
      borderRadius: 16,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                value,
                style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w800, color: AppTheme.textPrimary),
              ),
              Icon(icon, size: 16, color: color),
            ],
          ),
          const SizedBox(height: 4),
          Text(
            label,
            style: const TextStyle(fontSize: 10, fontWeight: FontWeight.w600, color: AppTheme.textSecondary),
          ),
        ],
      ),
    );
  }

  Widget _buildFilterChip(String key, String label) {
    final isSelected = _selectedFilter == key;
    return GestureDetector(
      onTap: () {
        setState(() => _selectedFilter = key);
        ref.read(authorityClaimsProvider.notifier).setStatusFilter(key);
      },
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
        decoration: BoxDecoration(
          color: isSelected ? AppTheme.darkTeal : Colors.white,
          borderRadius: BorderRadius.circular(16),
          border: Border.all(
            color: isSelected ? AppTheme.darkTeal : AppTheme.borderLight,
          ),
        ),
        child: Text(
          label,
          style: TextStyle(
            fontSize: 12,
            fontWeight: FontWeight.w700,
            color: isSelected ? Colors.white : AppTheme.textSecondary,
          ),
        ),
      ),
    );
  }

  Widget _buildClaimCard(ClaimModel claim) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12.0),
      child: GlassCard(
        padding: const EdgeInsets.all(18),
        onTap: () => context.push('/authority/claim/${claim.id}'),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Claim ${claim.claimNumber}',
                      style: const TextStyle(fontSize: 15, fontWeight: FontWeight.w800, color: AppTheme.textPrimary),
                    ),
                    const SizedBox(height: 2),
                    Text(
                      'Cust #${claim.customerId.substring(0, claim.customerId.length > 8 ? 8 : claim.customerId.length)} • Incident: ${claim.incidentDate}',
                      style: const TextStyle(fontSize: 11, color: AppTheme.textSecondary),
                    ),
                  ],
                ),
                StatusBadge.fromStatus(claim.status),
              ],
            ),
            const Divider(color: AppTheme.borderLight, height: 22),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Row(
                  children: [
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                      decoration: BoxDecoration(
                        color: AppTheme.gradientSkyBlue.withValues(alpha: 0.12),
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: Text(
                        claim.claimCategory,
                        style: const TextStyle(fontSize: 11, fontWeight: FontWeight.w700, color: AppTheme.gradientSkyBlue),
                      ),
                    ),
                    const SizedBox(width: 8),
                    Text(
                      'Requested: \$${claim.requestedAmount}',
                      style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w700, color: AppTheme.textPrimary),
                    ),
                  ],
                ),
                const Row(
                  children: [
                    Text('Review Claim', style: TextStyle(fontSize: 12, fontWeight: FontWeight.w700, color: AppTheme.darkTeal)),
                    SizedBox(width: 4),
                    Icon(Icons.arrow_forward_ios_rounded, size: 12, color: AppTheme.darkTeal),
                  ],
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}
