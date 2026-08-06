import React, { useState } from 'react';
import { User, Activity, AlertTriangle, ShieldAlert, ArrowRight } from 'lucide-react';
import Card from '../common/Card';
import ActorProfileDrawer from './ActorProfileDrawer';

export default function BehavioralIntelligence({ profilesData }) {
  const [selectedProfile, setSelectedProfile] = useState(null);
  const profiles = profilesData || [];

  const getLevelColor = (level) => {
    switch (level) {
      case 'Critical': return 'text-rose-700 bg-rose-50 border-rose-200';
      case 'High': return 'text-amber-700 bg-amber-50 border-amber-200';
      case 'Watch': return 'text-indigo-700 bg-indigo-50 border-indigo-200';
      default: return 'text-emerald-700 bg-emerald-50 border-emerald-200';
    }
  };

  const getScoreColor = (score) => {
    if (score >= 85) return 'text-rose-600';
    if (score >= 60) return 'text-amber-600';
    if (score >= 30) return 'text-indigo-600';
    return 'text-emerald-600';
  };

  // Stats
  const criticalActors = profiles.filter(p => p.behavior_level === 'Critical').length;
  const highActors = profiles.filter(p => p.behavior_level === 'High').length;
  const watchActors = profiles.filter(p => p.behavior_level === 'Watch').length;

  return (
    <div className="space-y-6">
      {/* ── Behavior Stats ── */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="p-4 flex flex-col justify-between">
          <div className="text-slate-500 text-sm font-medium flex items-center gap-2">
            <User size={16} /> Total Tracked Actors
          </div>
          <div className="text-3xl font-bold text-slate-800 mt-2">{profiles.length}</div>
        </Card>
        <Card className="p-4 flex flex-col justify-between bg-rose-50 border-rose-100">
          <div className="text-rose-700 text-sm font-medium flex items-center gap-2">
            <ShieldAlert size={16} /> Critical Risk
          </div>
          <div className="text-3xl font-bold text-rose-800 mt-2">{criticalActors}</div>
        </Card>
        <Card className="p-4 flex flex-col justify-between">
          <div className="text-amber-700 text-sm font-medium flex items-center gap-2">
            <AlertTriangle size={16} /> High Risk
          </div>
          <div className="text-3xl font-bold text-amber-800 mt-2">{highActors}</div>
        </Card>
        <Card className="p-4 flex flex-col justify-between">
          <div className="text-indigo-700 text-sm font-medium flex items-center gap-2">
            <Activity size={16} /> On Watchlist
          </div>
          <div className="text-3xl font-bold text-indigo-800 mt-2">{watchActors}</div>
        </Card>
      </div>

      {/* ── Actor Profiles Table ── */}
      <Card className="p-0 overflow-hidden">
        <div className="p-5 border-b border-slate-100 flex justify-between items-center bg-white">
          <h2 className="text-base font-semibold text-slate-800">Actor Profiles</h2>
        </div>
        
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-slate-50 border-b border-slate-200">
                <th className="px-6 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">Actor Identifier</th>
                <th className="px-6 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">Behavior Score</th>
                <th className="px-6 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">Risk Level</th>
                <th className="px-6 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">Total Reports</th>
                <th className="px-6 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {profiles.length === 0 ? (
                <tr>
                  <td colSpan="5" className="px-6 py-8 text-center text-slate-500 text-sm">
                    No behavioral profiles found.
                  </td>
                </tr>
              ) : (
                profiles.map((profile, i) => (
                  <tr key={i} className="hover:bg-slate-50/50 transition-colors">
                    <td className="px-6 py-4">
                      <div className="text-sm font-medium text-slate-900">{profile.actor_id}</div>
                      <div className="text-xs text-slate-500">Last seen: {new Date(profile.last_seen).toLocaleString()}</div>
                    </td>
                    <td className="px-6 py-4">
                      <div className={`text-xl font-bold ${getScoreColor(profile.behavior_score)}`}>
                        {profile.behavior_score.toFixed(1)}
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <span className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium border ${getLevelColor(profile.behavior_level)}`}>
                        {profile.behavior_level}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <div className="text-sm text-slate-700">{profile.total_reports}</div>
                      {profile.harmful_messages > 0 && (
                        <div className="text-xs text-rose-500 font-medium">{profile.harmful_messages} harmful</div>
                      )}
                    </td>
                    <td className="px-6 py-4">
                      <button 
                        onClick={() => setSelectedProfile(profile)}
                        className="text-indigo-600 hover:text-indigo-800 text-sm font-medium flex items-center gap-1 transition-colors"
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
