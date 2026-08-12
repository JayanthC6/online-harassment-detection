import { useState, useEffect } from 'react';
import PropTypes from 'prop-types';
import { X, MessageSquare, Shield, Activity, Tag, FileText, Clock, AlertTriangle, ChevronRight } from 'lucide-react';

export default function ConversationDetailsDrawer({ conversation, onClose }) {
  if (!conversation) return null;

  return (
    <>
      {/* Backdrop */}
      <div 
        className="fixed inset-0 bg-slate-900/20 backdrop-blur-sm z-40 transition-opacity"
        onClick={onClose}
      />
      
      {/* Drawer */}
      <div className="fixed inset-y-0 right-0 w-full md:w-[600px] bg-ink shadow-2xl z-50 flex flex-col overflow-hidden animate-slide-left border-l border-slate-700">
        
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-700 bg-panel">
          <div>
            <h2 className="text-lg font-bold text-off-white font-display uppercase tracking-wider">Conversation Details</h2>
            <p className="text-xs text-slate-400 font-mono mt-0.5">Logged: {new Date(conversation.logged_at).toLocaleString()}</p>
          </div>
          <button 
            onClick={onClose}
            className="p-2 text-slate-400 hover:text-off-white hover:bg-slate-800 border border-transparent hover:border-slate-700 transition-colors"
          >
            <X size={20} />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6 space-y-8">
          
          {/* Section: Escalation Intelligence */}
          <section>
            <h3 className="text-[10px] font-bold text-slate-500 font-mono uppercase tracking-wider mb-3 flex items-center gap-1.5"><Activity size={12} /> Escalation Intelligence</h3>
            <div className="bg-panel p-4 rounded-none border border-slate-700 shadow-sm">
              <div className="flex items-center justify-between mb-3 font-mono">
                <div className="flex items-center gap-2">
                  <span className={`px-2 py-0.5 rounded-none text-xs font-bold uppercase ${
                    conversation.escalation_level === 'High' ? 'bg-redaction-red text-ink' :
                    conversation.escalation_level === 'Medium' ? 'bg-alert-amber text-ink' :
                    'bg-slate-800 text-slate-300'
                  }`}>
                    {conversation.escalation_level} Escalation
                  </span>
                </div>
                <span className="text-sm font-bold text-off-white">Score: +{conversation.escalation_score}</span>
              </div>
              <ul className="text-sm text-slate-300 space-y-2 font-mono">
                {conversation.escalation_reason && conversation.escalation_reason.map((reason, idx) => (
                  <li key={idx} className="flex items-start gap-1.5">
                    <ChevronRight size={14} className="text-slate-500 mt-0.5" />
                    <span>{reason}</span>
                  </li>
                ))}
              </ul>
            </div>
          </section>

          {/* Section: AI Summary */}
          {conversation.ai_summary && (
            <section>
              <h3 className="text-[10px] font-bold text-slate-500 font-mono uppercase tracking-wider mb-3 flex items-center gap-1.5"><FileText size={12} /> AI Conversation Summary</h3>
              <div className="bg-slate-900 p-4 rounded-none border border-slate-700 shadow-sm">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                  <div>
                    <p className="text-[10px] text-slate-500 font-mono uppercase tracking-wider mb-1">Overall Sentiment</p>
                    <p className="text-sm font-bold font-mono text-off-white">{conversation.ai_summary.overall_sentiment}</p>
                  </div>
                  <div>
                    <p className="text-[10px] text-slate-500 font-mono uppercase tracking-wider mb-1">Harassment Pattern</p>
                    <p className="text-sm font-bold font-mono text-off-white">{conversation.ai_summary.harassment_pattern}</p>
                  </div>
                </div>
                <div className="pt-3 border-t border-slate-700">
                  <p className="text-[10px] text-slate-400 font-bold font-mono uppercase tracking-wider mb-1 flex items-center gap-1"><AlertTriangle size={12} /> Recommended Action</p>
                  <p className="text-sm text-off-white font-mono">{conversation.ai_summary.recommended_action}</p>
                </div>
              </div>
            </section>
          )}

          {/* Section: Detected Categories */}
          <section>
            <h3 className="text-[10px] font-bold text-slate-500 font-mono uppercase tracking-wider mb-3 flex items-center gap-1.5"><Tag size={12} /> Detected Categories</h3>
            <div className="space-y-3">
              <div className="bg-panel p-3 rounded-none border border-slate-700 shadow-sm relative overflow-hidden">
                <div className="relative z-10 flex justify-between items-center">
                  <div>
                    <span className="text-[10px] font-bold font-mono uppercase tracking-wider text-ink bg-redaction-red px-2 py-0.5 rounded-none mr-2">Primary</span>
                    <span className="font-bold font-mono text-off-white">{conversation.primary_label}</span>
                  </div>
                </div>
              </div>
              
              {conversation.secondary_labels && Object.entries(conversation.secondary_labels).map(([label, conf]) => (
                <div key={label} className="bg-panel p-3 rounded-none border border-slate-700 shadow-sm relative overflow-hidden">
                  <div 
                    className="absolute left-0 top-0 bottom-0 bg-alert-amber/20 z-0" 
                    style={{ width: `${conf * 100}%` }}
                  />
                  <div className="relative z-10 flex justify-between items-center font-mono">
                    <div>
                      <span className="text-[10px] font-bold uppercase tracking-wider text-ink bg-alert-amber px-2 py-0.5 rounded-none mr-2">Secondary</span>
                      <span className="font-bold text-slate-300">{label}</span>
                    </div>
                    <span className="font-bold text-slate-400 tabular-nums">{(conf * 100).toFixed(1)}%</span>
                  </div>
                </div>
              ))}
            </div>
          </section>

          {/* Section: Timeline */}
          <section>
            <h3 className="text-[10px] font-bold text-slate-500 font-mono uppercase tracking-wider mb-3 flex items-center gap-1.5"><Clock size={12} /> Message Timeline</h3>
            <div className="space-y-4 relative before:absolute before:inset-0 before:ml-5 before:-translate-x-px md:before:mx-auto md:before:translate-x-0 before:h-full before:w-px before:bg-gradient-to-b before:from-transparent before:via-slate-700 before:to-transparent">
              {conversation.messages && conversation.messages.map((msg, idx) => {
                const isHarmful = msg.prediction.label === 'harassing';
                return (
                  <div key={idx} className="relative flex items-center justify-between md:justify-normal md:odd:flex-row-reverse group is-active">
                    <div className="flex items-center justify-center w-10 h-10 rounded-none border-2 border-slate-700 bg-panel text-slate-500 font-mono shadow-sm shrink-0 md:order-1 md:group-odd:-translate-x-1/2 md:group-even:translate-x-1/2 z-10">
                      {idx + 1}
                    </div>
                    <div className="w-[calc(100%-4rem)] md:w-[calc(50%-2.5rem)] p-4 rounded-none border border-slate-700 bg-panel shadow-sm">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-xs font-bold font-mono text-slate-400">{msg.sender}</span>
                      </div>
                      <p className="text-sm text-off-white font-mono mb-3">{msg.text}</p>
                      <div className="flex justify-between items-center pt-2 border-t border-slate-700 font-mono">
                        <span className={`text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-none ${isHarmful ? 'bg-redaction-red text-ink' : 'bg-verified-teal text-ink'}`}>
                          {msg.prediction.primary_label || msg.prediction.category.replace('_', ' ')}
                        </span>
                        <span className="text-xs text-slate-500 font-bold">Risk: {msg.risk_score}</span>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </section>
        </div>
      </div>
    </>
  );
}

ConversationDetailsDrawer.propTypes = {
  conversation: PropTypes.object,
  onClose: PropTypes.func.isRequired
};
