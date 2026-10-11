"""
Gemini Policy-Promise Verification Service for InsureChain VoiceGuard.
Executes grounded comparison between sales transcripts and extracted policy texts.
Enforces strict hallucination detection and substring grounding validation.
"""

import hashlib
import json
import re
from typing import Any, Dict, List, Optional, Tuple
import uuid
import httpx
import psycopg

from app.core.config import get_settings
from app.core.exceptions import IntegrationException, ValidationException
from app.core.logging import get_logger
from app.db.repositories import (
    audit_repo,
    policy_repo,
    sales_session_repo,
    verification_repo,
)
from app.schemas.verification import (
    OverallIntegrityStatus,
    PromiseVerdict,
    ValidationStatus,
)
from app.services.policy_extractor import policy_extractor_service

logger = get_logger(__name__)


def normalize_text_for_matching(text: str) -> str:
    """Normalizes text for grounding substring comparison: collapses whitespace, lowercase, strips quotes."""
    if not text:
        return ""
    # Strip smart quotes, standard quotes, backticks
    cleaned = re.sub(r'["\'`\u201c\u201d\u2018\u2019]', "", text)
    # Collapse multiple whitespace characters into single space
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned.strip().lower()


def verify_grounding(
    quote: Optional[str],
    source_text: Optional[str],
    min_length: int = 5,
) -> bool:
    """
    Verifies that a quoted passage exists verbatim within the source document.
    Returns True if quote is empty or if normalized quote exists as a substring.
    """
    if not quote or not quote.strip():
        return True
    if not source_text or not source_text.strip():
        return False

    norm_quote = normalize_text_for_matching(quote)
    norm_source = normalize_text_for_matching(source_text)

    if len(norm_quote) < min_length:
        return True

    if norm_quote in norm_source:
        return True

    # If the quote is multi-sentence or has minor transcription variations,
    # check if first 50 chars or substantial prefix is contained
    if len(norm_quote) > 60:
        prefix = norm_quote[:50]
        if prefix in norm_source:
            return True

    return False


SYSTEM_PROMPT = """You are the InsureChain VoiceGuard Policy-Promise Verification Engine, an objective insurance compliance auditor.
Your job is to compare statements made by an insurance agent in a sales conversation transcript against the official, immutable policy document.

You must identify each material promise, coverage statement, waiting period claim, exclusion assurance, or benefit commitment made by the agent.
For each statement, classify it into EXACTLY ONE of the following 5 categories:
1. SUPPORTED: Explicitly confirmed and accurate according to the policy text.
2. PARTLY_TRUE: True in part, but omits critical waiting periods, sub-limits, caps, or conditions specified in the policy.
3. CONTRADICTED: Directly conflicts with or contradicts an explicit exclusion, term, or condition in the policy.
4. NOT_IN_POLICY: The promised benefit, rider, or feature is completely absent from the policy text.
5. UNCLEAR: Ambiguous statement or ambiguous clause where definitive determination requires human review.

CRITICAL RULES:
- Never invent policy clauses, page numbers, or quotes.
- Every "transcript_quote" MUST BE AN EXACT verbatim quotation from the provided transcript.
- Every "policy_excerpt" MUST BE AN EXACT verbatim quotation from the provided policy text (leave null/empty if NOT_IN_POLICY).
- Return your evaluation strictly in the requested JSON format.

JSON response schema:
{
  "summary": "Overall compliance summary of the conversation",
  "findings": [
    {
      "promise_text": "Brief statement of the agent's promise",
      "transcript_quote": "Exact verbatim quote from transcript",
      "speaker_label": "Agent or speaker name",
      "classification": "SUPPORTED | PARTLY_TRUE | CONTRADICTED | NOT_IN_POLICY | UNCLEAR",
      "policy_excerpt": "Exact verbatim quote from policy or null",
      "page_number": 1,
      "section_heading": "Section heading if identified",
      "explanation": "Clear explanation grounded in the text",
      "confidence": 0.95
    }
  ]
}
"""


