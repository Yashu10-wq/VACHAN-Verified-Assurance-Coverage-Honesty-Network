import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:insurechain_voiceguard/core/network/api_client.dart';
import 'package:insurechain_voiceguard/features/auth/models/user_model.dart';
import 'package:insurechain_voiceguard/features/customer/models/claim_model.dart';
import 'package:insurechain_voiceguard/features/customer/models/customer_policy_model.dart';
import 'package:insurechain_voiceguard/features/customer/models/verification_report_model.dart';
import 'package:insurechain_voiceguard/features/customer/providers/customer_provider.dart';
import 'package:insurechain_voiceguard/features/customer/screens/claims_list_screen.dart';
import 'package:insurechain_voiceguard/features/customer/screens/customer_help_screen.dart';
import 'package:insurechain_voiceguard/features/customer/screens/customer_more_screen.dart';
import 'package:insurechain_voiceguard/features/customer/screens/customer_policies_screen.dart';
import 'package:insurechain_voiceguard/features/customer/screens/verification_report_screen.dart';
import 'package:insurechain_voiceguard/features/customer/services/customer_api_service.dart';
import 'package:insurechain_voiceguard/features/customer/widgets/customer_bottom_nav.dart';
import 'package:insurechain_voiceguard/features/auth/providers/auth_provider.dart';
import 'package:insurechain_voiceguard/features/agent/models/sales_session_model.dart';
import 'package:insurechain_voiceguard/features/agent/providers/agent_provider.dart';
import 'package:insurechain_voiceguard/features/agent/screens/agent_home_screen.dart';
import 'package:insurechain_voiceguard/features/agent/screens/new_sales_session_screen.dart';
import 'package:insurechain_voiceguard/features/agent/services/agent_api_service.dart';
import 'package:insurechain_voiceguard/features/authority/providers/authority_provider.dart';
import 'package:insurechain_voiceguard/features/authority/screens/authority_claim_review_screen.dart';
import 'package:insurechain_voiceguard/features/authority/screens/authority_home_screen.dart';
import 'package:insurechain_voiceguard/features/authority/services/authority_api_service.dart';
import 'package:insurechain_voiceguard/features/auth/services/auth_api_service.dart';
import 'package:insurechain_voiceguard/core/storage/secure_storage_service.dart';
import 'package:insurechain_voiceguard/features/integrity/models/blockchain_status_model.dart';
import 'package:insurechain_voiceguard/features/integrity/providers/integrity_provider.dart';
import 'package:insurechain_voiceguard/features/integrity/screens/blockchain_integrity_screen.dart';
import 'package:insurechain_voiceguard/features/integrity/services/integrity_api_service.dart';

class FakeAuthNotifier extends AuthNotifier {
  FakeAuthNotifier(AuthState initial)
      : super(
          authService: AuthApiService(client: ApiClient()),
          storageService: SecureStorageService(),
        ) {
    state = initial;
  }
}

class FakeCustomerApiService extends CustomerApiService {
  FakeCustomerApiService() : super(apiClient: ApiClient());

  @override
  Future<List<DetailedPolicyModel>> listPolicies({String? category}) async => [];

  @override
  Future<List<CustomerRegistrationModel>> listRegistrations({String? status}) async => [];

  @override
  Future<List<ClaimModel>> listClaims({String? status}) async => [];

  @override
  Future<DetailedPolicyModel> getPolicyDetails(String policyId) async {
    return DetailedPolicyModel(
      id: policyId,
      insurerName: 'InsureChain',
      policyName: 'Test Policy',
      policyCode: 'TST-01',
      category: 'MOTOR',
      coverageLimit: 10000,
      waitingPeriodDays: 0,
      claimFilingWindowDays: 30,
      isActive: true,
    );
  }
}

class FakeAgentApiService extends AgentApiService {
  FakeAgentApiService() : super(apiClient: ApiClient());

  @override
  Future<List<SalesSessionModel>> listSalesSessions({String? status, int page = 1, int pageSize = 50}) async => [
        const SalesSessionModel(
          id: 'sess-test-001',
          customerId: 'cust-12345678-abcd',
          agentId: 'agent-101',
          policyId: 'pol-001',
          audioStorageRef: 'recordings/sess-test-001.m4a',
          audioMimeType: 'audio/m4a',
          audioFileSizeBytes: 1048576,
          durationSeconds: 120,
          audioChecksum: 'abc123def456',
          customerConsent: true,
          status: 'COMPLETED',
          detectedLanguage: 'en',
          providerModel: 'scribe_v1',
          createdAt: '2026-10-11T10:00:00Z',
          updatedAt: '2026-10-11T10:05:00Z',
        ),
      ];

