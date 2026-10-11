class FindingItemModel {
  final String findingId;
  final String promiseText;
  final String transcriptQuote;
  final String? speakerLabel;
  final String classification; // SUPPORTED, PARTLY_TRUE, CONTRADICTED, NOT_IN_POLICY, UNCLEAR
  final String? policyExcerpt;
  final int? pageNumber;
  final String? sectionHeading;
  final String explanation;
  final double confidence;
  final bool reviewRequired;
  final String validationStatus;

  const FindingItemModel({
    required this.findingId,
    required this.promiseText,
    required this.transcriptQuote,
    this.speakerLabel,
    required this.classification,
    this.policyExcerpt,
    this.pageNumber,
    this.sectionHeading,
    required this.explanation,
    required this.confidence,
    this.reviewRequired = false,
    this.validationStatus = 'GROUNDED',
  });

  factory FindingItemModel.fromJson(Map<String, dynamic> json) {
    return FindingItemModel(
      findingId: json['finding_id'] as String? ?? '',
      promiseText: json['promise_text'] as String? ?? '',
      transcriptQuote: json['transcript_quote'] as String? ?? '',
      speakerLabel: json['speaker_label'] as String?,
      classification: json['classification'] as String? ?? 'UNCLEAR',
      policyExcerpt: json['policy_excerpt'] as String?,
      pageNumber: json['page_number'] as int?,
      sectionHeading: json['section_heading'] as String?,
      explanation: json['explanation'] as String? ?? '',
      confidence: (json['confidence'] as num?)?.toDouble() ?? 1.0,
      reviewRequired: json['review_required'] as bool? ?? false,
      validationStatus: json['validation_status'] as String? ?? 'GROUNDED',
    );
  }
}

class VerificationReportModel {
  final String id;
  final String salesSessionId;
  final String customerId;
  final String agentId;
  final String policyId;
  final int reportVersion;
  final String status;
  final String? summary;
  final String? overallIntegrityStatus;
  final List<FindingItemModel> findings;
  final int supportedCount;
  final int partlyTrueCount;
  final int contradictedCount;
  final int notInPolicyCount;
  final int unclearCount;
  final String? createdAt;

  const VerificationReportModel({
    required this.id,
    required this.salesSessionId,
    required this.customerId,
    required this.agentId,
    required this.policyId,
    required this.reportVersion,
    required this.status,
    this.summary,
    this.overallIntegrityStatus,
    this.findings = const [],
    this.supportedCount = 0,
    this.partlyTrueCount = 0,
    this.contradictedCount = 0,
    this.notInPolicyCount = 0,
    this.unclearCount = 0,
    this.createdAt,
  });

  factory VerificationReportModel.fromJson(Map<String, dynamic> json) {
    return VerificationReportModel(
      id: json['id'] as String? ?? '',
      salesSessionId: json['sales_session_id'] as String? ?? '',
      customerId: json['customer_id'] as String? ?? '',
      agentId: json['agent_id'] as String? ?? '',
      policyId: json['policy_id'] as String? ?? '',
      reportVersion: json['report_version'] as int? ?? 1,
      status: json['status'] as String? ?? 'COMPLETED',
      summary: json['summary'] as String?,
      overallIntegrityStatus: json['overall_integrity_status'] as String?,
      findings: (json['findings'] as List? ?? [])
          .map((f) => FindingItemModel.fromJson(f as Map<String, dynamic>))
          .toList(),
      supportedCount: json['supported_count'] as int? ?? 0,
      partlyTrueCount: json['partly_true_count'] as int? ?? 0,
      contradictedCount: json['contradicted_count'] as int? ?? 0,
      notInPolicyCount: json['not_in_policy_count'] as int? ?? 0,
      unclearCount: json['unclear_count'] as int? ?? 0,
      createdAt: json['created_at'] as String?,
    );
  }
}
