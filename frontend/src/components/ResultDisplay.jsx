import React from 'react';
import PropTypes from 'prop-types';
import {
  Layers,
  Activity,
  Terminal,
  Lightbulb,
  Link,
  Sparkles,
  ShieldAlert,
  ShieldCheck,
  AlertTriangle,
  PhoneCall,
  ExternalLink,
  FileCheck2,
  Cpu
} from 'lucide-react';
import Card from './common/Card';
import RiskBadge from './prediction/RiskBadge';
import RiskGauge from './prediction/RiskGauge';
import ConfidenceBar from './prediction/ConfidenceBar';
import RedactionBar from './common/RedactionBar';
import PredictionSummary from './prediction/PredictionSummary';
import ConversationResultDisplay from './ConversationResultDisplay';
import GuidancePanel from './prediction/GuidancePanel';
import ExplainPanel from './prediction/ExplainPanel';
import PersonalizedSafetyPlan from './prediction/PersonalizedSafetyPlan';
import ThreatIntelligenceCard from './prediction/ThreatIntelligenceCard';

function getSecondaryTier(label) {
  const l = (label || '').toLowerCase();
  if (['threat', 'blackmail', 'extortion', 'hate_speech', 'hate speech', 'sextortion'].includes(l)) return 'danger';
  if (['scam', 'phishing', 'fraud'].includes(l)) return 'warning';
  return 'blue';
}

