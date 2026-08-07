import PropTypes from 'prop-types';
import { ShieldCheck, ShieldAlert, AlertTriangle } from 'lucide-react';

const getCategoryStyles = (category) => {
  const cat = category.toLowerCase();
  
  if (['hate_speech', 'threat', 'blackmail', 'extortion'].includes(cat)) {
    return { text: category.replace('_', ' '), color: 'text-rose-700 bg-rose-50 border-rose-200' };
  }
  if (['offensive_language', 'scam', 'fraud', 'impersonation'].includes(cat)) {
    return { text: category.replace('_', ' '), color: 'text-amber-700 bg-amber-50 border-amber-200' };
  }
  if (['phishing', 'social_engineering'].includes(cat)) {
    return { text: category.replace('_', ' '), color: 'text-purple-700 bg-purple-50 border-purple-200' };
  }
  
  // Default clean or unknown
  if (cat === 'none' || cat === 'clean') {
    return { text: 'Clean', color: 'text-emerald-700 bg-emerald-50 border-emerald-200' };
  }
  
  return { text: category.replace('_', ' '), color: 'text-slate-700 bg-slate-50 border-slate-200' };
};

export default function RiskBadge({ isHarassing, category, riskScore }) {
  const catInfo = getCategoryStyles(category);

  return (
    <div className="flex flex-wrap items-center gap-3">
      {/* Harassing / Safe badge */}
      <span
        className={`badge text-sm border flex items-center gap-1.5 ${
          isHarassing
            ? 'bg-rose-50 text-rose-700 border-rose-200'
            : 'bg-emerald-50 text-emerald-700 border-emerald-200'
        }`}
      >
        {isHarassing ? <ShieldAlert size={16} /> : <ShieldCheck size={16} />}
        {isHarassing ? 'Incident Detected' : 'Safe'}
      </span>

      {/* Category badge */}
      <span className={`badge text-xs border capitalize ${catInfo.color}`}>
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
          Safety Score: {Math.round(riskScore)}
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
