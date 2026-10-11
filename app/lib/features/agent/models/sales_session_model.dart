class SalesSessionModel {
  final String id;
  final String customerId;
  final String agentId;
  final String? policyId;
  final String? policyVersionId;
  final String? registrationId;
  final String audioStorageRef;
  final String audioMimeType;
  final int audioFileSizeBytes;
  final int? durationSeconds;
  final String audioChecksum;
  final bool customerConsent;
  final String? consentTimestamp;
  final String? consentNotes;
  final String status; // PENDING, RECORDED, PROCESSING, COMPLETED, FAILED
  final String? detectedLanguage;
  final String? providerModel;
  final String? errorCategory;
  final String? errorMessage;
  final String createdAt;
  final String updatedAt;

  const SalesSessionModel({
    required this.id,
    required this.customerId,
    required this.agentId,
    this.policyId,
    this.policyVersionId,
    this.registrationId,
    required this.audioStorageRef,
    required this.audioMimeType,
    required this.audioFileSizeBytes,
    this.durationSeconds,
    required this.audioChecksum,
    required this.customerConsent,
    this.consentTimestamp,
    this.consentNotes,
    required this.status,
    this.detectedLanguage,
    this.providerModel,
    this.errorCategory,
    this.errorMessage,
    required this.createdAt,
    required this.updatedAt,
  });

  factory SalesSessionModel.fromJson(Map<String, dynamic> json) {
    return SalesSessionModel(
      id: json['id'] as String? ?? '',
      customerId: json['customer_id'] as String? ?? '',
      agentId: json['agent_id'] as String? ?? '',
      policyId: json['policy_id'] as String?,
      policyVersionId: json['policy_version_id'] as String?,
      registrationId: json['registration_id'] as String?,
      audioStorageRef: json['audio_storage_ref'] as String? ?? '',
      audioMimeType: json['audio_mime_type'] as String? ?? 'audio/m4a',
      audioFileSizeBytes: (json['audio_file_size_bytes'] as num?)?.toInt() ?? 0,
      durationSeconds: (json['duration_seconds'] as num?)?.toInt(),
      audioChecksum: json['audio_checksum'] as String? ?? '',
      customerConsent: json['customer_consent'] as bool? ?? false,
      consentTimestamp: json['consent_timestamp'] as String?,
      consentNotes: json['consent_notes'] as String?,
      status: json['status'] as String? ?? 'PENDING',
      detectedLanguage: json['detected_language'] as String?,
      providerModel: json['provider_model'] as String?,
      errorCategory: json['error_category'] as String?,
      errorMessage: json['error_message'] as String?,
      createdAt: json['created_at'] as String? ?? '',
      updatedAt: json['updated_at'] as String? ?? '',
    );
  }

  bool get isCompleted => status == 'COMPLETED';
  bool get isProcessing => status == 'PROCESSING';
  bool get isFailed => status == 'FAILED';
}

class SalesTranscriptModel {
  final String sessionId;
  final String status;
  final String? transcript;
  final String? detectedLanguage;
  final List<Map<String, dynamic>> wordSegments;
  final List<Map<String, dynamic>> speakerDiarization;
  final String? providerModel;
  final String createdAt;
  final String updatedAt;

  const SalesTranscriptModel({
    required this.sessionId,
    required this.status,
    this.transcript,
    this.detectedLanguage,
    this.wordSegments = const [],
    this.speakerDiarization = const [],
    this.providerModel,
    required this.createdAt,
    required this.updatedAt,
  });

  factory SalesTranscriptModel.fromJson(Map<String, dynamic> json) {
    return SalesTranscriptModel(
      sessionId: json['session_id'] as String? ?? '',
      status: json['status'] as String? ?? 'COMPLETED',
      transcript: json['transcript'] as String?,
      detectedLanguage: json['detected_language'] as String?,
      wordSegments: (json['word_segments'] as List? ?? [])
          .map((w) => Map<String, dynamic>.from(w as Map))
          .toList(),
      speakerDiarization: (json['speaker_diarization'] as List? ?? [])
          .map((s) => Map<String, dynamic>.from(s as Map))
          .toList(),
      providerModel: json['provider_model'] as String?,
      createdAt: json['created_at'] as String? ?? '',
      updatedAt: json['updated_at'] as String? ?? '',
    );
  }
}
