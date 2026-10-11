class RuleEvaluationModel {
  final String ruleId;
  final String result;
  final String explanation;
  final Map<String, dynamic> details;

  const RuleEvaluationModel({
    required this.ruleId,
    required this.result,
    required this.explanation,
    this.details = const {},
  });

  factory RuleEvaluationModel.fromJson(Map<String, dynamic> json) {
    return RuleEvaluationModel(
      ruleId: json['rule_id'] as String? ?? '',
      result: json['result'] as String? ?? '',
      explanation: json['explanation'] as String? ?? '',
      details: json['details'] as Map<String, dynamic>? ?? {},
    );
  }
}

class ClaimAssessmentModel {
  final String id;
  final String claimId;
  final int assessmentVersion;
  final String overallOutcome;
  final List<RuleEvaluationModel> rulesEvaluated;
  final String requestedAmount;
  final String applicableLimit;
  final String potentiallyPayableAmount;
  final String excessAmount;
  final List<String> missingEvidence;
  final List<String> reviewFlags;
  final String? createdAt;

  const ClaimAssessmentModel({
    required this.id,
    required this.claimId,
    required this.assessmentVersion,
    required this.overallOutcome,
    required this.rulesEvaluated,
    required this.requestedAmount,
    required this.applicableLimit,
    required this.potentiallyPayableAmount,
    required this.excessAmount,
    required this.missingEvidence,
    required this.reviewFlags,
    this.createdAt,
  });

  factory ClaimAssessmentModel.fromJson(Map<String, dynamic> json) {
    return ClaimAssessmentModel(
      id: json['id'] as String? ?? '',
      claimId: json['claim_id'] as String? ?? '',
      assessmentVersion: json['assessment_version'] as int? ?? 1,
      overallOutcome: json['overall_outcome'] as String? ?? 'PENDING',
      rulesEvaluated: (json['rules_evaluated'] as List? ?? [])
          .map((r) => RuleEvaluationModel.fromJson(r as Map<String, dynamic>))
          .toList(),
      requestedAmount: json['requested_amount']?.toString() ?? '0.00',
      applicableLimit: json['applicable_limit']?.toString() ?? '0.00',
      potentiallyPayableAmount: json['potentially_payable_amount']?.toString() ?? '0.00',
      excessAmount: json['excess_amount']?.toString() ?? '0.00',
      missingEvidence: (json['missing_evidence'] as List? ?? []).map((e) => e.toString()).toList(),
      reviewFlags: (json['review_flags'] as List? ?? []).map((f) => f.toString()).toList(),
      createdAt: json['created_at'] as String?,
    );
  }
}

class ClaimEvidenceModel {
  final String id;
  final String claimId;
  final String? evidenceType;
  final String originalFilename;
  final int fileSizeBytes;
  final String mimeType;
  final String documentChecksum;
  final String createdAt;

  const ClaimEvidenceModel({
    required this.id,
    required this.claimId,
    this.evidenceType,
    required this.originalFilename,
    required this.fileSizeBytes,
    required this.mimeType,
    required this.documentChecksum,
    required this.createdAt,
  });

  factory ClaimEvidenceModel.fromJson(Map<String, dynamic> json) {
    return ClaimEvidenceModel(
      id: json['id'] as String? ?? '',
      claimId: json['claim_id'] as String? ?? '',
      evidenceType: json['evidence_type'] as String?,
      originalFilename: json['original_filename'] as String? ?? '',
      fileSizeBytes: json['file_size_bytes'] as int? ?? 0,
      mimeType: json['mime_type'] as String? ?? '',
      documentChecksum: json['document_checksum'] as String? ?? '',
      createdAt: json['created_at'] as String? ?? '',
    );
  }
}

class ClaimStatusHistoryModel {
  final String id;
  final String? previousStatus;
  final String newStatus;
  final String reason;
  final String actorRole;
  final String createdAt;

  const ClaimStatusHistoryModel({
    required this.id,
    this.previousStatus,
    required this.newStatus,
    required this.reason,
    required this.actorRole,
    required this.createdAt,
  });

  factory ClaimStatusHistoryModel.fromJson(Map<String, dynamic> json) {
    return ClaimStatusHistoryModel(
      id: json['id'] as String? ?? '',
      previousStatus: json['previous_status'] as String?,
      newStatus: json['new_status'] as String? ?? '',
      reason: json['reason'] as String? ?? '',
      actorRole: json['actor_role'] as String? ?? '',
      createdAt: json['created_at'] as String? ?? '',
    );
  }
}

class ClaimModel {
  final String id;
  final String customerId;
  final String registrationId;
  final String policyId;
  final String policyVersionId;
  final String claimCategory;
  final String requestedAmount;
  final String incidentDate;
  final String submissionTimestamp;
  final String description;
  final String status;
  final String createdAt;
  final List<ClaimEvidenceModel> evidence;
  final ClaimAssessmentModel? latestAssessment;
  final List<ClaimStatusHistoryModel> statusHistory;

  const ClaimModel({
    required this.id,
    required this.customerId,
    required this.registrationId,
    required this.policyId,
    required this.policyVersionId,
    required this.claimCategory,
    required this.requestedAmount,
    required this.incidentDate,
    required this.submissionTimestamp,
    required this.description,
    required this.status,
    required this.createdAt,
    this.evidence = const [],
    this.latestAssessment,
    this.statusHistory = const [],
  });

  factory ClaimModel.fromJson(Map<String, dynamic> json) {
    return ClaimModel(
      id: json['id'] as String? ?? '',
      customerId: json['customer_id'] as String? ?? '',
      registrationId: json['registration_id'] as String? ?? '',
      policyId: json['policy_id'] as String? ?? '',
      policyVersionId: json['policy_version_id'] as String? ?? '',
      claimCategory: json['claim_category'] as String? ?? 'GENERIC',
      requestedAmount: json['requested_amount']?.toString() ?? '0.00',
      incidentDate: json['incident_date'] as String? ?? '',
      submissionTimestamp: json['submission_timestamp'] as String? ?? '',
      description: json['description'] as String? ?? '',
      status: json['status'] as String? ?? 'SUBMITTED',
      createdAt: json['created_at'] as String? ?? '',
      evidence: (json['evidence'] as List? ?? [])
          .map((e) => ClaimEvidenceModel.fromJson(e as Map<String, dynamic>))
          .toList(),
      latestAssessment: json['latest_assessment'] != null
          ? ClaimAssessmentModel.fromJson(json['latest_assessment'] as Map<String, dynamic>)
          : null,
      statusHistory: (json['status_history'] as List? ?? [])
          .map((h) => ClaimStatusHistoryModel.fromJson(h as Map<String, dynamic>))
          .toList(),
    );
  }

  String get claimNumber => '#${id.substring(0, id.length > 8 ? 8 : id.length)}';
  double get requestedAmountValue => double.tryParse(requestedAmount) ?? 0.0;
}
