import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/errors/app_exception.dart';
import '../../../core/network/api_client.dart';
import '../../../core/storage/secure_storage_service.dart';
import '../models/user_model.dart';
import '../services/auth_api_service.dart';

// Providers for dependencies
final secureStorageProvider = Provider<SecureStorageService>((ref) {
  return SecureStorageService();
});

final apiClientProvider = Provider<ApiClient>((ref) {
  final storage = ref.watch(secureStorageProvider);
  return ApiClient(customStorage: storage);
});

final authApiServiceProvider = Provider<AuthApiService>((ref) {
  final client = ref.watch(apiClientProvider);
  return AuthApiService(client: client);
});

// Auth State Definition
enum AuthStatus {
  initial,
  loading,
  authenticated,
  unauthenticated,
  pendingVerification,
  pendingApproval,
  error,
}

class AuthState {
  final AuthStatus status;
  final UserModel? user;
  final String? errorMessage;
  final String? pendingEmail;

  const AuthState({
    required this.status,
    this.user,
    this.errorMessage,
    this.pendingEmail,
  });

  factory AuthState.initial() => const AuthState(status: AuthStatus.initial);

  factory AuthState.loading() => const AuthState(status: AuthStatus.loading);

  factory AuthState.authenticated(UserModel user) => AuthState(
        status: AuthStatus.authenticated,
        user: user,
      );

  factory AuthState.unauthenticated() =>
      const AuthState(status: AuthStatus.unauthenticated);

  factory AuthState.pendingVerification(String email) => AuthState(
        status: AuthStatus.pendingVerification,
        pendingEmail: email,
      );

  factory AuthState.pendingApproval(UserModel? user, {String? email}) =>
      AuthState(
        status: AuthStatus.pendingApproval,
        user: user,
        pendingEmail: email,
      );

  factory AuthState.error(String message) => AuthState(
        status: AuthStatus.error,
        errorMessage: message,
      );

  bool get isAuthenticated => status == AuthStatus.authenticated && user != null;
}

// Auth Notifier
class AuthNotifier extends StateNotifier<AuthState> {
  final AuthApiService _authService;
  final SecureStorageService _storageService;

  AuthNotifier({
    required AuthApiService authService,
    required SecureStorageService storageService,
  })  : _authService = authService,
        _storageService = storageService,
        super(AuthState.initial());

  Future<void> checkSession() async {
    state = AuthState.loading();
    try {
      final token = await _storageService.getAccessToken();
      if (token == null || token.isEmpty) {
        state = AuthState.unauthenticated();
        return;
      }

      // Try fetching fresh profile from backend
      try {
        final user = await _authService.getMe();
        _handleLoadedUser(user);
      } catch (e) {
        // If offline, check if we have cached user
        final cached = await _storageService.getCachedUser();
        if (cached != null) {
          _handleLoadedUser(cached);
        } else {
          state = AuthState.unauthenticated();
        }
      }
    } catch (_) {
      state = AuthState.unauthenticated();
    }
  }

  void _handleLoadedUser(UserModel user) {
    if (user.accountStatus == AccountStatus.pendingVerification) {
      state = AuthState.pendingVerification(user.email);
    } else if (user.accountStatus == AccountStatus.pendingApproval) {
      state = AuthState.pendingApproval(user, email: user.email);
    } else if (user.accountStatus == AccountStatus.active) {
      state = AuthState.authenticated(user);
    } else {
      state = AuthState.error('Account status: ${user.accountStatus.displayName}');
    }
  }

  Future<bool> login(String email, String password) async {
    state = AuthState.loading();
    try {
      final response = await _authService.login(email: email, password: password);
      _handleLoadedUser(response.user);
      return true;
    } on PendingStatusException catch (e) {
      if (e.status == 'PENDING_VERIFICATION') {
        state = AuthState.pendingVerification(email);
      } else {
        state = AuthState.pendingApproval(null, email: email);
      }
      return false;
    } catch (e) {
      state = AuthState.error(e.toString());
      return false;
    }
  }

  Future<bool> signup({
    required String email,
    required String password,
    required String fullName,
    String? phone,
    required UserRole role,
  }) async {
    state = AuthState.loading();
    try {
      final user = await _authService.signup(
        email: email,
        password: password,
        fullName: fullName,
        phone: phone,
        role: role,
      );

      if (user.accountStatus == AccountStatus.pendingVerification) {
        state = AuthState.pendingVerification(user.email);
      } else {
        state = AuthState.pendingApproval(user, email: user.email);
      }
      return true;
    } catch (e) {
      state = AuthState.error(e.toString());
      return false;
    }
  }

  Future<void> logout() async {
    state = AuthState.loading();
    await _authService.logout();
    state = AuthState.unauthenticated();
  }

  void resetError() {
    if (state.status == AuthStatus.error) {
      state = AuthState.unauthenticated();
    }
  }
}

final authProvider = StateNotifierProvider<AuthNotifier, AuthState>((ref) {
  final authService = ref.watch(authApiServiceProvider);
  final storageService = ref.watch(secureStorageProvider);
  return AuthNotifier(
    authService: authService,
    storageService: storageService,
  );
});
