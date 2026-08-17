import PropTypes from 'prop-types';
import { ShieldCheck, ShieldAlert, AlertTriangle, ShieldX } from 'lucide-react';

function getScoreClass(score) {
  if (score >= 80) return 'score-critical';
  if (score >= 55) return 'score-high';
  if (score >= 30) return 'score-medium';
  return 'score-low';
}

function getCategoryBadgeClass(category) {
  const cat = (category || '').toLowerCase();
  if (['hate_speech', 'threat', 'blackmail', 'extortion'].includes(cat)) return 'badge-danger';
  if (['scam', 'fraud', 'impersonation', 'phishing', 'social_engineering'].includes(cat)) return 'badge-critical';
  if (['offensive_language', 'cyberbullying_harassment', 'cyberbullying'].includes(cat)) return 'badge-warning';
  if (cat === 'none' || cat === 'clean') return 'badge-success';
  return 'badge-muted';
}

export default function RiskBadge({ isHarassing, category, riskScore }) {
  const score = Math.round(riskScore ?? 0);
  const catLabel = (category || 'none').replace(/_/g, ' ').replace(/\//g, ' / ');

  return (
    <div className="flex flex-col gap-4 w-full">
      {/* Status pill */}
      <div className="flex items-center gap-2">
        {isHarassing ? (
          <span className="badge badge-danger text-sm">
            <ShieldAlert size={14} />
            Threat Detected
          </span>
        ) : (
          <span className="badge badge-success text-sm">
            <ShieldCheck size={14} />
            Safe
          </span>
        )}
        <span className={`badge ${getCategoryBadgeClass(category)} capitalize text-xs`}>
          {catLabel}
        </span>
      </div>

      {/* Large score display */}
      {riskScore != null && (
        <div className="flex items-end gap-3">
          <span className="text-4xl font-extrabold text-text-primary tabular-nums font-mono">
            {score}
          </span>
          <div className="mb-1">
            <span className={`score-pill ${getScoreClass(score)}`}>
              {score >= 80 ? 'Critical' : score >= 55 ? 'High' : score >= 30 ? 'Medium' : 'Low'}
            </span>
          </div>
        </div>
      )}

      {/* Score bar */}
      {riskScore != null && (
        <div className="space-y-1.5">
          <div className="progress-bar h-2">
            <div
              className={`progress-bar-fill ${
                score >= 80 ? 'bg-danger' : score >= 55 ? 'bg-critical' : score >= 30 ? 'bg-warning' : 'bg-success'
              }`}
              style={{ width: `${score}%` }}
            />
          </div>
          <p className="text-2xs text-text-muted">Risk Score / 100</p>
        </div>
      )}
    </div>
  );
}

RiskBadge.propTypes = {
  isHarassing: PropTypes.bool.isRequired,
  category:    PropTypes.string.isRequired,
  riskScore:   PropTypes.number,
};
