const { expect } = require("chai");
const { ethers } = require("hardhat");

describe("AuditAnchor Smart Contract", function () {
  let auditAnchor;
  let owner;
  let nonOwner;

  const sampleRoot1 = "0x" + "a".repeat(64);
  const sampleRoot2 = "0x" + "b".repeat(64);
  const zeroRoot = ethers.ZeroHash;

  beforeEach(async function () {
    [owner, nonOwner] = await ethers.getSigners();
    const AuditAnchorFactory = await ethers.getContractFactory("AuditAnchor");
    auditAnchor = await AuditAnchorFactory.deploy();
    await auditAnchor.waitForDeployment();
  });

  describe("Deployment", function () {
    it("should set the deployer as owner", async function () {
      expect(await auditAnchor.owner()).to.equal(owner.address);
    });

    it("should start with 0 total anchors", async function () {
      expect(await auditAnchor.totalAnchors()).to.equal(0);
    });
  });

  describe("Successful Anchoring", function () {
    it("should anchor a valid batch commitment monotonically", async function () {
      const tx = await auditAnchor.anchorBatch(sampleRoot1, 10);
      const receipt = await tx.wait();

      expect(await auditAnchor.totalAnchors()).to.equal(1);

      // Verify stored commitment
      const [exists, seq, timestamp, count] = await auditAnchor.verifyCommitment(sampleRoot1);
      expect(exists).to.be.true;
      expect(seq).to.equal(1);
      expect(count).to.equal(10);
      expect(timestamp).to.be.gt(0);

      // Verify anchor getter
      const [rootHash, anchorTs, anchorCount] = await auditAnchor.getAnchor(1);
      expect(rootHash).to.equal(sampleRoot1);
      expect(anchorCount).to.equal(10);
      expect(anchorTs).to.equal(timestamp);
    });

    it("should support multiple sequential anchors (append-only)", async function () {
      await auditAnchor.anchorBatch(sampleRoot1, 5);
      await auditAnchor.anchorBatch(sampleRoot2, 8);

      expect(await auditAnchor.totalAnchors()).to.equal(2);

      const [, seq1] = await auditAnchor.verifyCommitment(sampleRoot1);
      const [, seq2] = await auditAnchor.verifyCommitment(sampleRoot2);

      expect(seq1).to.equal(1);
      expect(seq2).to.equal(2);
    });
  });

  describe("Error and Validation Conditions", function () {
    it("should reject zero-value root hash", async function () {
      await expect(
        auditAnchor.anchorBatch(zeroRoot, 5)
      ).to.be.revertedWith("AuditAnchor: root hash cannot be zero");
    });

    it("should reject zero event count", async function () {
      await expect(
        auditAnchor.anchorBatch(sampleRoot1, 0)
      ).to.be.revertedWith("AuditAnchor: event count must be greater than zero");
    });

    it("should reject duplicate commitments", async function () {
      await auditAnchor.anchorBatch(sampleRoot1, 5);

      await expect(
        auditAnchor.anchorBatch(sampleRoot1, 5)
      ).to.be.revertedWith("AuditAnchor: commitment already anchored");
    });

    it("should reject unauthorized callers", async function () {
      await expect(
        auditAnchor.connect(nonOwner).anchorBatch(sampleRoot1, 5)
      ).to.be.revertedWith("AuditAnchor: caller is not owner");
    });

    it("should return false for unknown commitments", async function () {
      const unknownHash = "0x" + "f".repeat(64);
      const [exists, seq, timestamp, count] = await auditAnchor.verifyCommitment(unknownHash);
      expect(exists).to.be.false;
      expect(seq).to.equal(0);
      expect(timestamp).to.equal(0);
      expect(count).to.equal(0);
    });

    it("should revert getAnchor for out of bounds sequence", async function () {
      await expect(
        auditAnchor.getAnchor(99)
      ).to.be.revertedWith("AuditAnchor: sequence number out of bounds");
    });
  });
});
