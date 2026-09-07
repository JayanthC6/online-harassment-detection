import PropTypes from 'prop-types';
import { Layers, Activity, Terminal, Lightbulb, Link, Sparkles } from 'lucide-react';
import Card from './common/Card';
import RiskBadge from './prediction/RiskBadge';
import ConfidenceBar from './prediction/ConfidenceBar';
import RedactionBar from './common/RedactionBar';
import ToxicWordHighlight from './prediction/ToxicWordHighlight';
import PredictionSummary from './prediction/PredictionSummary';
import ConversationResultDisplay from './ConversationResultDisplay';
import GuidancePanel from './prediction/GuidancePanel';
import ExplainPanel from './prediction/ExplainPanel';

function getSecondaryTier(label) {
  const l = label.toLowerCase();
  if (['threat', 'blackmail', 'extortion', 'hate_speech', 'hate speech'].includes(l)) return 'danger';
  if (['scam', 'phishing', 'fraud'].includes(l)) return 'warning';
  return 'blue';
}

export default function ResultDisplay({ result }) {
  if (!result) return null;
  if (result.messages) return <ConversationResultDisplay result={result} />;

  const isHarassing = result.label === 'harassing';

  return (
    <div className="space-y-4 animate-slide-up mt-6">
      {/* Top row: Risk + Confidence + Model */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Risk Classification */}
        <Card className="col-span-1">
          <p className="section-title">Risk Classification</p>
          <RiskBadge
            safetyStatus={result.safety_status}
            severityTier={result.severity_tier}
            category={result.category}
            threatScore={result.threat_score}
          />
        </Card>

        {/* Confidence */}
        <Card className="col-span-1">
          <p className="section-title">Model Confidence</p>
          <ConfidenceBar
            confidence={result.confidence}
            isHarassing={isHarassing}
          />
        </Card>

        {/* Model info */}
        <Card className="col-span-1">
          <p className="section-title">Detection Engine</p>
          <p className="text-xs font-mono text-text-secondary break-words leading-relaxed">
            {result.model || 'ShieldAI Pipeline'}
          </p>
          {result.timestamp && (
            <p className="text-2xs text-text-muted mt-3 font-mono">
              {new Date(result.timestamp).toLocaleString()}
            </p>
          )}
        </Card>
      </div>

      {/* Second row: Secondary labels + Highlights */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Secondary labels */}
        <Card>
          <div className="flex items-center gap-2 mb-4">
            <Lightbulb size={14} className="text-blue" />
            <p className="section-title mb-0">Secondary Classifications</p>
          </div>
          {!result.secondary_labels || Object.keys(result.secondary_labels).length === 0 ? (
            <p className="text-sm text-text-muted italic">No secondary categories detected.</p>
          ) : (
            <div className="space-y-3">
              {Object.entries(result.secondary_labels).map(([label, conf]) => (
                <div key={label} className="flex items-center gap-3">
                  <span className="text-sm text-text-secondary w-36 truncate flex-shrink-0">{label}</span>
                  <div className="flex-1">
                    <RedactionBar score={conf} tier={getSecondaryTier(label)} heightClass="h-1.5" />
                  </div>
                  <span className="text-xs font-mono text-text-muted w-10 text-right tabular-nums">
                    {(conf * 100).toFixed(0)}%
                  </span>
                </div>
              ))}
            </div>
          )}
        </Card>

        {/* AI Insights */}
        <Card>
          <div className="flex items-center gap-2 mb-4">
            <Activity size={14} className="text-blue" />
            <p className="section-title mb-0">AI Insights</p>
          </div>
          <PredictionSummary
            isHarassing={isHarassing}
            category={result.category}
            confidence={result.confidence}
            textToSummarize={result.text_preview || result.transcript || result.extracted_text}
          />
        </Card>
      </div>

      {result.bot_summary_text && (
        <Card className="bg-blue-muted border-blue">
          <div className="flex items-center gap-2 mb-2">
            <Sparkles size={16} className="text-blue" />
            <p className="section-title mb-0 text-blue font-bold text-sm">AI Agent Analysis & Recommended Action</p>
          </div>
          <div className="text-sm text-text-primary mt-2 whitespace-pre-wrap leading-relaxed">
            {result.bot_summary_text}
          </div>
        </Card>
      )}

      {/* Threat Intel / Malicious URLs */}
      {result.malicious_urls && result.malicious_urls.filter(u => u.status !== 'Safe').length > 0 && (
        <Card className="border border-danger/30 bg-background-elevated">
          <div className="flex items-center gap-2 mb-4">
            <Link size={14} className="text-danger" />
            <p className="section-title mb-0 text-danger font-bold text-sm">Threat Intel Warning</p>
          </div>
          <div className="space-y-3">
            {result.malicious_urls.filter(u => u.status !== 'Safe').map((urlObj, idx) => {
              let badgeColor = "bg-surface text-text-muted border-border"; // Unknown (Gray/Muted)
              if (urlObj.status === "High Risk") {
                badgeColor = "bg-danger/20 text-danger border-danger/50"; // Red
              } else if (urlObj.status === "Suspicious") {
                badgeColor = "bg-warning/20 text-warning border-warning/50"; // Orange/Yellow
              }

              return (
                <div key={idx} className="flex flex-col md:flex-row md:items-center justify-between p-3 rounded bg-surface/50 border border-border/50 gap-3">
                  <div className="flex items-center gap-2 overflow-hidden">
                    <span className={`text-xs px-2 py-0.5 rounded border font-semibold whitespace-nowrap ${badgeColor}`}>
                      {urlObj.status}
                    </span>
                    <span className="text-sm font-mono text-text-primary truncate" title={urlObj.url}>
                      {urlObj.url}
                    </span>
                  </div>
                  <div className="flex items-center gap-3 text-xs md:justify-end shrink-0">
                    <span className="text-text-secondary">
                      Reason: <span className="font-semibold text-text-primary">{urlObj.reason}</span>
                    </span>
                    <span className="px-2 py-1 bg-background rounded border border-border font-mono">
                      Risk: {urlObj.risk_score}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        </Card>
      )}

      {/* Third row: Evidence panel */}
      <Card className="terminal-block">
        <div className="flex items-center gap-2 px-1 pb-3 border-b border-border mb-4">
          <div className="flex gap-1.5">
            <div className="w-2.5 h-2.5 rounded-full bg-danger opacity-60" />
            <div className="w-2.5 h-2.5 rounded-full bg-warning opacity-40" />
            <div className="w-2.5 h-2.5 rounded-full bg-success opacity-40" />
          </div>
          <span className="text-2xs text-text-muted font-mono ml-2">analysis_output.log</span>
        </div>

        <div className="font-mono text-xs leading-relaxed text-text-muted space-y-2 max-h-64 overflow-y-auto">
          <p className="text-blue">{'>'} Forensic evidence extraction complete.</p>

          {result.evidence && (
            <>
              <p className="text-text-secondary">{'>'} Detected Evidence:</p>
              <div className="pl-4 text-text-primary border-l-2 border-blue ml-2 whitespace-pre-wrap">
                {result.evidence}
              </div>
            </>
          )}

          {result.extracted_text && (
            <>
              <p className="text-text-secondary mt-3">{'>'} OCR extraction:</p>
              <div className="pl-4 text-text-primary border-l-2 border-blue ml-2">
                {result.extracted_text}
              </div>
            </>
          )}

          {result.similar_reports?.length > 0 && (
            <>
              <p className="text-danger mt-3">{'>'} Correlated incidents ({result.similar_reports.length}):</p>
              {result.similar_reports.map((sr, i) => (
                <div key={i} className="pl-4 flex items-start gap-2">
                  <span className="text-danger mt-0.5">▸</span>
                  <span className="text-text-muted">
                    "{sr.text_preview}" —{' '}
                    <span className="text-warning">{Math.round(sr.similarity * 100)}% match</span>
                  </span>
                </div>
              ))}
            </>
          )}

          {result.threat_intel?.urls?.length > 0 && (
            <>
              <p className="text-warning mt-3">{'>'} Threat Intel — URLs:</p>
              {result.threat_intel.urls.map((u, i) => (
                <div key={i} className="pl-4 space-y-0.5">
                  <p className="text-text-primary">{u.url}</p>
                  {u.typosquat_match && (
                    <p className="text-danger">↳ Typosquatting: spoofing {u.typosquat_match}</p>
                  )}
                  {u.domain_age_days != null && (
                    <p className="text-text-muted">↳ Domain age: {u.domain_age_days} days</p>
                  )}
                  {u.safe_browsing && u.safe_browsing !== 'safe' && (
                    <p className="text-danger">↳ Safe Browsing: {u.safe_browsing}</p>
                  )}
                </div>
              ))}
            </>
          )}

          <p className="animate-pulse-soft text-text-muted mt-2">_</p>
        </div>
      </Card>

      {/* Incident Intelligence / Explainability panel */}
      {result.primary_label && (result.text_full || result.text_preview || result.transcript || result.extracted_text) && (
        <ExplainPanel
          text={result.text_full || result.text_preview || result.transcript || result.extracted_text}
          primaryLabel={result.primary_label}
          secondaryLabels={result.secondary_labels || {}}
        />
      )}

      {/* Guidance panel */}
      {result.guidance && (
        <GuidancePanel guidance={result.guidance} />
      )}
    </div>
  );
}

ResultDisplay.propTypes = {
  result: PropTypes.shape({
    label:            PropTypes.string,
    category:         PropTypes.string,
    confidence:       PropTypes.number,
    model:            PropTypes.string,
    explanation:      PropTypes.array,
    transcript:       PropTypes.string,
    risk_score:       PropTypes.number,
    extracted_text:   PropTypes.string,
    similar_reports:  PropTypes.array,
    text_preview:     PropTypes.string,
    timestamp:        PropTypes.string,
    secondary_labels: PropTypes.object,
    guidance:         PropTypes.object,
    threat_intel:     PropTypes.object,
  }),
};
