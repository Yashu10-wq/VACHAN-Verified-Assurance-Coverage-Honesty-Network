# InsureChain VoiceGuard — Backend Service

## 1. Overview & Purpose
This folder houses the central backend service for **InsureChain VoiceGuard**, built for **VORTEXA 3.0 (Problem Statement B-02: Policy-Aware Insurance Claims Workflow)**.

The backend is responsible for all core business logic, deterministic rule evaluation, state machine transitions, Neon Cloud PostgreSQL data persistence, document OCR extraction, ElevenLabs voice processing, and EVM blockchain audit hash anchoring.

---

## 2. Technology Stack
- **Framework**: Python (3.11 compatible) with FastAPI and Uvicorn
- **Data Validation & Settings**: Pydantic v2 and Pydantic-Settings
- **Database Access**: Psycopg 3 (`psycopg[binary]`, `psycopg-pool`) utilizing pure parameterized SQL
- **Authentication**: JWT authentication with `python-jose` and password hashing via `bcrypt` / `passlib`
- **Document Processing**: PyMuPDF (`fitz`), Pillow, and PyTesseract OCR
- **Voice AI**: ElevenLabs REST APIs via `httpx` (async client)
- **Blockchain Client**: Web3.py for interaction with local Hardhat EVM node
- **Testing**: Pytest and Pytest-Asyncio

---

## 3. Strict Database Mandate
- **Primary & Only Application Database**: Neon Cloud PostgreSQL via TLS connection string (`DATABASE_URL`).
- **Connection Handling**: Managed through `psycopg_pool.AsyncConnectionPool` or `ConnectionPool` with strict parameterized SQL.
- **Explicit Prohibitions**:
  - **No SQLAlchemy**: ORM abstractions are prohibited in favor of clean, auditable parameterized SQL.
  - **No SQLite**: SQLite and any local fallback database are strictly prohibited. The system must fail loudly if the Neon connection is unavailable.
- **Migration Strategy**: Versioned pure SQL migrations executed by a lightweight, deterministic runner.

---

## 4. Architectural Modules & Responsibilities

### 4.1 Authentication & Role-Based Access Control (RBAC)
- Secure endpoints for login and token refresh.
- Enforce strict server-side authorization for exactly three roles:
  - `CUSTOMER`
  - `AGENT`
  - `AUTHORITY`
- Resource-level data isolation ensuring customers can only access their own records.

### 4.2 Module 1: Sales Recording & Transcription
- Ingest audio recordings initiated by agents with verifiable consent metadata.
- Secure off-chain storage with SHA-256 integrity hash calculation.
- Asynchronous transcription via ElevenLabs Speech-to-Text.
- Immutable storage of original recordings and transcripts with versioned correction tracking.

### 4.3 Module 2: Promise Extraction & Policy Comparison
- Structured extraction of agent commitments from conversation transcripts.
- Comparison engine against configured scheme clauses producing verdicts:
  - `SUPPORTED`, `PARTLY_TRUE`, `CONTRADICTED`, `NOT_IN_POLICY`, `UNCLEAR`.
- Detailed clause citation, page referencing, and evidence strength scoring.

### 4.4 Module 3 & 4: Policy Confirmation & Lifecycle Management
- Transaction-safe policy confirmation mechanism restricted to the customer.
- Deterministic policy state transitions (`PENDING_CONFIRMATION`, `ACTIVE`, `EXPIRING_SOON`, `EXPIRED`, `DECLINED`).
- Idempotent reminder and notification engine for renewals, expiries, and claims.

### 4.5 Module 5: ElevenLabs Voice Integration
- Voice policy assistant handling customer coverage, limits, and claim queries.
- Text-to-speech synthesis for spoken decision explanations.
- Graceful mock/fallback mode when API keys are not supplied, with clear labelling.

### 4.6 Module 6 & 7: Category-Specific Claims & Document Extraction
- Dynamic schemas for Vehicle, Mediclaim, and Generic insurance claims.
- PDF and image processing pipeline:
  - File integrity and format validation.
  - SHA-256 evidence hashing.
  - PyMuPDF text parsing and Tesseract OCR for scanned receipts.
  - Date and financial amount cross-verification with structured claim narratives.

### 4.7 Module 8: Deterministic Claim Eligibility Engine
- Rule evaluation engine operating independently from LLMs:
  - Validates policy window, incident date, exclusions, and monetary limits.
  - Explicit rule IDs for every check.
  - **Above-Limit Rule**: Flags claims exceeding coverage limits as ineligible as submitted and deterministically calculates the maximum potentially payable amount and excess.

### 4.8 Module 9: Duplicate Incident Detection
- Multi-signal scoring engine inspecting policy ID, incident timeframe, normalized narrative semantics, and evidence SHA-256 hashes.
- Flags duplicate candidates for human review without automated fraud accusations.

### 4.9 Module 10: Claim State Machine
- Server-enforced state machine:
  - `SUBMITTED` → `UNDER_REVIEW` ↔ `EVIDENCE_REQUESTED`
  - `UNDER_REVIEW` → `APPROVED` / `REJECTED`
  - `APPROVED` → `PAID`
- Transaction-safe recording of all accepted transitions and rejected unauthorized attempts with actor, timestamp, and rationale.

### 4.10 Module 11 & 12: Blockchain-Backed Audit Service
- Append-only audit log hashing canonical event representations with SHA-256.
- Cryptographic hash chaining linking consecutive events (`previous_hash` → `current_hash`).
- Web3.py integration anchoring hash batches onto a Solidity smart contract on an EVM development node.
- Zero sensitive or PII data on-chain; only cryptographic hashes and batch IDs.
- Ledger verification endpoint comparing on-chain anchors with stored audit events.

---

## 5. Future Development Roadmap
- Create database migration runner and initial Neon schema (`migrations/001_initial_schema.sql`).
- Implement core database pool manager (`core/database.py`).
- Implement domain routers, services, and repositories.
- Deploy and connect the Solidity smart contract via Hardhat.
- Add comprehensive Pytest test suites for eligibility rules and audit chain integrity.
