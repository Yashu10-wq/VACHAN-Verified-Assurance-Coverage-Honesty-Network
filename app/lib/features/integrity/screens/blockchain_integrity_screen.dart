import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/theme/app_theme.dart';
import '../../../shared/widgets/glass_card.dart';
import '../../../shared/widgets/status_badge.dart';
import '../../auth/models/user_model.dart';
import '../../auth/providers/auth_provider.dart';
import '../models/blockchain_status_model.dart';
import '../providers/integrity_provider.dart';

class BlockchainIntegrityScreen extends ConsumerStatefulWidget {
  final String? initialEventId;

  const BlockchainIntegrityScreen({super.key, this.initialEventId});

  @override
  ConsumerState<BlockchainIntegrityScreen> createState() => _BlockchainIntegrityScreenState();
}

class _BlockchainIntegrityScreenState extends ConsumerState<BlockchainIntegrityScreen> {
  late final TextEditingController _eventIdController;
  String? _inspectedEventId;
  bool _isAnchoring = false;
  String? _actionMessage;

  @override
  void initState() {
    super.initState();
    _eventIdController = TextEditingController(text: widget.initialEventId ?? '');
    _inspectedEventId = widget.initialEventId;
  }

  @override
  void dispose() {
    _eventIdController.dispose();
    super.dispose();
  }

