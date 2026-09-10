import PropTypes from 'prop-types';
import { Layers, Lightbulb, MessageSquare, AlertTriangle, ChevronRight, Users, Activity, Link } from 'lucide-react';
import Card from './common/Card';
import RiskBadge from './prediction/RiskBadge';
import RedactionBar from './common/RedactionBar';
import GuidancePanel from './prediction/GuidancePanel';
import PersonalizedSafetyPlan from './prediction/PersonalizedSafetyPlan';
import ThreatIntelligenceCard from './prediction/ThreatIntelligenceCard';

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

      {/* Deterministic Flagging Reasons */}
      {result.flagging_reasons && result.flagging_reasons.length > 0 && (
        <Card className="bg-panel border-alert-amber/30">
          <div className="flex items-center gap-2 mb-3">
            <Layers size={14} className="text-alert-amber" />
            <p className="text-xs font-bold text-alert-amber font-mono uppercase tracking-wider mb-0">Why was this flagged?</p>
          </div>
          <ul className="list-disc pl-5 space-y-1 text-sm text-off-white">
            {result.flagging_reasons.map((reason, idx) => (
              <li key={idx}>{reason}</li>
            ))}
          </ul>
        </Card>
      )}

      {/* Threat Intel / Malicious URLs */}
      {result.malicious_urls && result.malicious_urls.filter(u => u.status !== 'Safe').length > 0 && (
        <Card className="bg-panel border-redaction-red/30 mt-4">
          <div className="flex items-center gap-2 mb-3">
            <Link size={14} className="text-redaction-red" />
            <p className="text-xs font-bold text-redaction-red font-mono uppercase tracking-wider mb-0">Threat Intel Warning</p>
          </div>
          <div className="space-y-3">
            {result.malicious_urls.filter(u => u.status !== 'Safe').map((urlObj, idx) => {
              let badgeColor = "bg-slate-800 text-slate-400 border-slate-700"; // Unknown
              if (urlObj.status === "High Risk") {
                badgeColor = "bg-redaction-red/20 text-redaction-red border-redaction-red/50"; 
              } else if (urlObj.status === "Suspicious") {
                badgeColor = "bg-alert-amber/20 text-alert-amber border-alert-amber/50";
              }

              return (
                <div key={idx} className="flex flex-col md:flex-row md:items-center justify-between p-3 rounded bg-slate-800/50 border border-slate-700/50 gap-3">
                  <div className="flex items-center gap-2 overflow-hidden">
                    <span className={`text-xs px-2 py-0.5 rounded border font-semibold whitespace-nowrap ${badgeColor}`}>
                      {urlObj.status}
                    </span>
                    <span className="text-sm font-mono text-off-white truncate" title={urlObj.url}>
                      {urlObj.url}
                    </span>
                  </div>
                  <div className="flex items-center gap-3 text-xs md:justify-end shrink-0">
                    <span className="text-slate-400">
                      Reason: <span className="font-semibold text-off-white">{urlObj.reason}</span>
                    </span>
                    <span className="px-2 py-1 bg-panel rounded border border-slate-700 font-mono text-off-white">
                      Risk: {urlObj.risk_score}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        </Card>
      )}

      {/* Advanced Threat Intelligence Signals */}
      <ThreatIntelligenceCard result={result} isConversation={true} />

      {/* ── SECTION 1.2: CONVERSATION SIGNALS ── */}
      {result.conversation_signals && result.conversation_signals.length > 0 && (
        <Card className="bg-panel border-slate-700/50 mt-4">
          <div className="flex items-center gap-2 mb-3">
            <Activity size={14} className="text-slate-400" />
            <p className="text-xs font-bold text-slate-400 font-mono uppercase tracking-wider mb-0">Conversation Signals</p>
          </div>
          <ul className="list-disc pl-5 space-y-1 text-sm text-off-white">
            {result.conversation_signals.map((signal, idx) => (
              <li key={idx}>{signal}</li>
            ))}
          </ul>
        </Card>
      )}

      {/* ── SECTION 1.3: ACTOR INTELLIGENCE ── */}
      {result.actor_intelligence && Object.keys(result.actor_intelligence).length > 0 && (
        <div className="space-y-3 pt-4">
          <h2 className="text-sm font-bold text-off-white font-display flex items-center gap-2">
            <Users size={18} className="text-slate-500" />
            Actor Breakdown
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {Object.entries(result.actor_intelligence).map(([actor, stats]) => (
              <Card key={actor} className="p-4 border-slate-700">
                <div className="flex justify-between items-center mb-3">
                  <h3 className="font-bold text-off-white font-mono truncate">{actor}</h3>
                  {stats.risk_concentration_percentage > 50 && (
                    <span className="px-2 py-0.5 text-xs bg-redaction-red/20 text-redaction-red border border-redaction-red/50 rounded font-bold">
                      {stats.risk_concentration_percentage}% of Flagged
                    </span>
                  )}
                </div>
                <div className="grid grid-cols-2 gap-3 text-sm">
                  <div>
                    <p className="text-[10px] font-semibold text-slate-500 font-mono uppercase tracking-wider mb-1">Total</p>
                    <p className="text-off-white">{stats.total_messages}</p>
                  </div>
                  <div>
                    <p className="text-[10px] font-semibold text-slate-500 font-mono uppercase tracking-wider mb-1">Flagged</p>
                    <p className={stats.flagged_messages > 0 ? "text-alert-amber" : "text-off-white"}>{stats.flagged_messages}</p>
                  </div>
                  <div>
                    <p className="text-[10px] font-semibold text-slate-500 font-mono uppercase tracking-wider mb-1">High Risk</p>
                    <p className={stats.high_risk_messages > 0 ? "text-redaction-red" : "text-off-white"}>{stats.high_risk_messages}</p>
                  </div>
                  <div>
                    <p className="text-[10px] font-semibold text-slate-500 font-mono uppercase tracking-wider mb-1">Avg Risk</p>
                    <p className="text-off-white">{stats.average_risk_score.toFixed(1)}</p>
                  </div>
                </div>
              </Card>
            ))}
          </div>
        </div>
      )}

      {/* ── SECTION 1.4: TEMPORAL INTELLIGENCE ── */}
      {result.temporal_intelligence && result.temporal_intelligence.risk_timeline && result.temporal_intelligence.risk_timeline.length > 0 && (
        <div className="space-y-3 pt-4">
          <h2 className="text-sm font-bold text-off-white font-display flex items-center gap-2">
            <Activity size={18} className="text-slate-500" />
            Risk Timeline
          </h2>
          <Card className="p-4">
            <div className="flex items-center gap-4 overflow-x-auto pb-2">
              {result.temporal_intelligence.risk_timeline.map((point, idx) => (
                <div key={idx} className="flex flex-col items-center gap-2 min-w-[24px]">
                  <div className="text-[9px] text-slate-500 font-mono">#{point.sequence + 1}</div>
                  <div 
                    className={`w-4 rounded-t ${point.is_high_risk ? 'bg-redaction-red' : point.risk_score > 0 ? 'bg-alert-amber' : 'bg-slate-700'}`}
                    style={{ height: `${Math.max(point.risk_score, 5)}px`, minHeight: '5px' }}
                    title={`Risk: ${point.risk_score}`}
                  ></div>
                </div>
              ))}
            </div>
            {result.temporal_intelligence.high_risk_clusters && result.temporal_intelligence.high_risk_clusters.length > 0 && (
              <p className="text-xs text-slate-400 mt-4">
                <span className="text-redaction-red font-bold">Detected: </span> 
                {result.temporal_intelligence.high_risk_clusters.length} high-risk message cluster(s).
              </p>
            )}
          </Card>
        </div>
      )}

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
      
      {/* ── SECTION 2.5: PERSONALIZED SAFETY PLAN ── */}
      {result.evidence_plan && (
        <PersonalizedSafetyPlan result={result} />
      )}
      
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
