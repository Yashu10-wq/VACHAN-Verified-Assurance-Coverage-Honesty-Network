import '../../../core/network/api_client.dart';
import '../../customer/models/claim_model.dart';

class AuthorityApiService {
  final ApiClient apiClient;

  AuthorityApiService({required this.apiClient});

  // 1. List All System-Wide Claims
  Future<List<ClaimModel>> listAllClaims({
    String? status,
    int page = 1,
    int pageSize = 100,
  }) async {
    try {
      final response = await apiClient.dio.get(
        '/claims',
        queryParameters: {
          if (status != null && status.isNotEmpty && status != 'ALL') 'status': status,
          'page': page,
          'page_size': pageSize,
        },
      );
      final list = (response.data as List)
          .map((item) => ClaimModel.fromJson(item as Map<String, dynamic>))
          .toList();
      return list;
    } catch (e) {
      throw apiClient.mapDioError(e);
    }
  }

  // 2. Get Claim Details
  Future<ClaimModel> getClaimDetails(String claimId) async {
    try {
      final response = await apiClient.dio.get('/claims/$claimId');
      return ClaimModel.fromJson(response.data as Map<String, dynamic>);
    } catch (e) {
      throw apiClient.mapDioError(e);
    }
  }

  // 3. Deterministic Eligibility Assessment Execution
  Future<ClaimAssessmentModel> assessClaim(String claimId) async {
    try {
      final response = await apiClient.dio.post('/claims/$claimId/assess');
      return ClaimAssessmentModel.fromJson(response.data as Map<String, dynamic>);
    } catch (e) {
      throw apiClient.mapDioError(e);
    }
  }

  // 4. Duplicate Claims Check
  Future<List<Map<String, dynamic>>> checkDuplicates(String claimId) async {
    try {
      final response = await apiClient.dio.get('/claims/$claimId/duplicates');
      final data = response.data as Map<String, dynamic>;
      final candidates = data['candidates'] as List? ?? [];
      return candidates.map((c) => Map<String, dynamic>.from(c as Map)).toList();
    } catch (e) {
      return [];
    }
  }

  // 5. Short-lived Signed URL for Private Cloudinary Evidence View
  Future<String> getEvidenceSignedUrl(String claimId, String evidenceId) async {
    try {
      final response = await apiClient.dio.get('/claims/$claimId/evidence/$evidenceId/signed-url');
      final data = response.data as Map<String, dynamic>;
      return data['signed_url'] as String? ?? '';
    } catch (e) {
      throw apiClient.mapDioError(e);
    }
  }

  // 6. Transition Claim Lifecycle Status (Requires reason >= 5 chars)
  Future<ClaimModel> transitionStatus({
    required String claimId,
    required String targetStatus,
    required String reason,
    Map<String, dynamic>? decisionMetadata,
  }) async {
    try {
      final response = await apiClient.dio.post(
        '/claims/$claimId/transition',
        data: {
          'target_status': targetStatus,
          'reason': reason,
          'decision_metadata': decisionMetadata ?? {},
        },
      );
      return ClaimModel.fromJson(response.data as Map<String, dynamic>);
    } catch (e) {
      throw apiClient.mapDioError(e);
    }
  }

  // 7. Simulated Payment Execution (Exclusively for APPROVED claims, transitions to PAID)
  Future<ClaimModel> simulatePayment({
    required String claimId,
    required String reason,
    Map<String, dynamic>? decisionMetadata,
  }) async {
    try {
      final response = await apiClient.dio.post(
        '/claims/$claimId/simulate-payment',
        data: {
          'target_status': 'PAID',
          'reason': reason,
          'decision_metadata': decisionMetadata ?? {},
        },
      );
      return ClaimModel.fromJson(response.data as Map<String, dynamic>);
    } catch (e) {
      throw apiClient.mapDioError(e);
    }
  }

  // 8. Status History
  Future<List<ClaimStatusHistoryModel>> getStatusHistory(String claimId) async {
    try {
      final response = await apiClient.dio.get('/claims/$claimId/history');
      return (response.data as List)
          .map((item) => ClaimStatusHistoryModel.fromJson(item as Map<String, dynamic>))
          .toList();
    } catch (e) {
      return [];
    }
  }
}
