# InsureChain VoiceGuard — Frontend Web Application

## 1. Overview & Purpose
This folder contains the React-based web application for **InsureChain VoiceGuard**, developed for **VORTEXA 3.0 (Problem Statement B-02: Policy-Aware Insurance Claims Workflow)**.

The frontend serves as the unified desktop and tablet web interface supporting all three system roles:
1. **Customer**
2. **Insurance Agent**
3. **Approval Authority**

The application makes insurance sales promises verifiable, claims decisions explainable, claim-state transitions enforceable, and audit records tamper-evident. All operations represent a simulated prototype environment.

---

## 2. Technology Stack
- **Framework**: React 18 with TypeScript and Vite
- **Styling**: Tailwind CSS adhering to a fintech design system (Navy, Off-white, Violet, Teal)
- **Routing**: React Router (v6) with client-side role-based route guards
- **Icons & Visuals**: Lucide React
- **Data Visualization**: Recharts (for claims analytics and distribution metrics)
- **API Communication**: Typed Axios HTTP client communicating exclusively with the FastAPI backend

---

## 3. Architecture & Security Requirements
- **No Direct Database Access**: The frontend communicates **only** with the backend API over HTTPS/TLS. It holds no direct database credentials (Neon PostgreSQL is strictly accessed by the backend).
- **Client-Side Authorization**: Routes and controls are rendered according to the authenticated user's role, but all authorization checks are strictly validated on the backend.
- **Off-Chain Media Handling**: Audio recordings and claim evidence are uploaded and retrieved through authenticated backend endpoints with SHA-256 integrity verification.

---

## 4. Intended Modules & User Role Capabilities

### 4.1 Customer Portal
- **Policy Management**: View active and pending policies, policy numbers, coverage limits, covered/excluded categories, waiting periods, and renewal dates.
- **Vaada-Inspired Confirmation**:
  - Review pending registrations (`PENDING_CONFIRMATION`).
  - Audio player to listen to the sales conversation recording.
  - Interactive transcript viewer with extracted agent promises.
  - Contradiction inspector comparing promises against actual written policy clauses with source page references.
  - Explicit customer action to **Confirm** (activate simulated policy) or **Decline**.
- **Claims Filing (Category-Specific)**:
  - Dynamic forms for Vehicle Insurance, Hospitalization/Mediclaim, and Generic claims.
  - Evidence upload manager with file validation and document checklists.
  - Real-time display of document completeness and validation summaries.
- **Claim Tracker & Timeline**:
  - Live state tracking (`SUBMITTED` → `UNDER_REVIEW` → `EVIDENCE_REQUESTED` → `APPROVED` / `REJECTED` → `PAID`).
  - Transparent explanations of eligibility decisions and calculated potentially payable amounts.
- **ElevenLabs Voice Policy Assistant**:
  - Integrated text and voice assistant for policy queries, coverage clarification, and claim status inquiries.

### 4.2 Insurance Agent Portal
- **Sales Scheme Selector**: Browse available simulated insurance schemes and their clauses.
- **Consent-Gated Audio Recording**:
  - Explicit affirmative consent prompt prior to recording.
  - Live recording status indicator and audio waveform visualization.
  - Secure upload triggering backend transcription and promise extraction.
- **Synthetic Customer Registration**:
  - Input synthetic customer contact details and declarations.
  - Upload supporting simulation documents.
  - Submit registration for customer review and confirmation.
- **Extraction Review**:
  - Preliminary inspection of transcribed text, extracted promises, and rule comparison results.

### 4.3 Approval Authority Workbench
- **Executive Metrics Dashboard**:
  - Real-time metrics: Total Claims, Submitted, Under Review, Evidence Requested, Approved, Rejected, Paid, Possible Duplicates, and Document Inconsistency Flags.
- **Searchable Claims Management**:
  - Filterable claims table by customer, policy number, category, incident date, requested amount, payable amount, and status.
- **Claim Review Workbench**:
  - Side-by-side policy clause and claim narrative inspector.
  - Deterministic eligibility engine outputs showing passed/failed rule IDs.
  - Above-limit calculation view displaying requested amount, limit, and excess calculations.
  - Duplicate incident detection panel with similarity score and matching candidate details.
  - Document extraction results and integrity alerts.
  - Action controls: Request Evidence, Approve, Reject (with mandatory recorded reason), and Initiate Simulated Payment.
  - Spoken decision explanation playback powered by ElevenLabs.
- **Tamper-Evident Audit & Blockchain Ledger**:
  - Visual append-only audit event chain.
  - EVM blockchain anchor verification status indicator (matching local SHA-256 hashes against smart contract state).
  - Interactive tampered-event demonstration.

---

## 5. Future Development Roadmap
- Set up Vite + React + Tailwind configuration (`vite.config.ts`, `tailwind.config.js`, `postcss.config.js`).
- Build shared design system components (buttons, badges, modals, metric cards, audio player).
- Implement auth context with JWT handling.
- Construct the three dedicated role layouts and dashboards.
