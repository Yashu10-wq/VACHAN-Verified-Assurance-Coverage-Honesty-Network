class BlockchainStatusModel {
  final bool isConnected;
  final String rpcUrl;
  final int configuredChainId;
  final int? nodeChainId;
  final int? blockNumber;
  final String? contractAddress;
  final bool contractDeployed;
  final String status;
  final int totalEvents;
  final int unchainedEvents;
  final int pendingEvents;
  final int batchedEvents;
  final int anchoredEvents;
  final int failedEvents;

  const BlockchainStatusModel({
    required this.isConnected,
    required this.rpcUrl,
    required this.configuredChainId,
    this.nodeChainId,
    this.blockNumber,
    this.contractAddress,
    required this.contractDeployed,
    required this.status,
    this.totalEvents = 0,
    this.unchainedEvents = 0,
    this.pendingEvents = 0,
    this.batchedEvents = 0,
    this.anchoredEvents = 0,
    this.failedEvents = 0,
  });

  factory BlockchainStatusModel.fromJson(Map<String, dynamic> json) {
    return BlockchainStatusModel(
      isConnected: json['is_connected'] as bool? ?? false,
      rpcUrl: json['rpc_url'] as String? ?? '',
      configuredChainId: (json['configured_chain_id'] as num?)?.toInt() ?? 0,
      nodeChainId: (json['node_chain_id'] as num?)?.toInt(),
      blockNumber: (json['block_number'] as num?)?.toInt(),
      contractAddress: json['contract_address'] as String?,
      contractDeployed: json['contract_deployed'] as bool? ?? false,
      status: json['status'] as String? ?? 'UNKNOWN',
      totalEvents: (json['total_events'] as num?)?.toInt() ?? 0,
      unchainedEvents: (json['unchained_events'] as num?)?.toInt() ?? 0,
      pendingEvents: (json['pending_events'] as num?)?.toInt() ?? 0,
      batchedEvents: (json['batched_events'] as num?)?.toInt() ?? 0,
      anchoredEvents: (json['anchored_events'] as num?)?.toInt() ?? 0,
      failedEvents: (json['failed_events'] as num?)?.toInt() ?? 0,
    );
  }

  bool get isNodeOnline => isConnected;
  bool get isContractReady => contractDeployed && (contractAddress != null && contractAddress!.isNotEmpty);
}

class MerkleProofStepModel {
  final String position; // 'left' or 'right'
  final String hash;

  const MerkleProofStepModel({
    required this.position,
    required this.hash,
  });

  factory MerkleProofStepModel.fromJson(Map<String, dynamic> json) {
    return MerkleProofStepModel(
      position: json['position'] as String? ?? 'right',
      hash: json['hash'] as String? ?? '',
    );
  }
}

class AuditEventVerificationModel {
  final String eventId;
  final String outcome; // VALID, HASH_MISMATCH, PREVIOUS_HASH_MISMATCH, ANCHOR_PENDING, ANCHOR_NOT_FOUND, NOT_FOUND
  final String message;
  final int? sequenceNumber;
  final String? eventHash;
  final String? previousHash;
  final String? payloadHash;
  final String? anchoringStatus;
  final String? batchId;
  final String? createdAt;
  final bool onChainVerified;

  const AuditEventVerificationModel({
    required this.eventId,
    required this.outcome,
    required this.message,
    this.sequenceNumber,
    this.eventHash,
    this.previousHash,
    this.payloadHash,
    this.anchoringStatus,
    this.batchId,
    this.createdAt,
    this.onChainVerified = false,
  });

  factory AuditEventVerificationModel.fromJson(Map<String, dynamic> json) {
    return AuditEventVerificationModel(
      eventId: json['event_id'] as String? ?? '',
      outcome: json['outcome'] as String? ?? 'UNKNOWN',
      message: json['message'] as String? ?? '',
      sequenceNumber: (json['sequence_number'] as num?)?.toInt(),
      eventHash: json['event_hash'] as String?,
      previousHash: json['previous_hash'] as String?,
      payloadHash: json['payload_hash'] as String?,
      anchoringStatus: json['anchoring_status'] as String?,
      batchId: json['batch_id'] as String?,
      createdAt: json['created_at'] as String?,
      onChainVerified: json['on_chain_verified'] as bool? ?? false,
    );
  }

  bool get isValid => outcome == 'VALID';
  bool get isPending => outcome == 'ANCHOR_PENDING';
  bool get isMismatch => outcome == 'HASH_MISMATCH' || outcome == 'PREVIOUS_HASH_MISMATCH';
}

class AuditEventProofModel {
  final String eventId;
  final int sequenceNumber;
  final String eventHash;
  final String batchId;
  final int batchSequence;
  final String batchRootHash;
  final int leafIndex;
  final List<MerkleProofStepModel> merkleProof;
  final String? txHash;
  final int? blockNumber;
  final int? chainId;
  final String? contractAddress;
  final bool onChainCommitmentVerified;
  final String? anchoredAt;

  const AuditEventProofModel({
    required this.eventId,
    required this.sequenceNumber,
    required this.eventHash,
    required this.batchId,
    required this.batchSequence,
    required this.batchRootHash,
    required this.leafIndex,
    required this.merkleProof,
    this.txHash,
    this.blockNumber,
    this.chainId,
    this.contractAddress,
    this.onChainCommitmentVerified = false,
    this.anchoredAt,
  });

  factory AuditEventProofModel.fromJson(Map<String, dynamic> json) {
    return AuditEventProofModel(
      eventId: json['event_id'] as String? ?? '',
      sequenceNumber: (json['sequence_number'] as num?)?.toInt() ?? 0,
      eventHash: json['event_hash'] as String? ?? '',
      batchId: json['batch_id'] as String? ?? '',
      batchSequence: (json['batch_sequence'] as num?)?.toInt() ?? 0,
      batchRootHash: json['batch_root_hash'] as String? ?? '',
      leafIndex: (json['leaf_index'] as num?)?.toInt() ?? 0,
      merkleProof: (json['merkle_proof'] as List? ?? [])
          .map((s) => MerkleProofStepModel.fromJson(s as Map<String, dynamic>))
          .toList(),
      txHash: json['tx_hash'] as String?,
      blockNumber: (json['block_number'] as num?)?.toInt(),
      chainId: (json['chain_id'] as num?)?.toInt(),
      contractAddress: json['contract_address'] as String?,
      onChainCommitmentVerified: json['on_chain_commitment_verified'] as bool? ?? false,
      anchoredAt: json['anchored_at'] as String?,
    );
  }
}
