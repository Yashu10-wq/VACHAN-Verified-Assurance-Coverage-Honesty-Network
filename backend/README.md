# InsureChain VoiceGuard — Backend Service

## 1. Overview & System Purpose

This directory contains the central backend service for **InsureChain VoiceGuard**, developed for **VORTEXA 3.0 (Problem Statement B-02: Policy-Aware Insurance Claims Workflow)**.

The backend acts as the single source of truth and authoritative rules engine for both the **Flutter mobile application** and the **React web dashboard**. It provides:
- Deterministic claims evaluation and policy verification.
- Pure parameterized SQL access to **Neon Cloud PostgreSQL** via **Psycopg 3**.
- Integration interfaces for **Cloudinary** (private media/document storage), **ElevenLabs** (voice STT/TTS), and **Google Gemini** (promise extraction vs. policy clause comparison).
- SHA-256 cryptographic audit chaining and EVM smart contract anchor tracking.

---

## 2. Mandatory Cross-Platform Architecture & Identity Requirements

1. **Single Backend & Database**: The Flutter mobile app and React web dashboard communicate with the same FastAPI backend API and use the same Neon PostgreSQL database. There are no separate databases or independent data silos.
2. **Three Roles Supported Universally**: `CUSTOMER`, `INSURANCE_AGENT`, and `APPROVAL_AUTHORITY` are supported across both mobile and web clients.
3. **Strict Server-Side Authorization**: Hiding a UI button or screen is not an authorization mechanism. The backend verifies JWT tokens, roles, and resource ownership on every protected endpoint.
4. **Controlled Authority Verification**: Public users cannot self-grant authority privileges. Authority onboarding requires explicit verification, tracked via account activation status.
5. **Mobile-Only Sales Recording**: Voice recording of sales conversations is accessible strictly through the Flutter mobile app by authorized insurance agents with explicit affirmative consent.
6. **Centralized Off-Chain Storage**: Recordings, documents, transcripts, comparison reports, and claim evidence are stored centrally and off-chain (Cloudinary / secure file store), referenced via hashes in Neon PostgreSQL.
7. **Secure Activation Workflow**: Agent customer registration initiates private storage, ElevenLabs transcription, and Gemini comparison. Customer account activation uses expiring, single-use links rather than plaintext passwords.
8. **Customer-Gated Policy Activation**: Only an explicit, affirmative confirmation by the customer activates a policy. AI analysis alone never activates a policy or modifies claim states.
9. **Single Versioned API Contract**: Standardized `/api/v1` endpoints with structured JSON responses, CORS allowlisting, and consistent error models.
10. **Phase 1 Scope Discipline**: Only foundational infrastructure (configuration, logging, connection layer, migration runner, health checks, test suite) is implemented in Phase 1.

---

## 3. Strict Database Mandate

- **Application Database**: Neon Cloud PostgreSQL exclusively (`postgresql://` or `postgres://`).
- **Driver**: Psycopg 3 (`psycopg[binary]`, `psycopg-pool`) using pure parameterized SQL.
- **Strictly Prohibited**: No SQLite, no SQLAlchemy, no SQLModel, and no local fallback databases.
- **Migrations**: Versioned, pure SQL migrations executed transactionally under PostgreSQL advisory locks.

---

## 4. Backend Project Layout

