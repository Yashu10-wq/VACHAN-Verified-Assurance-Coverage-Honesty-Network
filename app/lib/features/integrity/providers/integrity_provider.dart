import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../auth/providers/auth_provider.dart';
import '../models/blockchain_status_model.dart';
import '../services/integrity_api_service.dart';

final integrityApiServiceProvider = Provider<IntegrityApiService>((ref) {
  final apiClient = ref.watch(apiClientProvider);
  return IntegrityApiService(apiClient: apiClient);
});

final blockchainStatusProvider = FutureProvider<BlockchainStatusModel>((ref) async {
  final apiService = ref.watch(integrityApiServiceProvider);
  return await apiService.getBlockchainStatus();
});

final auditEventVerificationProvider =
    FutureProvider.family<AuditEventVerificationModel, String>((ref, eventId) async {
  final apiService = ref.watch(integrityApiServiceProvider);
  return await apiService.verifyAuditEvent(eventId);
});

final auditEventProofProvider =
    FutureProvider.family<AuditEventProofModel, String>((ref, eventId) async {
  final apiService = ref.watch(integrityApiServiceProvider);
  return await apiService.getAuditEventProof(eventId);
});
