import '../../../core/network/api_client.dart';
import '../models/blockchain_status_model.dart';

class IntegrityApiService {
  final ApiClient apiClient;

  IntegrityApiService({required this.apiClient});

  // 1. Get Blockchain Connectivity & Anchoring Status
  Future<BlockchainStatusModel> getBlockchainStatus() async {
    try {
      final response = await apiClient.dio.get('/integrity/status');
      return BlockchainStatusModel.fromJson(response.data as Map<String, dynamic>);
    } catch (e) {
      throw apiClient.mapDioError(e);
    }
  }

  // 2. Verify Individual Audit Event Hash-Chain
  Future<AuditEventVerificationModel> verifyAuditEvent(String eventId) async {
    try {
      final response = await apiClient.dio.get('/integrity/audit-events/$eventId');
      return AuditEventVerificationModel.fromJson(response.data as Map<String, dynamic>);
    } catch (e) {
      throw apiClient.mapDioError(e);
    }
  }

  // 3. Get Cryptographic Merkle Inclusion Proof
  Future<AuditEventProofModel> getAuditEventProof(String eventId) async {
    try {
      final response = await apiClient.dio.get('/integrity/audit-events/$eventId/proof');
      return AuditEventProofModel.fromJson(response.data as Map<String, dynamic>);
    } catch (e) {
      throw apiClient.mapDioError(e);
    }
  }

  // 4. Verify Multiple Audit Events
  Future<List<AuditEventVerificationModel>> verifyMultipleAuditEvents(List<String> eventIds) async {
    try {
      final response = await apiClient.dio.post(
        '/integrity/verify',
        data: {'event_ids': eventIds},
      );
      final list = (response.data as List)
          .map((item) => AuditEventVerificationModel.fromJson(item as Map<String, dynamic>))
          .toList();
      return list;
    } catch (e) {
      throw apiClient.mapDioError(e);
    }
  }

  // 5. Trigger Anchor Pending Batches (Approval Authority Only)
  Future<Map<String, dynamic>> anchorPendingBatches() async {
    try {
      final response = await apiClient.dio.post('/integrity/anchor-pending');
      return response.data as Map<String, dynamic>;
    } catch (e) {
      throw apiClient.mapDioError(e);
    }
  }

  // 6. Trigger Legacy Audit Backfill (Approval Authority Only)
  Future<Map<String, dynamic>> triggerLegacyBackfill() async {
    try {
      final response = await apiClient.dio.post('/integrity/backfill');
      return response.data as Map<String, dynamic>;
    } catch (e) {
      throw apiClient.mapDioError(e);
    }
  }
}
