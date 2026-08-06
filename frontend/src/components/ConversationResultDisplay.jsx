import PropTypes from 'prop-types';
import { Layers, Lightbulb, MessageSquare, AlertTriangle, ChevronRight } from 'lucide-react';
import Card from './common/Card';
import RiskBadge from './prediction/RiskBadge';

export default function ConversationResultDisplay({ result }) {
  if (!result || !result.messages) return null;

  const isHarassing = result.primary_label !== 'Clean';

  return (
    <div className="space-y-6 animate-slide-up mt-8">
      {/* ── SECTION 1: CONVERSATION ASSESSMENT ── */}
      <div className="space-y-3">
        <h2 className="text-sm font-semibold text-slate-800 flex items-center gap-2">
          <Layers size={18} className="text-indigo-600" />
          Conversation Assessment
        </h2>
        
        <Card className="p-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            <div className="space-y-6">
              <div>
                <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-3">Primary Category & Risk</p>
                <div className="flex items-center gap-4">
                  <RiskBadge
                    isHarassing={isHarassing}
                    category={result.primary_label}
                    riskScore={result.conversation_risk}
                  />
                </div>
              </div>
              
              <div>
                <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-3">Escalation Intelligence</p>
                <div className="flex items-center gap-3 mb-2">
                  <span className={`px-2.5 py-1 text-xs font-medium rounded-md ${
                    result.escalation_level === 'High' ? 'bg-rose-100 text-rose-700' :
                    result.escalation_level === 'Medium' ? 'bg-amber-100 text-amber-700' :
                    'bg-slate-100 text-slate-700'
                  }`}>
                    {result.escalation_level} Escalation
                  </span>
                  <span className="text-xs text-slate-500 font-medium">Score: +{result.escalation_score}</span>
                </div>
                <ul className="text-sm text-slate-600 space-y-1 mt-2">
                  {result.escalation_reason.map((r, i) => (
                    <li key={i} className="flex items-start gap-1.5">
                      <ChevronRight size={14} className="text-slate-400 mt-0.5" /> {r}
                    </li>
                  ))}
                </ul>
              </div>
            </div>

            <div className="space-y-4 border-t md:border-t-0 md:border-l border-slate-100 pt-4 md:pt-0 md:pl-8">
              <div className="flex items-center justify-between mb-2">
                <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Secondary Categories</p>
              </div>
              
              {!result.secondary_labels || Object.keys(result.secondary_labels).length === 0 ? (
                <p className="text-sm text-slate-400 italic">No secondary categories detected.</p>
              ) : (
                <div className="space-y-3">
                  {Object.entries(result.secondary_labels).map(([label, conf]) => (
                    <div key={label} className="flex items-center gap-3">
                      <span className="text-sm text-slate-700 w-32 truncate">{label}</span>
                      <div className="flex-1 h-2 bg-slate-100 rounded-full overflow-hidden">
                        <div 
                          className="h-full bg-amber-500 rounded-full" 
                          style={{ width: `${conf * 100}%` }}
                        />
                      </div>
                      <span className="text-xs font-medium text-slate-500 w-10 text-right">
                        {(conf * 100).toFixed(0)}%
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </Card>
      </div>

      {/* ── SECTION 2: AI SUMMARY ── */}
      <div className="space-y-3 pt-4">
        <h2 className="text-sm font-semibold text-slate-800 flex items-center gap-2">
          <Lightbulb size={18} className="text-indigo-600" />
          AI Conversation Summary
        </h2>
        
        <Card className="p-0 overflow-hidden">
          <div className="grid grid-cols-1 md:grid-cols-3 divide-y md:divide-y-0 md:divide-x divide-slate-100">
            <div className="p-5">
              <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">Overall Sentiment</p>
              <p className="text-sm text-slate-700 font-medium">{result.ai_summary?.overall_sentiment}</p>
            </div>
            <div className="p-5">
              <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">Harassment Pattern</p>
              <p className="text-sm text-slate-700 font-medium">{result.ai_summary?.harassment_pattern}</p>
            </div>
            <div className="p-5 bg-indigo-50/30">
              <p className="text-xs font-semibold text-indigo-800/60 uppercase tracking-wider mb-2 flex items-center gap-1.5"><AlertTriangle size={14} /> Recommended Action</p>
              <p className="text-sm text-indigo-900 leading-snug">{result.ai_summary?.recommended_action}</p>
            </div>
          </div>
        </Card>
      </div>

      {/* ── SECTION 3: MESSAGE TIMELINE ── */}
      <div className="space-y-3 pt-4">
        <h2 className="text-sm font-semibold text-slate-800 flex items-center gap-2">
          <MessageSquare size={18} className="text-indigo-600" />
          Message Timeline
        </h2>
        
        <div className="space-y-4">
          {result.messages.map((msg, idx) => {
            const isMsgHarmful = msg.prediction.label === 'harassing';
            return (
              <Card key={msg.message_id || idx} className={`p-4 border-l-4 ${isMsgHarmful ? 'border-l-rose-500 bg-rose-50/30' : 'border-l-emerald-500'}`}>
                <div className="flex justify-between items-start mb-2">
                  <span className="text-xs font-semibold text-slate-700">{msg.sender}</span>
                  <span className="text-[10px] text-slate-400">{new Date(msg.timestamp).toLocaleTimeString()}</span>
                </div>
                <p className="text-sm text-slate-800 mb-3">{msg.text}</p>
                <div className="flex items-center gap-2 text-xs">
                  <span className={`font-medium ${isMsgHarmful ? 'text-rose-600' : 'text-emerald-600'}`}>
                    {msg.prediction.primary_label || msg.prediction.category}
                  </span>
                  <span className="text-slate-300">•</span>
                  <span className="text-slate-500">Risk: {msg.risk_score}</span>
                </div>
              </Card>
            )
          })}
        </div>
      </div>
    </div>
  );
}

ConversationResultDisplay.propTypes = {
  result: PropTypes.object
};
