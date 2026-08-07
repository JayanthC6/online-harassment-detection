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
        className="fixed inset-y-0 right-0 w-full max-w-2xl bg-[#F8FAFC] shadow-2xl z-50 overflow-y-auto border-l border-slate-200 transform transition-transform duration-300 ease-in-out"
      >
        <div className="sticky top-0 bg-white border-b border-slate-200 px-6 py-4 flex justify-between items-center z-10">
          <div>
            <h2 className="text-xl font-semibold text-slate-900 flex items-center gap-2">
              <User className="text-slate-400" size={20} />
              {profile.actor_id}
            </h2>
            <p className="text-xs text-slate-500 mt-1">
              First seen: {new Date(profile.first_seen).toLocaleString()}
            </p>
          </div>
          <button 
            onClick={onClose}
            className="p-2 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-full transition-colors"
          >
            <X size={20} />
          </button>
        </div>

        <div className="p-6 space-y-6">
          
          {/* Score Overview */}
          <div className="flex gap-4">
            <Card className="flex-1 p-5 flex flex-col justify-center">
              <div className="text-sm font-medium text-slate-500 mb-1 flex items-center gap-2">
                <Activity size={16} /> Safety Score
              </div>
              <div className={`text-4xl font-bold ${getScoreColor(profile.behavior_score)}`}>
                {profile.behavior_score.toFixed(1)}
              </div>
            </Card>
            <Card className="flex-1 p-5 flex flex-col justify-center">
              <div className="text-sm font-medium text-slate-500 mb-1 flex items-center gap-2">
                <ShieldAlert size={16} /> Safety Level
              </div>
              <div>
                <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-semibold border ${getLevelColor(profile.behavior_level)}`}>
                  {profile.behavior_level}
                </span>
              </div>
            </Card>
          </div>

          {/* AI Recommendation */}
          <Card className="bg-indigo-50/50 border-indigo-100 p-5">
            <div className="flex items-start gap-3">
              <div className="p-2 bg-indigo-100 text-indigo-600 rounded-lg">
                <Info size={18} />
              </div>
              <div>
                <h3 className="text-xs font-bold text-indigo-800 uppercase tracking-wider mb-1">
                  AI Recommendation
                </h3>
                <p className="text-sm text-indigo-900 font-medium">
                  {profile.recommendation}
                </p>
              </div>
            </div>
          </Card>

          {/* Explainability / Logic */}
          <div>
            <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3 flex items-center gap-2">
              <TrendingUp size={14} /> Score Factors
            </h3>
            <Card className="p-0 overflow-hidden divide-y divide-slate-100">
              {profile.explanation && profile.explanation.length > 0 ? (
                profile.explanation.map((exp, idx) => (
                  <div key={idx} className="p-4 flex items-start gap-3 bg-white">
                    <div className="mt-0.5 w-2 h-2 rounded-full bg-slate-300 flex-shrink-0" />
                    <p className="text-sm text-slate-700">{exp}</p>
                  </div>
                ))
              ) : (
                <div className="p-4 text-sm text-slate-500 bg-white">No factors recorded.</div>
              )}
            </Card>
          </div>

          <div className="grid grid-cols-2 gap-6">
            {/* Stats */}
            <div>
              <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3 flex items-center gap-2">
                <BarChart2 size={14} /> Overall Statistics
              </h3>
              <Card className="p-4 space-y-3">
                <div className="flex justify-between items-center text-sm">
                  <span className="text-slate-500">Total Reports</span>
                  <span className="font-semibold text-slate-800">{profile.total_reports}</span>
                </div>
                <div className="flex justify-between items-center text-sm">
                  <span className="text-slate-500">Safe Messages</span>
                  <span className="font-semibold text-emerald-600">{profile.safe_messages}</span>
                </div>
                <div className="flex justify-between items-center text-sm">
                  <span className="text-slate-500">Harmful Messages</span>
                  <span className="font-semibold text-rose-600">{profile.harmful_messages}</span>
                </div>
                <div className="flex justify-between items-center text-sm border-t border-slate-100 pt-3">
                  <span className="text-slate-500">Highest Safety Risk Seen</span>
                  <span className="font-semibold text-slate-800">{profile.highest_risk.toFixed(1)}</span>
                </div>
                <div className="flex justify-between items-center text-sm">
                  <span className="text-slate-500">Average Safety Risk</span>
                  <span className="font-semibold text-slate-800">{profile.avg_risk.toFixed(1)}</span>
                </div>
              </Card>
            </div>

            {/* Categories */}
            <div>
              <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3 flex items-center gap-2">
                <Activity size={14} /> Category Distribution
              </h3>
              <Card className="p-4 space-y-3">
                {categories.length > 0 ? (
                  categories.map(([cat, count]) => (
                    <div key={cat} className="flex justify-between items-center text-sm">
                      <span className="text-slate-600">{cat}</span>
                      <span className="font-medium px-2 py-0.5 bg-slate-100 text-slate-700 rounded-md">
                        {count}
                      </span>
                    </div>
                  ))
                ) : (
                  <div className="text-sm text-slate-500">No categories recorded.</div>
                )}
              </Card>
            </div>
          </div>

          {/* Timeline */}
          <div>
            <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3 flex items-center gap-2">
              <Activity size={14} /> Behavioral Timeline
            </h3>
            <div className="relative pl-4 space-y-6 before:absolute before:inset-y-0 before:left-[23px] before:w-0.5 before:bg-slate-200">
              {(profile.timeline || []).map((t, idx) => (
                <div key={idx} className="relative flex items-start gap-4">
                  <div className="absolute -left-1.5 mt-1 w-3 h-3 bg-white border-2 border-indigo-400 rounded-full" />
                  <div className="ml-6 flex-1 bg-white p-4 rounded-lg border border-slate-200 shadow-sm">
                    <div className="flex justify-between items-center mb-1">
                      <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold border ${getLevelColor(t.level)}`}>
                        {t.level}
                      </span>
                      <span className="text-xs text-slate-400">
                        {new Date(t.timestamp).toLocaleString()}
                      </span>
                    </div>
                    <p className="text-sm text-slate-600 mt-2">{t.reason}</p>
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
