import PropTypes from 'prop-types';
import { ShieldAlert, Info, AlertTriangle, Key, Mail, Clock, Link, Briefcase } from 'lucide-react';
import Card from '../common/Card';

const SE_LABELS = {
  credential_request: "Credential request",
  otp_code_request: "OTP request",
  account_verification_pressure: "Account verification pressure",
  payment_request: "Payment request",
  gift_card_request: "Gift card request",
  crypto_payment_request: "Cryptocurrency payment request",
  ransom_demand: "Ransom demand",
  blackmail_indicator: "Blackmail indicator",
  investment_scam_indicator: "Investment scam indicator"
};

export default function ThreatIntelligenceCard({ result, isConversation = false }) {
  if (!result) return null;

  const threatIntel = result.threat_intel || {};
  const threatSignals = threatIntel.threat_signals || {};
  const threatSummary = result.threat_signal_summary || {};
  const emails = threatIntel.emails || [];
  const jobScam = threatIntel.job_scam_signals || {};
  
  const hasBreachedEmail = emails.some(e => e.breach_count > 0);
  const detectedSignals = threatSummary.detected === true;
  const hasJobScamSignals = jobScam.detected === true && jobScam.recruitment_context === true;

  if (!detectedSignals && !hasBreachedEmail && !hasJobScamSignals) {
    return null;
  }

  const title = isConversation 
    ? "Threat Intelligence Signals Detected Across Conversation" 
    : "Threat Intelligence & Safety Signals";

  return (
    <Card className="border border-purple/30 bg-[#060913]/90 shadow-[0_0_20px_rgba(168,85,247,0.1)] mt-4 relative overflow-hidden">
      <div className="absolute top-0 left-0 w-1 h-full bg-gradient-to-b from-purple to-blue shadow-[0_0_10px_rgba(168,85,247,0.5)]"></div>
      <div className="flex items-center gap-2 mb-4 pb-3 border-b border-border/50">
        <ShieldAlert size={18} className="text-purple" />
        <h2 className="section-title mb-0 text-purple font-bold text-sm tracking-widest drop-shadow-[0_0_5px_rgba(168,85,247,0.4)]">
          {title}
        </h2>
      </div>

      <div className="space-y-4">
        {/* Email / Breach Intelligence */}
        {hasBreachedEmail && (
          <div className="flex items-start gap-3 p-3 bg-black/40 rounded border border-border/30 border-l-[3px] border-l-purple shadow-[inset_0_0_10px_rgba(0,0,0,0.5)]">
            <Mail size={16} className="text-warning mt-0.5 shrink-0" />
            <div>
              <p className="text-sm font-semibold text-text-primary">Data Breach Intelligence</p>
              <p className="text-sm text-text-secondary mt-1">
                An email address in the submitted content appears in known data-breach records.
              </p>
            </div>
          </div>
        )}

        {/* Social Engineering */}
        {threatSignals.social_engineering?.detected && (
          <div className="flex items-start gap-3 p-3 bg-black/40 rounded border border-border/30 border-l-[3px] border-l-blue shadow-[inset_0_0_10px_rgba(0,0,0,0.5)]">
            <Key size={16} className="text-danger mt-0.5 shrink-0" />
            <div className="flex-1">
              <p className="text-sm font-semibold text-text-primary">Social Engineering Indicators</p>
              <ul className="mt-2 space-y-1">
                {(threatSignals.social_engineering.indicators || []).map((indicator, idx) => (
                  <li key={idx} className="flex items-center gap-2 text-sm text-text-secondary">
                    <span className="w-1.5 h-1.5 rounded-full bg-danger/70"></span>
                    {SE_LABELS[indicator] || indicator.replace(/_/g, ' ')}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        )}

        {/* Urgency */}
        {threatSignals.urgency?.detected && (
          <div className="flex items-start gap-3 p-3 bg-black/40 rounded border border-border/30 border-l-[3px] border-l-warning shadow-[inset_0_0_10px_rgba(0,0,0,0.5)]">
            <Clock size={16} className="text-warning mt-0.5 shrink-0" />
            <div>
              <p className="text-sm font-semibold text-text-primary">Urgency & Pressure</p>
              <p className="text-sm text-text-secondary mt-1">
                {threatSignals.urgency.count > 1 
                  ? "Multiple urgency indicators detected." 
                  : "An urgency indicator was detected."}
              </p>
            </div>
          </div>
        )}

        {/* Brand Impersonation */}
        {threatSignals.brand_impersonation?.detected && (
          <div className="flex items-start gap-3 p-3 bg-black/40 rounded border border-border/30 border-l-[3px] border-l-purple shadow-[inset_0_0_10px_rgba(0,0,0,0.5)]">
            <Briefcase size={16} className="text-warning mt-0.5 shrink-0" />
            <div>
              <p className="text-sm font-semibold text-text-primary">Authority Impersonation</p>
              <div className="mt-1 space-y-1">
                {(threatSignals.brand_impersonation.brands || []).map((brand, idx) => (
                  <p key={idx} className="text-sm text-text-secondary">
                    Potential brand impersonation indicator involving <span className="font-semibold text-text-primary">{brand}</span>
                  </p>
                ))}
                {(!threatSignals.brand_impersonation.brands || threatSignals.brand_impersonation.brands.length === 0) && (
                  <p className="text-sm text-text-secondary">Potential brand impersonation indicator</p>
                )}
              </div>
            </div>
          </div>
        )}

        {/* URL Intelligence (Shorteners, IP-based, Dangerous Schemes) */}
        {(threatSignals.url_shorteners?.length > 0 || threatSignals.ip_based_urls?.length > 0 || threatSignals.dangerous_schemes?.length > 0) && (
          <div className="flex items-start gap-3 p-3 bg-black/40 rounded border border-border/30 border-l-[3px] border-l-danger shadow-[inset_0_0_10px_rgba(0,0,0,0.5)]">
            <Link size={16} className="text-danger mt-0.5 shrink-0" />
            <div className="flex-1">
              <p className="text-sm font-semibold text-text-primary">Advanced URL Intelligence</p>
              <div className="mt-2 space-y-2">
                {threatSignals.url_shorteners?.length > 0 && (
                  <p className="text-sm text-text-secondary flex items-start gap-2">
                    <span className="w-1.5 h-1.5 rounded-full bg-danger/70 mt-1.5 shrink-0"></span>
                    A URL shortener was detected; the final destination is not visible.
                  </p>
                )}
                {threatSignals.ip_based_urls?.length > 0 && (
                  <p className="text-sm text-text-secondary flex items-start gap-2">
                    <span className="w-1.5 h-1.5 rounded-full bg-danger/70 mt-1.5 shrink-0"></span>
                    An IP-based URL was detected instead of a conventional domain name.
                  </p>
                )}
                {threatSignals.dangerous_schemes?.map((schemeObj, idx) => (
                  <p key={idx} className="text-sm text-text-secondary flex items-start gap-2">
                    <span className="w-1.5 h-1.5 rounded-full bg-danger/70 mt-1.5 shrink-0"></span>
                    <span>A potentially dangerous URL scheme was detected: <span className="font-mono text-xs bg-background px-1 border border-border rounded">{schemeObj.scheme}</span></span>
                  </p>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Job Scam Intelligence */}
        {hasJobScamSignals && (
          <div className="flex items-start gap-3 p-3 bg-black/40 rounded border border-border/30 border-l-[3px] border-l-purple shadow-[inset_0_0_10px_rgba(0,0,0,0.5)]">
            <Briefcase size={16} className="text-warning mt-0.5 shrink-0" />
            <div className="flex-1">
              <div className="flex items-center justify-between">
                <p className="text-sm font-semibold text-text-primary">Job / Recruitment Intelligence</p>
                <span className="text-xs px-2 py-0.5 rounded border border-border/50 bg-surface text-text-secondary font-mono">
                  Context: DETECTED
                </span>
              </div>
              
              {jobScam.indicators && jobScam.indicators.length > 0 && (
                <div className="mt-3">
                  <p className="text-xs text-text-muted mb-1 uppercase tracking-wider font-semibold">Indicators:</p>
                  <ul className="space-y-1">
                    {jobScam.indicators.map((indicator, idx) => {
                      let text = indicator.replace(/_/g, ' ');
                      text = text.charAt(0).toUpperCase() + text.slice(1);
                      return (
                        <li key={idx} className="flex items-center gap-2 text-sm text-text-secondary">
                          <span className="w-1.5 h-1.5 rounded-full bg-danger/70"></span>
                          {text}
                        </li>
                      );
                    })}
                  </ul>
                </div>
              )}

              <div className="mt-3 p-2 bg-surface/50 border border-border/30 rounded">
                <p className="text-xs text-text-muted mb-1 uppercase tracking-wider font-semibold">Assessment:</p>
                <p className="text-sm text-text-primary">{jobScam.assessment}</p>
              </div>

              {jobScam.detected_suspicious && (
                <div className="mt-2 p-2 bg-warning/10 border border-warning/20 rounded">
                  <p className="text-xs text-warning/80 mb-1 uppercase tracking-wider font-semibold">Recommendation:</p>
                  <p className="text-sm text-text-secondary">
                    Verify the employer through an independently obtained official contact channel before sharing personal information or making payments.
                  </p>
                </div>
              )}
            </div>
          </div>
        )}

      </div>
    </Card>
  );
}

ThreatIntelligenceCard.propTypes = {
  result: PropTypes.shape({
    threat_signals: PropTypes.object,
    threat_signal_summary: PropTypes.object,
    threat_intel: PropTypes.object,
  }),
  isConversation: PropTypes.bool
};
