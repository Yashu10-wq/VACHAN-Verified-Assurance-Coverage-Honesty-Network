import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../core/theme/app_theme.dart';
import '../../../shared/widgets/glass_card.dart';
import '../../../shared/widgets/status_badge.dart';
import '../models/customer_policy_model.dart';
import '../providers/customer_provider.dart';
import '../widgets/customer_bottom_nav.dart';

class CustomerPoliciesScreen extends ConsumerStatefulWidget {
  const CustomerPoliciesScreen({super.key});

  @override
  ConsumerState<CustomerPoliciesScreen> createState() => _CustomerPoliciesScreenState();
}

class _CustomerPoliciesScreenState extends ConsumerState<CustomerPoliciesScreen> {
  String _selectedFilter = 'ALL'; // ALL, ACTIVE, PENDING, CATALOGUE
  final _searchController = TextEditingController();
  String _searchQuery = '';

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final dashboardState = ref.watch(customerDashboardProvider);
    final isLoading = dashboardState.isLoading;

    return Scaffold(
      backgroundColor: AppTheme.background,
      bottomNavigationBar: const CustomerBottomNav(currentIndex: 1),
      appBar: AppBar(
        title: const Text('My Policies & Coverage'),
        automaticallyImplyLeading: false,
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh_rounded),
            onPressed: () {
              ref.read(customerDashboardProvider.notifier).fetchDashboardData();
            },
          ),
        ],
      ),
      body: SafeArea(
        child: RefreshIndicator(
          color: AppTheme.gradientSkyBlue,
          onRefresh: () async {
            await ref.read(customerDashboardProvider.notifier).fetchDashboardData();
          },
          child: Column(
            children: [
              // Search & Filter header
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 20.0, vertical: 8.0),
                child: Column(
                  children: [
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
                              onChanged: (val) => setState(() => _searchQuery = val.trim().toLowerCase()),
                              decoration: const InputDecoration(
                                hintText: 'Search your policies...',
                                border: InputBorder.none,
                                enabledBorder: InputBorder.none,
                                focusedBorder: InputBorder.none,
                                contentPadding: EdgeInsets.zero,
                              ),
                            ),
                          ),
                          if (_searchQuery.isNotEmpty) ...[
                            IconButton(
                              icon: const Icon(Icons.clear_rounded, size: 18),
                              onPressed: () {
                                _searchController.clear();
                                setState(() => _searchQuery = '');
                              },
                            ),
                          ],
                        ],
                      ),
                    ),
                    const SizedBox(height: 12),
                    // Filter Chips
                    SingleChildScrollView(
                      scrollDirection: Axis.horizontal,
                      child: Row(
                        children: [
                          _buildFilterChip('ALL', 'All Policies'),
                          const SizedBox(width: 8),
                          _buildFilterChip('ACTIVE', 'Active Coverage (${dashboardState.activePolicies.length})'),
                          const SizedBox(width: 8),
                          _buildFilterChip('PENDING', 'Awaiting Action (${dashboardState.pendingConfirmationPolicies.length})'),
                          const SizedBox(width: 8),
                          _buildFilterChip('CATALOGUE', 'Catalogue (${dashboardState.cataloguePolicies.length})'),
                        ],
                      ),
                    ),
                  ],
                ),
              ),

              const SizedBox(height: 6),

              // Content List
              Expanded(
                child: isLoading
                    ? const Center(
                        child: CircularProgressIndicator(
                          valueColor: AlwaysStoppedAnimation<Color>(AppTheme.gradientSkyBlue),
                        ),
                      )
                    : _buildContentList(dashboardState),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildFilterChip(String key, String label) {
    final isSelected = _selectedFilter == key;
    return GestureDetector(
      onTap: () => setState(() => _selectedFilter = key),
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 180),
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
        decoration: BoxDecoration(
          color: isSelected ? AppTheme.darkTeal : Colors.white,
          borderRadius: BorderRadius.circular(18),
          border: Border.all(
            color: isSelected ? AppTheme.darkTeal : AppTheme.borderLight,
          ),
        ),
        child: Text(
          label,
          style: TextStyle(
            fontSize: 12,
            fontWeight: FontWeight.w600,
            color: isSelected ? Colors.white : AppTheme.textSecondary,
          ),
        ),
      ),
    );
  }

  Widget _buildContentList(CustomerDashboardState state) {
    if (_selectedFilter == 'CATALOGUE') {
      final catalogue = state.cataloguePolicies.where((p) {
        if (_searchQuery.isEmpty) return true;
        return p.policyName.toLowerCase().contains(_searchQuery) ||
            p.policyCode.toLowerCase().contains(_searchQuery) ||
            p.category.toLowerCase().contains(_searchQuery);
      }).toList();

      if (catalogue.isEmpty) {
        return _buildEmptyState('No policies match your search in the catalogue.');
      }

      return ListView.separated(
        padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 8),
        itemCount: catalogue.length,
        separatorBuilder: (_, __) => const SizedBox(height: 12),
        itemBuilder: (context, index) {
          final p = catalogue[index];
          return _buildCatalogueCard(p);
        },
      );
    }

    // Registrations
    var regs = state.registrations;
    if (_selectedFilter == 'ACTIVE') {
      regs = regs.where((r) => r.isConfirmed).toList();
    } else if (_selectedFilter == 'PENDING') {
      regs = regs.where((r) => r.isAwaitingConfirmation).toList();
    }

    if (_searchQuery.isNotEmpty) {
      regs = regs.where((r) {
        final policy = state.cataloguePolicies.firstWhere(
          (p) => p.id == r.policyId,
          orElse: () => DetailedPolicyModel(
            id: '',
            insurerName: '',
            policyName: 'Policy #${r.policyId.substring(0, 8)}',
            policyCode: '',
            category: '',
            coverageLimit: 0,
            waitingPeriodDays: 0,
            claimFilingWindowDays: 0,
            isActive: true,
          ),
        );
        return policy.policyName.toLowerCase().contains(_searchQuery) ||
            r.id.toLowerCase().contains(_searchQuery);
      }).toList();
    }

    if (regs.isEmpty) {
      return _buildEmptyState(
        _selectedFilter == 'ACTIVE'
            ? 'You do not have any active confirmed policies yet.'
            : _selectedFilter == 'PENDING'
                ? 'No policy registrations currently await your confirmation.'
                : 'No policy registrations found for your account.',
      );
    }

    return ListView.separated(
      padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 8),
      itemCount: regs.length,
      separatorBuilder: (_, __) => const SizedBox(height: 12),
      itemBuilder: (context, index) {
        final reg = regs[index];
        final policy = state.cataloguePolicies.cast<DetailedPolicyModel?>().firstWhere(
              (p) => p?.id == reg.policyId,
              orElse: () => null,
            );
        return _buildRegistrationCard(reg, policy);
      },
    );
  }

  Widget _buildRegistrationCard(CustomerRegistrationModel reg, DetailedPolicyModel? policy) {
    final policyName = policy?.policyName ?? 'Enrolled Policy #${reg.policyId.substring(0, reg.policyId.length > 8 ? 8 : reg.policyId.length)}';
    final policyCategory = policy?.category ?? 'INSURANCE';
    final limit = policy != null ? '\$${policy.coverageLimit.toStringAsFixed(0)}' : 'Underwritten';

    return GlassCard(
      padding: const EdgeInsets.all(18),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                decoration: BoxDecoration(
                  color: AppTheme.gradientSkyBlue.withValues(alpha: 0.12),
                  borderRadius: BorderRadius.circular(10),
                ),
                child: Text(
                  policyCategory,
                  style: const TextStyle(
                    fontSize: 11,
                    fontWeight: FontWeight.w700,
                    color: AppTheme.gradientSkyBlue,
                  ),
                ),
              ),
              StatusBadge.fromStatus(reg.status),
            ],
          ),
          const SizedBox(height: 12),
          Text(
            policyName,
            style: const TextStyle(
              fontSize: 16,
              fontWeight: FontWeight.w800,
              color: AppTheme.textPrimary,
              letterSpacing: -0.2,
            ),
          ),
          const SizedBox(height: 4),
          Text(
            'Ref: ${reg.id}',
            style: const TextStyle(
              fontSize: 11,
              color: AppTheme.textMuted,
            ),
          ),
          const SizedBox(height: 10),
          Row(
            children: [
              const Icon(Icons.shield_outlined, size: 16, color: AppTheme.textSecondary),
              const SizedBox(width: 6),
              Text(
                'Coverage Limit: $limit',
                style: const TextStyle(
                  fontSize: 13,
                  fontWeight: FontWeight.w600,
                  color: AppTheme.textPrimary,
                ),
              ),
            ],
          ),

          // Action buttons for Awaiting Confirmation
          if (reg.isAwaitingConfirmation) ...[
            const Divider(color: AppTheme.borderLight, height: 24),
            Container(
              padding: const EdgeInsets.all(10),
              decoration: BoxDecoration(
                color: AppTheme.warning.withValues(alpha: 0.1),
                borderRadius: BorderRadius.circular(12),
              ),
              child: const Row(
                children: [
                  Icon(Icons.info_outline_rounded, size: 16, color: AppTheme.warning),
                  SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      'Please review terms and confirm affirmative acceptance to activate coverage.',
                      style: TextStyle(fontSize: 11, color: Color(0xFF92400E)),
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 12),
            Row(
              children: [
                Expanded(
                  child: ElevatedButton(
                    onPressed: () => _handleConfirm(reg.id),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: AppTheme.darkTeal,
                      padding: const EdgeInsets.symmetric(vertical: 10),
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
                    ),
                    child: const Text('Confirm Policy', style: TextStyle(fontSize: 13)),
                  ),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: OutlinedButton(
                    onPressed: () => _handleDecline(reg.id),
                    style: OutlinedButton.styleFrom(
                      padding: const EdgeInsets.symmetric(vertical: 10),
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
                    ),
                    child: const Text('Decline', style: TextStyle(fontSize: 13, color: AppTheme.error)),
                  ),
                ),
              ],
            ),
          ],

          // View details CTA
          if (policy != null) ...[
            const SizedBox(height: 10),
            Align(
              alignment: Alignment.centerRight,
              child: TextButton.icon(
                icon: const Icon(Icons.visibility_outlined, size: 16),
                label: const Text('View Policy Clauses & Verification', style: TextStyle(fontSize: 12, fontWeight: FontWeight.w600)),
                onPressed: () {
                  context.push('/policy-detail/${policy.id}');
                },
              ),
            ),
          ],
        ],
      ),
    );
  }

  Widget _buildCatalogueCard(DetailedPolicyModel p) {
    return GlassCard(
      padding: const EdgeInsets.all(18),
      onTap: () => context.push('/policy-detail/${p.id}'),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                decoration: BoxDecoration(
                  color: AppTheme.gradientSkyBlue.withValues(alpha: 0.12),
                  borderRadius: BorderRadius.circular(10),
                ),
                child: Text(
                  p.category,
                  style: const TextStyle(
                    fontSize: 11,
                    fontWeight: FontWeight.w700,
                    color: AppTheme.gradientSkyBlue,
                  ),
                ),
              ),
              const Text(
                'Catalogue Scheme',
                style: TextStyle(fontSize: 11, color: AppTheme.textMuted, fontWeight: FontWeight.w600),
              ),
            ],
          ),
          const SizedBox(height: 10),
          Text(
            p.policyName,
            style: const TextStyle(
              fontSize: 16,
              fontWeight: FontWeight.w800,
              color: AppTheme.textPrimary,
            ),
          ),
          const SizedBox(height: 4),
          Text(
            'Code: ${p.policyCode} • Insurer: ${p.insurerName}',
            style: const TextStyle(fontSize: 12, color: AppTheme.textSecondary),
          ),
          const SizedBox(height: 10),
          Text(
            'Coverage Limit: \$${p.coverageLimit.toStringAsFixed(0)} • Claim Window: ${p.claimFilingWindowDays} days',
            style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w600, color: AppTheme.textPrimary),
          ),
        ],
      ),
    );
  }

  Widget _buildEmptyState(String message) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32.0),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Container(
              width: 64,
              height: 64,
              decoration: BoxDecoration(
                color: AppTheme.gradientSkyBlue.withValues(alpha: 0.12),
                shape: BoxShape.circle,
              ),
              child: const Icon(Icons.shield_outlined, color: AppTheme.gradientSkyBlue, size: 32),
            ),
            const SizedBox(height: 16),
            Text(
              message,
              textAlign: TextAlign.center,
              style: const TextStyle(
                fontSize: 14,
                color: AppTheme.textSecondary,
                height: 1.4,
              ),
            ),
            const SizedBox(height: 20),
            ElevatedButton(
              onPressed: () => setState(() => _selectedFilter = 'CATALOGUE'),
              style: ElevatedButton.styleFrom(backgroundColor: AppTheme.darkTeal),
              child: const Text('Browse Policy Catalogue'),
            ),
          ],
        ),
      ),
    );
  }

  Future<void> _handleConfirm(String regId) async {
    final confirmed = await ref.read(customerDashboardProvider.notifier).confirmRegistration(regId);
    if (mounted && confirmed) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Policy registration confirmed! Your coverage is now active.'),
          backgroundColor: AppTheme.success,
        ),
      );
    }
  }

  Future<void> _handleDecline(String regId) async {
    final declined = await ref.read(customerDashboardProvider.notifier).declineRegistration(regId);
    if (mounted && declined) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Policy proposal declined.'),
          backgroundColor: AppTheme.textSecondary,
        ),
      );
    }
  }
}
