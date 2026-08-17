import React, { useState } from 'react';
import { AlertTriangle, ShieldCheck, CheckSquare, Square, Info, Phone } from 'lucide-react';
import Card from '../common/Card';

export default function GuidancePanel({ guidance }) {
  if (!guidance) return null;
  const [checkedItems, setCheckedItems] = useState({});
  const toggleCheck = (i) => setCheckedItems(prev => ({ ...prev, [i]: !prev[i] }));

  return (
    <div className="space-y-4">
      {/* ── Critical Resources Banner ── */}
      {guidance.show_critical_resources && guidance.critical_resources && (
        <div className="border border-danger bg-danger-bg rounded-lg p-4 flex gap-3">
          <div className="flex-shrink-0 mt-0.5">
            <AlertTriangle size={18} className="text-danger" />
          </div>
          <div className="space-y-1.5">
            <p className="text-sm font-bold text-danger">Critical Incident — Immediate Help Available</p>
            <p className="text-sm text-text-secondary">
              <span className="font-semibold text-text-primary">{guidance.critical_resources.helpline_title}</span>: {guidance.critical_resources.helpline_desc}
            </p>
            {guidance.critical_resources.url && (
              <a href={guidance.critical_resources.url} target="_blank" rel="noopener noreferrer"
                className="text-blue hover:text-blue-dim text-sm underline inline-block">
                {guidance.critical_resources.url}
              </a>
            )}
            <div className="flex flex-wrap gap-4 mt-1">
              {guidance.critical_resources.primary_phone && (
                <div className="flex items-center gap-1.5 text-sm">
                  <Phone size={13} className="text-text-muted" />
                  <span className="font-mono font-semibold text-text-primary">{guidance.critical_resources.primary_phone}</span>
                </div>
              )}
              {guidance.critical_resources.women_helpline_phone && (
                <div className="flex items-center gap-1.5 text-sm">
                  <Phone size={13} className="text-text-muted" />
                  <span className="font-mono font-semibold text-text-primary">{guidance.critical_resources.women_helpline_phone}</span>
                  <span className="text-text-muted text-xs">(Women's Helpline)</span>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* ── Platform Instructions ── */}
        <Card>
          <div className="flex items-center gap-2 mb-3">
            <Info size={14} className="text-blue" />
            <p className="text-sm font-semibold text-text-primary">Action Plan — {guidance.platform_name}</p>
          </div>
          <div className="space-y-3">
            <div>
              <p className="text-2xs font-semibold text-text-muted uppercase tracking-widest mb-1">Reporting</p>
              <p className="text-sm text-text-secondary leading-relaxed">{guidance.report_instructions}</p>
            </div>
            <div className="border-t border-border pt-3">
              <p className="text-2xs font-semibold text-text-muted uppercase tracking-widest mb-1">Blocking</p>
              <p className="text-sm text-text-secondary leading-relaxed">{guidance.block_instructions}</p>
            </div>
          </div>
        </Card>

        {/* ── Evidence Checklist ── */}
        {guidance.evidence_checklist && guidance.evidence_checklist.length > 0 && (
          <Card>
            <div className="flex items-center gap-2 mb-1">
              <ShieldCheck size={14} className="text-blue" />
              <p className="text-sm font-semibold text-text-primary">Evidence Preservation</p>
            </div>
            <p className="text-xs text-text-muted mb-3">Complete before reporting or blocking.</p>
            <div className="space-y-2.5">
              {guidance.evidence_checklist.map((item, idx) => (
                <label key={idx} className="flex items-start gap-2.5 cursor-pointer group" onClick={() => toggleCheck(idx)}>
                  <div className="flex-shrink-0 mt-0.5">
                    {checkedItems[idx]
                      ? <CheckSquare size={15} className="text-success" />
                      : <Square size={15} className="text-text-muted group-hover:text-text-secondary transition-colors" />
                    }
                  </div>
                  <span className={`text-sm select-none leading-snug transition-colors ${
                    checkedItems[idx] ? 'text-text-disabled line-through' : 'text-text-secondary group-hover:text-text-primary'
                  }`}>
                    {item}
                  </span>
                </label>
              ))}
            </div>
          </Card>
        )}
      </div>
    </div>
  );
}
