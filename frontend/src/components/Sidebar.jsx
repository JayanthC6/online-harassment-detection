import React from 'react';
import { ShieldCheck, Search, BarChart3, Settings, Bell, Fingerprint, Database, Grid } from 'lucide-react';

export default function Sidebar({ activeTab, setActiveTab }) {
  return (
    <aside className="fixed left-0 top-16 h-[calc(100vh-64px)] z-40 flex flex-col bg-surface-container-low/90 backdrop-blur-md border-r border-outline-variant/50 w-64 hidden md:flex">
      <div className="p-6 border-b border-outline-variant/30 mb-4">
        <div className="flex items-center gap-3 mb-1">
          <div className="w-10 h-10 clip-path-chamfer border border-primary-fixed/30 flex items-center justify-center bg-primary-fixed/10">
            <ShieldCheck size={20} className="text-primary-fixed" />
          </div>
          <div>
            <div className="font-label-caps text-label-caps text-primary-fixed">Core Terminal</div>
            <div className="font-metadata-sm text-metadata-sm text-on-surface-variant">Level 4 Clearance</div>
          </div>
        </div>
      </div>
      
      <div className="flex-1 px-4 space-y-1">
        <button
          onClick={() => setActiveTab('dashboard')}
          className={`w-full flex items-center gap-3 p-3 font-label-caps text-label-caps transition-all duration-200 ${
            activeTab === 'dashboard' 
              ? 'bg-primary-container/10 text-primary-fixed border-l-4 border-primary-fixed clip-path-chamfer scale-95 duration-100'
              : 'text-on-surface-variant hover:bg-surface-variant/30 hover:border-l-4 hover:border-secondary-fixed'
          }`}
        >
          <Grid size={18} /> Dashboard
        </button>

        <button
          onClick={() => setActiveTab('analyze')}
          className={`w-full flex items-center gap-3 p-3 font-label-caps text-label-caps transition-all duration-200 ${
            activeTab === 'analyze' 
              ? 'bg-primary-container/10 text-primary-fixed border-l-4 border-primary-fixed clip-path-chamfer scale-95 duration-100'
              : 'text-on-surface-variant hover:bg-surface-variant/30 hover:border-l-4 hover:border-secondary-fixed'
          }`}
        >
          <Search size={18} /> Threat Hunt
        </button>

        <button
          onClick={() => setActiveTab('evidence')}
          className={`w-full flex items-center gap-3 p-3 font-label-caps text-label-caps transition-all duration-200 ${
            activeTab === 'evidence' 
              ? 'bg-primary-container/10 text-primary-fixed border-l-4 border-primary-fixed clip-path-chamfer scale-95 duration-100'
              : 'text-on-surface-variant hover:bg-surface-variant/30 hover:border-l-4 hover:border-secondary-fixed'
          }`}
        >
          <Fingerprint size={18} /> Evidence
        </button>

        <button className="w-full flex items-center gap-3 text-on-surface-variant p-3 hover:bg-surface-variant/30 hover:border-l-4 hover:border-secondary-fixed transition-all duration-200 font-label-caps text-label-caps">
          <Database size={18} /> Archives
        </button>
      </div>
      
      <div className="p-4 mt-auto border-t border-outline-variant/30">
        <button 
          onClick={() => setActiveTab('analyze')}
          className="w-full py-2 bg-primary-fixed/10 text-primary-fixed border border-primary-fixed clip-path-chamfer font-label-caps text-label-caps hover:bg-primary-fixed hover:text-on-primary-fixed transition-colors shadow-[0_0_15px_rgba(116,245,255,0.2)]"
        >
          New Scan
        </button>
      </div>
    </aside>
  );
}
