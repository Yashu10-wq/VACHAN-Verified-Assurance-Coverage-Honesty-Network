import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../auth/providers/auth_provider.dart';
import '../../customer/models/customer_policy_model.dart';
import '../models/sales_session_model.dart';
import '../services/agent_api_service.dart';

final agentApiServiceProvider = Provider<AgentApiService>((ref) {
  final apiClient = ref.watch(apiClientProvider);
  return AgentApiService(apiClient: apiClient);
});

class SalesSessionsListState {
  final bool isLoading;
  final List<SalesSessionModel> sessions;
  final String? errorMessage;
  final String? statusFilter;
  final String searchQuery;

  const SalesSessionsListState({
    this.isLoading = false,
    this.sessions = const [],
    this.errorMessage,
    this.statusFilter,
    this.searchQuery = '',
  });

  List<SalesSessionModel> get filteredSessions {
    return sessions.where((s) {
      final matchesStatus = statusFilter == null || statusFilter == 'ALL' || s.status == statusFilter;
      final matchesQuery = searchQuery.isEmpty ||
          s.id.toLowerCase().contains(searchQuery.toLowerCase()) ||
          s.customerId.toLowerCase().contains(searchQuery.toLowerCase()) ||
          (s.policyId?.toLowerCase().contains(searchQuery.toLowerCase()) ?? false);
      return matchesStatus && matchesQuery;
    }).toList();
  }

  SalesSessionsListState copyWith({
    bool? isLoading,
    List<SalesSessionModel>? sessions,
    String? errorMessage,
    String? statusFilter,
    String? searchQuery,
  }) {
    return SalesSessionsListState(
      isLoading: isLoading ?? this.isLoading,
      sessions: sessions ?? this.sessions,
      errorMessage: errorMessage,
      statusFilter: statusFilter ?? this.statusFilter,
      searchQuery: searchQuery ?? this.searchQuery,
    );
  }
}

class SalesSessionsListNotifier extends StateNotifier<SalesSessionsListState> {
  final AgentApiService _apiService;

  SalesSessionsListNotifier(this._apiService) : super(const SalesSessionsListState()) {
    fetchSessions();
  }

  Future<void> fetchSessions({String? status}) async {
    state = state.copyWith(isLoading: true, errorMessage: null, statusFilter: status);
    try {
      final sessions = await _apiService.listSalesSessions(
        status: status == 'ALL' ? null : status,
      );
      state = state.copyWith(isLoading: false, sessions: sessions);
    } catch (e) {
      state = state.copyWith(isLoading: false, errorMessage: e.toString());
    }
  }

  void setSearchQuery(String query) {
    state = state.copyWith(searchQuery: query);
  }

  void setStatusFilter(String? status) {
    state = state.copyWith(statusFilter: status);
    fetchSessions(status: status);
  }
}

final salesSessionsListProvider =
    StateNotifierProvider<SalesSessionsListNotifier, SalesSessionsListState>((ref) {
  final apiService = ref.watch(agentApiServiceProvider);
  return SalesSessionsListNotifier(apiService);
});

// Single session detail provider
final sessionDetailProvider =
    FutureProvider.family<SalesSessionModel, String>((ref, sessionId) async {
  final apiService = ref.watch(agentApiServiceProvider);
  return await apiService.getSalesSessionDetails(sessionId);
});

// Transcript provider
final sessionTranscriptProvider =
    FutureProvider.family<SalesTranscriptModel?, String>((ref, sessionId) async {
  final apiService = ref.watch(agentApiServiceProvider);
  try {
    return await apiService.getTranscript(sessionId);
  } catch (_) {
    return null;
  }
});

// Registrations provider for dropdown selection
final agentRegistrationsProvider =
    FutureProvider<List<CustomerRegistrationModel>>((ref) async {
  final apiService = ref.watch(agentApiServiceProvider);
  try {
    return await apiService.listRegistrations();
  } catch (_) {
    return [];
  }
});

// Published Policies provider for dropdown selection
final agentPoliciesProvider =
    FutureProvider<List<DetailedPolicyModel>>((ref) async {
  final apiService = ref.watch(agentApiServiceProvider);
  try {
    return await apiService.listPolicies();
  } catch (_) {
    return [];
  }
});
