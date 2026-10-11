# InsureChain VoiceGuard

<div align="center">

### VORTEXA 3.0 | Problem Statement B-02
**Policy-Aware Insurance Claims Workflow with Blockchain-Backed Audit Integrity & ElevenLabs Voice AI**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](#)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688.svg?logo=fastapi&logoColor=white)](#)
[![PostgreSQL](https://img.shields.io/badge/Database-Neon%20Postgres-336791.svg?logo=postgresql&logoColor=white)](#)
[![React](https://img.shields.io/badge/Frontend-React%2018%20%7C%20Vite-61DAFB.svg?logo=react&logoColor=black)](#)
[![Flutter](https://img.shields.io/badge/Mobile-Flutter%20%7C%20Dart-02569B.svg?logo=flutter&logoColor=white)](#)
[![Solidity](https://img.shields.io/badge/Blockchain-Solidity%20%7C%20EVM-363636.svg?logo=solidity&logoColor=white)](#)
[![ElevenLabs](https://img.shields.io/badge/Voice%20AI-ElevenLabs-black.svg)](#)

</div>

---

## 📌 Project Overview

**InsureChain VoiceGuard** addresses the systemic trust deficit in insurance by bridging the gap between verbal sales representations and written policy clauses, while enforcing tamper-evident claims processing.

- **🎙️ Vaada-Inspired Protection**: Agents record sales consultations with explicit customer consent. ElevenLabs transcribes conversations, and an AI comparator extracts agent promises and compares them directly against policy clauses. Customers must personally review contradictions and explicitly confirm before any policy is activated.
- **⚙️ Policy-Aware Claims Workflow**: Claims move through a strictly enforced state machine (`SUBMITTED` → `UNDER_REVIEW` ↔ `EVIDENCE_REQUESTED` → `APPROVED`/`REJECTED` → `PAID`). A deterministic eligibility engine evaluates rules, computes above-limit excess amounts, and detects duplicate incidents.
- **🔊 Spoken Explainability**: ElevenLabs powers both a customer-facing conversational voice policy assistant and spoken claim decision explanations for authorities and policyholders.
- **⛓️ Blockchain-Backed Audit Ledger**: All decisions and state transitions are cryptographically hashed using SHA-256 in an append-only chain and anchored to an EVM smart contract, ensuring tamper-evident auditability while keeping private data off-chain.

> **Note**: This is an academic hackathon prototype for VORTEXA 3.0. All policy schemes, claims, documents, and payments are strictly synthetic simulations.

---

## 📐 Architecture & Modules

```
Flutter Mobile App (Material 3)       React Web App (Tailwind CSS)
        \                                   /
         \                                 /
          ▼                               ▼
       Central FastAPI Backend (Psycopg 3 / Python 3.11)
            ├── Neon Cloud PostgreSQL (Pure Parameterized SQL)
            ├── ElevenLabs Voice AI (STT / TTS / Voice Assistant)
            ├── Document Extraction & OCR Pipeline (PyMuPDF / Tesseract)
            ├── Deterministic Claims Eligibility Engine
            └── EVM Smart Contract (Hardhat SHA-256 Hash Anchoring)
```

For the comprehensive architectural blueprint, module specifications, and 15 demonstration scenarios, see:  
📖 **[PROJECT_CONTEXT.md](./PROJECT_CONTEXT.md)**

---

## 📂 Repository Structure

| Directory | Platform / Technology | Purpose |
| :--- | :--- | :--- |
| **[`frontend/`](./frontend)** | React 18, Vite, TypeScript, Tailwind CSS, Recharts | Web portals for Customer, Insurance Agent, and Approval Authority Workbench. |
| **[`backend/`](./backend)** | FastAPI, Psycopg 3, PyMuPDF, Web3.py, ElevenLabs | Central API service, deterministic rules engine, state machine, and audit ledger. |
| **[`app/`](./app)** | Flutter, Dart, Riverpod, GoRouter, Dio | Android mobile client with consent-gated audio recording and voice assistant. |

---

## 👥 Three System Roles

1. **Customer**: Reviews sales audio & extracted contradictions, confirms policy purchases, submits claims with evidence, asks voice policy queries, and monitors claim timelines.
2. **Insurance Agent**: Initiates consent-gated sales recordings, onboards synthetic customers, selects schemes, and reviews preliminary promise extractions.
3. **Approval Authority**: Inspects claims, reviews deterministic rule breakdowns, analyzes duplicate alerts, requests evidence, approves/rejects claims with recorded reasons, executes simulated payments, and verifies blockchain audit integrity.

---

## 🔒 Security & Privacy Guarantees

- **No Secrets in Client Code**: All ElevenLabs credentials and database connections remain on the backend.
- **Neon Cloud PostgreSQL Only**: Explicitly parameterized SQL with transaction safety; SQLite and SQLAlchemy are strictly forbidden.
- **Zero On-Chain PII**: Personal data, audio recordings, and medical documents remain securely off-chain; only cryptographic hashes are anchored on the blockchain.
- **Responsible AI**: AI inconsistency signals assist human review and never independently decide claim eligibility or prove fraud.
