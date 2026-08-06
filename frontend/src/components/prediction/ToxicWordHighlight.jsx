import PropTypes from 'prop-types';

export default function ToxicWordHighlight({ explanation }) {
  if (!explanation || explanation.length === 0) return null;

  return (
    <div className="flex gap-2 flex-wrap">
      {explanation.map((item, i) => (
        <div
          key={i}
          className="bg-indigo-50 border border-indigo-100 rounded-lg px-3 py-1.5 text-xs flex items-center gap-1.5"
          title={item.reason || ''}
        >
          <span className="text-indigo-900 font-medium">{item.word}</span>
          <span className="text-indigo-400">
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
