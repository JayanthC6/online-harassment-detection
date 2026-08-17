import PropTypes from 'prop-types';

/**
 * Clean horizontal progress bar replacing the "redaction bar" hatch pattern.
 * tier: 'danger' | 'warning' | 'success' | 'blue'
 */
export default function RedactionBar({ score, tier = 'blue', heightClass = 'h-1.5', className = '' }) {
  const percentage = Math.min(Math.max(score * 100, 0), 100);

  const colors = {
    danger:  'bg-danger',
    red:     'bg-danger',
    warning: 'bg-warning',
    amber:   'bg-warning',
    success: 'bg-success',
    teal:    'bg-success',
    blue:    'bg-blue',
  };
  const fill = colors[tier] || 'bg-blue';

  return (
    <div className={`progress-bar ${heightClass} ${className}`}>
      <div className={`progress-bar-fill ${fill}`} style={{ width: `${percentage}%` }} />
    </div>
  );
}

RedactionBar.propTypes = {
  score:       PropTypes.number.isRequired,
  tier:        PropTypes.string,
  heightClass: PropTypes.string,
  className:   PropTypes.string,
};
