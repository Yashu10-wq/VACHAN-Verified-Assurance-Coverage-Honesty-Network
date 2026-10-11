import '../../../core/network/api_client.dart';
import '../models/user_model.dart';

class AuthResponse {
  final String accessToken;
  final String refreshToken;
  final int expiresInMinutes;
  final UserModel user;

  const AuthResponse({
    required this.accessToken,
    required this.refreshToken,
    required this.expiresInMinutes,
    required this.user,
  });

  factory AuthResponse.fromJson(Map<String, dynamic> json) {
    return AuthResponse(
      accessToken: json['access_token'] as String,
      refreshToken: json['refresh_token'] as String,
      expiresInMinutes: json['expires_in_minutes'] as int? ?? 60,
      user: UserModel.fromJson(json['user'] as Map<String, dynamic>),
    );
  }
}

class AuthApiService {
  final ApiClient apiClient;

  AuthApiService({ApiClient? client}) : apiClient = client ?? ApiClient();

  Future<AuthResponse> login({
    required String email,
    required String password,
  }) async {
    try {
      final response = await apiClient.dio.post(
        '/auth/login',
        data: {
          'email': email.trim(),
          'password': password,
        },
      );
      final authResponse = AuthResponse.fromJson(response.data as Map<String, dynamic>);
      await apiClient.storageService.saveTokens(
        accessToken: authResponse.accessToken,
        refreshToken: authResponse.refreshToken,
      );
      await apiClient.storageService.saveUser(authResponse.user);
      return authResponse;
    } catch (e) {
      throw apiClient.mapDioError(e);
    }
  }

  Future<UserModel> signup({
    required String email,
    required String password,
    required String fullName,
    String? phone,
    required UserRole role,
  }) async {
    try {
      final response = await apiClient.dio.post(
        '/auth/signup',
        data: {
          'email': email.trim(),
          'password': password,
          'full_name': fullName.trim(),
          if (phone != null && phone.trim().isNotEmpty) 'phone': phone.trim(),
          'role': role.value,
        },
      );
      return UserModel.fromJson(response.data as Map<String, dynamic>);
    } catch (e) {
      throw apiClient.mapDioError(e);
    }
  }

  Future<void> logout() async {
    try {
      final refreshToken = await apiClient.storageService.getRefreshToken();
      if (refreshToken != null) {
        await apiClient.dio.post(
          '/auth/logout',
          data: {'refresh_token': refreshToken},
        );
      }
    } catch (_) {
      // Best-effort logout on backend; always clear local session
    } finally {
      await apiClient.storageService.clearSession();
    }
  }

  Future<UserModel> getMe() async {
    try {
      final response = await apiClient.dio.get('/auth/me');
      final user = UserModel.fromJson(response.data as Map<String, dynamic>);
      await apiClient.storageService.saveUser(user);
      return user;
    } catch (e) {
      throw apiClient.mapDioError(e);
    }
  }

  Future<String> verifyEmail(String token) async {
    try {
      final response = await apiClient.dio.post(
        '/auth/verify-email',
        data: {'token': token.trim()},
      );
      final data = response.data as Map<String, dynamic>;
      return data['message'] as String? ?? 'Email verified successfully.';
    } catch (e) {
      throw apiClient.mapDioError(e);
    }
  }

  Future<String> resendVerification(String email) async {
    try {
      final response = await apiClient.dio.post(
        '/auth/resend-verification',
        data: {'email': email.trim()},
      );
      final data = response.data as Map<String, dynamic>;
      return data['message'] as String? ?? 'Verification email resent.';
    } catch (e) {
      throw apiClient.mapDioError(e);
    }
  }

  Future<String> requestPasswordReset(String email) async {
    try {
      final response = await apiClient.dio.post(
        '/auth/password-reset/request',
        data: {'email': email.trim()},
      );
      final data = response.data as Map<String, dynamic>;
      return data['message'] as String? ?? 'Password reset email sent.';
    } catch (e) {
      throw apiClient.mapDioError(e);
    }
  }

  Future<String> confirmPasswordReset({
    required String token,
    required String newPassword,
  }) async {
    try {
      final response = await apiClient.dio.post(
        '/auth/password-reset/confirm',
        data: {
          'token': token.trim(),
          'new_password': newPassword,
        },
      );
      final data = response.data as Map<String, dynamic>;
      return data['message'] as String? ?? 'Password updated successfully.';
    } catch (e) {
      throw apiClient.mapDioError(e);
    }
  }
}
