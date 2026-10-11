import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/errors/app_exception.dart';
import '../../auth/providers/auth_provider.dart';
import '../models/claim_model.dart';
import '../models/customer_policy_model.dart';
import '../models/verification_report_model.dart';
import '../services/customer_api_service.dart';

// Service provider
final customerApiServiceProvider = Provider<CustomerApiService>((ref) {
  final apiClient = ref.watch(apiClientProvider);
  return CustomerApiService(apiClient: apiClient);
});

// ==============================================================================
// 1. Customer Dashboard & Policies State & Notifier
// ==============================================================================

class CustomerDashboardState {
  final bool isLoading;
  final List<DetailedPolicyModel> cataloguePolicies;
  final List<CustomerRegistrationModel> registrations;
  final List<ClaimModel> recentClaims;
  final String? errorMessage;
  final bool isOffline;

  const CustomerDashboardState({
    this.isLoading = false,
    this.cataloguePolicies = const [],
    this.registrations = const [],
    this.recentClaims = const [],
    this.errorMessage,
    this.isOffline = false,
  });

  List<DetailedPolicyModel> get policies => cataloguePolicies;

  List<CustomerRegistrationModel> get activePolicies =>
      registrations.where((r) => r.isConfirmed).toList();

  List<CustomerRegistrationModel> get pendingConfirmationPolicies =>
      registrations.where((r) => r.isAwaitingConfirmation).toList();

  CustomerDashboardState copyWith({
    bool? isLoading,
    List<DetailedPolicyModel>? cataloguePolicies,
    List<CustomerRegistrationModel>? registrations,
    List<ClaimModel>? recentClaims,
    String? errorMessage,
    bool? isOffline,
  }) {
    return CustomerDashboardState(
      isLoading: isLoading ?? this.isLoading,
      cataloguePolicies: cataloguePolicies ?? this.cataloguePolicies,
      registrations: registrations ?? this.registrations,
      recentClaims: recentClaims ?? this.recentClaims,
      errorMessage: errorMessage,
      isOffline: isOffline ?? this.isOffline,
    );
  }
}

class CustomerDashboardNotifier extends StateNotifier<CustomerDashboardState> {
  final CustomerApiService _apiService;
  final Ref _ref;

  CustomerDashboardNotifier(this._apiService, this._ref)
      : super(const CustomerDashboardState()) {
    fetchDashboardData();
  }

  Future<void> fetchDashboardData() async {
    state = state.copyWith(isLoading: true, errorMessage: null, isOffline: false);

    try {
      // 1. Fetch published policy catalogue
      final policies = await _apiService.listPolicies();

      // 2. Fetch authenticated customer registrations & claims if logged in
      List<CustomerRegistrationModel> registrations = [];
      List<ClaimModel> claims = [];

      final authState = _ref.read(authProvider);
      if (authState.isAuthenticated) {
        try {
          registrations = await _apiService.listRegistrations();
        } catch (_) {}

        try {
          claims = await _apiService.listClaims();
        } catch (_) {}
      }

      state = state.copyWith(
        isLoading: false,
        cataloguePolicies: policies,
        registrations: registrations,
        recentClaims: claims,
      );
    } on NetworkException {
      state = state.copyWith(
        isLoading: false,
        isOffline: true,
        errorMessage: 'Network connection unavailable. Showing cached data.',
      );
    } catch (e) {
      state = state.copyWith(
        isLoading: false,
        errorMessage: e.toString(),
      );
    }
  }

  Future<bool> confirmRegistration(String registrationId) async {
    try {
      final updated = await _apiService.confirmRegistration(registrationId);
      final updatedRegs = state.registrations.map((r) {
        return r.id == registrationId ? updated : r;
      }).toList();
      state = state.copyWith(registrations: updatedRegs);
      return true;
    } catch (e) {
      state = state.copyWith(errorMessage: e.toString());
      return false;
    }
  }

  Future<bool> declineRegistration(String registrationId) async {
    try {
      final updated = await _apiService.declineRegistration(registrationId);
      final updatedRegs = state.registrations.map((r) {
        return r.id == registrationId ? updated : r;
      }).toList();
      state = state.copyWith(registrations: updatedRegs);
      return true;
    } catch (e) {
      state = state.copyWith(errorMessage: e.toString());
      return false;
    }
  }
}

final customerDashboardProvider =
    StateNotifierProvider<CustomerDashboardNotifier, CustomerDashboardState>((ref) {
  final apiService = ref.watch(customerApiServiceProvider);
  return CustomerDashboardNotifier(apiService, ref);
});

// ==============================================================================
// 2. Customer Claims State & Notifier
// ==============================================================================

class ClaimsListState {
  final bool isLoading;
  final List<ClaimModel> claims;
  final String? errorMessage;
  final String? statusFilter;

  const ClaimsListState({
    this.isLoading = false,
    this.claims = const [],
    this.errorMessage,
    this.statusFilter,
  });

  ClaimsListState copyWith({
    bool? isLoading,
    List<ClaimModel>? claims,
    String? errorMessage,
    String? statusFilter,
  }) {
    return ClaimsListState(
      isLoading: isLoading ?? this.isLoading,
      claims: claims ?? this.claims,
      errorMessage: errorMessage,
      statusFilter: statusFilter ?? this.statusFilter,
    );
  }
}

class ClaimsListNotifier extends StateNotifier<ClaimsListState> {
  final CustomerApiService _apiService;

  ClaimsListNotifier(this._apiService) : super(const ClaimsListState()) {
    fetchClaims();
  }

  Future<void> fetchClaims({String? status}) async {
    state = state.copyWith(isLoading: true, errorMessage: null, statusFilter: status);
    try {
      final claims = await _apiService.listClaims(status: status);
      state = state.copyWith(isLoading: false, claims: claims);
    } catch (e) {
      state = state.copyWith(isLoading: false, errorMessage: e.toString());
    }
  }

  Future<ClaimModel?> submitClaim({
    required String registrationId,
    required String claimCategory,
    required double requestedAmount,
    required String incidentDate,
    required String description,
  }) async {
    state = state.copyWith(isLoading: true, errorMessage: null);
    try {
      final newClaim = await _apiService.submitClaim(
        registrationId: registrationId,
        claimCategory: claimCategory,
        requestedAmount: requestedAmount,
        incidentDate: incidentDate,
        description: description,
      );
      state = state.copyWith(
        isLoading: false,
        claims: [newClaim, ...state.claims],
      );
      return newClaim;
    } catch (e) {
      state = state.copyWith(isLoading: false, errorMessage: e.toString());
      return null;
    }
  }
}

final claimsListProvider =
    StateNotifierProvider<ClaimsListNotifier, ClaimsListState>((ref) {
  final apiService = ref.watch(customerApiServiceProvider);
  return ClaimsListNotifier(apiService);
});

// ==============================================================================
// 3. Verification Report Detail Provider
// ==============================================================================

final verificationReportProvider =
    FutureProvider.family<VerificationReportModel?, String>((ref, reportId) async {
  final apiService = ref.watch(customerApiServiceProvider);
  try {
    return await apiService.getVerificationReport(reportId);
  } catch (e) {
    return null;
  }
});
