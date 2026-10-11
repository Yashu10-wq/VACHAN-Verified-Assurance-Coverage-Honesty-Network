"""
Deterministic Claims Eligibility Engine for InsureChain VoiceGuard.
Executes non-AI, auditable, deterministic rule-based assessments
using exact decimal arithmetic and policy version terms.
"""

from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from app.core.security import AssessmentOutcome, RuleOutcome


@dataclass
class RuleResult:
    rule_id: str
    result: RuleOutcome
    explanation: str
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AssessmentEvaluation:
    overall_outcome: AssessmentOutcome
    rules_evaluated: List[RuleResult]
    requested_amount: Decimal
    applicable_limit: Decimal
    potentially_payable_amount: Decimal
    excess_amount: Decimal
    missing_evidence: List[str]
    review_flags: List[str]


CATEGORY_DEFAULT_REQUIRED_EVIDENCE = {
    "VEHICLE": ["REGISTRATION_CERTIFICATE", "INCIDENT_PHOTO"],
    "MEDICAL": ["MEDICAL_BILL", "DISCHARGE_SUMMARY"],
    "GENERIC": ["SUPPORTING_DOCUMENT"],
}


class DeterministicEligibilityEngine:
    """
    Evaluates policy terms and claim attributes deterministically.
    Does not use LLMs or probabilistic heuristics.
    """

    def evaluate_claim(
        self,
        claim: Dict[str, Any],
        registration: Dict[str, Any],
        policy: Dict[str, Any],
        policy_version: Dict[str, Any],
        evidence_list: List[Dict[str, Any]],
        duplicate_candidate_count: int = 0,
    ) -> AssessmentEvaluation:
        rules: List[RuleResult] = []
        missing_evidence: List[str] = []
        review_flags: List[str] = []

        # Parse amounts using exact Decimal precision (quantized to 2 decimal places)
        requested_amount = Decimal(str(claim["requested_amount"])).quantize(Decimal("0.01"))
        coverage_limit = Decimal(str(policy["coverage_limit"])).quantize(Decimal("0.01"))

        # 1. Rule: Policy Registration Status
        reg_status = registration.get("status")
        if reg_status == "CONFIRMED":
            rules.append(
                RuleResult(
                    rule_id="RULE_REGISTRATION_STATUS",
                    result=RuleOutcome.PASS,
                    explanation="Policy registration is actively CONFIRMED by customer.",
                    details={"status": reg_status},
                )
            )
        else:
            rules.append(
                RuleResult(
                    rule_id="RULE_REGISTRATION_STATUS",
                    result=RuleOutcome.FAIL,
                    explanation=f"Policy registration is not confirmed (current status: {reg_status}).",
                    details={"status": reg_status},
                )
            )

        # 2. Rule: Policy Active and Version Published
        is_active = policy.get("is_active", False)
        is_published = policy_version.get("is_published", False)
        if is_active and is_published:
            rules.append(
                RuleResult(
                    rule_id="RULE_POLICY_STATUS",
                    result=RuleOutcome.PASS,
                    explanation="Policy is active and target policy version is published.",
                    details={"is_active": is_active, "is_published": is_published},
                )
            )
        else:
            rules.append(
                RuleResult(
                    rule_id="RULE_POLICY_STATUS",
                    result=RuleOutcome.FAIL,
                    explanation=f"Policy or version inactive (policy active: {is_active}, version published: {is_published}).",
                    details={"is_active": is_active, "is_published": is_published},
                )
            )

        # 3. Rule: Category Matching
        claim_cat = str(claim.get("claim_category", "")).upper()
        policy_cat = str(policy.get("category", "")).upper()
        category_match = False
        if claim_cat == policy_cat:
            category_match = True
        elif claim_cat == "MEDICAL" and policy_cat in ("HOSPITALIZATION", "MEDICAL"):
            category_match = True
        elif policy_cat == "GENERIC":
            category_match = True

        if category_match:
            rules.append(
                RuleResult(
                    rule_id="RULE_CATEGORY_MATCH",
                    result=RuleOutcome.PASS,
                    explanation=f"Claim category '{claim_cat}' is covered under policy category '{policy_cat}'.",
                    details={"claim_category": claim_cat, "policy_category": policy_cat},
                )
            )
        else:
            rules.append(
                RuleResult(
                    rule_id="RULE_CATEGORY_MATCH",
                    result=RuleOutcome.FAIL,
                    explanation=f"Claim category '{claim_cat}' does not match policy category '{policy_cat}'.",
                    details={"claim_category": claim_cat, "policy_category": policy_cat},
                )
            )

        # 4. Rule: Coverage Period & Waiting Period
        # Dates
        raw_incident = claim.get("incident_date")
        if isinstance(raw_incident, str):
            incident_date = date.fromisoformat(raw_incident)
        elif isinstance(raw_incident, date):
            incident_date = raw_incident
        else:
            incident_date = date.today()

        raw_effective = policy_version.get("effective_date")
        effective_date = (
            date.fromisoformat(raw_effective)
            if isinstance(raw_effective, str)
            else (raw_effective or date.min)
        )

        raw_expiry = policy_version.get("expiry_date")
        expiry_date = (
            date.fromisoformat(raw_expiry)
            if isinstance(raw_expiry, str)
            else raw_expiry
        )

        waiting_period = int(policy.get("waiting_period_days", 0))

        if incident_date < effective_date:
            rules.append(
                RuleResult(
                    rule_id="RULE_COVERAGE_PERIOD",
                    result=RuleOutcome.FAIL,
                    explanation=f"Incident date ({incident_date}) occurred before policy effective date ({effective_date}).",
                    details={
                        "incident_date": str(incident_date),
                        "effective_date": str(effective_date),
                    },
                )
            )
        elif expiry_date and incident_date > expiry_date:
            rules.append(
                RuleResult(
                    rule_id="RULE_COVERAGE_PERIOD",
                    result=RuleOutcome.FAIL,
                    explanation=f"Incident date ({incident_date}) occurred after policy expiry date ({expiry_date}).",
                    details={
                        "incident_date": str(incident_date),
                        "expiry_date": str(expiry_date),
                    },
                )
            )
        elif incident_date > date.today():
            rules.append(
                RuleResult(
                    rule_id="RULE_COVERAGE_PERIOD",
                    result=RuleOutcome.FAIL,
                    explanation=f"Incident date ({incident_date}) cannot be in the future.",
                    details={"incident_date": str(incident_date)},
                )
            )
        else:
            rules.append(
                RuleResult(
                    rule_id="RULE_COVERAGE_PERIOD",
                    result=RuleOutcome.PASS,
                    explanation=f"Incident date ({incident_date}) is within the active coverage window.",
                    details={
                        "incident_date": str(incident_date),
                        "effective_date": str(effective_date),
                        "expiry_date": str(expiry_date) if expiry_date else None,
                    },
                )
            )

        # 5. Rule: Claim Filing Deadline Window
        raw_submission = claim.get("submission_timestamp") or claim.get("created_at")
        if isinstance(raw_submission, str):
            submission_date = datetime.fromisoformat(raw_submission.replace("Z", "+00:00")).date()
        elif isinstance(raw_submission, datetime):
            submission_date = raw_submission.date()
        else:
            submission_date = date.today()

        filing_window_days = int(policy.get("claim_filing_window_days", 30))
        days_since_incident = (submission_date - incident_date).days

        if days_since_incident > filing_window_days:
            rules.append(
                RuleResult(
                    rule_id="RULE_FILING_DEADLINE",
                    result=RuleOutcome.FAIL,
                    explanation=f"Claim submitted {days_since_incident} days after incident, exceeding the allowed {filing_window_days}-day filing window.",
                    details={
                        "days_since_incident": days_since_incident,
                        "filing_window_days": filing_window_days,
                    },
                )
            )
        else:
            rules.append(
                RuleResult(
                    rule_id="RULE_FILING_DEADLINE",
                    result=RuleOutcome.PASS,
                    explanation=f"Claim submitted within {filing_window_days} days of incident ({days_since_incident} days elapsed).",
                    details={
                        "days_since_incident": days_since_incident,
                        "filing_window_days": filing_window_days,
                    },
                )
            )

        # 6. Rule: Amount Validity
        if requested_amount <= Decimal("0.00"):
            rules.append(
                RuleResult(
                    rule_id="RULE_AMOUNT_VALIDITY",
                    result=RuleOutcome.FAIL,
                    explanation=f"Requested amount ({requested_amount}) must be strictly positive.",
                    details={"requested_amount": str(requested_amount)},
                )
            )
        else:
            rules.append(
                RuleResult(
                    rule_id="RULE_AMOUNT_VALIDITY",
                    result=RuleOutcome.PASS,
                    explanation=f"Requested amount ({requested_amount}) is a valid positive value.",
                    details={"requested_amount": str(requested_amount)},
                )
            )

        # 7. Rule: Coverage Limit & Potentially Payable Amount
        # Strict rule: requested amount cannot exceed policy coverage limit
        if requested_amount <= coverage_limit:
            potentially_payable_amount = requested_amount
            excess_amount = Decimal("0.00")
            rules.append(
                RuleResult(
                    rule_id="RULE_COVERAGE_LIMIT",
                    result=RuleOutcome.PASS,
                    explanation=f"Requested amount of ₹{requested_amount} is within policy coverage limit of ₹{coverage_limit}.",
                    details={
                        "requested_amount": str(requested_amount),
                        "coverage_limit": str(coverage_limit),
                        "excess_amount": "0.00",
                        "potentially_payable_amount": str(potentially_payable_amount),
                    },
                )
            )
        else:
            potentially_payable_amount = coverage_limit
            excess_amount = requested_amount - coverage_limit
            rules.append(
                RuleResult(
                    rule_id="RULE_COVERAGE_LIMIT",
                    result=RuleOutcome.FAIL,
                    explanation=(
                        f"Requested amount of ₹{requested_amount} exceeds policy coverage limit "
                        f"of ₹{coverage_limit} by ₹{excess_amount}. "
                        "Under strict policy limits, full-request exceeds coverage."
                    ),
                    details={
                        "requested_amount": str(requested_amount),
                        "coverage_limit": str(coverage_limit),
                        "excess_amount": str(excess_amount),
                        "potentially_payable_amount": str(potentially_payable_amount),
                    },
                )
            )

        # 8. Rule: Required Evidence Completeness
        terms_json = policy_version.get("terms_json") or {}
        policy_required = terms_json.get("required_evidence")
        if not policy_required:
            policy_required = CATEGORY_DEFAULT_REQUIRED_EVIDENCE.get(claim_cat, ["SUPPORTING_DOCUMENT"])

        submitted_types = {e.get("evidence_type") for e in evidence_list}
        missing = [req for req in policy_required if req not in submitted_types]

        if missing:
            missing_evidence.extend(missing)
            rules.append(
                RuleResult(
                    rule_id="RULE_EVIDENCE_COMPLETENESS",
                    result=RuleOutcome.NEEDS_REVIEW,
                    explanation=f"Missing required evidence document(s): {', '.join(missing)}.",
                    details={
                        "required_evidence": policy_required,
                        "submitted_evidence": list(submitted_types),
                        "missing": missing,
                    },
                )
            )
        else:
            rules.append(
                RuleResult(
                    rule_id="RULE_EVIDENCE_COMPLETENESS",
                    result=RuleOutcome.PASS,
                    explanation=f"All required evidence documents provided ({len(evidence_list)} file(s)).",
                    details={
                        "required_evidence": policy_required,
                        "submitted_evidence": list(submitted_types),
                    },
                )
            )

        # 9. Rule: Exclusions Check
        exclusions = terms_json.get("exclusions", [])
        desc_lower = str(claim.get("description", "")).lower()
        matched_exclusions = [ex for ex in exclusions if ex.lower() in desc_lower]
        if matched_exclusions:
            rules.append(
                RuleResult(
                    rule_id="RULE_POLICY_EXCLUSIONS",
                    result=RuleOutcome.NEEDS_REVIEW,
                    explanation=f"Incident description mentions potential excluded clause: {', '.join(matched_exclusions)}.",
                    details={"matched_exclusions": matched_exclusions},
                )
            )
            review_flags.append(f"Potential policy exclusion matched: {', '.join(matched_exclusions)}")
        else:
            rules.append(
                RuleResult(
                    rule_id="RULE_POLICY_EXCLUSIONS",
                    result=RuleOutcome.PASS,
                    explanation="No explicit policy exclusions triggered by incident description.",
                    details={"exclusions_checked": len(exclusions)},
                )
            )

        # 10. Duplicate Candidate Review Flag
        if duplicate_candidate_count > 0:
            review_flags.append(
                f"Potential duplicate claim candidate detected ({duplicate_candidate_count} similar claim(s) found)."
            )

        # Compute Overall Outcome
        has_fail = any(r.result == RuleOutcome.FAIL for r in rules)
        has_needs_review = any(r.result == RuleOutcome.NEEDS_REVIEW for r in rules)

        if has_fail:
            overall_outcome = AssessmentOutcome.INELIGIBLE
        elif has_needs_review or len(review_flags) > 0:
            overall_outcome = AssessmentOutcome.NEEDS_REVIEW
        else:
            overall_outcome = AssessmentOutcome.ELIGIBLE

        return AssessmentEvaluation(
            overall_outcome=overall_outcome,
            rules_evaluated=rules,
            requested_amount=requested_amount,
            applicable_limit=coverage_limit,
            potentially_payable_amount=potentially_payable_amount,
            excess_amount=excess_amount,
            missing_evidence=missing_evidence,
            review_flags=review_flags,
        )


eligibility_engine = DeterministicEligibilityEngine()
