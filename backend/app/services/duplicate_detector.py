"""
Duplicate Claim Candidate Detector for InsureChain VoiceGuard.
Identifies potential duplicate incidents across customer, registration,
incident date, category, and domain-specific identifiers without auto-rejecting.
"""

from datetime import date, timedelta
from typing import Any, Dict, List, Optional
import psycopg

from app.schemas.claim import DuplicateCandidateResponse


def _normalize_string(val: Optional[str]) -> str:
    if not val:
        return ""
    return "".join(c for c in val.lower() if c.isalnum())


class DuplicateDetector:
    """
    Computes explainable duplicate candidate scores and matches.
    Flags potential duplicates for human adjuster review.
    """

    async def find_candidates(
        self,
        conn: psycopg.AsyncConnection,
        target_claim: Dict[str, Any],
        scope_customer_id: Optional[str] = None,
    ) -> List[DuplicateCandidateResponse]:
        claim_id = target_claim["id"]
        customer_id = target_claim["customer_id"]
        registration_id = target_claim["registration_id"]
        claim_category = target_claim["claim_category"]
        raw_incident = target_claim["incident_date"]
        target_incident_date = (
            date.fromisoformat(raw_incident)
            if isinstance(raw_incident, str)
            else raw_incident
        )
        target_details = target_claim.get("structured_details") or {}

        # Search window +/- 7 days around incident date
        start_date = target_incident_date - timedelta(days=7)
        end_date = target_incident_date + timedelta(days=7)

        # Base query excluding the target claim itself
        query = """
        SELECT id, customer_id, registration_id, claim_category,
               requested_amount, incident_date, structured_details, status
        FROM claims
        WHERE id != %s
        """
        params: List[Any] = [claim_id]

        if scope_customer_id:
            query += " AND customer_id = %s"
            params.append(scope_customer_id)

        query += " AND incident_date BETWEEN %s AND %s;"
        params.extend([start_date, end_date])

        candidates: List[DuplicateCandidateResponse] = []

        async with conn.cursor() as cur:
            await cur.execute(query, tuple(params))
            rows = await cur.fetchall()

            for row in rows:
                c_id = str(row[0])
                c_customer_id = str(row[1])
                c_reg_id = str(row[2])
                c_cat = row[3]
                c_amount = str(row[4])
                c_inc_date = row[5]
                c_details = row[6] if isinstance(row[6], dict) else {}
                c_status = row[7]

                score = 0.0
                reasons: List[str] = []

                # Signal 1: Same customer
                if c_customer_id == customer_id:
                    score += 0.25
                    reasons.append("Identical claimant customer ID")

                # Signal 2: Same policy registration
                if c_reg_id == registration_id:
                    score += 0.25
                    reasons.append("Identical policy registration ID")

                # Signal 3: Same category
                if c_cat == claim_category:
                    score += 0.15
                    reasons.append(f"Identical claim category ({claim_category})")

                # Signal 4: Exact incident date
                c_date = (
                    date.fromisoformat(c_inc_date)
                    if isinstance(c_inc_date, str)
                    else c_inc_date
                )
                if c_date == target_incident_date:
                    score += 0.20
                    reasons.append(f"Exact incident date match ({target_incident_date})")
                else:
                    score += 0.05
                    reasons.append("Incident occurred within 7-day proximity window")

                # Signal 5: Domain identifier matches in structured_details
                for key in (
                    "vehicle_registration_number",
                    "chassis_number",
                    "fir_number",
                    "hospital_name",
                    "invoice_number",
                    "admission_number",
                ):
                    val_target = _normalize_string(str(target_details.get(key, "")))
                    val_cand = _normalize_string(str(c_details.get(key, "")))
                    if val_target and val_cand and val_target == val_cand:
                        score += 0.30
                        reasons.append(f"Exact match on structured identifier '{key}': {target_details.get(key)}")

                final_score = min(round(score, 2), 1.0)
                # Only include as candidate if score meets threshold
                if final_score >= 0.40:
                    candidates.append(
                        DuplicateCandidateResponse(
                            candidate_claim_id=c_id,
                            match_score=final_score,
                            match_reasons=reasons,
                            claim_status=c_status,
                            incident_date=c_date.isoformat(),
                            requested_amount=c_amount,
                            claim_category=c_cat,
                        )
                    )

        # Sort highest score first
        candidates.sort(key=lambda c: c.match_score, reverse=True)
        return candidates


duplicate_detector = DuplicateDetector()
