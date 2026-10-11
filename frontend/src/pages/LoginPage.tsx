import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { UserRole } from '../types';

export const LoginPage: React.FC = () => {
  const { login, signup } = useAuth();
  const navigate = useNavigate();

  // Mode: 'signin' | 'signup'
  const [mode, setMode] = useState<'signin' | 'signup'>('signin');

  // Roles for Sign In: 'customer' | 'agent' | 'claims'
  const [selectedRole, setSelectedRole] = useState<'customer' | 'agent' | 'claims'>('customer');
  const [email, setEmail] = useState('customer@vachan.in');
  const [password, setPassword] = useState('password123');
  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(true);
  const [isLoading, setIsLoading] = useState(false);
  const [toastMessage, setToastMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Sign Up state
  const [fullName, setFullName] = useState('');
  const [phone, setPhone] = useState('+91 ');
  const [signupRole, setSignupRole] = useState<UserRole>('CUSTOMER');

  const handleRoleSelect = (roleKey: 'customer' | 'agent' | 'claims') => {
    setSelectedRole(roleKey);
    setErrorMessage(null);
    if (roleKey === 'customer') {
      setEmail('customer@vachan.in');
      setPassword('password123');
    } else if (roleKey === 'agent') {
      setEmail('agent@vachan.in');
      setPassword('password123');
    } else {
      setEmail('authority@vachan.gov.in');
      setPassword('password123');
    }
  };

  const showToast = (msg: string) => {
    setToastMessage(msg);
    setTimeout(() => setToastMessage(null), 4000);
  };

  const handleFormSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setErrorMessage(null);

    try {
      if (mode === 'signin') {
        showToast(`Authenticating against Neon PostgreSQL...`);
        await login(email, password);
        showToast('Login successful! Redirecting to workspace...');
        navigate('/dashboard');
      } else {
        showToast(`Registering account and dispatching credentials email...`);
        await signup({
          email,
          password,
          full_name: fullName,
          phone,
          role: signupRole,
        });
        showToast('Account created & credentials email sent! Redirecting...');
        navigate('/dashboard');
      }
    } catch (err: any) {
      const msg = err?.response?.data?.detail || err?.response?.data?.message || err?.message || 'Authentication error';
      setErrorMessage(typeof msg === 'string' ? msg : JSON.stringify(msg));
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="h-full text-slate-800 antialiased selection:bg-brand-500 selection:text-white bg-slate-50 font-sans min-h-screen">
      {/* Toast Notification */}
      {toastMessage && (
        <div className="fixed top-5 right-5 z-50 transform transition-all duration-300">
          <div className="flex items-center gap-3 bg-navy-900 text-white px-5 py-3.5 rounded-xl shadow-xl border border-slate-700">
            <div className="w-2 h-2 rounded-full bg-emerald-400 animate-ping"></div>
            <p className="text-sm font-medium">{toastMessage}</p>
          </div>
        </div>
      )}

      <main className="min-h-screen flex flex-col lg:flex-row overflow-x-hidden">
        {/* BEGIN: LeftColumnBrandAtmosphere (1:1 from login_tab_stitch/code.html) */}
        <section className="lg:w-1/2 relative bg-gradient-to-br from-[#eef4ff] via-[#f4f7fe] to-[#faf8ff] p-8 lg:p-14 flex flex-col justify-between border-b lg:border-b-0 lg:border-r border-slate-200/80 ambient-glow overflow-hidden">
          {/* Top Bar: Navigation & Brand Header */}
          <div className="relative z-10">
            <div className="flex items-center justify-between">
              {/* Back Link */}
              <Link
                to="/"
                className="inline-flex items-center gap-1.5 text-xs font-semibold tracking-wide text-slate-500 hover:text-brand-600 transition-colors py-1.5 px-3 rounded-lg hover:bg-white/60"
              >
                <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path d="M10 19l-7-7m0 0l7-7m-7 7h18" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.2"></path>
                </svg>
                Back to Home
              </Link>
              {/* Minor Security Micro-indicator */}
              <div className="flex items-center gap-1.5 text-[11px] font-medium text-slate-400 bg-white/70 backdrop-blur-sm px-2.5 py-1 rounded-full border border-slate-200/60">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
                System Live • TLS 1.3
              </div>
            </div>

            {/* Logo & Wordmark */}
            <div className="mt-8 flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-brand-600 text-white flex items-center justify-center shadow-md shadow-brand-500/20">
                <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.2" viewBox="0 0 24 24">
                  <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path>
                  <path d="m9 12 2 2 4-4"></path>
                </svg>
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-xl font-bold tracking-tight text-navy-900">VACHAN</span>
                  <span className="inline-flex items-center px-2 py-0.5 rounded-md text-[11px] font-semibold bg-brand-100/70 text-brand-700 tracking-wide border border-brand-200/50">
                    VoiceGuard
                  </span>
                </div>
                <p className="text-[10px] uppercase font-bold tracking-widest text-slate-400">AI Policy Assurance</p>
              </div>
            </div>
          </div>

          {/* Mid Content: Headline, Editorial Copy & Mockup Visualizer */}
          <div className="relative z-10 my-10 lg:my-0 max-w-lg">
            <h1 className="text-3xl lg:text-4xl font-extrabold text-navy-900 tracking-tight leading-tight">
              Deterministic Policy Verification &amp; Audit.
            </h1>
            <p className="mt-3.5 text-sm lg:text-base text-slate-600 leading-relaxed font-normal">
              Reconciling spoken promises against underwritten clauses with cryptographic precision and verifiable speech signatures.
            </p>

            {/* Dynamic Glassmorphic Verification Mockup Card */}
            <div className="mt-8 bg-white/85 backdrop-blur-md rounded-2xl p-5 border border-white/80 shadow-card transition-transform duration-300 hover:translate-y-[-2px]">
              {/* Card Top Row */}
              <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                <div className="flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-brand-600"></span>
                  <span className="text-xs font-bold text-navy-900 tracking-tight">Policy #VG-9402</span>
                  <span className="text-[11px] text-slate-400">• Active Tier-1</span>
                </div>
                <span className="px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider rounded-md bg-emerald-50 text-emerald-700 border border-emerald-200">
                  Verified
                </span>
              </div>

              {/* Card Middle: Waveform Audio Visualizer Snippet */}
              <div className="mt-3.5 flex items-center justify-between bg-slate-50/90 rounded-xl p-3 border border-slate-100">
                <div className="flex items-center gap-2.5">
                  <button aria-label="Play sample snippet" className="w-7 h-7 rounded-full bg-brand-600 text-white flex items-center justify-center hover:bg-brand-700 transition" type="button">
                    <svg className="w-3 h-3 fill-current ml-0.5" viewBox="0 0 24 24"><path d="M8 5v14l11-7z"></path></svg>
                  </button>
                  <div>
                    <p className="text-xs font-semibold text-navy-900">Tele-Sale Call Recording</p>
                    <p className="text-[10px] text-slate-400">Timestamp: 03:42 • 48kHz FLAC</p>
                  </div>
                </div>

                {/* Stylized Waveform Bars */}
                <div aria-hidden="true" className="flex items-end gap-1 h-5 px-1">
                  <span className="w-1 bg-brand-200 rounded-full h-2"></span>
                  <span className="w-1 bg-brand-400 rounded-full h-4"></span>
                  <span className="w-1 bg-brand-600 rounded-full h-5"></span>
                  <span className="w-1 bg-brand-500 rounded-full h-3"></span>
                  <span className="w-1 bg-brand-300 rounded-full h-4"></span>
                  <span className="w-1 bg-brand-600 rounded-full h-2"></span>
                </div>
              </div>

              {/* Card Bottom: Semantic Clause Reconcile Pill & Hash */}
              <div className="mt-3.5 flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-[11px]">
                <div className="inline-flex items-center gap-1.5 text-brand-700 bg-brand-50 px-2.5 py-1 rounded-md font-medium border border-brand-100">
                  <svg className="w-3.5 h-3.5 text-brand-600" fill="currentColor" viewBox="0 0 20 20">
                    <path clipRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" fillRule="evenodd"></path>
                  </svg>
                  100% Match • Clause 14.B (Hospitalization)
                </div>
                {/* SHA-256 Digest Code Pill */}
                <div className="font-mono text-[10px] text-slate-400 bg-slate-100/90 px-2 py-1 rounded flex items-center gap-1">
                  <span className="text-slate-500 font-semibold">SHA-256:</span>
                  <span className="truncate max-w-[110px]">7f83b165...4b01e</span>
                </div>
              </div>
            </div>
          </div>

          {/* Bottom Pillar: Trust & Standards */}
          <div className="relative z-10 pt-4 border-t border-slate-200/50 flex items-center justify-between text-xs text-slate-500">
            <div className="flex items-center gap-2">
              <svg className="w-4 h-4 text-brand-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2"></path>
              </svg>
              <span>Enterprise compliance • ISO 27001 &amp; SOC-2 aligned</span>
            </div>
            <span className="text-[11px] text-slate-400 font-mono">v2.4.0-stable</span>
          </div>

          {/* Ornamental Blur Circles */}
          <div aria-hidden="true" className="absolute -bottom-20 -left-20 w-80 h-80 bg-blue-200/30 rounded-full blur-3xl pointer-events-none"></div>
          <div aria-hidden="true" className="absolute top-1/4 -right-16 w-64 h-64 bg-indigo-100/40 rounded-full blur-2xl pointer-events-none"></div>
        </section>

        {/* BEGIN: RightColumnSignInPanel */}
        <section className="lg:w-1/2 flex items-center justify-center p-6 sm:p-10 lg:p-14 bg-white">
          <div className="w-full max-w-[460px] flex flex-col justify-center">
            {/* Header */}
            <header className="mb-6">
              <div className="flex items-center justify-between mb-3">
                <span className="text-[11px] font-mono text-brand-700 bg-brand-50 px-2.5 py-1 rounded-full border border-brand-200/60 font-semibold uppercase tracking-wider">
                  Role-Based Portal Access
                </span>
                <span className="text-[11px] font-mono text-emerald-600 bg-emerald-50 px-2.5 py-1 rounded-full border border-emerald-200/60 font-semibold">
                  Neon DB Active
                </span>
              </div>
              <h2 className="text-2xl lg:text-3xl font-bold tracking-tight text-navy-900">
                Sign In to VACHAN
              </h2>
              <p className="text-sm text-slate-500 mt-1">
                Enter your authorized credentials or select a seeded database profile.
              </p>
            </header>

            {/* Error Message Banner */}
            {errorMessage && (
              <div className="mb-5 p-3 rounded-xl bg-red-50 border border-red-200 text-red-700 text-xs flex items-center gap-2">
                <svg className="w-4 h-4 text-red-600 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <span>{errorMessage}</span>
              </div>
            )}

            {/* Form */}
            <form className="space-y-4" onSubmit={handleFormSubmit}>
              {/* Email Input Field */}
              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-700 mb-1.5" htmlFor="email">
                  Work / Registered Email Address
                </label>
                <input
                  className="w-full text-sm bg-white rounded-xl border border-slate-200 px-3.5 py-2.5 text-navy-900 placeholder:text-slate-400 focus:border-brand-600 focus:ring-2 focus:ring-brand-600/15 focus:outline-none shadow-subtle"
                  id="email"
                  name="email"
                  placeholder="name@example.com"
                  required
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                />
              </div>

              {/* Password Input Field */}
              <div>
                <div className="flex items-center justify-between mb-1.5">
                  <label className="block text-xs font-semibold uppercase tracking-wider text-slate-700" htmlFor="password">
                    Password
                  </label>
                  <button
                    type="button"
                    onClick={() => showToast('Password reset token dispatched to email.')}
                    className="text-xs font-semibold text-brand-600 hover:text-brand-700 hover:underline"
                  >
                    Forgot password?
                  </button>
                </div>
                <div className="relative">
                  <input
                    className="w-full text-sm bg-white rounded-xl border border-slate-200 px-3.5 py-2.5 pr-10 text-navy-900 placeholder:text-slate-400 focus:border-brand-600 focus:ring-2 focus:ring-brand-600/15 focus:outline-none shadow-subtle"
                    id="password"
                    name="password"
                    placeholder="Enter password"
                    required
                    type={showPassword ? 'text' : 'password'}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                  />
                  <button
                    aria-label="Toggle password visibility"
                    className="absolute inset-y-0 right-0 pr-3.5 flex items-center text-slate-400 hover:text-slate-600 focus:outline-none"
                    onClick={() => setShowPassword(!showPassword)}
                    type="button"
                  >
                    {showPassword ? (
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l18 18" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2"></path>
                      </svg>
                    ) : (
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2"></path>
                        <path d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2"></path>
                      </svg>
                    )}
                  </button>
                </div>
              </div>

              {/* Submit Button */}
              <div className="pt-2">
                <button
                  className="w-full flex items-center justify-center gap-2 rounded-xl bg-brand-600 hover:bg-brand-700 text-white font-semibold py-2.5 px-4 text-sm shadow-md shadow-brand-600/20 active:scale-[0.99] transition-all cursor-pointer"
                  disabled={isLoading}
                  type="submit"
                >
                  {isLoading ? (
                    <>
                      <span>Authenticating...</span>
                      <svg className="w-4 h-4 text-white animate-spin" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" fill="currentColor"></path>
                      </svg>
                    </>
                  ) : (
                    <span>Sign In to Workspace</span>
                  )}
                </button>
              </div>
            </form>

            {/* Quick-Fill Seeded Accounts for Testing */}
            {mode === 'signin' && (
              <div className="mt-6 pt-5 border-t border-slate-200">
                <div className="flex items-center justify-between mb-2.5">
                  <span className="text-xs font-semibold uppercase tracking-wider text-slate-700">Database Test Accounts</span>
                  <span className="text-[10px] text-slate-400 font-medium">Click to auto-fill credentials</span>
                </div>
                <div className="grid grid-cols-1 gap-2">
                  <button
                    type="button"
                    onClick={() => handleRoleSelect('claims')}
                    className={`p-2.5 rounded-xl border text-left transition-all flex items-center justify-between ${
                      selectedRole === 'claims'
                        ? 'border-brand-600 bg-brand-50/50 ring-1 ring-brand-600/30'
                        : 'border-slate-200 hover:border-slate-300 bg-white'
                    }`}
                  >
                    <div>
                      <div className="text-xs font-bold text-navy-900">Dr. Aris Thorne (Authority)</div>
                      <div className="text-[11px] font-mono text-slate-500">authority@vachan.gov.in • password123</div>
                    </div>
                    <span className="text-[10px] font-semibold text-brand-600 bg-brand-50 px-2 py-0.5 rounded-md border border-brand-200">
                      Approval Authority
                    </span>
                  </button>

                  <button
                    type="button"
                    onClick={() => handleRoleSelect('agent')}
                    className={`p-2.5 rounded-xl border text-left transition-all flex items-center justify-between ${
                      selectedRole === 'agent'
                        ? 'border-brand-600 bg-brand-50/50 ring-1 ring-brand-600/30'
                        : 'border-slate-200 hover:border-slate-300 bg-white'
                    }`}
                  >
                    <div>
                      <div className="text-xs font-bold text-navy-900">Rajesh M. (Insurance Agent)</div>
                      <div className="text-[11px] font-mono text-slate-500">agent@vachan.in • password123</div>
                    </div>
                    <span className="text-[10px] font-semibold text-indigo-600 bg-indigo-50 px-2 py-0.5 rounded-md border border-indigo-200">
                      Insurance Agent
                    </span>
                  </button>

                  <button
                    type="button"
                    onClick={() => handleRoleSelect('customer')}
                    className={`p-2.5 rounded-xl border text-left transition-all flex items-center justify-between ${
                      selectedRole === 'customer'
                        ? 'border-brand-600 bg-brand-50/50 ring-1 ring-brand-600/30'
                        : 'border-slate-200 hover:border-slate-300 bg-white'
                    }`}
                  >
                    <div>
                      <div className="text-xs font-bold text-navy-900">Ananya Kapoor (Customer)</div>
                      <div className="text-[11px] font-mono text-slate-500">customer@vachan.in • password123</div>
                    </div>
                    <span className="text-[10px] font-semibold text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded-md border border-emerald-200">
                      Customer
                    </span>
                  </button>
                </div>
              </div>
            )}

            {/* Bottom Disclaimer Notice */}
            <footer className="mt-8 text-center">
              <p className="text-[11px] text-slate-400 leading-normal">
                Protected by SHA-256 evidence integrity • Simulated demo sandbox environment
              </p>
              <div className="mt-2 flex items-center justify-center gap-4 text-[11px] text-slate-500">
                <span className="hover:underline cursor-pointer">Privacy Policy</span>
                <span>•</span>
                <span className="hover:underline cursor-pointer">Terms of Service</span>
                <span>•</span>
                <span className="hover:underline cursor-pointer">Security Disclosures</span>
              </div>
            </footer>
          </div>
        </section>
      </main>
    </div>
  );
};
