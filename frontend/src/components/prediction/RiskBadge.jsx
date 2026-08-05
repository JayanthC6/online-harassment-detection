import PropTypes from 'prop-types';

const CATEGORY_LABELS = {
  hate_speech: { text: 'Hate Speech', color: 'text-red-700 bg-red-50 border-red-200' },
  offensive_language: { text: 'Offensive Language', color: 'text-amber-700 bg-amber-50 border-amber-200' },
  none: { text: 'Clean', color: 'text-emerald-700 bg-emerald-50 border-emerald-200' },
};

export default function RiskBadge({ isHarassing, category, riskScore }) {
  const catInfo = CATEGORY_LABELS[category] || CATEGORY_LABELS.none;

  return (
    <div className="flex items-center gap-3">
      {/* Harassing / Safe badge */}
      <span
        className={`badge text-sm border ${
          isHarassing
            ? 'bg-red-50 text-red-700 border-red-200'
            : 'bg-emerald-50 text-emerald-700 border-emerald-200'
        }`}
      >
        {isHarassing ? '🚨 Harassing' : '✅ Safe'}
      </span>

      {/* Category badge */}
      <span className={`badge text-xs border ${catInfo.color}`}>
        {catInfo.text}
      </span>

      {/* Risk score badge */}
      {riskScore != null && (
        <span
          className={`badge text-xs border ${
            riskScore >= 70
              ? 'bg-red-50 text-red-700 border-red-200'
              : riskScore >= 40
              ? 'bg-amber-50 text-amber-700 border-amber-200'
              : 'bg-gray-50 text-gray-600 border-gray-200'
          }`}
        >
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
