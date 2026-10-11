# InsureChain VoiceGuard — Project Context & System Architecture

> **VORTEXA 3.0 Hackathon** | **Problem Statement B-02**: Policy-Aware Insurance Claims Workflow  
> **Domain**: Blockchain & Decentralized Trust  
> **Technology Sponsor**: ElevenLabs  
> **Repository**: `insurechain-voiceguard`

---

## 1. Executive Summary & Identity

**InsureChain VoiceGuard** is a next-generation decentralized insurance platform designed to solve systemic trust deficits across the insurance lifecycle: **sales misrepresentation**, **opaque claims adjudication**, **unverifiable policy state transitions**, and **tamperable audit logs**.

Combining **Vaada-inspired customer protection**, **deterministic claims processing**, **multimodal document extraction**, **ElevenLabs conversational voice AI**, and **EVM blockchain hash anchoring**, the system establishes end-to-end transparency and accountability from policy inception to claim settlement.

### Important Prototype Disclosure
All customers, policies, registrations, claims, medical documents, and payments in this project are **synthetic simulations**. The project is an academic prototype built for VORTEXA 3.0 and does not represent an actual insurance company or process legal transactions.

---

## 2. Core Pillars

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│                           INSURECHAIN VOICEGUARD                                 │
└──────────────────────────────────────────────────────────────────────────────────┘
       │                                 │                                 │
       ▼                                 ▼                                 ▼
┌─────────────────────────┐   ┌─────────────────────────┐   ┌─────────────────────────┐
│     VAADA INTEGRITY     │   │  DETERMINISTIC CLAIMS   │   │   DECENTRALIZED TRUST   │
│ • Consent recording     │   │ • Rule-based engine     │   │ • SHA-256 audit chaining│
│ • Promise extraction    │   │ • Multi-signal duplicate│   │ • EVM smart contract    │
│ • Clause contradictions │   │ • Strict state machine  │   │   hash anchoring        │
│ • Explicit confirmation │   │ • Above-limit excess    │   │ • Sensitive data off-   │
│ • ElevenLabs voice AI   │   │   calculation           │   │   chain                 │
└─────────────────────────┘   └─────────────────────────┘   └─────────────────────────┘
```

### A. Vaada-Inspired Customer Protection (Sales Integrity)
- **Agent Field Recording**: An agent records the sales conversation directly through the app only after affirmative customer consent.
- **Promise Extraction**: Audio is transcribed via ElevenLabs; structured AI extracts promises regarding benefits, coverage limits, exclusions, and waiting periods.
- **Clause Grounding**: Extracted promises are matched against the actual policy wording to flag contradictions, unsupported claims, or partial truths.
- **Gated Activation**: The policy remains `PENDING_CONFIRMATION` until the customer personally reviews the recording, transcript, and contradiction report, and explicitly confirms the purchase.

### B. Policy-Aware Claims Workflow
- **Category-Specific Claims**: Supports configurable claim submissions across Vehicle Insurance, Hospitalization/Mediclaim, and Generic Insurance.
- **Deterministic Eligibility Engine**: Evaluates claims against policy rules (filing window, exclusions, incident date, limits) independently of any LLM, outputting stable rule IDs.
- **Above-Limit Excess Calculation**: Flags claims exceeding coverage limits without altering customer claims, calculating the maximum potentially payable amount and excess.
- **Duplicate Incident Detection**: Evaluates semantic similarity, incident dates, and evidence hashes across claims to alert authorities to duplicates.
- **Controlled State Machine**: Server-side transitions (`SUBMITTED` → `UNDER_REVIEW` ↔ `EVIDENCE_REQUESTED` → `APPROVED`/`REJECTED` → `PAID`) with transactional logging of accepted and refused actions.

### C. ElevenLabs Voice AI
- Speech-to-text for high-accuracy sales conversation transcription.
- Conversational voice assistant for policy coverage, exclusions, waiting periods, and claim inquiries.
- Text-to-speech audio synthesis for explainable, spoken claim outcomes and decisions.

### D. Blockchain-Backed Audit Integrity
- Canonical SHA-256 hashing for all state changes and authority decisions.
- Cryptographic hash chaining (`previous_hash` → `current_hash`).
- Periodic hash anchoring to a Solidity smart contract deployed on an EVM development network (Hardhat).
- Strict off-chain privacy: personal data, audio, and documents remain securely off-chain.

---

## 3. System Architecture

```
                 ┌───────────────────────────────────────────┐
                 │          Mobile Client (Flutter)          │
                 │   • Android (Material 3)                  │
                 │   • Riverpod + GoRouter + Dio             │
                 └─────────────────────┬─────────────────────┘
                                       │ HTTPS / REST
                                       ▼
                 ┌───────────────────────────────────────────┐
                 │          Web Client (React + Vite)        │
                 │   • TypeScript + Tailwind CSS             │
                 │   • Recharts + Lucide                     │
                 └─────────────────────┬─────────────────────┘
                                       │ HTTPS / REST
                                       ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│                           CENTRAL FASTAPI BACKEND                                │
