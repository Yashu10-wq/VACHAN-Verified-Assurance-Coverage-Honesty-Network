# InsureChain VoiceGuard — Blockchain Audit Anchoring (Phase 8)

## 1. Architecture & Trust Boundaries

The Blockchain Audit Anchoring engine provides cryptographic immutability and verifiable provenance for all security-sensitive events across the InsureChain VoiceGuard backend.

```
+-------------------------------------------------------------------------------+
|                             FastAPI Backend                                   |
|                                                                               |
|  [ Domain Action ]                                                            |
|         |                                                                     |
|         v                                                                     |
|  [ Chained Audit Logger ] ---> Deterministic Canonical JSON + SHA-256         |
|         |                      Sequence Linkage: SHA-256(v1|seq|prev|payload) |
|         v                                                                     |
|  [ Neon PostgreSQL ]                                                          |
|    - audit_logs (sequence_number, payload_hash, previous_hash, event_hash)    |
|    - audit_anchor_batches (batch_sequence, batch_root_hash, tx_hash, block)   |
|         |                                                                     |
|         v (Batching Engine)                                                   |
|  [ Binary Merkle Tree ] ---> Merkle Root (32 bytes)                           |
+---------|---------------------------------------------------------------------+
          | JSON-RPC (eth_sendTransaction)
          v
+-------------------------------------------------------------------------------+
|                       EVM Smart Contract (AuditAnchor)                        |
|                                                                               |
|  Function: anchorBatch(bytes32 rootHash, uint256 eventCount)                   |
|  - Append-only sequence counter                                               |
|  - Emits: AuditBatchAnchored(sequenceNumber, rootHash, eventCount, timestamp) |
|  - View: verifyCommitment(bytes32 rootHash) -> (exists, seq, ts, count)       |
+-------------------------------------------------------------------------------+
```

### What is and is NOT Stored On-Chain:
- **Stored On-Chain:** ONLY the cryptographic Merkle root commitment (a 32-byte hash `bytes32`), the batch sequence number, event count, and block timestamp.
- **NEVER Stored On-Chain:** Customer identity (PII), audio files, transcripts, policy texts, claim documents, or raw database records.

---

## 2. Local Hardhat Setup

### Prerequisites
- Node.js `>= 18.x` (tested on Node.js `v22.20.0`)
- npm `>= 9.x`

### Installation
From the repository root:
```bash
cd blockchain
npm install
```

### Compile Smart Contracts
```bash
npx hardhat compile
```

### Run Solidity Unit Tests
```bash
npx hardhat test
```
All 10 contract unit tests run in in-memory Hardhat EVM:
- Deployment ownership and initialization
- Monotonic sequential batch anchoring
- Duplicate commitment rejection
- Zero-value root hash rejection
- Zero event count rejection
- Unauthorized caller access control
- Unknown commitment verification failure
- Out-of-bounds sequence getter revert

---

## 3. Starting the Local Hardhat Node & Deployment

### Step 1: Start Local EVM Node (Terminal 1)
```bash
cd blockchain
npx hardhat node
```
This launches a JSON-RPC node listening at `http://127.0.0.1:8545` with pre-funded test accounts and chain ID `31337`.

### Step 2: Deploy Contract to Local Node (Terminal 2)
```bash
cd blockchain
npx hardhat run scripts/deploy.js --network localhost
```
This deploys `AuditAnchor.sol` and exports the contract address and ABI artifact to `backend/app/core/abi/AuditAnchor.json`.

---

## 4. Environment Variables (`.env`)

Add the following placeholders to `backend/.env`:
```env
# Blockchain Audit Anchoring Configuration
BLOCKCHAIN_RPC_URL="http://127.0.0.1:8545"
BLOCKCHAIN_CHAIN_ID=31337
AUDIT_CONTRACT_ADDRESS="0x5FbDB2315678afecb367f032d93F642f64180aa3"
BLOCKCHAIN_RPC_TIMEOUT_SECONDS=5.0
MAX_ANCHOR_BATCH_SIZE=50
RUN_LIVE_BLOCKCHAIN_TEST=false
```

---

## 5. Database Migrations

Apply Migration 0007 using the existing migration runner:
```bash
cd backend
.venv\Scripts\python.exe -m app.db.migrations apply
```
Applies:
- `audit_anchor_batches` table
- `audit_log_seq` sequence
- Extended integrity columns on `audit_logs` (`sequence_number`, `payload_hash`, `previous_hash`, `event_hash`, `hash_version`, `anchoring_status`, `batch_id`)

---

## 6. How to Verify an Event and its Merkle Proof

### A. Individual Event Integrity
```http
GET /api/v1/integrity/audit-events/{event_id}
```
Checks:
1. Recomputes `payload_hash` from stored fields.
2. Recomputes `event_hash = SHA-256(v1|seq|prev_hash|payload_hash)`.
3. Verifies `previous_hash` continuity with preceding sequence.
4. Checks on-chain smart contract if marked as `ANCHORED`.

### B. Merkle Inclusion Proof
```http
GET /api/v1/integrity/audit-events/{event_id}/proof
```
Returns:
- `event_hash`
- `batch_root_hash`
- `leaf_index`
- `merkle_proof`: List of `[{"position": "left"|"right", "hash": "<hex>"}]`
- `tx_hash`, `block_number`, `chain_id`, `contract_address`
- `on_chain_commitment_verified`: `true`

---

## 7. How to Process Pending Anchors (Admin)

Authorized Approval Authorities can trigger batch anchoring:
```http
POST /api/v1/integrity/anchor-pending
Authorization: Bearer <AUTHORITY_JWT_TOKEN>
```
Batches up to `MAX_ANCHOR_BATCH_SIZE` pending audit events, derives the Merkle tree root, submits `anchorBatch(rootHash, count)` to the smart contract, and updates DB statuses to `ANCHORED`.

---

## 8. Simulating Tampering in Test Environment

To verify tamper detection:
```python
# 1. Modify metadata of an existing event directly in the database:
UPDATE audit_logs SET metadata = '{"amount": 9999999}' WHERE id = '<event_id>';

# 2. Call verification endpoint:
GET /api/v1/integrity/audit-events/<event_id>
# -> Returns outcome: "HASH_MISMATCH" with explanation that payload was modified.
```

---

## 9. Offline Resilience & Limitations

- **If the Blockchain Node is Offline:** Audit logging continues seamlessly without crashing. Events are marked as `PENDING` in PostgreSQL. When the node comes back online, `POST /api/v1/integrity/anchor-pending` will catch up.
- **Local Hardhat Chain Limitations:** A local Hardhat node resets its state whenever restarted. In production, connect `BLOCKCHAIN_RPC_URL` and `AUDIT_CONTRACT_ADDRESS` to an EVM-compatible testnet or private rollup with persistent storage.
