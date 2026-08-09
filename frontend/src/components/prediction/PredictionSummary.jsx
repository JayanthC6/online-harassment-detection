import { useState } from 'react';
import PropTypes from 'prop-types';
import { FileText, Sparkles, AlertCircle } from 'lucide-react';
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

  if (!isHarassing) {
    return (
      <div className="text-xs text-slate-500 flex items-start gap-2 bg-slate-50 p-3 rounded-lg border border-slate-100">
        <AlertCircle size={14} className="mt-0.5 text-slate-400 flex-shrink-0" />
        <p>No incident summary required. The message is classified as safe.</p>
      </div>
    );
  }

  return (
    <>
      {!summary && (
        <Button
          onClick={handleSummarize}
          disabled={summaryLoading}
          loading={summaryLoading}
          loadingText="Generating summary..."
          variant="outline"
          className="text-sm w-full justify-center"
        >
          <Sparkles size={16} /> Generate Incident Summary
        </Button>
      )}

      {summaryError && <p className="text-sm text-rose-600 mt-2">{summaryError}</p>}

      {summary && (
        <div className="space-y-4 text-sm animate-fade-in">
          <div>
            <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider">
              Description
            </span>
            <p className="text-slate-700 mt-1 leading-relaxed">
              {summary.incident_description}
            </p>
          </div>
          <div className="grid grid-cols-2 gap-4 pt-2">
            <div>
              <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider">
                Category
              </span>
              <p className="text-slate-700 mt-1">{summary.category}</p>
            </div>
            <div>
              <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider">
                Severity
              </span>
              <p
                className={`mt-1 font-medium ${
                  summary.severity === 'high'
                    ? 'text-rose-600'
                    : summary.severity === 'medium'
                    ? 'text-amber-600'
                    : 'text-slate-600'
                }`}
              >
                {summary.severity?.toUpperCase()}
              </p>
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