  @override
  Future<List<CustomerRegistrationModel>> listRegistrations({String? status}) async => [];

  @override
  Future<List<DetailedPolicyModel>> listPolicies() async => [];
}

class FakeAuthorityApiService extends AuthorityApiService {
  FakeAuthorityApiService() : super(apiClient: ApiClient());

  @override
  Future<List<ClaimModel>> listAllClaims({String? status, int page = 1, int pageSize = 50}) async => [
        const ClaimModel(
          id: 'claim-auth-001',
          customerId: 'cust-12345678-abcd',
          registrationId: 'reg-001',
          policyId: 'pol-001',
          policyVersionId: 'ver-001',
          claimCategory: 'ACCIDENT',
          requestedAmount: '4500.00',
          incidentDate: '2026-10-01',
          submissionTimestamp: '2026-10-02T10:00:00Z',
          description: 'Vehicle damage evaluation',
          status: 'SUBMITTED',
          createdAt: '2026-10-02T10:00:00Z',
          evidence: [],
          statusHistory: [],
        ),
      ];

  @override
  Future<ClaimModel> getClaimDetails(String claimId) async {
    return const ClaimModel(
      id: 'claim-auth-001',
      customerId: 'cust-12345678-abcd',
      registrationId: 'reg-001',
      policyId: 'pol-001',
      policyVersionId: 'ver-001',
      claimCategory: 'ACCIDENT',
      requestedAmount: '4500.00',
      incidentDate: '2026-10-01',
      submissionTimestamp: '2026-10-02T10:00:00Z',
      description: 'Vehicle front bumper collision',
      status: 'SUBMITTED',
      createdAt: '2026-10-02T10:00:00Z',
      evidence: [],
      statusHistory: [
        ClaimStatusHistoryModel(
          id: 'hist-01',
          previousStatus: 'DRAFT',
          newStatus: 'SUBMITTED',
          reason: 'Initial submission',
          actorRole: 'CUSTOMER',
          createdAt: '2026-10-02T10:00:00Z',
        )
      ],
      latestAssessment: ClaimAssessmentModel(
        id: 'assess-01',
        claimId: 'claim-auth-001',
        assessmentVersion: 1,
        overallOutcome: 'ELIGIBLE',
        requestedAmount: '4500.00',
        applicableLimit: '50000.00',
        potentiallyPayableAmount: '4500.00',
        excessAmount: '0.00',
        rulesEvaluated: [
          RuleEvaluationModel(
            ruleId: 'COVERAGE_LIMIT_CHECK',
            result: 'PASS',
            explanation: 'Requested 4500 is within 50000 coverage limit.',
          ),
        ],
        missingEvidence: [],
        reviewFlags: [],
      ),
    );
  }

  @override
  Future<List<Map<String, dynamic>>> checkDuplicates(String claimId) async => [
        {
          'candidate_claim_id': 'claim-past-999',
          'match_score': 0.85,
          'incident_date': '2026-09-28',
          'common_attributes': ['category', 'vehicle_vin'],
        }
      ];
}

class FakeIntegrityApiService extends IntegrityApiService {
  FakeIntegrityApiService() : super(apiClient: ApiClient());

  @override
  Future<BlockchainStatusModel> getBlockchainStatus() async {
    return const BlockchainStatusModel(
      isConnected: true,
      rpcUrl: 'http://127.0.0.1:8545',
      configuredChainId: 31337,
      nodeChainId: 31337,
      blockNumber: 42,
      contractAddress: '0x5FbDB2315678afecb367f032d93F642f64180aa3',
      contractDeployed: true,
      status: 'ONLINE',
      totalEvents: 15,
      unchainedEvents: 0,
      pendingEvents: 2,
      batchedEvents: 5,
      anchoredEvents: 8,
      failedEvents: 0,
    );
  }

