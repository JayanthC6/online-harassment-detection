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

export default function RiskBadge({ safetyStatus, severityTier, category, threatScore }) {
  const score = Math.round(threatScore ?? 0);
  const catLabel = (category || 'none').replace(/_/g, ' ').replace(/\//g, ' / ');

  return (
    <div className="flex flex-col gap-4 w-full">
      {/* Status pill */}
      <div className="flex items-center gap-2">
        {(safetyStatus || severityTier) !== 'Safe' ? (
          <span className="badge badge-danger text-sm">
            <ShieldAlert size={14} />
            {safetyStatus || 'Threat Detected'}
          </span>
        ) : (
          <span className="badge badge-success text-sm">
            <ShieldCheck size={14} />
            No Threat Detected
          </span>
        )}
        <span className={`badge ${getCategoryBadgeClass(category)} capitalize text-xs`}>
          {catLabel}
        </span>
      </div>

      {/* Large score display */}
      {threatScore != null && (
        <div className="flex items-end gap-3">
          <span 
            className="text-5xl font-extrabold tabular-nums font-mono tracking-tight"
            style={{ 
              color: score >= 80 ? '#F43F5E' : score >= 55 ? '#F97316' : score >= 30 ? '#F59E0B' : '#10B981',
              textShadow: `0 0 20px ${score >= 80 ? 'rgba(244,63,94,0.4)' : score >= 55 ? 'rgba(249,115,22,0.4)' : score >= 30 ? 'rgba(245,158,11,0.4)' : 'rgba(16,185,129,0.4)'}` 
            }}
          >
            {score}
          </span>
          <div className="mb-2">
            <span className={`score-pill ${getScoreClass(score)}`}>
              {severityTier || (score >= 80 ? 'Critical' : score >= 55 ? 'High' : score >= 30 ? 'Medium' : 'Low')}
            </span>
          </div>
        </div>
      )}

      {/* Score bar */}
      {threatScore != null && (
        <div className="space-y-2">
          <div className="progress-bar h-1.5 bg-black/50 overflow-hidden shadow-inner">
            <div
              className={`progress-bar-fill h-full rounded-full transition-all duration-1000 ease-out ${
                score >= 80 ? 'bg-critical shadow-[0_0_10px_rgba(244,63,94,0.8)]' : score >= 55 ? 'bg-danger shadow-[0_0_10px_rgba(249,115,22,0.8)]' : score >= 30 ? 'bg-warning shadow-[0_0_10px_rgba(245,158,11,0.8)]' : 'bg-success shadow-[0_0_10px_rgba(16,185,129,0.8)]'
              }`}
              style={{ width: `${score}%` }}
            />
          </div>
          <p className="text-2xs text-text-muted">Threat Score / 100</p>
        </div>
      )}
    </div>
  );
}

RiskBadge.propTypes = {
  safetyStatus: PropTypes.string,
  severityTier: PropTypes.string,
  category:     PropTypes.string.isRequired,
  threatScore:  PropTypes.number,
};
