import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../core/theme/app_theme.dart';
import '../../../shared/widgets/glass_card.dart';
import '../../../shared/widgets/status_badge.dart';
import '../models/verification_report_model.dart';
import '../providers/customer_provider.dart';

class VerificationReportScreen extends ConsumerStatefulWidget {
  final String reportId;

  const VerificationReportScreen({super.key, required this.reportId});

  @override
  ConsumerState<VerificationReportScreen> createState() => _VerificationReportScreenState();
}

class _VerificationReportScreenState extends ConsumerState<VerificationReportScreen> {
  String _selectedFilter = 'ALL';

  @override
  Widget build(BuildContext context) {
    final reportAsync = ref.watch(verificationReportProvider(widget.reportId));

    return Scaffold(
      backgroundColor: AppTheme.background,
      appBar: AppBar(
        title: const Text('VoiceGuard Verification'),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_ios_new_rounded, size: 20),
          onPressed: () => context.pop(),
        ),
      ),
      body: SafeArea(
        child: reportAsync.when(
          loading: () => const Center(
            child: CircularProgressIndicator(
              valueColor: AlwaysStoppedAnimation<Color>(AppTheme.gradientSkyBlue),
            ),
          ),
          error: (err, _) => _buildErrorState(err.toString()),
          data: (report) {
            if (report == null) {
              return _buildMissingReportState();
            }
            return _buildReportContent(report);
          },
        ),
      ),
    );
  }

  Widget _buildMissingReportState() {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(28.0),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Container(
              width: 72,
              height: 72,
              decoration: BoxDecoration(
                color: AppTheme.backgroundSurface,
                borderRadius: BorderRadius.circular(20),
              ),
              child: const Icon(Icons.analytics_outlined, size: 36, color: AppTheme.textMuted),
            ),
            const SizedBox(height: 18),
            const Text(
              'No Verification Report Available',
              style: TextStyle(
                fontSize: 18,
                fontWeight: FontWeight.w800,
                color: AppTheme.textPrimary,
              ),
            ),
            const SizedBox(height: 8),
            const Text(
              'A verification report has not been finalized for this sales session yet. '
              'Verification occurs after audio transcription is complete and policy clauses are analyzed.',
              textAlign: TextAlign.center,
              style: TextStyle(fontSize: 13, color: AppTheme.textSecondary, height: 1.4),
            ),
            const SizedBox(height: 20),
            ElevatedButton(
              onPressed: () => ref.refresh(verificationReportProvider(widget.reportId)),
              style: ElevatedButton.styleFrom(
                backgroundColor: AppTheme.darkTeal,
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
              ),
              child: const Text('Check Again'),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildErrorState(String message) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24.0),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.error_outline_rounded, color: AppTheme.error, size: 40),
            const SizedBox(height: 14),
            Text(message, textAlign: TextAlign.center),
            const SizedBox(height: 16),
            ElevatedButton(
              onPressed: () => ref.refresh(verificationReportProvider(widget.reportId)),
              child: const Text('Retry'),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildReportContent(VerificationReportModel report) {
    final filteredFindings = _selectedFilter == 'ALL'
        ? report.findings
        : report.findings.where((f) => f.classification == _selectedFilter).toList();

    return RefreshIndicator(
      onRefresh: () async {
        ref.invalidate(verificationReportProvider(widget.reportId));
      },
      child: SingleChildScrollView(
        padding: const EdgeInsets.symmetric(horizontal: 20.0, vertical: 12.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Top Overview GlassCard
            GlassCard(
              padding: const EdgeInsets.all(20),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      _buildIntegrityBadge(report.overallIntegrityStatus),
                      Text(
                        'Report v${report.reportVersion}',
                        style: const TextStyle(
                          fontSize: 12,
                          fontWeight: FontWeight.w700,
                          color: AppTheme.textMuted,
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 12),
                  const Text(
                    'Policy-Promise Audit Summary',
                    style: TextStyle(
                      fontSize: 19,
                      fontWeight: FontWeight.w800,
                      color: AppTheme.textPrimary,
                      letterSpacing: -0.3,
                    ),
                  ),
                  if (report.summary != null && report.summary!.isNotEmpty) ...[
                    const SizedBox(height: 8),
                    Text(
                      report.summary!,
                      style: const TextStyle(
                        fontSize: 13,
                        color: AppTheme.textSecondary,
                        height: 1.4,
                      ),
                    ),
                  ],
                  const SizedBox(height: 16),
                  // Disclaimer Card (Mandatory Contract Distinction)
                  Container(
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: AppTheme.darkTeal.withValues(alpha: 0.06),
                      borderRadius: BorderRadius.circular(14),
                      border: Border.all(color: AppTheme.darkTeal.withValues(alpha: 0.12)),
                    ),
                    child: const Row(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Icon(Icons.gavel_rounded, size: 18, color: AppTheme.darkTeal),
                        SizedBox(width: 10),
                        Expanded(
                          child: Text(
                            'AI-Assisted Grounding Notice: Findings compare transcript utterances against underwritten policy terms. These findings provide transparency and do not substitute for official contract terms or claim rulings.',
                            style: TextStyle(
                              fontSize: 11,
                              color: Color(0xFF1E3A42),
                              height: 1.35,
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),

            const SizedBox(height: 16),

            // Category Count Badges
            SingleChildScrollView(
              scrollDirection: Axis.horizontal,
              child: Row(
                children: [
                  _buildCountChip(
                    label: 'SUPPORTED',
                    count: report.supportedCount,
                    color: AppTheme.success,
                    isSelected: _selectedFilter == 'SUPPORTED',
                    onTap: () => _toggleFilter('SUPPORTED'),
                  ),
                  const SizedBox(width: 8),
                  _buildCountChip(
                    label: 'PARTLY TRUE',
                    count: report.partlyTrueCount,
                    color: AppTheme.warning,
                    isSelected: _selectedFilter == 'PARTLY_TRUE',
                    onTap: () => _toggleFilter('PARTLY_TRUE'),
                  ),
                  const SizedBox(width: 8),
                  _buildCountChip(
                    label: 'CONTRADICTED',
                    count: report.contradictedCount,
                    color: AppTheme.error,
                    isSelected: _selectedFilter == 'CONTRADICTED',
                    onTap: () => _toggleFilter('CONTRADICTED'),
                  ),
                  const SizedBox(width: 8),
                  _buildCountChip(
                    label: 'NOT IN POLICY',
                    count: report.notInPolicyCount,
                    color: const Color(0xFF7C3AED),
                    isSelected: _selectedFilter == 'NOT_IN_POLICY',
                    onTap: () => _toggleFilter('NOT_IN_POLICY'),
                  ),
                  const SizedBox(width: 8),
                  _buildCountChip(
                    label: 'UNCLEAR',
                    count: report.unclearCount,
                    color: AppTheme.textMuted,
                    isSelected: _selectedFilter == 'UNCLEAR',
                    onTap: () => _toggleFilter('UNCLEAR'),
                  ),
                ],
              ),
            ),

            const SizedBox(height: 20),

            // Findings Section Header
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(
                  'Statements Examined (${filteredFindings.length})',
                  style: const TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.w800,
                    color: AppTheme.textPrimary,
                  ),
                ),
                if (_selectedFilter != 'ALL') ...[
                  TextButton(
                    onPressed: () => setState(() => _selectedFilter = 'ALL'),
                    style: TextButton.styleFrom(padding: EdgeInsets.zero),
                    child: const Text('Show All', style: TextStyle(fontSize: 12)),
                  ),
                ],
              ],
            ),

            const SizedBox(height: 10),

            if (filteredFindings.isEmpty) ...[
              GlassCard(
                padding: const EdgeInsets.all(24),
                child: Center(
                  child: Column(
                    children: [
                      const Icon(Icons.search_off_rounded, size: 36, color: AppTheme.textMuted),
                      const SizedBox(height: 10),
                      Text(
                        _selectedFilter == 'ALL'
                            ? 'No promise statements were extracted from this session.'
                            : 'No findings match classification "$_selectedFilter".',
                        style: const TextStyle(fontSize: 13, color: AppTheme.textSecondary),
                      ),
                    ],
                  ),
                ),
              ),
            ] else ...[
              ...filteredFindings.map((finding) => _buildFindingCard(finding)),
            ],

            const SizedBox(height: 28),
          ],
        ),
      ),
    );
  }

  void _toggleFilter(String filter) {
    setState(() {
      _selectedFilter = _selectedFilter == filter ? 'ALL' : filter;
    });
  }

  Widget _buildIntegrityBadge(String? status) {
    final effectiveStatus = status ?? 'VERIFIED';
    Color color;
    String label;
    IconData icon;

    switch (effectiveStatus) {
      case 'VERIFIED':
        color = AppTheme.success;
        label = 'All Claims Grounded';
        icon = Icons.check_circle_rounded;
        break;
      case 'DISCREPANCIES_FOUND':
        color = AppTheme.warning;
        label = 'Discrepancies Found';
        icon = Icons.warning_amber_rounded;
        break;
      case 'MISLEADING_CLAIMS_DETECTED':
        color = AppTheme.error;
        label = 'Misleading Claims';
        icon = Icons.cancel_rounded;
        break;
      case 'NEEDS_REVIEW':
      default:
        color = const Color(0xFFD97706);
        label = 'Under Review';
        icon = Icons.rate_review_rounded;
    }

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.12),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 14, color: color),
          const SizedBox(width: 6),
          Text(
            label,
            style: TextStyle(fontSize: 12, fontWeight: FontWeight.w700, color: color),
          ),
        ],
      ),
    );
  }

  Widget _buildCountChip({
    required String label,
    required int count,
    required Color color,
    required bool isSelected,
    required VoidCallback onTap,
  }) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
        decoration: BoxDecoration(
          color: isSelected ? color : Colors.white,
          borderRadius: BorderRadius.circular(14),
          border: Border.all(
            color: isSelected ? color : AppTheme.borderLight,
            width: isSelected ? 1.5 : 1.0,
          ),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withValues(alpha: 0.02),
              blurRadius: 4,
              offset: const Offset(0, 2),
            ),
          ],
        ),
        child: Row(
          children: [
            Container(
              width: 8,
              height: 8,
              decoration: BoxDecoration(
                color: isSelected ? Colors.white : color,
                shape: BoxShape.circle,
              ),
            ),
            const SizedBox(width: 6),
            Text(
              label,
              style: TextStyle(
                fontSize: 11,
                fontWeight: FontWeight.w700,
                color: isSelected ? Colors.white : AppTheme.textPrimary,
              ),
            ),
            const SizedBox(width: 6),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
              decoration: BoxDecoration(
                color: isSelected
                    ? Colors.white.withValues(alpha: 0.25)
                    : color.withValues(alpha: 0.12),
                borderRadius: BorderRadius.circular(10),
              ),
              child: Text(
                '$count',
                style: TextStyle(
                  fontSize: 11,
                  fontWeight: FontWeight.w800,
                  color: isSelected ? Colors.white : color,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildFindingCard(FindingItemModel finding) {
    Color verdictColor;
    switch (finding.classification) {
      case 'SUPPORTED':
        verdictColor = AppTheme.success;
        break;
      case 'PARTLY_TRUE':
        verdictColor = AppTheme.warning;
        break;
      case 'CONTRADICTED':
        verdictColor = AppTheme.error;
        break;
      case 'NOT_IN_POLICY':
        verdictColor = const Color(0xFF7C3AED);
        break;
      case 'UNCLEAR':
      default:
        verdictColor = AppTheme.textMuted;
    }

    return Padding(
      padding: const EdgeInsets.only(bottom: 12.0),
      child: GlassCard(
        padding: const EdgeInsets.all(18),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Classification & Confidence Header
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                StatusBadge(
                  label: finding.classification.replaceAll('_', ' '),
                  color: verdictColor,
                ),
                Text(
                  '${(finding.confidence * 100).toStringAsFixed(0)}% Confidence',
                  style: const TextStyle(
                    fontSize: 11,
                    fontWeight: FontWeight.w600,
                    color: AppTheme.textMuted,
                  ),
                ),
              ],
            ),

            const SizedBox(height: 12),

            // Stated Promise
            Text(
              finding.promiseText,
              style: const TextStyle(
                fontSize: 15,
                fontWeight: FontWeight.w700,
                color: AppTheme.textPrimary,
              ),
            ),

            const SizedBox(height: 10),

            // Transcript Quote with speaker label
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: AppTheme.backgroundSurface,
                borderRadius: BorderRadius.circular(12),
                border: Border(left: BorderSide(color: verdictColor, width: 3)),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      const Icon(Icons.mic_none_rounded, size: 14, color: AppTheme.textSecondary),
                      const SizedBox(width: 6),
                      Text(
                        finding.speakerLabel != null && finding.speakerLabel!.isNotEmpty
                            ? 'Sales Audio (${finding.speakerLabel}):'
                            : 'Transcript Excerpt:',
                        style: const TextStyle(
                          fontSize: 11,
                          fontWeight: FontWeight.w700,
                          color: AppTheme.textSecondary,
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 4),
                  Text(
                    '"${finding.transcriptQuote}"',
                    style: const TextStyle(
                      fontSize: 12,
                      fontStyle: FontStyle.italic,
                      color: AppTheme.textPrimary,
                      height: 1.35,
                    ),
                  ),
                ],
              ),
            ),

            // Policy Excerpt if supplied by backend
            if (finding.policyExcerpt != null && finding.policyExcerpt!.isNotEmpty) ...[
              const SizedBox(height: 10),
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: AppTheme.gradientSkyBlue.withValues(alpha: 0.06),
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: AppTheme.gradientSkyBlue.withValues(alpha: 0.2)),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        const Icon(Icons.menu_book_rounded, size: 14, color: AppTheme.gradientSkyBlue),
                        const SizedBox(width: 6),
                        Expanded(
                          child: Text(
                            finding.sectionHeading != null
                                ? '${finding.sectionHeading} (p. ${finding.pageNumber ?? 'N/A'})'
                                : 'Contract Clause (p. ${finding.pageNumber ?? 'N/A'}):',
                            style: const TextStyle(
                              fontSize: 11,
                              fontWeight: FontWeight.w700,
                              color: AppTheme.gradientSkyBlue,
                            ),
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 4),
                    Text(
                      finding.policyExcerpt!,
                      style: const TextStyle(
                        fontSize: 12,
                        color: AppTheme.textPrimary,
                        height: 1.35,
                      ),
                    ),
                  ],
                ),
              ),
            ],

            // Explanation
            if (finding.explanation.isNotEmpty) ...[
              const SizedBox(height: 10),
              Text(
                finding.explanation,
                style: const TextStyle(
                  fontSize: 12,
                  color: AppTheme.textSecondary,
                  height: 1.35,
                ),
              ),
            ],

            // Manual Review Required Callout if backend flagged it
            if (finding.reviewRequired) ...[
              const SizedBox(height: 10),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                decoration: BoxDecoration(
                  color: AppTheme.warning.withValues(alpha: 0.1),
                  borderRadius: BorderRadius.circular(10),
                ),
                child: const Row(
                  children: [
                    Icon(Icons.flag_outlined, size: 14, color: AppTheme.warning),
                    SizedBox(width: 6),
                    Expanded(
                      child: Text(
                        'Flagged for compliance review',
                        style: TextStyle(
                          fontSize: 11,
                          fontWeight: FontWeight.w600,
                          color: Color(0xFFB45309),
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }
}
