import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../services/api';
import { MOCK_POLICIES, MOCK_REGISTRATIONS } from '../data/mockData';
import { Registration, Policy } from '../types';
import { useAuth } from '../context/AuthContext';

export const AgentDashboard: React.FC = () => {
  const { user } = useAuth();
  const [registrations, setRegistrations] = useState<Registration[]>(MOCK_REGISTRATIONS);
  const [policies, setPolicies] = useState<Policy[]>(MOCK_POLICIES);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [isSyncing, setIsSyncing] = useState(false);
  const [syncMessage, setSyncMessage] = useState<string | null>(null);

  // Modals state
  const [showEnrollModal, setShowEnrollModal] = useState(false);
  const [selectedSchemeForEnroll, setSelectedSchemeForEnroll] = useState<string>('pol-001');
  const [customerName, setCustomerName] = useState('');
  const [customerEmail, setCustomerEmail] = useState('');
  const [customerPhone, setCustomerPhone] = useState('');
  const [customerConsent, setCustomerConsent] = useState(true);
  const [consentNotes, setConsentNotes] = useState('Oral affirmative consent recorded under voice telemetry.');
  const [isSubmittingEnrollment, setIsSubmittingEnrollment] = useState(false);

  // Detail Modal
  const [activeDetailReg, setActiveDetailReg] = useState<Registration | null>(null);
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [activeAgentNav, setActiveAgentNav] = useState<'overview' | 'schemes' | 'registrations' | 'telemetry'>('overview');

  // Telemetry AI & Gemini 2.5 State
  const [salesTranscript, setSalesTranscript] = useState(`[Agent Rajesh]: Namaste Vikram ji, Care Premier Health Shield me inpatient room rent aur ICU charges cashless network par Rs 15,00,000 tak puri tarah covered hain. Sath hi 60 days pre-hospitalization aur 90 days post-hospitalization bills bhi milenge.
[Customer Vikram]: Sahi hai. Aur mujhe diabetes aur BP ki problem hai, uska kya hoga?
[Agent Rajesh]: Vikram ji don't worry, aapka diabetes aur BP is policy me completely covered hai, uski saari dawaiyan aur hospitalization admissible hongi.
[Customer Vikram]: Aur cosmetic skin laser treatment ya normal doctor OPD checkups?
[Agent Rajesh]: Haan bilkul, aap koi bhi cosmetic laser treatment karwayein ya normal OPD me clinic jakar checkup karwayein, bina hospital me admit huye bhi hum 100% reimburse kar denge.
[Customer Vikram]: Theek hai Rajesh ji, main is policy ke liye apni verbal consent deta hoon.
[Agent Rajesh]: Dhanyawad Vikram ji, aapka consent record ho gaya hai. Emergency road ambulance bhi Rs 3,000 tak covered rahegi.`);

  const [audioFileName, setAudioFileName] = useState<string | null>('sales_call_vikram_care_shield.mp3');
  const [isAuditing, setIsAuditing] = useState(false);
  const [auditResult, setAuditResult] = useState<any | null>(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setIsSyncing(true);
    try {
      const [fetchedRegs, fetchedPolicies] = await Promise.all([
        api.getRegistrations(),
        api.getPolicies(),
      ]);
      if (fetchedRegs) setRegistrations(fetchedRegs);
      if (fetchedPolicies && fetchedPolicies.length > 0) {
        setPolicies(fetchedPolicies);
        setSelectedSchemeForEnroll(fetchedPolicies[0].id);
      }
      setSyncMessage('Vault synchronized with Neon PostgreSQL.');
      setTimeout(() => setSyncMessage(null), 3000);
    } catch (e) {
      console.warn('Using offline data fallback', e);
    } finally {
      setIsSyncing(false);
    }
  };

  const handleCopy = (text: string) => {
    navigator.clipboard?.writeText(text);
    setCopiedId(text);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const handleCreateEnrollment = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!customerEmail || !customerName) return;

    setIsSubmittingEnrollment(true);
    try {
      await api.createRegistration({
        customer_email: customerEmail,
        customer_full_name: customerName,
        customer_phone: customerPhone || '+91 98000 00000',
        policy_id: selectedSchemeForEnroll,
        customer_consent: customerConsent,
        consent_notes: consentNotes,
      });

      await loadData();
      setShowEnrollModal(false);
      setCustomerName('');
      setCustomerEmail('');
      setCustomerPhone('');
      setSyncMessage(`Customer created on Neon DB & credentials dispatched to ${customerEmail}`);
      setTimeout(() => setSyncMessage(null), 4000);
    } catch (err: any) {
      const msg = err?.response?.data?.detail || err?.response?.data?.message || err?.message || 'Enrollment failed';
      alert(typeof msg === 'string' ? msg : JSON.stringify(msg));
    } finally {
      setIsSubmittingEnrollment(false);
    }
  };

  const handleRunGeminiAudit = async () => {
    setIsAuditing(true);
    try {
      const res = await api.auditTranscriptDirect(salesTranscript, selectedSchemeForEnroll);
      setAuditResult(res);
      setSyncMessage('Gemini 2.5 Policy Parity Evaluation Completed!');
      setTimeout(() => setSyncMessage(null), 4000);
    } catch (e: any) {
      alert('Audit failed: ' + e.message);
    } finally {
      setIsAuditing(false);
    }
  };

  // Filtered registrations
  const filteredRegistrations = registrations.filter((reg) => {
    const q = searchQuery.toLowerCase().trim();
    const matchesQuery =
      q === '' ||
      reg.id.toLowerCase().includes(q) ||
      (reg.customer?.full_name && reg.customer.full_name.toLowerCase().includes(q)) ||
      (reg.customer?.phone && reg.customer.phone.toLowerCase().includes(q)) ||
      (reg.policy?.policy_name && reg.policy.policy_name.toLowerCase().includes(q));

    const matchesStatus =
      statusFilter === 'ALL' || reg.status.toLowerCase() === statusFilter.toLowerCase();

    return matchesQuery && matchesStatus;
  });

  // Metric counts
  const countAwaiting = registrations.filter(
    (r) => r.status === 'AWAITING_CUSTOMER_CONFIRMATION'
  ).length;
  const countConfirmed = registrations.filter((r) => r.status === 'CONFIRMED').length;
  const countPending = registrations.filter((r) => r.status === 'PENDING_REVIEW').length;
  const totalCount = registrations.length;

  return (
    <div className="bg-background font-body-md text-on-surface antialiased min-h-screen">
      {/* BEGIN: Left Fixed Sidebar (1:1 Stitch Agent Specification) */}
      <aside
        className={`fixed left-0 top-0 h-full w-72 bg-surface-container-low shadow-[0_1px_8px_rgba(0,0,0,0.04)] z-50 flex flex-col justify-between p-space-md transition-transform duration-300 ease-in-out ${
          sidebarOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        <div className="flex flex-col gap-space-md">
          {/* Logo Brand Header */}
          <div className="flex items-center">
            <Link to="/" className="flex items-center gap-space-sm px-space-xs py-space-xs group">
              <div className="w-10 h-10 rounded-xl bg-primary flex items-center justify-center text-on-primary shadow-[0_4px_14px_rgba(37,99,235,0.25)] group-hover:scale-105 transition-transform">
                <span className="material-symbols-outlined text-[24px]">graphic_eq</span>
              </div>
              <div className="flex flex-col">
                <div className="flex items-center gap-1.5">
                  <span className="font-headline-sm text-headline-sm font-bold tracking-tight text-on-surface">
                    VACHAN
                  </span>
                  <span className="font-label-sm text-label-sm bg-primary-fixed text-on-primary-fixed px-1.5 py-0.5 rounded font-bold">
                    PRO
                  </span>
                </div>
                <span className="font-label-sm text-label-sm text-primary font-medium tracking-wide">
                  VoiceGuard Intelligence
                </span>
              </div>
            </Link>
          </div>

          {/* Role Pill */}
          <div className="px-space-xs">
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-surface-container text-on-surface-variant">
              <span className="w-2 h-2 rounded-full bg-primary animate-pulse"></span>
              <span className="font-label-sm text-label-sm font-semibold tracking-wide uppercase">
                Agent Portal • Field Operations
              </span>
            </div>
          </div>

          {/* Module Links */}
          <div className="pt-space-xs">
            <span className="px-space-xs font-label-sm text-label-sm uppercase tracking-wider text-outline font-semibold">
              Core Modules
            </span>
          </div>

          <nav className="flex flex-col gap-1.5">
            <button
              onClick={() => {
                setActiveAgentNav('overview');
                setStatusFilter('ALL');
                setSearchQuery('');
              }}
              className={`w-full flex items-center gap-3 px-3.5 py-2.5 rounded-xl transition-all group text-left cursor-pointer ${
                activeAgentNav === 'overview'
                  ? 'bg-primary-container text-on-primary-container font-semibold shadow-[0_4px_14px_rgba(37,99,235,0.18)]'
                  : 'text-on-surface-variant hover:bg-surface-container-high hover:text-on-surface'
              }`}
            >
              <span className="material-symbols-outlined text-[20px] transition-transform group-hover:scale-105">
                dashboard
              </span>
              <span className="font-label-lg text-label-lg">Overview</span>
            </button>

            <button
              onClick={() => setActiveAgentNav('schemes')}
              className={`w-full flex items-center gap-3 px-3.5 py-2.5 rounded-xl transition-all group text-left cursor-pointer ${
                activeAgentNav === 'schemes'
                  ? 'bg-primary-container text-on-primary-container font-semibold shadow-[0_4px_14px_rgba(37,99,235,0.18)]'
                  : 'text-on-surface-variant hover:bg-surface-container-high hover:text-on-surface'
              }`}
            >
              <span className="material-symbols-outlined text-[20px] transition-transform group-hover:scale-105">
                verified_user
              </span>
              <span className="font-label-lg text-label-lg">Insurance Schemes</span>
            </button>

            <button
              onClick={() => setShowEnrollModal(true)}
              className="w-full flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-on-surface-variant hover:bg-surface-container-high hover:text-on-surface transition-all group text-left cursor-pointer"
            >
              <span className="material-symbols-outlined text-[20px] transition-transform group-hover:scale-105">
                add_circle
              </span>
              <span className="font-label-lg text-label-lg">New Enrollment</span>
            </button>

            <button
              onClick={() => setActiveAgentNav('registrations')}
              className={`w-full flex items-center gap-3 px-3.5 py-2.5 rounded-xl transition-all group text-left cursor-pointer ${
                activeAgentNav === 'registrations'
                  ? 'bg-primary-container text-on-primary-container font-semibold shadow-[0_4px_14px_rgba(37,99,235,0.18)]'
                  : 'text-on-surface-variant hover:bg-surface-container-high hover:text-on-surface'
              }`}
            >
              <span className="material-symbols-outlined text-[20px] transition-transform group-hover:scale-105">
                fact_check
              </span>
              <span className="font-label-lg text-label-lg">Registrations Queue</span>
            </button>

            <button
              onClick={() => setActiveAgentNav('telemetry')}
              className={`w-full flex items-center gap-3 px-3.5 py-2.5 rounded-xl transition-all group text-left cursor-pointer ${
                activeAgentNav === 'telemetry'
                  ? 'bg-primary-container text-on-primary-container font-semibold shadow-[0_4px_14px_rgba(37,99,235,0.18)]'
                  : 'text-on-surface-variant hover:bg-surface-container-high hover:text-on-surface'
              }`}
            >
              <span className="material-symbols-outlined text-[20px] transition-transform group-hover:scale-105">
                graphic_eq
              </span>
              <span className="font-label-lg text-label-lg">Voice Telemetry AI</span>
            </button>
          </nav>
        </div>

        {/* Sidebar Footer Widget */}
        <div className="flex flex-col gap-space-sm pt-space-md">
          <div className="p-3.5 rounded-xl bg-surface-container-lowest shadow-[0_2px_6px_-1px_rgba(15,23,42,0.03)] flex flex-col gap-2">
            <div className="flex items-center justify-between">
              <span className="font-label-sm text-label-sm text-outline uppercase tracking-wider font-semibold">
                Voice Biometric Engine
              </span>
              <span className="flex h-2 w-2 relative">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-primary"></span>
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="font-body-sm text-body-sm text-on-surface font-medium">
                Telemetry Stream
              </span>
              <span className="font-label-sm text-label-sm text-primary font-bold">
                99.8% Conf.
              </span>
            </div>
          </div>

          <div className="flex items-center justify-between px-space-xs text-outline font-label-sm text-label-sm">
            <span>v4.18.2 Secured</span>
            <span className="material-symbols-outlined text-[16px]">lock</span>
          </div>
        </div>
      </aside>
      {/* END: Sidebar */}

      {/* BEGIN: Main Content Area */}
      <div className={`transition-all duration-300 ease-in-out ${sidebarOpen ? 'pl-72' : 'pl-0'}`}>
        {/* Sticky Top Header */}
        <header
          className={`fixed top-0 right-0 h-16 bg-surface/85 backdrop-blur-xl shadow-[0_1px_8px_rgba(0,0,0,0.04)] z-40 px-space-lg flex items-center justify-between transition-all duration-300 ease-in-out ${
            sidebarOpen ? 'left-72' : 'left-0'
          }`}
        >
          <div className="flex items-center gap-space-md">
            {/* Three lines hamburger toggle button */}
            <button
              type="button"
              onClick={() => setSidebarOpen(!sidebarOpen)}
              title={sidebarOpen ? "Close sidebar" : "Open sidebar"}
              className="w-10 h-10 rounded-xl flex items-center justify-center text-on-surface hover:bg-surface-container transition-colors cursor-pointer shrink-0"
            >
              <span className="material-symbols-outlined text-[24px] transition-transform duration-200">
                {sidebarOpen ? 'close' : 'menu'}
              </span>
            </button>

            <div className="flex items-center gap-2">
              <span className="font-body-sm text-body-sm text-on-surface-variant">Agent Workspace</span>
              <span className="material-symbols-outlined text-[16px] text-outline">chevron_right</span>
              <span className="font-label-md text-label-md text-on-surface font-semibold capitalize">
                {activeAgentNav === 'overview'
                  ? 'Overview'
                  : activeAgentNav === 'schemes'
                  ? 'Insurance Schemes'
                  : activeAgentNav === 'registrations'
                  ? 'Registrations Queue'
                  : 'Voice Telemetry AI'}
              </span>
            </div>
            <div className="hidden xl:flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-surface-container text-on-surface-variant font-label-sm text-label-sm">
              <span className="w-1.5 h-1.5 rounded-full bg-secondary"></span>
              <span>Demo Sandbox • TLS 1.3</span>
            </div>
          </div>

          <div className="flex items-center gap-space-md">
            {/* Search Input */}
            <div className="relative flex items-center">
              <span className="material-symbols-outlined absolute left-3 text-[18px] text-outline">search</span>
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search registrations, schemes, or clients..."
                className="w-80 h-9 pl-9 pr-12 rounded-xl bg-surface-container-low text-on-surface font-body-sm text-body-sm placeholder:text-outline focus:outline-none focus:bg-surface-container-lowest transition-all"
              />
              <span className="absolute right-2.5 px-1.5 py-0.5 rounded bg-surface-container-highest text-on-surface-variant font-label-sm text-label-sm text-[10px]">
                ⌘K
              </span>
            </div>

            {/* Notification Bell */}
            <button className="relative p-2 rounded-xl text-on-surface-variant hover:bg-surface-container-high hover:text-on-surface transition-colors">
              <span className="material-symbols-outlined text-[20px]">notifications</span>
              <span className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-primary"></span>
            </button>

            <div className="h-6 w-px bg-outline-variant"></div>

            {/* User Pill */}
            <div className="flex items-center gap-3 pl-1">
              <div className="flex flex-col text-right">
                <div className="flex items-center justify-end gap-1.5">
                  <span className="font-label-md text-label-md text-on-surface font-semibold">
                    {user?.full_name || 'Rajesh M.'}
                  </span>
                  <span className="w-2 h-2 rounded-full bg-primary"></span>
                </div>
                <span className="font-label-sm text-label-sm text-on-surface-variant truncate max-w-[160px]">
                  {user?.email || 'Senior Advisory Agent'}
                </span>
              </div>
              <div className="w-8 h-8 rounded-full bg-primary flex items-center justify-center">
                <span className="material-symbols-outlined text-on-primary text-[18px]">person</span>
              </div>
            </div>
          </div>
        </header>

        {/* Main Body */}
        <main className="relative pt-24 pb-20 w-full min-h-screen bg-background">
          <div className="max-w-7xl mx-auto px-6 sm:px-10 lg:px-12 py-4 flex flex-col w-full gap-y-8">
            {/* Sync Feedback Toast */}
            {syncMessage && (
              <div className="p-3 bg-emerald-50 border border-emerald-200 text-emerald-800 rounded-xl text-sm flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="material-symbols-outlined text-emerald-600 text-[18px]">check_circle</span>
                  <span>{syncMessage}</span>
                </div>
                <button onClick={() => setSyncMessage(null)} className="text-emerald-600 font-bold text-xs">
                  DISMISS
                </button>
              </div>
            )}

            {activeAgentNav === 'overview' && (
              <>
                {/* 1. Page Header */}
            <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4 pb-2">
              <div className="flex flex-col gap-1">
                <div className="flex items-center gap-2">
                  <h1 className="font-headline-lg text-headline-lg text-on-surface tracking-tight font-bold">
                    Agent Workspace
                  </h1>
                  <span className="px-2 py-0.5 rounded-full bg-surface-container font-label-sm text-label-sm text-primary font-semibold tracking-wide">
                    PORTFOLIO v4.18
                  </span>
                </div>
                <p className="font-body-md text-body-md text-on-surface-variant max-w-2xl">
                  Manage customer enrollments and ensure policy terms are ready for confirmation.
                </p>
              </div>

              <div className="flex items-center gap-3 shrink-0">
                <button
                  type="button"
                  onClick={loadData}
                  disabled={isSyncing}
                  className="inline-flex items-center gap-2 px-5 py-2.5 rounded-full bg-surface-container hover:bg-surface-container-high text-on-surface font-label-lg text-label-lg shadow-sm transition-all group cursor-pointer"
                >
                  <span
                    className={`material-symbols-outlined text-[18px] text-outline group-hover:text-on-surface ${isSyncing ? 'animate-spin text-primary' : ''
                      }`}
                  >
                    sync
                  </span>
                  <span>{isSyncing ? 'Syncing...' : 'Sync Vault'}</span>
                </button>

                <button
                  type="button"
                  onClick={() => setShowEnrollModal(true)}
                  className="inline-flex items-center gap-2.5 px-6 py-2.5 rounded-full bg-primary hover:bg-secondary text-on-primary font-label-lg text-label-lg shadow-[0_4px_14px_rgba(37,99,235,0.28)] transition-all transform hover:-translate-y-0.5 cursor-pointer"
                >
                  <span className="material-symbols-outlined text-[20px]">add</span>
                  <span>Start New Enrollment</span>
                </button>
              </div>
            </div>

            {/* 2. Overview Metrics Row (4 Status Cards) */}
            {/* 2. Overview Metrics Row (4 Status Cards) */}
            <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
              {/* Card 1: Total Registrations */}
              <div className="rounded-2xl bg-white p-5 border border-slate-200/80 shadow-xs flex flex-col justify-between hover:shadow-md transition">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold uppercase tracking-wider text-slate-500">
                    Total Registrations
                  </span>
                  <div className="w-9 h-9 rounded-xl bg-blue-50 text-blue-700 flex items-center justify-center">
                    <span className="material-symbols-outlined text-[20px]">folder_shared</span>
                  </div>
                </div>
                <div className="mt-4 flex items-baseline justify-between">
                  <span className="text-3xl font-extrabold text-[#131B2E]">
                    {totalCount}
                  </span>
                  <span className="px-2 py-0.5 rounded-full bg-slate-100 text-slate-700 text-[11px] font-bold">
                    100% Volume
                  </span>
                </div>
                <p className="text-[11px] text-slate-400 mt-2">All-time agent portfolio</p>
              </div>

              {/* Card 2: Awaiting Customer Confirmation */}
              <div className="rounded-2xl bg-white p-5 border border-slate-200/80 shadow-xs flex flex-col justify-between hover:shadow-md transition">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold uppercase tracking-wider text-slate-500">
                    Awaiting Customer
                  </span>
                  <div className="w-9 h-9 rounded-xl bg-amber-50 text-amber-700 flex items-center justify-center">
                    <span className="material-symbols-outlined text-[20px]">pending_actions</span>
                  </div>
                </div>
                <div className="mt-4 flex items-baseline justify-between">
                  <span className="text-3xl font-extrabold text-amber-800">
                    {countAwaiting}
                  </span>
                  <span className="px-2 py-0.5 rounded-full bg-amber-100 text-amber-800 text-[11px] font-bold">
                    Action Required
                  </span>
                </div>
                <p className="text-[11px] text-slate-400 mt-2">Awaiting customer sign-off</p>
              </div>

              {/* Card 3: Confirmed Registrations */}
              <div className="rounded-2xl bg-white p-5 border border-slate-200/80 shadow-xs flex flex-col justify-between hover:shadow-md transition">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold uppercase tracking-wider text-slate-500">
                    Confirmed
                  </span>
                  <div className="w-9 h-9 rounded-xl bg-emerald-50 text-emerald-700 flex items-center justify-center">
                    <span className="material-symbols-outlined text-[20px]">verified</span>
                  </div>
                </div>
                <div className="mt-4 flex items-baseline justify-between">
                  <span className="text-3xl font-extrabold text-emerald-800">
                    {countConfirmed}
                  </span>
                  <span className="px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800 text-[11px] font-bold">
                    {totalCount > 0 ? `${Math.round((countConfirmed / totalCount) * 100)}% Bound` : '0% Bound'}
                  </span>
                </div>
                <p className="text-[11px] text-slate-400 mt-2">Customer bound &amp; activated</p>
              </div>

              {/* Card 4: Pending Review */}
              <div className="rounded-2xl bg-white p-5 border border-slate-200/80 shadow-xs flex flex-col justify-between hover:shadow-md transition">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold uppercase tracking-wider text-slate-500">
                    Pending Review
                  </span>
                  <div className="w-9 h-9 rounded-xl bg-purple-50 text-purple-700 flex items-center justify-center">
                    <span className="material-symbols-outlined text-[20px]">fact_check</span>
                  </div>
                </div>
                <div className="mt-4 flex items-baseline justify-between">
                  <span className="text-3xl font-extrabold text-purple-900">
                    {countPending}
                  </span>
                  <span className="px-2 py-0.5 rounded-full bg-purple-100 text-purple-800 text-[11px] font-bold">
                    Audit Queue
                  </span>
                </div>
                <p className="text-[11px] text-slate-400 mt-2">In telemetry parity scan</p>
              </div>
            </div>

            {/* 3. Primary Workflow Panel ("Start an Enrollment") */}
            <div className="relative rounded-2xl bg-surface-container-lowest p-6 sm:p-7 shadow-[0_4px_20px_-2px_rgba(37,99,235,0.06),0_2px_6px_-1px_rgba(15,23,42,0.03)] overflow-hidden">
              <div className="absolute -top-24 -right-24 w-96 h-96 rounded-full bg-surface-container opacity-40 blur-3xl pointer-events-none"></div>
              <div className="relative flex flex-col gap-6">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                  <div className="flex items-center gap-3">
                    <div className="w-9 h-9 rounded-xl bg-primary flex items-center justify-center text-on-primary">
                      <span className="material-symbols-outlined text-[20px]">assignment_add</span>
                    </div>
                    <div>
                      <h2 className="font-headline-sm text-headline-sm text-on-surface font-bold tracking-tight">
                        Start an Enrollment
                      </h2>
                      <p className="font-body-sm text-body-sm text-on-surface-variant">
                        Follow deterministic voice protocols to bind statutory policies in real-time.
                      </p>
                    </div>
                  </div>
                  <span className="self-start sm:self-auto px-3 py-1 rounded-full bg-primary-fixed text-on-primary-fixed font-label-sm text-label-sm font-bold tracking-wide uppercase">
                    Guided 3-Step Process
                  </span>
                </div>

                {/* 3 Horizontal Steps */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {/* Step 1 */}
                  <div className="flex flex-col gap-2 p-4 rounded-xl bg-surface-container-low transition-colors hover:bg-surface-container">
                    <div className="flex items-center justify-between">
                      <span className="font-label-md text-label-md font-bold text-primary uppercase tracking-wider">
                        Step 01
                      </span>
                      <span className="material-symbols-outlined text-[18px] text-outline">verified_user</span>
                    </div>
                    <h3 className="font-label-lg text-label-lg font-bold text-on-surface">1. Select Scheme</h3>
                    <p className="font-body-sm text-body-sm text-on-surface-variant">
                      Choose an active underwritten policy scheme suited to client requirements.
                    </p>
                  </div>

                  {/* Step 2 */}
                  <div className="flex flex-col gap-2 p-4 rounded-xl bg-surface-container-low transition-colors hover:bg-surface-container">
                    <div className="flex items-center justify-between">
                      <span className="font-label-md text-label-md font-bold text-primary uppercase tracking-wider">
                        Step 02
                      </span>
                      <span className="material-symbols-outlined text-[18px] text-outline">mic</span>
                    </div>
                    <h3 className="font-label-lg text-label-lg font-bold text-on-surface">
                      2. Capture Consent &amp; Audio
                    </h3>
                    <p className="font-body-sm text-body-sm text-on-surface-variant">
                      Record customer tele-sales consultation and explicit consent under voice telemetry.
                    </p>
                  </div>

                  {/* Step 3 */}
                  <div className="flex flex-col gap-2 p-4 rounded-xl bg-surface-container-low transition-colors hover:bg-surface-container">
                    <div className="flex items-center justify-between">
                      <span className="font-label-md text-label-md font-bold text-primary uppercase tracking-wider">
                        Step 03
                      </span>
                      <span className="material-symbols-outlined text-[18px] text-outline">send_time_extension</span>
                    </div>
                    <h3 className="font-label-lg text-label-lg font-bold text-on-surface">
                      3. Submit for Confirmation
                    </h3>
                    <p className="font-body-sm text-body-sm text-on-surface-variant">
                      Dispatch deterministic terms to client vault for binding approval and audit validation.
                    </p>
                  </div>
                </div>

                {/* Action CTA Bar */}
                <div className="flex flex-col sm:flex-row items-center justify-between gap-4 pt-2">
                  <div className="flex items-center gap-4">
                    <button
                      type="button"
                      onClick={() => setShowEnrollModal(true)}
                      className="inline-flex items-center gap-2 px-6 py-2.5 rounded-full bg-primary hover:bg-secondary text-on-primary font-label-lg text-label-lg shadow-[0_4px_14px_rgba(37,99,235,0.25)] transition-all cursor-pointer"
                    >
                      <span>Create Enrollment</span>
                      <span className="material-symbols-outlined text-[18px]">arrow_forward</span>
                    </button>
                    <a
                      className="font-label-md text-label-md text-primary hover:text-secondary font-semibold transition-colors flex items-center gap-1"
                      href="#agent-guidelines"
                      onClick={(e) => {
                        e.preventDefault();
                        alert('IRDAI Compliance Guideline: Explicit customer affirmative consent is required for all verbal policy representations.');
                      }}
                    >
                      <span>Review Agent Guidelines</span>
                      <span className="material-symbols-outlined text-[16px]">open_in_new</span>
                    </a>
                  </div>
                  <div className="flex items-center gap-2 text-outline font-label-sm text-label-sm">
                    <span className="material-symbols-outlined text-[16px] text-primary">security</span>
                    <span>IRDAI Non-Repudiation Guaranteed • Audio Hash SHA-256</span>
                  </div>
                </div>
              </div>
            </div>

            {/* 4. Two-Column Grid for Operational Sections */}
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
              {/* Left Column (8 cols): Recent Registrations Table */}
              <div className="lg:col-span-8 flex flex-col gap-4" id="recent-registrations">
                <div className="rounded-2xl bg-surface-container-lowest p-6 shadow-[0_4px_20px_-2px_rgba(37,99,235,0.05),0_2px_6px_-1px_rgba(15,23,42,0.03)]">
                  {/* Section Header + Controls */}
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-5">
                    <div className="flex flex-col">
                      <h2 className="font-headline-sm text-headline-sm text-on-surface font-bold">
                        Recent Registrations
                      </h2>
                      <span className="font-body-sm text-body-sm text-on-surface-variant">
                        Live audit log of all-channel voice submissions
                      </span>
                    </div>

                    <div className="flex items-center gap-2.5">
                      {/* Search */}
                      <div className="relative flex items-center">
                        <span className="material-symbols-outlined absolute left-3 text-[16px] text-outline">
                          search
                        </span>
                        <input
                          type="text"
                          value={searchQuery}
                          onChange={(e) => setSearchQuery(e.target.value)}
                          placeholder="Filter records..."
                          className="h-9 w-44 sm:w-52 pl-8 pr-3 rounded-xl bg-surface-container-low text-on-surface font-body-sm text-body-sm placeholder:text-outline focus:outline-none focus:bg-surface-container-lowest transition-all"
                        />
                      </div>

                      {/* Filter Dropdown */}
                      <div className="relative">
                        <select
                          value={statusFilter}
                          onChange={(e) => setStatusFilter(e.target.value)}
                          className="h-9 px-3 pr-8 rounded-xl bg-surface-container-low text-on-surface font-label-md text-label-md focus:outline-none appearance-none cursor-pointer"
                        >
                          <option value="ALL">All Statuses</option>
                          <option value="AWAITING_CUSTOMER_CONFIRMATION">Awaiting Confirmation</option>
                          <option value="CONFIRMED">Confirmed</option>
                          <option value="PENDING_REVIEW">Pending Review</option>
                          <option value="DECLINED">Declined</option>
                        </select>
                        <span className="material-symbols-outlined absolute right-2 top-2 text-[18px] text-outline pointer-events-none">
                          expand_more
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Clean Enterprise Data Table */}
                  <div className="overflow-x-auto">
                    <table className="w-full text-left">
                      <thead>
                        <tr className="bg-surface-container-low font-label-sm text-label-sm text-outline uppercase tracking-wider">
                          <th className="py-3 px-3.5 rounded-l-xl font-bold">Registration Ref</th>
                          <th className="py-3 px-3.5 font-bold">Customer Name</th>
                          <th className="py-3 px-3.5 font-bold">Policy / Scheme</th>
                          <th className="py-3 px-3.5 font-bold">Created Date</th>
                          <th className="py-3 px-3.5 font-bold">Status</th>
                          <th className="py-3 px-3.5 rounded-r-xl font-bold text-right">Actions</th>
                        </tr>
                      </thead>
                      <tbody className="font-body-sm text-body-sm divide-y-0">
                        {filteredRegistrations.length === 0 ? (
                          <tr>
                            <td colSpan={6} className="text-center py-8 text-on-surface-variant font-medium">
                              No registrations match current search criteria.
                            </td>
                          </tr>
                        ) : (
                          filteredRegistrations.map((reg) => {
                            const dateStr = new Date(reg.created_at).toLocaleDateString('en-US', {
                              month: 'short',
                              day: 'numeric',
                              year: 'numeric',
                            });

                            return (
                              <tr
                                key={reg.id}
                                className="hover:bg-surface-container-low/60 transition-colors group"
                              >
                                <td className="py-3.5 px-3.5">
                                  <div className="flex items-center gap-1.5">
                                    <span className="font-label-md text-label-md font-bold text-on-surface">
                                      {reg.id}
                                    </span>
                                    <button
                                      onClick={() => handleCopy(reg.id)}
                                      title="Copy Ref"
                                      className="material-symbols-outlined text-[14px] text-outline opacity-0 group-hover:opacity-100 hover:text-primary cursor-pointer transition-opacity"
                                    >
                                      {copiedId === reg.id ? 'check' : 'content_copy'}
                                    </button>
                                  </div>
                                </td>

                                <td className="py-3.5 px-3.5">
                                  <div className="flex flex-col">
                                    <span className="font-label-md text-label-md font-semibold text-on-surface">
                                      {reg.customer?.full_name || 'Valued Customer'}
                                    </span>
                                    <span className="font-label-sm text-label-sm text-outline">
                                      {reg.customer?.phone || reg.customer?.email || '—'}
                                    </span>
                                  </div>
                                </td>

                                <td className="py-3.5 px-3.5 text-on-surface-variant font-medium">
                                  {reg.policy?.policy_name || 'Care Premier Health Shield'}
                                </td>

                                <td className="py-3.5 px-3.5 text-outline">{dateStr}</td>

                                <td className="py-3.5 px-3.5">
                                  {reg.status === 'AWAITING_CUSTOMER_CONFIRMATION' && (
                                    <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-surface-container-highest text-on-surface font-label-sm text-label-sm font-semibold">
                                      <span className="w-1.5 h-1.5 rounded-full bg-secondary-container"></span>
                                      AWAITING_CUSTOMER_CONFIRMATION
                                    </span>
                                  )}
                                  {reg.status === 'CONFIRMED' && (
                                    <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-surface-container-high text-primary font-label-sm text-label-sm font-bold">
                                      <span className="w-1.5 h-1.5 rounded-full bg-primary"></span>
                                      CONFIRMED
                                    </span>
                                  )}
                                  {reg.status === 'PENDING_REVIEW' && (
                                    <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-surface-container text-on-surface-variant font-label-sm text-label-sm font-semibold">
                                      <span className="w-1.5 h-1.5 rounded-full bg-outline"></span>
                                      PENDING_REVIEW
                                    </span>
                                  )}
                                  {reg.status === 'DECLINED' && (
                                    <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-error-container text-on-error-container font-label-sm text-label-sm font-semibold">
                                      <span className="w-1.5 h-1.5 rounded-full bg-error"></span>
                                      DECLINED
                                    </span>
                                  )}
                                </td>

                                <td className="py-3.5 px-3.5 text-right">
                                  <button
                                    onClick={() => setActiveDetailReg(reg)}
                                    className="inline-flex items-center gap-1 px-3 py-1 rounded-lg bg-surface-container hover:bg-primary hover:text-on-primary text-on-surface font-label-sm text-label-sm font-semibold transition-colors cursor-pointer"
                                    type="button"
                                  >
                                    <span>View Details</span>
                                    <span className="material-symbols-outlined text-[14px]">
                                      chevron_right
                                    </span>
                                  </button>
                                </td>
                              </tr>
                            );
                          })
                        )}
                      </tbody>
                    </table>
                  </div>

                  {/* Pagination Summary */}
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pt-5 mt-2">
                    <span className="font-body-sm text-body-sm text-outline">
                      Showing{' '}
                      <strong className="text-on-surface font-semibold">
                        {filteredRegistrations.length}
                      </strong>{' '}
                      of{' '}
                      <strong className="text-on-surface font-semibold">{totalCount}</strong>{' '}
                      registrations
                    </span>
                    <button
                      type="button"
                      onClick={() => {
                        setStatusFilter('ALL');
                        setSearchQuery('');
                      }}
                      className="inline-flex items-center gap-1.5 font-label-md text-label-md text-primary hover:text-secondary font-bold transition-colors cursor-pointer"
                    >
                      <span>View All Registrations</span>
                      <span className="material-symbols-outlined text-[16px]">arrow_forward</span>
                    </button>
                  </div>
                </div>
              </div>

              {/* Right Column (4 cols): Available Schemes Preview */}
              <div className="lg:col-span-4 flex flex-col gap-4" id="available-schemes">
                <div className="rounded-2xl bg-surface-container-lowest p-6 shadow-[0_4px_20px_-2px_rgba(37,99,235,0.05),0_2px_6px_-1px_rgba(15,23,42,0.03)] flex flex-col gap-4">
                  {/* Header */}
                  <div className="flex items-center justify-between">
                    <div className="flex flex-col">
                      <h2 className="font-headline-sm text-headline-sm text-on-surface font-bold">
                        Available Schemes
                      </h2>
                      <span className="font-body-sm text-body-sm text-outline">
                        Underwritten policy packages
                      </span>
                    </div>
                    <button
                      onClick={() => setShowEnrollModal(true)}
                      className="inline-flex items-center gap-1 font-label-sm text-label-sm text-primary hover:text-secondary font-semibold transition-colors cursor-pointer"
                    >
                      <span>Browse Schemes</span>
                      <span className="material-symbols-outlined text-[14px]">arrow_forward</span>
                    </button>
                  </div>

                  {/* Stack of 3 Preview Cards */}
                  <div className="flex flex-col gap-3">
                    {/* Scheme 1: Care Premier Health Shield */}
                    <div
                      onClick={() => {
                        setSelectedSchemeForEnroll('pol-001');
                        setShowEnrollModal(true);
                      }}
                      className="p-4 rounded-xl bg-surface-container-low hover:bg-surface-container transition-all flex flex-col gap-2.5 group cursor-pointer"
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex flex-col">
                          <span className="font-label-lg text-label-lg font-bold text-on-surface group-hover:text-primary transition-colors">
                            Care Premier Health Shield
                          </span>
                          <span className="font-label-sm text-label-sm text-outline">
                            Health &amp; Critical Care
                          </span>
                        </div>
                        <span className="w-7 h-7 rounded-full bg-surface-container flex items-center justify-center text-primary group-hover:bg-primary group-hover:text-on-primary transition-colors">
                          <span className="material-symbols-outlined text-[16px]">add</span>
                        </span>
                      </div>
                      <p className="font-body-sm text-body-sm text-on-surface-variant">
                        Comprehensive inpatient hospitalization with cashless network.
                      </p>
                      <div className="flex flex-wrap items-center gap-x-3 gap-y-1 pt-1 font-label-sm text-label-sm text-outline">
                        <span>
                          Limit: <strong className="text-on-surface font-semibold">₹15,00,000</strong>
                        </span>
                        <span>•</span>
                        <span>
                          Wait: <strong className="text-on-surface font-semibold">24 Mos</strong>
                        </span>
                        <span>•</span>
                        <span className="px-1.5 py-0.2 rounded bg-surface-container font-semibold text-primary">
                          v2.4 (IRDAI)
                        </span>
                      </div>
                    </div>

                    {/* Scheme 2: Comprehensive Auto DriveProtect */}
                    <div
                      onClick={() => {
                        setSelectedSchemeForEnroll('pol-002');
                        setShowEnrollModal(true);
                      }}
                      className="p-4 rounded-xl bg-surface-container-low hover:bg-surface-container transition-all flex flex-col gap-2.5 group cursor-pointer"
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex flex-col">
                          <span className="font-label-lg text-label-lg font-bold text-on-surface group-hover:text-primary transition-colors">
                            Comprehensive Auto DriveProtect
                          </span>
                          <span className="font-label-sm text-label-sm text-outline">
                            Motor &amp; Roadside Logistics
                          </span>
                        </div>
                        <span className="w-7 h-7 rounded-full bg-surface-container flex items-center justify-center text-primary group-hover:bg-primary group-hover:text-on-primary transition-colors">
                          <span className="material-symbols-outlined text-[16px]">add</span>
                        </span>
                      </div>
                      <p className="font-body-sm text-body-sm text-on-surface-variant">
                        Motor protection including zero depreciation and roadside telemetry.
                      </p>
                      <div className="flex flex-wrap items-center gap-x-3 gap-y-1 pt-1 font-label-sm text-label-sm text-outline">
                        <span>
                          Limit: <strong className="text-on-surface font-semibold">₹8,50,000</strong>
                        </span>
                        <span>•</span>
                        <span>
                          Wait: <strong className="text-on-surface font-semibold">Day 1</strong>
                        </span>
                        <span>•</span>
                        <span className="px-1.5 py-0.2 rounded bg-surface-container font-semibold text-primary">
                          v1.8
                        </span>
                      </div>
                    </div>

                    {/* Scheme 3: Life Horizon Secure Term */}
                    <div
                      onClick={() => {
                        setSelectedSchemeForEnroll('pol-003');
                        setShowEnrollModal(true);
                      }}
                      className="p-4 rounded-xl bg-surface-container-low hover:bg-surface-container transition-all flex flex-col gap-2.5 group cursor-pointer"
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex flex-col">
                          <span className="font-label-lg text-label-lg font-bold text-on-surface group-hover:text-primary transition-colors">
                            Life Horizon Secure Term
                          </span>
                          <span className="font-label-sm text-label-sm text-outline">
                            Term Life Assurance
                          </span>
                        </div>
                        <span className="w-7 h-7 rounded-full bg-surface-container flex items-center justify-center text-primary group-hover:bg-primary group-hover:text-on-primary transition-colors">
                          <span className="material-symbols-outlined text-[16px]">add</span>
                        </span>
                      </div>
                      <p className="font-body-sm text-body-sm text-on-surface-variant">
                        Pure term life protection with critical illness telemetry rider.
                      </p>
                      <div className="flex flex-wrap items-center gap-x-3 gap-y-1 pt-1 font-label-sm text-label-sm text-outline">
                        <span>
                          Limit: <strong className="text-on-surface font-semibold">₹50,00,000</strong>
                        </span>
                        <span>•</span>
                        <span>
                          Wait: <strong className="text-on-surface font-semibold">30 Days</strong>
                        </span>
                        <span>•</span>
                        <span className="px-1.5 py-0.2 rounded bg-surface-container font-semibold text-primary">
                          v3.1
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Bottom Secondary Button */}
                  <button
                    onClick={() => setShowEnrollModal(true)}
                    className="w-full py-2.5 px-4 rounded-xl bg-surface-container hover:bg-surface-container-high text-on-surface font-label-md text-label-md font-semibold text-center transition-colors flex items-center justify-center gap-2 cursor-pointer"
                  >
                    <span className="material-symbols-outlined text-[18px] text-outline">library_books</span>
                    <span>Browse All Schemes</span>
                  </button>
                </div>
              </div>
            </div>
          </>
        )}

        {/* TAB: INSURANCE SCHEMES */}
        {activeAgentNav === 'schemes' && (
          <div className="flex flex-col gap-6 animate-fadeIn">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div>
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-[11px] font-bold uppercase tracking-wider text-primary">Master Policy Catalog</span>
                  <span className="text-slate-400 text-xs">•</span>
                  <span className="text-[11px] font-semibold text-on-surface-variant">IRDAI Approved</span>
                </div>
                <h2 className="text-2xl font-bold text-on-surface">Available Insurance Schemes</h2>
                <p className="text-xs text-on-surface-variant">Underwriting portfolio with deterministic clause extraction and verbal parity bounds.</p>
              </div>
              <button
                onClick={() => setShowEnrollModal(true)}
                className="self-start sm:self-auto px-4 py-2 rounded-full bg-primary text-on-primary text-xs font-bold flex items-center gap-1.5 hover:bg-secondary transition-colors cursor-pointer shadow-sm"
              >
                <span className="material-symbols-outlined text-[16px]">add_circle</span>
                <span>Start New Enrollment</span>
              </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {policies.map((p) => (
                <div key={p.id} className="bg-surface-container-lowest rounded-2xl border border-slate-100 p-6 shadow-xs flex flex-col justify-between gap-6 hover:shadow-md transition-shadow">
                  <div className="flex flex-col gap-4">
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex items-center gap-3">
                        <div className="w-12 h-12 rounded-xl bg-surface-container-low text-primary flex items-center justify-center font-bold">
                          <span className="material-symbols-outlined text-[24px]">verified_user</span>
                        </div>
                        <div>
                          <h3 className="text-base font-bold text-on-surface">{p.policy_name}</h3>
                          <p className="text-xs text-on-surface-variant font-mono">{p.policy_code} • {p.insurer_name}</p>
                        </div>
                      </div>
                      <span className="px-2.5 py-1 rounded-full text-[10px] font-bold bg-primary-fixed text-on-primary-fixed uppercase">
                        {p.category}
                      </span>
                    </div>

                    <p className="text-xs text-on-surface-variant leading-relaxed">{p.description}</p>

                    <div className="grid grid-cols-3 gap-2 p-3 bg-surface-container-low rounded-xl text-center">
                      <div>
                        <span className="text-[10px] text-on-surface-variant uppercase font-medium">Coverage Limit</span>
                        <p className="text-xs font-bold text-on-surface">₹{(p.coverage_limit || 0).toLocaleString('en-IN')}</p>
                      </div>
                      <div>
                        <span className="text-[10px] text-on-surface-variant uppercase font-medium">Waiting Period</span>
                        <p className="text-xs font-bold text-on-surface">{p.waiting_period_days || 0} Days</p>
                      </div>
                      <div>
                        <span className="text-[10px] text-on-surface-variant uppercase font-medium">Claim Window</span>
                        <p className="text-xs font-bold text-on-surface">{p.claim_filing_window_days || 0} Days</p>
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center justify-between pt-4 border-t border-slate-100">
                    <span className="text-xs text-emerald-600 font-semibold flex items-center gap-1">
                      <span className="material-symbols-outlined text-[14px]">check_circle</span>
                      <span>IRDAI Active</span>
                    </span>
                    <button
                      onClick={() => {
                        setSelectedSchemeForEnroll(p.id);
                        setShowEnrollModal(true);
                      }}
                      className="px-4 py-2 rounded-full bg-primary hover:bg-secondary text-on-primary text-xs font-bold transition-colors flex items-center gap-1.5 cursor-pointer"
                    >
                      <span className="material-symbols-outlined text-[14px]">person_add</span>
                      <span>Enroll Customer</span>
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* TAB: REGISTRATIONS QUEUE */}
        {activeAgentNav === 'registrations' && (
          <div className="flex flex-col gap-6 animate-fadeIn">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div>
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-[11px] font-bold uppercase tracking-wider text-primary">Field Operations Desk</span>
                  <span className="text-slate-400 text-xs">•</span>
                  <span className="text-[11px] font-semibold text-on-surface-variant">Live Client Handshake</span>
                </div>
                <h2 className="text-2xl font-bold text-on-surface">Customer Registrations Queue</h2>
                <p className="text-xs text-on-surface-variant">Complete ledger of customer registrations, audio telemetry statuses, and confirmation tracking.</p>
              </div>
              <div className="flex items-center gap-2">
                {(['ALL', 'AWAITING_CUSTOMER_CONFIRMATION', 'CONFIRMED', 'PENDING_REVIEW', 'DECLINED'] as const).map((filter) => (
                  <button
                    key={filter}
                    onClick={() => setStatusFilter(filter)}
                    className={`px-3 py-1.5 rounded-full text-xs font-bold transition-all cursor-pointer ${
                      statusFilter === filter
                        ? 'bg-primary text-on-primary shadow-xs'
                        : 'bg-surface-container-low text-on-surface-variant hover:bg-surface-container-high'
                    }`}
                  >
                    {filter === 'ALL' ? 'All' : filter === 'AWAITING_CUSTOMER_CONFIRMATION' ? 'Awaiting' : filter === 'CONFIRMED' ? 'Confirmed' : filter === 'PENDING_REVIEW' ? 'Review' : 'Declined'}
                  </button>
                ))}
              </div>
            </div>

            <div className="bg-surface-container-lowest rounded-2xl border border-slate-100 overflow-hidden shadow-xs">
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="border-b border-slate-100 bg-surface-container-low/50 text-[11px] font-bold uppercase tracking-wider text-on-surface-variant">
                      <th className="py-3 px-4">Registration ID</th>
                      <th className="py-3 px-4">Customer</th>
                      <th className="py-3 px-4">Policy Scheme</th>
                      <th className="py-3 px-4">Telemetry Status</th>
                      <th className="py-3 px-4">Status</th>
                      <th className="py-3 px-4 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 text-xs">
                    {filteredRegistrations.map((reg) => (
                      <tr key={reg.id} className="hover:bg-surface-container-low/40 transition-colors">
                        <td className="py-3 px-4 font-mono font-bold text-primary">{reg.id}</td>
                        <td className="py-3 px-4">
                          <span className="font-semibold text-on-surface">{reg.customer?.full_name || 'Customer'}</span>
                          <p className="text-[11px] text-on-surface-variant">{reg.customer?.phone || '+91 98402 11920'}</p>
                        </td>
                        <td className="py-3 px-4 font-medium text-on-surface">
                          {reg.policy?.policy_name || 'Care Premier Health'}
                        </td>
                        <td className="py-3 px-4">
                          <span className="flex items-center gap-1 text-[11px] text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-full w-fit font-bold">
                            <span className="material-symbols-outlined text-[12px]">graphic_eq</span>
                            <span>Audio Sealed</span>
                          </span>
                        </td>
                        <td className="py-3 px-4">
                          <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold uppercase ${
                            reg.status === 'CONFIRMED'
                              ? 'bg-emerald-50 text-emerald-700'
                              : reg.status === 'AWAITING_CUSTOMER_CONFIRMATION'
                              ? 'bg-amber-50 text-amber-700'
                              : 'bg-slate-100 text-slate-700'
                          }`}>
                            {reg.status}
                          </span>
                        </td>
                        <td className="py-3 px-4 text-right">
                          <button
                            onClick={() => setActiveDetailReg(reg)}
                            className="px-3 py-1 rounded-full bg-surface-container-low hover:bg-surface-container-high text-on-surface text-xs font-semibold transition-colors cursor-pointer"
                          >
                            Inspect
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

        {/* TAB: VOICE TELEMETRY AI */}
        {activeAgentNav === 'telemetry' && (
          <div className="flex flex-col gap-6 animate-fadeIn">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div>
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-[11px] font-bold uppercase tracking-wider text-primary">ElevenLabs Speech Engine</span>
                  <span className="text-slate-400 text-xs">•</span>
                  <span className="text-[11px] font-semibold text-emerald-600">Cloudinary Secured</span>
                  <span className="text-slate-400 text-xs">•</span>
                  <span className="text-[11px] font-semibold text-primary">Gemini 2.5 Policy Parity</span>
                </div>
                <h2 className="text-2xl font-bold text-on-surface">Voice Tele-Sales Telemetry & Compliance AI</h2>
                <p className="text-xs text-on-surface-variant">Real-time acoustic analysis of sales calls to ensure verbal disclosures match written policy terms.</p>
              </div>

              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => {
                    setSalesTranscript(`[Agent Rajesh]: Namaste Vikram ji, Care Premier Health Shield me inpatient room rent aur ICU charges cashless network par Rs 15,00,000 tak puri tarah covered hain. Sath hi 60 days pre-hospitalization aur 90 days post-hospitalization bills bhi milenge.
[Customer Vikram]: Sahi hai. Aur mujhe diabetes aur BP ki problem hai, uska kya hoga?
[Agent Rajesh]: Vikram ji don't worry, aapka diabetes aur BP is policy me completely covered hai, uski saari dawaiyan aur hospitalization admissible hongi.
[Customer Vikram]: Aur cosmetic skin laser treatment ya normal doctor OPD checkups?
[Agent Rajesh]: Haan bilkul, aap koi bhi cosmetic laser treatment karwayein ya normal OPD me clinic jakar checkup karwayein, bina hospital me admit huye bhi hum 100% reimburse kar denge.
[Customer Vikram]: Theek hai Rajesh ji, main is policy ke liye apni verbal consent deta hoon.
[Agent Rajesh]: Dhanyawad Vikram ji, aapka consent record ho gaya hai. Emergency road ambulance bhi Rs 3,000 tak covered rahegi.`);
                    setAudioFileName('care_premier_tele_sales_recording_001.mp3');
                  }}
                  className="px-3 py-1.5 rounded-full bg-surface-container-low hover:bg-surface-container-high text-primary text-xs font-bold transition-all border border-slate-200 cursor-pointer flex items-center gap-1.5"
                >
                  <span className="material-symbols-outlined text-[16px]">content_paste</span>
                  <span>Pre-fill Official Recording Script</span>
                </button>
              </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
              {/* Left Column: Transcript & Audio Uploader */}
              <div className="lg:col-span-7 bg-surface-container-lowest rounded-2xl border border-slate-100 p-6 shadow-xs flex flex-col gap-4">
                <div className="flex items-center justify-between pb-3 border-b border-slate-100">
                  <div className="flex items-center gap-2">
                    <span className="material-symbols-outlined text-primary text-[22px]">mic</span>
                    <h3 className="text-sm font-bold text-on-surface">Sales Call Audio & Transcription Feed</h3>
                  </div>
                  {audioFileName && (
                    <span className="px-2.5 py-0.5 rounded-full bg-blue-50 text-blue-700 font-mono text-[10px] font-bold flex items-center gap-1">
                      <span className="material-symbols-outlined text-[12px]">cloud_done</span>
                      <span>Cloudinary: {audioFileName}</span>
                    </span>
                  )}
                </div>

                {/* Target Policy Selection */}
                <div>
                  <label className="block text-xs font-bold text-on-surface uppercase mb-1">
                    Audited Master Policy Wording (Cloudinary PDF Linked)
                  </label>
                  <select
                    value={selectedSchemeForEnroll}
                    onChange={(e) => setSelectedSchemeForEnroll(e.target.value)}
                    className="w-full h-10 px-3 rounded-xl bg-surface-container-low border border-slate-200 text-xs font-semibold text-on-surface focus:outline-none focus:border-primary cursor-pointer"
                  >
                    {policies.map((p) => (
                      <option key={p.id} value={p.id}>
                        {p.policy_name} ({p.policy_code}) — Limit: ₹{(p.coverage_limit || 0).toLocaleString('en-IN')}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Sales Call Transcript Input */}
                <div>
                  <label className="block text-xs font-bold text-on-surface uppercase mb-1">
                    Live Tele-Sales Transcript / Audio Captions
                  </label>
                  <textarea
                    rows={8}
                    value={salesTranscript}
                    onChange={(e) => setSalesTranscript(e.target.value)}
                    className="w-full p-3 rounded-xl bg-surface-container-low border border-slate-200 font-mono text-xs text-on-surface leading-relaxed focus:outline-none focus:border-primary"
                    placeholder="Enter or paste the voice conversation transcript between Agent and Customer..."
                  />
                </div>

                {/* Run Audit Button */}
                <div className="flex items-center justify-between pt-2">
                  <div className="flex items-center gap-2">
                    <label className="px-3 py-1.5 rounded-full bg-surface-container-low hover:bg-surface-container-high text-xs font-semibold text-slate-700 border border-slate-200 cursor-pointer flex items-center gap-1">
                      <span className="material-symbols-outlined text-[16px] text-primary">upload_file</span>
                      <span>Upload Recording File</span>
                      <input
                        type="file"
                        accept="audio/*"
                        className="hidden"
                        onChange={(e) => {
                          if (e.target.files && e.target.files[0]) {
                            setAudioFileName(e.target.files[0].name);
                          }
                        }}
                      />
                    </label>
                  </div>

                  <button
                    type="button"
                    onClick={handleRunGeminiAudit}
                    disabled={isAuditing || !salesTranscript.trim()}
                    className="px-5 py-2.5 rounded-full bg-primary hover:bg-secondary text-on-primary text-xs font-bold transition-all shadow-md flex items-center gap-2 cursor-pointer disabled:opacity-50"
                  >
                    {isAuditing ? (
                      <>
                        <span className="animate-spin material-symbols-outlined text-[16px]">sync</span>
                        <span>Auditing with Gemini 2.5...</span>
                      </>
                    ) : (
                      <>
                        <span className="material-symbols-outlined text-[16px]">verified</span>
                        <span>Execute Gemini Policy Parity Audit</span>
                      </>
                    )}
                  </button>
                </div>
              </div>

              {/* Right Column: Parity Findings & Verdicts */}
              <div className="lg:col-span-5 bg-surface-container-lowest rounded-2xl border border-slate-100 p-6 shadow-xs flex flex-col gap-4">
                <div className="flex items-center justify-between pb-3 border-b border-slate-100">
                  <h3 className="text-sm font-bold text-on-surface">Gemini Compliance Parity Verdict</h3>
                  {auditResult && (
                    <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase ${
                      auditResult.overall_status === 'COMPLIANT'
                        ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                        : 'bg-red-50 text-red-700 border border-red-200'
                    }`}>
                      {auditResult.overall_status === 'COMPLIANT' ? '100% Compliant' : 'Discrepancy Detected'}
                    </span>
                  )}
                </div>

                {auditResult ? (
                  <div className="flex flex-col gap-3 max-h-[500px] overflow-y-auto pr-1">
                    <p className="text-xs text-on-surface-variant italic bg-slate-50 p-2.5 rounded-xl border border-slate-200/60">
                      "{auditResult.summary}"
                    </p>

                    <div className="grid grid-cols-3 gap-2 text-center text-xs p-2.5 bg-surface-container-low rounded-xl">
                      <div>
                        <span className="text-[10px] uppercase font-bold text-emerald-600">Supported</span>
                        <p className="font-mono text-sm font-bold text-emerald-700">{auditResult.supported_count || 0}</p>
                      </div>
                      <div>
                        <span className="text-[10px] uppercase font-bold text-amber-600">Partly True</span>
                        <p className="font-mono text-sm font-bold text-amber-700">{auditResult.partly_true_count || 0}</p>
                      </div>
                      <div>
                        <span className="text-[10px] uppercase font-bold text-red-600">Contradicted</span>
                        <p className="font-mono text-sm font-bold text-red-700">{auditResult.contradicted_count || 0}</p>
                      </div>
                    </div>

                    <div className="space-y-3 pt-1">
                      {auditResult.findings?.map((f: any, idx: number) => (
                        <div
                          key={idx}
                          className={`p-3 rounded-xl border text-xs flex flex-col gap-1.5 ${
                            f.verdict === 'SUPPORTED'
                              ? 'bg-emerald-50/40 border-emerald-200 text-slate-800'
                              : f.verdict === 'PARTLY_TRUE'
                              ? 'bg-amber-50/50 border-amber-200 text-slate-800'
                              : 'bg-red-50/50 border-red-200 text-slate-800'
                          }`}
                        >
                          <div className="flex items-center justify-between gap-1">
                            <span className="font-bold text-navy-900">{f.promise_text}</span>
                            <span className={`px-2 py-0.5 rounded-full text-[9px] font-bold shrink-0 ${
                              f.verdict === 'SUPPORTED'
                                ? 'bg-emerald-600 text-white'
                                : f.verdict === 'PARTLY_TRUE'
                                ? 'bg-amber-600 text-white'
                                : 'bg-red-600 text-white'
                            }`}>
                              {f.verdict}
                            </span>
                          </div>

                          <div className="text-[11px] text-slate-600">
                            <strong>Transcript Quote:</strong> "{f.transcript_quote}"
                          </div>

                          <div className="text-[11px] text-slate-600 bg-white/70 p-2 rounded-lg border border-slate-200/50">
                            <strong>Policy Citation:</strong> {f.policy_excerpt || 'Clause not in policy'}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                ) : (
                  <div className="flex flex-col items-center justify-center py-10 text-center gap-3 text-on-surface-variant">
                    <span className="material-symbols-outlined text-[48px] text-slate-300">smart_toy</span>
                    <p className="text-xs">Click <strong>"Execute Gemini Policy Parity Audit"</strong> to compare verbal commitments against official policy clauses.</p>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </main>
  </div>

      {/* BEGIN: Create Enrollment Modal */}
      {showEnrollModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 backdrop-blur-sm p-4">
          <div className="bg-white rounded-2xl max-w-lg w-full p-6 shadow-2xl border border-slate-100 flex flex-col gap-4 animate-in fade-in duration-200">
            <div className="flex items-center justify-between pb-2 border-b border-slate-100">
              <div className="flex items-center gap-2.5">
                <div className="w-8 h-8 rounded-lg bg-primary text-on-primary flex items-center justify-center">
                  <span className="material-symbols-outlined text-[18px]">add_circle</span>
                </div>
                <div>
                  <h3 className="font-bold text-lg text-on-surface">Start New Customer Enrollment</h3>
                  <p className="text-xs text-outline">Deterministic voice tele-sales binding</p>
                </div>
              </div>
              <button
                onClick={() => setShowEnrollModal(false)}
                className="text-slate-400 hover:text-slate-600 p-1"
              >
                <span className="material-symbols-outlined text-[20px]">close</span>
              </button>
            </div>

            <form onSubmit={handleCreateEnrollment} className="flex flex-col gap-4">
              <div>
                <label className="block text-xs font-bold text-on-surface uppercase mb-1">
                  Customer Full Name *
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Vikram Sengupta"
                  value={customerName}
                  onChange={(e) => setCustomerName(e.target.value)}
                  className="w-full h-10 px-3 rounded-xl bg-surface-container-low border border-slate-200 text-sm focus:outline-none focus:border-primary"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-bold text-on-surface uppercase mb-1">
                    Customer Email *
                  </label>
                  <input
                    type="email"
                    required
                    placeholder="vikram@example.com"
                    value={customerEmail}
                    onChange={(e) => setCustomerEmail(e.target.value)}
                    className="w-full h-10 px-3 rounded-xl bg-surface-container-low border border-slate-200 text-sm focus:outline-none focus:border-primary"
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold text-on-surface uppercase mb-1">
                    Phone Number
                  </label>
                  <input
                    type="tel"
                    placeholder="+91 98402 11920"
                    value={customerPhone}
                    onChange={(e) => setCustomerPhone(e.target.value)}
                    className="w-full h-10 px-3 rounded-xl bg-surface-container-low border border-slate-200 text-sm focus:outline-none focus:border-primary"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-bold text-on-surface uppercase mb-1">
                  Select Policy Scheme *
                </label>
                <select
                  value={selectedSchemeForEnroll}
                  onChange={(e) => setSelectedSchemeForEnroll(e.target.value)}
                  className="w-full h-10 px-3 rounded-xl bg-surface-container-low border border-slate-200 text-sm focus:outline-none focus:border-primary cursor-pointer"
                >
                  {policies.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.policy_name} ({p.insurer_name}) — Limit: ₹{(p.coverage_limit || 0).toLocaleString('en-IN')}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-bold text-on-surface uppercase mb-1">
                  Consultation Notes
                </label>
                <textarea
                  rows={2}
                  value={consentNotes}
                  onChange={(e) => setConsentNotes(e.target.value)}
                  className="w-full p-2.5 rounded-xl bg-surface-container-low border border-slate-200 text-sm focus:outline-none focus:border-primary"
                />
              </div>

              <label className="flex items-start gap-2.5 p-3 rounded-xl bg-blue-50 border border-blue-100 cursor-pointer">
                <input
                  type="checkbox"
                  checked={customerConsent}
                  onChange={(e) => setCustomerConsent(e.target.checked)}
                  className="mt-0.5 rounded text-primary focus:ring-primary h-4 w-4"
                />
                <span className="text-xs text-slate-700 leading-snug">
                  <strong>Explicit Audio Consent Captured:</strong> Customer has affirmatively consented to policy representations via verified voice telemetry.
                </span>
              </label>

              <div className="flex items-center justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setShowEnrollModal(false)}
                  className="px-4 py-2 rounded-full text-sm font-semibold text-slate-600 hover:bg-slate-100 cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmittingEnrollment}
                  className="px-6 py-2.5 rounded-full text-sm font-semibold text-white bg-primary hover:bg-secondary shadow-md disabled:opacity-50 cursor-pointer"
                >
                  {isSubmittingEnrollment ? 'Dispatching...' : 'Dispatch Enrollment'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* BEGIN: Details View Modal */}
      {activeDetailReg && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 backdrop-blur-sm p-4">
          <div className="bg-white rounded-2xl max-w-lg w-full p-6 shadow-2xl border border-slate-100 flex flex-col gap-4 animate-in fade-in duration-200">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <div className="flex items-center gap-2">
                <span className="font-mono text-sm font-bold bg-slate-100 px-2 py-1 rounded text-primary">
                  {activeDetailReg.id}
                </span>
                <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-blue-50 text-blue-700 border border-blue-200">
                  {activeDetailReg.status}
                </span>
              </div>
              <button
                onClick={() => setActiveDetailReg(null)}
                className="text-slate-400 hover:text-slate-600 p-1 cursor-pointer"
              >
                <span className="material-symbols-outlined text-[20px]">close</span>
              </button>
            </div>

            <div className="space-y-3 text-sm">
              <div>
                <span className="text-xs font-bold text-outline uppercase block">Customer Details</span>
                <p className="font-semibold text-on-surface">
                  {activeDetailReg.customer?.full_name || 'Vikram Sengupta'}
                </p>
                <p className="text-xs text-slate-500">
                  {activeDetailReg.customer?.email || 'vikram@example.com'} • {activeDetailReg.customer?.phone || '+91 98402 11920'}
                </p>
              </div>

              <div>
                <span className="text-xs font-bold text-outline uppercase block">Policy Scheme</span>
                <p className="font-semibold text-on-surface">
                  {activeDetailReg.policy?.policy_name || 'Care Premier Health Shield'}
                </p>
                <p className="text-xs text-slate-500">
                  Insurer: {activeDetailReg.policy?.insurer_name || 'Care Premier Health'} • Limit: ₹{(activeDetailReg.policy?.coverage_limit || 1500000).toLocaleString('en-IN')}
                </p>
              </div>

              <div>
                <span className="text-xs font-bold text-outline uppercase block">Voice Telemetry Hash</span>
                <p className="font-mono text-[11px] bg-slate-50 p-2 rounded border border-slate-200 text-slate-700 break-all">
                  {activeDetailReg.audio_checksum || 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'}
                </p>
              </div>

              <div>
                <span className="text-xs font-bold text-outline uppercase block">Consent Log</span>
                <p className="text-xs text-slate-600 bg-slate-50 p-2 rounded">
                  {activeDetailReg.consent_notes || 'Oral affirmative consent validated under IRDAI standard tele-sales guidelines.'}
                </p>
              </div>
            </div>

            <div className="pt-2 flex justify-end">
              <button
                onClick={() => setActiveDetailReg(null)}
                className="px-5 py-2 rounded-full text-sm font-semibold bg-primary text-white hover:bg-secondary transition-all cursor-pointer"
              >
                Close Details
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AgentDashboard;