  Future<void> _triggerAnchoring() async {
    setState(() {
      _isAnchoring = true;
      _actionMessage = null;
    });

    try {
      final api = ref.read(integrityApiServiceProvider);
      final res = await api.anchorPendingBatches();
      ref.invalidate(blockchainStatusProvider);

      if (mounted) {
        setState(() {
          _actionMessage = res['message']?.toString() ?? 'Anchoring batch created successfully.';
        });
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(_actionMessage!),
            backgroundColor: AppTheme.success,
          ),
        );
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _actionMessage = 'Anchoring error: $e';
        });
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(_actionMessage!),
            backgroundColor: AppTheme.error,
          ),
        );
      }
    } finally {
      if (mounted) setState(() => _isAnchoring = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final statusAsync = ref.watch(blockchainStatusProvider);
    final authState = ref.watch(authProvider);
    final isAuthority = authState.user?.role == UserRole.approvalAuthority;

    return Scaffold(
      backgroundColor: AppTheme.background,
      appBar: AppBar(
        title: const Text('Blockchain Audit Integrity'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh_rounded),
            onPressed: () {
              ref.invalidate(blockchainStatusProvider);
              if (_inspectedEventId != null) {
                ref.invalidate(auditEventVerificationProvider(_inspectedEventId!));
                ref.invalidate(auditEventProofProvider(_inspectedEventId!));
              }
            },
          ),
        ],
      ),
      body: SafeArea(
        child: RefreshIndicator(
          color: AppTheme.gradientSkyBlue,
          onRefresh: () async {
            ref.invalidate(blockchainStatusProvider);
            if (_inspectedEventId != null) {
              ref.invalidate(auditEventVerificationProvider(_inspectedEventId!));
              ref.invalidate(auditEventProofProvider(_inspectedEventId!));
            }
          },
          child: SingleChildScrollView(
            physics: const AlwaysScrollableScrollPhysics(),
            padding: const EdgeInsets.symmetric(horizontal: 20.0, vertical: 14.0),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // 1. Blockchain Network Status Card
                statusAsync.when(
                  loading: () => const Padding(
                    padding: EdgeInsets.symmetric(vertical: 20),
                    child: Center(
                      child: CircularProgressIndicator(valueColor: AlwaysStoppedAnimation<Color>(AppTheme.gradientSkyBlue)),
                    ),
                  ),
                  error: (err, _) => GlassCard(
                    padding: const EdgeInsets.all(18),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Row(
                          children: [
                            Icon(Icons.cloud_off_rounded, color: AppTheme.error, size: 22),
                            SizedBox(width: 10),
                            Text(
                              'Blockchain Node Offline',
                              style: TextStyle(fontSize: 15, fontWeight: FontWeight.w800, color: AppTheme.error),
                            ),
                          ],
                        ),
                        const SizedBox(height: 8),
                        const Text(
                          'Unable to reach blockchain RPC node. Anchoring commitments are preserved in local hash-chain storage and will resume when connectivity is restored.',
                          style: TextStyle(fontSize: 12, color: AppTheme.textSecondary, height: 1.35),
                        ),
                        const SizedBox(height: 12),
                        ElevatedButton.icon(
                          onPressed: () => ref.invalidate(blockchainStatusProvider),
                          icon: const Icon(Icons.refresh_rounded, size: 16),
                          label: const Text('Retry Connection'),
                          style: ElevatedButton.styleFrom(backgroundColor: AppTheme.darkTeal),
                        ),
                      ],
                    ),
                  ),
                  data: (status) => _buildNetworkCard(status, isAuthority),
                ),

                const SizedBox(height: 20),

                // 2. Audit Event Hash-Chain Inspector Section
                const Text(
                  'Audit Event Hash Verification',
                  style: TextStyle(fontSize: 16, fontWeight: FontWeight.w800, color: AppTheme.textPrimary, letterSpacing: -0.3),
                ),
                const SizedBox(height: 6),
                const Text(
                  'Verify SHA-256 cryptographic sequence linkages and Merkle inclusion proofs for statutory audit records.',
                  style: TextStyle(fontSize: 12, color: AppTheme.textSecondary),
                ),
                const SizedBox(height: 12),

                GlassCard(
                  padding: const EdgeInsets.all(18),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text(
                        'Audit Event UUID *',
                        style: TextStyle(fontSize: 12, fontWeight: FontWeight.w700, color: AppTheme.textSecondary),
                      ),
                      const SizedBox(height: 6),
                      Row(
                        children: [
                          Expanded(
                            child: TextField(
                              controller: _eventIdController,
                              style: const TextStyle(fontSize: 13, fontFamily: 'monospace'),
                              decoration: const InputDecoration(
                                hintText: 'Enter audit event UUID...',
                                filled: true,
                                fillColor: Colors.white,
                                contentPadding: EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                                border: OutlineInputBorder(borderRadius: BorderRadius.all(Radius.circular(12)), borderSide: BorderSide(color: AppTheme.borderLight)),
                                enabledBorder: OutlineInputBorder(borderRadius: BorderRadius.all(Radius.circular(12)), borderSide: BorderSide(color: AppTheme.borderLight)),
                              ),
                            ),
                          ),
                          const SizedBox(width: 10),
                          ElevatedButton(
                            onPressed: () {
                              final text = _eventIdController.text.trim();
                              if (text.isNotEmpty) {
                                setState(() => _inspectedEventId = text);
                              }
                            },
                            style: ElevatedButton.styleFrom(
                              backgroundColor: AppTheme.darkTeal,
                              foregroundColor: Colors.white,
                              padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 14),
                              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                            ),
                            child: const Text('Verify', style: TextStyle(fontWeight: FontWeight.w700)),
                          ),
                        ],
                      ),
                    ],
                  ),
                ),

                const SizedBox(height: 18),

                // 3. Inspected Event Verification Result
                if (_inspectedEventId != null && _inspectedEventId!.isNotEmpty) ...[
                  _buildEventVerificationView(_inspectedEventId!),
                ],
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildNetworkCard(BlockchainStatusModel status, bool isAuthority) {
    return GlassCard(
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Row(
                children: [
                  Container(
                    width: 44,
                    height: 44,
                    decoration: BoxDecoration(
                      gradient: AppTheme.cyanTileGradient,
                      borderRadius: BorderRadius.circular(14),
                    ),
                    child: const Center(
                      child: Icon(Icons.hub_rounded, color: Colors.white, size: 24),
                    ),
                  ),
                  const SizedBox(width: 12),
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text(
                        'Audit Anchor Smart Contract',
                        style: TextStyle(fontSize: 15, fontWeight: FontWeight.w800, color: AppTheme.textPrimary),
                      ),
                      const SizedBox(height: 2),
                      Text(
                        status.isNodeOnline ? 'Hardhat Node Connected' : 'Node Disconnected',
                        style: TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: status.isNodeOnline ? AppTheme.success : AppTheme.error),
                      ),
                    ],
                  ),
                ],
              ),
              StatusBadge(
                label: status.status,
                color: status.isNodeOnline ? AppTheme.success : AppTheme.error,
              ),
            ],
          ),

          const SizedBox(height: 16),
          const Divider(color: AppTheme.borderLight),
          const SizedBox(height: 12),

          // Details Grid
          _buildInfoRow('Configured Chain ID', '${status.configuredChainId}'),
          if (status.blockNumber != null) _buildInfoRow('Current Block Number', '#${status.blockNumber}'),
          if (status.contractAddress != null && status.contractAddress!.isNotEmpty)
            _buildInfoRow('Contract Address', '${status.contractAddress!.substring(0, 10)}...${status.contractAddress!.substring(status.contractAddress!.length - 6)}'),
          _buildInfoRow('Contract State', status.contractDeployed ? 'DEPLOYED & ACTIVE' : 'NOT DEPLOYED'),

          const SizedBox(height: 16),

          // Metric Counters
          Row(
            children: [
              Expanded(
                child: _buildCountTile(
                  label: 'Anchored',
                  count: status.anchoredEvents,
                  color: AppTheme.success,
                ),
              ),
              const SizedBox(width: 8),
              Expanded(
                child: _buildCountTile(
                  label: 'Batched',
                  count: status.batchedEvents,
                  color: AppTheme.gradientSkyBlue,
                ),
              ),
              const SizedBox(width: 8),
              Expanded(
                child: _buildCountTile(
                  label: 'Pending',
                  count: status.pendingEvents,
                  color: AppTheme.warning,
                ),
              ),
              const SizedBox(width: 8),
              Expanded(
                child: _buildCountTile(
                  label: 'Total Chained',
                  count: status.totalEvents,
                  color: AppTheme.darkTeal,
                ),
              ),
            ],
          ),

          if (isAuthority) ...[
            const SizedBox(height: 16),
            SizedBox(
              width: double.infinity,
              child: ElevatedButton.icon(
                onPressed: _isAnchoring ? null : _triggerAnchoring,
                icon: _isAnchoring
                    ? const SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                    : const Icon(Icons.anchor_rounded),
                label: const Text('Anchor Pending Batches On-Chain'),
                style: ElevatedButton.styleFrom(
                  backgroundColor: AppTheme.darkTeal,
                  foregroundColor: Colors.white,
                  padding: const EdgeInsets.symmetric(vertical: 12),
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                ),
              ),
            ),
          ],
        ],
      ),
    );
  }

  Widget _buildCountTile({required String label, required int count, required Color color}) {
    return Container(
      padding: const EdgeInsets.symmetric(vertical: 10, horizontal: 8),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.08),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: color.withValues(alpha: 0.2)),
      ),
      child: Column(
        children: [
          Text(
            '$count',
            style: TextStyle(fontSize: 16, fontWeight: FontWeight.w900, color: color),
          ),
          const SizedBox(height: 2),
          Text(
            label,
            style: TextStyle(fontSize: 10, fontWeight: FontWeight.w700, color: color),
            textAlign: TextAlign.center,
          ),
        ],
      ),
    );
  }

  Widget _buildInfoRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 6.0),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label, style: const TextStyle(fontSize: 12, color: AppTheme.textSecondary)),
          Text(value, style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w700, color: AppTheme.textPrimary, fontFamily: 'monospace')),
        ],
      ),
    );
  }

  Widget _buildEventVerificationView(String eventId) {
    final verificationAsync = ref.watch(auditEventVerificationProvider(eventId));
    final proofAsync = ref.watch(auditEventProofProvider(eventId));

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text(
          'Verification Analysis',
          style: TextStyle(fontSize: 16, fontWeight: FontWeight.w800, color: AppTheme.textPrimary),
        ),
        const SizedBox(height: 8),

        verificationAsync.when(
          loading: () => const LinearProgressIndicator(),
          error: (err, _) => GlassCard(
            padding: const EdgeInsets.all(16),
            child: Row(
              children: [
                const Icon(Icons.error_outline_rounded, color: AppTheme.error, size: 20),
                const SizedBox(width: 10),
                Expanded(
                  child: Text(
                    'Verification error: $err',
                    style: const TextStyle(fontSize: 12, color: AppTheme.error),
                  ),
                ),
              ],
            ),
          ),
          data: (ver) {
            Color statusColor;
            switch (ver.outcome) {
              case 'VALID':
                statusColor = AppTheme.success;
                break;
              case 'ANCHOR_PENDING':
                statusColor = AppTheme.warning;
                break;
              case 'HASH_MISMATCH':
              case 'PREVIOUS_HASH_MISMATCH':
                statusColor = AppTheme.error;
                break;
              default:
                statusColor = AppTheme.textMuted;
            }

            return GlassCard(
              padding: const EdgeInsets.all(18),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Row(
                        children: [
                          Icon(
                            ver.isValid ? Icons.verified_rounded : Icons.warning_rounded,
                            color: statusColor,
                            size: 22,
                          ),
                          const SizedBox(width: 8),
                          Text(
                            ver.outcome,
                            style: TextStyle(fontSize: 15, fontWeight: FontWeight.w900, color: statusColor),
                          ),
                        ],
                      ),
                      if (ver.onChainVerified)
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                          decoration: BoxDecoration(
                            color: AppTheme.success.withValues(alpha: 0.12),
                            borderRadius: BorderRadius.circular(8),
                          ),
                          child: const Row(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              Icon(Icons.link_rounded, size: 14, color: AppTheme.success),
                              SizedBox(width: 4),
                              Text('ON-CHAIN ANCHORED', style: TextStyle(fontSize: 10, fontWeight: FontWeight.w800, color: AppTheme.success)),
                            ],
                          ),
                        ),
                    ],
                  ),
                  const SizedBox(height: 8),
                  Text(ver.message, style: const TextStyle(fontSize: 12, color: AppTheme.textSecondary)),

                  const Divider(color: AppTheme.borderLight, height: 20),

                  if (ver.sequenceNumber != null) _buildInfoRow('Global Sequence #', '${ver.sequenceNumber}'),
                  if (ver.eventHash != null) _buildInfoRow('Event Hash (H_i)', '${ver.eventHash!.substring(0, 16)}...'),
                  if (ver.previousHash != null) _buildInfoRow('Previous Hash (H_i-1)', '${ver.previousHash!.substring(0, 16)}...'),
                  if (ver.payloadHash != null) _buildInfoRow('Payload Hash (P_i)', '${ver.payloadHash!.substring(0, 16)}...'),
                  if (ver.batchId != null) _buildInfoRow('Batch UUID', '${ver.batchId!.substring(0, 8)}...'),

                  const SizedBox(height: 14),

                  // Merkle Proof Subsection
                  proofAsync.when(
                    loading: () => const Text('Deriving Merkle inclusion proof...', style: TextStyle(fontSize: 11, color: AppTheme.textSecondary)),
                    error: (_, __) => const Text('Merkle inclusion proof not yet generated (event unbatched).', style: TextStyle(fontSize: 11, fontStyle: FontStyle.italic, color: AppTheme.textMuted)),
                    data: (proof) => Container(
                      padding: const EdgeInsets.all(12),
                      decoration: BoxDecoration(
                        color: AppTheme.backgroundSurface,
                        borderRadius: BorderRadius.circular(12),
                        border: Border.all(color: AppTheme.borderLight),
                      ),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const Row(
                            children: [
                              Icon(Icons.account_tree_rounded, size: 16, color: AppTheme.gradientSkyBlue),
                              SizedBox(width: 6),
                              Text('Merkle Inclusion Proof', style: TextStyle(fontSize: 12, fontWeight: FontWeight.w800, color: AppTheme.textPrimary)),
                            ],
                          ),
                          const SizedBox(height: 6),
                          _buildInfoRow('Batch Root', '${proof.batchRootHash.substring(0, 18)}...'),
                          _buildInfoRow('Leaf Index', '${proof.leafIndex} (of Batch #${proof.batchSequence})'),
                          if (proof.txHash != null) _buildInfoRow('Tx Hash', '${proof.txHash!.substring(0, 16)}...'),
                          if (proof.blockNumber != null) _buildInfoRow('Block #', '${proof.blockNumber}'),
                          const SizedBox(height: 6),
                          Text('Proof Steps (${proof.merkleProof.length}):', style: const TextStyle(fontSize: 11, fontWeight: FontWeight.w700, color: AppTheme.textSecondary)),
                          const SizedBox(height: 4),
                          ...proof.merkleProof.map((step) => Padding(
                            padding: const EdgeInsets.only(bottom: 2.0),
                            child: Text(
                              '• [${step.position.toUpperCase()}] ${step.hash.substring(0, 20)}...',
                              style: const TextStyle(fontSize: 10, fontFamily: 'monospace', color: AppTheme.textMuted),
                            ),
                          )),
                        ],
                      ),
                    ),
                  ),
                ],
              ),
            );
          },
        ),
      ],
    );
  }
}
