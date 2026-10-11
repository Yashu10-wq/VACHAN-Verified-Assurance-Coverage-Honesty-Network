const hre = require("hardhat");
const fs = require("fs");
const path = require("path");

async function main() {
  console.log("Deploying AuditAnchor to network:", hre.network.name);

  const AuditAnchor = await hre.ethers.getContractFactory("AuditAnchor");
  const auditAnchor = await AuditAnchor.deploy();
  await auditAnchor.waitForDeployment();

  const contractAddress = await auditAnchor.getAddress();
  console.log("AuditAnchor deployed successfully at:", contractAddress);

  // Read artifact to get ABI
  const artifactPath = path.join(__dirname, "../artifacts/contracts/AuditAnchor.sol/AuditAnchor.json");
  const artifact = JSON.parse(fs.readFileSync(artifactPath, "utf8"));

  const deploymentData = {
    contractAddress: contractAddress,
    network: hre.network.name,
    chainId: hre.network.config.chainId || 31337,
    deployedAt: new Date().toISOString(),
    abi: artifact.abi,
  };

  // 1. Save in blockchain workspace
  const deployDir = path.join(__dirname, "../deployments");
  if (!fs.existsSync(deployDir)) {
    fs.mkdirSync(deployDir, { recursive: true });
  }
  fs.writeFileSync(
    path.join(deployDir, `${hre.network.name}.json`),
    JSON.stringify(deploymentData, null, 2)
  );

  // 2. Export ABI and address for backend
  const backendAbiDir = path.join(__dirname, "../../backend/app/core/abi");
  if (!fs.existsSync(backendAbiDir)) {
    fs.mkdirSync(backendAbiDir, { recursive: true });
  }
  fs.writeFileSync(
    path.join(backendAbiDir, "AuditAnchor.json"),
    JSON.stringify(deploymentData, null, 2)
  );

  console.log("ABI and deployment metadata exported to backend/app/core/abi/AuditAnchor.json");
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
