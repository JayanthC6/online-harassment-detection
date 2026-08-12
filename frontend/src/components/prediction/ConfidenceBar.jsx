import PropTypes from 'prop-types';
import RedactionBar from '../common/RedactionBar';

export default function ConfidenceBar({ confidence, isHarassing }) {
  const conf = Math.round((confidence || 0) * 100);

  return (
    <div className="flex items-center gap-3">
      <div className="w-28">
        <RedactionBar score={confidence} tier={isHarassing ? 'red' : 'teal'} />
      </div>
      <span className="text-sm text-slate-400 font-mono tabular-nums">{conf}%</span>
    </div>
  );
}

ConfidenceBar.propTypes = {
  confidence: PropTypes.number.isRequired,
  isHarassing: PropTypes.bool.isRequired,
};