│                                                                                  │
│  ┌─────────────────────────┐  ┌─────────────────────────┐  ┌──────────────────┐  │
│  │     Auth & RBAC         │  │ Promise Extraction &    │  │ Deterministic    │  │
│  │  (Customer/Agent/Admin) │  │ Clause Comparator       │  │ Eligibility Engine│ │
│  └─────────────────────────┘  └─────────────────────────┘  └──────────────────┘  │
│  ┌─────────────────────────┐  ┌─────────────────────────┐  ┌──────────────────┐  │
│  │ Document OCR Pipeline   │  │ State Machine Engine    │  │ Audit Chaining & │  │
│  │ (PyMuPDF / Tesseract)   │  │ (Strict Transitions)    │  │ Web3 Anchor      │  │
│  └─────────────────────────┘  └─────────────────────────┘  └──────────────────┘  │
└───────┬───────────────────────────────┬──────────────────────────────┬───────────┘
        │ Parameterized SQL             │ REST API                     │ JSON-RPC
        ▼                               ▼                              ▼
┌─────────────────────────┐   ┌─────────────────────────┐   ┌──────────────────────┐
│  Neon Cloud PostgreSQL  │   │     ElevenLabs APIs     │   │  Hardhat EVM Node    │
│  • Psycopg 3            │   │  • STT (Transcription)  │   │  • Solidity Anchor   │
│  • Relational Schema    │   │  • TTS (Spoken Expl.)   │   │  • Hash Verification │
│  • Strict Constraints   │   │  • Conversational Agent │   │  • Immutable Ledger  │
└─────────────────────────┘   └─────────────────────────┘   └──────────────────────┘
```

---

## 4. User Roles & Access Control

The platform enforces **strictly three** user roles across both mobile and web clients:

| Role | Primary Responsibilities | Scope Limitations |
| :--- | :--- | :--- |
| **Customer** | View policies, listen to recordings, review promises vs. clauses, confirm/decline registrations, submit claims with evidence, ask voice assistant questions, track claim lifecycle. | Cannot view other customers' records; cannot approve or edit claims. |
| **Insurance Agent** | Select schemes, initiate consent-gated recordings, register synthetic clients, upload preliminary documents, inspect extracted promises. | Cannot activate policies without explicit customer confirmation; cannot adjudicate or approve claims. |
| **Approval Authority** | Review claims across customers, inspect eligibility rule breakdowns, review OCR/duplicate alerts, request evidence, approve/reject claims, trigger simulated payments, verify blockchain anchors. | Must follow server-enforced state machine; cannot bypass rule validation or delete audit events. |

---

## 5. Functional Modules Breakdown

### Module 1: Agent-Initiated Sales Recording
- Affirmative customer consent screen before recording starts.
- Real-time audio waveform visualizer and visible recording indicator.
- Off-chain secure file storage with SHA-256 hash generation.
- Asynchronous transcription via ElevenLabs STT.

### Module 2: Promise Extraction & Policy Clause Comparison
- LLM-assisted extraction of commitments (full reimbursement, waiting periods, copays, coverage dates).
- Grounded matching against scheme clauses producing one of 5 verdicts:
  `SUPPORTED`, `PARTLY_TRUE`, `CONTRADICTED`, `NOT_IN_POLICY`, `UNCLEAR`.
- Detailed clause citation with section, exact text, and PDF page number.

### Module 3: Customer Confirmation & Activation
- Registration begins in `PENDING_CONFIRMATION`.
- Replay audio, read transcript, and inspect contradiction alerts.
- Two-factor explicit confirmation activating the policy and issuing a simulated policy ID.
- Rejection sets the state to `DECLINED` (no policy issued).

### Module 4: Policy Management & Notification Engine
- Policy statuses: `Pending Confirmation`, `Active`, `Expiring Soon`, `Expired`, `Declined`.
- Display limits, covered/excluded categories, waiting periods, and premium dates.
- Idempotent in-app notification triggers for premiums, renewals, and claims.

### Module 5: ElevenLabs Voice Policy Assistant
- Text and voice queries regarding coverage, exclusions, waiting periods, and claim requirements.
- Spoken decision explanation playback on demand.
- Transparent demonstration fallback mode if ElevenLabs credentials are not configured.

### Module 6: Category-Specific Claim Submission
- Guided workflows for:
  - **Vehicle Insurance**: Incident location, vehicle details, RC, DL, damage photos, repair invoices.
  - **Hospitalization / Mediclaim**: Admission dates, hospital details, prescriptions, discharge summary, bills.
  - **Generic Insurance**: Incident description, category, invoices, proof.
- Checklists and downloadable simulated claim forms.

### Module 7: Document Extraction & Integrity Analysis
- PDF and image analysis pipeline using PyMuPDF and Tesseract OCR.
- Field extraction: dates, claim amounts, hospital/workshop names, document identifiers.
- Deterministic checks: date timeline consistency, arithmetic invoice validation, hash duplicate checks, and missing mandatory documents.

### Module 8: Deterministic Claim Eligibility Engine
- Pure deterministic logic (zero LLM reliance for eligibility).
- Configurable rules: filing deadline, excluded categories, incident date validity, coverage limits.
- Stable rule IDs for transparency.
- **Above-Limit Policy**: Ineligible as submitted; calculates excess and displays maximum potentially payable amount without mutating original request.

### Module 9: Duplicate Incident Detection
- Flags candidate claims matching: same policy, identical/overlapping incident dates, identical category, normalized narrative similarity, or duplicate evidence hashes.
- Human review alert without automated fraud accusation.

### Module 10: Claim State Machine & Authorization
- Enforced states: `SUBMITTED`, `UNDER_REVIEW`, `EVIDENCE_REQUESTED`, `APPROVED`, `REJECTED`, `PAID`.
- Prevents invalid jumps (e.g. `SUBMITTED` directly to `PAID`).
- Full audit event creation for every transition and failed unauthorized attempt.

### Module 11: Approval Authority Dashboard
- High-level KPIs: pending claims, approved, rejected, paid, duplicate flags, OCR warnings.
- Review workbench: rule outputs, excess calculation, document preview, duplicate comparison, blockchain verification badge, and spoken decision summary.

### Module 12: Blockchain-Backed Audit Integrity
- Append-only audit events hashed with SHA-256.
- Sequential hash linking (`event[n].prev_hash = hash(event[n-1])`).
- Solidity smart contract on Hardhat EVM anchoring batch/event root hashes.
- Verification workbench: local hash chain validation, on-chain hash lookup, and tampered-event simulation view.

### Module 13: Database Design
- **Neon Cloud PostgreSQL** with Psycopg 3 and pure parameterized SQL.
- Strict rejection of SQLite and SQLAlchemy.
- Core entities: `users`, `customer_profiles`, `insurance_schemes`, `policy_clauses`, `policy_registrations`, `sales_recordings`, `transcripts`, `promises`, `policies`, `claims`, `evidence`, `document_analysis_reports`, `claim_decisions`, `payments`, `audit_events`, `blockchain_anchors`.

### Module 14: Demonstration Scenarios (15 Test Cases)
1. Supported policy promise matching clause.
2. Contradictory agent promise.
3. Policy registration awaiting customer review.
4. Fully eligible claim.
5. Late claim past filing deadline.
6. Excluded category claim.
7. Above-limit claim with excess calculation.
8. Duplicate claims with distinct reference numbers.
9. Claim with incomplete evidence.
10. Narrative inconsistency flag (human review).
11. Refused unauthorized transition attempt.
12. Authorized claim approval.
13. Simulated claim payout.
14. Tampered audit event detection.
15. Verified on-chain blockchain anchor.

---

## 6. Repository Layout

```
insurechain-voiceguard/
├── PROJECT_CONTEXT.md          # Comprehensive architectural & product specification
├── README.md                   # Repository overview & quick start
├── SETUP.TXT                   # Hackathon master prompt & constraints
├── frontend/                   # React 18 + Vite + TypeScript web application
│   ├── README.md               # Web architecture, portals & design system
│   └── package.json            # Web dependencies manifest
├── backend/                    # Python FastAPI backend service
│   ├── README.md               # API architecture, Neon SQL & rules engine
│   └── requirements.txt        # Backend dependencies (strictly no SQLite/SQLAlchemy)
└── app/                        # Flutter mobile application
    ├── README.md               # Mobile architecture, Material 3 & audio pipeline
    └── pubspec.yaml            # Flutter dependencies manifest
```

---

## 7. Security & Compliance Principles

1. **Synthetic Data Only**: Real Aadhaar, PAN, medical records, or payment credentials are never used or simulated as authentic.
2. **Affirmative Recording Consent**: Voice recordings require explicit user consent and provide an active visual indicator.
3. **No Frontend Secrets**: Database credentials and ElevenLabs API keys reside strictly on the backend.
4. **Zero On-Chain PII**: The EVM blockchain stores only cryptographic hashes and batch timestamps.
5. **AI as Review Assistant, Not Decision Maker**: AI recommendations, OCR extractions, and inconsistency scores assist human authorities but never independently approve or reject claims.