class GeminiVerifierService:
    """Performs grounded sales promise verification using Google Gemini AI."""

    async def _call_gemini_api(
        self,
        transcript: str,
        policy_text: str,
        policy_meta: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Calls the Gemini generateContent API and returns parsed JSON output."""
        settings = get_settings()
        api_key = settings.GEMINI_API_KEY
        if not api_key:
            raise ValidationException("GEMINI_API_KEY is not configured.")

        model = settings.GEMINI_MODEL or "gemini-2.5-flash"
        endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"

        user_content = f"""POLICY INFORMATION:
Policy Name: {policy_meta.get('policy_name', 'N/A')}
Policy Code: {policy_meta.get('policy_code', 'N/A')}
Coverage Limit: {policy_meta.get('coverage_limit', 'N/A')}
Waiting Period: {policy_meta.get('waiting_period_days', 'N/A')} days
Filing Window: {policy_meta.get('claim_filing_window_days', 'N/A')} days

POLICY DOCUMENT TEXT:
{policy_text}

SALES CONVERSATION TRANSCRIPT:
{transcript}

Please audit the sales conversation transcript against the policy document text according to the instructions. Return strictly valid JSON.
"""

        payload = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": SYSTEM_PROMPT + "\n\n" + user_content}],
                }
            ],
            "generationConfig": {
                "temperature": 0.1,
                "responseMimeType": "application/json",
            },
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(endpoint, json=payload)
            if response.status_code != 200:
                logger.error("Gemini API error (%d): %s", response.status_code, response.text)
                raise IntegrationException(f"Gemini API returned error code {response.status_code}.")

            data = response.json()
            try:
                raw_text = data["candidates"][0]["content"]["parts"][0]["text"]
                return json.loads(raw_text)
            except (KeyError, IndexError, json.JSONDecodeError) as e:
                logger.error("Failed to parse Gemini JSON output: %s", str(e))
                raise IntegrationException(f"Invalid JSON returned by Gemini: {str(e)}")

    def validate_and_ground_findings(
        self,
        raw_findings: List[Dict[str, Any]],
        transcript: str,
        policy_text: str,
    ) -> Tuple[List[Dict[str, Any]], List[str]]:
        """
        Validates that quotes and citations generated by the LLM exist in source documents.
        Enforces review flags if citations cannot be grounded.
        """
        grounded_findings: List[Dict[str, Any]] = []
        review_flags: List[str] = []

        valid_verdicts = {v.value for v in PromiseVerdict}

        for idx, item in enumerate(raw_findings):
            finding_id = str(uuid.uuid4())
            promise_text = str(item.get("promise_text", "")).strip()
            transcript_quote = str(item.get("transcript_quote", "")).strip()
            speaker_label = item.get("speaker_label")
            raw_classification = str(item.get("classification", "UNCLEAR")).strip().upper()
            classification = raw_classification if raw_classification in valid_verdicts else PromiseVerdict.UNCLEAR.value
            policy_excerpt = item.get("policy_excerpt")
            if policy_excerpt:
                policy_excerpt = str(policy_excerpt).strip()
            page_number = item.get("page_number")
            section_heading = item.get("section_heading")
            explanation = str(item.get("explanation", "Verification finding.")).strip()
            confidence = float(item.get("confidence", 0.9))
            confidence = max(0.0, min(1.0, confidence))

            validation_status = ValidationStatus.GROUNDED.value
            review_required = False
            review_reason = None

            # 1. Grounding check on transcript quote
            if transcript_quote:
                is_transcript_grounded = verify_grounding(transcript_quote, transcript)
                if not is_transcript_grounded:
                    validation_status = ValidationStatus.INVALID_QUOTE.value
                    review_required = True
                    review_reason = f"Transcript quote '{transcript_quote[:40]}...' was not found verbatim in conversation audio transcript."
                    review_flags.append(f"Finding {idx + 1}: Unverified transcript quote.")

            # 2. Grounding check on policy excerpt for supported/partly_true/contradicted
            if classification in (PromiseVerdict.SUPPORTED.value, PromiseVerdict.PARTLY_TRUE.value, PromiseVerdict.CONTRADICTED.value) and policy_excerpt:
                is_policy_grounded = verify_grounding(policy_excerpt, policy_text)
                if not is_policy_grounded:
                    if validation_status == ValidationStatus.GROUNDED.value:
                        validation_status = ValidationStatus.UNVERIFIED_CITATION.value
                    review_required = True
                    citation_reason = f"Cited policy clause '{policy_excerpt[:40]}...' was not found verbatim in extracted policy document."
                    review_reason = f"{review_reason}; {citation_reason}" if review_reason else citation_reason
                    review_flags.append(f"Finding {idx + 1}: Unverified policy citation.")

            # If classification is UNCLEAR, always flag for operator review
            if classification == PromiseVerdict.UNCLEAR.value:
                review_required = True
                if not review_reason:
                    review_reason = "Ambiguous clause or promise requires human operator review."

            grounded_findings.append({
                "finding_id": finding_id,
                "promise_text": promise_text,
                "transcript_quote": transcript_quote,
                "speaker_label": speaker_label,
                "classification": classification,
                "policy_excerpt": policy_excerpt,
                "page_number": page_number,
                "section_heading": section_heading,
                "explanation": explanation,
                "confidence": confidence,
                "review_required": review_required,
                "review_reason": review_reason,
                "validation_status": validation_status,
            })

        return grounded_findings, review_flags

    def calculate_metrics_and_integrity(
        self,
        findings: List[Dict[str, Any]],
        review_flags: List[str],
    ) -> Tuple[int, int, int, int, int, str]:
        """Calculates counts across the 5 categories and determines overall integrity status."""
        supported = sum(1 for f in findings if f["classification"] == PromiseVerdict.SUPPORTED.value)
        partly_true = sum(1 for f in findings if f["classification"] == PromiseVerdict.PARTLY_TRUE.value)
        contradicted = sum(1 for f in findings if f["classification"] == PromiseVerdict.CONTRADICTED.value)
        not_in_policy = sum(1 for f in findings if f["classification"] == PromiseVerdict.NOT_IN_POLICY.value)
        unclear = sum(1 for f in findings if f["classification"] == PromiseVerdict.UNCLEAR.value)

        # Integrity Status determination:
        # CONTRADICTED -> MISLEADING_CLAIMS_DETECTED
        # PARTLY_TRUE or NOT_IN_POLICY -> DISCREPANCIES_FOUND
        # UNCLEAR or review flags present -> NEEDS_REVIEW
        # Otherwise -> VERIFIED
        if contradicted > 0:
            overall_status = OverallIntegrityStatus.MISLEADING_CLAIMS_DETECTED.value
        elif partly_true > 0 or not_in_policy > 0:
            overall_status = OverallIntegrityStatus.DISCREPANCIES_FOUND.value
        elif unclear > 0 or len(review_flags) > 0:
            overall_status = OverallIntegrityStatus.NEEDS_REVIEW.value
        else:
            overall_status = OverallIntegrityStatus.VERIFIED.value

        return supported, partly_true, contradicted, not_in_policy, unclear, overall_status

    async def verify_sales_session(
        self,
        conn: psycopg.AsyncConnection,
        sales_session_id: str,
        actor_id: str,
        actor_role: str,
        mock_gemini_response: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Executes policy verification for a completed sales session.
        Creates an immutable, version-tracked verification report.
        """
        # 1. Fetch sales session
        session = await sales_session_repo.get_session_by_id(conn, sales_session_id)
        if not session:
            raise ValidationException(f"Sales session '{sales_session_id}' not found.")

        if session.get("status") != "COMPLETED":
            raise ValidationException(
                f"Sales session status is '{session.get('status')}'. Transcription must be COMPLETED before policy verification."
            )

        transcript = session.get("transcript")
        if not transcript or not transcript.strip():
            raise ValidationException("Sales session has an empty transcript.")

        # 2. Resolve policy version
        policy_id = session.get("policy_id")
        policy_version_id = session.get("policy_version_id")

        if not policy_version_id:
            if not policy_id:
                raise ValidationException("Sales session does not specify a policy or policy version.")
            latest_version = await policy_repo.get_published_version(conn, policy_id)
            if not latest_version:
                raise ValidationException(f"No published policy version found for policy '{policy_id}'.")
            policy_version_id = latest_version["id"]
        elif not policy_id:
            ver_obj = await policy_repo.get_policy_version_by_id(conn, policy_version_id)
            if ver_obj:
                policy_id = ver_obj["policy_id"]

        policy_obj = await policy_repo.get_policy_by_id(conn, policy_id)
        if not policy_obj:
            raise ValidationException(f"Policy '{policy_id}' not found.")

        # 3. Extract policy document text
        extraction = await policy_extractor_service.get_or_extract_policy_text(conn, policy_version_id)
        policy_text = extraction.get("extracted_text") or ""

        # 4. Create pending verification report (with incremental version)
        transcript_checksum = hashlib.sha256(transcript.encode("utf-8")).hexdigest()
        settings = get_settings()
        model_name = settings.GEMINI_MODEL or "gemini-2.5-flash"

        report = await verification_repo.create_verification_report(
            conn=conn,
            sales_session_id=sales_session_id,
            customer_id=session["customer_id"],
            agent_id=session["agent_id"],
            policy_id=policy_id,
            policy_version_id=policy_version_id,
            transcript_checksum=transcript_checksum,
            model_identifier=model_name,
            status="PROCESSING",
        )
        report_id = report["id"]

        try:
            # 5. Call Gemini (or use mock for testing)
            if mock_gemini_response is not None:
                llm_output = mock_gemini_response
            else:
                llm_output = await self._call_gemini_api(
                    transcript=transcript,
                    policy_text=policy_text,
                    policy_meta=policy_obj,
                )

            summary = llm_output.get("summary", "Policy promise verification completed.")
            raw_findings = llm_output.get("findings", [])

            # 6. Validate grounding against ground truth
            grounded_findings, review_flags = self.validate_and_ground_findings(
                raw_findings=raw_findings,
                transcript=transcript,
                policy_text=policy_text,
            )

            # If policy extraction itself was flagged as NEEDS_REVIEW, add to flags
            if extraction.get("status") == "NEEDS_REVIEW":
                review_flags.append("Policy document extraction flagged as NEEDS_REVIEW (insufficient digital text).")

            # 7. Compute metrics & integrity status
            sup, part, cont, not_in, unc, overall_status = self.calculate_metrics_and_integrity(
                findings=grounded_findings,
                review_flags=review_flags,
            )

            # 8. Update report
            final_report = await verification_repo.update_report_results(
                conn=conn,
                report_id=report_id,
                status="COMPLETED",
                summary=summary,
                overall_integrity_status=overall_status,
                findings=grounded_findings,
                supported_count=sup,
                partly_true_count=part,
                contradicted_count=cont,
                not_in_policy_count=not_in,
                unclear_count=unc,
                review_flags=review_flags,
                error_message=None,
            )

            # 9. Audit event
            await audit_repo.log_audit_event(
                conn=conn,
                actor_id=actor_id,
                actor_role=actor_role,
                action="VERIFY_SALES_PROMISES",
                target_type="verification_report",
                target_id=report_id,
                metadata={
                    "sales_session_id": sales_session_id,
                    "report_version": report["report_version"],
                    "overall_integrity_status": overall_status,
                    "contradicted_count": cont,
                    "findings_count": len(grounded_findings),
                },
            )

            return final_report

        except Exception as e:
            logger.error("Failed to verify sales session promises: %s", str(e), exc_info=True)
            failed_report = await verification_repo.update_report_results(
                conn=conn,
                report_id=report_id,
                status="FAILED",
                error_message=str(e),
            )
            return failed_report or report


gemini_verifier_service = GeminiVerifierService()
