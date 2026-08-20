import React, { useState, useEffect } from 'react';
import PropTypes from 'prop-types';
import { Cpu, Loader2, ChevronDown, ChevronUp, Zap, AlertTriangle, Info } from 'lucide-react';
import TokenHeatmap from './TokenHeatmap';
import Card from '../common/Card';

// Labels the neural model was trained on (must match backend NEURAL_LABELS)
const NEURAL_LABELS = new Set([
  'Hate Speech',
  'Cyberbullying / Harassment',
  'Threat',
  'Toxicity / Offensive Language',
  'Profanity',
  'Clean',
]);

function isNeural(label) {
  return NEURAL_LABELS.has(label);
}

/**
 * Fetches and renders /predict/explain for a single label.
 * Auto-fetches on mount for the primary label; secondary labels are on-demand.
 */
function LabelExplanation({ text, label, autoFetch = false }) {
  const [state, setState] = useState({ status: 'idle', data: null, error: null });
  const [open, setOpen] = useState(autoFetch);

  const fetch_ = async () => {
    if (state.status === 'loading' || state.status === 'done') return;
    setState({ status: 'loading', data: null, error: null });
    try {
      const res = await fetch('/predict/explain', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text, label }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || 'Server error');
      setState({ status: 'done', data, error: null });
    } catch (e) {
      setState({ status: 'error', data: null, error: e.message });
    }
  };

  // Auto-fetch for primary label when panel opens
  useEffect(() => {
    if (autoFetch) fetch_();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const neural = isNeural(label);
  const statusBadge = neural
    ? <span className="text-2xs text-blue font-mono px-1.5 py-0.5 border border-blue/30 rounded bg-blue-glow">Neural · LIG</span>
    : <span className="text-2xs text-warning font-mono px-1.5 py-0.5 border border-warning/30 rounded bg-surface-3">Rule Engine</span>;

  const handleToggle = () => {
    if (!open) {
      fetch_();
    }
    setOpen(v => !v);
  };

  return (
    <div className="border border-border rounded-lg overflow-hidden">
      {/* Header row */}
      <button
        onClick={handleToggle}
        className="w-full flex items-center justify-between px-3 py-2.5 bg-surface hover:bg-surface-2 transition-colors text-left"
      >
        <div className="flex items-center gap-2">
          {neural ? <Cpu size={13} className="text-blue shrink-0" /> : <Zap size={13} className="text-warning shrink-0" />}
          <span className="text-sm font-medium text-text-primary">{label}</span>
          {statusBadge}
        </div>
        <div className="flex items-center gap-2">
          {state.status === 'loading' && <Loader2 size={13} className="text-blue animate-spin" />}
          {open ? <ChevronUp size={14} className="text-text-muted" /> : <ChevronDown size={14} className="text-text-muted" />}
        </div>
      </button>

      {/* Body */}
      {open && (
        <div className="p-3 border-t border-border bg-surface-2 space-y-3">
          {state.status === 'idle' && (
            <p className="text-sm text-text-muted italic">Loading…</p>
          )}

          {state.status === 'loading' && (
            <div className="flex items-center gap-2 text-sm text-text-muted">
              <Loader2 size={14} className="animate-spin text-blue" />
              Computing Layer Integrated Gradients — this may take 10–20 seconds…
            </div>
          )}

          {state.status === 'error' && (
            <div className="flex items-start gap-2 text-sm text-danger">
              <AlertTriangle size={14} className="shrink-0 mt-0.5" />
              {state.error}
            </div>
          )}

          {state.status === 'done' && state.data && (
            <>
              {state.data.is_neural ? (
                /* ── Neural: show LIG heatmap ── */
                <TokenHeatmap tokens={state.data.tokens} label={label} />
              ) : (
                /* ── Symbolic: show rule evidence ── */
                <div className="space-y-2">
                  <div className="flex items-start gap-2 text-xs text-text-muted p-2 bg-surface border border-border/50 rounded">
                    <Info size={13} className="shrink-0 mt-0.5 text-warning" />
                    <span>{state.data.reason}</span>
                  </div>
                  {state.data.rule_evidence && state.data.rule_evidence.length > 0 ? (
                    <div>
                      <p className="text-2xs text-text-muted uppercase tracking-wider mb-2 font-semibold">Rule Evidence</p>
                      <div className="flex flex-wrap gap-1.5">
                        {state.data.rule_evidence.map((hit, i) => (
                          <span
                            key={i}
                            className="inline-flex items-center gap-1 px-2 py-1 rounded text-xs font-mono bg-surface border border-warning/30 text-warning"
                            title={hit.reason || ''}
                          >
                            {hit.word}
                            <span className="text-text-muted text-2xs">→ {hit.label}</span>
                          </span>
                        ))}
                      </div>
                    </div>
                  ) : (
                    <p className="text-xs text-text-muted italic">
                      No specific rule keywords matched — this label was inferred from context signals.
                    </p>
                  )}
                </div>
              )}
            </>
          )}
        </div>
      )}
    </div>
  );
}

/**
 * ExplainPanel — mounts inside ResultDisplay.
 *
 * Auto-fetches the primary label attribution (if neural).
 * Secondary labels each get an expand-to-explain accordion.
 * Symbolic-only categories show rule evidence instead of IG.
 *
 * Props:
 *   text          (str) — the original analyzed message
 *   primaryLabel  (str) — result.primary_label
 *   secondaryLabels (object) — result.secondary_labels {label: conf}
 */
export default function ExplainPanel({ text, primaryLabel, secondaryLabels }) {
  if (!text || !primaryLabel) return null;

  const secondaryEntries = Object.entries(secondaryLabels || {});

  return (
    <Card>
      <div className="flex items-center gap-2 mb-4">
        <Cpu size={14} className="text-blue" />
        <p className="section-title mb-0">Incident Intelligence</p>
        <span className="text-2xs text-text-muted font-mono ml-auto">
          {isNeural(primaryLabel) ? 'Captum Layer IG · DistilBERT' : 'Rule Engine'}
        </span>
      </div>

      <div className="space-y-2">
        {/* Primary label — auto-fetches immediately */}
        <div>
          <p className="text-2xs text-text-muted uppercase tracking-wider mb-1.5 font-semibold">Primary Label</p>
          <LabelExplanation
            key={`primary-${primaryLabel}-${text}`}
            text={text}
            label={primaryLabel}
            autoFetch={true}
          />
        </div>

        {/* Secondary labels — expand on demand */}
        {secondaryEntries.length > 0 && (
          <div className="pt-2">
            <p className="text-2xs text-text-muted uppercase tracking-wider mb-1.5 font-semibold">
              Secondary Labels — click to explain
            </p>
            <div className="space-y-1.5">
              {secondaryEntries.map(([label]) => (
                <LabelExplanation
                  key={`sec-${label}-${text}`}
                  text={text}
                  label={label}
                  autoFetch={false}
                />
              ))}
            </div>
          </div>
        )}
      </div>
    </Card>
  );
}

ExplainPanel.propTypes = {
  text: PropTypes.string.isRequired,
  primaryLabel: PropTypes.string.isRequired,
  secondaryLabels: PropTypes.object,
};

ExplainPanel.defaultProps = {
  secondaryLabels: {},
};
