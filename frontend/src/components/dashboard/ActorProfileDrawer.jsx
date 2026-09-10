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
      case 'Critical': return 'text-white bg-critical/80 shadow-[0_0_10px_rgba(244,63,94,0.4)] border-critical rounded';
      case 'High': return 'text-white bg-danger/80 shadow-[0_0_10px_rgba(249,115,22,0.4)] border-danger rounded';
      case 'Watch': return 'text-text-primary bg-black/40 border-border/50 rounded';
      default: return 'text-success bg-success/20 border-success/30 rounded';
    }
  };

  const getScoreColor = (score) => {
    if (score >= 85) return 'text-critical drop-shadow-[0_0_5px_rgba(244,63,94,0.5)]';
    if (score >= 60) return 'text-danger drop-shadow-[0_0_5px_rgba(249,115,22,0.5)]';
    if (score >= 30) return 'text-text-primary';
    return 'text-success drop-shadow-[0_0_5px_rgba(16,185,129,0.5)]';
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
        className="fixed inset-y-0 right-0 w-full max-w-2xl bg-[#060913]/95 backdrop-blur-3xl shadow-[0_0_50px_rgba(0,242,254,0.1)] z-50 overflow-y-auto border-l border-blue/30 transform transition-transform duration-300 ease-in-out"
      >
        <div className="sticky top-0 bg-black/40 border-b border-border/50 shadow-inner px-6 py-4 flex justify-between items-center z-10">
          <div>
            <h2 className="text-xl font-bold text-white font-mono uppercase tracking-wider flex items-center gap-2 drop-shadow-[0_0_2px_rgba(255,255,255,0.3)]">
              <User className="text-blue shadow-[0_0_5px_rgba(0,242,254,0.5)]" size={20} />
              {profile.actor_id}
            </h2>
            <p className="text-xs text-text-muted mt-1">
              First seen: {new Date(profile.first_seen).toLocaleString()}
            </p>
          </div>
          <button 
            onClick={onClose}
            className="p-2 text-text-muted hover:text-white hover:bg-white/5 border border-transparent hover:border-border transition-colors rounded"
          >
            <X size={20} />
          </button>
        </div>

        <div className="p-6 space-y-6">
          
          {/* Score Overview */}
          <div className="flex gap-4">
            <Card className="flex-1 p-5 flex flex-col justify-center bg-black/40 border border-border/50 rounded-xl shadow-inner">
              <div className="text-sm font-bold text-text-muted font-mono uppercase tracking-wider mb-1 flex items-center gap-2">
                <Activity size={16} /> Safety Score
              </div>
              <div className={`text-4xl font-bold font-mono tabular-nums ${getScoreColor(profile.behavior_score)}`}>
                {profile.behavior_score.toFixed(1)}
              </div>
            </Card>
            <Card className="flex-1 p-5 flex flex-col justify-center bg-black/40 border border-border/50 rounded-xl shadow-inner">
              <div className="text-sm font-bold text-text-muted font-mono uppercase tracking-wider mb-1 flex items-center gap-2">
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
          <Card className="bg-black/40 border border-purple/30 rounded-xl p-5 shadow-[inset_0_0_15px_rgba(168,85,247,0.15)] relative overflow-hidden">
            <div className="absolute top-0 left-0 w-1 h-full bg-gradient-to-b from-purple to-blue"></div>
            <div className="flex items-start gap-3 relative z-10">
              <div className="p-2 bg-black/40 border border-purple/30 text-purple rounded-md shadow-inner">
                <Info size={18} />
              </div>
              <div>
                <h3 className="text-xs font-bold text-text-muted font-mono uppercase tracking-wider mb-1 drop-shadow-[0_0_2px_rgba(255,255,255,0.1)]">
                  AI Recommendation
                </h3>
                <p className="text-sm text-white font-mono">
                  {profile.recommendation}
                </p>
              </div>
            </div>
          </Card>

          {/* Explainability / Logic */}
          <div>
            <h3 className="text-xs font-bold text-text-muted font-mono uppercase tracking-wider mb-3 flex items-center gap-2">
              <TrendingUp size={14} /> Score Factors
            </h3>
            <Card className="p-0 overflow-hidden divide-y divide-border/50 bg-black/40 border-border/50 rounded-xl shadow-inner">
              {profile.explanation && profile.explanation.length > 0 ? (
                profile.explanation.map((exp, idx) => (
                  <div key={idx} className="p-4 flex items-start gap-3 bg-black/40 hover:bg-white/5 transition-colors">
                    <div className="mt-1.5 w-1.5 h-1.5 bg-blue shadow-[0_0_5px_rgba(0,242,254,0.5)] rounded-full flex-shrink-0" />
                    <p className="text-sm text-text-primary font-mono">{exp}</p>
                  </div>
                ))
              ) : (
                <div className="p-4 text-sm text-text-muted bg-black/40 font-mono">No factors recorded.</div>
              )}
            </Card>
          </div>

          <div className="grid grid-cols-2 gap-6">
            {/* Stats */}
            <div>
              <h3 className="text-xs font-bold text-text-muted font-mono uppercase tracking-wider mb-3 flex items-center gap-2">
                <BarChart2 size={14} /> Overall Statistics
              </h3>
              <Card className="p-4 space-y-3 bg-black/40 border border-border/50 rounded-xl shadow-inner">
                <div className="flex justify-between items-center text-sm font-mono">
                  <span className="text-text-muted">Total Reports</span>
                  <span className="font-bold text-white tabular-nums">{profile.total_reports}</span>
                </div>
                <div className="flex justify-between items-center text-sm font-mono">
                  <span className="text-text-muted">Safe Messages</span>
                  <span className="font-bold text-success drop-shadow-[0_0_2px_rgba(16,185,129,0.3)] tabular-nums">{profile.safe_messages}</span>
                </div>
                <div className="flex justify-between items-center text-sm font-mono">
                  <span className="text-text-muted">Harmful Messages</span>
                  <span className="font-bold text-critical drop-shadow-[0_0_2px_rgba(244,63,94,0.3)] tabular-nums">{profile.harmful_messages}</span>
                </div>
                <div className="flex justify-between items-center text-sm font-mono border-t border-border/50 pt-3">
                  <span className="text-text-muted">Highest Safety Risk Seen</span>
                  <span className="font-bold text-white tabular-nums">{profile.highest_risk.toFixed(1)}</span>
                </div>
                <div className="flex justify-between items-center text-sm font-mono">
                  <span className="text-text-muted">Average Safety Risk</span>
                  <span className="font-bold text-white tabular-nums">{profile.avg_risk.toFixed(1)}</span>
                </div>
              </Card>
            </div>

            {/* Categories */}
            <div>
              <h3 className="text-xs font-bold text-text-muted font-mono uppercase tracking-wider mb-3 flex items-center gap-2">
                <Activity size={14} /> Category Distribution
              </h3>
              <Card className="p-4 space-y-3 bg-black/40 border border-border/50 rounded-xl shadow-inner">
                {categories.length > 0 ? (
                  categories.map(([cat, count]) => (
                    <div key={cat} className="flex justify-between items-center text-sm font-mono">
                      <span className="text-text-primary">{cat}</span>
                      <span className="font-bold px-2 py-0.5 bg-black/40 border border-border/50 text-white rounded tabular-nums">
                        {count}
                      </span>
                    </div>
                  ))
                ) : (
                  <div className="text-sm text-text-muted font-mono">No categories recorded.</div>
                )}
              </Card>
            </div>
          </div>

          {/* Timeline */}
          <div>
            <h3 className="text-xs font-bold text-text-muted font-mono uppercase tracking-wider mb-3 flex items-center gap-2">
              <Activity size={14} /> Behavioral Timeline
            </h3>
            <div className="relative pl-4 space-y-6 before:absolute before:inset-y-0 before:left-[23px] before:w-px before:bg-border/50">
              {(profile.timeline || []).map((t, idx) => (
                <div key={idx} className="relative flex items-start gap-4">
                  <div className="absolute -left-1 mt-1.5 w-2 h-2 bg-text-muted shadow-[0_0_5px_rgba(148,163,184,0.5)] rounded-full border border-border/50" />
                  <div className="ml-6 flex-1 bg-black/40 p-4 rounded-xl border border-border/50 shadow-inner">
                    <div className="flex justify-between items-center mb-1 font-mono">
                      <span className={`inline-flex items-center px-2 py-0.5 text-xs font-bold uppercase border shadow-sm ${getLevelColor(t.level)}`}>
                        {t.level}
                      </span>
                      <span className="text-xs text-text-muted">
                        {new Date(t.timestamp).toLocaleString()}
                      </span>
                    </div>
                    <p className="text-sm text-white mt-2 font-mono">{t.reason}</p>
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
