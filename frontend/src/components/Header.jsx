import React from 'react';
import { Bell, Settings, ShieldCheck, ChevronRight } from 'lucide-react';

const PAGE_LABELS = {
  analyze:          'Threat Hunt',
  dashboard:        'Organization Dashboard',
  incidents:        'Incidents',
  behavioral:       'Behavioral Intel',
  submit_complaint: 'File a Complaint',
  my_tickets:       'My Tickets',
};

export default function Header({ activeTab, setActiveTab, token, onLogout, role }) {
  return (
    <header
      style={{ left: 240 }}
      className="fixed top-0 right-0 z-30 flex items-center justify-between px-6 h-14 bg-bg/80 backdrop-blur-lg border-b border-border hidden md:flex"
    >
      {/* Breadcrumb */}
      <div className="flex items-center gap-1.5 text-xs text-text-muted">
        <span>ShieldAI</span>
        <ChevronRight size={12} />
        <span className="text-text-secondary font-medium">{PAGE_LABELS[activeTab] || activeTab}</span>
      </div>

      {/* Actions */}
      <div className="flex items-center gap-1">
        {token && (
          <button 
            onClick={onLogout}
            className="text-xs font-mono px-3 py-1 mr-2 rounded bg-surface-3 text-text-muted hover:text-text-primary hover:bg-surface-solid border border-border transition-colors"
          >
            Logout
          </button>
        )}
        <button className="w-8 h-8 rounded-md flex items-center justify-center text-text-muted hover:text-text-primary hover:bg-surface-3 transition-colors">
          <Bell size={16} />
        </button>
        <button className="w-8 h-8 rounded-md flex items-center justify-center text-text-muted hover:text-text-primary hover:bg-surface-3 transition-colors">
          <Settings size={16} />
        </button>
        <div className="w-8 h-8 rounded-full bg-blue/10 border border-blue/30 flex items-center justify-center ml-2 shadow-[0_0_10px_rgba(0,242,254,0.3)]">
          <ShieldCheck size={14} className="text-blue" />
        </div>
      </div>
    </header>
  );
}
