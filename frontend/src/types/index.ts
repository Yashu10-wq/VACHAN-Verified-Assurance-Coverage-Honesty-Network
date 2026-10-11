export type UserRole = 'CUSTOMER' | 'INSURANCE_AGENT' | 'APPROVAL_AUTHORITY';

export type AccountStatus = 'ACTIVE' | 'PENDING_VERIFICATION' | 'PENDING_APPROVAL' | 'SUSPENDED' | 'REJECTED';

export interface User {
  id: string;
  email: string;
  full_name: string;
  phone?: string;
  role: UserRole;
  account_status: AccountStatus;
  created_at?: string;
}

export type PolicyCategory = 'HEALTH' | 'VEHICLE' | 'TERM_LIFE' | 'PROPERTY' | 'TRAVEL';

export interface PolicyVersion {
  id: string;
  policy_id: string;
  version_number: number;
  document_storage_ref?: string;
  document_checksum?: string;
  effective_date: string;
  expiry_date?: string;
  is_published: boolean;
  terms_json?: {
    clauses?: Array<{
      id: string;
      title: string;
      text: string;
      page_number?: number;
      is_exclusion?: boolean;
    }>;
    waiting_period_exceptions?: string[];
    co_pay_percentage?: number;
  };
}

export interface Policy {
  id: string;
  insurer_name: string;
  policy_name: string;
  policy_code: string;
  category: PolicyCategory;
  description: string;
  coverage_limit: number;
  waiting_period_days: number;
  claim_filing_window_days: number;
  is_active: boolean;
  latest_version?: PolicyVersion;
}

export type RegistrationStatus =
  | 'PENDING_REVIEW'
  | 'PENDING_VERIFICATION'
  | 'AWAITING_CUSTOMER_CONFIRMATION'
  | 'CONFIRMED'
  | 'DECLINED'
  | 'EXPIRED';

export interface ExtractedPromise {
  id: string;
  category: string;
  spoken_promise: string;
  matched_clause_id?: string;
  matched_clause_text?: string;
  page_reference?: number;
  verdict: 'SUPPORTED' | 'PARTLY_TRUE' | 'CONTRADICTED' | 'NOT_IN_POLICY' | 'UNCLEAR';
  explanation: string;
}

export interface Registration {
  id: string;
  customer_id: string;
  agent_id: string;
  policy_id: string;
  policy_version_id: string;
  status: RegistrationStatus;
  customer_consent: boolean;
  consent_notes?: string;
  created_at: string;
  confirmed_at?: string;
  audio_recording_url?: string;
  audio_checksum?: string;
  transcript_text?: string;
  extracted_promises?: ExtractedPromise[];
  policy?: Policy;
  customer?: User;
}

export type ClaimCategory = 'VEHICLE' | 'HOSPITALIZATION' | 'GENERIC';

export type ClaimStatus =
  | 'SUBMITTED'
  | 'UNDER_REVIEW'
  | 'EVIDENCE_REQUESTED'
  | 'APPROVED'
  | 'REJECTED'
  | 'PAID';

export type EvidenceType =
  | 'ACCIDENT_PHOTO'
  | 'REPAIR_ESTIMATE'
  | 'DISCHARGE_SUMMARY'
  | 'HOSPITAL_BILL'
  | 'PRESCRIPTION'
  | 'DIAGNOSTIC_REPORT'
  | 'OTHER';

export interface ClaimEvidence {
  id: string;
  claim_id: string;
  evidence_type: EvidenceType;
  original_filename: string;
  document_storage_ref: string;
  document_checksum: string;
  file_size_bytes: number;
  mime_type: string;
  created_at: string;
}

export interface EvaluatedRule {
  rule_id: string;
  result: 'PASSED' | 'FAILED' | 'WARNING';
  explanation: string;
  details?: Record<string, any>;
}

export interface ClaimAssessment {
  id: string;
  claim_id: string;
  overall_outcome: 'ELIGIBLE' | 'INELIGIBLE' | 'REQUIRES_REVIEW';
  rules_evaluated: EvaluatedRule[];
  requested_amount: number;
  applicable_limit: number;
  potentially_payable_amount: number;
  excess_amount: number;
  missing_evidence?: string[];
  review_flags?: string[];
  assessed_at: string;
}

export interface ClaimStatusHistory {
  id: string;
  claim_id: string;
  previous_status?: ClaimStatus;
  new_status: ClaimStatus;
  transition_reason: string;
  actor_id: string;
  actor_role: UserRole;
  created_at: string;
}

export interface Claim {
  id: string;
  customer_id: string;
  registration_id: string;
  policy_id: string;
  policy_version_id: string;
  claim_category: ClaimCategory;
  status: ClaimStatus;
  requested_amount: number;
  incident_date: string;
  description: string;
  structured_details?: Record<string, any>;
  created_at: string;
  policy?: Policy;
  evidence?: ClaimEvidence[];
  latest_assessment?: ClaimAssessment;
  status_history?: ClaimStatusHistory[];
}

export interface DuplicateCandidate {
  candidate_claim_id: string;
  customer_id: string;
  incident_date: string;
  requested_amount: number;
  status: ClaimStatus;
  similarity_score: number;
  matching_reasons: string[];
}
