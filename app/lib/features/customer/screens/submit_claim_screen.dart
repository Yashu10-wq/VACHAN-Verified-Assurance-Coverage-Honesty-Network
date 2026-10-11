import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../core/theme/app_theme.dart';
import '../../../shared/widgets/app_button.dart';
import '../../../shared/widgets/app_text_field.dart';
import '../../../shared/widgets/glass_card.dart';
import '../models/customer_policy_model.dart';
import '../providers/customer_provider.dart';

class SubmitClaimScreen extends ConsumerStatefulWidget {
  const SubmitClaimScreen({super.key});

  @override
  ConsumerState<SubmitClaimScreen> createState() => _SubmitClaimScreenState();
}

class _SubmitClaimScreenState extends ConsumerState<SubmitClaimScreen> {
  final _formKey = GlobalKey<FormState>();
  final _amountController = TextEditingController();
  final _descriptionController = TextEditingController();

  CustomerRegistrationModel? _selectedRegistration;
  String _selectedCategory = 'GENERIC'; // VEHICLE, MEDICAL, GENERIC
  DateTime _incidentDate = DateTime.now();
  bool _isSubmitting = false;

  @override
  void initState() {
    super.initState();
    final dashboard = ref.read(customerDashboardProvider);
    if (dashboard.activePolicies.isNotEmpty) {
      _selectedRegistration = dashboard.activePolicies.first;
    }
  }

  @override
  void dispose() {
    _amountController.dispose();
    _descriptionController.dispose();
    super.dispose();
  }

  Future<void> _pickDate() async {
    final picked = await showDatePicker(
      context: context,
      initialDate: _incidentDate,
      firstDate: DateTime(2020),
      lastDate: DateTime.now(),
    );
    if (picked != null) {
      setState(() => _incidentDate = picked);
    }
  }

