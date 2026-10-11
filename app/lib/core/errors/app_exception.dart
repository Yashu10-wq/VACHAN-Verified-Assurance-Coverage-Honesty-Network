class AppException implements Exception {
  final String message;
  final int? statusCode;
  final dynamic details;

  const AppException(this.message, {this.statusCode, this.details});

  @override
  String toString() => message;
}

class NetworkException extends AppException {
  const NetworkException([
    super.message = 'Unable to connect to the server. Please check your internet connection.',
  ]);
}

class AuthException extends AppException {
  const AuthException(super.message, {super.statusCode = 401});
}

class PendingStatusException extends AppException {
  final String status;
  const PendingStatusException(super.message, {required this.status})
      : super(statusCode: 403);
}

class ValidationAppException extends AppException {
  const ValidationAppException(super.message, {super.details})
      : super(statusCode: 422);
}

class ServerException extends AppException {
  const ServerException([
    super.message = 'A server error occurred. Please try again later.',
  ]) : super(statusCode: 500);
}
