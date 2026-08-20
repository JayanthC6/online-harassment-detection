import PropTypes from 'prop-types';

/**
 * Renders a token-level attribution heatmap with signed coloring.
 *
 * Each token in `tokens` has:
 *   - token: string
 *   - score: float in [0, 1]  — absolute magnitude
 *   - sign:  "positive" | "negative" | "neutral"
 *
 * Positive (pushed TOWARD label) → cyan glow
 * Negative (pushed AWAY from label) → danger/orange glow
 * Neutral → no highlight
 */
export default function TokenHeatmap({ tokens, label }) {
  if (!tokens || tokens.length === 0) {
    return (
      <p className="text-sm text-text-muted italic">No tokens returned for this label.</p>
    );
  }

  return (
    <div className="space-y-3">
      {/* Legend */}
      <div className="flex items-center gap-4 text-xs text-text-muted">
        <span className="flex items-center gap-1.5">
          <span
            className="inline-block w-3 h-3 rounded-sm"
            style={{ background: 'rgba(0,242,254,0.55)', border: '1px solid rgba(0,242,254,0.4)' }}
          />
          Pushed <strong className="text-blue">toward</strong> {label}
        </span>
        <span className="flex items-center gap-1.5">
          <span
            className="inline-block w-3 h-3 rounded-sm"
            style={{ background: 'rgba(245,101,101,0.55)', border: '1px solid rgba(245,101,101,0.4)' }}
          />
          Pushed <strong className="text-danger">away</strong>
        </span>
        <span className="flex items-center gap-1.5">
          <span
            className="inline-block w-3 h-3 rounded-sm border border-border"
            style={{ background: 'transparent' }}
          />
          Neutral
        </span>
      </div>

      {/* Token heatmap */}
      <div className="flex flex-wrap gap-1 p-3 bg-surface rounded-lg border border-border leading-relaxed">
        {tokens.map((t, i) => {
          const alpha = Math.min(0.9, t.score * 0.85);  // max opacity 0.9

          let bg = 'transparent';
          let borderColor = 'transparent';
          let textClass = 'text-text-muted';

          if (t.sign === 'positive' && t.score > 0.05) {
            bg = `rgba(0,242,254,${alpha})`;
            borderColor = `rgba(0,242,254,${alpha * 0.6})`;
            textClass = t.score > 0.4 ? 'text-bg font-semibold' : 'text-text-primary';
          } else if (t.sign === 'negative' && t.score > 0.05) {
            bg = `rgba(245,101,101,${alpha})`;
            borderColor = `rgba(245,101,101,${alpha * 0.6})`;
            textClass = t.score > 0.4 ? 'text-bg font-semibold' : 'text-text-primary';
          }

          return (
            <span
              key={i}
              className={`inline-block px-1.5 py-0.5 rounded text-xs font-mono transition-all cursor-default ${textClass}`}
              style={{
                background: bg,
                border: `1px solid ${borderColor}`,
              }}
              title={`${t.sign === 'positive' ? '+' : t.sign === 'negative' ? '-' : ''}${t.score.toFixed(3)} (${t.sign})`}
            >
              {t.token}
            </span>
          );
        })}
      </div>

      <p className="text-2xs text-text-muted font-mono">
        Method: Layer Integrated Gradients · Target: logit[{label}] · Hover tokens for raw score
      </p>
    </div>
  );
}

TokenHeatmap.propTypes = {
  tokens: PropTypes.arrayOf(
    PropTypes.shape({
      token: PropTypes.string.isRequired,
      score: PropTypes.number.isRequired,
      sign: PropTypes.oneOf(['positive', 'negative', 'neutral']).isRequired,
    })
  ).isRequired,
  label: PropTypes.string.isRequired,
};
