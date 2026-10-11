import 'package:flutter/material.dart';
import '../../../core/theme/app_theme.dart';
import '../../../shared/widgets/glass_card.dart';
import '../widgets/customer_bottom_nav.dart';

class CustomerHelpScreen extends StatelessWidget {
  const CustomerHelpScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.background,
      bottomNavigationBar: const CustomerBottomNav(currentIndex: 3),
      appBar: AppBar(
        title: const Text('Help & Support'),
        automaticallyImplyLeading: false,
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.symmetric(horizontal: 20.0, vertical: 12.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Support Banner
              GlassCard(
                padding: const EdgeInsets.all(20),
                child: Row(
                  children: [
                    Container(
                      width: 48,
                      height: 48,
                      decoration: BoxDecoration(
                        color: AppTheme.gradientSkyBlue.withValues(alpha: 0.15),
                        shape: BoxShape.circle,
                      ),
                      child: const Icon(
                        Icons.support_agent_rounded,
                        color: AppTheme.gradientSkyBlue,
                        size: 26,
                      ),
                    ),
                    const SizedBox(width: 14),
                    const Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            'InsureChain VoiceGuard Help',
                            style: TextStyle(
                              fontSize: 16,
                              fontWeight: FontWeight.w800,
                              color: AppTheme.textPrimary,
                            ),
                          ),
                          SizedBox(height: 2),
                          Text(
                            'Transparent coverage & claim guidance',
                            style: TextStyle(fontSize: 12, color: AppTheme.textSecondary),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),

              const SizedBox(height: 16),

              // Roadmap Disclaimer Card
              Container(
                padding: const EdgeInsets.all(14),
                decoration: BoxDecoration(
                  color: AppTheme.darkTeal.withValues(alpha: 0.06),
                  borderRadius: BorderRadius.circular(16),
                  border: Border.all(color: AppTheme.darkTeal.withValues(alpha: 0.15)),
                ),
                child: const Row(
                  children: [
                    Icon(Icons.info_outline_rounded, color: AppTheme.darkTeal, size: 20),
                    SizedBox(width: 10),
                    Expanded(
                      child: Text(
                        'Live AI voice assistant & direct dispute arbitration chat are scheduled for subsequent phases. Current options provide official guidance and verified contacts.',
                        style: TextStyle(fontSize: 11, color: Color(0xFF1E3A42), height: 1.35),
                      ),
                    ),
                  ],
                ),
              ),

              const SizedBox(height: 20),

              const Text(
                'Frequently Asked Questions',
                style: TextStyle(
                  fontSize: 17,
                  fontWeight: FontWeight.w800,
                  color: AppTheme.textPrimary,
                  letterSpacing: -0.3,
                ),
              ),

              const SizedBox(height: 12),

              _buildFaqTile(
                question: 'How does VoiceGuard verify my policy promises?',
                answer:
                    'When an agent onboards you, the sales conversation audio is securely transcribed. The Gemini verification engine compares verbatim agent statements against registered policy terms, classifying each as Supported, Partly True, Contradicted, Not in Policy, or Unclear.',
              ),
              _buildFaqTile(
                question: 'How do I accept or decline a pending policy?',
                answer:
                    'Go to the Policies tab and switch to the "Awaiting Confirmation" filter. Review the verified clauses and tap "Confirm Policy" for affirmative consent, or tap "Decline" if the terms differ from your expectations.',
              ),
              _buildFaqTile(
                question: 'How are claim decisions evaluated?',
                answer:
                    'Claims undergo deterministic rule evaluation checking your policy coverage limit, waiting period compliance, and incident date window before submission to the underwriting authority.',
              ),
              _buildFaqTile(
                question: 'What is the Blockchain Audit Seal?',
                answer:
                    'Every critical event—including policy publication, sales verification, consent confirmation, and claim state changes—is anchored in an immutable cryptographic audit chain backed by smart contracts.',
              ),

              const SizedBox(height: 20),

              const Text(
                'Contact Assistance',
                style: TextStyle(
                  fontSize: 17,
                  fontWeight: FontWeight.w800,
                  color: AppTheme.textPrimary,
                  letterSpacing: -0.3,
                ),
              ),

              const SizedBox(height: 12),

              GlassCard(
                padding: const EdgeInsets.all(16),
                child: Column(
                  children: [
                    _buildContactRow(
                      icon: Icons.phone_in_talk_rounded,
                      title: 'Customer Claims Hotline',
                      subtitle: '1-800-INSURE-CHAIN (24/7 Support)',
                    ),
                    const Divider(color: AppTheme.borderLight, height: 20),
                    _buildContactRow(
                      icon: Icons.alternate_email_rounded,
                      title: 'Compliance & Verification Office',
                      subtitle: 'support@insurechain-voiceguard.io',
                    ),
                  ],
                ),
              ),

              const SizedBox(height: 28),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildFaqTile({required String question, required String answer}) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 10.0),
      child: GlassCard(
        padding: const EdgeInsets.all(16),
        child: ExpansionTile(
          tilePadding: EdgeInsets.zero,
          childrenPadding: const EdgeInsets.only(top: 8),
          title: Text(
            question,
            style: const TextStyle(
              fontSize: 13,
              fontWeight: FontWeight.w700,
              color: AppTheme.textPrimary,
            ),
          ),
          children: [
            Text(
              answer,
              style: const TextStyle(
                fontSize: 12,
                color: AppTheme.textSecondary,
                height: 1.4,
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildContactRow({
    required IconData icon,
    required String title,
    required String subtitle,
  }) {
    return Row(
      children: [
        Container(
          width: 38,
          height: 38,
          decoration: BoxDecoration(
            color: AppTheme.gradientSkyBlue.withValues(alpha: 0.12),
            borderRadius: BorderRadius.circular(10),
          ),
          child: Icon(icon, color: AppTheme.gradientSkyBlue, size: 20),
        ),
        const SizedBox(width: 12),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                title,
                style: const TextStyle(
                  fontSize: 13,
                  fontWeight: FontWeight.w700,
                  color: AppTheme.textPrimary,
                ),
              ),
              const SizedBox(height: 2),
              Text(
                subtitle,
                style: const TextStyle(fontSize: 12, color: AppTheme.textSecondary),
              ),
            ],
          ),
        ),
      ],
    );
  }
}
