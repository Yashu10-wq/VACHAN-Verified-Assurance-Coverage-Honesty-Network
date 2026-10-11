import React from 'react';
import { Link } from 'react-router-dom';

export const LandingPage: React.FC = () => {
  return (
    <div className="gradient-mesh-bg text-slate-800 antialiased min-h-screen selection:bg-blue-600 selection:text-white relative overflow-x-hidden font-sans">
      {/* BEGIN: FloatingAtmosphere */}
      <div className="pointer-events-none absolute top-0 left-1/2 -translate-x-1/2 w-full max-w-7xl h-[850px] overflow-hidden -z-10">
        <div className="hero-glow-sphere absolute -top-40 left-1/4 w-[650px] h-[650px] rounded-full"></div>
        <div className="hero-glow-sphere absolute top-32 right-10 w-[450px] h-[450px] rounded-full opacity-60"></div>
      </div>
      {/* END: FloatingAtmosphere */}

      {/* BEGIN: NavigationBar */}
      <header className="sticky top-0 z-50 backdrop-blur-md bg-white/75 border-b border-slate-200/70 transition-all">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-20 flex items-center justify-between">
          {/* Brand Logo */}
          <Link aria-label="VACHAN VoiceGuard Home" className="flex items-center gap-3 group focus:outline-none" to="/">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-brand-700 via-brand-600 to-sky-400 flex items-center justify-center text-white shadow-md shadow-brand-600/25 group-hover:scale-105 transition-transform duration-200">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.2" viewBox="0 0 24 24">
                <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path>
                <path d="m9 12 2 2 4-4"></path>
              </svg>
            </div>
            <div className="flex flex-col">
              <div className="flex items-center gap-2">
                <span className="font-extrabold text-xl tracking-tight text-navy-900">VACHAN</span>
                <span className="text-xs font-semibold uppercase tracking-wider px-2 py-0.5 rounded-full bg-blue-50 text-brand-700 border border-blue-200/60">VoiceGuard</span>
              </div>
              <span className="text-[10px] font-medium tracking-wide text-slate-500 uppercase -mt-0.5">AI Policy Assurance</span>
            </div>
          </Link>

          {/* Desktop Navigation Links */}
          <nav className="hidden md:flex items-center gap-8 text-sm font-medium text-slate-600">
            <a className="hover:text-brand-600 transition-colors" href="#browser-demo">Product</a>
            <a className="hover:text-brand-600 transition-colors" href="#how-it-works">How It Works</a>
            <a className="hover:text-brand-600 transition-colors" href="#trust">Trust &amp; Security</a>
            <Link className="hover:text-brand-600 transition-colors" to="/dashboard">Audit Console</Link>
          </nav>

          {/* Action Buttons */}
          <div className="flex items-center gap-3">
            <Link className="text-sm font-semibold text-slate-700 hover:text-brand-700 px-3 py-2 transition-colors" to="/login">
              Sign In
            </Link>
            <Link className="inline-flex items-center justify-center px-4 sm:px-5 py-2.5 rounded-full text-sm font-semibold text-white bg-gradient-to-r from-brand-700 to-brand-500 hover:from-brand-800 hover:to-brand-600 shadow-md shadow-brand-700/20 hover:shadow-brand-700/30 transition-all duration-200 active:scale-98" to="/login">
              Get Started
              <svg className="w-4 h-4 ml-1.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path d="M13.5 4.5L21 12m0 0l-7.5 7.5M21 12H3" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2"></path>
              </svg>
            </Link>
          </div>
        </div>
      </header>
      {/* END: NavigationBar */}

      <main>
        {/* BEGIN: HeroSection */}
        <section className="relative pt-12 pb-20 lg:pt-20 lg:pb-32 px-4 sm:px-6 lg:px-8">
          <div className="max-w-5xl mx-auto text-center">
            {/* Live Badge */}
            <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-white/90 border border-blue-200 shadow-sm text-xs font-semibold text-brand-700 mb-8 backdrop-blur-sm">
              <span className="flex h-2 w-2 rounded-full bg-emerald-500 animate-pulse"></span>
              <span>Next-Gen Policy Transparency &amp; Voice Audit</span>
            </div>
            {/* Main Headline */}
            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold text-navy-900 tracking-tight leading-[1.12]">
              Insurance You Can Trust. <br className="hidden sm:inline"/>
              <span className="bg-clip-text text-transparent bg-gradient-to-r from-brand-700 via-brand-600 to-sky-500">
                Decisions You Can Verify.
              </span>
            </h1>
            {/* Subtitle */}
            <p className="mt-6 text-lg sm:text-xl text-slate-600 max-w-2xl mx-auto font-normal leading-relaxed">
              Verify what you were promised during enrollment, audit complex clauses against spoken audio, and follow claim adjudications with deterministic cryptographic proof.
            </p>
            {/* CTA Action Group */}
            <div className="mt-8 flex flex-col sm:flex-row items-center justify-center gap-3.5">
              <a className="w-full sm:w-auto inline-flex items-center justify-center px-7 py-3.5 rounded-full text-base font-semibold text-white bg-navy-900 hover:bg-navy-800 shadow-lg shadow-navy-900/15 hover:shadow-xl hover:shadow-navy-900/25 transition-all" href="#browser-demo">
                Explore the Platform
                <svg className="w-4 h-4 ml-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path d="M14 5l7 7m0 0l-7 7m7-7H3" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.2"></path>
                </svg>
              </a>
              <Link className="w-full sm:w-auto inline-flex items-center justify-center px-6 py-3.5 rounded-full text-base font-semibold text-slate-700 bg-white/80 hover:bg-white border border-slate-300/80 shadow-sm hover:shadow transition-all" to="/login">
                Sign In with Policy ID
              </Link>
            </div>
            {/* Trust Mini Counter Metrics */}
            <div className="mt-12 pt-8 border-t border-slate-200/60 max-w-3xl mx-auto grid grid-cols-2 md:grid-cols-4 gap-6 text-left">
              <div>
                <div className="text-2xl font-bold text-navy-900 tracking-tight">99.8%</div>
                <div className="text-xs font-medium text-slate-500 mt-0.5">Clause Match Accuracy</div>
              </div>
              <div>
                <div className="text-2xl font-bold text-navy-900 tracking-tight">&lt; 3 Sec</div>
                <div className="text-xs font-medium text-slate-500 mt-0.5">Deterministic Audit Proof</div>
              </div>
              <div>
                <div className="text-2xl font-bold text-navy-900 tracking-tight">₹42.8 Cr+</div>
                <div className="text-xs font-medium text-slate-500 mt-0.5">Claims Verified</div>
              </div>
              <div>
                <div className="text-2xl font-bold text-navy-900 tracking-tight">SHA-256</div>
                <div className="text-xs font-medium text-slate-500 mt-0.5">Immutable Evidence Logs</div>
              </div>
            </div>
          </div>

          {/* BEGIN: HeroVisualMockup (1:1 from landing_page_stich/code.html) */}
          <div className="mt-14 max-w-6xl mx-auto" id="browser-demo">
            <div className="bg-white rounded-2xl shadow-browser border border-slate-200/90 overflow-hidden transform transition duration-500">
              {/* Mockup Window Bar */}
              <div className="bg-slate-100/90 border-b border-slate-200 px-4 py-3 flex items-center justify-between gap-4">
                <div className="flex items-center gap-2">
                  <span className="w-3 h-3 rounded-full bg-rose-400/90 inline-block"></span>
                  <span className="w-3 h-3 rounded-full bg-amber-400/90 inline-block"></span>
                  <span className="w-3 h-3 rounded-full bg-emerald-400/90 inline-block"></span>
                </div>
                {/* URL Bar */}
                <div className="flex-1 max-w-md mx-auto bg-white border border-slate-200 rounded-lg px-3 py-1 flex items-center gap-2 text-xs font-mono text-slate-600 shadow-sm">
                  <svg className="w-3.5 h-3.5 text-emerald-600 shrink-0" fill="currentColor" viewBox="0 0 20 20">
                    <path clipRule="evenodd" d="M10 1a4.5 4.5 0 00-4.5 4.5V9H5a2 2 0 00-2 2v6a2 2 0 002 2h10a2 2 0 002-2v-6a2 2 0 00-2-2h-.5V5.5A4.5 4.5 0 0010 1zm3 8V5.5a3 3 0 10-6 0V9h6z" fillRule="evenodd"></path>
                  </svg>
                  <span className="truncate">https://vachan.guard/audit/POL-8829-PROMISE-VERIFY</span>
                  <span className="ml-auto text-[10px] bg-slate-100 text-slate-600 px-1.5 py-0.5 rounded font-sans">LIVE AUDIT</span>
                </div>
                {/* Mock Actions */}
                <div className="flex items-center gap-2 text-slate-400">
                  <span className="text-xs font-mono text-slate-500">v2.4.0-verified</span>
                </div>
              </div>

              {/* Mockup Interior Dashboard */}
              <div className="bg-slate-50/70 p-4 sm:p-6 lg:p-8">
                {/* Dashboard Top Meta Ribbon */}
                <div className="bg-white rounded-xl p-4 border border-slate-200/80 shadow-sm mb-6 flex flex-wrap items-center justify-between gap-4">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-lg bg-blue-50 text-brand-600 flex items-center justify-center font-bold">
                      🚗
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-navy-900 text-sm sm:text-base">HDFC ERGO Comprehensive Auto</span>
                        <span className="bg-emerald-50 text-emerald-700 text-[11px] font-semibold px-2 py-0.5 rounded-full border border-emerald-200">Active</span>
                      </div>
                      <p className="text-xs font-mono text-slate-500">Policy #VG-9402-CAR • Insured ID: KA-01-MJ-8821</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-4 text-right">
                    <div className="hidden sm:block">
                      <span className="text-[11px] uppercase tracking-wider text-slate-400 font-semibold block">Total Coverage</span>
                      <span className="text-sm font-bold text-navy-900">₹15,00,000 IDV</span>
                    </div>
                    <div className="border-l border-slate-200 pl-4">
                      <span className="text-[11px] uppercase tracking-wider text-emerald-600 font-bold block flex items-center gap-1 justify-end">
                        <span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span> Validated Proof
                      </span>
                      <span className="text-xs font-mono text-slate-600 bg-slate-100 px-2 py-0.5 rounded inline-block mt-0.5">sha256:7f8a9...b401e</span>
                    </div>
                  </div>
                </div>

                {/* Core Dual Comparison Grid */}
                <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
                  {/* Left 8 Cols: The Spoken vs Written Verification View */}
                  <div className="lg:col-span-8 space-y-5">
                    <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm">
                      <div className="flex items-center justify-between pb-3 border-b border-slate-100 mb-4">
                        <div className="flex items-center gap-2">
                          <span className="w-2.5 h-2.5 rounded-full bg-blue-600"></span>
                          <h2 className="text-sm font-bold text-navy-900 uppercase tracking-wide">Promise Audit: Spoken Call vs Underwritten Contract</h2>
                        </div>
                        <span className="text-xs font-semibold text-emerald-700 bg-emerald-50 px-2.5 py-1 rounded-full border border-emerald-200 flex items-center gap-1">
                          <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path d="M5 13l4 4L19 7" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5"></path></svg>
                          Verified Match (99.4%)
                        </span>
                      </div>

                      {/* Audio Call Recording Snippet */}
                      <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200/70 mb-4">
                        <div className="flex items-center justify-between mb-2">
                          <div className="flex items-center gap-2 text-xs font-medium text-slate-700">
                            <span className="p-1 rounded bg-blue-100 text-brand-700">
                              <svg className="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 20 20"><path d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zM7 8a1 1 0 012 0v4a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v4a1 1 0 102 0V8a1 1 0 00-1-1z"></path></svg>
                            </span>
                            <span>Agent Tele-Sales Recording • Timestamp 04:12</span>
                          </div>
                          <div className="flex items-center gap-1 text-[11px] font-mono text-slate-500">
                            <span>04:12 / 07:45</span>
                          </div>
                        </div>

                        {/* Simulated Audio Waveform */}
                        <div className="h-6 flex items-center gap-1 px-1 bg-white rounded border border-slate-200/80 mb-3">
                          <div className="w-1 bg-brand-500 rounded-full audio-bar"></div>
                          <div className="w-1 bg-brand-500 rounded-full audio-bar"></div>
                          <div className="w-1 bg-brand-400 rounded-full audio-bar"></div>
                          <div className="w-1 bg-brand-600 rounded-full audio-bar"></div>
                          <div className="w-1 bg-brand-300 rounded-full audio-bar"></div>
                          <div className="w-1 bg-brand-500 rounded-full audio-bar"></div>
                          <div className="w-1 bg-brand-400 rounded-full h-2"></div>
                          <div className="w-1 bg-slate-300 rounded-full h-1.5"></div>
                          <div className="w-1 bg-slate-300 rounded-full h-3"></div>
                          <div className="w-1 bg-slate-300 rounded-full h-1"></div>
                          <div className="w-1 bg-slate-300 rounded-full h-4"></div>
                          <div className="w-1 bg-slate-300 rounded-full h-2"></div>
                        </div>

                        <div className="text-xs sm:text-sm text-navy-900 font-medium italic pl-3 border-l-2 border-brand-500">
                          "Yes sir, cashless garage repair is covered up to 100% within 2 hours across all our authorized multi-brand service centers, without mandatory salvage deductions."
                        </div>
                      </div>

                      {/* Downward Flow Connector */}
                      <div className="flex justify-center my-2">
                        <div className="bg-blue-50 text-brand-600 text-xs font-semibold px-3 py-1 rounded-full border border-blue-200 flex items-center gap-1">
                          <span>Mapped to Legal Contract Clause</span>
                          <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path d="M19 14l-7 7m0 0l-7-7m7 7V3" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2"></path></svg>
                        </div>
                      </div>

                      {/* Policy Clause Written Equivalent */}
                      <div className="p-3.5 rounded-xl bg-emerald-50/50 border border-emerald-200">
                        <div className="flex items-center justify-between mb-1.5">
                          <span className="text-xs font-bold text-emerald-900 font-mono">CLAUSE SECTION 14.B • CASHLESS PRIVILEGE</span>
                          <span className="text-[10px] font-semibold text-emerald-700 uppercase bg-emerald-100 px-2 py-0.5 rounded">Deterministic Match</span>
                        </div>
                        <p className="text-xs text-slate-700 leading-relaxed font-normal">
                          "The Insurer guarantees direct cashless settlement with 4,500+ authorized repair hubs. Zero deductible applies to standard labor and replacement parts provided intimation occurs within 24 hours of loss."
                        </p>
                      </div>
                    </div>

                    {/* Secondary Sub-Audit Card */}
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                      <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex flex-col justify-between">
                        <div>
                          <div className="flex items-center justify-between text-xs text-slate-500 mb-1">
                            <span>Consensus Audit</span>
                            <span className="text-emerald-600 font-semibold font-mono">0 Ambiguities</span>
                          </div>
                          <div className="text-sm font-bold text-navy-900">Zero Hidden Depreciation</div>
                          <p className="text-xs text-slate-500 mt-1">Bumper-to-bumper bumper replacement endorsed under Add-on Pack 03.</p>
                        </div>
                        <div className="mt-3 pt-2 border-t border-slate-100 flex items-center justify-between text-[11px]">
                          <span className="text-slate-400">Add-on Endorsement #4</span>
                          <span className="text-emerald-700 font-medium">✓ Fully Covered</span>
                        </div>
                      </div>

                      <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex flex-col justify-between">
                        <div>
                          <div className="flex items-center justify-between text-xs text-slate-500 mb-1">
                            <span>Intimation SLA</span>
                            <span className="text-blue-600 font-semibold font-mono">Instant Priority</span>
                          </div>
                          <div className="text-sm font-bold text-navy-900">Turnaround Commitment</div>
                          <p className="text-xs text-slate-500 mt-1">Surveyor dispatched digitally within 45 minutes of automated app report.</p>
                        </div>
                        <div className="mt-3 pt-2 border-t border-slate-100 flex items-center justify-between text-[11px]">
                          <span className="text-slate-400">Guaranteed Max Time</span>
                          <span className="text-brand-700 font-medium">120 Minutes</span>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Right 4 Cols: Live Claim Adjudication Tracker & Fingerprint Details */}
                  <div className="lg:col-span-4 space-y-5">
                    {/* Live Claim Tracking Box */}
                    <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm">
                      <div className="flex items-center justify-between mb-4">
                        <span className="text-xs font-bold uppercase tracking-wider text-slate-500">Live Claim Journey</span>
                        <span className="text-[11px] font-mono bg-blue-50 text-brand-700 px-2 py-0.5 rounded border border-blue-200">#CLM-8921-24</span>
                      </div>
                      <div className="mb-4">
                        <div className="text-base font-bold text-navy-900">Front Bumper &amp; Grille Repair</div>
                        <div className="text-xs text-slate-500 mt-0.5">Authorized Service Station: Trident Auto</div>
                      </div>

                      {/* Claim Status Timeline */}
                      <div className="space-y-4 relative pl-5 before:content-[''] before:absolute before:left-1.5 before:top-1.5 before:bottom-1.5 before:w-0.5 before:bg-slate-200">
                        <div className="relative">
                          <span className="absolute -left-5 top-1 w-2.5 h-2.5 rounded-full bg-emerald-500 ring-4 ring-emerald-50"></span>
                          <div className="text-xs font-bold text-navy-900">Voice Promise Verification</div>
                          <p className="text-[11px] text-slate-500">Agent recorded commitment validated against Clause 14.B.</p>
                        </div>
                        <div className="relative">
                          <span className="absolute -left-5 top-1 w-2.5 h-2.5 rounded-full bg-emerald-500 ring-4 ring-emerald-50"></span>
                          <div className="text-xs font-bold text-navy-900">Crypto Fingerprint Logged</div>
                          <p className="text-[11px] text-slate-500 font-mono">hash: 9d83...10ff (Signed)</p>
                        </div>
                        <div className="relative">
                          <span className="absolute -left-5 top-1 w-2.5 h-2.5 rounded-full bg-brand-500 ring-4 ring-brand-50 animate-pulse"></span>
                          <div className="text-xs font-bold text-brand-700">Instant Cashless Payout Approved</div>
                          <p className="text-[11px] text-slate-500">Approved amount: <span className="font-semibold text-navy-900">₹32,450</span> (No salvage fee)</p>
                        </div>
                      </div>

                      {/* Action CTA inside Card */}
                      <div className="mt-6 pt-4 border-t border-slate-100">
                        <Link to="/dashboard" className="w-full py-2.5 rounded-lg bg-brand-600 hover:bg-brand-700 text-white text-xs font-semibold shadow-sm transition-colors flex items-center justify-center gap-1.5">
                          <span>Open Full Workbench</span>
                          <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path d="M14 5l7 7m0 0l-7 7m7-7H3" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2"></path></svg>
                        </Link>
                      </div>
                    </div>

                    {/* Proof of Integrity Badge */}
                    <div className="bg-gradient-to-br from-navy-900 to-navy-800 rounded-xl p-4 text-white shadow-md">
                      <div className="flex items-center gap-2 mb-2">
                        <svg className="w-4 h-4 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5"></path></svg>
                        <span className="text-xs font-bold uppercase tracking-wider text-slate-200">Tamper-Proof Ledger</span>
                      </div>
                      <p className="text-[11px] text-slate-300 leading-relaxed">
                        Every promise and adjudication is sealed cryptographically before reaching underwriters. No retroactive policy edits possible.
                      </p>
                      <div className="mt-3 flex items-center justify-between text-[10px] text-slate-400 font-mono">
                        <span>BLOCK: #820,491</span>
                        <span className="text-emerald-400">IMMUTABLE</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
          {/* END: HeroVisualMockup */}
        </section>
        {/* END: HeroSection */}

        {/* BEGIN: HowItWorks (1:1 from landing_page_stich/code.html) */}
        <section className="py-20 lg:py-28 bg-white/70 border-y border-slate-200/80 backdrop-blur-sm" id="how-it-works">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="text-center max-w-3xl mx-auto mb-16">
              <span className="text-xs font-bold uppercase tracking-wider text-brand-600 bg-blue-50 px-3 py-1 rounded-full border border-blue-200/80">
                Engineered For Clarity
              </span>
              <h2 className="text-3xl sm:text-4xl font-extrabold text-navy-900 tracking-tight mt-3">
                Three Steps to Total Policy Assurance
              </h2>
              <p className="mt-4 text-base sm:text-lg text-slate-600">
                Eliminate conflicting oral promises, confusing exclusions, and opaque claims processing with our verifiable audit architecture.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
              {/* Card 1 */}
              <div className="bg-white rounded-2xl p-7 border border-slate-200/90 shadow-card-glass hover:shadow-card-elevated hover:border-blue-200 transition-all duration-300 flex flex-col justify-between group">
                <div>
                  <div className="w-12 h-12 rounded-xl bg-blue-50 text-brand-600 flex items-center justify-center font-bold text-lg mb-6 group-hover:scale-110 group-hover:bg-brand-600 group-hover:text-white transition-all">
                    01
                  </div>
                  <h3 className="text-xl font-bold text-navy-900 mb-2 group-hover:text-brand-600 transition-colors">
                    Verify Spoken Promises
                  </h3>
                  <p className="text-sm text-slate-600 leading-relaxed mb-6">
                    Directly cross-reference tele-sales enrollment audio with the underwritten policy wording. Flags mismatches in co-pays, deductibles, and network coverage before purchase.
                  </p>
                </div>
                <div className="pt-4 border-t border-slate-100 flex items-center text-xs font-semibold text-brand-600 group-hover:translate-x-1 transition-transform">
                  <span>Automatic Audio-to-Clause Map</span>
                  <svg className="w-4 h-4 ml-1" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path d="M9 5l7 7-7 7" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2"></path></svg>
                </div>
              </div>

              {/* Card 2 */}
              <div className="bg-white rounded-2xl p-7 border border-slate-200/90 shadow-card-glass hover:shadow-card-elevated hover:border-blue-200 transition-all duration-300 flex flex-col justify-between group">
                <div>
                  <div className="w-12 h-12 rounded-xl bg-blue-50 text-brand-600 flex items-center justify-center font-bold text-lg mb-6 group-hover:scale-110 group-hover:bg-brand-600 group-hover:text-white transition-all">
                    02
                  </div>
                  <h3 className="text-xl font-bold text-navy-900 mb-2 group-hover:text-brand-600 transition-colors">
                    Submit &amp; Track Claims
                  </h3>
                  <p className="text-sm text-slate-600 leading-relaxed mb-6">
                    Streamline incident reports with browser-side SHA-256 fingerprinting. Every invoice, survey photo, and repair estimate is stamped with indelible timestamps.
                  </p>
                </div>
                <div className="pt-4 border-t border-slate-100 flex items-center text-xs font-semibold text-brand-600 group-hover:translate-x-1 transition-transform">
                  <span>Cryptographic Timestamping</span>
                  <svg className="w-4 h-4 ml-1" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path d="M9 5l7 7-7 7" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2"></path></svg>
                </div>
              </div>

              {/* Card 3 */}
              <div className="bg-white rounded-2xl p-7 border border-slate-200/90 shadow-card-glass hover:shadow-card-elevated hover:border-blue-200 transition-all duration-300 flex flex-col justify-between group">
                <div>
                  <div className="w-12 h-12 rounded-xl bg-blue-50 text-brand-600 flex items-center justify-center font-bold text-lg mb-6 group-hover:scale-110 group-hover:bg-brand-600 group-hover:text-white transition-all">
                    03
                  </div>
                  <h3 className="text-xl font-bold text-navy-900 mb-2 group-hover:text-brand-600 transition-colors">
                    Transparent Decisions
                  </h3>
                  <p className="text-sm text-slate-600 leading-relaxed mb-6">
                    Receive plain-English justifications for approved sums or deductions with direct citations to the policy handbook and original spoken agent commitments.
                  </p>
                </div>
                <div className="pt-4 border-t border-slate-100 flex items-center text-xs font-semibold text-brand-600 group-hover:translate-x-1 transition-transform">
                  <span>Deterministic Audit Proofs</span>
                  <svg className="w-4 h-4 ml-1" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path d="M9 5l7 7-7 7" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2"></path></svg>
                </div>
              </div>
            </div>
          </div>
        </section>
        {/* END: HowItWorks */}

        {/* BEGIN: TrustAndSecurity (1:1 from landing_page_stich/code.html) */}
        <section className="py-20 lg:py-28 bg-navy-950 text-white relative overflow-hidden" id="trust">
          <div className="absolute -top-40 -right-40 w-96 h-96 bg-brand-600/20 rounded-full blur-3xl pointer-events-none"></div>
          <div className="absolute -bottom-40 -left-40 w-96 h-96 bg-sky-500/10 rounded-full blur-3xl pointer-events-none"></div>
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
            <div className="max-w-3xl mx-auto text-center mb-16">
              <span className="text-xs font-mono uppercase tracking-widest text-sky-400 bg-sky-950/80 px-3 py-1 rounded-full border border-sky-800">
                Deterministic Security Protocol
              </span>
              <h2 className="text-3xl sm:text-4xl font-extrabold tracking-tight mt-4 text-white">
                Built on Verifiable Cryptographic Integrity
              </h2>
              <p className="mt-4 text-slate-400 text-base sm:text-lg">
                VACHAN VoiceGuard removes speculation. We create mathematical certainty between customer statements and insurer policy commitments.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
              {/* Pillar 1 */}
              <div className="bg-navy-900/90 rounded-2xl p-7 border border-slate-800 hover:border-brand-500/50 transition-colors">
                <div className="w-10 h-10 rounded-lg bg-brand-900/60 text-brand-400 flex items-center justify-center mb-5 border border-brand-700/50">
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2"></path>
                  </svg>
                </div>
                <h3 className="text-lg font-bold text-white mb-2">Verifiable Clause Mapping</h3>
                <p className="text-sm text-slate-400 leading-relaxed">
                  Every decision cites precise paragraph numbers and addendum riders from the filed regulatory policy documents, not opaque algorithmic scores.
                </p>
              </div>

              {/* Pillar 2 */}
              <div className="bg-navy-900/90 rounded-2xl p-7 border border-slate-800 hover:border-brand-500/50 transition-colors">
                <div className="w-10 h-10 rounded-lg bg-brand-900/60 text-brand-400 flex items-center justify-center mb-5 border border-brand-700/50">
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2"></path>
                  </svg>
                </div>
                <h3 className="text-lg font-bold text-white mb-2">Evidence Integrity &amp; Hashing</h3>
                <p className="text-sm text-slate-400 leading-relaxed">
                  Customer voice recordings and repair documentation are fingerprinted via browser-side SHA-256 before transmission, preventing post-facto alteration.
                </p>
              </div>

              {/* Pillar 3 */}
              <div className="bg-navy-900/90 rounded-2xl p-7 border border-slate-800 hover:border-brand-500/50 transition-colors">
                <div className="w-10 h-10 rounded-lg bg-brand-900/60 text-brand-400 flex items-center justify-center mb-5 border border-brand-700/50">
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path d="M13 10V3L4 14h7v7l9-11h-7z" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2"></path>
                  </svg>
                </div>
                <h3 className="text-lg font-bold text-white mb-2">Tamper-Evident Audit History</h3>
                <p className="text-sm text-slate-400 leading-relaxed">
                  Every status revision, agent affirmation, and assessor adjustment is stored on an append-only verifiable ledger accessible to policyholders anytime.
                </p>
              </div>
            </div>

            {/* Compliance Banner */}
            <div className="mt-12 p-4 rounded-xl bg-navy-900/60 border border-slate-800 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-slate-400">
              <div className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-sky-400"></span>
                <span>Deterministic Policy Audit Framework. AI flags act as review signals adhering to IRDAI guidelines.</span>
              </div>
              <div className="font-mono text-slate-500">ISO 27001 &amp; SOC-2 Type II Compliant Architecture</div>
            </div>
          </div>
        </section>
        {/* END: TrustAndSecurity */}

        {/* BEGIN: CallToAction */}
        <section className="py-20 lg:py-24 px-4 sm:px-6 lg:px-8">
          <div className="max-w-5xl mx-auto">
            <div className="bg-gradient-to-br from-brand-700 via-brand-600 to-sky-600 rounded-3xl p-8 sm:p-12 lg:p-16 text-center text-white shadow-2xl shadow-brand-700/25 relative overflow-hidden">
              <div className="absolute -top-24 -left-24 w-64 h-64 rounded-full bg-white/10 pointer-events-none"></div>
              <div className="absolute -bottom-24 -right-24 w-64 h-64 rounded-full bg-white/10 pointer-events-none"></div>
              <span className="inline-block px-3.5 py-1 rounded-full bg-white/20 text-xs font-semibold uppercase tracking-wider backdrop-blur-sm mb-4">
                Zero Ambiguity Guarantee
              </span>
              <h2 className="text-3xl sm:text-4xl lg:text-5xl font-extrabold tracking-tight max-w-2xl mx-auto leading-tight">
                Ready to eliminate ambiguity in policy coverage?
              </h2>
              <p className="mt-4 text-base sm:text-lg text-blue-100 max-w-xl mx-auto font-normal">
                Verify your ongoing policy today, or connect with our assurance specialists for an instant policy health report.
              </p>
              <div className="mt-8 flex flex-col sm:flex-row items-center justify-center gap-4">
                <Link className="w-full sm:w-auto px-8 py-3.5 rounded-full font-bold text-navy-900 bg-white hover:bg-slate-100 shadow-md hover:shadow-lg transition-all text-sm" to="/login">
                  Get Started with VoiceGuard
                </Link>
                <Link className="w-full sm:w-auto px-7 py-3.5 rounded-full font-semibold text-white bg-brand-800/60 hover:bg-brand-800 border border-white/25 backdrop-blur-sm transition-all text-sm" to="/dashboard">
                  Launch Enterprise Demo
                </Link>
              </div>
            </div>
          </div>
        </section>
        {/* END: CallToAction */}
      </main>

      {/* BEGIN: MainFooter (1:1 from landing_page_stich/code.html) */}
      <footer className="bg-white border-t border-slate-200 pt-16 pb-12 text-slate-600 text-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 md:grid-cols-5 gap-10 pb-12 border-b border-slate-200">
            {/* Col 1: Brand Info */}
            <div className="md:col-span-2 space-y-4">
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-lg bg-brand-700 flex items-center justify-center text-white font-bold">
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2"></path></svg>
                </div>
                <span className="font-extrabold text-navy-900 tracking-tight text-lg">VACHAN VoiceGuard</span>
              </div>
              <p className="text-xs text-slate-500 max-w-sm leading-relaxed">
                Pioneering verifiable consumer assurance in general insurance. We audit verbal pledges against underwritten contracts with immutable proofs.
              </p>
              <div className="text-[11px] font-mono text-slate-400">
                Audit Protocol v2.4 • SHA-256 Ledger Enabled
              </div>
            </div>
            {/* Col 2 */}
            <div>
              <h4 className="text-xs font-bold uppercase tracking-wider text-navy-900 mb-3">Product</h4>
              <ul className="space-y-2 text-xs">
                <li><a className="hover:text-brand-600 transition-colors" href="#how-it-works">Voice Audit Engine</a></li>
                <li><a className="hover:text-brand-600 transition-colors" href="#browser-demo">Clause Matcher</a></li>
                <li><a className="hover:text-brand-600 transition-colors" href="#browser-demo">Claims Transparency</a></li>
                <li><Link className="hover:text-brand-600 transition-colors" to="/dashboard">Enterprise Console</Link></li>
              </ul>
            </div>
            {/* Col 3 */}
            <div>
              <h4 className="text-xs font-bold uppercase tracking-wider text-navy-900 mb-3">Security &amp; Trust</h4>
              <ul className="space-y-2 text-xs">
                <li><a className="hover:text-brand-600 transition-colors" href="#trust">Cryptographic Proofs</a></li>
                <li><a className="hover:text-brand-600 transition-colors" href="#trust">Data Privacy Policy</a></li>
                <li><a className="hover:text-brand-600 transition-colors" href="#trust">Regulatory Compliance</a></li>
                <li><a className="hover:text-brand-600 transition-colors" href="#trust">Security Whitepaper</a></li>
              </ul>
            </div>
            {/* Col 4 */}
            <div>
              <h4 className="text-xs font-bold uppercase tracking-wider text-navy-900 mb-3">Account</h4>
              <ul className="space-y-2 text-xs">
                <li><Link className="hover:text-brand-600 transition-colors" to="/login">Policyholder Sign In</Link></li>
                <li><Link className="hover:text-brand-600 transition-colors" to="/login">Broker Portal</Link></li>
                <li><Link className="hover:text-brand-600 transition-colors" to="/login">Grievance Redressal</Link></li>
                <li><Link className="hover:text-brand-600 transition-colors" to="/login">Contact Support</Link></li>
              </ul>
            </div>
          </div>
          {/* Disclaimer */}
          <div className="pt-8 flex flex-col md:flex-row items-center justify-between gap-4 text-xs text-slate-500">
            <div>
              © 2026 VACHAN VoiceGuard Assurance Technologies Inc. All rights reserved.
            </div>
            <div className="text-[11px] text-slate-400 text-center md:text-right">
              Disclaimer: VACHAN VoiceGuard acts as an independent verifiable audit software. Decisions are governed by original underwriter terms.
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
};
