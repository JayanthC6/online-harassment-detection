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
                    safetyStatus={result.safety_status}
                    severityTier={result.severity_tier}
                    category={result.primary_label || result.category}
                    threatScore={result.threat_score}
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

      {/* ── SECTION 1.5: AGGREGATE STATS ── */}
      {(result.total_messages > 0) && (
        <div className="space-y-3 pt-4">
          <h2 className="text-sm font-bold text-off-white font-display flex items-center gap-2">
            <Layers size={18} className="text-slate-500" />
            Conversation Stats
          </h2>
          <Card className="p-0 overflow-hidden">
            <div className="grid grid-cols-2 md:grid-cols-4 divide-x divide-y md:divide-y-0 divide-slate-700">
              <div className="p-4 text-center">
                <p className="text-[10px] font-semibold text-slate-500 font-mono uppercase tracking-wider mb-1">Total Messages</p>
                <p className="text-xl text-off-white font-mono">{result.total_messages}</p>
              </div>
              <div className="p-4 text-center">
                <p className="text-[10px] font-semibold text-slate-500 font-mono uppercase tracking-wider mb-1">High Risk Msgs</p>
                <p className={`text-xl font-mono ${result.high_risk_message_count > 0 ? 'text-redaction-red' : 'text-off-white'}`}>
                  {result.high_risk_message_count}
                </p>
              </div>
              <div className="p-4 text-center">
                <p className="text-[10px] font-semibold text-slate-500 font-mono uppercase tracking-wider mb-1">Threat Freq.</p>
                <p className="text-xl text-off-white font-mono">
                  {((result.threat_frequency || 0) * 100).toFixed(0)}%
                </p>
              </div>
              <div className="p-4 text-center flex flex-col items-center justify-center">
                <p className="text-[10px] font-semibold text-slate-500 font-mono uppercase tracking-wider mb-1">Repeated Abuse</p>
                {result.repeated_harassment ? (
                  <span className="px-2 py-0.5 text-xs bg-redaction-red/20 text-redaction-red border border-redaction-red/50 rounded font-bold">DETECTED</span>
                ) : (
                  <span className="px-2 py-0.5 text-xs bg-slate-800 text-slate-400 border border-slate-700 rounded">CLEAN</span>
                )}
              </div>
            </div>
          </Card>
        </div>
      )}

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
              <p className="text-sm text-off-white">{result.ai_summary?.overall_sentiment || "Analyzing overall sentiment..."}</p>
            </div>
            <div className="p-5">
              <p className="text-xs font-semibold text-slate-500 font-mono uppercase tracking-wider mb-2">Harassment Pattern</p>
              <p className="text-sm text-off-white">{result.ai_summary?.harassment_pattern || "Evaluating conversation patterns..."}</p>
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
            const cat = msg.prediction.primary_label || msg.prediction.category || "Clean";
            let colorClass = "border-l-verified-teal bg-panel";
            let textClass = "text-verified-teal";
            
            if (msg.risk_score >= 70) {
              colorClass = "border-l-redaction-red bg-slate-800";
              textClass = "text-redaction-red";
            } else if (msg.risk_score >= 30) {
              colorClass = "border-l-alert-amber bg-slate-800";
              textClass = "text-alert-amber";
            }
            
            // Check if this is the start of the second half where escalation occurred
            const isMidpoint = result.total_messages >= 10 && idx === Math.floor(result.total_messages / 2);
            const showEscalationDivider = isMidpoint && result.escalation_level !== 'None';

            return (
              <div key={msg.message_id || idx} className="space-y-4">
                {showEscalationDivider && (
                  <div className="flex items-center gap-4 py-2 opacity-80">
                    <div className="h-px bg-redaction-red/50 flex-1"></div>
                    <span className="text-[10px] font-bold text-redaction-red font-mono uppercase tracking-wider bg-redaction-red/10 px-2 py-1 rounded border border-redaction-red/30">
                      Escalation Detected in Second Half
                    </span>
                    <div className="h-px bg-redaction-red/50 flex-1"></div>
                  </div>
                )}
                <Card className={`p-4 border-l-4 ${colorClass}`}>
                  <div className="flex justify-between items-start mb-2">
                    <span className="text-xs font-semibold text-off-white font-mono">{msg.sender}</span>
                    <span className="text-[10px] text-slate-500 font-mono">{new Date(msg.timestamp).toLocaleTimeString()}</span>
                  </div>
                  <p className="text-sm text-off-white mb-3">{msg.text}</p>
                  <div className="flex items-center gap-2 text-xs font-mono">
                    <span className={`font-semibold ${textClass}`}>
                      {cat}
                    </span>
                    <span className="text-slate-600">•</span>
                    <span className="text-slate-400">Risk: {msg.risk_score}</span>
                  </div>
                </Card>
              </div>
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
