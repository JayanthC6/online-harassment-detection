import React from 'react';
import { Settings, Bell, ShieldCheck } from 'lucide-react';

export default function Header({ activeTab, setActiveTab }) {
  return (
    <nav className="fixed top-0 left-0 w-full z-50 flex justify-between items-center px-margin h-16 bg-surface/80 backdrop-blur-xl border-b border-outline-variant/30 hidden md:flex">
      <div className="flex items-center gap-8">
        <div className="font-headline-lg text-primary-fixed-dim uppercase tracking-widest drop-shadow-[0_0_8px_rgba(0,219,231,0.8)]">
          ShieldAI
        </div>
        <div className="flex gap-6">
          <button 
            onClick={() => setActiveTab('analyze')}
            className={`font-medium pb-1 transition-colors duration-300 ${
              activeTab === 'analyze' 
                ? 'text-primary-fixed font-bold border-b-2 border-primary-fixed opacity-80 duration-150' 
                : 'text-on-surface-variant hover:text-primary-fixed-dim'
            }`}
          >
            Analyze
          </button>
          <button 
            onClick={() => setActiveTab('dashboard')}
            className={`font-medium pb-1 transition-colors duration-300 ${
              activeTab === 'dashboard' 
                ? 'text-primary-fixed font-bold border-b-2 border-primary-fixed opacity-80 duration-150' 
                : 'text-on-surface-variant hover:text-primary-fixed-dim'
            }`}
          >
            Incidents
          </button>
          <button 
            className="text-on-surface-variant font-medium pb-1 hover:text-primary-fixed-dim transition-colors duration-300"
          >
            Intelligence
          </button>
        </div>
      </div>
      <div className="flex items-center gap-4">
        <button className="text-on-surface-variant hover:text-primary-fixed transition-colors">
          <Settings size={20} />
        </button>
        <button className="text-on-surface-variant hover:text-primary-fixed transition-colors">
          <Bell size={20} />
        </button>
        <div className="w-8 h-8 rounded-full border border-primary-fixed/50 flex items-center justify-center bg-surface-container-high ml-2">
           <ShieldCheck size={16} className="text-primary-fixed" />
        </div>
      </div>
    </nav>
  );
}
