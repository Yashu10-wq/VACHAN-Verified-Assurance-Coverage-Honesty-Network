// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title AuditAnchor
 * @dev Append-only cryptographic audit trail anchoring smart contract for InsureChain VoiceGuard.
 * Stores batch commitments (Merkle roots) monotonically and emits verifiable provenance events.
 * Never stores PII, raw business records, or sensitive text on-chain.
 */
contract AuditAnchor {
    address public owner;
    uint256 public totalAnchors;

    struct AnchorRecord {
        bytes32 rootHash;
        uint256 sequenceNumber;
        uint256 timestamp;
        uint256 eventCount;
    }

    // Monotonically increasing sequenceNumber => AnchorRecord
    mapping(uint256 => AnchorRecord) public anchors;

    // Commitment rootHash => sequenceNumber (0 if non-existent)
    mapping(bytes32 => uint256) public commitmentToSequence;

    event OwnershipTransferred(address indexed previousOwner, address indexed newOwner);
    event AuditBatchAnchored(
        uint256 indexed sequenceNumber,
        bytes32 indexed rootHash,
        uint256 eventCount,
        uint256 timestamp
    );

    modifier onlyOwner() {
        require(msg.sender == owner, "AuditAnchor: caller is not owner");
        _;
    }

    constructor() {
        owner = msg.sender;
        emit OwnershipTransferred(address(0), msg.sender);
    }

    /**
     * @dev Transfers ownership of the contract to a new address.
     */
    function transferOwnership(address newOwner) external onlyOwner {
        require(newOwner != address(0), "AuditAnchor: new owner is the zero address");
        emit OwnershipTransferred(owner, newOwner);
        owner = newOwner;
    }

    /**
     * @dev Anchors a new audit batch commitment (Merkle root).
     * Monotonically appends sequence numbers and prevents duplicate submissions.
     */
    function anchorBatch(bytes32 rootHash, uint256 eventCount) external onlyOwner returns (uint256 sequenceNumber) {
        require(rootHash != bytes32(0), "AuditAnchor: root hash cannot be zero");
        require(eventCount > 0, "AuditAnchor: event count must be greater than zero");
        require(commitmentToSequence[rootHash] == 0, "AuditAnchor: commitment already anchored");

        totalAnchors += 1;
        sequenceNumber = totalAnchors;

        anchors[sequenceNumber] = AnchorRecord({
            rootHash: rootHash,
            sequenceNumber: sequenceNumber,
            timestamp: block.timestamp,
            eventCount: eventCount
        });

        commitmentToSequence[rootHash] = sequenceNumber;

        emit AuditBatchAnchored(sequenceNumber, rootHash, eventCount, block.timestamp);
        return sequenceNumber;
    }

    /**
     * @dev Checks if a given root hash has been anchored and returns its record metadata.
     */
    function verifyCommitment(bytes32 rootHash) external view returns (
        bool exists,
        uint256 sequenceNumber,
        uint256 timestamp,
        uint256 eventCount
    ) {
        uint256 seq = commitmentToSequence[rootHash];
        if (seq == 0) {
            return (false, 0, 0, 0);
        }
        AnchorRecord memory rec = anchors[seq];
        return (true, rec.sequenceNumber, rec.timestamp, rec.eventCount);
    }

    /**
     * @dev Retrieves anchor details by sequential identifier.
     */
    function getAnchor(uint256 sequenceNumber) external view returns (
        bytes32 rootHash,
        uint256 timestamp,
        uint256 eventCount
    ) {
        require(sequenceNumber > 0 && sequenceNumber <= totalAnchors, "AuditAnchor: sequence number out of bounds");
        AnchorRecord memory rec = anchors[sequenceNumber];
        return (rec.rootHash, rec.timestamp, rec.eventCount);
    }
}
