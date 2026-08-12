import PropTypes from 'prop-types';
import { Layers, Lightbulb, MessageSquare, AlertTriangle, ChevronRight } from 'lucide-react';
import Card from './common/Card';
import RiskBadge from './prediction/RiskBadge';
import RedactionBar from './common/RedactionBar';
import GuidancePanel from './prediction/GuidancePanel';

export default function ConversationResultDisplay({ result }) {
  if (!result || !result.messages) return null;

  const isHarassing = result.primary_label !== 'Clean';

  return (
    <div className="space-y-6 animate-slide-up mt-8">
      {/* ── SECTION 1: CONVERSATION ASSESSMENT ── */}
      <div className="space-y-3">
        <h2 className="text-sm font-bold text-off-white font-display flex items-center gap-2">
          <Layers size={18} className="text-slate-500" />
          Conversation Assessment
        </h2>
        
        <Card className="p-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            <div className="space-y-6">
              <div>
                <p className="text-xs font-semibold text-slate-500 font-mono uppercase tracking-wider mb-3">Incident Classification</p>
                <div className="flex items-center gap-4">
                  <RiskBadge
                    isHarassing={isHarassing}
                    category={result.primary_label}
                    riskScore={result.conversation_risk}
                  />
                </div>
              </div>
              
              <div>
                <p className="text-xs font-semibold text-slate-500 font-mono uppercase tracking-wider mb-3">Behavior Intelligence</p>
                <div className="flex items-center gap-3 mb-2">
                  <span className={`px-2.5 py-1 text-xs font-medium rounded-none border ${
                    result.escalation_level === 'High' ? 'bg-panel border-redaction-red text-redaction-red' :
                    result.escalation_level === 'Medium' ? 'bg-panel border-alert-amber text-alert-amber' :
                    'bg-panel border-slate-700 text-off-white'
                  }`}>
                    {result.escalation_level} Escalation
                  </span>
                  <span className="text-xs text-slate-400 font-mono">Score: +{result.escalation_score}</span>
                </div>
                <ul className="text-sm text-slate-400 space-y-1 mt-2">
                  {result.escalation_reason.map((r, i) => (
                    <li key={i} className="flex items-start gap-1.5">
                      <ChevronRight size={14} className="text-slate-400 mt-0.5" /> {r}
                    </li>
                  ))}
                </ul>
              </div>
            </div>

            <div className="space-y-4 border-t md:border-t-0 md:border-l border-slate-700 pt-4 md:pt-0 md:pl-8">
              <div className="flex items-center justify-between mb-2">
                <p className="text-xs font-semibold text-slate-500 font-mono uppercase tracking-wider">Detected Categories</p>
              </div>
              
              {!result.secondary_labels || Object.keys(result.secondary_labels).length === 0 ? (
                <p className="text-sm text-slate-500 italic">No secondary categories detected.</p>
              ) : (
                <div className="space-y-3">
                  {Object.entries(result.secondary_labels).map(([label, conf]) => (
                    <div key={label} className="flex items-center gap-3">
                      <span className="text-sm text-off-white w-32 truncate">{label}</span>
                      <div className="flex-1">
                        <RedactionBar score={conf} tier="amber" />
                      </div>
                      <span className="text-xs font-medium text-slate-400 font-mono tabular-nums w-10 text-right">
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
        <h2 className="text-sm font-bold text-off-white font-display flex items-center gap-2">
          <Lightbulb size={18} className="text-slate-500" />
          AI Recommendation
        </h2>
        
        <Card className="p-0 overflow-hidden">
          <div className="grid grid-cols-1 md:grid-cols-2 divide-y md:divide-y-0 md:divide-x divide-slate-700">
            <div className="p-5">
              <p className="text-xs font-semibold text-slate-500 font-mono uppercase tracking-wider mb-2">Overall Sentiment</p>
              <p className="text-sm text-off-white">{result.ai_summary?.overall_sentiment}</p>
            </div>
            <div className="p-5">
              <p className="text-xs font-semibold text-slate-500 font-mono uppercase tracking-wider mb-2">Harassment Pattern</p>
              <p className="text-sm text-off-white">{result.ai_summary?.harassment_pattern}</p>
            </div>
          </div>
        </Card>
      </div>
      
      {/* ── SECTION 2B: VICTIM GUIDANCE ── */}
      {result.guidance && (
        <div className="space-y-3 pt-4">
          <h2 className="text-sm font-bold text-off-white font-display flex items-center gap-2">
            <AlertTriangle size={18} className="text-alert-amber" />
            Victim Guidance
          </h2>
          <GuidancePanel guidance={result.guidance} />
        </div>
      )}

      {/* ── SECTION 3: MESSAGE TIMELINE ── */}
      <div className="space-y-3 pt-4">
        <h2 className="text-sm font-bold text-off-white font-display flex items-center gap-2">
          <MessageSquare size={18} className="text-slate-500" />
          Message Timeline
        </h2>
        
        <div className="space-y-4">
          {result.messages.map((msg, idx) => {
            const isMsgHarmful = msg.prediction.label === 'harassing';
            return (
              <Card key={msg.message_id || idx} className={`p-4 border-l-4 ${isMsgHarmful ? 'border-l-redaction-red bg-slate-800' : 'border-l-verified-teal bg-panel'}`}>
                <div className="flex justify-between items-start mb-2">
                  <span className="text-xs font-semibold text-off-white font-mono">{msg.sender}</span>
                  <span className="text-[10px] text-slate-500 font-mono">{new Date(msg.timestamp).toLocaleTimeString()}</span>
                </div>
                <p className="text-sm text-off-white mb-3">{msg.text}</p>
                <div className="flex items-center gap-2 text-xs font-mono">
                  <span className={`font-semibold ${isMsgHarmful ? 'text-redaction-red' : 'text-verified-teal'}`}>
                    {msg.prediction.primary_label || msg.prediction.category}
                  </span>
                  <span className="text-slate-600">•</span>
                  <span className="text-slate-400">Risk: {msg.risk_score}</span>
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
