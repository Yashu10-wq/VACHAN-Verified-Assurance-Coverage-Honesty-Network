class PolicyVersionModel {
  final String id;
  final String policyId;
  final int versionNumber;
  final String? documentStorageRef;
  final String? documentChecksum;
  final String? effectiveDate;
  final String? expiryDate;
  final bool isPublished;
  final Map<String, dynamic> termsJson;

  const PolicyVersionModel({
    required this.id,
    required this.policyId,
    required this.versionNumber,
    this.documentStorageRef,
    this.documentChecksum,
    this.effectiveDate,
    this.expiryDate,
    this.isPublished = false,
    this.termsJson = const {},
  });

  factory PolicyVersionModel.fromJson(Map<String, dynamic> json) {
    return PolicyVersionModel(
      id: json['id'] as String? ?? '',
      policyId: json['policy_id'] as String? ?? '',
      versionNumber: json['version_number'] as int? ?? 1,
      documentStorageRef: json['document_storage_ref'] as String?,
      documentChecksum: json['document_checksum'] as String?,
      effectiveDate: json['effective_date'] as String?,
      expiryDate: json['expiry_date'] as String?,
      isPublished: json['is_published'] as bool? ?? false,
      termsJson: json['terms_json'] as Map<String, dynamic>? ?? {},
    );
  }
}

class DetailedPolicyModel {
  final String id;
  final String insurerName;
  final String policyName;
  final String policyCode;
  final String category;
  final String? description;
  final double coverageLimit;
  final int waitingPeriodDays;
  final int claimFilingWindowDays;
  final bool isActive;
  final PolicyVersionModel? latestVersion;
  final String? createdAt;

  const DetailedPolicyModel({
    required this.id,
    required this.insurerName,
    required this.policyName,
    required this.policyCode,
    required this.category,
    this.description,
    required this.coverageLimit,
    required this.waitingPeriodDays,
    required this.claimFilingWindowDays,
    required this.isActive,
    this.latestVersion,
    this.createdAt,
  });

  factory DetailedPolicyModel.fromJson(Map<String, dynamic> json) {
    return DetailedPolicyModel(
      id: json['id'] as String? ?? '',
      insurerName: json['insurer_name'] as String? ?? '',
      policyName: json['policy_name'] as String? ?? '',
      policyCode: json['policy_code'] as String? ?? '',
      category: json['category'] as String? ?? '',
      description: json['description'] as String?,
      coverageLimit: (json['coverage_limit'] as num?)?.toDouble() ?? 0.0,
      waitingPeriodDays: json['waiting_period_days'] as int? ?? 0,
      claimFilingWindowDays: json['claim_filing_window_days'] as int? ?? 30,
      isActive: json['is_active'] as bool? ?? true,
      latestVersion: json['latest_version'] != null
          ? PolicyVersionModel.fromJson(json['latest_version'] as Map<String, dynamic>)
          : (json['versions'] as List?)?.isNotEmpty == true
              ? PolicyVersionModel.fromJson((json['versions'] as List).first as Map<String, dynamic>)
              : null,
      createdAt: json['created_at'] as String?,
    );
  }
}

class CustomerRegistrationModel {
  final String id;
  final String customerId;
  final String? agentId;
  final String policyId;
  final String policyVersionId;
  final String status;
  final bool customerConsent;
  final String? consentNotes;
  final String? createdAt;
  final String? confirmedAt;
  final DetailedPolicyModel? policyDetail;

  const CustomerRegistrationModel({
    required this.id,
    required this.customerId,
    this.agentId,
    required this.policyId,
    required this.policyVersionId,
    required this.status,
    required this.customerConsent,
    this.consentNotes,
    this.createdAt,
    this.confirmedAt,
    this.policyDetail,
  });

  factory CustomerRegistrationModel.fromJson(
    Map<String, dynamic> json, {
    DetailedPolicyModel? policy,
  }) {
    return CustomerRegistrationModel(
      id: json['id'] as String? ?? '',
      customerId: json['customer_id'] as String? ?? '',
      agentId: json['agent_id'] as String?,
      policyId: json['policy_id'] as String? ?? '',
      policyVersionId: json['policy_version_id'] as String? ?? '',
      status: json['status'] as String? ?? 'PENDING',
      customerConsent: json['customer_consent'] as bool? ?? false,
      consentNotes: json['consent_notes'] as String?,
      createdAt: json['created_at'] as String?,
      confirmedAt: json['confirmed_at'] as String?,
      policyDetail: policy,
    );
  }

  bool get isConfirmed => status == 'CONFIRMED';
  bool get isAwaitingConfirmation =>
      status == 'AWAITING_CUSTOMER_CONFIRMATION' || status == 'PENDING_VERIFICATION';
  bool get isDeclined => status == 'DECLINED';
}
