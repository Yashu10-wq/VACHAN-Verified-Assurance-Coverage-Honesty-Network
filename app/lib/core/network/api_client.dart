import 'package:dio/dio.dart';
import '../config/app_config.dart';
import '../errors/app_exception.dart';
import '../storage/secure_storage_service.dart';

class ApiClient {
  final Dio dio;
  final SecureStorageService storageService;

  ApiClient({
    Dio? customDio,
    SecureStorageService? customStorage,
  })  : dio = customDio ??
            Dio(
              BaseOptions(
                baseUrl: AppConfig.apiBaseUrl,
                connectTimeout: AppConfig.connectTimeout,
                receiveTimeout: AppConfig.receiveTimeout,
                headers: {
                  'Content-Type': 'application/json',
                  'Accept': 'application/json',
                },
              ),
            ),
        storageService = customStorage ?? SecureStorageService() {
    _setupInterceptors();
  }

  void updateBaseUrl(String newBaseUrl) {
    dio.options.baseUrl = newBaseUrl;
    AppConfig.apiBaseUrl = newBaseUrl;
  }

  void _setupInterceptors() {
    dio.interceptors.add(
      InterceptorsWrapper(
        onRequest: (options, handler) async {
          // Attach authorization token if present
          final token = await storageService.getAccessToken();
          if (token != null && token.isNotEmpty) {
            options.headers['Authorization'] = 'Bearer $token';
          }
          return handler.next(options);
        },
        onError: (DioException error, handler) async {
          // Safe 401 handling: attempt token refresh if refresh token exists
          if (error.response?.statusCode == 401 &&
              !error.requestOptions.path.contains('/auth/login') &&
              !error.requestOptions.path.contains('/auth/refresh')) {
            final refreshToken = await storageService.getRefreshToken();
            if (refreshToken != null && refreshToken.isNotEmpty) {
              try {
                final refreshResponse = await dio.post(
                  '/auth/refresh',
                  data: {'refresh_token': refreshToken},
                  options: Options(headers: {}), // Don't send stale expired Bearer
                );
                if (refreshResponse.statusCode == 200) {
                  final data = refreshResponse.data as Map<String, dynamic>;
                  final newAccessToken = data['access_token'] as String;
                  final newRefreshToken = data['refresh_token'] as String;

                  await storageService.saveTokens(
                    accessToken: newAccessToken,
                    refreshToken: newRefreshToken,
                  );

                  // Retry original request with new token
                  final retryOptions = error.requestOptions;
                  retryOptions.headers['Authorization'] = 'Bearer $newAccessToken';
                  final retryResponse = await dio.fetch(retryOptions);
                  return handler.resolve(retryResponse);
                }
              } catch (_) {
                // Refresh failed; clear stored session
                await storageService.clearSession();
              }
            } else {
              await storageService.clearSession();
            }
          }
          return handler.next(error);
        },
      ),
    );
  }

  AppException mapDioError(dynamic error) {
    if (error is AppException) return error;

    if (error is DioException) {
      if (error.type == DioExceptionType.connectionTimeout ||
          error.type == DioExceptionType.receiveTimeout ||
          error.type == DioExceptionType.sendTimeout ||
          error.type == DioExceptionType.connectionError) {
        return const NetworkException(
          'Cannot reach the server. Please check your connection or API server status.',
        );
      }

      final response = error.response;
      if (response != null) {
        final statusCode = response.statusCode;
        final data = response.data;
        String message = 'An unexpected error occurred.';

        if (data is Map<String, dynamic> && data.containsKey('detail')) {
          final detail = data['detail'];
          if (detail is String) {
            message = detail;
          } else if (detail is List && detail.isNotEmpty) {
            final first = detail[0];
            if (first is Map && first.containsKey('msg')) {
              message = first['msg'].toString();
            } else {
              message = detail.toString();
            }
          }
        }

        if (statusCode == 401) {
          return AuthException(message, statusCode: statusCode);
        } else if (statusCode == 403) {
          if (message.contains('Email verification') ||
              message.contains('verification required')) {
            return PendingStatusException(
              message,
              status: 'PENDING_VERIFICATION',
            );
          }
          if (message.contains('awaiting') ||
              message.contains('review and approval') ||
              message.contains('PENDING_APPROVAL')) {
            return PendingStatusException(
              message,
              status: 'PENDING_APPROVAL',
            );
          }
          return AuthException(message, statusCode: statusCode);
        } else if (statusCode == 422 || statusCode == 400) {
          return ValidationAppException(message, details: data);
        } else if (statusCode == 409) {
          return ValidationAppException(message, details: data);
        } else if (statusCode != null && statusCode >= 500) {
          return ServerException(message);
        }
        return AppException(message, statusCode: statusCode);
      }
    }

    return AppException(error.toString());
  }
}
