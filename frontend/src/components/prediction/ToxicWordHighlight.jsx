import PropTypes from 'prop-types';

export default function ToxicWordHighlight({ explanation }) {
  if (!explanation || explanation.length === 0) return null;

  return (
    <div className="bg-violet-50 border border-violet-200 rounded-xl p-4">
      <p className="text-xs font-semibold text-violet-700 mb-3 flex items-center gap-2">
        <span>🔬</span> Word-Level Contributions
        <span className="text-violet-400 font-normal">
          (TF-IDF × LR coefficients)
        </span>
      </p>
      <div className="flex gap-2 flex-wrap">
        {explanation.map((item, i) => (
          <div
            key={i}
            className="bg-violet-100 border border-violet-200 rounded-lg px-3 py-1.5 text-xs"
          >
            <span className="text-violet-800 font-medium">{item.word}</span>
            <span className="text-violet-500 ml-1.5">
              +{item.contribution.toFixed(3)}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

ToxicWordHighlight.propTypes = {
  explanation: PropTypes.arrayOf(
    PropTypes.shape({
      word: PropTypes.string.isRequired,
      contribution: PropTypes.number.isRequired,
    })
  ),
};
