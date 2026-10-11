import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../core/theme/app_theme.dart';
import '../../../shared/widgets/glass_card.dart';
import '../../../shared/widgets/status_badge.dart';
import '../../customer/models/claim_model.dart';
import '../providers/authority_provider.dart';

class AuthorityClaimReviewScreen extends ConsumerStatefulWidget {
  final String claimId;

  const AuthorityClaimReviewScreen({super.key, required this.claimId});

  @override
  ConsumerState<AuthorityClaimReviewScreen> createState() => _AuthorityClaimReviewScreenState();
}

class _AuthorityClaimReviewScreenState extends ConsumerState<AuthorityClaimReviewScreen> {
  bool _isActionInProgress = false;
  String? _actionErrorMessage;

  Future<void> _assessClaim() async {
    setState(() {
      _isActionInProgress = true;
      _actionErrorMessage = null;
    });

    try {
      final apiService = ref.read(authorityApiServiceProvider);
      await apiService.assessClaim(widget.claimId);

      ref.invalidate(authorityClaimDetailProvider(widget.claimId));
      ref.read(authorityClaimsProvider.notifier).fetchClaims();

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Deterministic eligibility assessment completed!'),
            backgroundColor: AppTheme.success,
          ),
        );
      }
    } catch (e) {
      setState(() => _actionErrorMessage = e.toString());
    } finally {
      if (mounted) setState(() => _isActionInProgress = false);
    }
  }

  Future<void> _showTransitionDialog({
    required String targetStatus,
    required String title,
    required String actionButtonText,
    required Color buttonColor,
    bool isSimulatedPayment = false,
  }) async {
    final reasonController = TextEditingController();
    String? dialogError;

    await showDialog(
      context: context,
      builder: (ctx) => StatefulBuilder(
        builder: (ctx, setDialogState) => AlertDialog(
          title: Text(title, style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 17)),
          content: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                if (dialogError != null) ...[
                  Text(dialogError!, style: const TextStyle(color: AppTheme.error, fontSize: 12)),
                  const SizedBox(height: 8),
                ],
                if (isSimulatedPayment) ...[
                  Container(
                    padding: const EdgeInsets.all(10),
                    margin: const EdgeInsets.only(bottom: 12),
                    decoration: BoxDecoration(
                      color: AppTheme.darkTeal.withValues(alpha: 0.08),
                      borderRadius: BorderRadius.circular(10),
                    ),
                    child: const Text(
                      'Simulated payment confirms audit settlement on-chain. It records state transition to PAID without initiating external fiat wires.',
                      style: TextStyle(fontSize: 11, color: Color(0xFF132A33)),
                    ),
                  ),
                ],
                const Text(
                  'Mandatory Adjudication Reason *',
                  style: TextStyle(fontSize: 12, fontWeight: FontWeight.w700, color: AppTheme.textSecondary),
                ),
                const SizedBox(height: 6),
                TextField(
                  controller: reasonController,
                  maxLines: 3,
                  decoration: const InputDecoration(
                    hintText: 'Enter formal statutory reason (min 5 characters)...',
                    border: OutlineInputBorder(),
                  ),
                ),
              ],
            ),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(ctx),
              child: const Text('Cancel'),
            ),
            ElevatedButton(
              onPressed: () async {
                final reason = reasonController.text.trim();
                if (reason.length < 5) {
                  setDialogState(() => dialogError = 'Reason must be at least 5 characters long.');
                  return;
                }

                Navigator.pop(ctx);
                await _executeStatusTransition(
                  targetStatus: targetStatus,
                  reason: reason,
                  isSimulatedPayment: isSimulatedPayment,
                );
              },
              style: ElevatedButton.styleFrom(backgroundColor: buttonColor),
              child: Text(actionButtonText),
            ),
          ],
        ),
      ),
    );
  }

  Future<void> _executeStatusTransition({
    required String targetStatus,
    required String reason,
    required bool isSimulatedPayment,
  }) async {
    setState(() {
      _isActionInProgress = true;
      _actionErrorMessage = null;
    });

    try {
      final apiService = ref.read(authorityApiServiceProvider);
      if (isSimulatedPayment) {
        await apiService.simulatePayment(claimId: widget.claimId, reason: reason);
      } else {
        await apiService.transitionStatus(claimId: widget.claimId, targetStatus: targetStatus, reason: reason);
      }

      ref.invalidate(authorityClaimDetailProvider(widget.claimId));
      ref.read(authorityClaimsProvider.notifier).fetchClaims();

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Claim successfully transitioned to $targetStatus!'),
            backgroundColor: AppTheme.success,
          ),
        );
      }
    } catch (e) {
      setState(() => _actionErrorMessage = e.toString());
    } finally {
      if (mounted) setState(() => _isActionInProgress = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final claimAsync = ref.watch(authorityClaimDetailProvider(widget.claimId));
    final duplicatesAsync = ref.watch(authorityDuplicatesProvider(widget.claimId));

    return Scaffold(
      backgroundColor: AppTheme.background,
      appBar: AppBar(
        title: const Text('Claim Adjudication Review'),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_ios_new_rounded, size: 20),
          onPressed: () => context.pop(),
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh_rounded),
            onPressed: () {
              ref.invalidate(authorityClaimDetailProvider(widget.claimId));
              ref.invalidate(authorityDuplicatesProvider(widget.claimId));
            },
          ),
        ],
      ),
      body: SafeArea(
        child: claimAsync.when(
          loading: () => const Center(
            child: CircularProgressIndicator(valueColor: AlwaysStoppedAnimation<Color>(AppTheme.gradientSkyBlue)),
          ),
          error: (err, _) => Center(
            child: Padding(
              padding: const EdgeInsets.all(24.0),
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  const Icon(Icons.error_outline_rounded, color: AppTheme.error, size: 40),
                  const SizedBox(height: 12),
                  Text(err.toString(), textAlign: TextAlign.center),
                  const SizedBox(height: 16),
                  ElevatedButton(
                    onPressed: () => ref.refresh(authorityClaimDetailProvider(widget.claimId)),
                    child: const Text('Retry'),
                  ),
                ],
              ),
            ),
          ),
          data: (claim) => _buildReviewContent(context, claim, duplicatesAsync),
        ),
      ),
    );
  }

  Widget _buildReviewContent(
    BuildContext context,
    ClaimModel claim,
    AsyncValue<List<Map<String, dynamic>>> duplicatesAsync,
  ) {
    final assessment = claim.latestAssessment;
    final isApproved = claim.status == 'APPROVED';
    final isTerminal = claim.status == 'PAID' || claim.status == 'REJECTED';

    return SingleChildScrollView(
      padding: const EdgeInsets.symmetric(horizontal: 20.0, vertical: 12.0),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (_actionErrorMessage != null) ...[
            Container(
              padding: const EdgeInsets.all(12),
              margin: const EdgeInsets.only(bottom: 16),
              decoration: BoxDecoration(
                color: AppTheme.error.withValues(alpha: 0.1),
                borderRadius: BorderRadius.circular(14),
                border: Border.all(color: AppTheme.error.withValues(alpha: 0.3)),
              ),
              child: Row(
                children: [
                  const Icon(Icons.error_outline_rounded, color: AppTheme.error, size: 20),
                  const SizedBox(width: 10),
                  Expanded(
                    child: Text(_actionErrorMessage!, style: const TextStyle(fontSize: 12, color: AppTheme.error)),
                  ),
                ],
              ),
            ),
          ],

          // 1. Claim Header GlassCard
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
                        style: const TextStyle(fontSize: 11, fontWeight: FontWeight.w700, color: AppTheme.gradientSkyBlue),
                      ),
                    ),
                    StatusBadge.fromStatus(claim.status),
                  ],
                ),
                const SizedBox(height: 14),
                Text(
                  'Claim ${claim.claimNumber}',
                  style: const TextStyle(fontSize: 20, fontWeight: FontWeight.w800, color: AppTheme.textPrimary, letterSpacing: -0.3),
                ),
                const SizedBox(height: 6),
                Text('Customer UUID: ${claim.customerId}', style: const TextStyle(fontSize: 12, color: AppTheme.textSecondary)),
                Text('Policy UUID: ${claim.policyId}', style: const TextStyle(fontSize: 12, color: AppTheme.textSecondary)),
                Text('Incident Date: ${claim.incidentDate} • Filed: ${claim.submissionTimestamp.isNotEmpty ? claim.submissionTimestamp.substring(0, 10) : 'N/A'}',
                    style: const TextStyle(fontSize: 12, color: AppTheme.textSecondary)),
                if (claim.description.isNotEmpty) ...[
                  const SizedBox(height: 10),
                  Text(
                    'Incident Description:\n${claim.description}',
                    style: const TextStyle(fontSize: 12, color: AppTheme.textPrimary, height: 1.35),
                  ),
                ],
              ],
            ),
          ),

          const SizedBox(height: 16),

          // 2. Financial Overview Grid
          Row(
            children: [
              Expanded(
                child: _buildFinancialCard(
                  label: 'Requested',
                  value: '\$${claim.requestedAmount}',
                  color: AppTheme.textPrimary,
                ),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: _buildFinancialCard(
                  label: 'Limit',
                  value: assessment != null ? '\$${assessment.applicableLimit}' : 'Checking',
                  color: AppTheme.gradientSkyBlue,
                ),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: _buildFinancialCard(
                  label: 'Payable',
                  value: assessment != null ? '\$${assessment.potentiallyPayableAmount}' : 'Pending',
                  color: AppTheme.success,
                ),
              ),
            ],
          ),

          const SizedBox(height: 20),

          // 3. Deterministic Eligibility Engine Section
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              const Text(
                'Eligibility Assessment Rules',
                style: TextStyle(fontSize: 16, fontWeight: FontWeight.w800, color: AppTheme.textPrimary),
              ),
              TextButton.icon(
                onPressed: _isActionInProgress ? null : _assessClaim,
                icon: const Icon(Icons.sync_rounded, size: 16),
                label: const Text('Re-evaluate', style: TextStyle(fontSize: 12)),
              ),
            ],
          ),
          const SizedBox(height: 8),

          if (assessment == null) ...[
            GlassCard(
              padding: const EdgeInsets.all(20),
              child: Center(
                child: Column(
                  children: [
                    const Icon(Icons.rule_rounded, size: 36, color: AppTheme.textMuted),
                    const SizedBox(height: 10),
                    const Text('No Assessment Run Yet', style: TextStyle(fontWeight: FontWeight.w700, fontSize: 14)),
                    const SizedBox(height: 4),
                    const Text('Execute the deterministic rule engine against registered policy terms.', style: TextStyle(fontSize: 11, color: AppTheme.textSecondary)),
                    const SizedBox(height: 14),
                    ElevatedButton(
                      onPressed: _isActionInProgress ? null : _assessClaim,
                      style: ElevatedButton.styleFrom(backgroundColor: AppTheme.darkTeal),
                      child: const Text('Run Eligibility Assessment'),
                    ),
                  ],
                ),
              ),
            ),
          ] else ...[
            GlassCard(
              padding: const EdgeInsets.all(18),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      const Text('Overall Deterministic Outcome:', style: TextStyle(fontSize: 12, fontWeight: FontWeight.w700, color: AppTheme.textSecondary)),
                      StatusBadge(
                        label: assessment.overallOutcome,
                        color: assessment.overallOutcome == 'ELIGIBLE' ? AppTheme.success : AppTheme.warning,
                      ),
                    ],
                  ),
                  const Divider(color: AppTheme.borderLight, height: 20),
                  ...assessment.rulesEvaluated.map((rule) {
                    final isPass = rule.result == 'PASS';
                    return Padding(
                      padding: const EdgeInsets.only(bottom: 8.0),
                      child: Row(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Icon(isPass ? Icons.check_circle_rounded : Icons.warning_amber_rounded, size: 16, color: isPass ? AppTheme.success : AppTheme.warning),
                          const SizedBox(width: 8),
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(rule.ruleId.replaceAll('_', ' '), style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w700, color: AppTheme.textPrimary)),
                                Text(rule.explanation, style: const TextStyle(fontSize: 11, color: AppTheme.textSecondary)),
                              ],
                            ),
                          ),
                        ],
                      ),
                    );
                  }),
                ],
              ),
            ),
          ],

          const SizedBox(height: 20),

          // 4. Duplicate Claim Detection Signals
          const Text(
            'Duplicate Incident Analysis',
            style: TextStyle(fontSize: 16, fontWeight: FontWeight.w800, color: AppTheme.textPrimary),
          ),
          const SizedBox(height: 8),

          duplicatesAsync.when(
            loading: () => const LinearProgressIndicator(),
            error: (_, __) => const SizedBox.shrink(),
            data: (duplicates) {
              return GlassCard(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Icon(duplicates.isEmpty ? Icons.shield_outlined : Icons.report_problem_outlined,
                            size: 18, color: duplicates.isEmpty ? AppTheme.success : AppTheme.warning),
                        const SizedBox(width: 8),
                        Text(
                          duplicates.isEmpty ? 'Zero Duplicate Incident Signals' : '${duplicates.length} Potential Duplicate Incident Candidates',
                          style: TextStyle(
                            fontSize: 13,
                            fontWeight: FontWeight.w800,
                            color: duplicates.isEmpty ? AppTheme.success : const Color(0xFFB45309),
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 4),
                    const Text(
                      'Statutory Notice: Duplicate candidates are an advisory signal to check past incidents, NOT proof of fraud.',
                      style: TextStyle(fontSize: 11, color: AppTheme.textSecondary, fontStyle: FontStyle.italic),
                    ),
                    if (duplicates.isNotEmpty) ...[
                      const SizedBox(height: 10),
                      ...duplicates.map((dup) {
                        return Container(
                          padding: const EdgeInsets.all(10),
                          margin: const EdgeInsets.only(bottom: 6),
                          decoration: BoxDecoration(
                            color: AppTheme.backgroundSurface,
                            borderRadius: BorderRadius.circular(10),
                          ),
                          child: Text(
                            'Candidate #${dup['candidate_claim_id']?.toString().substring(0, 8)} • Match Score: ${(dup['match_score'] as num? ?? 0.0).toStringAsFixed(2)} • Date: ${dup['incident_date']}',
                            style: const TextStyle(fontSize: 11, color: AppTheme.textPrimary),
                          ),
                        );
                      }),
                    ],
                  ],
                ),
              );
            },
          ),

          const SizedBox(height: 20),

          // 5. Submitted Evidence Documents
          const Text(
            'Submitted Evidence Documents',
            style: TextStyle(fontSize: 16, fontWeight: FontWeight.w800, color: AppTheme.textPrimary),
          ),
          const SizedBox(height: 8),

          if (claim.evidence.isEmpty) ...[
            const GlassCard(
              padding: EdgeInsets.all(16),
              child: Text('No evidence files attached to this claim.', style: TextStyle(fontSize: 12, color: AppTheme.textSecondary)),
            ),
          ] else ...[
            ...claim.evidence.map((ev) {
              return Padding(
                padding: const EdgeInsets.only(bottom: 8.0),
                child: GlassCard(
                  padding: const EdgeInsets.all(14),
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Row(
                        children: [
                          const Icon(Icons.file_present_rounded, size: 20, color: AppTheme.gradientSkyBlue),
                          const SizedBox(width: 10),
                          Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(ev.originalFilename, style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w700, color: AppTheme.textPrimary)),
                              Text('${ev.evidenceType} • ${(ev.fileSizeBytes / 1024).toStringAsFixed(1)} KB', style: const TextStyle(fontSize: 10, color: AppTheme.textSecondary)),
                            ],
                          ),
                        ],
                      ),
                      TextButton.icon(
                        icon: const Icon(Icons.open_in_new_rounded, size: 14),
                        label: const Text('Signed URL', style: TextStyle(fontSize: 11)),
                        onPressed: () async {
                          try {
                            final url = await ref.read(authorityApiServiceProvider).getEvidenceSignedUrl(claim.id, ev.id);
                            if (context.mounted) {
                              showDialog(
                                context: context,
                                builder: (ctx) => AlertDialog(
                                  title: const Text('Signed Asset URL (300s TTL)'),
                                  content: SelectableText(url, style: const TextStyle(fontSize: 12)),
                                  actions: [TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('Close'))],
                                ),
                              );
                            }
                          } catch (e) {
                            if (context.mounted) {
                              ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Failed: $e'), backgroundColor: AppTheme.error));
                            }
                          }
                        },
                      ),
                    ],
                  ),
                ),
              );
            }),
          ],

          const SizedBox(height: 20),

          // 6. Claim Status History Audit Trail
          if (claim.statusHistory.isNotEmpty) ...[
            const Text(
              'Lifecycle Audit Timeline',
              style: TextStyle(fontSize: 16, fontWeight: FontWeight.w800, color: AppTheme.textPrimary),
            ),
            const SizedBox(height: 8),
            GlassCard(
              padding: const EdgeInsets.all(16),
              child: Column(
                children: claim.statusHistory.map((hist) {
                  return Padding(
                    padding: const EdgeInsets.only(bottom: 10.0),
                    child: Row(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Icon(Icons.history_rounded, size: 16, color: AppTheme.textMuted),
                        const SizedBox(width: 10),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text('${hist.previousStatus ?? 'NEW'} → ${hist.newStatus} (by ${hist.actorRole})',
                                  style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w700, color: AppTheme.textPrimary)),
                              Text(hist.reason, style: const TextStyle(fontSize: 11, color: AppTheme.textSecondary)),
                              Text(hist.createdAt.substring(0, 19).replaceAll('T', ' '), style: const TextStyle(fontSize: 10, color: AppTheme.textMuted)),
                            ],
                          ),
                        ),
                      ],
                    ),
                  );
                }).toList(),
              ),
            ),
            const SizedBox(height: 24),
          ],

          // 7. Authority Action Panel
          if (!isTerminal) ...[
            const Text(
              'Authority Decision Actions',
              style: TextStyle(fontSize: 16, fontWeight: FontWeight.w800, color: AppTheme.textPrimary),
            ),
            const SizedBox(height: 10),

            Row(
              children: [
                Expanded(
                  child: ElevatedButton.icon(
                    onPressed: _isActionInProgress
                        ? null
                        : () => _showTransitionDialog(
                              targetStatus: 'APPROVED',
                              title: 'Approve Claim',
                              actionButtonText: 'Confirm Approval',
                              buttonColor: AppTheme.success,
                            ),
                    icon: const Icon(Icons.check_circle_rounded),
                    label: const Text('Approve'),
                    style: ElevatedButton.styleFrom(backgroundColor: AppTheme.success, foregroundColor: Colors.white, padding: const EdgeInsets.symmetric(vertical: 12)),
                  ),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: ElevatedButton.icon(
                    onPressed: _isActionInProgress
                        ? null
                        : () => _showTransitionDialog(
                              targetStatus: 'EVIDENCE_REQUESTED',
                              title: 'Request Additional Evidence',
                              actionButtonText: 'Request Evidence',
                              buttonColor: const Color(0xFFD97706),
                            ),
                    icon: const Icon(Icons.help_outline_rounded),
                    label: const Text('Req Evidence'),
                    style: ElevatedButton.styleFrom(backgroundColor: const Color(0xFFD97706), foregroundColor: Colors.white, padding: const EdgeInsets.symmetric(vertical: 12)),
                  ),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: ElevatedButton.icon(
                    onPressed: _isActionInProgress
                        ? null
                        : () => _showTransitionDialog(
                              targetStatus: 'REJECTED',
                              title: 'Reject Claim',
                              actionButtonText: 'Reject Claim',
                              buttonColor: AppTheme.error,
                            ),
                    icon: const Icon(Icons.cancel_rounded),
                    label: const Text('Reject'),
                    style: ElevatedButton.styleFrom(backgroundColor: AppTheme.error, foregroundColor: Colors.white, padding: const EdgeInsets.symmetric(vertical: 12)),
                  ),
                ),
              ],
            ),
          ],

          // Simulated Payment Button (Exclusively for APPROVED claims)
          if (isApproved) ...[
            const SizedBox(height: 14),
            SizedBox(
              width: double.infinity,
              child: ElevatedButton.icon(
                onPressed: _isActionInProgress
                    ? null
                    : () => _showTransitionDialog(
                          targetStatus: 'PAID',
                          title: 'Execute Simulated Settlement',
                          actionButtonText: 'Settle Simulated Payment',
                          buttonColor: const Color(0xFF0D9488),
                          isSimulatedPayment: true,
                        ),
                icon: const Icon(Icons.payments_rounded),
                label: const Text('Execute Simulated Settlement Payment (Audit Record)'),
                style: ElevatedButton.styleFrom(
                  backgroundColor: const Color(0xFF0D9488),
                  foregroundColor: Colors.white,
                  padding: const EdgeInsets.symmetric(vertical: 14),
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                ),
              ),
            ),
          ],

          const SizedBox(height: 36),
        ],
      ),
    );
  }

  Widget _buildFinancialCard({required String label, required String value, required Color color}) {
    return GlassCard(
      padding: const EdgeInsets.all(14),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(label, style: const TextStyle(fontSize: 10, fontWeight: FontWeight.w600, color: AppTheme.textSecondary)),
          const SizedBox(height: 4),
          Text(value, style: TextStyle(fontSize: 16, fontWeight: FontWeight.w800, color: color)),
        ],
      ),
    );
  }
}
