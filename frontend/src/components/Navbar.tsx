import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { ShieldCheck, UserCheck, Briefcase, Scale, LogOut, Sparkles } from 'lucide-react';

export const Navbar: React.FC = () => {
  const { user, role, setRole, logout } = useAuth();
  const location = useLocation();

  return (
    <header className="sticky top-0 z-50 backdrop-blur-md bg-white/80 border-b border-slate-200/80 transition-all">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-20 flex items-center justify-between">
        {/* Brand Logo */}
        <Link to="/" className="flex items-center gap-3 group focus:outline-none">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-brand-700 via-brand-600 to-sky-400 flex items-center justify-center text-white shadow-md shadow-brand-600/25 group-hover:scale-105 transition-transform duration-200">
            <ShieldCheck className="w-5 h-5 text-white" />
          </div>
          <div className="flex flex-col">
            <div className="flex items-center gap-2">
              <span className="font-extrabold text-xl tracking-tight text-navy-900">VACHAN</span>
              <span className="text-xs font-semibold uppercase tracking-wider px-2 py-0.5 rounded-full bg-blue-50 text-brand-700 border border-blue-200/60">
                VoiceGuard
              </span>
            </div>
            <span className="text-[10px] font-medium tracking-wide text-slate-500 uppercase -mt-0.5">
              AI Policy Assurance
            </span>
          </div>
        </Link>

        {/* Segmented Persona Switcher for Hackathon Judges */}
        {user && (
          <div className="hidden lg:flex items-center bg-slate-100/90 p-1.5 rounded-2xl border border-slate-200 shadow-inner">
            <button
              onClick={() => setRole('CUSTOMER')}
              className={`flex items-center gap-2 px-3.5 py-1.5 rounded-xl text-xs font-bold transition-all ${
                role === 'CUSTOMER'
                  ? 'bg-white text-brand-700 shadow-sm border border-slate-200/60'
                  : 'text-slate-600 hover:text-navy-900'
              }`}
            >
              <UserCheck className="w-3.5 h-3.5 text-violet-500" />
              <span>Customer</span>
            </button>
            <button
              onClick={() => setRole('INSURANCE_AGENT')}
              className={`flex items-center gap-2 px-3.5 py-1.5 rounded-xl text-xs font-bold transition-all ${
                role === 'INSURANCE_AGENT'
                  ? 'bg-white text-brand-700 shadow-sm border border-slate-200/60'
                  : 'text-slate-600 hover:text-navy-900'
              }`}
            >
              <Briefcase className="w-3.5 h-3.5 text-sky-500" />
              <span>Agent</span>
            </button>
            <button
              onClick={() => setRole('APPROVAL_AUTHORITY')}
              className={`flex items-center gap-2 px-3.5 py-1.5 rounded-xl text-xs font-bold transition-all ${
                role === 'APPROVAL_AUTHORITY'
                  ? 'bg-navy-900 text-white shadow-sm'
                  : 'text-slate-600 hover:text-navy-900'
              }`}
            >
              <Scale className="w-3.5 h-3.5 text-emerald-400" />
              <span>Authority</span>
            </button>
          </div>
        )}

        {/* Right side controls */}
        <div className="flex items-center gap-3">
          {/* Simulated EVM block status pill */}
          <div className="hidden sm:flex items-center gap-2 text-xs font-semibold px-3 py-1.5 rounded-full bg-slate-50 border border-slate-200/80 text-slate-600">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
            <span>EVM Anchor #142</span>
          </div>

          {user ? (
            <div className="flex items-center gap-3">
              <Link
                to="/dashboard"
                className={`text-sm font-semibold px-3.5 py-2 rounded-xl transition ${
                  location.pathname === '/dashboard'
                    ? 'text-brand-700 bg-brand-50'
                    : 'text-slate-700 hover:text-brand-600'
                }`}
              >
                Dashboard
              </Link>
              <div className="flex items-center gap-2 pl-2 border-l border-slate-200">
                <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-brand-600 to-indigo-500 text-white flex items-center justify-center text-xs font-bold shadow-sm">
                  {user.full_name.charAt(0)}
                </div>
                <button
                  onClick={logout}
                  title="Sign out"
                  className="p-1.5 text-slate-400 hover:text-rose-600 rounded-lg transition"
                >
                  <LogOut className="w-4 h-4" />
                </button>
              </div>
            </div>
          ) : (
            <div className="flex items-center gap-2">
              <Link
                to="/login"
                className="text-sm font-semibold text-slate-700 hover:text-brand-700 px-4 py-2 transition-colors"
              >
                Sign In
              </Link>
              <Link
                to="/login"
                className="inline-flex items-center justify-center px-4 py-2 rounded-full text-xs font-bold text-white bg-gradient-to-r from-brand-700 to-brand-500 hover:from-brand-800 hover:to-brand-600 shadow-md shadow-brand-700/20 transition-all active:scale-98"
              >
                Launch Demo
              </Link>
            </div>
          )}
        </div>
      </div>
    </header>
  );
};
