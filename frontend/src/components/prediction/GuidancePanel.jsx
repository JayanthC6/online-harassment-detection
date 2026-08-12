import React, { useState } from 'react';
import { AlertTriangle, Shield, CheckSquare, Square, Info } from 'lucide-react';
import Card from '../common/Card';

export default function GuidancePanel({ guidance }) {
  if (!guidance) return null;

  const [checkedItems, setCheckedItems] = useState({});

  const toggleCheck = (index) => {
    setCheckedItems(prev => ({ ...prev, [index]: !prev[index] }));
  };

  return (
    <div className="space-y-4">
      {/* Critical Resources Banner */}
      {guidance.show_critical_resources && guidance.critical_resources && (
        <div className="bg-slate-900 border-l-4 border-redaction-red p-4 rounded-none">
          <div className="flex items-start">
            <div className="flex-shrink-0 mt-0.5">
              <AlertTriangle className="h-5 w-5 text-redaction-red" />
            </div>
            <div className="ml-3">
              <h3 className="text-sm font-bold text-redaction-red font-mono uppercase tracking-wide">CRITICAL INCIDENT: Immediate Help is Available</h3>
              <div className="mt-2 text-sm text-slate-300 space-y-2">
                <p>
                  <strong className="text-off-white">{guidance.critical_resources.helpline_title}</strong>: {guidance.critical_resources.helpline_desc}
                  <br/>
                  <a href={guidance.critical_resources.url} target="_blank" rel="noopener noreferrer" className="font-semibold text-alert-amber hover:text-amber-400 underline">{guidance.critical_resources.url}</a>
                  <br/>
                  Call: <span className="font-bold text-off-white">{guidance.critical_resources.primary_phone}</span>
                </p>
                <p>
                  <strong className="text-off-white">{guidance.critical_resources.women_helpline_title}</strong>: Call <span className="font-bold text-off-white">{guidance.critical_resources.women_helpline_phone}</span>
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Platform Instructions */}
      <Card className="bg-panel border-slate-700">
        <div className="flex items-center gap-2 mb-3">
          <Info size={16} className="text-slate-500" />
          <h3 className="text-sm font-bold text-off-white font-mono uppercase tracking-wider">Action Plan: {guidance.platform_name}</h3>
        </div>
        <div className="space-y-3 text-sm text-slate-400">
          <div>
            <p className="font-bold text-off-white font-mono mb-1">Reporting</p>
            <p>{guidance.report_instructions}</p>
          </div>
          <div>
            <p className="font-bold text-off-white font-mono mb-1">Blocking</p>
            <p>{guidance.block_instructions}</p>
          </div>
        </div>
      </Card>

      {/* Evidence Preservation Checklist */}
      {guidance.evidence_checklist && guidance.evidence_checklist.length > 0 && (
        <Card className="bg-panel border-slate-700">
          <div className="flex items-center gap-2 mb-3">
            <Shield size={16} className="text-slate-500" />
            <h3 className="text-sm font-bold text-off-white font-mono uppercase tracking-wider">Evidence Preservation Checklist</h3>
          </div>
          <p className="text-xs text-slate-500 font-mono mb-4">Complete these steps before reporting or blocking the user.</p>
          <div className="space-y-2">
            {guidance.evidence_checklist.map((item, idx) => (
              <label key={idx} className="flex items-start gap-3 cursor-pointer group">
                <div 
                  className="mt-0.5 flex-shrink-0"
                  onClick={() => toggleCheck(idx)}
                >
                  {checkedItems[idx] ? (
                    <CheckSquare size={16} className="text-verified-teal" />
                  ) : (
                    <Square size={16} className="text-slate-500 group-hover:text-slate-400 transition-colors" />
                  )}
                </div>
                <span className={`text-sm select-none transition-colors ${checkedItems[idx] ? 'text-slate-600 line-through' : 'text-slate-300 group-hover:text-off-white'}`}>
                  {item}
                </span>
              </label>
            ))}
          </div>
        </Card>
      )}
    </div>
  );
}
