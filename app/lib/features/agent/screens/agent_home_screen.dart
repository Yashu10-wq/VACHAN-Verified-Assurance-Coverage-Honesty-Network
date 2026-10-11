import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../core/theme/app_theme.dart';
import '../../../shared/widgets/glass_card.dart';
import '../../../shared/widgets/status_badge.dart';
import '../../auth/models/user_model.dart';
import '../../auth/providers/auth_provider.dart';
import '../models/sales_session_model.dart';
import '../providers/agent_provider.dart';

class AgentHomeScreen extends ConsumerStatefulWidget {
  const AgentHomeScreen({super.key});

  @override
  ConsumerState<AgentHomeScreen> createState() => _AgentHomeScreenState();
}

class _AgentHomeScreenState extends ConsumerState<AgentHomeScreen> {
  final _searchController = TextEditingController();
  String _selectedFilter = 'ALL';

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final authState = ref.watch(authProvider);
    final user = authState.user;
    final sessionsState = ref.watch(salesSessionsListProvider);

    final isPendingApproval = user?.accountStatus == AccountStatus.pendingApproval;

    return Scaffold(
      backgroundColor: AppTheme.background,
      appBar: AppBar(
        title: const Text('Agent Workbench'),
        automaticallyImplyLeading: false,
        actions: [
          IconButton(
            icon: const Icon(Icons.hub_rounded, color: AppTheme.gradientSkyBlue),
            tooltip: 'Blockchain Integrity',
            onPressed: () => context.push('/integrity'),
          ),
          IconButton(
            icon: const Icon(Icons.refresh_rounded),
            onPressed: () {
              ref.read(salesSessionsListProvider.notifier).fetchSessions(status: _selectedFilter);
            },
          ),
          IconButton(
            icon: const Icon(Icons.logout_rounded, color: AppTheme.error),
            onPressed: () async {
              final confirm = await showDialog<bool>(
                context: context,
                builder: (ctx) => AlertDialog(
                  title: const Text('Sign Out'),
                  content: const Text('Are you sure you want to end your current agent session?'),
                  actions: [
                    TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text('Cancel')),
                    ElevatedButton(
                      onPressed: () => Navigator.pop(ctx, true),
                      style: ElevatedButton.styleFrom(backgroundColor: AppTheme.error),
                      child: const Text('Sign Out'),
                    ),
                  ],
                ),
              );
              if (confirm == true) {
                await ref.read(authProvider.notifier).logout();
                if (context.mounted) context.go('/login');
              }
            },
          ),
        ],
      ),
      floatingActionButton: isPendingApproval
          ? null
          : FloatingActionButton.extended(
              backgroundColor: AppTheme.darkTeal,
              foregroundColor: Colors.white,
              icon: const Icon(Icons.mic_rounded),
              label: const Text('New Sales Session', style: TextStyle(fontWeight: FontWeight.w700)),
              onPressed: () => context.push('/agent/new-session'),
            ),
      body: SafeArea(
        child: RefreshIndicator(
          color: AppTheme.gradientSkyBlue,
          onRefresh: () async {
            await ref.read(salesSessionsListProvider.notifier).fetchSessions(status: _selectedFilter);
          },
          child: SingleChildScrollView(
            physics: const AlwaysScrollableScrollPhysics(),
            padding: const EdgeInsets.symmetric(horizontal: 20.0, vertical: 12.0),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // Agent Profile Header Card
                GlassCard(
                  padding: const EdgeInsets.all(20),
                  child: Row(
                    children: [
                      Container(
                        width: 54,
                        height: 54,
                        decoration: BoxDecoration(
                          gradient: AppTheme.purpleGradient,
                          borderRadius: BorderRadius.circular(16),
                        ),
                        child: const Center(
                          child: Icon(Icons.support_agent_rounded, color: Colors.white, size: 28),
                        ),
                      ),
                      const SizedBox(width: 16),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              user?.fullName.isNotEmpty == true ? user!.fullName : 'Insurance Agent',
                              style: const TextStyle(
                                fontSize: 17,
                                fontWeight: FontWeight.w800,
                                color: AppTheme.textPrimary,
                              ),
                            ),
                            const SizedBox(height: 2),
                            Text(
                              user?.email ?? '',
                              style: const TextStyle(fontSize: 12, color: AppTheme.textSecondary),
                            ),
                            const SizedBox(height: 6),
                            StatusBadge.fromStatus(user?.accountStatus.value ?? 'ACTIVE'),
                          ],
                        ),
                      ),
                    ],
                  ),
                ),

                const SizedBox(height: 16),

                // Restricted Access Banner if Pending Approval
                if (isPendingApproval) ...[
                  Container(
                    padding: const EdgeInsets.all(16),
                    decoration: BoxDecoration(
                      color: AppTheme.warning.withValues(alpha: 0.12),
                      borderRadius: BorderRadius.circular(16),
                      border: Border.all(color: AppTheme.warning.withValues(alpha: 0.3)),
                    ),
                    child: const Row(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Icon(Icons.lock_clock_rounded, color: AppTheme.warning, size: 24),
                        SizedBox(width: 12),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                'Account Pending Authority Approval',
                                style: TextStyle(
                                  fontSize: 14,
                                  fontWeight: FontWeight.w800,
                                  color: Color(0xFF92400E),
                                ),
                              ),
                              SizedBox(height: 4),
                              Text(
                                'Your agent credentials have been registered and are currently awaiting review by an Approval Authority administrator. Privileged sales session recording is disabled until approval is granted.',
                                style: TextStyle(fontSize: 12, color: Color(0xFF92400E), height: 1.35),
                              ),
                            ],
                          ),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 16),
                ],

                // Metrics Overview Grid
                Row(
                  children: [
                    Expanded(
                      child: _buildMetricTile(
                        icon: Icons.record_voice_over_rounded,
                        label: 'Total Sessions',
                        value: '${sessionsState.sessions.length}',
                        color: AppTheme.gradientSkyBlue,
                      ),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: _buildMetricTile(
                        icon: Icons.check_circle_rounded,
                        label: 'Transcribed',
                        value: '${sessionsState.sessions.where((s) => s.isCompleted).length}',
                        color: AppTheme.success,
                      ),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: _buildMetricTile(
                        icon: Icons.hourglass_top_rounded,
                        label: 'Processing',
                        value: '${sessionsState.sessions.where((s) => s.isProcessing).length}',
                        color: AppTheme.warning,
                      ),
                    ),
                  ],
                ),

                const SizedBox(height: 20),

                // Quick Action Cards
                const Text(
                  'Quick Actions',
                  style: TextStyle(
                    fontSize: 17,
                    fontWeight: FontWeight.w800,
                    color: AppTheme.textPrimary,
                    letterSpacing: -0.3,
                  ),
                ),
                const SizedBox(height: 10),

                Row(
                  children: [
                    Expanded(
                      child: _buildActionCard(
                        icon: Icons.fiber_smart_record_rounded,
                        title: 'New Session',
                        subtitle: 'Record & Consent',
                        color: AppTheme.darkTeal,
                        onTap: isPendingApproval ? null : () => context.push('/agent/new-session'),
                      ),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: _buildActionCard(
                        icon: Icons.transcribe_rounded,
                        title: 'Transcripts',
                        subtitle: 'ElevenLabs Scribe',
                        color: const Color(0xFF0284C7),
                        onTap: () {
                          setState(() => _selectedFilter = 'COMPLETED');
                          ref.read(salesSessionsListProvider.notifier).setStatusFilter('COMPLETED');
                        },
                      ),
                    ),
                  ],
                ),

                const SizedBox(height: 24),

                // Search Bar
                Container(
                  height: 48,
                  decoration: BoxDecoration(
                    color: Colors.white,
                    borderRadius: BorderRadius.circular(24),
                    border: Border.all(color: AppTheme.borderLight),
                  ),
                  child: Row(
                    children: [
                      const SizedBox(width: 14),
                      const Icon(Icons.search_rounded, color: AppTheme.textMuted, size: 20),
                      const SizedBox(width: 10),
                      Expanded(
                        child: TextField(
                          controller: _searchController,
                          onChanged: (val) {
                            ref.read(salesSessionsListProvider.notifier).setSearchQuery(val.trim());
                          },
                          decoration: const InputDecoration(
                            hintText: 'Search session ID or customer UUID...',
                            border: InputBorder.none,
                            enabledBorder: InputBorder.none,
                            focusedBorder: InputBorder.none,
                            contentPadding: EdgeInsets.zero,
                          ),
                        ),
                      ),
                      if (_searchController.text.isNotEmpty) ...[
                        IconButton(
                          icon: const Icon(Icons.clear_rounded, size: 18),
                          onPressed: () {
                            _searchController.clear();
                            ref.read(salesSessionsListProvider.notifier).setSearchQuery('');
                          },
                        ),
                      ],
                    ],
                  ),
                ),

                const SizedBox(height: 12),

                // Status Filter Chips
                SingleChildScrollView(
                  scrollDirection: Axis.horizontal,
                  child: Row(
                    children: [
                      _buildFilterChip('ALL', 'All Sessions'),
                      const SizedBox(width: 8),
                      _buildFilterChip('COMPLETED', 'Transcribed'),
                      const SizedBox(width: 8),
                      _buildFilterChip('PROCESSING', 'Processing'),
                      const SizedBox(width: 8),
                      _buildFilterChip('RECORDED', 'Recorded'),
                      const SizedBox(width: 8),
                      _buildFilterChip('FAILED', 'Failed'),
                    ],
                  ),
                ),

                const SizedBox(height: 16),

                // Sessions List
                if (sessionsState.isLoading) ...[
                  const Center(
                    child: Padding(
                      padding: EdgeInsets.all(32.0),
                      child: CircularProgressIndicator(
                        valueColor: AlwaysStoppedAnimation<Color>(AppTheme.gradientSkyBlue),
                      ),
                    ),
                  ),
                ] else if (sessionsState.errorMessage != null) ...[
                  Center(
                    child: Padding(
                      padding: const EdgeInsets.all(24.0),
                      child: Column(
                        children: [
                          const Icon(Icons.error_outline_rounded, color: AppTheme.error, size: 36),
                          const SizedBox(height: 10),
                          Text(sessionsState.errorMessage!, textAlign: TextAlign.center),
                          const SizedBox(height: 12),
                          ElevatedButton(
                            onPressed: () {
                              ref.read(salesSessionsListProvider.notifier).fetchSessions(status: _selectedFilter);
                            },
                            child: const Text('Retry'),
                          ),
                        ],
                      ),
                    ),
                  ),
                ] else if (sessionsState.filteredSessions.isEmpty) ...[
                  GlassCard(
                    padding: const EdgeInsets.all(28),
                    child: Center(
                      child: Column(
                        children: [
                          const Icon(Icons.graphic_eq_rounded, size: 40, color: AppTheme.textMuted),
                          const SizedBox(height: 12),
                          const Text(
                            'No Sales Sessions Found',
                            style: TextStyle(fontSize: 16, fontWeight: FontWeight.w700, color: AppTheme.textPrimary),
                          ),
                          const SizedBox(height: 4),
                          const Text(
                            'Sales conversations recorded with explicit customer consent appear here.',
                            textAlign: TextAlign.center,
                            style: TextStyle(fontSize: 12, color: AppTheme.textSecondary),
                          ),
                          if (!isPendingApproval) ...[
                            const SizedBox(height: 16),
                            ElevatedButton.icon(
                              onPressed: () => context.push('/agent/new-session'),
                              icon: const Icon(Icons.add_rounded, size: 18),
                              label: const Text('Start First Session'),
                              style: ElevatedButton.styleFrom(backgroundColor: AppTheme.darkTeal),
                            ),
                          ],
                        ],
                      ),
                    ),
                  ),
                ] else ...[
                  ...sessionsState.filteredSessions.map((session) => _buildSessionCard(session)),
                ],

                const SizedBox(height: 36),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildMetricTile({
    required IconData icon,
    required String label,
    required String value,
    required Color color,
  }) {
    return GlassCard(
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 14),
      borderRadius: 18,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            width: 32,
            height: 32,
            decoration: BoxDecoration(
              color: color.withValues(alpha: 0.12),
              borderRadius: BorderRadius.circular(10),
            ),
            child: Icon(icon, color: color, size: 18),
          ),
          const SizedBox(height: 8),
          Text(
            value,
            style: const TextStyle(
              fontSize: 18,
              fontWeight: FontWeight.w800,
              color: AppTheme.textPrimary,
            ),
          ),
          const SizedBox(height: 2),
          Text(
            label,
            style: const TextStyle(fontSize: 10, color: AppTheme.textSecondary, fontWeight: FontWeight.w600),
          ),
        ],
      ),
    );
  }

  Widget _buildActionCard({
    required IconData icon,
    required String title,
    required String subtitle,
    required Color color,
    VoidCallback? onTap,
  }) {
    final isEnabled = onTap != null;
    return Opacity(
      opacity: isEnabled ? 1.0 : 0.5,
      child: GlassCard(
        padding: const EdgeInsets.all(16),
        borderRadius: 20,
        onTap: onTap,
        child: Row(
          children: [
            Container(
              width: 42,
              height: 42,
              decoration: BoxDecoration(
                color: color.withValues(alpha: 0.12),
                borderRadius: BorderRadius.circular(14),
              ),
              child: Icon(icon, color: color, size: 22),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    title,
                    style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w700, color: AppTheme.textPrimary),
                  ),
                  const SizedBox(height: 2),
                  Text(
                    subtitle,
                    style: const TextStyle(fontSize: 11, color: AppTheme.textSecondary),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildFilterChip(String key, String label) {
    final isSelected = _selectedFilter == key;
    return GestureDetector(
      onTap: () {
        setState(() => _selectedFilter = key);
        ref.read(salesSessionsListProvider.notifier).setStatusFilter(key);
      },
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
        decoration: BoxDecoration(
          color: isSelected ? AppTheme.darkTeal : Colors.white,
          borderRadius: BorderRadius.circular(16),
          border: Border.all(
            color: isSelected ? AppTheme.darkTeal : AppTheme.borderLight,
          ),
        ),
        child: Text(
          label,
          style: TextStyle(
            fontSize: 12,
            fontWeight: FontWeight.w700,
            color: isSelected ? Colors.white : AppTheme.textSecondary,
          ),
        ),
      ),
    );
  }

  Widget _buildSessionCard(SalesSessionModel session) {
    final shortSessionId = session.id.length > 8 ? session.id.substring(0, 8) : session.id;
    final shortCustomerId = session.customerId.length > 8 ? session.customerId.substring(0, 8) : session.customerId;

    return Padding(
      padding: const EdgeInsets.only(bottom: 12.0),
      child: GlassCard(
        padding: const EdgeInsets.all(18),
        onTap: () => context.push('/agent/session/${session.id}'),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Row(
                  children: [
                    Container(
                      width: 36,
                      height: 36,
                      decoration: BoxDecoration(
                        color: AppTheme.gradientSkyBlue.withValues(alpha: 0.12),
                        borderRadius: BorderRadius.circular(10),
                      ),
                      child: const Icon(Icons.mic_none_rounded, color: AppTheme.gradientSkyBlue, size: 20),
                    ),
                    const SizedBox(width: 10),
                    Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          'Session #$shortSessionId',
                          style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w800, color: AppTheme.textPrimary),
                        ),
                        Text(
                          'Customer: #$shortCustomerId',
                          style: const TextStyle(fontSize: 11, color: AppTheme.textSecondary),
                        ),
                      ],
                    ),
                  ],
                ),
                StatusBadge.fromStatus(session.status),
              ],
            ),
            const Divider(color: AppTheme.borderLight, height: 24),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Row(
                  children: [
                    Icon(
                      session.customerConsent ? Icons.check_circle_rounded : Icons.cancel_rounded,
                      size: 14,
                      color: session.customerConsent ? AppTheme.success : AppTheme.error,
                    ),
                    const SizedBox(width: 6),
                    Text(
                      session.customerConsent ? 'Consent Confirmed' : 'Consent Missing',
                      style: TextStyle(
                        fontSize: 11,
                        fontWeight: FontWeight.w600,
                        color: session.customerConsent ? AppTheme.success : AppTheme.error,
                      ),
                    ),
                  ],
                ),
                if (session.durationSeconds != null) ...[
                  Text(
                    '${session.durationSeconds}s duration',
                    style: const TextStyle(fontSize: 11, color: AppTheme.textSecondary),
                  ),
                ],
                const Icon(Icons.chevron_right_rounded, size: 18, color: AppTheme.textMuted),
              ],
            ),
          ],
        ),
      ),
    );
  }
}