  Future<void> _handleSubmit() async {
    if (!_formKey.currentState!.validate()) return;
    if (_selectedRegistration == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Please select an active policy registration.'),
          backgroundColor: AppTheme.error,
        ),
      );
      return;
    }

    final amount = double.tryParse(_amountController.text.trim());
    if (amount == null || amount <= 0) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Please enter a valid positive claim amount.'),
          backgroundColor: AppTheme.error,
        ),
      );
      return;
    }

    setState(() => _isSubmitting = true);

    final incidentDateStr =
        "${_incidentDate.year}-${_incidentDate.month.toString().padLeft(2, '0')}-${_incidentDate.day.toString().padLeft(2, '0')}";

    final newClaim = await ref.read(claimsListProvider.notifier).submitClaim(
          registrationId: _selectedRegistration!.id,
          claimCategory: _selectedCategory,
          requestedAmount: amount,
          incidentDate: incidentDateStr,
          description: _descriptionController.text.trim(),
        );

    setState(() => _isSubmitting = false);

    if (newClaim != null && mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Claim submitted successfully!'),
          backgroundColor: AppTheme.success,
        ),
      );
      context.pop();
    }
  }

  @override
  Widget build(BuildContext context) {
    final dashboard = ref.watch(customerDashboardProvider);
    final activeRegs = dashboard.activePolicies;

    return Scaffold(
      backgroundColor: AppTheme.background,
      appBar: AppBar(
        title: const Text('File an Insurance Claim'),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_ios_new_rounded, size: 20),
          onPressed: () => context.pop(),
        ),
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.symmetric(horizontal: 20.0, vertical: 12.0),
          child: Form(
            key: _formKey,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  'Incident & Policy Details',
                  style: TextStyle(
                    fontSize: 22,
                    fontWeight: FontWeight.w800,
                    color: AppTheme.textPrimary,
                    letterSpacing: -0.4,
                  ),
                ),
                const SizedBox(height: 6),
                const Text(
                  'Claims must be filed against active confirmed policy registrations.',
                  style: TextStyle(fontSize: 13, color: AppTheme.textSecondary),
                ),
                const SizedBox(height: 20),

                // Registration Selector
                if (activeRegs.isEmpty) ...[
                  Container(
                    padding: const EdgeInsets.all(16),
                    decoration: BoxDecoration(
                      color: AppTheme.warning.withValues(alpha: 0.12),
                      borderRadius: BorderRadius.circular(16),
                      border: Border.all(color: AppTheme.warning.withValues(alpha: 0.3)),
                    ),
                    child: const Row(
                      children: [
                        Icon(Icons.warning_amber_rounded, color: AppTheme.warning, size: 24),
                        SizedBox(width: 12),
                        Expanded(
                          child: Text(
                            'You do not have any active confirmed policies. You must have an active policy to file claims.',
                            style: TextStyle(fontSize: 12, color: Color(0xFF92400E), fontWeight: FontWeight.w500),
                          ),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 20),
                ] else ...[
                  const Text(
                    'Select Insured Policy',
                    style: TextStyle(fontSize: 14, fontWeight: FontWeight.w700, color: AppTheme.textPrimary),
                  ),
                  const SizedBox(height: 8),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
                    decoration: BoxDecoration(
                      color: Colors.white,
                      borderRadius: BorderRadius.circular(20),
                      border: Border.all(color: AppTheme.borderLight),
                    ),
                    child: DropdownButtonHideUnderline(
                      child: DropdownButton<CustomerRegistrationModel>(
                        isExpanded: true,
                        value: _selectedRegistration ?? activeRegs.first,
                        items: activeRegs.map((reg) {
                          return DropdownMenuItem(
                            value: reg,
                            child: Text(
                              'Policy #${reg.policyId.substring(0, reg.policyId.length > 8 ? 8 : reg.policyId.length)} (${reg.id.substring(0, 8)})',
                              style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w600),
                            ),
                          );
                        }).toList(),
                        onChanged: (val) {
                          if (val != null) setState(() => _selectedRegistration = val);
                        },
                      ),
                    ),
                  ),
                  const SizedBox(height: 18),
                ],

                // Category Selector
                const Text(
                  'Claim Category',
                  style: TextStyle(fontSize: 14, fontWeight: FontWeight.w700, color: AppTheme.textPrimary),
                ),
                const SizedBox(height: 8),
                Row(
                  children: [
                    _buildCategoryRadio('GENERIC', 'General', Icons.folder_outlined),
                    const SizedBox(width: 8),
                    _buildCategoryRadio('VEHICLE', 'Motor / Vehicle', Icons.directions_car_rounded),
                    const SizedBox(width: 8),
                    _buildCategoryRadio('MEDICAL', 'Medical / Health', Icons.medical_services_rounded),
                  ],
                ),

                const SizedBox(height: 18),

                // Requested Amount & Incident Date
                GlassCard(
                  padding: const EdgeInsets.all(20),
                  child: Column(
                    children: [
                      AppTextField(
                        controller: _amountController,
                        labelText: 'Requested Amount (\$)',
                        hintText: 'e.g. 25000.00',
                        keyboardType: const TextInputType.numberWithOptions(decimal: true),
                        prefixIcon: const Icon(Icons.attach_money_rounded, color: AppTheme.textMuted, size: 20),
                        validator: (value) {
                          if (value == null || value.trim().isEmpty) return 'Please enter requested amount';
                          final val = double.tryParse(value.trim());
                          if (val == null || val <= 0) return 'Must be greater than 0';
                          return null;
                        },
                      ),
                      const SizedBox(height: 16),
                      // Incident Date Picker
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              const Text(
                                'Date of Incident',
                                style: TextStyle(fontSize: 14, fontWeight: FontWeight.w600, color: AppTheme.textPrimary),
                              ),
                              const SizedBox(height: 4),
                              Text(
                                "${_incidentDate.year}-${_incidentDate.month.toString().padLeft(2, '0')}-${_incidentDate.day.toString().padLeft(2, '0')}",
                                style: const TextStyle(fontSize: 15, fontWeight: FontWeight.w700, color: AppTheme.darkTeal),
                              ),
                            ],
                          ),
                          OutlinedButton.icon(
                            icon: const Icon(Icons.calendar_today_rounded, size: 16),
                            label: const Text('Change Date'),
                            onPressed: _pickDate,
                          ),
                        ],
                      ),
                      const SizedBox(height: 16),
                      AppTextField(
                        controller: _descriptionController,
                        labelText: 'Detailed Incident Description',
                        hintText: 'Describe the incident, damage, or treatment in detail (min 10 characters)...',
                        maxLines: 4,
                        validator: (value) {
                          if (value == null || value.trim().length < 10) {
                            return 'Please provide at least 10 characters describing the incident';
                          }
                          return null;
                        },
                      ),
                    ],
                  ),
                ),

                const SizedBox(height: 24),

                AppButton(
                  label: 'Submit Claim for Evaluation',
                  isLoading: _isSubmitting,
                  onPressed: activeRegs.isEmpty ? null : _handleSubmit,
                  variant: AppButtonVariant.primaryGradient,
                ),

                const SizedBox(height: 24),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildCategoryRadio(String key, String label, IconData icon) {
    final isSelected = _selectedCategory == key;
    return Expanded(
      child: GestureDetector(
        onTap: () => setState(() => _selectedCategory = key),
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 180),
          padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 6),
          decoration: BoxDecoration(
            color: isSelected ? AppTheme.darkTeal : Colors.white,
            borderRadius: BorderRadius.circular(16),
            border: Border.all(
              color: isSelected ? AppTheme.darkTeal : AppTheme.borderLight,
            ),
          ),
          child: Column(
            children: [
              Icon(icon, size: 20, color: isSelected ? Colors.white : AppTheme.textSecondary),
              const SizedBox(height: 4),
              Text(
                label,
                style: TextStyle(
                  fontSize: 11,
                  fontWeight: FontWeight.w600,
                  color: isSelected ? Colors.white : AppTheme.textSecondary,
                ),
                textAlign: TextAlign.center,
              ),
            ],
          ),
        ),
      ),
    );
  }
}
