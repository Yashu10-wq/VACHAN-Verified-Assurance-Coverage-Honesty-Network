import 'package:flutter/material.dart';

class AppTheme {
  // Base Palette from visual reference
  static const Color background = Color(0xFFEAF5F9);
  static const Color backgroundSurface = Color(0xFFF3F9FB);
  static const Color cardWhite = Color(0xFFFFFFFF);
  static const Color darkTeal = Color(0xFF063743);
  static const Color darkTealHover = Color(0xFF094757);

  // Gradient definitions
  static const Color gradientSkyBlue = Color(0xFF4CA9F5);
  static const Color gradientCyan = Color(0xFF22C9E8);

  static const LinearGradient primaryGradient = LinearGradient(
    colors: [gradientSkyBlue, gradientCyan],
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
  );

  static const LinearGradient darkTealGradient = LinearGradient(
    colors: [Color(0xFF063743), Color(0xFF0D4B5C)],
    begin: Alignment.centerLeft,
    end: Alignment.centerRight,
  );

  // Feature icon squircle gradients
  static const LinearGradient purpleGradient = LinearGradient(
    colors: [Color(0xFF9D84F8), Color(0xFF7053E8)],
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
  );

  static const LinearGradient coralGradient = LinearGradient(
    colors: [Color(0xFFFF9E7D), Color(0xFFFF6A65)],
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
  );

  static const LinearGradient magentaGradient = LinearGradient(
    colors: [Color(0xFFE26BF5), Color(0xFFB534DF)],
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
  );

  static const LinearGradient cyanTileGradient = LinearGradient(
    colors: [Color(0xFF5AC8FA), Color(0xFF00A2D3)],
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
  );

  // Text & Semantic Colors
  static const Color textPrimary = Color(0xFF132A33);
  static const Color textSecondary = Color(0xFF6B8A99);
  static const Color textMuted = Color(0xFF9AB2BD);
  static const Color borderLight = Color(0xFFE1EEF2);
  static const Color success = Color(0xFF10B981);
  static const Color warning = Color(0xFFF59E0B);
  static const Color error = Color(0xFFEF4444);

  // Shadows
  static const List<BoxShadow> softCardShadow = [
    BoxShadow(
      color: Color(0x0C063743),
      blurRadius: 20,
      offset: Offset(0, 8),
      spreadRadius: -2,
    ),
    BoxShadow(
      color: Color(0x06000000),
      blurRadius: 6,
      offset: Offset(0, 2),
    ),
  ];

  static const List<BoxShadow> glowShadow = [
    BoxShadow(
      color: Color(0x2E22C9E8),
      blurRadius: 18,
      offset: Offset(0, 6),
    ),
  ];

  static ThemeData get lightTheme {
    return ThemeData(
      useMaterial3: true,
      brightness: Brightness.light,
      scaffoldBackgroundColor: background,
      colorScheme: const ColorScheme.light(
        primary: gradientSkyBlue,
        onPrimary: Colors.white,
        secondary: gradientCyan,
        onSecondary: Colors.white,
        surface: cardWhite,
        onSurface: textPrimary,
        error: error,
        onError: Colors.white,
      ),
      fontFamily: 'Roboto',
      appBarTheme: const AppBarTheme(
        backgroundColor: Colors.transparent,
        elevation: 0,
        scrolledUnderElevation: 0,
        centerTitle: false,
        iconTheme: IconThemeData(color: textPrimary),
        titleTextStyle: TextStyle(
          color: textPrimary,
          fontSize: 20,
          fontWeight: FontWeight.w700,
          letterSpacing: -0.2,
        ),
      ),
      cardTheme: CardThemeData(
        color: cardWhite,
        elevation: 0,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(24),
          side: const BorderSide(color: borderLight, width: 1),
        ),
        margin: EdgeInsets.zero,
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: cardWhite,
        hintStyle: const TextStyle(
          color: textMuted,
          fontSize: 15,
          fontWeight: FontWeight.w400,
        ),
        contentPadding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(24),
          borderSide: const BorderSide(color: borderLight),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(24),
          borderSide: const BorderSide(color: borderLight),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(24),
          borderSide: const BorderSide(color: gradientSkyBlue, width: 1.5),
        ),
        errorBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(24),
          borderSide: const BorderSide(color: error),
        ),
      ),
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          backgroundColor: darkTeal,
          foregroundColor: Colors.white,
          elevation: 0,
          padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 16),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(20),
          ),
          textStyle: const TextStyle(
            fontSize: 16,
            fontWeight: FontWeight.w600,
            letterSpacing: 0.1,
          ),
        ),
      ),
      bottomNavigationBarTheme: const BottomNavigationBarThemeData(
        backgroundColor: cardWhite,
        selectedItemColor: gradientSkyBlue,
        unselectedItemColor: textMuted,
        showUnselectedLabels: true,
        type: BottomNavigationBarType.fixed,
        elevation: 12,
      ),
    );
  }
}
