import 'dart:async';
import 'dart:io';
import 'package:crypto/crypto.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:path_provider/path_provider.dart';
import 'package:record/record.dart';
import '../../../core/theme/app_theme.dart';
import '../../../shared/widgets/glass_card.dart';
import '../providers/agent_provider.dart';

class NewSalesSessionScreen extends ConsumerStatefulWidget {
  const NewSalesSessionScreen({super.key});

  @override
  ConsumerState<NewSalesSessionScreen> createState() => _NewSalesSessionScreenState();
}

class _NewSalesSessionScreenState extends ConsumerState<NewSalesSessionScreen> {
  final _customerIdController = TextEditingController();
  final _consentNotesController = TextEditingController();

  String? _selectedPolicyId;
  String? _selectedRegistrationId;

  // Consent state
  bool _hasAffirmativeConsent = false;

  // Recording state
  late final AudioRecorder _audioRecorder;
  bool _isRecording = false;
  int _recordedSeconds = 0;
  Timer? _timer;
  String? _recordedFilePath;
  int _fileSizeBytes = 0;
  String? _sha256Checksum;

  bool _isSubmitting = false;
  String? _errorMessage;

  @override
  void initState() {
    super.initState();
    _audioRecorder = AudioRecorder();
  }

  @override
  void dispose() {
    _timer?.cancel();
    _audioRecorder.dispose();
    _customerIdController.dispose();
    _consentNotesController.dispose();
    super.dispose();
  }

