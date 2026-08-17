import React from 'react';
import { LayoutDashboard, Search, AlertTriangle, Brain, Settings, Bell, ShieldCheck } from 'lucide-react';

const NAV = [
  { id: 'dashboard',  label: 'Dashboard',         icon: LayoutDashboard },
  { id: 'analyze',    label: 'Threat Hunt',        icon: Search },
  { id: 'incidents',  label: 'Incidents',          icon: AlertTriangle },
  { id: 'behavioral', label: 'Behavioral Intel',   icon: Brain },
];

export default function Sidebar({ activeTab, setActiveTab }) {
  return (
    <aside
      style={{ width: 240 }}
      className="fixed left-0 top-0 h-screen z-40 flex flex-col bg-surface border-r border-border hidden md:flex"
    >
      {/* Logo */}
      <div className="flex items-center gap-2.5 px-5 h-14 border-b border-border flex-shrink-0">
        <div className="w-7 h-7 bg-blue rounded-md flex items-center justify-center flex-shrink-0">
          <ShieldCheck size={15} className="text-white" />
        </div>
        <span className="text-lg font-bold text-text-primary tracking-tight">
          Shield<span className="text-blue">AI</span>
        </span>
      </div>

      {/* Nav */}
      <nav className="flex-1 p-3 space-y-0.5 overflow-y-auto">
        <p className="section-title px-2 mt-2 mb-3">Main Menu</p>
        {NAV.map(({ id, label, icon: Icon }) => (
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

      {/* Footer */}
      <div className="p-3 border-t border-border flex-shrink-0">
        <button className="nav-item">
          <Settings size={15} />
          <span>Settings</span>
        </button>
        <div className="flex items-center gap-3 mt-3 px-3 py-2">
          <div className="w-7 h-7 rounded-full bg-blue-muted border border-border-2 flex items-center justify-center flex-shrink-0">
            <ShieldCheck size={13} className="text-blue" />
          </div>
          <div className="min-w-0">
            <p className="text-xs font-semibold text-text-primary truncate">Admin</p>
            <p className="text-2xs text-text-muted">Level 4 Access</p>
          </div>
        </div>
      </div>
    </aside>
  );
}
