import PropTypes from 'prop-types';
import { ShieldCheck, ShieldAlert, AlertTriangle } from 'lucide-react';

const CATEGORY_LABELS = {
  hate_speech: { text: 'Hate Speech', color: 'text-rose-700 bg-rose-50 border-rose-200' },
  offensive_language: { text: 'Offensive Language', color: 'text-amber-700 bg-amber-50 border-amber-200' },
  none: { text: 'Clean', color: 'text-emerald-700 bg-emerald-50 border-emerald-200' },
};

export default function RiskBadge({ isHarassing, category, riskScore }) {
  const catInfo = CATEGORY_LABELS[category] || CATEGORY_LABELS.none;

  return (
    <div className="flex items-center gap-3">
      {/* Harassing / Safe badge */}
      <span
        className={`badge text-sm border flex items-center gap-1.5 ${
          isHarassing
            ? 'bg-rose-50 text-rose-700 border-rose-200'
            : 'bg-emerald-50 text-emerald-700 border-emerald-200'
        }`}
      >
        {isHarassing ? <ShieldAlert size={16} /> : <ShieldCheck size={16} />}
        {isHarassing ? 'Harassing' : 'Safe'}
      </span>

      {/* Category badge */}
      <span className={`badge text-xs border ${catInfo.color}`}>
        {catInfo.text}
      </span>

      {/* Risk score badge */}
      {riskScore != null && (
        <span
          className={`badge text-xs border flex items-center gap-1.5 ${
            riskScore >= 70
              ? 'bg-rose-50 text-rose-700 border-rose-200'
              : riskScore >= 40
              ? 'bg-amber-50 text-amber-700 border-amber-200'
              : 'bg-slate-50 text-slate-600 border-slate-200'
          }`}
        >
          {riskScore >= 70 && <AlertTriangle size={14} />}
          Risk: {Math.round(riskScore)}
        </span>
      )}
    </div>
  );
}

RiskBadge.propTypes = {
  isHarassing: PropTypes.bool.isRequired,
  category: PropTypes.string.isRequired,
  riskScore: PropTypes.number,
};
