import PropTypes from 'prop-types';
import Card from '../common/Card';
import EmptyState from '../common/EmptyState';

const CATEGORY_LABELS = {
  hate_speech: 'Hate Speech',
  offensive_language: 'Offensive Language',
  none: 'Clean',
};

export default function RecentFlagsTable({ recent }) {
  return (
    <Card className="p-5">
      <p className="section-title">
        <span className="w-1.5 h-1.5 bg-red-500 rounded-full" />
        Recently Flagged (sorted by risk)
      </p>

      {recent.length === 0 ? (
        <EmptyState
          icon="📭"
          title="Nothing flagged yet."
          subtitle="Switch to the Analyze tab and submit some text."
        />
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-[11px] text-gray-500 uppercase tracking-wider">
                <th className="text-left py-2 pr-3 font-medium">Preview</th>
                <th className="text-left py-2 pr-3 font-medium">Category</th>
                <th className="text-center py-2 pr-3 font-medium">Risk</th>
                <th className="text-right py-2 font-medium">Confidence</th>
              </tr>
            </thead>
            <tbody>
              {recent.map((r, i) => (
                <tr key={i} className="border-t border-gray-100 hover:bg-gray-50 transition-colors">
                  <td className="py-2.5 pr-3 text-gray-700 truncate max-w-[220px]">
                    {r.text_preview}
                    {r.cluster_id && (
                      <span className="ml-2 inline-flex items-center text-[10px] text-amber-700 bg-amber-50 border border-amber-200 rounded-full px-1.5 py-0.5">
                        🔗 Similar
                      </span>
                    )}
                  </td>
                  <td className="py-2.5 pr-3">
                    <span
                      className={`badge text-[11px] border ${
                        r.category === 'hate_speech'
                          ? 'text-red-700 bg-red-50 border-red-200'
                          : r.category === 'offensive_language'
                          ? 'text-amber-700 bg-amber-50 border-amber-200'
                          : 'text-gray-500 bg-gray-50 border-gray-200'
                      }`}
                    >
                      {CATEGORY_LABELS[r.category] || r.category}
                    </span>
                  </td>
                  <td className="py-2.5 pr-3 text-center">
                    {r.risk_score != null && (
                      <span
                        className={`badge text-[11px] border ${
                          r.risk_score >= 70
                            ? 'bg-red-50 text-red-700 border-red-200'
                            : r.risk_score >= 40
                            ? 'bg-amber-50 text-amber-700 border-amber-200'
                            : 'bg-gray-50 text-gray-500 border-gray-200'
                        }`}
                      >
                        {Math.round(r.risk_score)}
                      </span>
                    )}
                  </td>
                  <td className="py-2.5 text-right text-gray-500 font-mono text-xs">
                    {Math.round(r.confidence * 100)}%
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </Card>
  );
}

RecentFlagsTable.propTypes = {
  recent: PropTypes.arrayOf(
    PropTypes.shape({
      text_preview: PropTypes.string.isRequired,
      cluster_id: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
      category: PropTypes.string.isRequired,
      risk_score: PropTypes.number,
      confidence: PropTypes.number.isRequired,
    })
  ).isRequired,
};
