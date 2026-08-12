import React, { useEffect, useRef } from 'react';
import { X, User, Activity, ShieldAlert, BarChart2, TrendingUp, Info } from 'lucide-react';
import Card from '../common/Card';

export default function ActorProfileDrawer({ profile, isOpen, onClose }) {
  const drawerRef = useRef(null);

  useEffect(() => {
    const handleEscape = (e) => {
      if (e.key === 'Escape' && isOpen) onClose();
    };
    document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, [isOpen, onClose]);

  if (!isOpen || !profile) return null;

  const getLevelColor = (level) => {
    switch (level) {
      case 'Critical': return 'text-redaction-red bg-slate-900 border-redaction-red rounded-none';
      case 'High': return 'text-alert-amber bg-panel border-alert-amber rounded-none';
      case 'Watch': return 'text-slate-300 bg-panel border-slate-500 rounded-none';
      default: return 'text-verified-teal bg-panel border-verified-teal rounded-none';
    }
  };

  const getScoreColor = (score) => {
    if (score >= 85) return 'text-redaction-red';
    if (score >= 60) return 'text-alert-amber';
    if (score >= 30) return 'text-slate-300';
    return 'text-verified-teal';
  };

  const categories = Object.entries(profile.multi_label_distribution || {})
    .sort((a, b) => b[1] - a[1]);

  return (
    <>
      <div 
        className="fixed inset-0 bg-slate-900/20 backdrop-blur-sm z-40 transition-opacity"
        onClick={onClose}
      />
      
      <div 
        ref={drawerRef}
        className="fixed inset-y-0 right-0 w-full max-w-2xl bg-ink shadow-2xl z-50 overflow-y-auto border-l border-slate-700 transform transition-transform duration-300 ease-in-out"
      >
        <div className="sticky top-0 bg-panel border-b border-slate-700 px-6 py-4 flex justify-between items-center z-10">
          <div>
            <h2 className="text-xl font-bold text-off-white font-mono uppercase tracking-wider flex items-center gap-2">
              <User className="text-slate-400" size={20} />
              {profile.actor_id}
            </h2>
            <p className="text-xs text-slate-500 mt-1">
              First seen: {new Date(profile.first_seen).toLocaleString()}
            </p>
          </div>
          <button 
            onClick={onClose}
            className="p-2 text-slate-400 hover:text-off-white hover:bg-slate-800 border border-transparent hover:border-slate-700 transition-colors"
          >
            <X size={20} />
          </button>
        </div>

        <div className="p-6 space-y-6">
          
          {/* Score Overview */}
          <div className="flex gap-4">
            <Card className="flex-1 p-5 flex flex-col justify-center bg-panel border-slate-700 rounded-none">
              <div className="text-sm font-bold text-slate-500 font-mono uppercase tracking-wider mb-1 flex items-center gap-2">
                <Activity size={16} /> Safety Score
              </div>
              <div className={`text-4xl font-bold font-mono tabular-nums ${getScoreColor(profile.behavior_score)}`}>
                {profile.behavior_score.toFixed(1)}
              </div>
            </Card>
            <Card className="flex-1 p-5 flex flex-col justify-center bg-panel border-slate-700 rounded-none">
              <div className="text-sm font-bold text-slate-500 font-mono uppercase tracking-wider mb-1 flex items-center gap-2">
                <ShieldAlert size={16} /> Safety Level
              </div>
              <div>
                <span className={`inline-flex items-center px-3 py-1 text-sm font-bold font-mono uppercase border ${getLevelColor(profile.behavior_level)}`}>
                  {profile.behavior_level}
                </span>
              </div>
            </Card>
          </div>

          {/* AI Recommendation */}
          <Card className="bg-slate-900 border-slate-700 rounded-none p-5">
            <div className="flex items-start gap-3">
              <div className="p-2 bg-panel border border-slate-700 text-slate-300 rounded-none">
                <Info size={18} />
              </div>
              <div>
                <h3 className="text-xs font-bold text-slate-400 font-mono uppercase tracking-wider mb-1">
                  AI Recommendation
                </h3>
                <p className="text-sm text-off-white font-mono">
                  {profile.recommendation}
                </p>
              </div>
            </div>
          </Card>

          {/* Explainability / Logic */}
          <div>
            <h3 className="text-xs font-bold text-slate-500 font-mono uppercase tracking-wider mb-3 flex items-center gap-2">
              <TrendingUp size={14} /> Score Factors
            </h3>
            <Card className="p-0 overflow-hidden divide-y divide-slate-700 bg-panel border-slate-700 rounded-none">
              {profile.explanation && profile.explanation.length > 0 ? (
                profile.explanation.map((exp, idx) => (
                  <div key={idx} className="p-4 flex items-start gap-3 bg-panel">
                    <div className="mt-1.5 w-1.5 h-1.5 bg-slate-500 rounded-none flex-shrink-0" />
                    <p className="text-sm text-slate-300 font-mono">{exp}</p>
                  </div>
                ))
              ) : (
                <div className="p-4 text-sm text-slate-500 bg-panel font-mono">No factors recorded.</div>
              )}
            </Card>
          </div>

          <div className="grid grid-cols-2 gap-6">
            {/* Stats */}
            <div>
              <h3 className="text-xs font-bold text-slate-500 font-mono uppercase tracking-wider mb-3 flex items-center gap-2">
                <BarChart2 size={14} /> Overall Statistics
              </h3>
              <Card className="p-4 space-y-3 bg-panel border-slate-700 rounded-none">
                <div className="flex justify-between items-center text-sm font-mono">
                  <span className="text-slate-500">Total Reports</span>
                  <span className="font-bold text-off-white tabular-nums">{profile.total_reports}</span>
                </div>
                <div className="flex justify-between items-center text-sm font-mono">
                  <span className="text-slate-500">Safe Messages</span>
                  <span className="font-bold text-verified-teal tabular-nums">{profile.safe_messages}</span>
                </div>
                <div className="flex justify-between items-center text-sm font-mono">
                  <span className="text-slate-500">Harmful Messages</span>
                  <span className="font-bold text-redaction-red tabular-nums">{profile.harmful_messages}</span>
                </div>
                <div className="flex justify-between items-center text-sm font-mono border-t border-slate-700 pt-3">
                  <span className="text-slate-500">Highest Safety Risk Seen</span>
                  <span className="font-bold text-off-white tabular-nums">{profile.highest_risk.toFixed(1)}</span>
                </div>
                <div className="flex justify-between items-center text-sm font-mono">
                  <span className="text-slate-500">Average Safety Risk</span>
                  <span className="font-bold text-off-white tabular-nums">{profile.avg_risk.toFixed(1)}</span>
                </div>
              </Card>
            </div>

            {/* Categories */}
            <div>
              <h3 className="text-xs font-bold text-slate-500 font-mono uppercase tracking-wider mb-3 flex items-center gap-2">
                <Activity size={14} /> Category Distribution
              </h3>
              <Card className="p-4 space-y-3 bg-panel border-slate-700 rounded-none">
                {categories.length > 0 ? (
                  categories.map(([cat, count]) => (
                    <div key={cat} className="flex justify-between items-center text-sm font-mono">
                      <span className="text-slate-400">{cat}</span>
                      <span className="font-bold px-2 py-0.5 bg-slate-800 border border-slate-700 text-off-white rounded-none tabular-nums">
                        {count}
                      </span>
                    </div>
                  ))
                ) : (
                  <div className="text-sm text-slate-500 font-mono">No categories recorded.</div>
                )}
              </Card>
            </div>
          </div>

          {/* Timeline */}
          <div>
            <h3 className="text-xs font-bold text-slate-500 font-mono uppercase tracking-wider mb-3 flex items-center gap-2">
              <Activity size={14} /> Behavioral Timeline
            </h3>
            <div className="relative pl-4 space-y-6 before:absolute before:inset-y-0 before:left-[23px] before:w-px before:bg-slate-700">
              {(profile.timeline || []).map((t, idx) => (
                <div key={idx} className="relative flex items-start gap-4">
                  <div className="absolute -left-1 mt-1.5 w-2 h-2 bg-slate-500 rounded-none border border-slate-700" />
                  <div className="ml-6 flex-1 bg-panel p-4 rounded-none border border-slate-700 shadow-sm">
                    <div className="flex justify-between items-center mb-1 font-mono">
                      <span className={`inline-flex items-center px-2 py-0.5 text-xs font-bold uppercase border ${getLevelColor(t.level)}`}>
                        {t.level}
                      </span>
                      <span className="text-xs text-slate-500">
                        {new Date(t.timestamp).toLocaleString()}
                      </span>
                    </div>
                    <p className="text-sm text-off-white mt-2 font-mono">{t.reason}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>

        </div>
      </div>
    </>
  );
}
