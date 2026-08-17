import PropTypes from 'prop-types';
import RedactionBar from '../common/RedactionBar';

export default function ConfidenceBar({ confidence, isHarassing }) {
  const pct = Math.round((confidence || 0) * 100);
  const tier = isHarassing ? (pct >= 75 ? 'danger' : 'warning') : 'success';

  return (
    <div className="flex flex-col gap-4 w-full">
      {/* Large number */}
      <div className="flex items-end gap-2">
        <span className="text-4xl font-extrabold text-text-primary tabular-nums font-mono">{pct}</span>
        <span className="text-2xl font-bold text-text-muted mb-0.5">%</span>
      </div>

      {/* Bar */}
      <RedactionBar score={confidence} tier={tier} heightClass="h-2" />
      <p className="text-2xs text-text-muted -mt-1">Model Confidence</p>
    </div>
  );
}

ConfidenceBar.propTypes = {
  confidence:  PropTypes.number.isRequired,
  isHarassing: PropTypes.bool.isRequired,
};
