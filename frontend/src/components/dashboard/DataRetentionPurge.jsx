import React, { useState } from 'react';
import { Trash2, ShieldCheck, AlertTriangle, Clock, Lock, CheckCircle2, RefreshCw } from 'lucide-react';
import { apiClient } from '../../api/client';
import Card from '../common/Card';

export default function DataRetentionPurge({ onPurgeSuccess }) {
  const [retentionDays, setRetentionDays] = useState(90);
  const [customDays, setCustomDays] = useState('');
  const [confirming, setConfirming] = useState(false);
  const [purging, setPurging] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const daysToPurge = customDays ? parseInt(customDays, 10) : retentionDays;

  const handleExecutePurge = async () => {
    if (isNaN(daysToPurge) || daysToPurge < 1) {
      setError('Please provide a valid positive number of retention days.');
      return;
    }

    setPurging(true);
    setError(null);
    setResult(null);

    try {
      const data = await apiClient('/admin/purge', {
        method: 'POST',
        body: JSON.stringify({ days: daysToPurge })
      });
      setResult(data);
      setConfirming(false);
      if (onPurgeSuccess) onPurgeSuccess(data);
    } catch (err) {
      setError(err.message || 'Failed to execute data purge.');
    } finally {
      setPurging(false);
    }
  };

  return (
    <div className="space-y-6 animate-fade-in">
      {/* ── Privacy & Masking Policy Overview ── */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card className="p-5 bg-surface/70 border border-border">
          <div className="flex items-center gap-2 mb-3">
            <Lock size={16} className="text-cyan-400" />
            <h3 className="text-sm font-bold text-text-primary uppercase font-mono tracking-wider">
              PII Masking & Data Sanitization
            </h3>
          </div>
          <p className="text-xs text-text-secondary leading-relaxed">
            ShieldAI automatically redacts personally identifiable information (PII) before storing user complaints and threat logs.
          </p>
          <ul className="mt-3 space-y-1.5 text-xs text-text-muted font-mono">
            <li className="flex items-center gap-1.5 text-emerald-400">
              <CheckCircle2 size={13} /> Phone numbers masked (+91 ••••••••23)
            </li>
            <li className="flex items-center gap-1.5 text-emerald-400">
              <CheckCircle2 size={13} /> Email addresses masked (u•••@domain.com)
            </li>
            <li className="flex items-center gap-1.5 text-emerald-400">
              <CheckCircle2 size={13} /> Aadhaar & 12-digit IDs masked (•••• •••• 1234)
            </li>
          </ul>
        </Card>

        <Card className="p-5 bg-surface/70 border border-border">
          <div className="flex items-center gap-2 mb-3">
            <Clock size={16} className="text-purple-400" />
            <h3 className="text-sm font-bold text-text-primary uppercase font-mono tracking-wider">
              Configurable Data Retention
            </h3>
          </div>
          <p className="text-xs text-text-secondary leading-relaxed">
            Organizations can enforce statutory data retention rules by routinely purging historical logs and forensic evidence older than a specific window.
          </p>
          <div className="mt-3 text-xs font-mono text-text-muted">
            Default policy: <strong className="text-text-primary">90 days</strong> (configured via <code className="text-cyan-400 bg-black/40 px-1 py-0.5 rounded">DATA_RETENTION_DAYS</code> env)
          </div>
        </Card>
      </div>

      {/* ── Purge Controls ── */}
      <Card className="p-6 bg-surface border border-red-500/20 shadow-lg">
        <div className="flex items-center gap-2.5 mb-4 pb-3 border-b border-border/50">
          <Trash2 size={18} className="text-red-400" />
          <h3 className="text-sm font-bold text-red-200 uppercase font-mono tracking-wider">
            Execute Historical Incident Purge
          </h3>
        </div>

        <p className="text-xs text-text-secondary mb-4 leading-relaxed">
          Select the retention threshold. All safety incidents, conversation traces, and message logs older than this age will be permanently expunged from the database.
        </p>

        {/* Retention Presets */}
        <div className="flex flex-wrap items-center gap-2 mb-5">
          <span className="text-xs font-mono text-text-muted mr-2">Retention Cutoff:</span>
          {[30, 60, 90, 180, 365].map((d) => (
            <button
              key={d}
              type="button"
              onClick={() => { setRetentionDays(d); setCustomDays(''); }}
              className={`px-3 py-1.5 rounded-lg text-xs font-mono transition-colors ${
                retentionDays === d && !customDays
                  ? 'bg-blue/20 text-blue border border-blue/40 font-bold'
                  : 'bg-surface-solid hover:bg-surface-2 text-text-secondary border border-border'
              }`}
            >
              {d} Days
            </button>
          ))}
          <div className="flex items-center gap-1.5 ml-2">
            <input
              type="number"
              min="1"
              max="3650"
              placeholder="Custom days..."
              value={customDays}
              onChange={(e) => setCustomDays(e.target.value)}
              className="input w-32 py-1 text-xs"
            />
          </div>
        </div>

        {/* Confirmation State */}
        {!confirming ? (
          <button
            type="button"
            onClick={() => setConfirming(true)}
            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-red-500/20 hover:bg-red-500/30 text-red-200 border border-red-500/40 text-xs font-mono font-bold transition-colors cursor-pointer"
          >
            <Trash2 size={14} />
            Purge Records Older Than {daysToPurge} Days
          </button>
        ) : (
          <div className="p-4 rounded-xl bg-red-950/60 border border-red-500/50 space-y-3 animate-fade-in">
            <div className="flex items-start gap-2.5 text-red-200 text-xs">
              <AlertTriangle size={18} className="text-red-400 shrink-0 mt-0.5" />
              <div>
                <p className="font-bold text-red-100 uppercase tracking-wide font-mono">
                  Confirm Data Purge Operation
                </p>
                <p className="mt-1 text-red-200/90 leading-relaxed">
                  Are you sure you want to permanently delete all records older than <strong>{daysToPurge} days</strong>? This operation cannot be undone. An audit record will be logged.
                </p>
              </div>
            </div>

            <div className="flex items-center gap-2 pt-2">
              <button
                type="button"
                disabled={purging}
                onClick={handleExecutePurge}
                className="flex items-center gap-1.5 px-4 py-1.5 rounded-lg bg-red-600 hover:bg-red-500 text-white font-mono text-xs font-bold transition-colors disabled:opacity-50 cursor-pointer shadow-lg shadow-red-900/50"
              >
                {purging && <RefreshCw size={13} className="animate-spin" />}
                {purging ? 'Purging Database...' : 'Yes, Permanently Purge'}
              </button>
              <button
                type="button"
                disabled={purging}
                onClick={() => setConfirming(false)}
                className="px-3 py-1.5 rounded-lg bg-surface hover:bg-surface-2 text-text-secondary border border-border text-xs font-mono transition-colors"
              >
                Cancel
              </button>
            </div>
          </div>
        )}

        {/* Purge Result Feedback */}
        {result && (
          <div className="mt-4 p-4 rounded-xl bg-emerald-950/50 border border-emerald-500/40 text-emerald-200 text-xs font-mono space-y-1 animate-fade-in">
            <div className="flex items-center gap-2 font-bold text-emerald-300">
              <CheckCircle2 size={16} />
              Purge Completed Successfully
            </div>
            <p>Retention cutoff applied: {result.retention_days} days</p>
            <p>Purged Reports: {result.purged_reports || 0} records</p>
            <p>Purged Conversations: {result.purged_conversations || 0} records</p>
          </div>
        )}

        {error && (
          <div className="mt-4 p-3 rounded-xl bg-red-950/40 border border-red-500/40 text-red-300 text-xs font-mono">
            {error}
          </div>
        )}
      </Card>
    </div>
  );
}

