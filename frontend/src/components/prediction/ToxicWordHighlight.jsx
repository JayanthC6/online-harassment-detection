import PropTypes from 'prop-types';

export default function ToxicWordHighlight({ explanation }) {
  if (!explanation || explanation.length === 0) return null;

  return (
    <div className="flex gap-2 flex-wrap">
      {explanation.map((item, i) => (
        <div
          key={i}
          className="bg-manila border border-[#C8B595] px-3 py-1.5 text-xs flex items-center gap-1.5 rounded-none shadow-sm"
          title={item.reason || ''}
        >
          <span className="text-slate-900 font-bold font-mono">{item.word}</span>
          <span className="text-slate-700 font-mono">
            {item.label ? `(${item.label})` : `+${item.contribution.toFixed(3)}`}
          </span>
        </div>
      ))}
    </div>
  );
}

ToxicWordHighlight.propTypes = {
  explanation: PropTypes.arrayOf(
    PropTypes.shape({
      word: PropTypes.string.isRequired,
      contribution: PropTypes.number.isRequired,
      label: PropTypes.string,
      reason: PropTypes.string,
    })
  ),
};
