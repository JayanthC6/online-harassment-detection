import PropTypes from 'prop-types';

export default function RedactionBar({ score, tier = 'teal', heightClass = 'h-4', className = '' }) {
  const percentage = Math.min(Math.max(score * 100, 0), 100);
  
  const getTierColor = () => {
    switch(tier) {
      case 'red': return 'bg-redaction-red';
      case 'amber': return 'bg-alert-amber';
      case 'teal': return 'bg-verified-teal';
      default: return 'bg-verified-teal';
    }
  };

  return (
    <div className={`w-full flex hatch-pattern overflow-hidden border border-slate-700 ${heightClass} ${className}`}>
      <div 
        className={`h-full ${getTierColor()}`}
        style={{ width: `${percentage}%` }}
      />
    </div>
  );
}

RedactionBar.propTypes = {
  score: PropTypes.number.isRequired,
  tier: PropTypes.oneOf(['red', 'amber', 'teal']),
  heightClass: PropTypes.string,
  className: PropTypes.string,
};