  @override
  Future<AuditEventVerificationModel> verifyAuditEvent(String eventId) async {
    return AuditEventVerificationModel(
      eventId: eventId,
      outcome: 'VALID',
      message: 'Cryptographic hash-chain and sequence linkage verified.',
      sequenceNumber: 7,
      eventHash: '0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef',
      previousHash: '0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890',
      payloadHash: '0x9999999999abcdef9999999999abcdef9999999999abcdef9999999999abcdef',
      anchoringStatus: 'ANCHORED',
      batchId: 'batch-uuid-001',
      createdAt: '2026-10-11T12:00:00Z',
      onChainVerified: true,
    );
  }

  @override
  Future<AuditEventProofModel> getAuditEventProof(String eventId) async {
    return const AuditEventProofModel(
      eventId: 'evt-001',
      sequenceNumber: 7,
      eventHash: '0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef',
      batchId: 'batch-uuid-001',
      batchSequence: 1,
      batchRootHash: '0xroot1234567890abcdef1234567890abcdef1234567890abcdef',
      leafIndex: 0,
      merkleProof: [
        MerkleProofStepModel(position: 'right', hash: '0xsibling1234567890abcdef'),
      ],
      txHash: '0xtx1234567890abcdef1234567890',
      blockNumber: 42,
      chainId: 31337,
      contractAddress: '0x5FbDB2315678afecb367f032d93F642f64180aa3',
      onChainCommitmentVerified: true,
      anchoredAt: '2026-10-11T12:05:00Z',
    );
  }
}

