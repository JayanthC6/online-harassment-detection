import React from 'react';
import PropTypes from 'prop-types';
import {
  LayoutDashboard,
  Search,
  AlertTriangle,
  Brain,
  ShieldCheck,
  HelpCircle,
  MessageSquare,
  Users,
  Trash2,
  LogIn,
  LogOut,
  Shield
} from 'lucide-react';

export default function Sidebar({ activeTab, setActiveTab, token, role, onLogout }) {
  const isAuth = Boolean(token);
  const isPublicUser = isAuth && role === 'User';
  const isAdminOrMod = isAuth && role !== 'User';

  let navItems = [];

  if (!isAuth) {
    // Unauthenticated public visitors
    navItems = [
      { id: 'analyze', label: 'Scan Content', icon: Search },
      { id: 'chat', label: 'AI Safety Chat', icon: MessageSquare },
      { id: 'how_it_works', label: 'How It Works', icon: HelpCircle },
      { id: 'login', label: 'Admin Sign In', icon: LogIn }
    ];
  } else if (isPublicUser) {
    // Authenticated regular user
    navItems = [
      { id: 'analyze', label: 'Scan Content', icon: Search },
      { id: 'chat', label: 'AI Safety Chat', icon: MessageSquare },
      { id: 'my_history', label: 'My History', icon: LayoutDashboard },
      { id: 'how_it_works', label: 'How It Works', icon: HelpCircle }
    ];
  } else {
    // Admin / Moderator
    navItems = [
      { id: 'dashboard', label: 'Operations Center', icon: LayoutDashboard },
      { id: 'analyze', label: 'Threat Hunt & Scan', icon: Search },
      { id: 'incidents', label: 'Report Queue', icon: AlertTriangle },
      { id: 'offenders', label: 'Repeat Offenders', icon: Users },
      { id: 'behavioral', label: 'Behavioral Intel', icon: Brain },
      { id: 'chat', label: 'AI Assistant', icon: MessageSquare },
      { id: 'retention', label: 'Retention & Purge', icon: Trash2 },
      { id: 'how_it_works', label: 'How It Works', icon: HelpCircle }
    ];
  }

  return (
    <aside
      style={{ width: 240 }}
      className="fixed left-0 top-0 h-screen z-40 flex flex-col bg-bg/95 backdrop-blur-xl border-r border-border hidden md:flex"
    >
      {/* Brand Header */}
      <div className="flex items-center gap-2.5 px-5 h-14 border-b border-border flex-shrink-0">
        <div className="w-8 h-8 bg-blue/10 border border-blue/30 rounded-md flex items-center justify-center flex-shrink-0 shadow-[0_0_15px_rgba(0,242,254,0.2)]">
          <ShieldCheck size={16} className="text-blue" />
        </div>
        <span className="text-lg font-bold text-text-primary tracking-tight font-mono" style={{ textShadow: '0 0 10px rgba(0,242,254,0.3)' }}>
          Shield<span className="text-blue">AI</span>
        </span>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-3 space-y-1 overflow-y-auto">
        <p className="section-title px-2 mt-2 mb-2">Main Navigation</p>
        {navItems.map(({ id, label, icon: Icon }) => (
          <button
            key={id}
            onClick={() => setActiveTab(id)}
            className={`nav-item ${activeTab === id ? 'active' : ''}`}
          >
            <Icon size={15} />
            <span>{label}</span>
          </button>
        ))}
      </nav>

      {/* User / Session Footer */}
      <div className="p-3 border-t border-border flex-shrink-0">
        {isAuth ? (
          <div className="space-y-2">
            <div className="flex items-center justify-between px-3 py-2 bg-surface-solid rounded-lg border border-border">
              <div className="flex items-center gap-2.5 min-w-0">
                <div className="w-7 h-7 rounded-full bg-blue/10 border border-blue/30 flex items-center justify-center flex-shrink-0">
                  <Shield size={13} className="text-blue" />
                </div>
                <div className="min-w-0">
                  <p className="text-xs font-semibold text-text-primary truncate font-mono">
                    {role || 'Admin'}
                  </p>
                  <p className="text-[10px] text-cyan-400 uppercase tracking-wider font-mono">
                    {isAdminOrMod ? 'SOC Level 4' : 'Standard'}
                  </p>
                </div>
              </div>
              <button
                onClick={onLogout}
                title="Log out"
                className="p-1 text-text-muted hover:text-red-400 transition-colors"
                aria-label="Log out"
              >
                <LogOut size={14} />
              </button>
            </div>
          </div>
        ) : (
          <div className="p-3 rounded-lg bg-surface-solid border border-border space-y-2">
            <div className="flex items-center gap-2 text-xs font-mono text-text-muted">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              <span>Public Safety Scanner</span>
            </div>
            <button
              onClick={() => setActiveTab('login')}
              className="w-full flex items-center justify-center gap-1.5 py-1.5 px-3 rounded bg-blue/15 hover:bg-blue/25 text-blue border border-blue/40 text-xs font-mono font-semibold transition-colors"
            >
              <LogIn size={13} /> Admin Portal
            </button>
          </div>
        )}
      </div>
    </aside>
  );
}

Sidebar.propTypes = {
  activeTab: PropTypes.string.isRequired,
  setActiveTab: PropTypes.func.isRequired,
  token: PropTypes.string,
  role: PropTypes.string,
  onLogout: PropTypes.func,
};
