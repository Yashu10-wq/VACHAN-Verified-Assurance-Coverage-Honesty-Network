import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../auth/providers/auth_provider.dart';
import '../../customer/models/claim_model.dart';
import '../services/authority_api_service.dart';

final authorityApiServiceProvider = Provider<AuthorityApiService>((ref) {
  final apiClient = ref.watch(apiClientProvider);
  return AuthorityApiService(apiClient: apiClient);
});

class AuthorityClaimsState {
  final bool isLoading;
  final List<ClaimModel> claims;
  final String? errorMessage;
  final String? statusFilter;
  final String searchQuery;

  const AuthorityClaimsState({
    this.isLoading = false,
    this.claims = const [],
    this.errorMessage,
    this.statusFilter,
    this.searchQuery = '',
  });

  int get submittedCount => claims.where((c) => c.status == 'SUBMITTED').length;
  int get inReviewCount => claims.where((c) => c.status == 'IN_REVIEW').length;
  int get evidenceRequestedCount => claims.where((c) => c.status == 'EVIDENCE_REQUESTED').length;
  int get approvedCount => claims.where((c) => c.status == 'APPROVED').length;
  int get paidCount => claims.where((c) => c.status == 'PAID').length;
  int get rejectedCount => claims.where((c) => c.status == 'REJECTED').length;

  List<ClaimModel> get filteredClaims {
    return claims.where((c) {
      final matchesStatus = statusFilter == null || statusFilter == 'ALL' || c.status == statusFilter;
      final matchesQuery = searchQuery.isEmpty ||
          c.id.toLowerCase().contains(searchQuery.toLowerCase()) ||
          c.customerId.toLowerCase().contains(searchQuery.toLowerCase()) ||
          c.claimCategory.toLowerCase().contains(searchQuery.toLowerCase());
      return matchesStatus && matchesQuery;
    }).toList();
  }

  AuthorityClaimsState copyWith({
    bool? isLoading,
    List<ClaimModel>? claims,
    String? errorMessage,
    String? statusFilter,
    String? searchQuery,
  }) {
    return AuthorityClaimsState(
      isLoading: isLoading ?? this.isLoading,
      claims: claims ?? this.claims,
      errorMessage: errorMessage,
      statusFilter: statusFilter ?? this.statusFilter,
      searchQuery: searchQuery ?? this.searchQuery,
    );
  }
}

class AuthorityClaimsNotifier extends StateNotifier<AuthorityClaimsState> {
  final AuthorityApiService _apiService;

  AuthorityClaimsNotifier(this._apiService) : super(const AuthorityClaimsState()) {
    fetchClaims();
  }

  Future<void> fetchClaims({String? status}) async {
    state = state.copyWith(isLoading: true, errorMessage: null, statusFilter: status);
    try {
      final claims = await _apiService.listAllClaims(status: status);
      state = state.copyWith(isLoading: false, claims: claims);
    } catch (e) {
      state = state.copyWith(isLoading: false, errorMessage: e.toString());
    }
  }

  void setSearchQuery(String query) {
    state = state.copyWith(searchQuery: query);
  }

  void setStatusFilter(String? status) {
    state = state.copyWith(statusFilter: status);
    fetchClaims(status: status);
  }
}

final authorityClaimsProvider =
    StateNotifierProvider<AuthorityClaimsNotifier, AuthorityClaimsState>((ref) {
  final apiService = ref.watch(authorityApiServiceProvider);
  return AuthorityClaimsNotifier(apiService);
});

final authorityClaimDetailProvider =
    FutureProvider.family<ClaimModel, String>((ref, claimId) async {
  final apiService = ref.watch(authorityApiServiceProvider);
  return await apiService.getClaimDetails(claimId);
});

final authorityDuplicatesProvider =
    FutureProvider.family<List<Map<String, dynamic>>, String>((ref, claimId) async {
  final apiService = ref.watch(authorityApiServiceProvider);
  return await apiService.checkDuplicates(claimId);
});