void main() {
  group('1. Auth & User Model Tests', () {
    test('UserModel JSON deserialization parses fields and roles properly', () {
      final json = {
        'id': 'user-123',
        'email': 'customer@example.com',
        'full_name': 'Jane Doe',
        'phone': '+1234567890',
        'role': 'CUSTOMER',
        'account_status': 'ACTIVE',
        'email_verified_at': '2026-10-11T12:00:00Z',
        'created_at': '2026-10-10T08:00:00Z',
      };

      final user = UserModel.fromJson(json);

      expect(user.id, 'user-123');
      expect(user.email, 'customer@example.com');
      expect(user.fullName, 'Jane Doe');
      expect(user.role, UserRole.customer);
      expect(user.accountStatus, AccountStatus.active);
      expect(user.role.displayName, 'Customer');
    });

    test('UserRole and AccountStatus parse case-insensitively', () {
      expect(UserRole.fromString('INSURANCE_AGENT'), UserRole.insuranceAgent);
      expect(UserRole.fromString('APPROVAL_AUTHORITY'), UserRole.approvalAuthority);
      expect(UserRole.fromString('UNKNOWN'), UserRole.customer);

      expect(AccountStatus.fromString('PENDING_APPROVAL'), AccountStatus.pendingApproval);
      expect(AccountStatus.fromString('SUSPENDED'), AccountStatus.suspended);
      expect(AccountStatus.fromString('ACTIVE'), AccountStatus.active);
    });
  });

  group('2. Customer Policy & Registration Serialization Tests', () {
    test('DetailedPolicyModel parses underwriting parameters and versions', () {
      final json = {
        'id': 'pol-001',
        'policy_code': 'MOT-2026-X',
        'policy_name': 'Comprehensive Motor Shield',
        'category': 'MOTOR',
        'insurer_name': 'InsureChain Underwriters',
        'description': 'Full accidental damage and roadside assistance.',
        'coverage_limit': 50000.0,
        'waiting_period_days': 15,
        'claim_filing_window_days': 30,
        'is_active': true,
        'versions': [
          {
            'id': 'ver-001',
            'policy_id': 'pol-001',
            'version_number': 2,
            'is_published': true,
            'document_checksum': 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',
            'effective_date': '2026-01-01',
            'terms_json': {'deductible': '250', 'roadside_included': 'yes'},
          }
        ],
      };

      final policy = DetailedPolicyModel.fromJson(json);
      expect(policy.id, 'pol-001');
      expect(policy.policyName, 'Comprehensive Motor Shield');
      expect(policy.coverageLimit, 50000.0);
      expect(policy.waitingPeriodDays, 15);
      expect(policy.latestVersion?.versionNumber, 2);
      expect(policy.latestVersion?.termsJson['deductible'], '250');
    });

    test('CustomerRegistrationModel verifies affirmative confirmation states', () {
      final pendingJson = {
        'id': 'reg-001',
        'customer_id': 'cust-01',
        'policy_id': 'pol-001',
        'policy_version_id': 'ver-001',
        'status': 'AWAITING_CUSTOMER_CONFIRMATION',
        'customer_consent': false,
      };
      final pendingReg = CustomerRegistrationModel.fromJson(pendingJson);
      expect(pendingReg.isAwaitingConfirmation, isTrue);
      expect(pendingReg.isConfirmed, isFalse);

      final confirmedJson = {
        'id': 'reg-002',
        'customer_id': 'cust-01',
        'policy_id': 'pol-001',
        'policy_version_id': 'ver-001',
        'status': 'CONFIRMED',
        'customer_consent': true,
      };
      final confirmedReg = CustomerRegistrationModel.fromJson(confirmedJson);
      expect(confirmedReg.isConfirmed, isTrue);
      expect(confirmedReg.isAwaitingConfirmation, isFalse);
    });
  });

  group('3. Claims & Assessment Serialization Tests', () {
    test('ClaimModel deserializes amount, status, and assessment outcomes', () {
      final json = {
        'id': 'claim-777',
        'customer_id': 'cust-01',
        'registration_id': 'reg-002',
        'policy_id': 'pol-001',
        'policy_version_id': 'ver-001',
        'claim_category': 'ACCIDENT',
        'requested_amount': '1250.50',
        'incident_date': '2026-10-01',
        'submission_timestamp': '2026-10-02T10:00:00Z',
        'description': 'Vehicle minor fender scrape on highway.',
        'status': 'UNDER_REVIEW',
        'latest_assessment': {
          'id': 'assess-01',
          'claim_id': 'claim-777',
          'assessment_version': 1,
          'overall_outcome': 'ELIGIBLE',
          'requested_amount': '1250.50',
          'applicable_limit': '50000.00',
          'potentially_payable_amount': '1250.50',
          'excess_amount': '0.00',
          'rules_evaluated': [
            {
              'rule_id': 'COVERAGE_LIMIT_CHECK',
              'result': 'PASS',
              'explanation': 'Requested amount is within \$50000 limit.',
            }
          ],
          'missing_evidence': [],
          'review_flags': [],
        },
      };

      final claim = ClaimModel.fromJson(json);
      expect(claim.id, 'claim-777');
      expect(claim.claimNumber, '#claim-77');
      expect(claim.requestedAmountValue, 1250.50);
      expect(claim.latestAssessment?.overallOutcome, 'ELIGIBLE');
      expect(claim.latestAssessment?.rulesEvaluated.first.result, 'PASS');
    });
  });

  group('4. Policy-Promise Verification Model Tests', () {
    test('VerificationReportModel accurately captures 5 promise classifications', () {
      final json = {
        'id': 'rep-001',
        'sales_session_id': 'sess-001',
        'customer_id': 'cust-01',
        'agent_id': 'agent-01',
        'policy_id': 'pol-001',
        'report_version': 1,
        'status': 'COMPLETED',
        'overall_integrity_status': 'VERIFIED',
        'supported_count': 3,
        'partly_true_count': 1,
        'contradicted_count': 0,
        'not_in_policy_count': 1,
        'unclear_count': 0,
        'findings': [
          {
            'finding_id': 'f-01',
            'promise_text': 'Towing is covered nationwide without deductibles.',
            'transcript_quote': 'We provide 24/7 complimentary nationwide towing without any deductible.',
            'classification': 'SUPPORTED',
            'policy_excerpt': 'Section 4.1: Nationwide towing roadside assistance is provided with \$0 copay.',
            'page_number': 6,
            'section_heading': 'Roadside Services',
            'explanation': 'Statement matches Section 4.1 clause verbatim.',
            'confidence': 0.98,
            'review_required': false,
          },
          {
            'finding_id': 'f-02',
            'promise_text': 'Free international travel insurance included.',
            'transcript_quote': 'You also get global travel coverage when you fly.',
            'classification': 'NOT_IN_POLICY',
            'explanation': 'Motor policy does not encompass international flight travel terms.',
            'confidence': 0.95,
            'review_required': true,
          }
        ],
      };

      final report = VerificationReportModel.fromJson(json);
      expect(report.id, 'rep-001');
      expect(report.overallIntegrityStatus, 'VERIFIED');
      expect(report.supportedCount, 3);
      expect(report.findings.length, 2);
      expect(report.findings[0].classification, 'SUPPORTED');
      expect(report.findings[0].sectionHeading, 'Roadside Services');
      expect(report.findings[1].classification, 'NOT_IN_POLICY');
      expect(report.findings[1].reviewRequired, isTrue);
    });
  });

  group('5. Customer Navigation & Screen Rendering Tests', () {
    testWidgets('CustomerBottomNav renders all 5 customer tabs with active highlighting', (tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: Scaffold(
            bottomNavigationBar: CustomerBottomNav(currentIndex: 1),
          ),
        ),
      );

      expect(find.text('Home'), findsOneWidget);
      expect(find.text('Policies'), findsOneWidget);
      expect(find.text('Claims'), findsOneWidget);
      expect(find.text('Help'), findsOneWidget);
      expect(find.text('More'), findsOneWidget);
    });

    testWidgets('CustomerPoliciesScreen displays search bar, filter chips, and empty state', (tester) async {
      await tester.pumpWidget(
        ProviderScope(
          overrides: [
            customerApiServiceProvider.overrideWithValue(FakeCustomerApiService()),
          ],
          child: const MaterialApp(
            home: CustomerPoliciesScreen(),
          ),
        ),
      );
      await tester.pumpAndSettle();

      expect(find.text('My Policies & Coverage'), findsOneWidget);
      expect(find.byType(TextField), findsOneWidget);
      expect(find.text('All Policies'), findsOneWidget);
      expect(find.textContaining('Active Coverage'), findsOneWidget);
      expect(find.text('Catalogue (0)'), findsOneWidget);
    });

    testWidgets('ClaimsListScreen renders title, filter chips, and File Claim FAB', (tester) async {
      await tester.pumpWidget(
        ProviderScope(
          overrides: [
            customerApiServiceProvider.overrideWithValue(FakeCustomerApiService()),
          ],
          child: const MaterialApp(
            home: ClaimsListScreen(),
          ),
        ),
      );
      await tester.pumpAndSettle();

      expect(find.text('My Insurance Claims'), findsOneWidget);
      expect(find.text('File Claim'), findsOneWidget);
      expect(find.text('All Claims'), findsOneWidget);
      expect(find.text('Submitted'), findsOneWidget);
      expect(find.text('Approved'), findsOneWidget);
    });

    testWidgets('CustomerHelpScreen renders FAQ expansion tiles and support info', (tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: CustomerHelpScreen(),
        ),
      );

      expect(find.text('Help & Support'), findsOneWidget);
      expect(find.text('Frequently Asked Questions'), findsOneWidget);
      expect(find.text('How does VoiceGuard verify my policy promises?'), findsOneWidget);
      expect(find.text('Customer Claims Hotline'), findsOneWidget);
    });

    testWidgets('CustomerMoreScreen renders user profile and system integrity info', (tester) async {
      await tester.pumpWidget(
        const ProviderScope(
          child: MaterialApp(
            home: CustomerMoreScreen(),
          ),
        ),
      );

      expect(find.text('Account & Security'), findsOneWidget);
      expect(find.text('Security & Integrity'), findsOneWidget);
      expect(find.text('Encrypted Keychain Storage'), findsOneWidget);
      expect(find.text('Blockchain Hash Chain'), findsOneWidget);
      expect(find.text('Sign Out'), findsOneWidget);
    });
  });

  group('6. Verification Report Screen Unit & Disclaimer Tests', () {
    testWidgets('VerificationReportScreen renders report findings, category counts, and disclaimer notice', (tester) async {
      const sampleReport = VerificationReportModel(
        id: 'rep-test-99',
        salesSessionId: 'sess-test',
        customerId: 'cust-test',
        agentId: 'agent-test',
        policyId: 'pol-test',
        reportVersion: 1,
        status: 'COMPLETED',
        overallIntegrityStatus: 'VERIFIED',
        summary: 'Agent statements match registered underwriting terms.',
        supportedCount: 2,
        partlyTrueCount: 0,
        contradictedCount: 0,
        notInPolicyCount: 0,
        unclearCount: 0,
        findings: [
          FindingItemModel(
            findingId: 'f-1',
            promiseText: 'Accidental medical coverage is up to \$100,000.',
            transcriptQuote: 'You have medical coverage up to one hundred grand included.',
            speakerLabel: 'Agent',
            classification: 'SUPPORTED',
            policyExcerpt: 'Clause 2: Accidental medical expense limit is \$100,000 per policy year.',
            pageNumber: 4,
            sectionHeading: 'Medical Protection',
            explanation: 'Transcript statement is fully verified by Clause 2.',
            confidence: 0.99,
          ),
        ],
      );

      await tester.pumpWidget(
        ProviderScope(
          overrides: [
            verificationReportProvider('rep-test-99').overrideWith((ref) => Future.value(sampleReport)),
          ],
          child: const MaterialApp(
            home: VerificationReportScreen(reportId: 'rep-test-99'),
          ),
        ),
      );

      await tester.pumpAndSettle();

      expect(find.text('VoiceGuard Verification'), findsOneWidget);
      expect(find.text('Policy-Promise Audit Summary'), findsOneWidget);
      expect(find.text('All Claims Grounded'), findsOneWidget);
      expect(find.textContaining('AI-Assisted Grounding Notice:'), findsOneWidget);
      expect(find.text('SUPPORTED'), findsAtLeastNWidgets(1));
      expect(find.text('Accidental medical coverage is up to \$100,000.'), findsOneWidget);
    });
  });

  group('7. Agent Sales Workflow Serialization & Logic Tests', () {
    test('SalesSessionModel correctly deserializes audio checksum, consent, and duration', () {
      final json = {
        'id': 'sess-12345',
        'customer_id': 'cust-888',
        'agent_id': 'agent-999',
        'policy_id': 'pol-111',
        'audio_storage_ref': 'recordings/sess-12345.m4a',
        'audio_mime_type': 'audio/m4a',
        'audio_file_size_bytes': 2097152,
        'duration_seconds': 180,
        'audio_checksum': '7f83b1657ff1fc53b92dc18148a1d65dfc2d4b1fa3d677284addd200126d9069',
        'customer_consent': true,
        'consent_timestamp': '2026-10-11T12:00:00Z',
        'consent_notes': 'Explicit affirmative voice consent granted.',
        'status': 'COMPLETED',
        'detected_language': 'en',
        'provider_model': 'scribe_v1',
        'created_at': '2026-10-11T11:58:00Z',
        'updated_at': '2026-10-11T12:05:00Z',
      };

      final session = SalesSessionModel.fromJson(json);

      expect(session.id, 'sess-12345');
      expect(session.customerId, 'cust-888');
      expect(session.audioChecksum, '7f83b1657ff1fc53b92dc18148a1d65dfc2d4b1fa3d677284addd200126d9069');
      expect(session.customerConsent, isTrue);
      expect(session.durationSeconds, 180);
      expect(session.isCompleted, isTrue);
      expect(session.isProcessing, isFalse);
    });

    test('SalesTranscriptModel preserves multi-speaker diarization and word timestamps', () {
      final json = {
        'session_id': 'sess-12345',
        'status': 'COMPLETED',
        'transcript': 'Hello, do you agree to record this call? Yes, I agree.',
        'detected_language': 'en',
        'word_segments': [
          {'word': 'Hello', 'start': 0.1, 'end': 0.5, 'speaker_id': 'speaker_0'},
          {'word': 'Yes', 'start': 2.1, 'end': 2.4, 'speaker_id': 'speaker_1'},
        ],
        'speaker_diarization': [
          {
            'speaker_id': 'speaker_0',
            'role': 'Agent',
            'start_time': 0.0,
            'end_time': 2.0,
            'text': 'Hello, do you agree to record this call?',
          },
          {
            'speaker_id': 'speaker_1',
            'role': 'Customer',
            'start_time': 2.0,
            'end_time': 3.5,
            'text': 'Yes, I agree.',
          },
        ],
        'provider_model': 'scribe_v1',
        'created_at': '2026-10-11T12:01:00Z',
        'updated_at': '2026-10-11T12:02:00Z',
      };

      final transcript = SalesTranscriptModel.fromJson(json);

      expect(transcript.sessionId, 'sess-12345');
      expect(transcript.speakerDiarization.length, 2);
      expect(transcript.speakerDiarization[0]['role'], 'Agent');
      expect(transcript.speakerDiarization[1]['role'], 'Customer');
      expect(transcript.wordSegments.length, 2);
      expect(transcript.wordSegments[0]['word'], 'Hello');
    });
  });

  group('8. Agent Dashboard & Sales Session Screen Tests', () {
    testWidgets('AgentHomeScreen renders active agent workbench, metric tiles, and new session CTA', (tester) async {
      const activeAgent = UserModel(
        id: 'agent-101',
        email: 'alex@insurechain.io',
        fullName: 'Alexander Vance',
        phone: '+1555123456',
        role: UserRole.insuranceAgent,
        accountStatus: AccountStatus.active,
      );

      await tester.pumpWidget(
        ProviderScope(
          overrides: [
            authProvider.overrideWith((ref) => FakeAuthNotifier(AuthState.authenticated(activeAgent))),
            agentApiServiceProvider.overrideWithValue(FakeAgentApiService()),
          ],
          child: const MaterialApp(
            home: AgentHomeScreen(),
          ),
        ),
      );

      await tester.pumpAndSettle();

      expect(find.text('Agent Workbench'), findsOneWidget);
      expect(find.text('Alexander Vance'), findsOneWidget);
      expect(find.text('New Sales Session'), findsOneWidget);
      expect(find.text('Total Sessions'), findsOneWidget);
      expect(find.text('Quick Actions'), findsOneWidget);
    });

    testWidgets('AgentHomeScreen displays restricted-access security state when agent is PENDING_APPROVAL', (tester) async {
      const pendingAgent = UserModel(
        id: 'agent-pending-01',
        email: 'unapproved@insurechain.io',
        fullName: 'Pending Review Agent',
        phone: '+1555987654',
        role: UserRole.insuranceAgent,
        accountStatus: AccountStatus.pendingApproval,
      );

      await tester.pumpWidget(
        ProviderScope(
          overrides: [
            authProvider.overrideWith((ref) => FakeAuthNotifier(AuthState.pendingApproval(pendingAgent))),
            agentApiServiceProvider.overrideWithValue(FakeAgentApiService()),
          ],
          child: const MaterialApp(
            home: AgentHomeScreen(),
          ),
        ),
      );

      await tester.pumpAndSettle();

      expect(find.text('Account Pending Authority Approval'), findsOneWidget);
      expect(find.textContaining('awaiting review by an Approval Authority'), findsOneWidget);
      // New sales session CTA must NOT be shown
      expect(find.text('New Sales Session'), findsNothing);
    });

    testWidgets('NewSalesSessionScreen renders statutory recording consent notice and requires affirmative consent', (tester) async {
      await tester.pumpWidget(
        ProviderScope(
          overrides: [
            agentApiServiceProvider.overrideWithValue(FakeAgentApiService()),
          ],
          child: const MaterialApp(
            home: NewSalesSessionScreen(),
          ),
        ),
      );

      await tester.pumpAndSettle();

      expect(find.text('New Sales Session'), findsOneWidget);
      expect(find.text('1. Customer & Policy Target'), findsOneWidget);
      expect(find.text('2. Mandatory Customer Recording Consent'), findsOneWidget);
      expect(find.textContaining('affirmative explicit consent'), findsOneWidget);
      expect(find.text('Start Recording'), findsOneWidget);
    });
  });

  group('9. Approval Authority Dashboard & Claim Adjudication Tests', () {
    testWidgets('AuthorityHomeScreen renders claims queue, metrics summary, and filter chips', (tester) async {
      const authorityUser = UserModel(
        id: 'auth-user-01',
        email: 'authority@insurechain.io',
        fullName: 'Chief Adjudicator',
        phone: '+1555456789',
        role: UserRole.approvalAuthority,
        accountStatus: AccountStatus.active,
      );

      await tester.pumpWidget(
        ProviderScope(
          overrides: [
            authProvider.overrideWith((ref) => FakeAuthNotifier(AuthState.authenticated(authorityUser))),
            authorityApiServiceProvider.overrideWithValue(FakeAuthorityApiService()),
          ],
          child: const MaterialApp(
            home: AuthorityHomeScreen(),
          ),
        ),
      );

      await tester.pumpAndSettle();

      expect(find.text('Authority Claims Queue'), findsOneWidget);
      expect(find.text('STATUTORY CLAIMS ADJUDICATOR'), findsOneWidget);
      expect(find.text('New Queue'), findsOneWidget);
      expect(find.text('In Review'), findsOneWidget);
      expect(find.textContaining('All Claims'), findsOneWidget);
    });

    testWidgets('AuthorityClaimReviewScreen renders financial limits, deterministic rules, and advisory duplicate warnings', (tester) async {
      await tester.pumpWidget(
        ProviderScope(
          overrides: [
            authorityApiServiceProvider.overrideWithValue(FakeAuthorityApiService()),
          ],
          child: const MaterialApp(
            home: AuthorityClaimReviewScreen(claimId: 'claim-auth-001'),
          ),
        ),
      );

      await tester.pumpAndSettle();

      expect(find.text('Claim Adjudication Review'), findsOneWidget);
      expect(find.text('Requested'), findsOneWidget);
      expect(find.text('Limit'), findsOneWidget);
      expect(find.text('Payable'), findsOneWidget);
      expect(find.text('Eligibility Assessment Rules'), findsOneWidget);
      expect(find.text('COVERAGE LIMIT CHECK'), findsOneWidget);
      expect(find.text('Duplicate Incident Analysis'), findsOneWidget);
      expect(find.textContaining('Statutory Notice: Duplicate candidates are an advisory signal'), findsOneWidget);
    });
  });

  group('10. Blockchain Integrity & Anchoring Tests', () {
    test('BlockchainStatusModel correctly deserializes connectivity and event metrics', () {
      final json = {
        'is_connected': true,
        'rpc_url': 'http://127.0.0.1:8545',
        'configured_chain_id': 31337,
        'node_chain_id': 31337,
        'block_number': 100,
        'contract_address': '0x5FbDB2315678afecb367f032d93F642f64180aa3',
        'contract_deployed': true,
        'status': 'ONLINE',
        'total_events': 25,
        'unchained_events': 0,
        'pending_events': 3,
        'batched_events': 10,
        'anchored_events': 12,
        'failed_events': 0,
      };

      final status = BlockchainStatusModel.fromJson(json);

      expect(status.isConnected, isTrue);
      expect(status.isNodeOnline, isTrue);
      expect(status.configuredChainId, 31337);
      expect(status.contractDeployed, isTrue);
      expect(status.isContractReady, isTrue);
      expect(status.anchoredEvents, 12);
      expect(status.pendingEvents, 3);
    });

    test('AuditEventVerificationModel correctly deserializes hash-chain linkage outcomes', () {
      final json = {
        'event_id': 'evt-123',
        'outcome': 'VALID',
        'message': 'Cryptographic hash linkage confirmed.',
        'sequence_number': 42,
        'event_hash': '0xhash42',
        'previous_hash': '0xhash41',
        'payload_hash': '0xpayload42',
        'anchoring_status': 'ANCHORED',
        'batch_id': 'batch-01',
        'created_at': '2026-10-11T12:00:00Z',
        'on_chain_verified': true,
      };

      final ver = AuditEventVerificationModel.fromJson(json);

      expect(ver.eventId, 'evt-123');
      expect(ver.outcome, 'VALID');
      expect(ver.isValid, isTrue);
      expect(ver.sequenceNumber, 42);
      expect(ver.onChainVerified, isTrue);
    });

    testWidgets('BlockchainIntegrityScreen renders network status card, counters, and event inspector', (tester) async {
      await tester.pumpWidget(
        ProviderScope(
          overrides: [
            integrityApiServiceProvider.overrideWithValue(FakeIntegrityApiService()),
          ],
          child: const MaterialApp(
            home: BlockchainIntegrityScreen(initialEventId: 'evt-001'),
          ),
        ),
      );

      await tester.pumpAndSettle();

      expect(find.text('Blockchain Audit Integrity'), findsOneWidget);
      expect(find.text('Audit Anchor Smart Contract'), findsOneWidget);
      expect(find.text('Hardhat Node Connected'), findsOneWidget);
      expect(find.text('Anchored'), findsOneWidget);
      expect(find.text('Batched'), findsOneWidget);
      expect(find.text('Pending'), findsOneWidget);
      expect(find.text('Total Chained'), findsOneWidget);
      expect(find.text('Audit Event Hash Verification'), findsOneWidget);
      expect(find.text('Verification Analysis'), findsOneWidget);
      expect(find.text('VALID'), findsOneWidget);
      expect(find.text('ON-CHAIN ANCHORED'), findsOneWidget);
      expect(find.text('Merkle Inclusion Proof'), findsOneWidget);
    });
  });
}
