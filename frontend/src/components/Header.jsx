import React from 'react';
import PropTypes from 'prop-types';
import { ShieldCheck, ChevronRight, LogIn, LogOut, Menu, User, Shield } from 'lucide-react';

const PAGE_LABELS = {
  analyze: 'Threat Scan & Analysis',
  chat: 'AI Cyber Safety Assistant',
  dashboard: 'Security Operations Center',
  incidents: 'Report Queue & Triage',
  offenders: 'Repeat Offender Intelligence',
  behavioral: 'Behavioral Profiling',
  retention: 'Data Retention & Privacy Purge',
  my_history: 'My Safety History',
  how_it_works: 'How ShieldAI Works',
  login: 'Admin & Operator Portal'
};

export default function Header({ activeTab, setActiveTab, token, onLogout, role, onMobileMenuToggle }) {
  const isAuth = Boolean(token);

  return (
    <header
      style={{ left: 240 }}
      className="fixed top-0 right-0 z-30 flex items-center justify-between px-6 h-14 bg-bg/90 backdrop-blur-xl border-b border-border hidden md:flex"
    >
      {/* Breadcrumb Navigation */}
      <div className="flex items-center gap-2 text-xs font-mono text-text-muted">
        <span className="text-blue font-bold tracking-wider">ShieldAI</span>
        <ChevronRight size={13} />
        <span className="text-text-primary font-semibold">
          {PAGE_LABELS[activeTab] || activeTab}
        </span>
      </div>

      {/* Header Actions */}
      <div className="flex items-center gap-3">
        {isAuth ? (
          <div className="flex items-center gap-2.5">
            <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-surface border border-border text-xs font-mono text-text-secondary">
              <span className="w-1.5 h-1.5 rounded-full bg-cyan-400" />
              <span>{role || 'Admin'}</span>
            </div>
            <button
              onClick={onLogout}
              className="flex items-center gap-1 px-3 py-1 rounded bg-surface hover:bg-surface-2 text-text-muted hover:text-red-400 border border-border text-xs font-mono transition-colors cursor-pointer"
            >
              <LogOut size={12} />
              <span>Logout</span>
            </button>
          </div>
        ) : (
          <button
            onClick={() => setActiveTab('login')}
            className="flex items-center gap-1.5 px-3 py-1 rounded bg-blue/15 hover:bg-blue/25 text-blue border border-blue/40 text-xs font-mono font-semibold transition-colors cursor-pointer"
          >
            <LogIn size={13} />
            <span>Admin Sign In</span>
          </button>
        )}

        <div className="w-8 h-8 rounded-full bg-blue/10 border border-blue/30 flex items-center justify-center shadow-[0_0_10px_rgba(0,242,254,0.25)]">
          <ShieldCheck size={14} className="text-blue" />
        </div>
      </div>
    </header>
  );
}

Header.propTypes = {
  activeTab: PropTypes.string.isRequired,
  setActiveTab: PropTypes.func.isRequired,
  token: PropTypes.string,
  onLogout: PropTypes.func,
  role: PropTypes.string,
  onMobileMenuToggle: PropTypes.func,
};
