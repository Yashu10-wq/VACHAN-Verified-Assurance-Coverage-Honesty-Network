"""
Merkle Tree Engine for InsureChain VoiceGuard Audit Anchoring.
Provides deterministic binary Merkle tree root calculation,
inclusion proof generation, and standalone cryptographic verification.
"""

import hashlib
from typing import Any, Dict, List, Optional, Tuple


def sha256_hex(data: str) -> str:
    """Computes SHA-256 hexadecimal hash of UTF-8 string."""
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def combine_hash_pair(left_hex: str, right_hex: str) -> str:
    """
    Combines two 32-byte hex hashes deterministically.
    Canonical format: left_hex + right_hex (lowercase).
    """
    combined = left_hex.lower() + right_hex.lower()
    return hashlib.sha256(combined.encode("utf-8")).hexdigest()


class MerkleTree:
    """
    Binary Merkle Tree built from an ordered list of leaf hashes (SHA-256 hex strings).
    Handles odd-length layers by duplicating the last node.
    """

    def __init__(self, leaf_hashes: List[str]):
        if not leaf_hashes:
            self.leaves = ["0" * 64]
        else:
            self.leaves = [h.lower() for h in leaf_hashes]

        self.levels: List[List[str]] = [self.leaves]
        self._build_tree()

    def _build_tree(self) -> None:
        """Constructs tree layers up to the root."""
        current_layer = self.leaves
        while len(current_layer) > 1:
            next_layer: List[str] = []
            for i in range(0, len(current_layer), 2):
                left = current_layer[i]
                # If odd number of elements, duplicate last node
                if i + 1 < len(current_layer):
                    right = current_layer[i + 1]
                else:
                    right = left
                next_layer.append(combine_hash_pair(left, right))
            self.levels.append(next_layer)
            current_layer = next_layer

    @property
    def root(self) -> str:
        """Returns the 32-byte hexadecimal Merkle root."""
        return self.levels[-1][0]

    def get_proof(self, leaf_index: int) -> List[Dict[str, str]]:
        """
        Generates an audit inclusion proof for a given leaf index.
        Returns a list of sibling objects: [{"position": "left"|"right", "hash": "<hex>"}]
        """
        if leaf_index < 0 or leaf_index >= len(self.leaves):
            raise IndexError(f"Leaf index {leaf_index} out of bounds (0..{len(self.leaves) - 1})")

        proof: List[Dict[str, str]] = []
        idx = leaf_index

        for level in self.levels[:-1]:  # Stop before root
            is_right_child = (idx % 2 == 1)
            if is_right_child:
                sibling_idx = idx - 1
                sibling_pos = "left"
            else:
                sibling_idx = idx + 1 if idx + 1 < len(level) else idx
                sibling_pos = "right"

            proof.append({
                "position": sibling_pos,
                "hash": level[sibling_idx],
            })
            idx = idx // 2

        return proof


def verify_merkle_proof(
    leaf_hash: str,
    proof: List[Dict[str, str]],
    expected_root: str,
) -> bool:
    """
    Verifies that leaf_hash belongs to the Merkle tree with expected_root given the proof.
    """
    if not leaf_hash or not expected_root:
        return False

    current = leaf_hash.lower()
    for step in proof:
        sibling = step.get("hash", "").lower()
        pos = step.get("position", "right")

        if pos == "left":
            current = combine_hash_pair(sibling, current)
        else:
            current = combine_hash_pair(current, sibling)

    return current.lower() == expected_root.lower()