```
backend/
├── app/
│   ├── main.py                     # FastAPI application factory, lifespan, CORS, and error handlers
│   ├── core/
│   │   ├── config.py               # Pydantic Settings (DATABASE_URL / DB_URI, CORS, integrations)
│   │   ├── exceptions.py           # Sanitized application exception hierarchy
│   │   └── logging.py              # Structured console logging with automatic secret redaction
│   ├── db/
│   │   ├── connection.py           # Psycopg 3 connection pool & readiness health check
│   │   └── migrations.py           # Transactional SQL migration runner with advisory locks
│   ├── integrations/
│   │   ├── cloudinary_client.py    # Cloudinary private storage configuration
│   │   ├── elevenlabs_client.py    # ElevenLabs Voice AI STT/TTS configuration
│   │   └── gemini_client.py        # Google Gemini clause comparison configuration
│   └── api/
│       ├── router.py               # Central /api/v1 router
│       └── routes/
│           └── health.py           # Liveness (/health), readiness (/health/ready), integrations status
├── migrations/
│   └── 0001_create_migration_tracking.sql  # Migration tracking schema
├── tests/
│   ├── conftest.py                 # AsyncClient fixtures and Windows event loop configuration
│   ├── test_config.py              # Config validation, secret scrubbing, and integration tests
│   ├── test_health.py              # Liveness, readiness, failure simulation, and CORS tests
│   └── test_migrations.py          # Migration discovery, checksum integrity, and idempotency tests
├── .env.example                    # Environment variable template with descriptive placeholders
├── .gitignore                      # Git ignore rules protecting credentials and cache
├── pytest.ini                      # Pytest configuration (pythonpath, asyncio mode)
├── requirements.txt                # Runtime dependencies
├── requirements-dev.txt            # Development and test dependencies
└── README.md                       # Architecture and developer setup guide
```

---

## 5. Developer Setup Guide (Windows PowerShell)

Follow these exact steps in PowerShell from the `backend/` directory:

### Step 1: Create and Activate Virtual Environment
```powershell
# Navigate to backend directory
cd d:\Vortexa\VACHAN-Verified-Assurance-Coverage-Honesty-Network\backend

# Create virtual environment
python -m venv .venv

# Activate virtual environment
.\.venv\Scripts\Activate.ps1
```

### Step 2: Install Dependencies
```powershell
pip install -r requirements-dev.txt
```

### Step 3: Configure Environment Variables
Copy `.env.example` to `.env` and verify your credentials:
```powershell
Copy-Item .env.example .env
```
Ensure your Neon PostgreSQL connection string is set via `DATABASE_URL` or `DB_URI`:
```ini
DB_URI=postgresql://<user>:<password>@<neon-host>/<dbname>?sslmode=require
```

### Step 4: Check Database Migration Status
```powershell
python -m app.db.migrations status
```

### Step 5: Apply Database Migrations
```powershell
python -m app.db.migrations apply
```

### Step 6: Start the FastAPI Development Server
```powershell
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Interactive OpenAPI documentation is available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Step 7: Check Health and Readiness Probes
```powershell
# Liveness probe (does not require DB)
curl.exe http://localhost:8000/api/v1/health

# Readiness probe (verifies live Neon PostgreSQL connectivity)
curl.exe http://localhost:8000/api/v1/health/ready

# Integration diagnostic overview
curl.exe http://localhost:8000/api/v1/health/integrations
```

### Step 8: Run the Test Suite
```powershell
pytest -v
```

---

## 6. Troubleshooting & Diagnostics

| Symptom | Cause | Solution |
| :--- | :--- | :--- |
| `InterfaceError: Psycopg cannot use ProactorEventLoop` | Default Windows asyncio event loop is incompatible with Psycopg async socket polling. | The backend automatically sets `asyncio.WindowsSelectorEventLoopPolicy()` on `win32` in `connection.py`, `migrations.py`, and `main.py`. |
| `Readiness returns HTTP 503` | Neon PostgreSQL is unreachable or credentials in `.env` are incorrect. | Verify network connectivity and ensure `DATABASE_URL` / `DB_URI` contains `sslmode=require`. Check `GET /api/v1/health/ready` response message. |
| `ConfigurationException: Database connection string is missing` | Neither `DATABASE_URL` nor `DB_URI` is defined in `.env`. | Provide a valid PostgreSQL connection string in `.env`. SQLite is intentionally rejected. |
| `Checksum mismatch on migration` | An applied migration file was modified post-application. | SQL migration files must be immutable once executed. Create a new sequential migration (`0002_...sql`). |
