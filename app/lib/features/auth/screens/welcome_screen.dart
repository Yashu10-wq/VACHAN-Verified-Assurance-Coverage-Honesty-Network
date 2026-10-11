import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import '../../../core/theme/app_theme.dart';
import '../../../shared/widgets/app_button.dart';
import '../../../shared/widgets/glass_card.dart';

class WelcomeScreen extends StatelessWidget {
  const WelcomeScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.background,
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 24.0, vertical: 20.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.center,
            children: [
              const Spacer(flex: 1),

              // Top Logo Emblem
              Container(
                width: 76,
                height: 76,
                decoration: BoxDecoration(
                  gradient: AppTheme.primaryGradient,
                  borderRadius: BorderRadius.circular(24),
                  boxShadow: AppTheme.glowShadow,
                ),
                child: const Icon(
                  Icons.shield_outlined,
                  color: Colors.white,
                  size: 40,
                ),
              ),
              const SizedBox(height: 24),

              const Text(
                'InsureChain VoiceGuard',
                textAlign: TextAlign.center,
                style: TextStyle(
                  fontSize: 28,
                  fontWeight: FontWeight.w800,
                  color: AppTheme.textPrimary,
                  letterSpacing: -0.6,
                ),
              ),
              const SizedBox(height: 10),

              const Text(
                'Ethical insurance sales verified by conversational AI and anchored on blockchain.',
                textAlign: TextAlign.center,
                style: TextStyle(
                  fontSize: 15,
                  color: AppTheme.textSecondary,
                  height: 1.4,
                ),
              ),

              const Spacer(flex: 1),

              // Hero Feature Card
              GlassCard(
                padding: const EdgeInsets.all(20),
                child: Column(
                  children: [
                    _buildFeatureItem(
                      icon: Icons.mic_rounded,
                      gradient: AppTheme.purpleGradient,
                      title: 'Voice Session Verification',
                      subtitle: 'Real-time AI monitoring preventing deceptive sales.',
                    ),
                    const Divider(color: AppTheme.borderLight, height: 24),
                    _buildFeatureItem(
                      icon: Icons.lock_clock_rounded,
                      gradient: AppTheme.coralGradient,
                      title: 'Immutable Blockchain Trail',
                      subtitle: 'Cryptographic SHA-256 audit logs anchored on-chain.',
                    ),
                    const Divider(color: AppTheme.borderLight, height: 24),
                    _buildFeatureItem(
                      icon: Icons.verified_user_rounded,
                      gradient: AppTheme.cyanTileGradient,
                      title: 'Customer Confirmation Portal',
                      subtitle: 'Explicit policy review with zero hidden clauses.',
                    ),
                  ],
                ),
              ),

              const Spacer(flex: 2),

              // Action Buttons
              AppButton(
                label: 'Sign In to Your Account',
                onPressed: () => context.push('/login'),
                variant: AppButtonVariant.primaryGradient,
              ),
              const SizedBox(height: 14),

              AppButton(
                label: 'Create New Account',
                onPressed: () => context.push('/signup'),
                variant: AppButtonVariant.outlined,
              ),

              const SizedBox(height: 16),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildFeatureItem({
    required IconData icon,
    required LinearGradient gradient,
    required String title,
    required String subtitle,
  }) {
    return Row(
      children: [
        Container(
          width: 44,
          height: 44,
          decoration: BoxDecoration(
            gradient: gradient,
            borderRadius: BorderRadius.circular(14),
          ),
          child: Icon(icon, color: Colors.white, size: 22),
        ),
        const SizedBox(width: 14),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                title,
                style: const TextStyle(
                  fontSize: 14,
                  fontWeight: FontWeight.w700,
                  color: AppTheme.textPrimary,
                ),
              ),
              const SizedBox(height: 2),
              Text(
                subtitle,
                style: const TextStyle(
                  fontSize: 12,
                  color: AppTheme.textSecondary,
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }
}
