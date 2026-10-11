import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../core/theme/app_theme.dart';
import '../../../shared/widgets/glass_card.dart';
import '../../../shared/widgets/status_badge.dart';
import '../models/claim_model.dart';
import '../providers/customer_provider.dart';

final claimDetailFutureProvider =
    FutureProvider.family<ClaimModel, String>((ref, claimId) async {
  final apiService = ref.watch(customerApiServiceProvider);
  return await apiService.getClaimDetails(claimId);
});

class ClaimDetailScreen extends ConsumerWidget {
  final String claimId;

  const ClaimDetailScreen({super.key, required this.claimId});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final claimAsync = ref.watch(claimDetailFutureProvider(claimId));

    return Scaffold(
      backgroundColor: AppTheme.background,
      appBar: AppBar(
        title: const Text('Claim Evaluation Details'),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_ios_new_rounded, size: 20),
          onPressed: () => context.pop(),
        ),
      ),
      body: SafeArea(
        child: claimAsync.when(
          loading: () => const Center(
            child: CircularProgressIndicator(
              valueColor: AlwaysStoppedAnimation<Color>(AppTheme.gradientSkyBlue),
            ),
          ),
          error: (err, _) => Center(
            child: Padding(
              padding: const EdgeInsets.all(24.0),
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  const Icon(Icons.error_outline_rounded, color: AppTheme.error, size: 40),
                  const SizedBox(height: 14),
                  Text(err.toString(), textAlign: TextAlign.center),
                  const SizedBox(height: 16),
                  ElevatedButton(
                    onPressed: () => ref.refresh(claimDetailFutureProvider(claimId)),
                    child: const Text('Retry'),
                  ),
                ],
              ),
            ),
          ),
          data: (claim) => _buildDetailContent(context, claim),
        ),
      ),
    );
  }

  Widget _buildDetailContent(BuildContext context, ClaimModel claim) {
    return SingleChildScrollView(
      padding: const EdgeInsets.symmetric(horizontal: 20.0, vertical: 12.0),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Header Card
          GlassCard(
            padding: const EdgeInsets.all(20),
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
                const SizedBox(height: 14),
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Expanded(
                      child: Text(
                        'Claim #${claim.id.substring(0, claim.id.length > 8 ? 8 : claim.id.length)}',
                        style: const TextStyle(
                          fontSize: 20,
                          fontWeight: FontWeight.w800,
                          color: AppTheme.textPrimary,
                        ),
                      ),
                    ),
                    Text(
                      '\$${claim.requestedAmount}',
                      style: const TextStyle(
                        fontSize: 22,
                        fontWeight: FontWeight.w800,
                        color: AppTheme.darkTeal,
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 6),
                Text(
                  'Incident Date: ${claim.incidentDate} • Filed: ${claim.submissionTimestamp.split('T').first}',
                  style: const TextStyle(fontSize: 12, color: AppTheme.textSecondary),
                ),
                const SizedBox(height: 14),
                const Text(
                  'Incident Description:',
                  style: TextStyle(fontSize: 13, fontWeight: FontWeight.w700, color: AppTheme.textPrimary),
                ),
                const SizedBox(height: 4),
                Text(
                  claim.description,
                  style: const TextStyle(fontSize: 13, color: AppTheme.textPrimary, height: 1.4),
                ),
              ],
            ),
          ),

          const SizedBox(height: 20),

          // Deterministic Eligibility Assessment
          if (claim.latestAssessment != null) ...[
            _buildAssessmentSection(claim.latestAssessment!),
            const SizedBox(height: 20),
          ],

          // Evidence Section
          _buildEvidenceSection(claim.evidence),

          const SizedBox(height: 20),

          // Lifecycle History Section
          if (claim.statusHistory.isNotEmpty) ...[
            _buildHistorySection(claim.statusHistory),
            const SizedBox(height: 20),
          ],

          const SizedBox(height: 16),
        ],
      ),
    );
  }

  Widget _buildAssessmentSection(ClaimAssessmentModel assessment) {
    Color outcomeColor;
    if (assessment.overallOutcome == 'ELIGIBLE') {
      outcomeColor = AppTheme.success;
    } else if (assessment.overallOutcome == 'POTENTIALLY_ELIGIBLE' ||
        assessment.overallOutcome == 'REQUIRES_MANUAL_REVIEW') {
      outcomeColor = AppTheme.warning;
    } else {
      outcomeColor = AppTheme.error;
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text(
          'Automated Eligibility Assessment',
          style: TextStyle(
            fontSize: 17,
            fontWeight: FontWeight.w800,
            color: AppTheme.textPrimary,
            letterSpacing: -0.3,
          ),
        ),
        const SizedBox(height: 10),
        GlassCard(
          padding: const EdgeInsets.all(18),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  const Text(
                    'Deterministic Outcome',
                    style: TextStyle(fontSize: 14, fontWeight: FontWeight.w600, color: AppTheme.textSecondary),
                  ),
                  StatusBadge(
                    label: assessment.overallOutcome.replaceAll('_', ' '),
                    color: outcomeColor,
                  ),
                ],
              ),
              const Divider(color: AppTheme.borderLight, height: 22),
              Row(
                children: [
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text('Potentially Payable', style: TextStyle(fontSize: 11, color: AppTheme.textSecondary)),
                        const SizedBox(height: 2),
                        Text(
                          '\$${assessment.potentiallyPayableAmount}',
                          style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w800, color: AppTheme.success),
                        ),
                      ],
                    ),
                  ),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text('Applicable Limit', style: TextStyle(fontSize: 11, color: AppTheme.textSecondary)),
                        const SizedBox(height: 2),
                        Text(
                          '\$${assessment.applicableLimit}',
                          style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w800, color: AppTheme.textPrimary),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
              if (assessment.rulesEvaluated.isNotEmpty) ...[
                const SizedBox(height: 16),
                const Text(
                  'Rules Evaluated:',
                  style: TextStyle(fontSize: 13, fontWeight: FontWeight.w700, color: AppTheme.textPrimary),
                ),
                const SizedBox(height: 8),
                ...assessment.rulesEvaluated.map((rule) {
                  final isPass = rule.result == 'PASS';
                  return Container(
                    margin: const EdgeInsets.only(bottom: 8),
                    padding: const EdgeInsets.all(10),
                    decoration: BoxDecoration(
                      color: isPass
                          ? AppTheme.success.withValues(alpha: 0.08)
                          : AppTheme.warning.withValues(alpha: 0.08),
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: Row(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Icon(
                          isPass ? Icons.check_circle_rounded : Icons.info_rounded,
                          size: 16,
                          color: isPass ? AppTheme.success : AppTheme.warning,
                        ),
                        const SizedBox(width: 8),
                        Expanded(
                          child: Text(
                            '${rule.ruleId.replaceAll('_', ' ')}: ${rule.explanation}',
                            style: const TextStyle(fontSize: 12, color: AppTheme.textPrimary),
                          ),
                        ),
                      ],
                    ),
                  );
                }),
              ],
            ],
          ),
        ),
      ],
    );
  }

  Widget _buildEvidenceSection(List<ClaimEvidenceModel> evidenceList) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text(
          'Evidence Documents',
          style: TextStyle(
            fontSize: 17,
            fontWeight: FontWeight.w800,
            color: AppTheme.textPrimary,
            letterSpacing: -0.3,
          ),
        ),
        const SizedBox(height: 10),
        if (evidenceList.isEmpty) ...[
          const GlassCard(
            padding: EdgeInsets.all(16),
            child: Row(
              children: [
                Icon(Icons.folder_open_rounded, color: AppTheme.textMuted, size: 24),
                SizedBox(width: 12),
                Expanded(
                  child: Text(
                    'No evidence files uploaded yet.',
                    style: TextStyle(fontSize: 13, color: AppTheme.textSecondary),
                  ),
                ),
              ],
            ),
          ),
        ] else ...[
          ...evidenceList.map((e) {
            final sizeKb = (e.fileSizeBytes / 1024).toStringAsFixed(1);
            return GlassCard(
              margin: const EdgeInsets.only(bottom: 8),
              padding: const EdgeInsets.all(14),
              child: Row(
                children: [
                  const Icon(Icons.attach_file_rounded, color: AppTheme.gradientSkyBlue, size: 22),
                  const SizedBox(width: 10),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          e.originalFilename,
                          style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w700, color: AppTheme.textPrimary),
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                        ),
                        Text(
                          '$sizeKb KB • ${e.mimeType}',
                          style: const TextStyle(fontSize: 11, color: AppTheme.textSecondary),
                        ),
                      ],
                    ),
                  ),
                  const Icon(Icons.lock_rounded, size: 16, color: AppTheme.success),
                ],
              ),
            );
          }),
        ],
      ],
    );
  }

  Widget _buildHistorySection(List<ClaimStatusHistoryModel> history) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text(
          'Audit Lifecycle History',
          style: TextStyle(
            fontSize: 17,
            fontWeight: FontWeight.w800,
            color: AppTheme.textPrimary,
            letterSpacing: -0.3,
          ),
        ),
        const SizedBox(height: 10),
        GlassCard(
          padding: const EdgeInsets.all(16),
          child: ListView.separated(
            shrinkWrap: true,
            physics: const NeverScrollableScrollPhysics(),
            itemCount: history.length,
            separatorBuilder: (_, __) => const Divider(color: AppTheme.borderLight, height: 16),
            itemBuilder: (context, index) {
              final h = history[index];
              return Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Container(
                    width: 8,
                    height: 8,
                    margin: const EdgeInsets.only(top: 5),
                    decoration: const BoxDecoration(
                      color: AppTheme.gradientSkyBlue,
                      shape: BoxShape.circle,
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            Text(
                              h.newStatus,
                              style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w700, color: AppTheme.textPrimary),
                            ),
                            Text(
                              h.createdAt.split('T').first,
                              style: const TextStyle(fontSize: 11, color: AppTheme.textMuted),
                            ),
                          ],
                        ),
                        const SizedBox(height: 2),
                        Text(
                          '${h.actorRole}: ${h.reason}',
                          style: const TextStyle(fontSize: 12, color: AppTheme.textSecondary),
                        ),
                      ],
                    ),
                  ),
                ],
              );
            },
          ),
        ),
      ],
    );
  }
}