  Future<void> _startRecording() async {
    if (!_hasAffirmativeConsent) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Affirmative customer consent is mandatory before starting recording.'),
          backgroundColor: AppTheme.error,
        ),
      );
      return;
    }

    try {
      final hasPermission = await _audioRecorder.hasPermission();
      if (!hasPermission) {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(
              content: Text('Microphone permission denied. Please grant microphone access to record.'),
              backgroundColor: AppTheme.error,
            ),
          );
        }
        return;
      }

      final tempDir = await getTemporaryDirectory();
      final path = '${tempDir.path}/sales_session_${DateTime.now().millisecondsSinceEpoch}.m4a';

      await _audioRecorder.start(
        const RecordConfig(encoder: AudioEncoder.aacLc, bitRate: 128000),
        path: path,
      );

      setState(() {
        _isRecording = true;
        _recordedSeconds = 0;
        _recordedFilePath = null;
        _errorMessage = null;
      });

      _timer?.cancel();
      _timer = Timer.periodic(const Duration(seconds: 1), (t) {
        if (mounted) {
          setState(() => _recordedSeconds = t.tick);
        }
      });
    } catch (e) {
      setState(() => _errorMessage = 'Failed to start recording: $e');
    }
  }

  Future<void> _stopRecording() async {
    try {
      _timer?.cancel();
      final path = await _audioRecorder.stop();

      if (path != null) {
        final file = File(path);
        final bytes = await file.readAsBytes();
        final digest = sha256.convert(bytes);

        setState(() {
          _isRecording = false;
          _recordedFilePath = path;
          _fileSizeBytes = bytes.length;
          _sha256Checksum = digest.toString();
        });
      } else {
        setState(() => _isRecording = false);
      }
    } catch (e) {
      setState(() {
        _isRecording = false;
        _errorMessage = 'Error stopping recording: $e';
      });
    }
  }

  Future<void> _cancelRecording() async {
    _timer?.cancel();
    await _audioRecorder.cancel();
    if (_recordedFilePath != null) {
      try {
        final f = File(_recordedFilePath!);
        if (await f.exists()) await f.delete();
      } catch (_) {}
    }
    setState(() {
      _isRecording = false;
      _recordedSeconds = 0;
      _recordedFilePath = null;
      _fileSizeBytes = 0;
      _sha256Checksum = null;
    });
  }

  Future<void> _submitSalesSession() async {
    final customerId = _customerIdController.text.trim();

    if (customerId.isEmpty) {
      setState(() => _errorMessage = 'Please specify or select a valid Customer UUID.');
      return;
    }

    if (!_hasAffirmativeConsent) {
      setState(() => _errorMessage = 'Mandatory customer consent must be explicitly confirmed.');
      return;
    }

    if (_sha256Checksum == null || _fileSizeBytes == 0) {
      setState(() => _errorMessage = 'Please complete the voice recording before creating session.');
      return;
    }

    // Backend max audio limit: 25MB (26214400 bytes)
    if (_fileSizeBytes > 26214400) {
      setState(() => _errorMessage = 'Audio size exceeds 25MB limit. Please re-record a shorter clip.');
      return;
    }

    setState(() {
      _isSubmitting = true;
      _errorMessage = null;
    });

    try {
      final apiService = ref.read(agentApiServiceProvider);
      final session = await apiService.createSalesSession(
        customerId: customerId,
        policyId: _selectedPolicyId,
        registrationId: _selectedRegistrationId,
        audioStorageRef: 'voiceguard/sessions/${DateTime.now().millisecondsSinceEpoch}_sales.m4a',
        audioMimeType: 'audio/m4a',
        audioFileSizeBytes: _fileSizeBytes,
        durationSeconds: _recordedSeconds,
        audioChecksum: _sha256Checksum!,
        customerConsent: _hasAffirmativeConsent,
        consentNotes: _consentNotesController.text.trim().isNotEmpty
            ? _consentNotesController.text.trim()
            : 'Affirmative verbal consent recorded during sales conversation.',
      );

      // Refresh agent sessions list
      ref.read(salesSessionsListProvider.notifier).fetchSessions();

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Sales session created with verified affirmative consent!'),
            backgroundColor: AppTheme.success,
          ),
        );
        context.pushReplacement('/agent/session/${session.id}');
      }
    } catch (e) {
      setState(() {
        _isSubmitting = false;
        _errorMessage = e.toString();
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final policiesAsync = ref.watch(agentPoliciesProvider);
    final registrationsAsync = ref.watch(agentRegistrationsProvider);

    return Scaffold(
      backgroundColor: AppTheme.background,
      appBar: AppBar(
        title: const Text('New Sales Session'),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_ios_new_rounded, size: 20),
          onPressed: () => context.pop(),
        ),
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.symmetric(horizontal: 20.0, vertical: 12.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              if (_errorMessage != null) ...[
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
                        child: Text(
                          _errorMessage!,
                          style: const TextStyle(fontSize: 12, color: AppTheme.error),
                        ),
                      ),
                    ],
                  ),
                ),
              ],

              // 1. Customer & Policy Selection Section
              const Text(
                '1. Customer & Policy Target',
                style: TextStyle(
                  fontSize: 16,
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
                    // Quick pick from existing registrations if available
                    registrationsAsync.when(
                      data: (regs) {
                        if (regs.isEmpty) return const SizedBox.shrink();
                        return Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            const Text(
                              'Pick from Registered Customers:',
                              style: TextStyle(fontSize: 12, fontWeight: FontWeight.w700, color: AppTheme.textSecondary),
                            ),
                            const SizedBox(height: 6),
                            DropdownButtonFormField<String>(
                              isExpanded: true,
                              decoration: const InputDecoration(
                                filled: true,
                                fillColor: Colors.white,
                                contentPadding: EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                                border: OutlineInputBorder(borderRadius: BorderRadius.all(Radius.circular(12)), borderSide: BorderSide(color: AppTheme.borderLight)),
                                enabledBorder: OutlineInputBorder(borderRadius: BorderRadius.all(Radius.circular(12)), borderSide: BorderSide(color: AppTheme.borderLight)),
                              ),
                              hint: const Text('Select a registered customer', style: TextStyle(fontSize: 13)),
                              items: regs.map((r) {
                                return DropdownMenuItem(
                                  value: r.customerId,
                                  child: Text('Cust #${r.customerId.substring(0, 8)} (${r.status})', style: const TextStyle(fontSize: 13)),
                                );
                              }).toList(),
                              onChanged: (val) {
                                if (val != null) {
                                  _customerIdController.text = val;
                                  final match = regs.firstWhere((r) => r.customerId == val);
                                  setState(() {
                                    _selectedPolicyId = match.policyId;
                                    _selectedRegistrationId = match.id;
                                  });
                                }
                              },
                            ),
                            const SizedBox(height: 14),
                            const Divider(color: AppTheme.borderLight),
                            const SizedBox(height: 10),
                          ],
                        );
                      },
                      loading: () => const SizedBox.shrink(),
                      error: (_, __) => const SizedBox.shrink(),
                    ),

                    const Text(
                      'Customer UUID *',
                      style: TextStyle(fontSize: 12, fontWeight: FontWeight.w700, color: AppTheme.textSecondary),
                    ),
                    const SizedBox(height: 6),
                    TextField(
                      controller: _customerIdController,
                      decoration: const InputDecoration(
                        hintText: 'Enter customer UUID (e.g. 550e8400-...)',
                        filled: true,
                        fillColor: Colors.white,
                        border: OutlineInputBorder(borderRadius: BorderRadius.all(Radius.circular(12)), borderSide: BorderSide(color: AppTheme.borderLight)),
                        enabledBorder: OutlineInputBorder(borderRadius: BorderRadius.all(Radius.circular(12)), borderSide: BorderSide(color: AppTheme.borderLight)),
                      ),
                    ),

                    const SizedBox(height: 14),

                    const Text(
                      'Target Policy Scheme',
                      style: TextStyle(fontSize: 12, fontWeight: FontWeight.w700, color: AppTheme.textSecondary),
                    ),
                    const SizedBox(height: 6),
                    policiesAsync.when(
                      data: (policies) => DropdownButtonFormField<String>(
                        key: ValueKey(_selectedPolicyId),
                        isExpanded: true,
                        initialValue: _selectedPolicyId,
                        decoration: const InputDecoration(
                          filled: true,
                          fillColor: Colors.white,
                          contentPadding: EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                          border: OutlineInputBorder(borderRadius: BorderRadius.all(Radius.circular(12)), borderSide: BorderSide(color: AppTheme.borderLight)),
                          enabledBorder: OutlineInputBorder(borderRadius: BorderRadius.all(Radius.circular(12)), borderSide: BorderSide(color: AppTheme.borderLight)),
                        ),
                        hint: const Text('Select policy being discussed', style: TextStyle(fontSize: 13)),
                        items: policies.map((p) {
                          return DropdownMenuItem(
                            value: p.id,
                            child: Text('${p.policyName} (${p.category})', style: const TextStyle(fontSize: 13)),
                          );
                        }).toList(),
                        onChanged: (val) => setState(() => _selectedPolicyId = val),
                      ),
                      loading: () => const LinearProgressIndicator(),
                      error: (_, __) => const Text('Failed to load published policies', style: TextStyle(color: AppTheme.error, fontSize: 12)),
                    ),
                  ],
                ),
              ),

              const SizedBox(height: 20),

              // 2. Affirmative Customer Consent Notice
              const Text(
                '2. Mandatory Customer Recording Consent',
                style: TextStyle(
                  fontSize: 16,
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
                    Container(
                      padding: const EdgeInsets.all(14),
                      decoration: BoxDecoration(
                        color: AppTheme.darkTeal.withValues(alpha: 0.08),
                        borderRadius: BorderRadius.circular(14),
                        border: Border.all(color: AppTheme.darkTeal.withValues(alpha: 0.15)),
                      ),
                      child: const Row(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Icon(Icons.gavel_rounded, color: AppTheme.darkTeal, size: 20),
                          SizedBox(width: 10),
                          Expanded(
                            child: Text(
                              'VoiceGuard Statutory Disclosure: '
                              '"This conversation is being recorded with your affirmative consent for transparency and policy promise verification. Verbatim sales statements will be compared against official policy clauses."',
                              style: TextStyle(
                                fontSize: 11,
                                color: Color(0xFF132A33),
                                height: 1.4,
                                fontStyle: FontStyle.italic,
                              ),
                            ),
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(height: 14),

                    CheckboxListTile(
                      contentPadding: EdgeInsets.zero,
                      value: _hasAffirmativeConsent,
                      activeColor: AppTheme.darkTeal,
                      title: const Text(
                        'I confirm customer gave affirmative explicit consent to voice recording.',
                        style: TextStyle(fontSize: 13, fontWeight: FontWeight.w700, color: AppTheme.textPrimary),
                      ),
                      subtitle: const Text(
                        'Mandatory requirement enforced by backend before transcription.',
                        style: TextStyle(fontSize: 11, color: AppTheme.textSecondary),
                      ),
                      onChanged: (val) {
                        setState(() => _hasAffirmativeConsent = val ?? false);
                      },
                    ),

                    const SizedBox(height: 10),

                    const Text(
                      'Consent Notes (Optional):',
                      style: TextStyle(fontSize: 12, fontWeight: FontWeight.w700, color: AppTheme.textSecondary),
                    ),
                    const SizedBox(height: 6),
                    TextField(
                      controller: _consentNotesController,
                      maxLines: 2,
                      decoration: const InputDecoration(
                        hintText: 'e.g. Customer stated "Yes, I agree to be recorded" at start of call.',
                        filled: true,
                        fillColor: Colors.white,
                        border: OutlineInputBorder(borderRadius: BorderRadius.all(Radius.circular(12)), borderSide: BorderSide(color: AppTheme.borderLight)),
                        enabledBorder: OutlineInputBorder(borderRadius: BorderRadius.all(Radius.circular(12)), borderSide: BorderSide(color: AppTheme.borderLight)),
                      ),
                    ),
                  ],
                ),
              ),

              const SizedBox(height: 20),

              // 3. Audio Recording Controller
              const Text(
                '3. Voice Session Recording',
                style: TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.w800,
                  color: AppTheme.textPrimary,
                  letterSpacing: -0.3,
                ),
              ),
              const SizedBox(height: 10),

              GlassCard(
                padding: const EdgeInsets.all(22),
                child: Column(
                  children: [
                    // Timer & Status Icon
                    Row(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        if (_isRecording) ...[
                          Container(
                            width: 12,
                            height: 12,
                            decoration: const BoxDecoration(
                              color: AppTheme.error,
                              shape: BoxShape.circle,
                            ),
                          ),
                          const SizedBox(width: 10),
                        ],
                        Text(
                          _formatDuration(_recordedSeconds),
                          style: TextStyle(
                            fontSize: 32,
                            fontWeight: FontWeight.w900,
                            color: _isRecording ? AppTheme.error : AppTheme.textPrimary,
                            letterSpacing: 1.0,
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 6),
                    Text(
                      _isRecording
                          ? 'Recording sales audio with explicit consent...'
                          : _recordedFilePath != null
                              ? 'Recording captured (${(_fileSizeBytes / 1024).toStringAsFixed(1)} KB)'
                              : 'Ready to record conversation',
                      style: TextStyle(
                        fontSize: 12,
                        fontWeight: FontWeight.w600,
                        color: _isRecording ? AppTheme.error : AppTheme.textSecondary,
                      ),
                    ),

                    if (_sha256Checksum != null) ...[
                      const SizedBox(height: 12),
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                        decoration: BoxDecoration(
                          color: AppTheme.backgroundSurface,
                          borderRadius: BorderRadius.circular(10),
                        ),
                        child: Text(
                          'SHA-256: ${_sha256Checksum!.substring(0, 24)}...',
                          style: const TextStyle(fontSize: 10, fontFamily: 'monospace', color: AppTheme.textMuted),
                        ),
                      ),
                    ],

                    const SizedBox(height: 20),

                    // Controls
                    if (_isRecording) ...[
                      Row(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          OutlinedButton.icon(
                            onPressed: _cancelRecording,
                            icon: const Icon(Icons.close_rounded, color: AppTheme.error),
                            label: const Text('Cancel', style: TextStyle(color: AppTheme.error)),
                            style: OutlinedButton.styleFrom(
                              side: const BorderSide(color: AppTheme.error),
                              padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 12),
                              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
                            ),
                          ),
                          const SizedBox(width: 16),
                          ElevatedButton.icon(
                            onPressed: _stopRecording,
                            icon: const Icon(Icons.stop_rounded),
                            label: const Text('Stop Recording'),
                            style: ElevatedButton.styleFrom(
                              backgroundColor: AppTheme.error,
                              foregroundColor: Colors.white,
                              padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
                              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
                            ),
                          ),
                        ],
                      ),
                    ] else ...[
                      Row(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          ElevatedButton.icon(
                            onPressed: _hasAffirmativeConsent ? _startRecording : null,
                            icon: Icon(_recordedFilePath != null ? Icons.replay_rounded : Icons.mic_rounded),
                            label: Text(_recordedFilePath != null ? 'Re-Record Audio' : 'Start Recording'),
                            style: ElevatedButton.styleFrom(
                              backgroundColor: _hasAffirmativeConsent ? AppTheme.darkTeal : AppTheme.textMuted,
                              foregroundColor: Colors.white,
                              padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
                              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
                            ),
                          ),
                        ],
                      ),
                    ],
                  ],
                ),
              ),

              const SizedBox(height: 28),

              // Final Submit Button
              SizedBox(
                width: double.infinity,
                child: ElevatedButton.icon(
                  onPressed: (_isSubmitting || _isRecording || _sha256Checksum == null)
                      ? null
                      : _submitSalesSession,
                  icon: _isSubmitting
                      ? const SizedBox(
                          width: 18,
                          height: 18,
                          child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2),
                        )
                      : const Icon(Icons.cloud_upload_rounded),
                  label: Text(
                    _isSubmitting ? 'Creating & Verifying...' : 'Submit Session to VoiceGuard',
                    style: const TextStyle(fontSize: 15, fontWeight: FontWeight.w700),
                  ),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: AppTheme.darkTeal,
                    foregroundColor: Colors.white,
                    padding: const EdgeInsets.symmetric(vertical: 16),
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(18)),
                  ),
                ),
              ),

              const SizedBox(height: 36),
            ],
          ),
        ),
      ),
    );
  }

  String _formatDuration(int seconds) {
    final m = seconds ~/ 60;
    final s = seconds % 60;
    return '${m.toString().padLeft(2, '0')}:${s.toString().padLeft(2, '0')}';
  }
}
