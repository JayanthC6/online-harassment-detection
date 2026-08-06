import { useState, useEffect } from 'react';
import PropTypes from 'prop-types';
import { X, MessageSquare, Shield, Activity, Cpu, Tag, FileText, Link, Clock, Sparkles } from 'lucide-react';
import { apiClient } from '../../api/client';

export default function ReportDetailsDrawer({ report, onClose }) {
  const [summary, setSummary] = useState(null);
  const [loadingSummary, setLoadingSummary] = useState(false);

  useEffect(() => {
    // Reset summary when report changes
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
  
  // Basic highlighting logic
  let highlightedText = report.text_preview || '';
  if (highlightedWords.length > 0) {
    highlightedWords.forEach(word => {
      // Escape word for regex
      const safeWord = word.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
      const regex = new RegExp(`\\b(${safeWord})\\b`, 'gi');
      highlightedText = highlightedText.replace(regex, '<mark class="bg-rose-100 text-rose-900 rounded px-1">$1</mark>');
    });
  }

  return (
    <>
      {/* Backdrop */}
      <div 
        className="fixed inset-0 bg-slate-900/20 backdrop-blur-sm z-40 transition-opacity"
        onClick={onClose}
      />
      
      {/* Drawer */}
      <div className="fixed inset-y-0 right-0 w-full md:w-[600px] bg-white shadow-2xl z-50 flex flex-col overflow-hidden animate-slide-left border-l border-slate-200">
        
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-100 bg-white">
          <div>
            <h2 className="text-lg font-semibold text-slate-800">Report Details</h2>
            <p className="text-xs text-slate-400 mt-0.5">ID: {report.cluster_id || 'unclustered'}-{new Date(report.logged_at).getTime()}</p>
          </div>
          <button 
            onClick={onClose}
            className="p-2 text-slate-400 hover:text-slate-600 hover:bg-slate-50 rounded-full transition-colors"
          >
            <X size={20} />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6 space-y-8">
          
          {/* Section: Original Message */}
          <section>
            <h3 className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider mb-3 flex items-center gap-1.5"><MessageSquare size={12} /> Original Message</h3>
            <div 
              className="bg-slate-50 p-4 rounded-xl border border-slate-100 text-slate-700 text-sm leading-relaxed"
              dangerouslySetInnerHTML={{ __html: highlightedWords.length > 0 ? highlightedText : report.text_preview }}
            />
            {explanationsList.length > 0 && (
              <div className="mt-3 flex flex-wrap gap-2 items-center">
                <span className="text-[10px] text-slate-400 font-medium uppercase tracking-wider">Explainable AI:</span>
                {explanationsList.map((ex, i) => (
                  <span key={i} className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-rose-50 text-rose-700 border border-rose-100" title={ex.reason || ''}>
                    {ex.word} <span className="ml-1 opacity-60">({ex.label ? ex.label : ex.contribution.toFixed(2)})</span>
                  </span>
                ))}
              </div>
            )}
          </section>

          {/* Section: Detected Categories (Multi-Label) */}
          <section>
            <h3 className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider mb-3 flex items-center gap-1.5"><Tag size={12} /> Detected Categories</h3>
            <div className="space-y-3">
              {/* Primary Label */}
              <div className="bg-white p-3 rounded-xl border border-rose-100 shadow-sm relative overflow-hidden">
                <div 
                  className="absolute left-0 top-0 bottom-0 bg-rose-50/50 z-0" 
                  style={{ width: `${(report.confidence || 0) * 100}%` }}
                />
                <div className="relative z-10 flex justify-between items-center">
                  <div>
                    <span className="text-[10px] font-bold uppercase tracking-wider text-rose-600 bg-rose-100 px-2 py-0.5 rounded-md mr-2">Primary</span>
                    <span className="font-semibold text-slate-800">{report.primary_label || report.category.replace('_', ' ')}</span>
                  </div>
                  <span className="font-semibold text-slate-700 tabular-nums">{(report.confidence * 100).toFixed(1)}%</span>
                </div>
              </div>
              
              {/* Secondary Labels */}
              {report.secondary_labels && Object.entries(report.secondary_labels).map(([label, conf]) => (
                <div key={label} className="bg-white p-3 rounded-xl border border-slate-100 shadow-sm relative overflow-hidden">
                  <div 
                    className="absolute left-0 top-0 bottom-0 bg-amber-50/50 z-0" 
                    style={{ width: `${conf * 100}%` }}
                  />
                  <div className="relative z-10 flex justify-between items-center">
                    <div>
                      <span className="text-[10px] font-bold uppercase tracking-wider text-amber-600 bg-amber-100 px-2 py-0.5 rounded-md mr-2">Secondary</span>
                      <span className="font-medium text-slate-700">{label}</span>
                    </div>
                    <span className="font-semibold text-slate-600 tabular-nums">{(conf * 100).toFixed(1)}%</span>
                  </div>
                </div>
              ))}
            </div>
          </section>

          {/* Section: Prediction Metrics */}
          <section className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <div className="bg-slate-50 p-3 rounded-xl border border-slate-100">
              <p className="text-[10px] text-slate-400 uppercase tracking-wider mb-1 flex items-center gap-1"><Tag size={10} /> Category</p>
              <p className="font-semibold text-slate-700 capitalize text-sm">{report.category.replace('_', ' ')}</p>
            </div>
            <div className="bg-slate-50 p-3 rounded-xl border border-slate-100">
              <p className="text-[10px] text-slate-400 uppercase tracking-wider mb-1 flex items-center gap-1"><Activity size={10} /> Risk</p>
              <p className={`font-semibold text-sm tabular-nums ${report.risk_score >= 75 ? 'text-rose-600' : report.risk_score >= 40 ? 'text-amber-600' : 'text-emerald-600'}`}>
                {report.risk_score} <span className="text-slate-400 font-normal text-xs">/ 100</span>
              </p>
            </div>
            <div className="bg-slate-50 p-3 rounded-xl border border-slate-100">
              <p className="text-[10px] text-slate-400 uppercase tracking-wider mb-1 flex items-center gap-1"><Shield size={10} /> Confidence</p>
              <p className="font-semibold text-slate-700 text-sm tabular-nums">{(report.confidence * 100).toFixed(1)}%</p>
            </div>
            <div className="bg-slate-50 p-3 rounded-xl border border-slate-100">
              <p className="text-[10px] text-slate-400 uppercase tracking-wider mb-1 flex items-center gap-1"><Cpu size={10} /> Engine</p>
              <p className="font-semibold text-slate-700 text-sm truncate" title={report.model}>{report.model === 'distilbert' ? 'DistilBERT' : report.model.replace('+multi_label_heuristics', ' + Heuristics')}</p>
            </div>
          </section>

          {/* Section: AI Incident Summary */}
          <section>
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-1.5"><FileText size={12} /> AI Incident Summary</h3>
              {!summary && (
                <button 
                  onClick={handleSummarize}
                  disabled={loadingSummary}
                  className="text-xs px-3 py-1.5 bg-indigo-50 text-indigo-600 hover:bg-indigo-100 rounded-md font-medium transition-colors disabled:opacity-50 flex items-center gap-1"
                >
                  {loadingSummary ? <Sparkles size={12} className="animate-spin" /> : <Sparkles size={12} />}
                  {loadingSummary ? 'Generating...' : 'Generate Summary'}
                </button>
              )}
            </div>
            
            {summary && (
              <div className="bg-indigo-50/50 p-4 rounded-xl border border-indigo-100 text-slate-700 text-sm leading-relaxed animate-fade-in">
                {summary}
              </div>
            )}
            {!summary && !loadingSummary && (
              <div className="bg-slate-50 p-4 rounded-xl border border-slate-100 text-slate-400 text-sm text-center italic">
                Summary has not been generated for this report yet.
              </div>
            )}
          </section>

          {/* Section: Duplicate Cluster Viewer */}
          {report.similar_reports && report.similar_reports.length > 0 && (
            <section>
              <h3 className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider mb-3 flex items-center gap-1.5">
                <Link size={12} /> Duplicate Cluster
                <span className="px-1.5 py-0.5 bg-slate-100 text-slate-500 rounded-md text-[9px] font-bold ml-1">
                  ID: {report.cluster_id}
                </span>
              </h3>
              <div className="space-y-3">
                {report.similar_reports.map((sim, i) => (
                  <div key={i} className="bg-white p-3 rounded-lg border border-slate-200 shadow-sm flex items-start gap-3">
                    <div className="shrink-0 pt-0.5">
                      <div className="w-8 h-8 rounded-md bg-amber-50 text-amber-600 border border-amber-100 flex items-center justify-center font-bold text-xs">
                        {(sim.similarity * 100).toFixed(0)}%
                      </div>
                    </div>
                    <div>
                      <p className="text-sm text-slate-700">{sim.text_preview}</p>
                      <p className="text-xs text-slate-400 mt-1 flex items-center gap-1">Previous Incident <span className="w-1 h-1 bg-slate-300 rounded-full" /> {sim.category.replace('_', ' ')}</p>
                    </div>
                  </div>
                ))}
              </div>
            </section>
          )}

          {/* Section: Incident Timeline */}
          <section>
            <h3 className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider mb-4 flex items-center gap-1.5"><Clock size={12} /> Incident Timeline</h3>
            <div className="relative border-l-2 border-indigo-100 ml-3 space-y-6 pb-4">
              
              <div className="relative pl-6">
                <div className="absolute w-3 h-3 bg-indigo-500 rounded-full -left-[7px] top-1.5 ring-4 ring-white" />
                <p className="text-sm font-semibold text-slate-700">Submitted</p>
                <p className="text-xs text-slate-400 mt-0.5">Message ingested by system</p>
              </div>

              <div className="relative pl-6">
                <div className="absolute w-3 h-3 bg-indigo-500 rounded-full -left-[7px] top-1.5 ring-4 ring-white" />
                <p className="text-sm font-semibold text-slate-700">Predicted</p>
                <p className="text-xs text-slate-400 mt-0.5">Processed by {report.model} ({(report.confidence * 100).toFixed(1)}% conf)</p>
              </div>

              <div className="relative pl-6">
                <div className="absolute w-3 h-3 bg-amber-500 rounded-full -left-[7px] top-1.5 ring-4 ring-white" />
                <p className="text-sm font-semibold text-slate-700">Risk Assigned</p>
                <p className="text-xs text-slate-400 mt-0.5">Scored {report.risk_score}/100 based on policy</p>
              </div>

              <div className="relative pl-6">
                <div className="absolute w-3 h-3 bg-emerald-500 rounded-full -left-[7px] top-1.5 ring-4 ring-white" />
                <p className="text-sm font-semibold text-slate-700">Stored</p>
                <p className="text-xs text-slate-400 mt-0.5 tabular-nums">{new Date(report.logged_at).toLocaleString()}</p>
              </div>

              {summary && (
                <div className="relative pl-6">
                  <div className="absolute w-3 h-3 bg-purple-500 rounded-full -left-[7px] top-1.5 ring-4 ring-white" />
                  <p className="text-sm font-semibold text-slate-700">Summarized</p>
                  <p className="text-xs text-slate-400 mt-0.5">AI incident summary generated</p>
                </div>
              )}

            </div>
          </section>

        </div>
      </div>
    </>
  );
}

ReportDetailsDrawer.propTypes = {
  report: PropTypes.object,
  onClose: PropTypes.func.isRequired
};
