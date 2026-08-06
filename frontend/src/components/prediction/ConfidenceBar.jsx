import PropTypes from 'prop-types';

export default function ConfidenceBar({ confidence, isHarassing }) {
  const conf = Math.round((confidence || 0) * 100);

  return (
    <div className="flex items-center gap-2">
      <div className="h-2 w-28 bg-slate-100 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-700 ${
            isHarassing ? 'bg-rose-500' : 'bg-emerald-500'
          }`}
          style={{ width: `${conf}%` }}
        />
      </div>
      <span className="text-sm text-slate-500 font-mono tabular-nums">{conf}%</span>
    </div>
  );
}

ConfidenceBar.propTypes = {
  confidence: PropTypes.number.isRequired,
  isHarassing: PropTypes.bool.isRequired,
};
