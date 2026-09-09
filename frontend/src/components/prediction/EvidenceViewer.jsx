import PropTypes from 'prop-types';
import Card from '../common/Card';

export default function EvidenceViewer({ result }) {
  if (!result) return null;

  return (
    <Card className="terminal-block mt-4">
      <div className="flex items-center gap-2 px-1 pb-3 border-b border-border mb-4">
        <div className="flex gap-1.5">
          <div className="w-2.5 h-2.5 rounded-full bg-danger opacity-60" />
          <div className="w-2.5 h-2.5 rounded-full bg-warning opacity-40" />
          <div className="w-2.5 h-2.5 rounded-full bg-success opacity-40" />
        </div>
        <span className="text-2xs text-text-muted font-mono ml-2">evidence_viewer.log</span>
      </div>

      <div className="font-mono text-xs leading-relaxed text-text-muted space-y-2 max-h-64 overflow-y-auto">
        <p className="text-blue">{'>'} Forensic evidence extraction complete.</p>

        {result.messages && result.messages.length > 0 ? (
          <>
            <p className="text-text-secondary mt-3">{'>'} Conversation Log:</p>
            <div className="pl-4 border-l-2 border-blue ml-2 space-y-3 mt-2">
              {result.messages.map((msg, idx) => (
                <div key={idx} className="bg-surface/50 p-2 rounded text-text-primary">
                  <div className="flex justify-between items-center mb-1 text-2xs text-text-muted">
                    <span className="font-bold">{msg.sender || "Unknown Sender"}</span>
                    <span>{msg.timestamp || ""}</span>
                  </div>
                  <div className="whitespace-pre-wrap">{msg.text}</div>
                </div>
              ))}
            </div>
          </>
        ) : (
          <>
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

        {result.threat_intel?.emails?.length > 0 && (
          <>
            <p className="text-warning mt-3">{'>'} Threat Intel — Emails:</p>
            {result.threat_intel.emails.map((e, i) => (
              <div key={i} className="pl-4 space-y-0.5">
                <p className="text-text-primary">{e.email}</p>
                {e.breach_count != null && (
                  <p className={e.breach_count > 0 ? "text-danger" : "text-success"}>
                    ↳ Known Breaches (HIBP): {e.breach_count}
                  </p>
                )}
              </div>
            ))}
          </>
        )}

        {result.pii_categories?.length > 0 && (
          <>
            <p className="text-danger mt-3">{'>'} PII Detected & Masked:</p>
            <div className="pl-4 text-text-primary">
              {result.pii_categories.join(', ')}
            </div>
          </>
        )}

        <p className="animate-pulse-soft text-text-muted mt-2">_</p>
      </div>
    </Card>
  );
}

EvidenceViewer.propTypes = {
  result: PropTypes.object.isRequired,
};
