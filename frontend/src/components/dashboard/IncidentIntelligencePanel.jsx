import { useState, useEffect } from 'react';
import PropTypes from 'prop-types';
import { X, MessageSquare, Shield, Activity, Cpu, Tag, FileText, Link, Clock, Sparkles, AlertTriangle, Lightbulb } from 'lucide-react';
import { apiClient } from '../../api/client';
import Card from '../common/Card';

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
      highlightedText = highlightedText.replace(regex, '<mark class="bg-rose-100 text-rose-900 rounded px-1">$1</mark>');
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
        className="fixed inset-y-0 right-0 w-full md:w-[600px] bg-[#F8FAFC] shadow-2xl z-50 flex flex-col overflow-hidden animate-slide-left border-l border-slate-200"
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-200 bg-white sticky top-0 z-10">
          <div>
            <h2 className="text-xl font-semibold text-slate-800">Incident Intelligence</h2>
            <p className="text-xs text-slate-500 mt-0.5">ID: {report.cluster_id || 'unclustered'}-{new Date(report.logged_at).getTime()}</p>
          </div>
          <button 
            onClick={onClose}
            className="p-2 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-indigo-500"
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
              <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1.5"><FileText size={14} /> Executive Summary</h3>
              {!summary && (
                <button 
                  onClick={handleSummarize}
                  disabled={loadingSummary}
                  className="text-xs px-3 py-1.5 bg-indigo-50 text-indigo-700 hover:bg-indigo-100 rounded-md font-semibold transition-colors disabled:opacity-50 flex items-center gap-1 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                >
                  {loadingSummary ? <Sparkles size={12} className="animate-spin" /> : <Sparkles size={12} />}
                  {loadingSummary ? 'Generating...' : 'Generate Summary'}
                </button>
              )}
            </div>
            
            {summary ? (
              <Card className="bg-indigo-50/50 border-indigo-100 p-4">
                <p className="text-sm text-indigo-900 leading-relaxed font-medium">
                  {summary}
                </p>
              </Card>
            ) : !loadingSummary ? (
              <Card className="p-4 flex items-center justify-center bg-slate-50 border-slate-200 border-dashed">
                <p className="text-sm text-slate-400 italic">No summary generated. Click above to generate an AI summary.</p>
              </Card>
            ) : null}
          </section>

          {/* 2. Classification */}
          <section>
            <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3 flex items-center gap-1.5"><Tag size={14} /> Incident Classification</h3>
            
            <div className="grid grid-cols-2 gap-4 mb-4">
              <Card className="p-4 flex flex-col justify-center bg-white">
                <p className="text-[10px] text-slate-400 uppercase tracking-wider mb-1 flex items-center gap-1"><Activity size={12} /> Safety Score</p>
                <div className="flex items-end gap-2">
                  <span className={`text-3xl font-bold tabular-nums leading-none ${report.risk_score >= 75 ? 'text-rose-600' : report.risk_score >= 40 ? 'text-amber-600' : 'text-emerald-600'}`}>
                    {report.risk_score}
                  </span>
                  <span className="text-slate-400 font-medium text-sm mb-1">/ 100</span>
                </div>
              </Card>
              
              <Card className="p-4 flex flex-col justify-center bg-white">
                <p className="text-[10px] text-slate-400 uppercase tracking-wider mb-1 flex items-center gap-1"><Shield size={12} /> Confidence</p>
                <div className="flex items-end gap-2">
                  <span className="text-3xl font-bold text-slate-700 tabular-nums leading-none">{(report.confidence * 100).toFixed(1)}%</span>
                </div>
              </Card>
            </div>

            <Card className="p-0 overflow-hidden divide-y divide-slate-100 bg-white">
              <div className="p-4 flex justify-between items-center relative overflow-hidden">
                <div 
                  className="absolute left-0 top-0 bottom-0 bg-rose-50/50 z-0" 
                  style={{ width: `${(report.confidence || 0) * 100}%` }}
                />
                <div className="relative z-10 flex items-center gap-3">
                  <span className="text-[10px] font-bold uppercase tracking-wider text-rose-700 bg-rose-100 px-2.5 py-1 rounded-md">Primary</span>
                  <span className="font-semibold text-slate-800 text-sm">{report.primary_label || report.category.replace('_', ' ')}</span>
                </div>
                <span className="relative z-10 text-xs font-medium text-slate-500">{(report.confidence * 100).toFixed(1)}% match</span>
              </div>
              
              {report.secondary_labels && Object.entries(report.secondary_labels).map(([label, conf]) => (
                <div key={label} className="p-4 flex justify-between items-center relative overflow-hidden">
                  <div 
                    className="absolute left-0 top-0 bottom-0 bg-amber-50/30 z-0" 
                    style={{ width: `${conf * 100}%` }}
                  />
                  <div className="relative z-10 flex items-center gap-3">
                    <span className="text-[10px] font-bold uppercase tracking-wider text-amber-700 bg-amber-100 px-2.5 py-1 rounded-md">Secondary</span>
                    <span className="font-medium text-slate-700 text-sm">{label}</span>
                  </div>
                  <span className="relative z-10 text-xs font-medium text-slate-500">{(conf * 100).toFixed(1)}% match</span>
                </div>
              ))}
            </Card>
            <div className="mt-2 text-right">
              <span className="text-[10px] text-slate-400 flex items-center justify-end gap-1"><Cpu size={10} /> Model: {report.model === 'distilbert' ? 'DistilBERT' : report.model.replace('+multi_label_heuristics', ' + Heuristics')}</span>
            </div>
          </section>

          {/* 3. Evidence */}
          <section>
            <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3 flex items-center gap-1.5"><MessageSquare size={14} /> Evidence</h3>
            <Card className="p-4 bg-white">
              <div 
                className="text-slate-800 text-sm leading-relaxed"
                dangerouslySetInnerHTML={{ __html: highlightedWords.length > 0 ? highlightedText : report.text_preview }}
              />
            </Card>
          </section>

          {/* 4. Explainability */}
          {explanationsList.length > 0 && (
            <section>
              <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3 flex items-center gap-1.5"><Lightbulb size={14} /> Explainability</h3>
              <Card className="p-4 bg-white flex flex-wrap gap-2 items-center">
                {explanationsList.map((ex, i) => (
                  <span key={i} className="inline-flex items-center px-2.5 py-1 rounded-md text-xs font-medium bg-rose-50 text-rose-700 border border-rose-100" title={ex.reason || ''}>
                    {ex.word} <span className="ml-1.5 text-[10px] font-bold opacity-60">({ex.label ? ex.label : ex.contribution.toFixed(2)})</span>
                  </span>
                ))}
              </Card>
            </section>
          )}

          {/* 5. Timeline */}
          <section>
            <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-4 flex items-center gap-1.5"><Clock size={14} /> Timeline</h3>
            <div className="relative border-l-2 border-indigo-100 ml-4 space-y-6 pb-2">
              
              <div className="relative pl-6">
                <div className="absolute w-3 h-3 bg-indigo-500 rounded-full -left-[7px] top-1.5 ring-4 ring-[#F8FAFC]" />
                <p className="text-sm font-semibold text-slate-700">Message Ingested</p>
                <p className="text-xs text-slate-500 mt-0.5">Submitted for analysis</p>
              </div>

              <div className="relative pl-6">
                <div className="absolute w-3 h-3 bg-amber-500 rounded-full -left-[7px] top-1.5 ring-4 ring-[#F8FAFC]" />
                <p className="text-sm font-semibold text-slate-700">Safety Assessment Assigned</p>
                <p className="text-xs text-slate-500 mt-0.5">Scored {report.risk_score}/100</p>
              </div>

              <div className="relative pl-6">
                <div className="absolute w-3 h-3 bg-emerald-500 rounded-full -left-[7px] top-1.5 ring-4 ring-[#F8FAFC]" />
                <p className="text-sm font-semibold text-slate-700">Incident Logged</p>
                <p className="text-xs text-slate-500 mt-0.5 tabular-nums">{new Date(report.logged_at).toLocaleString()}</p>
              </div>

            </div>
          </section>

          {/* 6. Behavior */}
          <section>
            <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3 flex items-center gap-1.5"><Activity size={14} /> Behavior</h3>
            <Card className="p-4 bg-white flex flex-col justify-center border-dashed border-slate-200">
              <p className="text-sm text-slate-500 text-center italic">Behavioral profiles are managed at the actor level. View the Behavioral Intelligence tab for details.</p>
            </Card>
          </section>

          {/* 7. Recommendation */}
          <section>
            <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3 flex items-center gap-1.5"><AlertTriangle size={14} /> Recommendation</h3>
            <Card className="p-4 bg-white flex flex-col justify-center border-dashed border-slate-200">
              <p className="text-sm text-slate-500 text-center italic">Monitor the user account if incidents escalate.</p>
            </Card>
          </section>

        </div>
      </div>
    </>
  );
}

IncidentIntelligencePanel.propTypes = {
  report: PropTypes.object,
  onClose: PropTypes.func.isRequired
};
