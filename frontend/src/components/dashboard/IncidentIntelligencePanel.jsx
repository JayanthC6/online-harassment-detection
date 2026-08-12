import { useState, useEffect } from 'react';
import PropTypes from 'prop-types';
import { X, MessageSquare, Shield, Activity, Cpu, Tag, FileText, Link, Clock, Sparkles, AlertTriangle, Lightbulb } from 'lucide-react';
import { apiClient } from '../../api/client';
import Card from '../common/Card';
import GuidancePanel from '../prediction/GuidancePanel';

export default function IncidentIntelligencePanel({ report, onClose }) {
  const [summary, setSummary] = useState(null);
  const [loadingSummary, setLoadingSummary] = useState(false);

  useEffect(() => {
    setSummary(null);
  }, [report]);

  if (!report) return null;

  const handleSummarize = async () => {
    setLoadingSummary(true);
    try {
      const data = await apiClient('/summarize', {
        method: 'POST',
        body: JSON.stringify({
          text: report.text_preview,
          category: report.category,
          confidence: report.confidence
        })
      });
      setSummary(data.summary || data.error);
    } catch (e) {
      setSummary('Failed to generate summary.');
    } finally {
      setLoadingSummary(false);
    }
  };

  const explanationsList = Array.isArray(report.explanation) ? report.explanation : [];
  const highlightedWords = explanationsList.map(ex => ex.word);
  
  let highlightedText = report.text_preview || '';
  if (highlightedWords.length > 0) {
    highlightedWords.forEach(word => {
      const safeWord = word.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
      const regex = new RegExp(`\\b(${safeWord})\\b`, 'gi');
      highlightedText = highlightedText.replace(regex, '<mark class="bg-manila text-ink rounded-none px-1">$1</mark>');
    });
  }

  return (
    <>
      <div 
        className="fixed inset-0 bg-slate-900/20 backdrop-blur-sm z-40 transition-opacity"
        onClick={onClose}
        aria-label="Close panel background"
      />
      
      <div 
        role="dialog"
        aria-label="Incident Intelligence Panel"
        className="fixed inset-y-0 right-0 w-full md:w-[600px] bg-ink shadow-2xl z-50 flex flex-col overflow-hidden animate-slide-left border-l border-slate-700"
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-700 bg-panel sticky top-0 z-10">
          <div>
            <h2 className="text-xl font-bold text-off-white font-display uppercase tracking-wider">Incident Intelligence</h2>
            <p className="text-xs text-slate-400 font-mono mt-0.5">ID: {report.cluster_id || 'unclustered'}-{new Date(report.logged_at).getTime()}</p>
          </div>
          <button 
            onClick={onClose}
            className="p-2 text-slate-400 hover:text-off-white hover:bg-slate-800 border border-transparent hover:border-slate-700 transition-colors focus:outline-none"
            aria-label="Close incident intelligence panel"
          >
            <X size={20} />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          
          {/* 1. Summary */}
          <section>
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-xs font-bold text-slate-500 font-mono uppercase tracking-wider flex items-center gap-1.5"><FileText size={14} /> Executive Summary</h3>
              {!summary && (
                <button 
                  onClick={handleSummarize}
                  disabled={loadingSummary}
                  className="text-xs px-3 py-1.5 bg-slate-800 text-slate-300 border border-slate-700 hover:bg-slate-700 rounded-none font-bold font-mono transition-colors disabled:opacity-50 flex items-center gap-1"
                >
                  {loadingSummary ? <Sparkles size={12} className="animate-spin" /> : <Sparkles size={12} />}
                  {loadingSummary ? 'Generating...' : 'Generate Summary'}
                </button>
              )}
            </div>
            
            {summary ? (
              <Card className="bg-slate-900 border-slate-700 rounded-none p-4">
                <p className="text-sm text-off-white leading-relaxed font-mono">
                  {summary}
                </p>
              </Card>
            ) : !loadingSummary ? (
              <Card className="p-4 flex items-center justify-center bg-panel border-slate-700 rounded-none border-dashed">
                <p className="text-sm text-slate-500 font-mono italic">No summary generated. Click above to generate an AI summary.</p>
              </Card>
            ) : null}
          </section>

          {/* 2. Classification */}
          <section>
            <h3 className="text-xs font-bold text-slate-500 font-mono uppercase tracking-wider mb-3 flex items-center gap-1.5"><Tag size={14} /> Incident Classification</h3>
            
            <div className="grid grid-cols-2 gap-4 mb-4">
              <Card className="p-4 flex flex-col justify-center bg-panel border-slate-700 rounded-none shadow-none">
                <p className="text-[10px] text-slate-400 font-mono uppercase tracking-wider mb-1 flex items-center gap-1"><Activity size={12} /> Safety Score</p>
                <div className="flex items-end gap-2">
                  <span className={`text-3xl font-bold font-mono tabular-nums leading-none ${report.risk_score >= 75 ? 'text-redaction-red' : report.risk_score >= 40 ? 'text-alert-amber' : 'text-verified-teal'}`}>
                    {report.risk_score}
                  </span>
                  <span className="text-slate-500 font-mono text-sm mb-1">/ 100</span>
                </div>
              </Card>
              
              <Card className="p-4 flex flex-col justify-center bg-panel border-slate-700 rounded-none shadow-none">
                <p className="text-[10px] text-slate-400 font-mono uppercase tracking-wider mb-1 flex items-center gap-1"><Shield size={12} /> Confidence</p>
                <div className="flex items-end gap-2">
                  <span className="text-3xl font-bold text-off-white font-mono tabular-nums leading-none">{(report.confidence * 100).toFixed(1)}%</span>
                </div>
              </Card>
            </div>

            <Card className="p-0 overflow-hidden divide-y divide-slate-700 bg-panel border-slate-700 rounded-none shadow-none">
              <div className="p-4 flex justify-between items-center relative overflow-hidden">
                <div 
                  className="absolute left-0 top-0 bottom-0 bg-redaction-red/20 z-0" 
                  style={{ width: `${(report.confidence || 0) * 100}%` }}
                />
                <div className="relative z-10 flex items-center gap-3">
                  <span className="text-[10px] font-bold font-mono uppercase tracking-wider text-ink bg-redaction-red px-2.5 py-1 rounded-none">Primary</span>
                  <span className="font-bold font-mono uppercase text-off-white text-sm">{report.primary_label || report.category.replace('_', ' ')}</span>
                </div>
                <span className="relative z-10 text-xs font-mono font-bold text-slate-400 tabular-nums">{(report.confidence * 100).toFixed(1)}% match</span>
              </div>
              
              {report.secondary_labels && Object.entries(report.secondary_labels).map(([label, conf]) => (
                <div key={label} className="p-4 flex justify-between items-center relative overflow-hidden">
                  <div 
                    className="absolute left-0 top-0 bottom-0 bg-alert-amber/20 z-0" 
                    style={{ width: `${conf * 100}%` }}
                  />
                  <div className="relative z-10 flex items-center gap-3">
                    <span className="text-[10px] font-bold font-mono uppercase tracking-wider text-ink bg-alert-amber px-2.5 py-1 rounded-none">Secondary</span>
                    <span className="font-bold font-mono text-slate-300 text-sm">{label}</span>
                  </div>
                  <span className="relative z-10 text-xs font-mono font-bold text-slate-400 tabular-nums">{(conf * 100).toFixed(1)}% match</span>
                </div>
              ))}
            </Card>
            <div className="mt-2 text-right">
              <span className="text-[10px] text-slate-500 font-mono uppercase tracking-wider flex items-center justify-end gap-1"><Cpu size={10} /> Model: {report.model}</span>
            </div>
          </section>

          {/* 3. Evidence */}
          <section>
            <h3 className="text-xs font-bold text-slate-500 font-mono uppercase tracking-wider mb-3 flex items-center gap-1.5"><MessageSquare size={14} /> Evidence</h3>
            <Card className="p-4 bg-panel border-slate-700 rounded-none shadow-none">
              <div 
                className="text-off-white text-sm leading-relaxed font-mono whitespace-pre-wrap"
                dangerouslySetInnerHTML={{ __html: highlightedWords.length > 0 ? highlightedText : report.text_preview }}
              />
            </Card>
          </section>

          {/* 4. Explainability */}
          {explanationsList.length > 0 && (
            <section>
              <h3 className="text-xs font-bold text-slate-500 font-mono uppercase tracking-wider mb-3 flex items-center gap-1.5"><Lightbulb size={14} /> Explainability</h3>
              <Card className="p-4 bg-panel border-slate-700 rounded-none shadow-none flex flex-wrap gap-2 items-center">
                {explanationsList.map((ex, i) => (
                  <span key={i} className="inline-flex items-center px-2.5 py-1 rounded-none text-xs font-bold font-mono bg-manila text-ink border border-manila" title={ex.reason || ''}>
                    {ex.word} <span className="ml-1.5 text-[10px] font-bold opacity-60">({ex.label ? ex.label : ex.contribution.toFixed(2)})</span>
                  </span>
                ))}
              </Card>
            </section>
          )}

          {/* 4.5 Threat Intelligence */}
          {report.threat_intel && (report.threat_intel.urls?.length > 0 || report.threat_intel.emails?.length > 0) && (
            <section>
              <h3 className="text-xs font-bold text-slate-500 font-mono uppercase tracking-wider mb-3 flex items-center gap-1.5"><Shield size={14} /> Threat Intelligence</h3>
              <div className="space-y-3">
                {report.threat_intel.urls?.map((u, i) => (
                  <Card key={i} className={`p-4 bg-panel border-slate-700 rounded-none shadow-none border-l-4 ${u.safe_browsing === 'unsafe' || u.typosquat_match ? 'border-l-redaction-red' : 'border-l-slate-700'}`}>
                    <div className="flex items-center gap-2 mb-2">
                      <Link size={14} className="text-slate-400" />
                      <span className="font-mono text-sm font-bold text-off-white break-all">{u.url}</span>
                    </div>
                    <div className="grid grid-cols-2 gap-2 mt-3">
                      {u.safe_browsing && (
                        <div>
                          <p className="text-[10px] font-mono text-slate-500 uppercase tracking-wider mb-1">Safe Browsing</p>
                          <span className={`inline-flex font-mono text-xs font-bold px-2 py-0.5 ${u.safe_browsing === 'unsafe' ? 'bg-redaction-red text-ink' : 'bg-verified-teal/20 text-verified-teal'}`}>
                            {u.safe_browsing === 'unsafe' ? 'UNSAFE (MATCH)' : 'CLEAN'}
                          </span>
                        </div>
                      )}
                      {u.domain_age_days !== undefined && (
                        <div>
                          <p className="text-[10px] font-mono text-slate-500 uppercase tracking-wider mb-1">Domain Age</p>
                          <span className={`inline-flex font-mono text-xs font-bold px-2 py-0.5 ${u.domain_age_days < 30 ? 'bg-alert-amber text-ink' : 'bg-slate-800 text-slate-300'}`}>
                            {u.domain_age_days} days
                          </span>
                        </div>
                      )}
                      {u.typosquat_match && (
                        <div className="col-span-2 mt-1">
                          <p className="text-[10px] font-mono text-slate-500 uppercase tracking-wider mb-1">Typosquat Detection</p>
                          <span className="inline-flex font-mono text-xs font-bold px-2 py-0.5 bg-redaction-red text-ink">
                            TARGETS: {u.typosquat_match}
                          </span>
                        </div>
                      )}
                    </div>
                  </Card>
                ))}
                
                {report.threat_intel.emails?.map((e, i) => (
                  <Card key={`e-${i}`} className="p-4 bg-panel border-slate-700 rounded-none shadow-none border-l-4 border-l-slate-700">
                    <div className="flex items-center gap-2 mb-2">
                      <MessageSquare size={14} className="text-slate-400" />
                      <span className="font-mono text-sm font-bold text-off-white break-all">{e.email}</span>
                    </div>
                    {e.breach_count !== undefined && (
                      <div className="mt-3">
                        <p className="text-[10px] font-mono text-slate-500 uppercase tracking-wider mb-1">Known Breaches (HIBP)</p>
                        <span className={`inline-flex font-mono text-xs font-bold px-2 py-0.5 ${e.breach_count > 0 ? 'bg-alert-amber text-ink' : 'bg-slate-800 text-slate-300'}`}>
                          {e.breach_count > 0 ? `${e.breach_count} BREACHES FOUND` : 'NO BREACHES'}
                        </span>
                      </div>
                    )}
                  </Card>
                ))}
              </div>
            </section>
          )}

          {/* 5. Timeline */}
          <section>
            <h3 className="text-xs font-bold text-slate-500 font-mono uppercase tracking-wider mb-4 flex items-center gap-1.5"><Clock size={14} /> Timeline</h3>
            <div className="relative border-l border-slate-700 ml-4 space-y-6 pb-2">
              
              <div className="relative pl-6">
                <div className="absolute w-2 h-2 bg-slate-500 rounded-none -left-[4.5px] top-1.5 border border-slate-700 ring-4 ring-ink" />
                <p className="text-sm font-bold font-mono text-off-white">Message Ingested</p>
                <p className="text-xs font-mono text-slate-500 mt-0.5">Submitted for analysis</p>
              </div>

              <div className="relative pl-6">
                <div className="absolute w-2 h-2 bg-alert-amber rounded-none -left-[4.5px] top-1.5 border border-slate-700 ring-4 ring-ink" />
                <p className="text-sm font-bold font-mono text-off-white">Safety Assessment Assigned</p>
                <p className="text-xs font-mono text-slate-500 mt-0.5">Scored {report.risk_score}/100</p>
              </div>

              <div className="relative pl-6">
                <div className="absolute w-2 h-2 bg-verified-teal rounded-none -left-[4.5px] top-1.5 border border-slate-700 ring-4 ring-ink" />
                <p className="text-sm font-bold font-mono text-off-white">Incident Logged</p>
                <p className="text-xs font-mono text-slate-500 mt-0.5 tabular-nums">{new Date(report.logged_at).toLocaleString()}</p>
              </div>

            </div>
          </section>

          {/* 6. Behavior */}
          <section>
            <h3 className="text-xs font-bold text-slate-500 font-mono uppercase tracking-wider mb-3 flex items-center gap-1.5"><Activity size={14} /> Behavior</h3>
            <Card className="p-4 bg-panel flex flex-col justify-center border-dashed border-slate-700 rounded-none shadow-none">
              <p className="text-sm text-slate-400 font-mono text-center italic">Behavioral profiles are managed at the actor level. View the Behavioral Intelligence tab for details.</p>
            </Card>
          </section>

          {/* 7. Victim Guidance */}
          {report.guidance && (
            <section>
              <h3 className="text-xs font-bold text-slate-500 font-mono uppercase tracking-wider mb-3 flex items-center gap-1.5"><AlertTriangle size={14} /> Victim Guidance</h3>
              <GuidancePanel guidance={report.guidance} />
            </section>
          )}

        </div>
      </div>
    </>
  );
}

IncidentIntelligencePanel.propTypes = {
  report: PropTypes.object,
  onClose: PropTypes.func.isRequired
};