export default function ResultDisplay({ result }) {
  if (!result) return null;
  if (result.messages) return <ConversationResultDisplay result={result} />;

  const isHarassing = result.label === 'harassing';
  const score = Math.round(result.threat_score ?? result.risk_score ?? 0);
  const signals = result.signals || [];
  const flaggingReasons = result.flagging_reasons || [];

  return (
    <div className="space-y-5 animate-slide-up mt-6">
      {/* ── Top Row: Gauge + Classification + Confidence + Engine ── */}
      <div className="grid grid-cols-1 md:grid-cols-12 gap-4">
        {/* Risk Gauge */}
        <Card className="md:col-span-4 flex items-center justify-center p-3 bg-surface/90 border border-border">
          <RiskGauge score={score} size={220} label="Threat Severity Gauge" />
        </Card>

        {/* Risk Classification & Level */}
        <Card className="md:col-span-4 p-5 flex flex-col justify-between bg-surface/90 border border-border">
          <div>
            <p className="section-title">Risk Assessment</p>
            <RiskBadge
              safetyStatus={result.safety_status}
              severityTier={result.severity_tier}
              category={result.category || result.primary_label || 'none'}
              threatScore={score}
            />
          </div>
          <div className="mt-4 pt-3 border-t border-border/50 text-xs font-mono text-text-muted flex items-center justify-between">
            <span>Primary Category:</span>
            <span className="font-semibold text-text-primary uppercase">
              {(result.category || result.primary_label || 'None').replace(/_/g, ' ')}
            </span>
          </div>
        </Card>

        {/* Model Engine & Confidence */}
        <Card className="md:col-span-4 p-5 flex flex-col justify-between bg-surface/90 border border-border">
          <div>
            <p className="section-title">Detection Pipeline</p>
            <div className="space-y-2">
              <div className="flex items-center gap-1.5 text-xs text-text-muted">
                <Cpu size={14} className="text-cyan-400" />
                <span>Engine:</span>
                <span className="font-mono font-semibold text-cyan-300">
                  {result.model || 'DistilBERT Multi-Label + Rules'}
                </span>
              </div>
              <div className="mt-3">
                <p className="text-xs text-text-muted mb-1 font-mono">Neural Model Confidence:</p>
                <ConfidenceBar
                  confidence={result.confidence}
                  isHarassing={isHarassing}
                />
              </div>
            </div>
          </div>
          {result.timestamp && (
            <p className="text-2xs text-text-muted pt-3 border-t border-border/50 font-mono">
              Evaluated at: {new Date(result.timestamp).toLocaleTimeString()}
            </p>
          )}
        </Card>
      </div>

      {/* ── Plain-English Threat Explanation ── */}
      <Card className="p-5 bg-surface/90 border border-border">
        <div className="flex items-center gap-2 mb-3 pb-2 border-b border-border/50">
          <Sparkles size={16} className="text-cyan-400" />
          <h3 className="section-title mb-0 text-cyan-300 font-bold tracking-wider">
            Plain-English Threat Assessment
          </h3>
        </div>

        <div className="text-sm text-text-primary leading-relaxed space-y-2">
          {score >= 80 ? (
            <p className="text-red-200">
              <strong className="text-red-400">Critical Threat Identified:</strong> This content contains severe risk markers such as direct physical threats, criminal extortion/blackmail, or malicious phishing links designed to compromise credentials or funds. Immediate defensive measures should be taken.
            </p>
          ) : score >= 55 ? (
            <p className="text-orange-200">
              <strong className="text-orange-400">High Risk Detected:</strong> This message displays clear patterns of harassment, cyberbullying, aggressive pressure, or suspicious fraudulent links. Do not engage with the sender or reveal sensitive data.
            </p>
          ) : score >= 30 ? (
            <p className="text-amber-200">
              <strong className="text-amber-400">Medium Risk Warning:</strong> Moderately offensive expressions, suspicious urgency keywords, or mild social engineering tactics were identified. Proceed with caution.
            </p>
          ) : (
            <p className="text-emerald-200">
              <strong className="text-emerald-400">Low Risk Content:</strong> No credible indicators of phishing, blackmail, harassment, or physical threats were discovered in this submission.
            </p>
          )}

          {/* Detailed summary if present */}
          {result.bot_summary_text && (
            <div className="mt-3 p-3 rounded-lg bg-black/40 border border-border/60 text-xs font-mono text-text-secondary whitespace-pre-wrap">
              {result.bot_summary_text}
            </div>
          )}
        </div>
      </Card>

      {/* ── Contributing Detection Signals ── */}
      {(signals.length > 0 || flaggingReasons.length > 0) && (
        <Card className="p-5 bg-surface/90 border border-border">
          <div className="flex items-center gap-2 mb-4 pb-2 border-b border-border/50">
            <Layers size={16} className="text-amber-400" />
            <h3 className="section-title mb-0 text-amber-300 font-bold tracking-wider">
              Contributing Detection Signals ({signals.length || flaggingReasons.length})
            </h3>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {signals.length > 0 ? (
              signals.map((sig, idx) => (
                <div
                  key={idx}
                  className="p-3 rounded-lg bg-black/40 border border-border/60 flex items-start justify-between gap-3 text-xs font-mono"
                >
                  <div className="space-y-1 overflow-hidden">
                    <div className="flex items-center gap-2">
                      <span className="w-1.5 h-1.5 rounded-full bg-cyan-400" />
                      <span className="font-bold text-text-primary truncate">
                        {sig.signal || sig.name || 'Threat Signal'}
                      </span>
                    </div>
                    {sig.detail && (
                      <p className="text-text-muted text-[11px] truncate">{sig.detail}</p>
                    )}
                  </div>
                  <div className="flex flex-col items-end shrink-0 gap-1">
                    <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-surface border border-border text-text-secondary">
                      {sig.category || 'Rule'}
                    </span>
                    {sig.weight != null && (
                      <span className="text-[10px] text-amber-400 font-bold">
                        +{Math.round(sig.weight)} pts
                      </span>
                    )}
                  </div>
                </div>
              ))
            ) : (
              flaggingReasons.map((reason, idx) => (
                <div
                  key={idx}
                  className="p-3 rounded-lg bg-black/40 border border-border/60 flex items-center gap-2.5 text-xs text-text-secondary font-mono"
                >
                  <span className="w-1.5 h-1.5 rounded-full bg-amber-400 shrink-0" />
                  <span>{reason}</span>
                </div>
              ))
            )}
          </div>
        </Card>
      )}

      {/* ── Actionable Safety Advice & Emergency Helplines ── */}
      <Card className="p-5 bg-surface/90 border border-cyan-500/30">
        <div className="flex items-center gap-2 mb-3 pb-2 border-b border-border/50">
          <FileCheck2 size={16} className="text-cyan-400" />
          <h3 className="section-title mb-0 text-cyan-300 font-bold tracking-wider">
            Actionable Safety Advice & Legal Helplines
          </h3>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="p-3.5 rounded-xl bg-black/40 border border-border/60 space-y-1.5">
            <div className="flex items-center gap-1.5 text-red-400 font-bold text-xs uppercase font-mono">
              <PhoneCall size={14} /> Emergency Danger
            </div>
            <p className="text-lg font-mono font-extrabold text-red-300">Call 112</p>
            <p className="text-[11px] text-text-muted leading-relaxed">
              If you or someone else is in immediate physical danger, contact emergency services first.
            </p>
          </div>

          <div className="p-3.5 rounded-xl bg-black/40 border border-border/60 space-y-1.5">
            <div className="flex items-center gap-1.5 text-amber-400 font-bold text-xs uppercase font-mono">
              <PhoneCall size={14} /> Cyber Fraud Helpline
            </div>
            <p className="text-lg font-mono font-extrabold text-amber-300">Call 1930</p>
            <p className="text-[11px] text-text-muted leading-relaxed">
              National cybercrime helpline to freeze unauthorized financial transactions and file immediate alerts.
            </p>
          </div>

          <div className="p-3.5 rounded-xl bg-black/40 border border-border/60 space-y-1.5">
            <div className="flex items-center gap-1.5 text-cyan-400 font-bold text-xs uppercase font-mono">
              <ExternalLink size={14} /> National Cyber Portal
            </div>
            <a
              href="https://cybercrime.gov.in"
              target="_blank"
              rel="noopener noreferrer"
              className="text-xs font-mono font-bold text-cyan-300 underline block hover:text-white"
            >
              cybercrime.gov.in &rarr;
            </a>
            <p className="text-[11px] text-text-muted leading-relaxed">
              Official Indian government portal for submitting formal digital harassment, extortion, and cyber fraud FIRs.
            </p>
          </div>
        </div>

        {/* Immediate Practical Victim Steps */}
        <div className="mt-4 pt-3 border-t border-border/40 text-xs text-text-secondary space-y-1.5">
          <p className="font-semibold text-text-primary">Recommended Victim Precautions:</p>
          <ul className="list-disc pl-5 space-y-1 font-mono text-[11px] text-text-muted">
            <li><strong>Do not transfer funds or Bitcoin:</strong> Extortionists routinely demand additional payments once money is sent.</li>
            <li><strong>Preserve Evidence:</strong> Capture full timestamped screenshots of messages, handles, and URLs before blocking.</li>
            <li><strong>Verify Shortened Links:</strong> Never enter OTPs or passwords on unverified domain redirects.</li>
          </ul>
        </div>
      </Card>

      {/* Threat Intel / Malicious URLs (if present) */}
      {result.malicious_urls && result.malicious_urls.filter(u => u.status !== 'Safe').length > 0 && (
        <Card className="border border-red-500/30 bg-surface/90">
          <div className="flex items-center gap-2 mb-3">
            <Link size={14} className="text-red-400" />
            <p className="section-title mb-0 text-red-300 font-bold text-xs">Malicious & Suspicious URLs Identified</p>
          </div>
          <div className="space-y-2">
            {result.malicious_urls.filter(u => u.status !== 'Safe').map((urlObj, idx) => (
              <div key={idx} className="flex flex-col md:flex-row md:items-center justify-between p-3 rounded bg-black/40 border border-border/60 gap-2 text-xs">
                <span className="font-mono text-red-200 truncate">{urlObj.url}</span>
                <span className="font-mono text-text-muted">{urlObj.reason} (Risk: {urlObj.risk_score})</span>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* Advanced Threat Intelligence Card */}
      <ThreatIntelligenceCard result={result} />

      {/* Guidance panel */}
      {result.guidance && <GuidancePanel guidance={result.guidance} />}
    </div>
  );
}

ResultDisplay.propTypes = {
  result: PropTypes.shape({
    label: PropTypes.string,
    category: PropTypes.string,
    confidence: PropTypes.number,
    model: PropTypes.string,
    explanation: PropTypes.array,
    transcript: PropTypes.string,
    threat_score: PropTypes.number,
    risk_score: PropTypes.number,
    severity_tier: PropTypes.string,
    safety_status: PropTypes.string,
    primary_label: PropTypes.string,
    secondary_labels: PropTypes.object,
    signals: PropTypes.array,
    flagging_reasons: PropTypes.array,
    bot_summary_text: PropTypes.string,
    guidance: PropTypes.object,
    threat_intel: PropTypes.object,
    malicious_urls: PropTypes.array,
    timestamp: PropTypes.string,
  }),
};
