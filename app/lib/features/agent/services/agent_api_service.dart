import '../../../core/network/api_client.dart';
import '../../customer/models/customer_policy_model.dart';
import '../../customer/models/verification_report_model.dart';
import '../models/sales_session_model.dart';

class AgentApiService {
  final ApiClient apiClient;

  AgentApiService({required this.apiClient});

  // 1. List Sales Sessions
  Future<List<SalesSessionModel>> listSalesSessions({
    String? status,
    int page = 1,
    int pageSize = 50,
  }) async {
    try {
      final response = await apiClient.dio.get(
        '/sales-sessions',
        queryParameters: {
          if (status != null && status.isNotEmpty) 'status': status,
          'page': page,
          'page_size': pageSize,
        },
      );
      final list = (response.data as List)
          .map((item) => SalesSessionModel.fromJson(item as Map<String, dynamic>))
          .toList();
      return list;
    } catch (e) {
      throw apiClient.mapDioError(e);
    }
  }

  // 2. Get Sales Session Details
  Future<SalesSessionModel> getSalesSessionDetails(String sessionId) async {
    try {
      final response = await apiClient.dio.get('/sales-sessions/$sessionId');
      return SalesSessionModel.fromJson(response.data as Map<String, dynamic>);
    } catch (e) {
      throw apiClient.mapDioError(e);
    }
  }

  // 3. Create Sales Session (with Mandatory Affirmative Customer Consent)
  Future<SalesSessionModel> createSalesSession({
    required String customerId,
    String? policyId,
    String? policyVersionId,
    String? registrationId,
    required String audioStorageRef,
    required String audioMimeType,
    required int audioFileSizeBytes,
    int? durationSeconds,
    required String audioChecksum,
    required bool customerConsent,
    String? consentNotes,
  }) async {
    try {
      final response = await apiClient.dio.post(
        '/sales-sessions',
        data: {
          'customer_id': customerId,
          if (policyId != null) 'policy_id': policyId,
          if (policyVersionId != null) 'policy_version_id': policyVersionId,
          if (registrationId != null) 'registration_id': registrationId,
          'audio_storage_ref': audioStorageRef,
          'audio_mime_type': audioMimeType,
          'audio_file_size_bytes': audioFileSizeBytes,
          if (durationSeconds != null) 'duration_seconds': durationSeconds,
          'audio_checksum': audioChecksum,
          'customer_consent': customerConsent,
          if (consentNotes != null) 'consent_notes': consentNotes,
        },
      );
      return SalesSessionModel.fromJson(response.data as Map<String, dynamic>);
    } catch (e) {
      throw apiClient.mapDioError(e);
    }
  }

  // 4. Trigger ElevenLabs Transcription
  Future<Map<String, dynamic>> startTranscription(String sessionId) async {
    try {
      final response = await apiClient.dio.post('/sales-sessions/$sessionId/transcribe');
      return response.data as Map<String, dynamic>;
    } catch (e) {
      throw apiClient.mapDioError(e);
    }
  }

  // 5. Get Session Transcript
  Future<SalesTranscriptModel> getTranscript(String sessionId) async {
    try {
      final response = await apiClient.dio.get('/sales-sessions/$sessionId/transcript');
      return SalesTranscriptModel.fromJson(response.data as Map<String, dynamic>);
    } catch (e) {
      throw apiClient.mapDioError(e);
    }
  }

  // 6. Trigger Gemini Policy-Promise Verification
  Future<VerificationReportModel> verifySalesSession(String sessionId) async {
    try {
      final response = await apiClient.dio.post('/sales-sessions/$sessionId/verify-policy');
      return VerificationReportModel.fromJson(response.data as Map<String, dynamic>);
    } catch (e) {
      throw apiClient.mapDioError(e);
    }
  }

  // 7. Get Verification Report
  Future<VerificationReportModel?> getSessionVerification(String sessionId) async {
    try {
      final response = await apiClient.dio.get('/sales-sessions/$sessionId/verification');
      return VerificationReportModel.fromJson(response.data as Map<String, dynamic>);
    } catch (e) {
      return null;
    }
  }

  // 8. List Registrations and Policies for Agent dropdowns
  Future<List<CustomerRegistrationModel>> listRegistrations() async {
    try {
      final response = await apiClient.dio.get('/registrations');
      return (response.data as List)
          .map((item) => CustomerRegistrationModel.fromJson(item as Map<String, dynamic>))
          .toList();
    } catch (e) {
      throw apiClient.mapDioError(e);
    }
  }

  Future<List<DetailedPolicyModel>> listPolicies() async {
    try {
      final response = await apiClient.dio.get('/policies');
      return (response.data as List)
          .map((item) => DetailedPolicyModel.fromJson(item as Map<String, dynamic>))
          .toList();
    } catch (e) {
      throw apiClient.mapDioError(e);
    }
  }
}
