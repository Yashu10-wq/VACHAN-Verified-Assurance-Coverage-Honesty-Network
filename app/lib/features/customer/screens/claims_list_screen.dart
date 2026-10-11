import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../core/theme/app_theme.dart';
import '../../../shared/widgets/glass_card.dart';
import '../../../shared/widgets/status_badge.dart';
import '../models/claim_model.dart';
import '../providers/customer_provider.dart';
import '../widgets/customer_bottom_nav.dart';

class ClaimsListScreen extends ConsumerStatefulWidget {
  const ClaimsListScreen({super.key});

  @override
  ConsumerState<ClaimsListScreen> createState() => _ClaimsListScreenState();
}

class _ClaimsListScreenState extends ConsumerState<ClaimsListScreen> {
  String? _selectedStatus; // null for all

  @override
  Widget build(BuildContext context) {
    final claimsState = ref.watch(claimsListProvider);
    final isLoading = claimsState.isLoading;

    return Scaffold(
      backgroundColor: AppTheme.background,
      bottomNavigationBar: const CustomerBottomNav(currentIndex: 2),
      appBar: AppBar(
        title: const Text('My Insurance Claims'),
        automaticallyImplyLeading: false,
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh_rounded),
            onPressed: () {
              ref.read(claimsListProvider.notifier).fetchClaims(status: _selectedStatus);
            },
          ),
        ],
      ),
      floatingActionButton: FloatingActionButton.extended(
        backgroundColor: AppTheme.darkTeal,
        foregroundColor: Colors.white,
        icon: const Icon(Icons.add_rounded),
        label: const Text('File Claim', style: TextStyle(fontWeight: FontWeight.w700)),
        onPressed: () => context.push('/submit-claim'),
      ),
      body: SafeArea(
        child: RefreshIndicator(
          color: AppTheme.gradientSkyBlue,
          onRefresh: () async {
            await ref.read(claimsListProvider.notifier).fetchClaims(status: _selectedStatus);
          },
          child: Column(
            children: [
              // Filter Chips Row
              SingleChildScrollView(
                scrollDirection: Axis.horizontal,
                padding: const EdgeInsets.symmetric(horizontal: 20.0, vertical: 12.0),
                child: Row(
                  children: [
                    _buildFilterChip(null, 'All Claims'),
                    const SizedBox(width: 8),
                    _buildFilterChip('SUBMITTED', 'Submitted'),
                    const SizedBox(width: 8),
                    _buildFilterChip('IN_REVIEW', 'Under Review'),
                    const SizedBox(width: 8),
                    _buildFilterChip('APPROVED', 'Approved'),
                    const SizedBox(width: 8),
                    _buildFilterChip('PAID', 'Paid'),
                    const SizedBox(width: 8),
                    _buildFilterChip('REJECTED', 'Rejected'),
                  ],
                ),
              ),

              // Content List
              Expanded(
                child: isLoading
                    ? const Center(
                        child: CircularProgressIndicator(
                          valueColor: AlwaysStoppedAnimation<Color>(AppTheme.gradientSkyBlue),
                        ),
                      )
                    : _buildClaimsList(claimsState.claims),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildFilterChip(String? statusKey, String label) {
    final isSelected = _selectedStatus == statusKey;
    return GestureDetector(
      onTap: () {
        setState(() => _selectedStatus = statusKey);
        ref.read(claimsListProvider.notifier).fetchClaims(status: statusKey);
      },
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

  Widget _buildClaimsList(List<ClaimModel> claims) {
    if (claims.isEmpty) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(32.0),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Container(
                width: 68,
                height: 68,
                decoration: BoxDecoration(
                  color: AppTheme.gradientSkyBlue.withValues(alpha: 0.12),
                  shape: BoxShape.circle,
                ),
                child: const Icon(
                  Icons.medical_services_outlined,
                  color: AppTheme.gradientSkyBlue,
                  size: 34,
                ),
              ),
              const SizedBox(height: 18),
              const Text(
                'No Claims Filed Yet',
                style: TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.w800,
                  color: AppTheme.textPrimary,
                ),
              ),
              const SizedBox(height: 8),
              const Text(
                'When you experience an insured incident, file a claim here for fast AI-verified processing.',
                textAlign: TextAlign.center,
                style: TextStyle(
                  fontSize: 13,
                  color: AppTheme.textSecondary,
                  height: 1.4,
                ),
              ),
              const SizedBox(height: 22),
              ElevatedButton.icon(
                onPressed: () => context.push('/submit-claim'),
                icon: const Icon(Icons.add_rounded, size: 20),
                label: const Text('Submit a Claim'),
                style: ElevatedButton.styleFrom(backgroundColor: AppTheme.darkTeal),
              ),
            ],
          ),
        ),
      );
    }

    return ListView.separated(
      padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 8),
      itemCount: claims.length,
      separatorBuilder: (_, __) => const SizedBox(height: 12),
      itemBuilder: (context, index) {
        final claim = claims[index];
        return _buildClaimCard(claim);
      },
    );
  }

  Widget _buildClaimCard(ClaimModel claim) {
    return GlassCard(
      padding: const EdgeInsets.all(18),
      onTap: () => context.push('/claim-detail/${claim.id}'),
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
                  claim.claimCategory,
                  style: const TextStyle(
                    fontSize: 11,
                    fontWeight: FontWeight.w700,
                    color: AppTheme.gradientSkyBlue,
                  ),
                ),
              ),
              StatusBadge.fromStatus(claim.status),
            ],
          ),
          const SizedBox(height: 12),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                'Claim #${claim.id.substring(0, claim.id.length > 8 ? 8 : claim.id.length)}',
                style: const TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.w800,
                  color: AppTheme.textPrimary,
                ),
              ),
              Text(
                '\$${claim.requestedAmount}',
                style: const TextStyle(
                  fontSize: 17,
                  fontWeight: FontWeight.w800,
                  color: AppTheme.darkTeal,
                ),
              ),
            ],
          ),
          const SizedBox(height: 6),
          Text(
            'Incident Date: ${claim.incidentDate}',
            style: const TextStyle(fontSize: 12, color: AppTheme.textSecondary),
          ),
          const SizedBox(height: 8),
          Text(
            claim.description,
            maxLines: 2,
            overflow: TextOverflow.ellipsis,
            style: const TextStyle(fontSize: 13, color: AppTheme.textPrimary, height: 1.3),
          ),
          const SizedBox(height: 12),
          const Row(
            mainAxisAlignment: MainAxisAlignment.end,
            children: [
              Text(
                'View Evaluation & Evidence',
                style: TextStyle(
                  fontSize: 12,
                  fontWeight: FontWeight.w700,
                  color: AppTheme.gradientSkyBlue,
                ),
              ),
              SizedBox(width: 4),
              Icon(Icons.chevron_right_rounded, size: 16, color: AppTheme.gradientSkyBlue),
            ],
          ),
        ],
      ),
    );
  }
}
