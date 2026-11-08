import PropTypes from 'prop-types';
import { Layers, Lightbulb, MessageSquare, AlertTriangle, ChevronRight, Users, Activity, Link, ShieldAlert, CheckCircle2 } from 'lucide-react';
import Card from './common/Card';
import RiskBadge from './prediction/RiskBadge';
import RedactionBar from './common/RedactionBar';
import GuidancePanel from './prediction/GuidancePanel';
import PersonalizedSafetyPlan from './prediction/PersonalizedSafetyPlan';
import ThreatIntelligenceCard from './prediction/ThreatIntelligenceCard';

export default function ConversationResultDisplay({ result }) {
  if (!result || !result.messages) return null;

  // Sort messages chronologically by timestamp or sequence
  const sortedMessages = [...result.messages].sort((a, b) => {
    if (a.timestamp && b.timestamp) {
      const ta = Date.parse(a.timestamp);
      const tb = Date.parse(b.timestamp);
      if (!isNaN(ta) && !isNaN(tb)) return ta - tb;
    }
    return (a.sequence_id || 0) - (b.sequence_id || 0);
  });

  return (
    <div className="space-y-6 animate-slide-up mt-8">
      {/* ── SECTION 1: CONVERSATION ASSESSMENT ── */}
      <div className="space-y-3">
        <h2 className="text-base font-bold text-off-white font-display flex items-center gap-2">
          <Layers size={18} className="text-slate-400" />
          Conversation Assessment
        </h2>
        
        <Card className="p-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            <div className="space-y-6">
              <div>
                <p className="text-xs font-semibold text-slate-400 font-mono uppercase tracking-wider mb-3">Incident Classification</p>
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
                <p className="text-xs font-semibold text-slate-400 font-mono uppercase tracking-wider mb-3">Behavior Intelligence</p>
                <div className="flex items-center gap-3 mb-2">
                  <span className={`px-2.5 py-1 text-xs font-medium rounded border ${
                    result.escalation_level === 'High' ? 'bg-panel border-redaction-red text-redaction-red' :
                    result.escalation_level === 'Medium' ? 'bg-panel border-alert-amber text-alert-amber' :
                    'bg-panel border-slate-700 text-off-white'
                  }`}>
                    {result.escalation_level} Escalation
                  </span>
                  <span className="text-xs text-slate-300 font-mono">Score: +{result.escalation_score}</span>
                </div>
                <ul className="text-sm text-slate-300 space-y-1.5 mt-2">
                  {result.escalation_reason.map((r, i) => (
                    <li key={i} className="flex items-start gap-1.5 leading-relaxed">
                      <ChevronRight size={14} className="text-slate-400 mt-0.5 shrink-0" /> {r}
                    </li>
                  ))}
                </ul>
              </div>
            </div>

            <div className="space-y-4 border-t md:border-t-0 md:border-l border-slate-700 pt-4 md:pt-0 md:pl-8">
              <div className="flex items-center justify-between mb-2">
                <p className="text-xs font-semibold text-slate-400 font-mono uppercase tracking-wider">Detected Categories</p>
              </div>
              
              {!result.secondary_labels || Object.keys(result.secondary_labels).length === 0 ? (
                <p className="text-sm text-slate-400 italic">No secondary categories detected.</p>
              ) : (
                <div className="space-y-3">
                  {Object.entries(result.secondary_labels).map(([label, conf]) => (
                    <div key={label} className="flex items-center gap-3">
                      <span className="text-sm text-off-white w-44 truncate">{label}</span>
                      <div className="flex-1">
                        <RedactionBar score={conf} tier="amber" />
                      </div>
                      <span className="text-xs font-medium text-slate-300 font-mono tabular-nums w-10 text-right">
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

      {/* Deterministic Evidence & Flagging Reasons */}
      {result.flagging_reasons && result.flagging_reasons.length > 0 && (
        <Card className="bg-panel border-alert-amber/40 shadow-md">
          <div className="flex items-center gap-2 mb-3">
            <ShieldAlert size={16} className="text-alert-amber" />
            <p className="text-xs font-bold text-alert-amber font-mono uppercase tracking-wider mb-0">Flagged Evidence & Indicators</p>
          </div>
          <ul className="space-y-2 text-sm text-slate-200">
            {result.flagging_reasons.map((reason, idx) => (
              <li key={idx} className="flex items-start gap-2 leading-relaxed">
                <ChevronRight size={14} className="text-alert-amber mt-1 shrink-0" />
                <span>{reason}</span>
              </li>
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
              let badgeColor = "bg-slate-800 text-slate-400 border-slate-700";
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
        <Card className="bg-panel border-slate-700/60 mt-4">
          <div className="flex items-center gap-2 mb-3">
            <Activity size={14} className="text-slate-400" />
            <p className="text-xs font-bold text-slate-400 font-mono uppercase tracking-wider mb-0">Conversation Signals</p>
          </div>
          <ul className="list-disc pl-5 space-y-1 text-sm text-slate-200">
            {result.conversation_signals.map((signal, idx) => (
              <li key={idx}>{signal}</li>
            ))}
          </ul>
        </Card>
      )}

      {/* ── SECTION 1.3: ACTOR INTELLIGENCE ── */}
      {result.actor_intelligence && Object.keys(result.actor_intelligence).length > 0 && (
        <div className="space-y-3 pt-4">
          <h2 className="text-base font-bold text-off-white font-display flex items-center gap-2">
            <Users size={18} className="text-slate-400" />
            Actor Breakdown
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {Object.entries(result.actor_intelligence).map(([actor, stats]) => {
              const isPrimaryOffender = stats.risk_concentration_percentage >= 50 && stats.flagged_messages > 0;
              const isInnocent = stats.flagged_messages === 0;

              return (
                <Card 
                  key={actor} 
                  className={`p-4 border transition-all ${
                    isPrimaryOffender 
                      ? 'border-redaction-red/60 bg-redaction-red/10 shadow-[0_0_12px_rgba(239,68,68,0.15)]' 
                      : isInnocent 
                      ? 'border-slate-700/80 bg-slate-900/40' 
                      : 'border-alert-amber/50 bg-alert-amber/10'
                  }`}
                >
                  <div className="flex justify-between items-center mb-3">
                    <h3 className="text-base font-bold text-white font-mono truncate">{actor}</h3>
                    {isPrimaryOffender ? (
                      <span className="px-2 py-0.5 text-xs bg-redaction-red/20 text-redaction-red border border-redaction-red/50 rounded font-bold">
                        {stats.risk_concentration_percentage}% of Flagged
                      </span>
                    ) : isInnocent ? (
                      <span className="px-2 py-0.5 text-xs bg-slate-800 text-slate-300 border border-slate-700 rounded font-medium">
                        0 Flagged
                      </span>
                    ) : (
                      <span className="px-2 py-0.5 text-xs bg-alert-amber/20 text-alert-amber border border-alert-amber/50 rounded font-semibold">
                        {stats.flagged_messages} Flagged
                      </span>
                    )}
                  </div>
                  <div className="grid grid-cols-2 gap-2.5 text-sm">
                    <div className="bg-slate-950/50 p-2.5 rounded border border-slate-800">
                      <p className="text-xs font-semibold text-slate-400 font-mono uppercase tracking-wider mb-0.5">Total</p>
                      <p className="text-base font-bold text-white font-mono">{stats.total_messages}</p>
                    </div>
                    <div className="bg-slate-950/50 p-2.5 rounded border border-slate-800">
                      <p className="text-xs font-semibold text-slate-400 font-mono uppercase tracking-wider mb-0.5">Flagged</p>
                      <p className={`text-base font-bold font-mono ${stats.flagged_messages > 0 ? "text-redaction-red" : "text-emerald-400"}`}>
                        {stats.flagged_messages}
                      </p>
                    </div>
                    <div className="bg-slate-950/50 p-2.5 rounded border border-slate-800">
                      <p className="text-xs font-semibold text-slate-400 font-mono uppercase tracking-wider mb-0.5">High Risk</p>
                      <p className={`text-base font-bold font-mono ${stats.high_risk_messages > 0 ? "text-redaction-red" : "text-slate-300"}`}>
                        {stats.high_risk_messages}
                      </p>
                    </div>
                    <div className="bg-slate-950/50 p-2.5 rounded border border-slate-800">
                      <p className="text-xs font-semibold text-slate-400 font-mono uppercase tracking-wider mb-0.5">Avg Risk</p>
                      <p className="text-base font-bold text-white font-mono">{stats.average_risk_score.toFixed(1)}</p>
                    </div>
                  </div>
                </Card>
              );
            })}
          </div>
        </div>
      )}

      {/* ── SECTION 1.4: TEMPORAL INTELLIGENCE ── */}
      {result.temporal_intelligence && result.temporal_intelligence.risk_timeline && result.temporal_intelligence.risk_timeline.length > 0 && (
        <div className="space-y-3 pt-4">
          <h2 className="text-base font-bold text-off-white font-display flex items-center gap-2">
            <Activity size={18} className="text-slate-400" />
            Risk Timeline
          </h2>
          <Card className="p-4">
            <div className="flex items-center gap-4 overflow-x-auto pb-2">
              {result.temporal_intelligence.risk_timeline.map((point, idx) => (
                <div key={idx} className="flex flex-col items-center gap-2 min-w-[24px]">
                  <div className="text-xs text-slate-400 font-mono">#{point.sequence + 1}</div>
                  <div 
                    className={`w-4 rounded-t ${point.is_high_risk ? 'bg-redaction-red' : point.risk_score > 0 ? 'bg-alert-amber' : 'bg-slate-700'}`}
                    style={{ height: `${Math.max(point.risk_score, 5)}px`, minHeight: '5px' }}
                    title={`Risk: ${point.risk_score}`}
                  ></div>
                </div>
              ))}
            </div>
            {result.temporal_intelligence.high_risk_clusters && result.temporal_intelligence.high_risk_clusters.length > 0 && (
              <p className="text-xs text-slate-300 mt-4">
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
          <h2 className="text-base font-bold text-off-white font-display flex items-center gap-2">
            <Layers size={18} className="text-slate-400" />
            Conversation Stats
          </h2>
          <Card className="p-0 overflow-hidden">
            <div className="grid grid-cols-2 md:grid-cols-4 divide-x divide-y md:divide-y-0 divide-slate-700">
              <div className="p-4 text-center">
                <p className="text-xs font-semibold text-slate-400 font-mono uppercase tracking-wider mb-1">Total Messages</p>
                <p className="text-2xl text-off-white font-mono font-bold">{result.total_messages}</p>
              </div>
              <div className="p-4 text-center">
                <p className="text-xs font-semibold text-slate-400 font-mono uppercase tracking-wider mb-1">High Risk Msgs</p>
                <p className={`text-2xl font-mono font-bold ${result.high_risk_message_count > 0 ? 'text-redaction-red' : 'text-off-white'}`}>
                  {result.high_risk_message_count}
                </p>
              </div>
              <div className="p-4 text-center">
                <p className="text-xs font-semibold text-slate-400 font-mono uppercase tracking-wider mb-1">Threat Freq.</p>
                <p className="text-2xl text-off-white font-mono font-bold">
                  {((result.threat_frequency || 0) * 100).toFixed(0)}%
                </p>
              </div>
              <div className="p-4 text-center flex flex-col items-center justify-center">
                <p className="text-xs font-semibold text-slate-400 font-mono uppercase tracking-wider mb-1">Repeated Abuse</p>
                {result.repeated_harassment ? (
                  <span className="px-2.5 py-1 text-xs bg-redaction-red/20 text-redaction-red border border-redaction-red/50 rounded font-bold">DETECTED</span>
                ) : (
                  <span className="px-2.5 py-1 text-xs bg-slate-800 text-slate-300 border border-slate-700 rounded font-medium">CLEAN</span>
                )}
              </div>
            </div>
          </Card>
        </div>
      )}

      {/* ── SECTION 2: AI SUMMARY ── */}
      <div className="space-y-3 pt-4">
        <h2 className="text-base font-bold text-off-white font-display flex items-center gap-2">
          <Lightbulb size={18} className="text-slate-400" />
          AI Recommendation
        </h2>
        
        <Card className="p-0 overflow-hidden">
          <div className="grid grid-cols-1 md:grid-cols-2 divide-y md:divide-y-0 md:divide-x divide-slate-700">
            <div className="p-5">
              <p className="text-xs font-semibold text-slate-400 font-mono uppercase tracking-wider mb-2">Overall Sentiment</p>
              <p className="text-sm text-slate-200 leading-relaxed">{result.ai_summary?.overall_sentiment || "Analyzing overall sentiment..."}</p>
            </div>
            <div className="p-5">
              <p className="text-xs font-semibold text-slate-400 font-mono uppercase tracking-wider mb-2">Harassment Pattern</p>
              <p className="text-sm text-slate-200 leading-relaxed">{result.ai_summary?.harassment_pattern || "Evaluating conversation patterns..."}</p>
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
          <h2 className="text-base font-bold text-off-white font-display flex items-center gap-2">
            <AlertTriangle size={18} className="text-alert-amber" />
            Victim Guidance
          </h2>
          <GuidancePanel guidance={result.guidance} />
        </div>
      )}

      {/* ── SECTION 3: PER-MESSAGE BREAKDOWN TABLE (Sorted by Time) ── */}
      <div className="space-y-3 pt-4">
        <div className="flex items-center justify-between">
          <h2 className="text-base font-bold text-off-white font-display flex items-center gap-2">
            <MessageSquare size={18} className="text-slate-400" />
            Per-Message Threat Breakdown
          </h2>
          <span className="text-xs text-slate-400 font-mono">
            {sortedMessages.length} messages (sorted by time)
          </span>
        </div>

        <Card className="p-0 overflow-hidden border border-slate-700/80 shadow-lg">
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-slate-900/90 border-b border-slate-700 text-xs font-semibold text-slate-300 font-mono uppercase tracking-wider">
                  <th className="py-3.5 px-4 w-12 text-center">#</th>
                  <th className="py-3.5 px-4 w-28">Time</th>
                  <th className="py-3.5 px-4 w-32">Sender</th>
                  <th className="py-3.5 px-4">Message Content</th>
                  <th className="py-3.5 px-4 w-44">Category</th>
                  <th className="py-3.5 px-4 w-28 text-center">Risk Score</th>
                  <th className="py-3.5 px-4 w-24 text-center">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800 text-sm font-sans">
                {sortedMessages.map((msg, idx) => {
                  const pred = msg.prediction || {};
                  const cat = pred.primary_label || pred.category || "Clean";
                  const score = Number(msg.risk_score || 0);
                  const isFlagged = msg.is_flagged !== undefined 
                    ? msg.is_flagged 
                    : (score >= 30 && cat.toLowerCase() !== 'clean');
                  
                  let rowBg = "hover:bg-slate-800/40";
                  let catColor = "bg-verified-teal/15 text-verified-teal border-verified-teal/30";
                  if (score >= 70) {
                    rowBg = "bg-redaction-red/10 hover:bg-redaction-red/15";
                    catColor = "bg-redaction-red/20 text-redaction-red border-redaction-red/40";
                  } else if (score >= 30) {
                    rowBg = "bg-alert-amber/5 hover:bg-alert-amber/10";
                    catColor = "bg-alert-amber/20 text-alert-amber border-alert-amber/40";
                  }

                  const timeStr = msg.timestamp 
                    ? (!isNaN(Date.parse(msg.timestamp)) ? new Date(msg.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : msg.timestamp)
                    : `+${idx}m`;

                  return (
                    <tr key={msg.message_id || idx} className={`transition-colors ${rowBg}`}>
                      <td className="py-3.5 px-4 text-center text-xs text-slate-400 font-mono">
                        {idx + 1}
                      </td>
                      <td className="py-3.5 px-4 text-xs text-slate-300 font-mono whitespace-nowrap">
                        {timeStr}
                      </td>
                      <td className="py-3.5 px-4 font-semibold text-white font-mono whitespace-nowrap">
                        {msg.sender}
                      </td>
                      <td className="py-3.5 px-4 text-slate-200 break-words leading-relaxed max-w-md">
                        {msg.text}
                      </td>
                      <td className="py-3.5 px-4 whitespace-nowrap">
                        <span className={`inline-block px-2.5 py-1 rounded text-xs font-semibold border ${catColor}`}>
                          {cat}
                        </span>
                      </td>
                      <td className="py-3.5 px-4 text-center font-mono text-xs whitespace-nowrap">
                        <span className={`inline-block px-2.5 py-1 rounded font-bold ${
                          score >= 70 ? 'bg-redaction-red/25 text-red-400 border border-redaction-red/40' :
                          score >= 30 ? 'bg-alert-amber/25 text-amber-300 border border-alert-amber/40' :
                          'bg-slate-800/80 text-slate-300 border border-slate-700'
                        }`}>
                          {score.toFixed(0)} / 100
                        </span>
                      </td>
                      <td className="py-3.5 px-4 text-center whitespace-nowrap">
                        {isFlagged ? (
                          <span className="inline-flex items-center gap-1 px-2.5 py-1 text-xs font-bold rounded bg-redaction-red/20 text-redaction-red border border-redaction-red/50 uppercase tracking-wide">
                            <ShieldAlert size={12} />
                            Flagged
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 px-2.5 py-1 text-xs font-semibold rounded bg-slate-800 text-emerald-400 border border-slate-700 uppercase tracking-wide">
                            <CheckCircle2 size={12} />
                            Clean
                          </span>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </Card>
      </div>
    </div>
  );
}

ConversationResultDisplay.propTypes = {
  result: PropTypes.object
};
