import React, { useState } from 'react';
import { User, Activity, AlertTriangle, ShieldAlert, ArrowRight } from 'lucide-react';
import Card from '../common/Card';
import ActorProfileDrawer from './ActorProfileDrawer';

export default function BehavioralIntelligence({ profilesData }) {
  const [selectedProfile, setSelectedProfile] = useState(null);
  const profiles = profilesData || [];

  const getLevelColor = (level) => {
    switch (level) {
      case 'Critical': return 'text-critical bg-black/60 border-critical shadow-[inset_0_0_15px_rgba(244,63,94,0.3)] rounded-none';
      case 'High': return 'text-danger bg-black/60 border-danger shadow-[inset_0_0_15px_rgba(249,115,22,0.3)] rounded-none';
      case 'Watch': return 'text-blue bg-black/60 border-blue shadow-[inset_0_0_15px_rgba(0,242,254,0.3)] rounded-none';
      default: return 'text-success bg-black/60 border-success shadow-[inset_0_0_15px_rgba(16,185,129,0.3)] rounded-none';
    }
  };

  const getScoreColor = (score) => {
    if (score >= 85) return 'text-critical drop-shadow-[0_0_5px_rgba(244,63,94,0.6)]';
    if (score >= 60) return 'text-danger drop-shadow-[0_0_5px_rgba(249,115,22,0.6)]';
    if (score >= 30) return 'text-blue drop-shadow-[0_0_5px_rgba(0,242,254,0.6)]';
    return 'text-success drop-shadow-[0_0_5px_rgba(16,185,129,0.6)]';
  };

  // Stats
  const criticalActors = profiles.filter(p => p.behavior_level === 'Critical').length;
  const highActors = profiles.filter(p => p.behavior_level === 'High').length;
  const watchActors = profiles.filter(p => p.behavior_level === 'Watch').length;

  return (
    <div className="space-y-6">
      {/* ── Behavior Stats ── */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="p-4 flex flex-col justify-between bg-black/40 backdrop-blur-md border border-blue/40 shadow-[0_0_15px_rgba(0,242,254,0.1)] rounded-none">
          <div className="text-blue text-sm font-bold font-mono uppercase tracking-wider flex items-center gap-2 drop-shadow-[0_0_5px_rgba(0,242,254,0.4)]">
            <User size={16} /> Total Tracked Actors
          </div>
          <div className="text-3xl font-extrabold text-white mt-2 font-mono drop-shadow-md">{profiles.length}</div>
        </Card>
        <Card className="p-4 flex flex-col justify-between bg-black/40 backdrop-blur-md border border-critical shadow-[0_0_15px_rgba(244,63,94,0.2)] rounded-none">
          <div className="text-critical text-sm font-bold font-mono uppercase tracking-wider flex items-center gap-2 drop-shadow-[0_0_5px_rgba(244,63,94,0.4)]">
            <ShieldAlert size={16} /> Critical Risk
          </div>
          <div className="text-3xl font-extrabold text-critical mt-2 font-mono drop-shadow-md">{criticalActors}</div>
        </Card>
        <Card className="p-4 flex flex-col justify-between bg-black/40 backdrop-blur-md border border-danger shadow-[0_0_15px_rgba(249,115,22,0.2)] rounded-none">
          <div className="text-danger text-sm font-bold font-mono uppercase tracking-wider flex items-center gap-2 drop-shadow-[0_0_5px_rgba(249,115,22,0.4)]">
            <AlertTriangle size={16} /> High Risk
          </div>
          <div className="text-3xl font-extrabold text-danger mt-2 font-mono drop-shadow-md">{highActors}</div>
        </Card>
        <Card className="p-4 flex flex-col justify-between bg-black/40 backdrop-blur-md border border-warning shadow-[0_0_15px_rgba(245,158,11,0.1)] rounded-none">
          <div className="text-warning text-sm font-bold font-mono uppercase tracking-wider flex items-center gap-2 drop-shadow-[0_0_5px_rgba(245,158,11,0.4)]">
            <Activity size={16} /> On Watchlist
          </div>
          <div className="text-3xl font-extrabold text-warning mt-2 font-mono drop-shadow-md">{watchActors}</div>
        </Card>
      </div>

      {/* ── Actor Profiles Table ── */}
      <Card className="p-0 overflow-hidden bg-panel border-slate-700 rounded-none">
        <div className="p-5 border-b border-slate-700 flex justify-between items-center bg-panel">
          <h2 className="text-sm font-bold text-off-white font-display uppercase tracking-wider">Actor Profiles</h2>
        </div>
        
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-slate-800 border-b border-slate-700">
                <th className="px-6 py-3 text-xs font-bold text-slate-400 font-mono uppercase tracking-wider">Actor Identifier</th>
                <th className="px-6 py-3 text-xs font-bold text-slate-400 font-mono uppercase tracking-wider">Safety Score</th>
                <th className="px-6 py-3 text-xs font-bold text-slate-400 font-mono uppercase tracking-wider">Safety Level</th>
                <th className="px-6 py-3 text-xs font-bold text-slate-400 font-mono uppercase tracking-wider">Total Reports</th>
                <th className="px-6 py-3 text-xs font-bold text-slate-400 font-mono uppercase tracking-wider">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-700 bg-panel">
              {profiles.length === 0 ? (
                <tr>
                  <td colSpan="5" className="px-6 py-8 text-center text-slate-500 text-sm">
                    No behavioral profiles found.
                  </td>
                </tr>
              ) : (
                profiles.map((profile, i) => (
                  <tr key={i} className="hover:bg-slate-800/50 transition-colors group">
                    <td className="px-6 py-4">
                      <div className="text-sm font-bold text-off-white font-mono">{profile.actor_id}</div>
                      <div className="text-xs text-slate-500 font-mono">Last seen: {new Date(profile.last_seen).toLocaleString()}</div>
                    </td>
                    <td className="px-6 py-4">
                      <div className={`text-xl font-bold font-mono tabular-nums ${getScoreColor(profile.behavior_score)}`}>
                        {profile.behavior_score.toFixed(1)}
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <span className={`inline-flex items-center px-2.5 py-1 text-xs font-bold font-mono uppercase border ${getLevelColor(profile.behavior_level)}`}>
                        {profile.behavior_level}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <div className="text-sm text-off-white font-mono tabular-nums">{profile.total_reports}</div>
                      {profile.harmful_messages > 0 && (
                        <div className="text-xs text-redaction-red font-bold font-mono mt-1">{profile.harmful_messages} harmful</div>
                      )}
                    </td>
                    <td className="px-6 py-4">
                      <button 
                        onClick={() => setSelectedProfile(profile)}
                        className="text-slate-400 group-hover:text-off-white text-sm font-bold font-mono uppercase tracking-wider flex items-center gap-1 transition-colors"
                      >
                        View Profile <ArrowRight size={14} />
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </Card>

      <ActorProfileDrawer
        profile={selectedProfile}
        isOpen={!!selectedProfile}
        onClose={() => setSelectedProfile(null)}
      />
    </div>
  );
}
