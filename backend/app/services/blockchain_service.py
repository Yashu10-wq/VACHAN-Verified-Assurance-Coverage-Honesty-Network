"""
Blockchain Audit Anchoring Service for InsureChain VoiceGuard.
Connects asynchronously to EVM JSON-RPC (Hardhat local node) to submit
batch Merkle root commitments, verify on-chain anchors, and track transactions.
Fails cleanly when blockchain node is offline; never exposes secrets.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import httpx
import psycopg

from app.core.config import get_settings
from app.core.exceptions import IntegrationException, ValidationException
from app.core.logging import get_logger
from app.db.repositories import anchor_batch_repo, audit_repo
from app.services.merkle_tree import MerkleTree

logger = get_logger(__name__)

# Function selectors for AuditAnchor contract
SELECTOR_ANCHOR_BATCH = "0x9a1d0d41"       # anchorBatch(bytes32,uint256)
SELECTOR_VERIFY_COMMITMENT = "0xfc6326ce"   # verifyCommitment(bytes32)
SELECTOR_GET_ANCHOR = "0x4c7df18f"          # getAnchor(uint256)


def pad_bytes32_hex(hex_str: str) -> str:
    """Formats hex string to exact 32-byte (64 hex characters) representation without 0x prefix."""
    cleaned = hex_str.lower().replace("0x", "")
    return cleaned.rjust(64, "0")[:64]


def pad_uint256_hex(val: int) -> str:
    """Formats integer to 32-byte (64 hex characters) hex representation without 0x prefix."""
    hex_repr = hex(val)[2:]
    return hex_repr.rjust(64, "0")[:64]


class BlockchainService:
    """Asynchronous JSON-RPC client for Hardhat EVM node interaction."""

    def __init__(self):
        self._cached_contract_address: Optional[str] = None

    def get_contract_address(self) -> Optional[str]:
        """Resolves configured or exported contract address."""
        settings = get_settings()
        if settings.AUDIT_CONTRACT_ADDRESS:
            return settings.AUDIT_CONTRACT_ADDRESS

        if self._cached_contract_address:
            return self._cached_contract_address

        # Check deployed metadata export
        abi_path = Path(__file__).parent.parent / "core" / "abi" / "AuditAnchor.json"
        if abi_path.is_file():
            try:
                data = json.loads(abi_path.read_text(encoding="utf-8"))
                addr = data.get("contractAddress")
                if addr:
                    self._cached_contract_address = addr
                    return addr
            except Exception as e:
                logger.warning("Could not read exported AuditAnchor artifact: %s", str(e))

        return None

    async def _rpc_call(self, method: str, params: List[Any]) -> Any:
        """Sends a JSON-RPC request to the configured blockchain RPC URL."""
        settings = get_settings()
        rpc_url = settings.BLOCKCHAIN_RPC_URL
        timeout = settings.BLOCKCHAIN_RPC_TIMEOUT_SECONDS

        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
            "id": 1,
        }

        async with httpx.AsyncClient(timeout=timeout) as client:
            try:
                resp = await client.post(rpc_url, json=payload)
                resp.raise_for_status()
                data = resp.json()
            except httpx.ConnectError:
                raise IntegrationException("Blockchain", f"Unable to connect to RPC node at {rpc_url}.")
            except httpx.TimeoutException:
                raise IntegrationException("Blockchain", f"RPC request timed out after {timeout}s.")
            except Exception as e:
                raise IntegrationException("Blockchain", f"RPC request failed: {str(e)}")

            if "error" in data:
                err_msg = data["error"].get("message", str(data["error"]))
                raise IntegrationException("Blockchain", f"EVM RPC error: {err_msg}")

            return data.get("result")

    async def get_blockchain_status(self) -> Dict[str, Any]:
        """
        Queries blockchain node connectivity and contract status safely.
        Never throws unhandled exceptions; reports status gracefully if node is down.
        """
        settings = get_settings()
        contract_addr = self.get_contract_address()

        status_result = {
            "is_connected": False,
            "rpc_url": settings.BLOCKCHAIN_RPC_URL,
            "configured_chain_id": settings.BLOCKCHAIN_CHAIN_ID,
            "node_chain_id": None,
            "block_number": None,
            "contract_address": contract_addr,
            "contract_deployed": False,
            "status": "BLOCKCHAIN_UNAVAILABLE",
        }

        try:
            # 1. Check chain ID
            chain_id_hex = await self._rpc_call("eth_chainId", [])
            node_chain_id = int(chain_id_hex, 16)
            status_result["node_chain_id"] = node_chain_id
            status_result["is_connected"] = True

            # 2. Check block number
            block_hex = await self._rpc_call("eth_blockNumber", [])
            status_result["block_number"] = int(block_hex, 16)

            # 3. Check contract bytecode if address is known
            if contract_addr:
                code_hex = await self._rpc_call("eth_getCode", [contract_addr, "latest"])
                if code_hex and code_hex != "0x" and len(code_hex) > 4:
                    status_result["contract_deployed"] = True
                    status_result["status"] = "ACTIVE"
                else:
                    status_result["status"] = "CONTRACT_NOT_DEPLOYED"
            else:
                status_result["status"] = "CONTRACT_ADDRESS_NOT_CONFIGURED"

        except Exception as e:
            logger.debug("Blockchain status check indicated node is offline: %s", str(e))
            status_result["status"] = "BLOCKCHAIN_UNAVAILABLE"

        return status_result

    async def verify_commitment_on_chain(self, root_hash: str) -> Dict[str, Any]:
        """
        Calls `verifyCommitment(bytes32)` on the smart contract.
        Returns: { "exists": bool, "sequence_number": int, "timestamp": int, "event_count": int }
        """
        contract_addr = self.get_contract_address()
        if not contract_addr:
            return {"exists": False, "reason": "Contract address not configured."}

        padded_hash = pad_bytes32_hex(root_hash)
        calldata = SELECTOR_VERIFY_COMMITMENT + padded_hash

        try:
            result_hex = await self._rpc_call("eth_call", [{"to": contract_addr, "data": calldata}, "latest"])
            if not result_hex or result_hex == "0x" or len(result_hex) < 130:
                return {"exists": False, "reason": "Empty contract response."}

            # Decode 4 uint256 words:
            # word 1: bool exists
            # word 2: uint256 sequenceNumber
            # word 3: uint256 timestamp
            # word 4: uint256 eventCount
            clean = result_hex[2:] if result_hex.startswith("0x") else result_hex
            exists = (int(clean[0:64], 16) != 0)
            seq = int(clean[64:128], 16)
            timestamp = int(clean[128:192], 16) if len(clean) >= 192 else 0
            event_count = int(clean[192:256], 16) if len(clean) >= 256 else 0

            return {
                "exists": exists,
                "sequence_number": seq,
                "timestamp": timestamp,
                "event_count": event_count,
            }
        except Exception as e:
            logger.warning("Could not verify commitment on chain: %s", str(e))
            return {"exists": False, "error": str(e)}

    async def anchor_batch_to_chain(
        self,
        root_hash: str,
        event_count: int,
    ) -> Dict[str, Any]:
        """
        Submits `anchorBatch(bytes32 rootHash, uint256 eventCount)` to smart contract.
        Waits for transaction receipt and validates execution status.
        """
        contract_addr = self.get_contract_address()
        if not contract_addr:
            raise ValidationException("AuditAnchor contract address is not configured or deployed.")

        # 1. Fetch available unlocked accounts from Hardhat node
        accounts = await self._rpc_call("eth_accounts", [])
        if not accounts:
            raise IntegrationException("Blockchain", "No unlocked accounts available on RPC node.")
        sender = accounts[0]

        # 2. Construct calldata
        padded_root = pad_bytes32_hex(root_hash)
        padded_count = pad_uint256_hex(event_count)
        calldata = SELECTOR_ANCHOR_BATCH + padded_root + padded_count

        # 3. Send transaction
        tx_hash = await self._rpc_call(
            "eth_sendTransaction",
            [
                {
                    "from": sender,
                    "to": contract_addr,
                    "data": calldata,
                    "gas": "0x4c4b40",  # 5,000,000 gas limit
                }
            ],
        )

        if not tx_hash:
            raise IntegrationException("Blockchain", "Failed to obtain transaction hash from node.")

        # 4. Wait for receipt
        receipt = await self._rpc_call("eth_getTransactionReceipt", [tx_hash])
        block_number = None
        if receipt:
            status_hex = receipt.get("status")
            if status_hex != "0x1":
                raise IntegrationException("Blockchain", f"Transaction reverted on chain (status {status_hex}).")
            block_number = int(receipt.get("blockNumber", "0x0"), 16)

        # 5. Fetch current chain ID
        chain_id_hex = await self._rpc_call("eth_chainId", [])
        chain_id = int(chain_id_hex, 16)

        return {
            "tx_hash": tx_hash,
            "block_number": block_number,
            "chain_id": chain_id,
            "contract_address": contract_addr,
        }

    async def process_pending_audit_batches(
        self,
        conn: psycopg.AsyncConnection,
        actor_id: Optional[str] = None,
        actor_role: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Selects eligible unbatched audit events, derives Merkle tree commitment,
        submits anchor to smart contract, and updates database records.
        Idempotent and resilient to temporary RPC outages.
        """
        settings = get_settings()
        batch_limit = settings.MAX_ANCHOR_BATCH_SIZE

        # 1. Check if blockchain is available
        status = await self.get_blockchain_status()
        if not status["is_connected"] or not status["contract_deployed"]:
            return {
                "batches_created": 0,
                "anchored_events": 0,
                "status": status["status"],
                "message": "Blockchain node or contract is not available for anchoring.",
            }

        # 2. Process pending audit events in batches until queue is clear
        total_batches_created = 0
        total_anchored_events = 0
        last_batch = None

        while True:
            events = await anchor_batch_repo.get_pending_audit_events(conn, limit=batch_limit)
            if not events:
                break

            event_ids = [e["id"] for e in events]
            leaf_hashes = [e["event_hash"] for e in events]
            first_seq = events[0]["sequence_number"]
            last_seq = events[-1]["sequence_number"]
            event_count = len(events)

            # 3. Calculate Merkle Tree root
            tree = MerkleTree(leaf_hashes)
            root_hash = "0x" + tree.root

            # 4. Create batch record in database
            batch = await anchor_batch_repo.create_anchor_batch(
                conn=conn,
                batch_root_hash=root_hash,
                first_seq=first_seq,
                last_seq=last_seq,
                event_count=event_count,
                event_ids=event_ids,
            )
            batch_id = batch["id"]

            # 5. Submit anchor to smart contract
            try:
                tx_res = await self.anchor_batch_to_chain(
                    root_hash=root_hash,
                    event_count=event_count,
                )

                # 6. Update batch and events to ANCHORED
                updated_batch = await anchor_batch_repo.update_batch_anchored(
                    conn=conn,
                    batch_id=batch_id,
                    tx_hash=tx_res["tx_hash"],
                    block_number=tx_res["block_number"],
                    chain_id=tx_res["chain_id"],
                    contract_address=tx_res["contract_address"],
                )
                last_batch = updated_batch
                total_batches_created += 1
                total_anchored_events += event_count

            except Exception as e:
                logger.error("Failed to anchor batch %s to blockchain: %s", batch_id, str(e), exc_info=True)
                await anchor_batch_repo.update_batch_failed(
                    conn=conn,
                    batch_id=batch_id,
                    error_message=str(e),
                )
                return {
                    "batches_created": total_batches_created,
                    "anchored_events": total_anchored_events,
                    "status": "FAILED",
                    "error": str(e),
                }

            if total_batches_created >= 20:
                break

        if total_batches_created == 0:
            return {
                "batches_created": 0,
                "anchored_events": 0,
                "status": "IDLE",
                "message": "No pending audit events to anchor.",
            }

        # 7. Audit the anchoring action without creating infinite loops
        # (Note: get_pending_audit_events explicitly ignores ANCHOR_AUDIT_BATCH)
        await audit_repo.log_audit_event(
            conn=conn,
            actor_id=actor_id,
            actor_role=actor_role or "APPROVAL_AUTHORITY",
            action="ANCHOR_AUDIT_BATCH",
            target_type="audit_anchor_batch",
            target_id=last_batch["id"] if last_batch else None,
            metadata={
                "batches_created": total_batches_created,
                "anchored_events": total_anchored_events,
            },
        )

        return {
            "batches_created": total_batches_created,
            "anchored_events": total_anchored_events,
            "batch": last_batch,
            "status": "SUCCESS",
            "message": f"Successfully anchored {total_anchored_events} audit events across {total_batches_created} batch(es).",
        }


blockchain_service = BlockchainService()
