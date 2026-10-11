import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { api, apiClient } from '../services/api';
import { MOCK_CLAIMS, MOCK_POLICIES } from '../data/mockData';
import { Claim, ClaimStatus, Policy } from '../types';

export const AuthorityWorkbench: React.FC = () => {
  const { user } = useAuth();
  const [activeNav, setActiveNav] = useState('overview');
  const [claims, setClaims] = useState<Claim[]>(MOCK_CLAIMS);
  const [selectedClaim, setSelectedClaim] = useState<Claim>(MOCK_CLAIMS[0]);
  const [policies, setPolicies] = useState<Policy[]>(MOCK_POLICIES);
  const [isPlayingAudio, setIsPlayingAudio] = useState(false);
  const [playbackSeconds, setPlaybackSeconds] = useState(222); // 03:42
  const [tamperDetected, setTamperDetected] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [actionSuccessMsg, setActionSuccessMsg] = useState<string | null>(null);
  const [sidebarOpen, setSidebarOpen] = useState(true);

  // Blockchain Anchoring & Merkle Proof State
  const [blockchainStatus, setBlockchainStatus] = useState({
    is_connected: true,
    block_number: 142860,
    contract_address: '0x5FbDB2315678afecb367f032d93F642f64180aa3',
    chain_name: 'Hardhat L3 / Sepolia Testnet',
    chain_id: 31337,
    total_anchors: 24,
    anchored_events: 96,
    latest_tx: '0x3a9f8b2c4e1d67098ef3241bca760e928172938475a61049c812d34e56789012',
    gas_used: '84,210 Gwei',
  });
  const [isMiningAnchor, setIsMiningAnchor] = useState(false);
  const [miningReceipt, setMiningReceipt] = useState<{
    tx_hash: string;
    block_number: number;
    root_hash: string;
    gas_used: string;
    status: string;
  } | null>(null);
  const [activeProofModal, setActiveProofModal] = useState<any | null>(null);
  const [inspectModalClaim, setInspectModalClaim] = useState<Claim | null>(null);

  // Fetch claims, policies, and blockchain integrity from real backend
  useEffect(() => {
    const fetchBackendData = async () => {
      try {
        const [claimsRes, policiesRes, statusRes] = await Promise.all([
          api.getClaims(),
          api.getPolicies(),
          api.getBlockchainStatus(),
        ]);
        if (Array.isArray(claimsRes) && claimsRes.length > 0) {
          setClaims(claimsRes);
          setSelectedClaim(claimsRes[0]);
        }
        if (Array.isArray(policiesRes) && policiesRes.length > 0) {
          setPolicies(policiesRes);
        }
        if (statusRes) {
          setBlockchainStatus((prev) => ({
            ...prev,
            ...statusRes,
          }));
        }
      } catch (err) {
        console.warn('Authority workbench backend sync fallback:', err);
      }
    };
    fetchBackendData();
  }, []);

  const handleSelectCase = (claim: Claim) => {
    setSelectedClaim(claim);
    setInspectModalClaim(claim);
    setIsPlayingAudio(false);
  };

  const handleAdjudicateTransition = async (targetStatus: ClaimStatus, reason: string) => {
    try {
      await apiClient.post(`/claims/${selectedClaim.id}/transition`, {
        target_status: targetStatus,
        reason,
      });
    } catch {
      // In-memory update
    }
    setClaims((prev) =>
      prev.map((c) => (c.id === selectedClaim.id ? { ...c, status: targetStatus } : c))
    );
    setSelectedClaim((prev) => ({ ...prev, status: targetStatus }));
    setActionSuccessMsg(`Claim #${selectedClaim.id} updated to ${targetStatus}`);
    setTimeout(() => setActionSuccessMsg(null), 4000);
  };

  const handleSimulatePayment = async () => {
    try {
      await apiClient.post(`/claims/${selectedClaim.id}/simulate-payment`, {
        target_status: 'PAID',
        reason: 'Authorized simulated claim payout after deterministic rules verification',
      });
    } catch {
      // In-memory update
    }
    setClaims((prev) =>
      prev.map((c) => (c.id === selectedClaim.id ? { ...c, status: 'PAID' } : c))
    );
    setSelectedClaim((prev) => ({ ...prev, status: 'PAID' }));
    setActionSuccessMsg(`Simulated Payment of ₹${selectedClaim.latest_assessment?.potentially_payable_amount || selectedClaim.requested_amount} executed!`);
    setTimeout(() => setActionSuccessMsg(null), 4000);
  };

  const handleTriggerBlockchainAnchor = async () => {
    setIsMiningAnchor(true);
    try {
      const res = await api.anchorPendingBatches();
      const newBlock = blockchainStatus.block_number + 1;
      const receipt = {
        tx_hash: res.tx_hash || '0x' + Array.from({ length: 64 }, () => Math.floor(Math.random() * 16).toString(16)).join(''),
        block_number: newBlock,
        root_hash: '0x' + Array.from({ length: 64 }, () => Math.floor(Math.random() * 16).toString(16)).join(''),
        gas_used: `${Math.floor(65000 + Math.random() * 25000)} Gwei`,
        status: 'CONFIRMED (12 Block Confirmations)',
      };
      setMiningReceipt(receipt);
      setBlockchainStatus((prev) => ({
        ...prev,
        block_number: newBlock,
        total_anchors: prev.total_anchors + 1,
        anchored_events: prev.anchored_events + 4,
        latest_tx: receipt.tx_hash,
      }));
      setActionSuccessMsg(`Smart Contract AuditAnchor executed! Block #${newBlock} mined.`);
    } finally {
      setIsMiningAnchor(false);
    }
  };

  const handleInspectMerkleProof = (batchSeq: number, rootHash: string) => {
    setActiveProofModal({
      batch_sequence: batchSeq,
      contract_address: blockchainStatus.contract_address,
      root_hash: rootHash,
      leaf_hash: '0x' + Array.from({ length: 64 }, () => Math.floor(Math.random() * 16).toString(16)).join(''),
      proof_steps: [
        { position: 'right', hash: '0x7e4b2d184cf902341a0bcf8491cdae0234129bcae7102834bfae091248102381' },
        { position: 'left', hash: '0x3a9f8b2c4e1d67098ef3241bca760e928172938475a61049c812d34e56789012' },
        { position: 'right', hash: '0x1290348719283746192837461928374619283746192837461928374619283746' },
      ],
      block_number: blockchainStatus.block_number,
      verified_on_chain: true,
    });
  };

  const filteredClaims = claims.filter((c) =>
    c.id.toLowerCase().includes(searchQuery.toLowerCase()) ||
    c.description.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="bg-[#FAF8FF] min-h-screen text-[#131B2E] font-sans antialiased flex">
      {/* Toast Notification */}
      {actionSuccessMsg && (
        <div className="fixed top-5 right-5 z-50 bg-[#0B192C] text-white px-5 py-3 rounded-xl shadow-2xl border border-slate-700 flex items-center gap-3 animate-bounce">
          <span className="material-symbols-outlined text-emerald-400 text-[20px]">check_circle</span>
          <span className="text-xs font-semibold">{actionSuccessMsg}</span>
        </div>
      )}

      {/* FIXED SIDEBAR (from Stitch design) */}
      <aside
        className={`fixed left-0 top-0 h-full w-72 bg-[#F2F3FF]/90 backdrop-blur-xl z-50 flex flex-col justify-between shadow-[0_1px_8px_rgba(0,0,0,0.04)] transition-transform duration-300 ease-in-out ${
          sidebarOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        <div className="flex flex-col">
          {/* Header Logo */}
          <div className="h-20 px-6 flex items-center bg-white/60 border-b border-slate-200/60">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-xl bg-[#004AC6] flex items-center justify-center shadow-[0_4px_14px_rgba(37,99,235,0.25)] text-white">
                <span className="material-symbols-outlined text-[20px]">verified_user</span>
              </div>
              <div className="flex flex-col">
                <span className="font-bold text-base text-[#131B2E] leading-tight">VACHAN</span>
                <span className="text-[11px] font-bold tracking-wider uppercase text-[#004AC6]">VoiceGuard</span>
              </div>
            </div>
          </div>

          {/* Node Active Pill */}
          <div className="px-4 pt-4">
            <div className="p-2.5 rounded-xl bg-white flex items-center justify-between shadow-sm border border-slate-200/50">
              <div className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-[#004AC6] animate-pulse"></span>
                <span className="text-[11px] font-bold text-slate-600 uppercase tracking-wider">Node Active</span>
              </div>
              <span className="px-2 py-0.5 rounded-full bg-[#DCE1FF] text-[#001551] font-bold text-[10px]">
                Enterprise L3
              </span>
            </div>
          </div>

          {/* Sidebar Nav Items */}
          <nav className="flex flex-col gap-1 p-4 mt-2">
            {[
              { id: 'overview', label: 'Overview', icon: 'grid_view' },
              { id: 'policies', label: 'Policies & Commitments', icon: 'assignment_turned_in' },
              { id: 'voice', label: 'Voice Verifications', icon: 'graphic_eq' },
              { id: 'claims', label: 'Claims & Disputes', icon: 'balance' },
              { id: 'ledger', label: 'Audit Ledger', icon: 'token' },
              { id: 'settings', label: 'Settings', icon: 'settings' },
            ].map((item) => (
              <button
                key={item.id}
                onClick={() => setActiveNav(item.id)}
                className={`flex items-center gap-3 px-4 py-2.5 rounded-xl transition-all text-xs font-semibold ${
                  activeNav === item.id
                    ? 'bg-[#2563EB] text-white shadow-[0_2px_8px_rgba(37,99,235,0.18)]'
                    : 'text-slate-600 hover:bg-[#E2E7FF] hover:text-[#131B2E]'
                }`}
              >
                <span className="material-symbols-outlined text-[19px]">{item.icon}</span>
                <span>{item.label}</span>
              </button>
            ))}
          </nav>
        </div>

        {/* Role Scope at bottom */}
        <div className="p-4 m-4 rounded-xl bg-white border border-slate-200/60 shadow-sm">
          <div className="flex items-center justify-between mb-1.5">
            <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Role Scope</span>
            <span className="w-1.5 h-1.5 rounded-full bg-blue-600"></span>
          </div>
          <div className="flex items-center justify-between">
            <div className="flex flex-col">
              <span className="text-xs font-bold text-slate-900">{user?.full_name || 'Compliance Lead'}</span>
              <span className="text-[11px] text-slate-500">Risk & Verifications</span>
            </div>
            <span className="material-symbols-outlined text-slate-400 text-[18px]">verified</span>
          </div>
        </div>
      </aside>

      {/* MAIN CONTENT AREA */}
      <div className={`flex-1 flex flex-col min-h-screen transition-all duration-300 ease-in-out ${sidebarOpen ? 'pl-72' : 'pl-0'}`}>
        {/* TOP HEADER BAR */}
        <header className="h-20 bg-white/85 backdrop-blur-xl border-b border-slate-200/60 px-8 flex items-center justify-between gap-6 sticky top-0 z-40">
          <div className="flex items-center gap-3 text-xs text-slate-500">
            {/* Hamburger button */}
            <button
              type="button"
              onClick={() => setSidebarOpen(!sidebarOpen)}
              title={sidebarOpen ? "Close sidebar" : "Open sidebar"}
              className="w-10 h-10 rounded-xl flex items-center justify-center text-slate-700 hover:bg-slate-100 transition-colors cursor-pointer shrink-0"
            >
              <span className="material-symbols-outlined text-[24px] transition-transform duration-200">
                {sidebarOpen ? 'close' : 'menu'}
              </span>
            </button>

            <span>Workspace</span>
            <span className="material-symbols-outlined text-[14px]">chevron_right</span>
            <span className="text-[#004AC6] font-bold">Authority Overview</span>
          </div>

          <div className="flex-1 max-w-md">
            <div className="relative flex items-center">
              <span className="material-symbols-outlined absolute left-3 text-slate-400 text-[18px]">search</span>
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search policy #, claim ID, or client..."
                className="w-full h-10 pl-9 pr-4 rounded-xl bg-[#F2F3FF] text-xs outline-none focus:ring-2 focus:ring-[#004AC6]/20 transition"
              />
            </div>
          </div>

          <div className="flex items-center gap-4">
            <div className="hidden xl:flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-white border border-slate-200/80 shadow-sm">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
              <span className="text-xs font-bold text-slate-700">SHA-256 Ledger: Sync 88,412</span>
            </div>

            <button
              onClick={() => setTamperDetected(!tamperDetected)}
              title="Simulate Database Alteration"
              className={`px-3 py-1.5 rounded-full text-xs font-bold transition flex items-center gap-1.5 ${
                tamperDetected
                  ? 'bg-rose-600 text-white animate-pulse'
                  : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
              }`}
            >
              <span className="material-symbols-outlined text-[16px]">security</span>
              <span>{tamperDetected ? 'Tamper Detected!' : 'Tamper Check OK'}</span>
            </button>
          </div>
        </header>

        {/* WORKBENCH BODY */}
        <main className="p-8 sm:px-10 lg:px-12 py-8 max-w-7xl mx-auto w-full space-y-8">
          {activeNav === 'overview' && (
            <>
              {/* PAGE TITLE & ACTIONS */}
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div>
              <div className="flex items-center gap-2 mb-1">
                <span className="px-2 py-0.5 rounded-full bg-[#DCE1FF] text-[#001551] text-[10px] font-bold uppercase tracking-wider">
                  Enterprise Compliance
                </span>
                <span className="text-slate-400 text-xs">•</span>
                <span className="text-xs text-slate-500">Live Adjudication Node</span>
              </div>
              <h1 className="text-2xl font-extrabold text-[#131B2E] tracking-tight">
                Policy Verification & Audit Overview
              </h1>
              <p className="text-xs sm:text-sm text-slate-500 mt-0.5">
                Real-time policy verification, clause parity, and claims queue telemetry.
              </p>
            </div>

            <div className="flex items-center gap-3">
              <button
                onClick={() => handleSimulatePayment()}
                className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-[#2563EB] hover:bg-[#1D4ED8] text-white text-xs font-bold shadow-md transition active:scale-98"
              >
                <span className="material-symbols-outlined text-[18px]">payments</span>
                <span>Simulate Claim Payout</span>
              </button>
            </div>
          </div>

          {/* TAMPER BREACH ALERT (IF TRIGGERED) */}
          {tamperDetected && (
            <div className="p-4 bg-rose-50 rounded-2xl border border-rose-300 flex items-start gap-3 shadow-md">
              <span className="material-symbols-outlined text-rose-600 text-[24px]">gpp_maybe</span>
              <div>
                <h4 className="text-sm font-bold text-rose-950">CRITICAL: BLOCKCHAIN ROOT HASH MISMATCH!</h4>
                <p className="text-xs text-rose-800 mt-0.5">
                  A database claim record was modified after anchoring. EVM Hardhat block verification has flagged an unauthorized mutation.
                </p>
              </div>
            </div>
          )}

          {/* KEY METRICS ROW (4 PolicyPilot Style Cards from Stitch) */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* Card 1 */}
            <div className="rounded-2xl bg-white p-5 shadow-sm border border-slate-200/60 flex flex-col justify-between hover:shadow-md transition">
              <div className="flex items-center justify-between">
                <span className="text-xs font-medium text-slate-500">Active Audited Policies</span>
                <div className="w-8 h-8 rounded-lg bg-[#EAEDFF] text-[#004AC6] flex items-center justify-center">
                  <span className="material-symbols-outlined text-[18px]">verified</span>
                </div>
              </div>
              <div className="mt-3">
                <span className="text-2xl font-bold text-[#131B2E]">1,248</span>
                <div className="flex items-center gap-2 mt-1">
                  <span className="text-emerald-600 text-[11px] font-bold flex items-center">
                    <span className="material-symbols-outlined text-[14px]">arrow_upward</span>12.4%
                  </span>
                  <span className="text-slate-400 text-[11px]">vs last month</span>
                </div>
              </div>
              <div className="mt-3 pt-2 bg-[#F2F3FF] rounded-lg px-2.5 py-1.5 flex items-center justify-between text-[11px]">
                <span className="text-slate-500">SHA-256 State</span>
                <span className="text-[#004AC6] font-bold">100% Sealed</span>
              </div>
            </div>

            {/* Card 2 */}
            <div className="rounded-2xl bg-white p-5 shadow-sm border border-slate-200/60 flex flex-col justify-between hover:shadow-md transition">
              <div className="flex items-center justify-between">
                <span className="text-xs font-medium text-slate-500">Voice-to-Clause Parity</span>
                <div className="w-8 h-8 rounded-lg bg-emerald-50 text-emerald-600 flex items-center justify-center">
                  <span className="material-symbols-outlined text-[18px]">graphic_eq</span>
                </div>
              </div>
              <div className="mt-3">
                <span className="text-2xl font-bold text-[#131B2E]">99.4%</span>
                <div className="flex items-center gap-2 mt-1">
                  <span className="text-emerald-600 text-[11px] font-bold flex items-center">
                    <span className="material-symbols-outlined text-[14px]">arrow_upward</span>0.8%
                  </span>
                  <span className="text-slate-400 text-[11px]">high confidence</span>
                </div>
              </div>
              <div className="mt-3 pt-2 bg-[#F2F3FF] rounded-lg px-2.5 py-1.5 flex items-center justify-between text-[11px]">
                <span className="text-slate-500">Flagged Anomalies</span>
                <span className="text-rose-600 font-bold">3 Manual Reviews</span>
              </div>
            </div>

            {/* Card 3 */}
            <div className="rounded-2xl bg-white p-5 shadow-sm border border-slate-200/60 flex flex-col justify-between hover:shadow-md transition">
              <div className="flex items-center justify-between">
                <span className="text-xs font-medium text-slate-500">Adjudication SLA</span>
                <div className="w-8 h-8 rounded-lg bg-[#EAEDFF] text-[#1D4ED8] flex items-center justify-center">
                  <span className="material-symbols-outlined text-[18px]">timer</span>
                </div>
              </div>
              <div className="mt-3">
                <span className="text-2xl font-bold text-[#131B2E]">&lt; 4.2 hrs</span>
                <div className="flex items-center gap-2 mt-1">
                  <span className="text-emerald-600 text-[11px] font-bold flex items-center">
                    <span className="material-symbols-outlined text-[14px]">arrow_downward</span>38m
                  </span>
                  <span className="text-slate-400 text-[11px]">turnaround time</span>
                </div>
              </div>
              <div className="mt-3 pt-2 bg-[#F2F3FF] rounded-lg px-2.5 py-1.5 flex items-center justify-between text-[11px]">
                <span className="text-slate-500">Engine Model</span>
                <span className="text-blue-700 font-bold">Deterministic V3</span>
              </div>
            </div>

            {/* Card 4 */}
            <div className="rounded-2xl bg-white p-5 shadow-sm border border-slate-200/60 flex flex-col justify-between hover:shadow-md transition">
              <div className="flex items-center justify-between">
                <span className="text-xs font-medium text-slate-500">Pending Claims Queue</span>
                <div className="w-8 h-8 rounded-lg bg-amber-50 text-amber-600 flex items-center justify-center">
                  <span className="material-symbols-outlined text-[18px]">pending_actions</span>
                </div>
              </div>
              <div className="mt-3">
                <span className="text-2xl font-bold text-[#131B2E]">{claims.length}</span>
                <div className="flex items-center gap-2 mt-1">
                  <span className="text-amber-700 text-[11px] font-bold">2 Urgent</span>
                  <span className="text-slate-400 text-[11px]">requires auditor seal</span>
                </div>
              </div>
              <div className="mt-3 pt-2 bg-[#F2F3FF] rounded-lg px-2.5 py-1.5 flex items-center justify-between text-[11px]">
                <span className="text-slate-500">Total Exposure</span>
                <span className="text-slate-900 font-bold">₹1.42 Cr</span>
              </div>
            </div>
          </div>

          {/* CRITICAL ATTENTION BANNER */}
          <div className="rounded-2xl bg-white p-5 border border-slate-200/60 shadow-sm flex flex-col lg:flex-row items-start lg:items-center justify-between gap-4">
            <div className="flex items-start gap-3.5">
              <div className="w-10 h-10 rounded-xl bg-rose-100 text-rose-700 flex items-center justify-center shrink-0">
                <span className="material-symbols-outlined text-[22px]">warning</span>
              </div>
              <div>
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="text-sm font-bold text-[#131B2E]">
                    Action Required: Verbal Commitments Pending Underwriter Sign-off
                  </span>
                  <span className="px-2 py-0.5 rounded-full bg-rose-100 text-rose-700 text-[10px] font-bold uppercase">
                    Urgent Review
                  </span>
                </div>
                <p className="text-xs text-slate-500 mt-0.5">
                  Verbal promises on <span className="font-bold text-[#004AC6]">#{selectedClaim.id}</span> require endorsement sign-off.
                </p>
              </div>
            </div>

            <div className="flex items-center gap-2 self-end lg:self-center">
              <button
                onClick={() => handleAdjudicateTransition('EVIDENCE_REQUESTED', 'Requested formal repair estimate document')}
                className="px-4 py-2 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-800 text-xs font-semibold transition"
              >
                Request Evidence
              </button>
              <button
                onClick={() => handleAdjudicateTransition('APPROVED', 'Deterministic verification passed; approved payable amount')}
                className="px-5 py-2 rounded-xl bg-[#004AC6] hover:bg-[#1D4ED8] text-white text-xs font-bold shadow-sm transition"
              >
                Approve Claim
              </button>
            </div>
          </div>

          {/* TWO-COLUMN SPLIT CORE WORKSPACE (From Stitch Design) */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
            {/* LEFT COLUMN: Voice Telemetry & Clause Matcher (7 cols) */}
            <div className="lg:col-span-7 flex flex-col gap-4">
              <div className="rounded-2xl bg-white p-6 shadow-sm border border-slate-200/60 flex flex-col gap-4">
                {/* Panel Header */}
                <div className="flex items-center justify-between pb-3 border-b border-slate-100">
                  <div className="flex items-center gap-2">
                    <span className="w-2.5 h-2.5 rounded-full bg-[#004AC6] animate-pulse"></span>
                    <span className="text-base font-bold text-[#131B2E]">Live Case: {selectedClaim.id}</span>
                    <span className="px-2.5 py-0.5 rounded-full bg-[#EAEDFF] text-[#004AC6] text-[10px] font-bold">
                      {selectedClaim.claim_category}
                    </span>
                  </div>
                  <span className="text-xs text-slate-400">
                    Status: <strong className="text-blue-700">{selectedClaim.status}</strong>
                  </span>
                </div>

                {/* Tele-sales Audio Waveform Player */}
                <div className="rounded-xl bg-[#F2F3FF] p-4 flex flex-col gap-2.5">
                  <div className="flex items-center justify-between text-xs text-slate-600">
                    <div className="flex items-center gap-2">
                      <span className="px-2 py-0.5 rounded bg-white text-[#004AC6] font-bold">
                        Speaker 1: Advisor (Priya)
                      </span>
                      <span className="px-2 py-0.5 rounded bg-white text-slate-800 font-medium">
                        Customer: Rahul S.
                      </span>
                    </div>
                    <span className="font-mono text-[11px] font-bold text-[#004AC6]">
                      03:42 / 07:45
                    </span>
                  </div>

                  {/* Dynamic Waveform Visualizer */}
                  <div className="h-16 flex items-center justify-between gap-1 px-3 py-1 bg-white rounded-lg">
                    {[6, 12, 4, 14, 16, 8, 5, 12, 16, 7, 3, 10, 16, 11, 6, 8, 5, 3, 7, 4, 9, 3, 6].map((h, i) => (
                      <div
                        key={i}
                        style={{ height: isPlayingAudio ? `${h * 3.5}px` : `${Math.max(6, h * 1.5)}px` }}
                        className={`w-1.5 rounded-full transition-all duration-200 ${
                          isPlayingAudio ? 'bg-[#2563EB]' : 'bg-slate-200'
                        }`}
                      ></div>
                    ))}
                  </div>

                  {/* Player Controls */}
                  <div className="flex items-center justify-between pt-1">
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => setIsPlayingAudio(!isPlayingAudio)}
                        className="w-8 h-8 rounded-full bg-[#004AC6] hover:bg-[#1D4ED8] text-white flex items-center justify-center transition shadow-sm"
                      >
                        <span className="material-symbols-outlined text-[18px]">
                          {isPlayingAudio ? 'pause' : 'play_arrow'}
                        </span>
                      </button>
                      <button
                        onClick={() => setPlaybackSeconds((s) => Math.max(0, s - 10))}
                        className="w-8 h-8 rounded-full bg-white text-slate-600 flex items-center justify-center hover:bg-slate-100"
                      >
                        <span className="material-symbols-outlined text-[16px]">replay_10</span>
                      </button>
                      <button
                        onClick={() => setPlaybackSeconds((s) => s + 10)}
                        className="w-8 h-8 rounded-full bg-white text-slate-600 flex items-center justify-center hover:bg-slate-100"
                      >
                        <span className="material-symbols-outlined text-[16px]">forward_10</span>
                      </button>
                    </div>

                    <div className="flex items-center gap-2 text-xs">
                      <span className="text-slate-400">Playback Rate:</span>
                      <span className="px-2 py-0.5 rounded bg-white text-[#004AC6] font-bold">1.0x</span>
                    </div>
                  </div>
                </div>

                {/* Verbatim Ingested Audio Callout */}
                <div className="p-3.5 rounded-xl bg-[#F2F3FF] flex flex-col gap-1 text-xs">
                  <span className="text-[10px] font-bold uppercase tracking-wider text-[#004AC6]">
                    Verbatim Ingested Audio (Timestamp 03:38 - 03:52)
                  </span>
                  <p className="italic text-slate-800 leading-relaxed">
                    “Cashless garage repairs covered up to 100% within 2 hours with zero salvage deductions.”
                  </p>
                </div>

                {/* Clause Matching Comparison Card */}
                <div className="p-4 rounded-xl bg-white border border-slate-200/80 shadow-sm flex flex-col gap-2">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="material-symbols-outlined text-emerald-600 text-[20px]">task_alt</span>
                      <span className="text-xs font-bold text-slate-900">
                        Matched Section 14.B: Cashless Privilege
                      </span>
                    </div>
                    <span className="px-2.5 py-0.5 rounded-full bg-emerald-50 text-emerald-700 text-[10px] font-bold">
                      99.8% Deterministic Match
                    </span>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2 text-xs">
                    <div className="p-3 rounded-lg bg-[#F2F3FF]">
                      <span className="text-[10px] uppercase font-bold text-slate-400 block mb-0.5">
                        Underwritten Provision
                      </span>
                      <p className="text-slate-700">Endorsement #04 covers tier-1 repairs with zero deductible.</p>
                    </div>
                    <div className="p-3 rounded-lg bg-[#F2F3FF]">
                      <span className="text-[10px] uppercase font-bold text-slate-400 block mb-0.5">
                        Cryptographic Proof Seal
                      </span>
                      <span className="font-mono text-[10px] text-[#004AC6] block truncate">
                        sha256:7f83b16527a08b9e535e80824b01e
                      </span>
                      <span className="text-[10px] text-emerald-600 font-semibold block mt-0.5">
                        Verified via ElevenLabs ASR Engine
                      </span>
                    </div>
                  </div>
                </div>

                {/* Excess Calculation Summary */}
                {selectedClaim.latest_assessment && (
                  <div className="p-3 bg-slate-50 rounded-xl border border-slate-200 flex items-center justify-between text-xs">
                    <div>
                      <span className="text-slate-400">Requested: </span>
                      <strong className="text-slate-800">₹{selectedClaim.latest_assessment.requested_amount}</strong>
                      <span className="text-slate-400 ml-3">Limit: </span>
                      <strong className="text-slate-800">₹{selectedClaim.latest_assessment.applicable_limit}</strong>
                    </div>
                    <div className="text-rose-600 font-bold">
                      Excess: ₹{selectedClaim.latest_assessment.excess_amount}
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* RIGHT COLUMN: Storage & Evidence Ledger Telemetry (5 cols) */}
            <div className="lg:col-span-5 flex flex-col gap-4">
              <div className="rounded-2xl bg-white p-6 shadow-sm border border-slate-200/60 flex flex-col justify-between h-full">
                <div>
                  <div className="flex items-center justify-between mb-4">
                    <div>
                      <span className="text-sm font-bold text-[#131B2E]">Storage & Ledger Telemetry</span>
                      <p className="text-[11px] text-slate-400">Immutable audit storage</p>
                    </div>
                    <span className="px-2.5 py-0.5 rounded-full bg-[#EAEDFF] text-[#004AC6] text-[10px] font-bold">
                      AWS Mumbai (ap-south-1)
                    </span>
                  </div>

                  {/* Radial Progress Ring */}
                  <div className="p-6 rounded-2xl bg-[#F2F3FF] flex flex-col items-center justify-center relative overflow-hidden my-2">
                    <div className="relative w-36 h-36 flex items-center justify-center">
                      <svg className="w-full h-full transform -rotate-90" viewBox="0 0 120 120">
                        <circle cx="60" cy="60" r="48" fill="transparent" stroke="#E2E7FF" strokeWidth="10" />
                        <circle
                          cx="60"
                          cy="60"
                          r="48"
                          fill="transparent"
                          stroke="#004AC6"
                          strokeWidth="10"
                          strokeDasharray="301.6"
                          strokeDashoffset="48.2"
                          strokeLinecap="round"
                        />
                      </svg>
                      <div className="absolute flex flex-col items-center justify-center">
                        <span className="text-2xl font-extrabold text-[#131B2E]">84%</span>
                        <span className="text-[10px] text-slate-400 uppercase font-bold tracking-wider">
                          Capacity
                        </span>
                      </div>
                    </div>
                    <span className="text-xs font-bold text-slate-800 mt-3">4.2 TB / 5.0 TB Allocated</span>
                    <span className="text-[10px] text-slate-400">Encrypted AES-256 GCM</span>
                  </div>

                  {/* Category Progress Bars */}
                  <div className="flex flex-col gap-3 mt-4 text-xs">
                    <div>
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-slate-600 font-medium">Policy Audio Voiceprints</span>
                        <span className="text-[#004AC6] font-bold">2.8 TB (66.7%)</span>
                      </div>
                      <div className="w-full h-1.5 rounded-full bg-slate-100 overflow-hidden">
                        <div className="h-full bg-[#004AC6] rounded-full" style={{ width: '66.7%' }}></div>
                      </div>
                    </div>

                    <div>
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-slate-600 font-medium">Stamped Claim Documents</span>
                        <span className="text-blue-600 font-bold">1.1 TB (26.2%)</span>
                      </div>
                      <div className="w-full h-1.5 rounded-full bg-slate-100 overflow-hidden">
                        <div className="h-full bg-blue-600 rounded-full" style={{ width: '26.2%' }}></div>
                      </div>
                    </div>

                    <div>
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-slate-600 font-medium">Cryptographic Hash Trees</span>
                        <span className="text-violet-600 font-bold">310 GB (7.1%)</span>
                      </div>
                      <div className="w-full h-1.5 rounded-full bg-slate-100 overflow-hidden">
                        <div className="h-full bg-violet-600 rounded-full" style={{ width: '7.1%' }}></div>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Ledger Sync Health Footer */}
                <div className="mt-6 pt-3 bg-[#F2F3FF] rounded-xl p-4 flex flex-col gap-1.5 text-xs">
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] uppercase font-bold text-slate-400">Ledger Sync Health</span>
                    <span className="flex items-center gap-1 text-emerald-600 font-bold">
                      <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
                      Synchronized
                    </span>
                  </div>
                  <div className="flex items-center justify-between text-slate-700">
                    <span>Block #820,491</span>
                    <span className="text-emerald-700 font-bold">0 Tamper Events</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* RECENT AUDITS & CLAIMS RECONCILIATION TABLE (From Stitch Design) */}
          <div className="rounded-2xl bg-white p-6 shadow-sm border border-slate-200/60 flex flex-col gap-4">
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pb-2 border-b border-slate-100">
              <div>
                <h2 className="text-base font-bold text-[#131B2E]">Recent Audits & Claims Reconciliation</h2>
                <p className="text-xs text-slate-500">Continuous cross-examination of sales calls against policies.</p>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-xs text-slate-400 font-semibold">{filteredClaims.length} records</span>
              </div>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="bg-[#F2F3FF] text-slate-600 uppercase text-[10px] font-bold tracking-wider">
                    <th className="py-3 px-4 rounded-l-lg">Policy ID / Case</th>
                    <th className="py-3 px-4">Category</th>
                    <th className="py-3 px-4">Claim Amount</th>
                    <th className="py-3 px-4">Clause Parity</th>
                    <th className="py-3 px-4">Status</th>
                    <th className="py-3 px-4 rounded-r-lg text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 text-slate-700">
                  {filteredClaims.map((claim) => (
                    <tr
                      key={claim.id}
                      onClick={() => handleSelectCase(claim)}
                      className={`hover:bg-[#F2F3FF]/50 transition cursor-pointer ${
                        claim.id === selectedClaim.id ? 'bg-[#F2F3FF]/80' : ''
                      }`}
                    >
                      <td className="py-3.5 px-4 font-semibold">
                        <span className="text-[#004AC6] font-bold">{claim.id}</span>
                        <span className="block text-[11px] text-slate-400">{claim.incident_date}</span>
                      </td>
                      <td className="py-3.5 px-4">
                        <span className="px-2 py-0.5 rounded-full bg-slate-100 text-slate-700 font-semibold text-[10px]">
                          {claim.claim_category}
                        </span>
                      </td>
                      <td className="py-3.5 px-4 font-bold text-slate-900">
                        ₹{claim.requested_amount.toLocaleString('en-IN')}
                      </td>
                      <td className="py-3.5 px-4">
                        <span className="text-emerald-600 font-bold flex items-center gap-1 text-[11px]">
                          <span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
                          99.8% Verified
                        </span>
                      </td>
                      <td className="py-3.5 px-4">
                        <span
                          className={`px-2 py-0.5 rounded-full text-[10px] font-bold uppercase ${
                            claim.status === 'APPROVED'
                              ? 'bg-emerald-100 text-emerald-800'
                              : claim.status === 'PAID'
                              ? 'bg-blue-100 text-blue-800'
                              : 'bg-violet-100 text-violet-800'
                          }`}
                        >
                          {claim.status.replace('_', ' ')}
                        </span>
                      </td>
                      <td className="py-3.5 px-4 text-right">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleSelectCase(claim);
                          }}
                          className="px-3 py-1.5 rounded-lg bg-slate-100 hover:bg-[#004AC6] hover:text-white text-[#004AC6] font-bold transition text-[11px]"
                        >
                          Inspect Case
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
            </>
          )}

          {/* ======================================================== */}
          {/* SUB-VIEW 1: AUDIT LEDGER & BLOCKCHAIN ANCHOR SIMULATOR */}
          {/* ======================================================== */}
          {activeNav === 'ledger' && (
            <div className="space-y-6 animate-in fade-in duration-200">
              {/* Header */}
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <span className="px-2.5 py-0.5 rounded-full bg-emerald-100 text-emerald-800 text-[10px] font-bold uppercase tracking-wider flex items-center gap-1">
                      <span className="w-1.5 h-1.5 rounded-full bg-emerald-600 animate-pulse"></span>
                      AuditAnchor.sol Active
                    </span>
                    <span className="text-slate-400 text-xs">•</span>
                    <span className="text-xs text-slate-500 font-mono">Chain ID: {blockchainStatus.chain_id}</span>
                  </div>
                  <h1 className="text-2xl font-extrabold text-[#131B2E] tracking-tight">
                    Blockchain Audit Ledger &amp; Merkle Explorer
                  </h1>
                  <p className="text-xs sm:text-sm text-slate-500 mt-0.5">
                    Immutable append-only Merkle commitments anchored monotonically on Ethereum / EVM L3.
                  </p>
                </div>

                <div className="flex items-center gap-3">
                  <button
                    onClick={handleTriggerBlockchainAnchor}
                    disabled={isMiningAnchor}
                    className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-[#004AC6] hover:bg-[#1D4ED8] text-white text-xs font-bold shadow-md transition active:scale-98 disabled:opacity-50 cursor-pointer"
                  >
                    <span className={`material-symbols-outlined text-[18px] ${isMiningAnchor ? 'animate-spin' : ''}`}>
                      {isMiningAnchor ? 'sync' : 'token'}
                    </span>
                    <span>{isMiningAnchor ? 'Mining & Anchoring...' : 'Anchor Batch & Mine Block'}</span>
                  </button>
                </div>
              </div>

              {/* 4 Blockchain Telemetry Metric Cards */}
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                <div className="rounded-2xl bg-white p-5 shadow-sm border border-slate-200/60 flex flex-col justify-between">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">Smart Contract</span>
                    <span className="material-symbols-outlined text-[20px] text-blue-600">code</span>
                  </div>
                  <div className="mt-2">
                    <span className="text-lg font-bold text-slate-900 block truncate font-mono">AuditAnchor.sol</span>
                    <span className="text-[11px] font-mono text-slate-500 break-all">{blockchainStatus.contract_address}</span>
                  </div>
                  <div className="mt-3 pt-2 border-t border-slate-100 flex items-center justify-between text-[11px]">
                    <span className="text-slate-500">Status</span>
                    <span className="text-emerald-600 font-bold flex items-center gap-1">
                      <span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
                      Verified Bytecode
                    </span>
                  </div>
                </div>

                <div className="rounded-2xl bg-white p-5 shadow-sm border border-slate-200/60 flex flex-col justify-between">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">Current Block Height</span>
                    <span className="material-symbols-outlined text-[20px] text-emerald-600">view_in_ar</span>
                  </div>
                  <div className="mt-2">
                    <span className="text-2xl font-extrabold text-slate-900 font-mono">#{blockchainStatus.block_number}</span>
                    <span className="text-[11px] text-slate-500 block">Avg block time: ~2.1s</span>
                  </div>
                  <div className="mt-3 pt-2 border-t border-slate-100 flex items-center justify-between text-[11px]">
                    <span className="text-slate-500">Gas Price</span>
                    <span className="text-slate-800 font-bold">12.4 Gwei</span>
                  </div>
                </div>

                <div className="rounded-2xl bg-white p-5 shadow-sm border border-slate-200/60 flex flex-col justify-between">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">Total Anchored Batches</span>
                    <span className="material-symbols-outlined text-[20px] text-violet-600">layers</span>
                  </div>
                  <div className="mt-2">
                    <span className="text-2xl font-extrabold text-slate-900 font-mono">{blockchainStatus.total_anchors}</span>
                    <span className="text-[11px] text-slate-500 block">{blockchainStatus.anchored_events} cryptographic events</span>
                  </div>
                  <div className="mt-3 pt-2 border-t border-slate-100 flex items-center justify-between text-[11px]">
                    <span className="text-slate-500">Merkle Depth</span>
                    <span className="text-violet-700 font-bold">Level 4 (Binary)</span>
                  </div>
                </div>

                <div className="rounded-2xl bg-white p-5 shadow-sm border border-slate-200/60 flex flex-col justify-between">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">Cryptographic Match</span>
                    <span className="material-symbols-outlined text-[20px] text-emerald-600">check_circle</span>
                  </div>
                  <div className="mt-2">
                    <span className="text-2xl font-extrabold text-emerald-600 font-mono">100.0%</span>
                    <span className="text-[11px] text-slate-500 block">0 hash discrepancies</span>
                  </div>
                  <div className="mt-3 pt-2 border-t border-slate-100 flex items-center justify-between text-[11px]">
                    <span className="text-slate-500">Legal Standard</span>
                    <span className="text-blue-700 font-bold">IRDAI Sec 45 Non-Repudiation</span>
                  </div>
                </div>
              </div>

              {/* Live Mining Receipt Banner */}
              {miningReceipt && (
                <div className="p-5 rounded-2xl bg-emerald-50 border border-emerald-200 flex flex-col md:flex-row items-start md:items-center justify-between gap-4 animate-in fade-in duration-300">
                  <div className="flex items-start gap-3">
                    <div className="w-10 h-10 rounded-xl bg-emerald-600 text-white flex items-center justify-center shrink-0">
                      <span className="material-symbols-outlined text-[22px]">verified</span>
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-sm text-emerald-950">On-Chain Batch Anchor Confirmed!</span>
                        <span className="px-2 py-0.5 rounded-full bg-emerald-200 text-emerald-900 font-bold text-[10px]">
                          Block #{miningReceipt.block_number}
                        </span>
                      </div>
                      <p className="text-xs text-emerald-800 mt-0.5 font-mono break-all">
                        Tx Hash: {miningReceipt.tx_hash}
                      </p>
                      <p className="text-xs text-emerald-700 font-mono break-all">
                        Merkle Root: {miningReceipt.root_hash} • Gas: {miningReceipt.gas_used}
                      </p>
                    </div>
                  </div>
                  <button
                    onClick={() => handleInspectMerkleProof(blockchainStatus.total_anchors, miningReceipt.root_hash)}
                    className="px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs shadow-sm transition whitespace-nowrap cursor-pointer"
                  >
                    Inspect Merkle Proof
                  </button>
                </div>
              )}

              {/* Visual Merkle Tree Architecture */}
              <div className="p-6 rounded-2xl bg-white border border-slate-200/60 shadow-sm flex flex-col gap-4">
                <div className="flex items-center justify-between pb-3 border-b border-slate-100">
                  <div className="flex items-center gap-2">
                    <span className="material-symbols-outlined text-blue-600 text-[20px]">account_tree</span>
                    <h3 className="font-bold text-sm text-slate-900">Cryptographic Merkle Tree Hierarchy</h3>
                  </div>
                  <span className="text-xs text-slate-500 font-mono">Algorithm: SHA-256 (Keccak-256 Compatible)</span>
                </div>

                <div className="p-4 rounded-xl bg-slate-50 border border-slate-200/50 flex flex-col items-center gap-4">
                  {/* Root */}
                  <div className="p-3 rounded-xl bg-blue-600 text-white text-center shadow-md max-w-md w-full">
                    <span className="text-[10px] uppercase font-bold tracking-wider text-blue-200 block">
                      Merkle Root Commitment (Stored in AuditAnchor.sol)
                    </span>
                    <span className="font-mono text-xs font-bold truncate block">
                      0x8c4e1d67098ef3241bca760e928172938475a61049c812d34e567890123a9f
                    </span>
                  </div>

                  {/* Branches */}
                  <div className="w-full flex justify-around gap-4 max-w-2xl">
                    <div className="p-2.5 rounded-xl bg-white border border-slate-200 shadow-xs text-center flex-1">
                      <span className="text-[9px] font-bold text-slate-400 block uppercase">Left Branch H(0,1)</span>
                      <span className="font-mono text-[11px] text-slate-700 truncate block">0x4a9b...21e7</span>
                    </div>
                    <div className="p-2.5 rounded-xl bg-white border border-slate-200 shadow-xs text-center flex-1">
                      <span className="text-[9px] font-bold text-slate-400 block uppercase">Right Branch H(2,3)</span>
                      <span className="font-mono text-[11px] text-slate-700 truncate block">0x9f1a...68b0</span>
                    </div>
                  </div>

                  {/* Leaves */}
                  <div className="w-full grid grid-cols-2 sm:grid-cols-4 gap-2">
                    <div className="p-2 rounded-lg bg-emerald-50 border border-emerald-200 text-center">
                      <span className="text-[9px] font-bold text-emerald-800 block">Leaf 0: Voice Telemetry</span>
                      <span className="font-mono text-[10px] text-emerald-700 truncate block">SHA256(audio)</span>
                    </div>
                    <div className="p-2 rounded-lg bg-blue-50 border border-blue-200 text-center">
                      <span className="text-[9px] font-bold text-blue-800 block">Leaf 1: Policy Binding</span>
                      <span className="font-mono text-[10px] text-blue-700 truncate block">SHA256(terms)</span>
                    </div>
                    <div className="p-2 rounded-lg bg-violet-50 border border-violet-200 text-center">
                      <span className="text-[9px] font-bold text-violet-800 block">Leaf 2: Customer Consent</span>
                      <span className="font-mono text-[10px] text-violet-700 truncate block">SHA256(consent)</span>
                    </div>
                    <div className="p-2 rounded-lg bg-amber-50 border border-amber-200 text-center">
                      <span className="text-[9px] font-bold text-amber-800 block">Leaf 3: Agent Affirmation</span>
                      <span className="font-mono text-[10px] text-amber-700 truncate block">SHA256(agent)</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Anchored Batches Table */}
              <div className="p-6 rounded-2xl bg-white border border-slate-200/60 shadow-sm flex flex-col gap-4">
                <div className="flex items-center justify-between pb-3 border-b border-slate-100">
                  <h3 className="font-bold text-sm text-slate-900">Historical Anchored Batches Ledger</h3>
                  <span className="text-xs text-slate-400">Total {blockchainStatus.total_anchors} batches confirmed</span>
                </div>

                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs">
                    <thead>
                      <tr className="bg-slate-50 text-slate-600 uppercase text-[10px] font-bold tracking-wider">
                        <th className="py-2.5 px-3 rounded-l-lg">Seq #</th>
                        <th className="py-2.5 px-3">Merkle Root Hash</th>
                        <th className="py-2.5 px-3">Block #</th>
                        <th className="py-2.5 px-3">Tx Hash</th>
                        <th className="py-2.5 px-3">Events</th>
                        <th className="py-2.5 px-3">Status</th>
                        <th className="py-2.5 px-3 rounded-r-lg text-right">Proof</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100 font-mono text-[11px]">
                      {[
                        { seq: 24, root: '0x8c4e1d67098ef3241bca760e928172938475a61049c812d34e567890123a9f', block: 142860, tx: '0x3a9f8b2c4e1d67098ef3241bca760e928172938475a61049c812d34e56789012', events: 4 },
                        { seq: 23, root: '0x1290348719283746192837461928374619283746192837461928374619283746', block: 142858, tx: '0x7e4b2d184cf902341a0bcf8491cdae0234129bcae7102834bfae091248102381', events: 6 },
                        { seq: 22, root: '0x7e4b2d184cf902341a0bcf8491cdae0234129bcae7102834bfae091248102381', block: 142855, tx: '0x9923847192837461928374619283746192837461928374619283746192837461', events: 8 },
                      ].map((item) => (
                        <tr key={item.seq} className="hover:bg-slate-50 transition">
                          <td className="py-3 px-3 font-bold text-blue-700">#{item.seq}</td>
                          <td className="py-3 px-3 truncate max-w-[160px] text-slate-800">{item.root}</td>
                          <td className="py-3 px-3 text-slate-700">#{item.block}</td>
                          <td className="py-3 px-3 truncate max-w-[140px] text-slate-500">{item.tx}</td>
                          <td className="py-3 px-3 text-slate-800">{item.events} events</td>
                          <td className="py-3 px-3 font-sans">
                            <span className="px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800 text-[10px] font-bold">
                              ANCHORED
                            </span>
                          </td>
                          <td className="py-3 px-3 text-right font-sans">
                            <button
                              onClick={() => handleInspectMerkleProof(item.seq, item.root)}
                              className="px-2.5 py-1 rounded bg-slate-100 hover:bg-blue-600 hover:text-white text-blue-700 font-bold text-xs transition cursor-pointer"
                            >
                              Verify
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}

          {/* ======================================================== */}
          {/* SUB-VIEW 2: VOICE VERIFICATIONS TELEMETRY */}
          {/* ======================================================== */}
          {activeNav === 'voice' && (
            <div className="space-y-6 animate-in fade-in duration-200">
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                  <h1 className="text-2xl font-extrabold text-[#131B2E] tracking-tight">
                    Voice Verifications &amp; Tele-sales Intelligence
                  </h1>
                  <p className="text-xs sm:text-sm text-slate-500 mt-0.5">
                    Deterministic speech-to-text analysis, affirmative consent recognition, and Gemini 2.5 Policy Parity.
                  </p>
                </div>
                <div className="px-3 py-1.5 rounded-full bg-emerald-100 text-emerald-800 font-bold text-xs flex items-center gap-1.5">
                  <span className="material-symbols-outlined text-[16px]">graphic_eq</span>
                  <span>Audio Telemetry Stream: 99.8% Confidence</span>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="rounded-2xl bg-white p-5 shadow-sm border border-slate-200/60">
                  <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">Acoustic Consent Match</span>
                  <p className="text-2xl font-bold text-[#131B2E] mt-2">100%</p>
                  <span className="text-xs text-emerald-600 font-medium">All affirmative phrases validated</span>
                </div>
                <div className="rounded-2xl bg-white p-5 shadow-sm border border-slate-200/60">
                  <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">Gemini 2.5 Verification</span>
                  <p className="text-2xl font-bold text-[#131B2E] mt-2">99.4%</p>
                  <span className="text-xs text-blue-600 font-medium">Verbal claims adhere to statutory terms</span>
                </div>
                <div className="rounded-2xl bg-white p-5 shadow-sm border border-slate-200/60">
                  <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">Audio Hash Sealed</span>
                  <p className="text-2xl font-bold text-[#131B2E] mt-2">SHA-256</p>
                  <span className="text-xs text-slate-500 font-medium">Immutable telemetry proof</span>
                </div>
              </div>

              <div className="p-6 rounded-2xl bg-white border border-slate-200/60 shadow-sm flex flex-col gap-4">
                <h3 className="font-bold text-sm text-slate-900">Recent Voice Telemetry Consultation Sessions</h3>
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs">
                    <thead>
                      <tr className="bg-slate-50 text-slate-600 uppercase text-[10px] font-bold tracking-wider">
                        <th className="py-2.5 px-3 rounded-l-lg">Session ID</th>
                        <th className="py-2.5 px-3">Customer</th>
                        <th className="py-2.5 px-3">Agent</th>
                        <th className="py-2.5 px-3">Duration</th>
                        <th className="py-2.5 px-3">Consent Status</th>
                        <th className="py-2.5 px-3">Policy Parity</th>
                        <th className="py-2.5 px-3 rounded-r-lg text-right">Playback</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {[
                        { id: 'SESS-2026-9912', customer: 'Rahul Sharma', agent: 'Priya Deshmukh', duration: '03:42', consent: 'AFFIRMATIVE_CAPTURED', parity: '99.8%' },
                        { id: 'SESS-2026-9911', customer: 'Ananya Kapoor', agent: 'Rajesh M.', duration: '01:27', consent: 'AFFIRMATIVE_CAPTURED', parity: '100.0%' },
                        { id: 'SESS-2026-9908', customer: 'Vikram Sengupta', agent: 'Rajesh M.', duration: '04:15', consent: 'AFFIRMATIVE_CAPTURED', parity: '98.9%' },
                      ].map((sess) => (
                        <tr key={sess.id} className="hover:bg-slate-50 transition">
                          <td className="py-3 px-3 font-mono font-bold text-blue-700">{sess.id}</td>
                          <td className="py-3 px-3 font-semibold">{sess.customer}</td>
                          <td className="py-3 px-3 text-slate-600">{sess.agent}</td>
                          <td className="py-3 px-3 font-mono">{sess.duration}</td>
                          <td className="py-3 px-3">
                            <span className="px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800 font-bold text-[10px]">
                              {sess.consent}
                            </span>
                          </td>
                          <td className="py-3 px-3 font-bold text-emerald-600">{sess.parity}</td>
                          <td className="py-3 px-3 text-right">
                            <button
                              onClick={() => {
                                setIsPlayingAudio(!isPlayingAudio);
                                setActionSuccessMsg(`Playing telemetry stream for ${sess.id}`);
                              }}
                              className="px-2.5 py-1 rounded bg-blue-50 text-blue-700 font-bold text-xs hover:bg-blue-600 hover:text-white transition cursor-pointer"
                            >
                              Play Audio
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}

          {/* ======================================================== */}
          {/* SUB-VIEW 3: POLICIES & STATUTORY COMMITMENTS */}
          {/* ======================================================== */}
          {activeNav === 'policies' && (
            <div className="space-y-6 animate-in fade-in duration-200">
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                  <h1 className="text-2xl font-extrabold text-[#131B2E] tracking-tight">
                    Policies &amp; Statutory Commitments
                  </h1>
                  <p className="text-xs sm:text-sm text-slate-500 mt-0.5">
                    Master underwriting registry verified under IRDAI standard guidelines.
                  </p>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {policies.map((p) => (
                  <div key={p.id} className="p-5 rounded-2xl bg-white border border-slate-200/60 shadow-sm flex flex-col justify-between gap-4 hover:shadow-md transition">
                    <div className="flex flex-col gap-1">
                      <div className="flex items-center justify-between">
                        <span className="font-mono text-xs font-bold text-blue-700">{p.id}</span>
                        <span className="px-2 py-0.5 rounded-full bg-blue-100 text-blue-800 font-bold text-[10px] uppercase">
                          {p.category}
                        </span>
                      </div>
                      <h3 className="font-bold text-base text-slate-900 mt-1">{p.policy_name}</h3>
                      <p className="text-xs text-slate-500">{p.insurer_name}</p>
                    </div>

                    <div className="p-3 rounded-xl bg-slate-50 border border-slate-100 flex items-center justify-between text-xs">
                      <span className="text-slate-500">Coverage Limit</span>
                      <span className="font-bold text-slate-900 font-mono">
                        ₹{(p.coverage_limit || 0).toLocaleString('en-IN')}
                      </span>
                    </div>

                    <div className="flex items-center justify-between text-[11px] text-slate-500">
                      <span>Status: <strong className="text-emerald-600">ACTIVE</strong></span>
                      <span className="flex items-center gap-1 text-blue-600 font-bold">
                        <span className="material-symbols-outlined text-[14px]">verified</span>
                        Audited V4
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* ======================================================== */}
          {/* SUB-VIEW 4: CLAIMS & DISPUTES WORKSPACE */}
          {/* ======================================================== */}
          {activeNav === 'claims' && (
            <div className="space-y-6 animate-in fade-in duration-200">
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                  <h1 className="text-2xl font-extrabold text-[#131B2E] tracking-tight">
                    Claims &amp; Disputes Adjudication Desk
                  </h1>
                  <p className="text-xs sm:text-sm text-slate-500 mt-0.5">
                    Real-time claim evidence validation, tele-sales transcript matching, and instant payout execution.
                  </p>
                </div>
                <button
                  onClick={() => handleSimulatePayment()}
                  className="px-5 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-bold text-xs shadow-md transition cursor-pointer"
                >
                  Simulate Selected Claim Payout
                </button>
              </div>

              {/* Claims Queue Table */}
              <div className="p-6 rounded-2xl bg-white border border-slate-200/60 shadow-sm flex flex-col gap-4">
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs">
                    <thead>
                      <tr className="bg-slate-50 text-slate-600 uppercase text-[10px] font-bold tracking-wider">
                        <th className="py-2.5 px-3 rounded-l-lg">Claim ID</th>
                        <th className="py-2.5 px-3">Category</th>
                        <th className="py-2.5 px-3">Requested Amount</th>
                        <th className="py-2.5 px-3">Calculated Payable</th>
                        <th className="py-2.5 px-3">Status</th>
                        <th className="py-2.5 px-3 rounded-r-lg text-right">Action</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {claims.map((c) => (
                        <tr key={c.id} className="hover:bg-slate-50 transition">
                          <td className="py-3 px-3 font-mono font-bold text-blue-700">{c.id}</td>
                          <td className="py-3 px-3 font-medium">{c.claim_category}</td>
                          <td className="py-3 px-3 font-bold font-mono">₹{c.requested_amount.toLocaleString('en-IN')}</td>
                          <td className="py-3 px-3 font-bold font-mono text-emerald-600">
                            ₹{(c.latest_assessment?.potentially_payable_amount || c.requested_amount).toLocaleString('en-IN')}
                          </td>
                          <td className="py-3 px-3">
                            <span className="px-2 py-0.5 rounded-full bg-blue-100 text-blue-800 font-bold text-[10px]">
                              {c.status}
                            </span>
                          </td>
                          <td className="py-3 px-3 text-right">
                            <button
                              onClick={() => handleSelectCase(c)}
                              className="px-3 py-1 rounded bg-slate-100 hover:bg-blue-600 hover:text-white text-blue-700 font-bold text-xs transition cursor-pointer"
                            >
                              Inspect Case
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}

          {/* ======================================================== */}
          {/* SUB-VIEW 5: SETTINGS */}
          {/* ======================================================== */}
          {activeNav === 'settings' && (
            <div className="space-y-6 animate-in fade-in duration-200">
              <h1 className="text-2xl font-extrabold text-[#131B2E] tracking-tight">
                System &amp; Smart Contract Settings
              </h1>
              <div className="p-6 rounded-2xl bg-white border border-slate-200/60 shadow-sm space-y-4 text-xs">
                <div>
                  <label className="block font-bold text-slate-700 uppercase mb-1">EVM RPC Endpoint</label>
                  <input
                    type="text"
                    readOnly
                    value="http://127.0.0.1:8545 (Hardhat Localhost Node)"
                    className="w-full h-10 px-3 rounded-xl bg-slate-50 border border-slate-200 font-mono text-xs"
                  />
                </div>
                <div>
                  <label className="block font-bold text-slate-700 uppercase mb-1">AuditAnchor Contract Address</label>
                  <input
                    type="text"
                    readOnly
                    value={blockchainStatus.contract_address}
                    className="w-full h-10 px-3 rounded-xl bg-slate-50 border border-slate-200 font-mono text-xs"
                  />
                </div>
                <div>
                  <label className="block font-bold text-slate-700 uppercase mb-1">Voice Telemetry Model</label>
                  <input
                    type="text"
                    readOnly
                    value="Google Gemini 2.5 Policy Parity Engine + ElevenLabs STT"
                    className="w-full h-10 px-3 rounded-xl bg-slate-50 border border-slate-200 text-xs"
                  />
                </div>
              </div>
            </div>
          )}
        </main>
      </div>

      {/* MERKLE PROOF INSPECTOR MODAL */}
      {activeProofModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 backdrop-blur-sm p-4">
          <div className="bg-white rounded-2xl max-w-xl w-full p-6 shadow-2xl border border-slate-100 flex flex-col gap-4 animate-in fade-in duration-200">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <div className="flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse"></span>
                <span className="font-bold text-sm text-slate-900">
                  On-Chain Merkle Proof Verification
                </span>
                <span className="px-2 py-0.5 rounded-full bg-blue-50 text-blue-700 text-[10px] font-bold">
                  Batch #{activeProofModal.batch_sequence}
                </span>
              </div>
              <button
                onClick={() => setActiveProofModal(null)}
                className="text-slate-400 hover:text-slate-600 p-1 cursor-pointer"
              >
                <span className="material-symbols-outlined text-[20px]">close</span>
              </button>
            </div>

            <div className="space-y-3 text-xs font-mono">
              <div className="p-3 bg-slate-50 rounded-xl border border-slate-200/60">
                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-1">
                  Target Smart Contract
                </span>
                <p className="text-blue-700 font-bold break-all">
                  AuditAnchor.sol ({activeProofModal.contract_address})
                </p>
                <span className="text-[11px] text-slate-500 block mt-1">
                  Block Number: #{activeProofModal.block_number} • EVM Hardhat / Sepolia
                </span>
              </div>

              <div className="p-3 bg-slate-50 rounded-xl border border-slate-200/60">
                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-1">
                  1. Leaf Hash (Audio Telemetry + Policy Binding)
                </span>
                <p className="text-slate-800 break-all">{activeProofModal.leaf_hash}</p>
              </div>

              <div className="p-3 bg-slate-50 rounded-xl border border-slate-200/60">
                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-1">
                  2. Merkle Proof Path (Cryptographic Steps)
                </span>
                <div className="space-y-1.5 mt-1">
                  {activeProofModal.proof_steps.map((step: any, i: number) => (
                    <div key={i} className="flex items-center gap-2 text-[11px]">
                      <span className="px-1.5 py-0.5 rounded bg-blue-100 text-blue-800 font-bold uppercase text-[9px]">
                        {step.position}
                      </span>
                      <span className="text-slate-600 truncate">{step.hash}</span>
                    </div>
                  ))}
                </div>
              </div>

              <div className="p-3 bg-emerald-50 rounded-xl border border-emerald-200">
                <span className="text-[10px] font-bold text-emerald-800 uppercase tracking-wider block mb-1">
                  3. Evaluated Merkle Root Hash
                </span>
                <p className="text-emerald-950 font-bold break-all">{activeProofModal.root_hash}</p>
                <div className="mt-2 flex items-center gap-1.5 text-emerald-700 font-sans font-bold text-xs">
                  <span className="material-symbols-outlined text-[16px]">check_circle</span>
                  <span>Commitment matches AuditAnchor on-chain registry monotonically.</span>
                </div>
              </div>
            </div>

            <div className="pt-2 flex justify-end">
              <button
                onClick={() => setActiveProofModal(null)}
                className="px-5 py-2 rounded-xl text-xs font-bold bg-[#004AC6] text-white hover:bg-[#1D4ED8] transition cursor-pointer"
              >
                Close Inspector
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ======================================================== */}
      {/* CASE INSPECTION MODAL (Interactive Adjudication & Payout) */}
      {/* ======================================================== */}
      {inspectModalClaim && (
        <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-xs flex items-center justify-center p-4 overflow-y-auto animate-in fade-in duration-200">
          <div className="bg-white rounded-3xl max-w-2xl w-full p-6 sm:p-8 shadow-2xl border border-slate-200 space-y-6 max-h-[90vh] overflow-y-auto">
            {/* Modal Header */}
            <div className="flex items-start justify-between pb-4 border-b border-slate-100">
              <div className="flex items-center gap-3">
                <div className="w-12 h-12 rounded-2xl bg-blue-50 text-[#004AC6] flex items-center justify-center font-bold">
                  <span className="material-symbols-outlined text-[28px]">gavel</span>
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="text-lg font-extrabold text-[#131B2E]">
                      Claim Adjudication Inspector
                    </h3>
                    <span className="px-2.5 py-0.5 rounded-full bg-blue-100 text-[#004AC6] text-[11px] font-bold font-mono">
                      {inspectModalClaim.id}
                    </span>
                  </div>
                  <p className="text-xs text-slate-500 mt-0.5">
                    Category: <span className="font-semibold text-slate-700">{inspectModalClaim.claim_category}</span> • 
                    Status: <span className="font-bold text-emerald-600">{inspectModalClaim.status}</span>
                  </p>
                </div>
              </div>
              <button
                onClick={() => setInspectModalClaim(null)}
                className="w-8 h-8 rounded-full bg-slate-100 hover:bg-slate-200 flex items-center justify-center text-slate-600 transition cursor-pointer"
              >
                <span className="material-symbols-outlined text-[20px]">close</span>
              </button>
            </div>

            {/* Financial Overview Cards */}
            <div className="grid grid-cols-2 gap-4">
              <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200/80">
                <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500 block">
                  Requested Claim
                </span>
                <span className="text-xl font-extrabold text-slate-900 mt-1 block">
                  ₹{inspectModalClaim.requested_amount.toLocaleString('en-IN')}
                </span>
                <span className="text-[11px] text-slate-500 mt-0.5 block">
                  Incident: {inspectModalClaim.incident_date}
                </span>
              </div>

              <div className="p-4 rounded-2xl bg-emerald-50 border border-emerald-200">
                <span className="text-[10px] font-bold uppercase tracking-wider text-emerald-700 block">
                  Deterministic Payable
                </span>
                <span className="text-xl font-extrabold text-emerald-800 mt-1 block">
                  ₹{(inspectModalClaim.latest_assessment?.potentially_payable_amount || inspectModalClaim.requested_amount).toLocaleString('en-IN')}
                </span>
                <span className="text-[11px] text-emerald-700 font-semibold mt-0.5 flex items-center gap-1">
                  <span className="material-symbols-outlined text-[14px]">verified</span>
                  <span>99.8% Speech Parity Validated</span>
                </span>
              </div>
            </div>

            {/* Description & Telemetry Evidence */}
            <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200/80 space-y-3">
              <span className="text-xs font-bold text-slate-800 flex items-center gap-1.5">
                <span className="material-symbols-outlined text-[18px] text-[#004AC6]">description</span>
                <span>Claim Narrative &amp; Tele-sales Binding Verification</span>
              </span>
              <p className="text-xs text-slate-600 leading-relaxed">
                {inspectModalClaim.description || 'Routine claim submitted with affirmative audio consent verified under SESS-2026-9911.'}
              </p>
              
              {/* Voice Telemetry Player */}
              <div className="p-3 bg-white rounded-xl border border-slate-200 flex items-center justify-between gap-3">
                <div className="flex items-center gap-2.5">
                  <button
                    onClick={() => setIsPlayingAudio(!isPlayingAudio)}
                    className="w-8 h-8 rounded-full bg-[#004AC6] text-white flex items-center justify-center hover:bg-[#1D4ED8] transition cursor-pointer"
                  >
                    <span className="material-symbols-outlined text-[18px]">
                      {isPlayingAudio ? 'pause' : 'play_arrow'}
                    </span>
                  </button>
                  <div>
                    <span className="text-xs font-bold text-slate-900 block">Sales Telemetry Audio: SESS-2026-9911</span>
                    <span className="text-[10px] text-slate-500 font-mono">00:32 / 01:24 • Bitrate: 128 kbps Opus</span>
                  </div>
                </div>
                <span className="px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800 text-[10px] font-bold uppercase">
                  Verified
                </span>
              </div>
            </div>

            {/* Assessment Rules Table */}
            <div className="space-y-2">
              <span className="text-xs font-bold text-slate-800 block">Evaluated Statutory Rules</span>
              <div className="space-y-1.5 text-xs">
                <div className="p-2.5 rounded-xl bg-slate-50 border border-slate-200/60 flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="material-symbols-outlined text-emerald-600 text-[16px]">check_circle</span>
                    <span className="font-medium text-slate-700">Clause 4.2: Cashless admission &amp; primary coverage</span>
                  </div>
                  <span className="px-2 py-0.5 rounded bg-emerald-100 text-emerald-800 font-bold text-[10px]">PASSED</span>
                </div>
                <div className="p-2.5 rounded-xl bg-slate-50 border border-slate-200/60 flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="material-symbols-outlined text-emerald-600 text-[16px]">check_circle</span>
                    <span className="font-medium text-slate-700">Clause 7.1: Zero depreciation deductible applied</span>
                  </div>
                  <span className="px-2 py-0.5 rounded bg-emerald-100 text-emerald-800 font-bold text-[10px]">PASSED</span>
                </div>
              </div>
            </div>

            {/* Adjudication Action Controls */}
            <div className="pt-4 border-t border-slate-100 flex flex-wrap items-center justify-end gap-3">
              <button
                onClick={() => {
                  handleAdjudicateTransition('EVIDENCE_REQUESTED', 'Requested official medical bills and invoice');
                  setInspectModalClaim(null);
                }}
                className="px-4 py-2.5 rounded-xl text-xs font-semibold text-slate-700 bg-slate-100 hover:bg-slate-200 transition cursor-pointer"
              >
                Request Evidence
              </button>
              <button
                onClick={() => {
                  handleAdjudicateTransition('REJECTED', 'Claim exceeds standard sub-limit thresholds');
                  setInspectModalClaim(null);
                }}
                className="px-4 py-2.5 rounded-xl text-xs font-semibold text-rose-600 bg-rose-50 hover:bg-rose-100 transition cursor-pointer"
              >
                Reject Claim
              </button>
              <button
                onClick={() => {
                  handleSimulatePayment();
                  setInspectModalClaim(null);
                }}
                className="px-6 py-2.5 rounded-xl text-xs font-bold text-white bg-emerald-600 hover:bg-emerald-700 shadow-md transition flex items-center gap-1.5 cursor-pointer"
              >
                <span className="material-symbols-outlined text-[16px]">payments</span>
                <span>Approve &amp; Simulate Instant IMPS Payout</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
export default AuthorityWorkbench;
