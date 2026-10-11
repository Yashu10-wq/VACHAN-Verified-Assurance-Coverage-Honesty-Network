import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../features/agent/screens/agent_home_screen.dart';
import '../../features/agent/screens/new_sales_session_screen.dart';
import '../../features/agent/screens/sales_session_detail_screen.dart';
import '../../features/authority/screens/authority_claim_review_screen.dart';
import '../../features/authority/screens/authority_home_screen.dart';
import '../../features/auth/models/user_model.dart';
import '../../features/auth/providers/auth_provider.dart';
import '../../features/auth/screens/account_pending_screen.dart';
import '../../features/auth/screens/forgot_password_screen.dart';
import '../../features/auth/screens/login_screen.dart';
import '../../features/auth/screens/signup_screen.dart';
import '../../features/auth/screens/splash_screen.dart';
import '../../features/auth/screens/welcome_screen.dart';
import '../../features/customer/screens/claim_detail_screen.dart';
import '../../features/customer/screens/claims_list_screen.dart';
import '../../features/customer/screens/customer_help_screen.dart';
import '../../features/customer/screens/customer_home_screen.dart';
import '../../features/customer/screens/customer_more_screen.dart';
import '../../features/customer/screens/customer_policies_screen.dart';
import '../../features/customer/screens/policy_detail_screen.dart';
import '../../features/customer/screens/submit_claim_screen.dart';
import '../../features/customer/screens/verification_report_screen.dart';
import '../../features/integrity/screens/blockchain_integrity_screen.dart';

final appRouterProvider = Provider<GoRouter>((ref) {
  final authState = ref.watch(authProvider);

  return GoRouter(
    initialLocation: '/splash',
    redirect: (BuildContext context, GoRouterState state) {
      final currentLoc = state.uri.path;
      final isSplash = currentLoc == '/splash';
      final isAuthScreen = currentLoc == '/login' ||
          currentLoc == '/signup' ||
          currentLoc == '/welcome' ||
          currentLoc == '/forgot-password';
      final isPendingScreen = currentLoc == '/pending-account';

      // 1. Session check in progress
      if (authState.status == AuthStatus.initial ||
          authState.status == AuthStatus.loading) {
        return isSplash ? null : '/splash';
      }

      // 2. Pending verification or approval states
      if (authState.status == AuthStatus.pendingVerification ||
          authState.status == AuthStatus.pendingApproval) {
        return isPendingScreen ? null : '/pending-account';
      }

      // 3. Authenticated session
      if (authState.isAuthenticated) {
        final role = authState.user!.role;
        String targetHome = '/customer-home';
        if (role == UserRole.insuranceAgent) {
          targetHome = '/agent-home';
        } else if (role == UserRole.approvalAuthority) {
          targetHome = '/authority-home';
        }

        // If currently on splash or any auth/pending screen, navigate to role-specific home
        if (isSplash || isAuthScreen || isPendingScreen) {
          return targetHome;
        }

        // Role-based route guard
        final isCustomerRoute = currentLoc == '/customer-home' ||
            currentLoc == '/policies' ||
            currentLoc.startsWith('/policy-detail') ||
            currentLoc == '/claims' ||
            currentLoc.startsWith('/claim-detail') ||
            currentLoc == '/submit-claim' ||
            currentLoc.startsWith('/verification-report') ||
            currentLoc == '/help' ||
            currentLoc == '/more';

        if (isCustomerRoute && role != UserRole.customer) {
          return targetHome;
        }

        final isAgentRoute = currentLoc == '/agent-home' || currentLoc.startsWith('/agent/');
        if (isAgentRoute && role != UserRole.insuranceAgent) {
          return targetHome;
        }

        final isAuthorityRoute = currentLoc == '/authority-home' || currentLoc.startsWith('/authority/');
        if (isAuthorityRoute && role != UserRole.approvalAuthority) {
          return targetHome;
        }

        return null;
      }

      // 4. Unauthenticated state
      if (isSplash) {
        return '/welcome';
      }

      // Prevent unauthorized access to protected routes
      if (!isAuthScreen) {
        return '/welcome';
      }

      return null;
    },
    routes: [
      GoRoute(
        path: '/splash',
        builder: (context, state) => const SplashScreen(),
      ),
      GoRoute(
        path: '/welcome',
        builder: (context, state) => const WelcomeScreen(),
      ),
      GoRoute(
        path: '/login',
        builder: (context, state) => const LoginScreen(),
      ),
      GoRoute(
        path: '/signup',
        builder: (context, state) => const SignupScreen(),
      ),
      GoRoute(
        path: '/forgot-password',
        builder: (context, state) => const ForgotPasswordScreen(),
      ),
      GoRoute(
        path: '/pending-account',
        builder: (context, state) => const AccountPendingScreen(),
      ),
      // Customer Routes
      GoRoute(
        path: '/customer-home',
        builder: (context, state) => const CustomerHomeScreen(),
      ),
      GoRoute(
        path: '/policies',
        builder: (context, state) => const CustomerPoliciesScreen(),
      ),
      GoRoute(
        path: '/policy-detail/:id',
        builder: (context, state) {
          final policyId = state.pathParameters['id'] ?? '';
          return PolicyDetailScreen(policyId: policyId);
        },
      ),
      GoRoute(
        path: '/claims',
        builder: (context, state) => const ClaimsListScreen(),
      ),
      GoRoute(
        path: '/claim-detail/:id',
        builder: (context, state) {
          final claimId = state.pathParameters['id'] ?? '';
          return ClaimDetailScreen(claimId: claimId);
        },
      ),
      GoRoute(
        path: '/submit-claim',
        builder: (context, state) => const SubmitClaimScreen(),
      ),
      GoRoute(
        path: '/verification-report/:id',
        builder: (context, state) {
          final reportId = state.pathParameters['id'] ?? '';
          return VerificationReportScreen(reportId: reportId);
        },
      ),
      GoRoute(
        path: '/help',
        builder: (context, state) => const CustomerHelpScreen(),
      ),
      GoRoute(
        path: '/more',
        builder: (context, state) => const CustomerMoreScreen(),
      ),
      // Agent Routes
      GoRoute(
        path: '/agent-home',
        builder: (context, state) => const AgentHomeScreen(),
      ),
      GoRoute(
        path: '/agent/new-session',
        builder: (context, state) => const NewSalesSessionScreen(),
      ),
      GoRoute(
        path: '/agent/session/:id',
        builder: (context, state) {
          final sessionId = state.pathParameters['id'] ?? '';
          return SalesSessionDetailScreen(sessionId: sessionId);
        },
      ),
      // Authority Routes
      GoRoute(
        path: '/authority-home',
        builder: (context, state) => const AuthorityHomeScreen(),
      ),
      GoRoute(
        path: '/authority/claim/:id',
        builder: (context, state) {
          final claimId = state.pathParameters['id'] ?? '';
          return AuthorityClaimReviewScreen(claimId: claimId);
        },
      ),
      GoRoute(
        path: '/integrity',
        builder: (context, state) {
          final eventId = state.uri.queryParameters['event_id'];
          return BlockchainIntegrityScreen(initialEventId: eventId);
        },
      ),
    ],
  );
});
