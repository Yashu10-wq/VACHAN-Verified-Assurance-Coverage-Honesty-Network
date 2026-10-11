import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../core/theme/app_theme.dart';
import '../../../shared/widgets/glass_card.dart';
import '../../../shared/widgets/status_badge.dart';
import '../models/sales_session_model.dart';
import '../providers/agent_provider.dart';

class SalesSessionDetailScreen extends ConsumerStatefulWidget {
  final String sessionId;

  const SalesSessionDetailScreen({super.key, required this.sessionId});

  @override
  ConsumerState<SalesSessionDetailScreen> createState() => _SalesSessionDetailScreenState();
}

class _SalesSessionDetailScreenState extends ConsumerState<SalesSessionDetailScreen> {
  bool _isTranscribing = false;
  bool _isVerifying = false;
  String? _actionError;

  Future<void> _triggerTranscription() async {
    setState(() {
      _isTranscribing = true;
      _actionError = null;
    });

    try {
      final apiService = ref.read(agentApiServiceProvider);
      await apiService.startTranscription(widget.sessionId);

      ref.invalidate(sessionDetailProvider(widget.sessionId));
      ref.invalidate(sessionTranscriptProvider(widget.sessionId));
      ref.read(salesSessionsListProvider.notifier).fetchSessions();

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('ElevenLabs transcription job executed successfully!'),
            backgroundColor: AppTheme.success,
          ),
        );
      }
    } catch (e) {
      setState(() => _actionError = e.toString());
    } finally {
      if (mounted) setState(() => _isTranscribing = false);
    }
  }

  Future<void> _triggerPolicyVerification() async {
    setState(() {
      _isVerifying = true;
      _actionError = null;
    });

    try {
      final apiService = ref.read(agentApiServiceProvider);
      final report = await apiService.verifySalesSession(widget.sessionId);

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Gemini Policy-Promise Verification report generated!'),
            backgroundColor: AppTheme.success,
          ),
        );
        context.push('/verification-report/${report.id}');
      }
    } catch (e) {
      setState(() => _actionError = e.toString());
    } finally {
      if (mounted) setState(() => _isVerifying = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final sessionAsync = ref.watch(sessionDetailProvider(widget.sessionId));
    final transcriptAsync = ref.watch(sessionTranscriptProvider(widget.sessionId));

    return Scaffold(
      backgroundColor: AppTheme.background,
      appBar: AppBar(
        title: const Text('Sales Session Audit'),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_ios_new_rounded, size: 20),
          onPressed: () => context.pop(),
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh_rounded),
            onPressed: () {
              ref.invalidate(sessionDetailProvider(widget.sessionId));
              ref.invalidate(sessionTranscriptProvider(widget.sessionId));
            },
          ),
        ],
      ),
      body: SafeArea(
        child: sessionAsync.when(
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
                  const SizedBox(height: 12),
                  Text(err.toString(), textAlign: TextAlign.center),
                  const SizedBox(height: 16),
                  ElevatedButton(
                    onPressed: () => ref.refresh(sessionDetailProvider(widget.sessionId)),
                    child: const Text('Retry'),
                  ),
                ],
              ),
            ),
          ),
          data: (session) => _buildSessionContent(context, session, transcriptAsync),
        ),
      ),
    );
  }

  Widget _buildSessionContent(
    BuildContext context,
    SalesSessionModel session,
    AsyncValue<SalesTranscriptModel?> transcriptAsync,
  ) {
    return SingleChildScrollView(
      padding: const EdgeInsets.symmetric(horizontal: 20.0, vertical: 12.0),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (_actionError != null) ...[
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
                    child: Text(_actionError!, style: const TextStyle(fontSize: 12, color: AppTheme.error)),
                  ),
                ],
              ),
            ),
          ],

          // 1. Session Overview GlassCard
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
                        color: AppTheme.darkTeal.withValues(alpha: 0.1),
                        borderRadius: BorderRadius.circular(10),
                      ),
                      child: const Text(
                        'Voice Conversation Session',
                        style: TextStyle(fontSize: 11, fontWeight: FontWeight.w700, color: AppTheme.darkTeal),
                      ),
                    ),
                    StatusBadge.fromStatus(session.status),
                  ],
                ),
                const SizedBox(height: 14),
                Text(
                  'Session #${session.id.substring(0, session.id.length > 8 ? 8 : session.id.length)}',
                  style: const TextStyle(
                    fontSize: 20,
                    fontWeight: FontWeight.w800,
                    color: AppTheme.textPrimary,
                    letterSpacing: -0.3,
                  ),
                ),
                const SizedBox(height: 6),
                Text(
                  'Customer ID: ${session.customerId}',
                  style: const TextStyle(fontSize: 12, color: AppTheme.textSecondary),
                ),
                if (session.policyId != null) ...[
                  const SizedBox(height: 2),
                  Text(
                    'Policy ID: ${session.policyId}',
                    style: const TextStyle(fontSize: 12, color: AppTheme.textSecondary),
                  ),
                ],
                const Divider(color: AppTheme.borderLight, height: 24),
                // Audio & Checksum details
                Row(
                  children: [
                    const Icon(Icons.audiotrack_rounded, size: 16, color: AppTheme.textSecondary),
                    const SizedBox(width: 6),
                    Text(
                      '${session.audioMimeType} • ${(session.audioFileSizeBytes / 1024).toStringAsFixed(1)} KB ${session.durationSeconds != null ? '• ${session.durationSeconds}s' : ''}',
                      style: const TextStyle(fontSize: 12, color: AppTheme.textSecondary, fontWeight: FontWeight.w600),
                    ),
                  ],
                ),
                const SizedBox(height: 8),
                Text(
                  'SHA-256 Checksum: ${session.audioChecksum}',
                  style: const TextStyle(fontSize: 10, fontFamily: 'monospace', color: AppTheme.textMuted),
                ),
              ],
            ),
          ),

          const SizedBox(height: 16),

          // 2. Affirmative Customer Consent Record
          GlassCard(
            padding: const EdgeInsets.all(18),
            child: Row(
              children: [
                Container(
                  width: 42,
                  height: 42,
                  decoration: BoxDecoration(
                    color: (session.customerConsent ? AppTheme.success : AppTheme.error).withValues(alpha: 0.12),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Icon(
                    session.customerConsent ? Icons.verified_user_rounded : Icons.gpp_bad_rounded,
                    color: session.customerConsent ? AppTheme.success : AppTheme.error,
                    size: 22,
                  ),
                ),
                const SizedBox(width: 14),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        session.customerConsent ? 'Affirmative Consent Verified' : 'Customer Consent Missing',
                        style: TextStyle(
                          fontSize: 13,
                          fontWeight: FontWeight.w800,
                          color: session.customerConsent ? AppTheme.success : AppTheme.error,
                        ),
                      ),
                      const SizedBox(height: 2),
                      Text(
                        session.consentNotes ?? 'Explicit consent registered at session creation.',
                        style: const TextStyle(fontSize: 11, color: AppTheme.textSecondary),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),

          const SizedBox(height: 20),

          // 3. ElevenLabs Transcription Section
          const Text(
            'Speech-to-Text Transcription',
            style: TextStyle(
              fontSize: 17,
              fontWeight: FontWeight.w800,
              color: AppTheme.textPrimary,
              letterSpacing: -0.3,
            ),
          ),
          const SizedBox(height: 10),

          if (!session.isCompleted) ...[
            GlassCard(
              padding: const EdgeInsets.all(20),
              child: Column(
                children: [
                  const Icon(Icons.transcribe_rounded, size: 36, color: AppTheme.textMuted),
                  const SizedBox(height: 10),
                  const Text(
                    'Audio Transcription Pending',
                    style: TextStyle(fontSize: 15, fontWeight: FontWeight.w700, color: AppTheme.textPrimary),
                  ),
                  const SizedBox(height: 4),
                  const Text(
                    'Process conversation audio through ElevenLabs Scribe STT engine.',
                    textAlign: TextAlign.center,
                    style: TextStyle(fontSize: 12, color: AppTheme.textSecondary),
                  ),
                  const SizedBox(height: 16),
                  ElevatedButton.icon(
                    onPressed: _isTranscribing ? null : _triggerTranscription,
                    icon: _isTranscribing
                        ? const SizedBox(
                            width: 16,
                            height: 16,
                            child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2),
                          )
                        : const Icon(Icons.play_arrow_rounded),
                    label: Text(_isTranscribing ? 'Processing Audio...' : 'Execute ElevenLabs Transcription'),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: AppTheme.darkTeal,
                      foregroundColor: Colors.white,
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
                    ),
                  ),
                ],
              ),
            ),
          ] else ...[
            // Render Transcript & Diarization
            transcriptAsync.when(
              loading: () => const LinearProgressIndicator(),
              error: (err, _) => Text('Error loading transcript: $err'),
              data: (transcript) {
                if (transcript == null || transcript.transcript == null) {
                  return const Text('Transcript processing complete.');
                }

                return Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    // Transcript Metadata
                    GlassCard(
                      padding: const EdgeInsets.all(16),
                      child: Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Row(
                            children: [
                              const Icon(Icons.language_rounded, size: 16, color: AppTheme.gradientSkyBlue),
                              const SizedBox(width: 6),
                              Text(
                                'Language: ${transcript.detectedLanguage?.toUpperCase() ?? 'ORIGINAL'}',
                                style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w700, color: AppTheme.textPrimary),
                              ),
                            ],
                          ),
                          Text(
                            transcript.providerModel ?? 'scribe_v2',
                            style: const TextStyle(fontSize: 11, color: AppTheme.textMuted),
                          ),
                        ],
                      ),
                    ),

                    const SizedBox(height: 12),

                    // Verbatim Speech Turns / Speaker Diarization
                    if (transcript.speakerDiarization.isNotEmpty) ...[
                      const Text(
                        'Speaker Diarization:',
                        style: TextStyle(fontSize: 13, fontWeight: FontWeight.w700, color: AppTheme.textSecondary),
                      ),
                      const SizedBox(height: 8),
                      ...transcript.speakerDiarization.map((turn) {
                        final speaker = turn['speaker'] as String? ?? 'Speaker';
                        final text = turn['text'] as String? ?? '';
                        final isAgent = speaker.toLowerCase().contains('agent') || speaker == 'speaker_0';

                        return Container(
                          margin: const EdgeInsets.only(bottom: 8),
                          padding: const EdgeInsets.all(12),
                          decoration: BoxDecoration(
                            color: isAgent ? Colors.white : AppTheme.backgroundSurface,
                            borderRadius: BorderRadius.circular(14),
                            border: Border.all(
                              color: isAgent ? AppTheme.gradientSkyBlue.withValues(alpha: 0.3) : AppTheme.borderLight,
                            ),
                          ),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Row(
                                children: [
                                  Icon(
                                    isAgent ? Icons.support_agent_rounded : Icons.person_rounded,
                                    size: 14,
                                    color: isAgent ? AppTheme.gradientSkyBlue : AppTheme.textSecondary,
                                  ),
                                  const SizedBox(width: 6),
                                  Text(
                                    isAgent ? 'Insurance Agent' : 'Customer',
                                    style: TextStyle(
                                      fontSize: 11,
                                      fontWeight: FontWeight.w800,
                                      color: isAgent ? AppTheme.gradientSkyBlue : AppTheme.textPrimary,
                                    ),
                                  ),
                                ],
                              ),
                              const SizedBox(height: 4),
                              Text(
                                text,
                                style: const TextStyle(fontSize: 12, color: AppTheme.textPrimary, height: 1.35),
                              ),
                            ],
                          ),
                        );
                      }),
                    ] else ...[
                      // Full transcript fallback
                      GlassCard(
                        padding: const EdgeInsets.all(16),
                        child: Text(
                          transcript.transcript!,
                          style: const TextStyle(fontSize: 13, color: AppTheme.textPrimary, height: 1.4),
                        ),
                      ),
                    ],
                  ],
                );
              },
            ),
          ],

          const SizedBox(height: 24),

          // 4. Gemini Policy-Promise Verification Section
          if (session.isCompleted) ...[
            const Text(
              'Policy-Promise AI Verification',
              style: TextStyle(
                fontSize: 17,
                fontWeight: FontWeight.w800,
                color: AppTheme.textPrimary,
                letterSpacing: -0.3,
              ),
            ),
            const SizedBox(height: 10),

            GlassCard(
              padding: const EdgeInsets.all(20),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Row(
                    children: [
                      Icon(Icons.fact_check_rounded, color: AppTheme.darkTeal, size: 24),
                      SizedBox(width: 12),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              'Gemini Clause Verification',
                              style: TextStyle(fontSize: 15, fontWeight: FontWeight.w800, color: AppTheme.textPrimary),
                            ),
                            SizedBox(height: 2),
                            Text(
                              'Ground verbatim sales promises against registered underwriting terms.',
                              style: TextStyle(fontSize: 11, color: AppTheme.textSecondary),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 16),
                  SizedBox(
                    width: double.infinity,
                    child: ElevatedButton.icon(
                      onPressed: _isVerifying ? null : _triggerPolicyVerification,
                      icon: _isVerifying
                          ? const SizedBox(
                              width: 16,
                              height: 16,
                              child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2),
                            )
                          : const Icon(Icons.auto_awesome_rounded),
                      label: Text(_isVerifying ? 'Analyzing Promises...' : 'Run Gemini Promise Verification'),
                      style: ElevatedButton.styleFrom(
                        backgroundColor: AppTheme.darkTeal,
                        foregroundColor: Colors.white,
                        padding: const EdgeInsets.symmetric(vertical: 14),
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ],

          const SizedBox(height: 36),
        ],
      ),
    );
  }
}
