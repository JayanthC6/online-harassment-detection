import { useState } from 'react';
import PropTypes from 'prop-types';
import Button from '../common/Button';
import { apiClient } from '../../api/client';

export default function PredictionSummary({
  isHarassing,
  category,
  confidence,
  textToSummarize,
}) {
  const [summary, setSummary] = useState(null);
  const [summaryLoading, setSummaryLoading] = useState(false);
  const [summaryError, setSummaryError] = useState(null);

  const handleSummarize = async () => {
    setSummaryLoading(true);
    setSummaryError(null);
    try {
      const data = await apiClient('/summarize', {
        method: 'POST',
        body: JSON.stringify({
          text: textToSummarize || '',
          category: category,
          confidence: confidence,
        }),
      });
      setSummary(data);
    } catch (err) {
      setSummaryError(err.message);
    } finally {
      setSummaryLoading(false);
    }
  };

  if (!isHarassing) return null;

  return (
    <>
      {!summary && (
        <Button
          onClick={handleSummarize}
          disabled={summaryLoading}
          loading={summaryLoading}
          loadingText="Generating summary..."
          variant="ghost"
          className="text-xs w-full justify-center"
        >
          📋 Generate Incident Summary
        </Button>
      )}

      {summaryError && <p className="text-xs text-red-600">{summaryError}</p>}

      {summary && (
        <div className="bg-indigo-50 border border-indigo-200 rounded-xl p-4 space-y-3">
          <p className="text-xs font-semibold text-indigo-700 flex items-center gap-2">
            <span>📋</span> Incident Summary
          </p>
          <div className="space-y-2 text-sm">
            <div>
              <span className="text-xs font-semibold text-gray-500 uppercase">
                Description
              </span>
              <p className="text-gray-700 mt-0.5">
                {summary.incident_description}
              </p>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <span className="text-xs font-semibold text-gray-500 uppercase">
                  Category
                </span>
                <p className="text-gray-700 mt-0.5">{summary.category}</p>
              </div>
              <div>
                <span className="text-xs font-semibold text-gray-500 uppercase">
                  Severity
                </span>
                <p
                  className={`mt-0.5 font-medium ${
                    summary.severity === 'high'
                      ? 'text-red-700'
                      : summary.severity === 'medium'
                      ? 'text-amber-700'
                      : 'text-gray-700'
                  }`}
                >
                  {summary.severity?.toUpperCase()}
                </p>
              </div>
            </div>
            <div>
              <span className="text-xs font-semibold text-gray-500 uppercase">
                Suggested Action
              </span>
              <p className="text-gray-700 mt-0.5">{summary.suggested_action}</p>
            </div>
          </div>
        </div>
      )}
    </>
  );
}

PredictionSummary.propTypes = {
  isHarassing: PropTypes.bool.isRequired,
  category: PropTypes.string.isRequired,
  confidence: PropTypes.number.isRequired,
  textToSummarize: PropTypes.string,
};
