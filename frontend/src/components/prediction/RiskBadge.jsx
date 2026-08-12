import PropTypes from 'prop-types';
import { ShieldCheck, ShieldAlert, AlertTriangle } from 'lucide-react';

const getCategoryStyles = (category) => {
  const cat = category.toLowerCase();
  
  if (['hate_speech', 'threat', 'blackmail', 'extortion'].includes(cat)) {
    return { text: category.replace('_', ' '), color: 'text-redaction-red border-redaction-red' };
  }
  if (['offensive_language', 'scam', 'fraud', 'impersonation'].includes(cat)) {
    return { text: category.replace('_', ' '), color: 'text-alert-amber border-alert-amber' };
  }
  if (['phishing', 'social_engineering'].includes(cat)) {
    return { text: category.replace('_', ' '), color: 'text-redaction-red border-redaction-red' }; // Merged purple to red since only 3 signal colors allowed
  }
  
  // Default clean or unknown
  if (cat === 'none' || cat === 'clean') {
    return { text: 'Clean', color: 'text-verified-teal border-verified-teal' };
  }
  
  return { text: category.replace('_', ' '), color: 'text-off-white border-off-white' };
};

export default function RiskBadge({ isHarassing, category, riskScore }) {
  const catInfo = getCategoryStyles(category);

  return (
    <div className="flex flex-wrap items-center gap-3">
      {/* Harassing / Safe badge */}
      <span
        className={`badge text-sm flex items-center gap-1.5 ${
          isHarassing
            ? 'text-redaction-red border-redaction-red'
            : 'text-verified-teal border-verified-teal'
        }`}
      >
        {isHarassing ? <ShieldAlert size={16} /> : <ShieldCheck size={16} />}
        {isHarassing ? 'Incident Detected' : 'Safe'}
      </span>

      {/* Category badge */}
      <span className={`badge text-xs capitalize ${catInfo.color}`}>
        {catInfo.text}
      </span>

      {/* Risk score badge */}
      {riskScore != null && (
        <span
          className={`badge text-xs flex items-center gap-1.5 ${
            riskScore >= 70
              ? 'text-redaction-red border-redaction-red'
              : riskScore >= 40
              ? 'text-alert-amber border-alert-amber'
              : 'text-verified-teal border-verified-teal'
          }`}
        >
          {riskScore >= 70 && <AlertTriangle size={14} />}
          Score: {Math.round(riskScore)}
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

