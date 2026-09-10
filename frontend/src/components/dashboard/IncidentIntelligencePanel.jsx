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
      highlightedText = highlightedText.replace(regex, '<mark class="bg-purple/30 text-white rounded-sm px-1 border border-purple/50 shadow-[0_0_5px_rgba(168,85,247,0.5)]">$1</mark>');
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
        className="fixed inset-y-0 right-0 w-full md:w-[600px] bg-[#060913]/95 backdrop-blur-3xl shadow-[-20px_0_50px_rgba(0,242,254,0.1)] z-50 flex flex-col overflow-hidden animate-slide-left border-l border-blue/30"
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-border/50 bg-black/40 sticky top-0 z-10 shadow-inner">
          <div>
            <h2 className="text-xl font-bold text-off-white font-display uppercase tracking-wider">Incident Intelligence</h2>
            <p className="text-xs text-slate-400 font-mono mt-0.5">ID: {report.cluster_id || 'unclustered'}-{new Date(report.logged_at).getTime()}</p>
          </div>
          <button 
            onClick={onClose}
            className="p-2 text-text-muted hover:text-white hover:bg-white/5 border border-transparent hover:border-border transition-colors focus:outline-none rounded-md"
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
                  className="text-xs px-3 py-1.5 bg-purple/10 text-purple border border-purple/30 hover:bg-purple/20 hover:shadow-[0_0_10px_rgba(168,85,247,0.3)] rounded font-bold font-mono transition-all disabled:opacity-50 flex items-center gap-1 drop-shadow-[0_0_5px_rgba(168,85,247,0.4)]"
                >
                  {loadingSummary ? <Sparkles size={12} className="animate-spin" /> : <Sparkles size={12} />}
                  {loadingSummary ? 'Generating...' : 'Generate Summary'}
                </button>
              )}
            </div>
            
            {summary ? (
              <Card className="bg-black/40 border-purple/30 rounded-xl p-4 shadow-[inset_0_0_15px_rgba(168,85,247,0.15)] relative overflow-hidden">
                <div className="absolute top-0 left-0 w-1 h-full bg-gradient-to-b from-purple to-blue"></div>
                <p className="text-sm text-text-primary leading-relaxed font-mono">
                  {summary}
                </p>
              </Card>
            ) : !loadingSummary ? (
              <Card className="p-4 flex items-center justify-center bg-black/20 border-border/50 rounded-xl border-dashed">
                <p className="text-sm text-text-muted font-mono italic">No summary generated. Click above to generate an AI summary.</p>
              </Card>
            ) : null}
          </section>

          {/* 2. Classification */}
          <section>
            <h3 className="text-xs font-bold text-slate-500 font-mono uppercase tracking-wider mb-3 flex items-center gap-1.5"><Tag size={14} /> Incident Classification</h3>
            
            <div className="grid grid-cols-2 gap-4 mb-4">
              <Card className="p-4 flex flex-col justify-center bg-black/40 border-border/50 rounded-xl shadow-inner">
                <p className="text-[10px] text-text-muted font-mono uppercase tracking-wider mb-1 flex items-center gap-1"><Activity size={12} /> Safety Score</p>
                <div className="flex items-end gap-2">
                  <span className={`text-3xl font-extrabold font-mono tabular-nums leading-none tracking-tight ${report.risk_score >= 75 ? 'text-critical drop-shadow-[0_0_5px_rgba(244,63,94,0.6)]' : report.risk_score >= 40 ? 'text-danger drop-shadow-[0_0_5px_rgba(249,115,22,0.6)]' : 'text-success drop-shadow-[0_0_5px_rgba(16,185,129,0.6)]'}`}>
                    {report.risk_score}
                  </span>
                  <span className="text-text-muted font-mono text-sm mb-1">/ 100</span>
                </div>
              </Card>
              
              <Card className="p-4 flex flex-col justify-center bg-black/40 border-border/50 rounded-xl shadow-inner">
                <p className="text-[10px] text-text-muted font-mono uppercase tracking-wider mb-1 flex items-center gap-1"><Shield size={12} /> Confidence</p>
                <div className="flex items-end gap-2">
                  <span className="text-3xl font-extrabold text-blue font-mono tabular-nums leading-none drop-shadow-[0_0_5px_rgba(0,242,254,0.4)]">{(report.confidence * 100).toFixed(1)}%</span>
                </div>
              </Card>
            </div>

            <Card className="p-0 overflow-hidden divide-y divide-border/50 bg-black/40 border-border/50 rounded-xl shadow-inner">
              <div className="p-4 flex justify-between items-center relative overflow-hidden">
                <div 
                  className="absolute left-0 top-0 bottom-0 bg-redaction-red/20 z-0" 
                  style={{ width: `${(report.confidence || 0) * 100}%` }}
                />
                <div className="relative z-10 flex items-center gap-3">
                  <span className="text-[10px] font-bold font-mono uppercase tracking-wider text-white bg-critical/80 px-2.5 py-1 rounded-none shadow-[0_0_5px_rgba(244,63,94,0.5)]">Primary</span>
                  <span className="font-bold font-mono uppercase text-white text-sm drop-shadow-[0_0_3px_rgba(0,242,254,0.3)]">{report.primary_label || report.category.replace('_', ' ')}</span>
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
                    <span className="text-[10px] font-bold font-mono uppercase tracking-wider text-white bg-danger/80 px-2.5 py-1 rounded-none shadow-[0_0_5px_rgba(249,115,22,0.5)]">Secondary</span>
                    <span className="font-bold font-mono text-text-primary text-sm">{label}</span>
                  </div>
                  <span className="relative z-10 text-xs font-mono font-bold text-slate-400 tabular-nums">{(conf * 100).toFixed(1)}% match</span>
                </div>
              ))}
            </Card>
            <div className="mt-2 text-right">
              <span className="text-[10px] text-text-muted font-mono uppercase tracking-wider flex items-center justify-end gap-1"><Cpu size={10} /> Model: {report.model}</span>
            </div>
          </section>

          {/* 3. Evidence */}
          <section>
            <h3 className="text-xs font-bold text-text-muted font-mono uppercase tracking-wider mb-3 flex items-center gap-1.5"><MessageSquare size={14} /> Evidence</h3>
            <Card className="p-4 bg-black/40 border-border/50 rounded-xl shadow-inner">
              <div 
                className="text-white text-sm leading-relaxed font-mono whitespace-pre-wrap drop-shadow-sm"
                dangerouslySetInnerHTML={{ __html: highlightedWords.length > 0 ? highlightedText : report.text_preview }}
              />
            </Card>
          </section>

          {/* 4. Explainability */}
          {explanationsList.length > 0 && (
            <section>
              <h3 className="text-xs font-bold text-text-muted font-mono uppercase tracking-wider mb-3 flex items-center gap-1.5"><Lightbulb size={14} /> Explainability</h3>
              <Card className="p-4 bg-black/40 border-border/50 rounded-xl shadow-inner flex flex-wrap gap-2 items-center">
                {explanationsList.map((ex, i) => (
                  <span key={i} className="inline-flex items-center px-2.5 py-1 rounded-sm text-xs font-bold font-mono bg-purple/20 text-white border border-purple/50 shadow-[0_0_5px_rgba(168,85,247,0.3)]" title={ex.reason || ''}>
                    {ex.word} <span className="ml-1.5 text-[10px] font-bold opacity-60">({ex.label ? ex.label : ex.contribution.toFixed(2)})</span>
                  </span>
                ))}
              </Card>
            </section>
          )}

          {/* 4.5 Threat Intelligence */}
          {report.threat_intel && (report.threat_intel.urls?.length > 0 || report.threat_intel.emails?.length > 0) && (
            <section>
              <h3 className="text-xs font-bold text-text-muted font-mono uppercase tracking-wider mb-3 flex items-center gap-1.5"><Shield size={14} /> Threat Intelligence</h3>
              <div className="space-y-3">
                {report.threat_intel.urls?.map((u, i) => (
                  <Card key={i} className={`p-4 bg-black/40 border-border/50 rounded-xl shadow-inner border-l-4 ${(u.safe_browsing && u.safe_browsing !== 'safe') || u.typosquat_match ? 'border-l-critical shadow-[inset_2px_0_15px_rgba(244,63,94,0.15)]' : 'border-l-blue shadow-[inset_2px_0_15px_rgba(0,242,254,0.15)]'}`}>
                    <div className="flex items-center gap-2 mb-2">
                      <Link size={14} className="text-blue" />
                      <span className="font-mono text-sm font-bold text-white break-all drop-shadow-[0_0_5px_rgba(0,242,254,0.5)]">{u.url}</span>
                    </div>
                    <div className="grid grid-cols-2 gap-2 mt-3">
                      {u.safe_browsing && (
                        <div>
                          <p className="text-[10px] font-mono text-text-muted uppercase tracking-wider mb-1">Safe Browsing</p>
                          <span className={`inline-flex font-mono text-xs font-bold px-2 py-0.5 rounded-sm ${u.safe_browsing !== 'safe' ? 'bg-critical text-white shadow-[0_0_10px_rgba(244,63,94,0.4)]' : 'bg-success/20 text-success border border-success/30'}`}>
                            {u.safe_browsing !== 'safe' ? u.safe_browsing.replace(/_/g, ' ') : 'CLEAN'}
                          </span>
                        </div>
                      )}
                      {u.domain_age_days !== undefined && (
                        <div>
                          <p className="text-[10px] font-mono text-text-muted uppercase tracking-wider mb-1">Domain Age</p>
                          <span className={`inline-flex font-mono text-xs font-bold px-2 py-0.5 rounded-sm ${u.domain_age_days < 30 ? 'bg-danger text-white shadow-[0_0_10px_rgba(249,115,22,0.4)]' : 'bg-black/40 text-text-primary border border-border/50'}`}>
                            {u.domain_age_days} days
                          </span>
                        </div>
                      )}
                      {u.typosquat_match && (
                        <div className="col-span-2 mt-1">
                          <p className="text-[10px] font-mono text-text-muted uppercase tracking-wider mb-1">Typosquat Detection</p>
                          <span className="inline-flex font-mono text-xs font-bold px-2 py-0.5 rounded-sm bg-critical text-white shadow-[0_0_10px_rgba(244,63,94,0.4)]">
                            TARGETS: {u.typosquat_match}
                          </span>
                        </div>
                      )}
                    </div>
                  </Card>
                ))}
                
                {report.threat_intel.emails?.map((e, i) => (
                  <Card key={`e-${i}`} className="p-4 bg-black/40 border-border/50 rounded-xl shadow-inner border-l-4 border-l-border/50">
                    <div className="flex items-center gap-2 mb-2">
                      <MessageSquare size={14} className="text-blue" />
                      <span className="font-mono text-sm font-bold text-white break-all">{e.email}</span>
                    </div>
                    {e.breach_count !== undefined && (
                      <div className="mt-3">
                        <p className="text-[10px] font-mono text-text-muted uppercase tracking-wider mb-1">Known Breaches (HIBP)</p>
                        <span className={`inline-flex font-mono text-xs font-bold px-2 py-0.5 rounded-sm ${e.breach_count > 0 ? 'bg-danger text-white shadow-[0_0_10px_rgba(249,115,22,0.4)]' : 'bg-black/40 text-text-primary border border-border/50'}`}>
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
            <h3 className="text-xs font-bold text-text-muted font-mono uppercase tracking-wider mb-4 flex items-center gap-1.5"><Clock size={14} /> Timeline</h3>
            <div className="relative border-l border-border/50 ml-4 space-y-6 pb-2">
              
              <div className="relative pl-6">
                <div className="absolute w-2 h-2 bg-text-muted rounded-full -left-[4.5px] top-1.5 border border-border/50 shadow-[0_0_5px_rgba(148,163,184,0.5)]" />
                <p className="text-sm font-bold font-mono text-white">Message Ingested</p>
                <p className="text-xs font-mono text-text-muted mt-0.5">Submitted for analysis</p>
              </div>

              <div className="relative pl-6">
                <div className="absolute w-2 h-2 bg-danger rounded-full -left-[4.5px] top-1.5 border border-border/50 shadow-[0_0_5px_rgba(249,115,22,0.5)]" />
                <p className="text-sm font-bold font-mono text-white">Safety Assessment Assigned</p>
                <p className="text-xs font-mono text-text-muted mt-0.5">Scored {report.risk_score}/100</p>
              </div>

              <div className="relative pl-6">
                <div className="absolute w-2 h-2 bg-success rounded-full -left-[4.5px] top-1.5 border border-border/50 shadow-[0_0_5px_rgba(16,185,129,0.5)]" />
                <p className="text-sm font-bold font-mono text-white">Incident Logged</p>
                <p className="text-xs font-mono text-text-muted mt-0.5 tabular-nums">{new Date(report.logged_at).toLocaleString()}</p>
              </div>

            </div>
          </section>

          {/* 6. Behavior */}
          <section>
            <h3 className="text-xs font-bold text-text-muted font-mono uppercase tracking-wider mb-3 flex items-center gap-1.5"><Activity size={14} /> Behavior</h3>
            <Card className="p-4 bg-black/20 flex flex-col justify-center border-dashed border-border/50 rounded-xl shadow-none">
              <p className="text-sm text-text-secondary font-mono text-center italic">Behavioral profiles are managed at the actor level. View the Behavioral Intelligence tab for details.</p>
            </Card>
          </section>

          {/* 7. Victim Guidance */}
          {report.guidance && (
            <section>
              <h3 className="text-xs font-bold text-text-muted font-mono uppercase tracking-wider mb-3 flex items-center gap-1.5"><AlertTriangle size={14} /> Victim Guidance</h3>
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
