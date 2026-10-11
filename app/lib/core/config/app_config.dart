import 'dart:io' show Platform;
import 'package:flutter/foundation.dart';

/// Central application configuration.
/// The backend API base URL can be supplied at compile time via:
/// `--dart-define=API_BASE_URL=https://api.yourdomain.com/api/v1`
class AppConfig {
  static const String _envBaseUrl = String.fromEnvironment('API_BASE_URL');

  static String get defaultBaseUrl {
    if (_envBaseUrl.isNotEmpty) {
      return _envBaseUrl;
    }
    // Web or desktop platforms point to localhost
    if (kIsWeb) {
      return 'http://localhost:8000/api/v1';
    }
    try {
      if (Platform.isAndroid) {
        // Standard Android emulator loopback to host
        return 'http://10.0.2.2:8000/api/v1';
      }
    } catch (_) {
      // Platform check may fail on web
    }
    return 'http://localhost:8000/api/v1';
  }

  static String apiBaseUrl = defaultBaseUrl;

  static const Duration connectTimeout = Duration(seconds: 15);
  static const Duration receiveTimeout = Duration(seconds: 20);

  static const String appName = 'InsureChain VoiceGuard';
  static const String appTagline = 'Verifiable Trust & AI Voice Assurance';
}
