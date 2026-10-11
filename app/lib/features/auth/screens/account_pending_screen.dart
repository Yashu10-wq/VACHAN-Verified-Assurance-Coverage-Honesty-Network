import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../core/theme/app_theme.dart';
import '../../../shared/widgets/app_button.dart';
import '../../../shared/widgets/app_text_field.dart';
import '../../../shared/widgets/glass_card.dart';
import '../providers/auth_provider.dart';

class AccountPendingScreen extends ConsumerStatefulWidget {
  const AccountPendingScreen({super.key});

  @override
  ConsumerState<AccountPendingScreen> createState() => _AccountPendingScreenState();
}

class _AccountPendingScreenState extends ConsumerState<AccountPendingScreen> {
  final _tokenController = TextEditingController();
  bool _isLoading = false;
  String? _statusMessage;
  String? _errorMessage;

  @override
  void dispose() {
    _tokenController.dispose();
    super.dispose();
  }

  Future<void> _handleVerifyToken() async {
    final token = _tokenController.text.trim();
    if (token.isEmpty) {
      setState(() => _errorMessage = 'Please enter your verification token.');
      return;
    }

    setState(() {
      _isLoading = true;
      _errorMessage = null;
      _statusMessage = null;
    });

    try {
      final authService = ref.read(authApiServiceProvider);
      final msg = await authService.verifyEmail(token);
      setState(() => _statusMessage = msg);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(msg),
            backgroundColor: AppTheme.success,
          ),
        );
        Future.delayed(const Duration(seconds: 2), () {
          if (mounted) context.go('/login');
        });
      }
    } catch (e) {
      setState(() => _errorMessage = e.toString());
    } finally {
      setState(() => _isLoading = false);
    }
  }

  Future<void> _handleResendVerification() async {
    final authState = ref.read(authProvider);
    final email = authState.pendingEmail ?? authState.user?.email;
    if (email == null || email.isEmpty) {
      setState(() => _errorMessage = 'Email address not found. Please log in again.');
      return;
    }

    setState(() {
      _isLoading = true;
      _errorMessage = null;
      _statusMessage = null;
    });

    try {
      final authService = ref.read(authApiServiceProvider);
      final msg = await authService.resendVerification(email);
      setState(() => _statusMessage = msg);
    } catch (e) {
      setState(() => _errorMessage = e.toString());
    } finally {
      setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final authState = ref.watch(authProvider);
    final isPendingApproval = authState.status == AuthStatus.pendingApproval;
    final displayEmail = authState.pendingEmail ?? authState.user?.email ?? 'your email';

    return Scaffold(
      backgroundColor: AppTheme.background,
      appBar: AppBar(
        title: const Text('Account Status'),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_ios_new_rounded, size: 20),
          onPressed: () => context.go('/login'),
        ),
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.symmetric(horizontal: 24.0, vertical: 16.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.center,
            children: [
              const SizedBox(height: 20),
              Container(
                width: 78,
                height: 78,
                decoration: BoxDecoration(
                  color: isPendingApproval ? AppTheme.darkTeal : AppTheme.gradientSkyBlue.withValues(alpha: 0.15),
                  shape: BoxShape.circle,
                ),
                child: Icon(
                  isPendingApproval ? Icons.hourglass_top_rounded : Icons.mark_email_unread_rounded,
                  color: isPendingApproval ? Colors.white : AppTheme.gradientSkyBlue,
                  size: 40,
                ),
              ),
              const SizedBox(height: 24),

              Text(
                isPendingApproval ? 'Awaiting Authority Approval' : 'Verify Your Email',
                textAlign: TextAlign.center,
                style: const TextStyle(
                  fontSize: 24,
                  fontWeight: FontWeight.w800,
                  color: AppTheme.textPrimary,
                  letterSpacing: -0.4,
                ),
              ),
              const SizedBox(height: 10),

              Text(
                isPendingApproval
                    ? 'Insurance Agent accounts require compliance verification. An administrator is currently reviewing your registration.'
                    : 'We sent a verification link to $displayEmail. Please enter your verification token below or check your inbox.',
                textAlign: TextAlign.center,
                style: const TextStyle(
                  fontSize: 14,
                  color: AppTheme.textSecondary,
                  height: 1.4,
                ),
              ),

              const SizedBox(height: 28),

              if (_errorMessage != null) ...[
                Container(
                  margin: const EdgeInsets.only(bottom: 20),
                  padding: const EdgeInsets.all(14),
                  decoration: BoxDecoration(
                    color: AppTheme.error.withValues(alpha: 0.1),
                    borderRadius: BorderRadius.circular(16),
                    border: Border.all(color: AppTheme.error.withValues(alpha: 0.3)),
                  ),
                  child: Row(
                    children: [
                      const Icon(Icons.error_outline_rounded, color: AppTheme.error, size: 20),
                      const SizedBox(width: 10),
                      Expanded(
                        child: Text(
                          _errorMessage!,
                          style: const TextStyle(
                            color: AppTheme.error,
                            fontSize: 13,
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
              ],

              if (_statusMessage != null) ...[
                Container(
                  margin: const EdgeInsets.only(bottom: 20),
                  padding: const EdgeInsets.all(14),
                  decoration: BoxDecoration(
                    color: AppTheme.success.withValues(alpha: 0.12),
                    borderRadius: BorderRadius.circular(16),
                    border: Border.all(color: AppTheme.success.withValues(alpha: 0.3)),
                  ),
                  child: Row(
                    children: [
                      const Icon(Icons.check_circle_outline_rounded, color: AppTheme.success, size: 20),
                      const SizedBox(width: 10),
                      Expanded(
                        child: Text(
                          _statusMessage!,
                          style: const TextStyle(
                            color: AppTheme.success,
                            fontSize: 13,
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
              ],

              if (!isPendingApproval) ...[
                GlassCard(
                  padding: const EdgeInsets.all(22),
                  child: Column(
                    children: [
                      AppTextField(
                        controller: _tokenController,
                        labelText: 'Verification Token',
                        hintText: 'Paste token from verification email',
                        prefixIcon: const Icon(Icons.key_rounded, color: AppTheme.textMuted, size: 20),
                      ),
                      const SizedBox(height: 20),
                      AppButton(
                        label: 'Verify Email',
                        isLoading: _isLoading,
                        onPressed: _handleVerifyToken,
                        variant: AppButtonVariant.primaryGradient,
                      ),
                      const SizedBox(height: 14),
                      AppButton(
                        label: 'Resend Verification Email',
                        isLoading: _isLoading,
                        onPressed: _handleResendVerification,
                        variant: AppButtonVariant.outlined,
                      ),
                    ],
                  ),
                ),
              ] else ...[
                GlassCard(
                  padding: const EdgeInsets.all(22),
                  child: Column(
                    children: [
                      const Icon(Icons.security_update_good_rounded, color: AppTheme.darkTeal, size: 36),
                      const SizedBox(height: 14),
                      const Text(
                        'Compliance Audit Active',
                        style: TextStyle(
                          fontSize: 16,
                          fontWeight: FontWeight.w700,
                          color: AppTheme.textPrimary,
                        ),
                      ),
                      const SizedBox(height: 6),
                      const Text(
                        'As per insurance regulatory safeguards, agent credentials and role permissions are granted after internal review.',
                        textAlign: TextAlign.center,
                        style: TextStyle(
                          fontSize: 13,
                          color: AppTheme.textSecondary,
                        ),
                      ),
                      const SizedBox(height: 22),
                      AppButton(
                        label: 'Check Approval Status',
                        isLoading: _isLoading,
                        onPressed: () async {
                          setState(() => _isLoading = true);
                          await ref.read(authProvider.notifier).checkSession();
                          setState(() => _isLoading = false);
                        },
                        variant: AppButtonVariant.darkTeal,
                      ),
                    ],
                  ),
                ),
              ],

              const SizedBox(height: 28),
              TextButton(
                onPressed: () {
                  ref.read(authProvider.notifier).logout();
                  context.go('/login');
                },
                child: const Text(
                  'Return to Sign In',
                  style: TextStyle(
                    fontSize: 14,
                    fontWeight: FontWeight.w600,
                    color: AppTheme.gradientSkyBlue,
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
