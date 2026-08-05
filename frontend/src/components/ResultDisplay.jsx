import PropTypes from 'prop-types';
import Card from './common/Card';
import RiskBadge from './prediction/RiskBadge';
import ConfidenceBar from './prediction/ConfidenceBar';
import ToxicWordHighlight from './prediction/ToxicWordHighlight';
import PredictionSummary from './prediction/PredictionSummary';

export default function ResultDisplay({ result }) {
  if (!result) return null;

  const isHarassing = result.label === 'harassing';

  return (
    <Card className="animate-slide-up space-y-5">
      {/* ── Verdict row ── */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        <RiskBadge
          isHarassing={isHarassing}
          category={result.category}
          riskScore={result.risk_score}
        />
        <ConfidenceBar
          confidence={result.confidence}
          isHarassing={isHarassing}
        />
      </div>

      {/* ── Explainability: word-level contributions (baseline model) ── */}
      <ToxicWordHighlight explanation={result.explanation} />

      {/* ── Model note for non-baseline models ── */}
      {result.model && result.model !== 'baseline' && (!result.explanation || !result.explanation.length) && (
        <div className="text-xs text-gray-400 italic flex items-center gap-1.5">
          <span>ℹ️</span>
          Word-level explanations are only available for the baseline (linear)
          model. The current model ({result.model}) uses non-linear
          classification.
        </div>
      )}

      {/* ── Audio transcript (from /predict/audio) ── */}
      {result.transcript && (
        <div className="bg-gray-50 border border-gray-200 rounded-xl p-4">
          <p className="text-xs font-semibold text-gray-600 mb-2 flex items-center gap-2">
            <span>📝</span> Transcript
            {result.language && (
              <span className="text-gray-400 font-normal">
                (detected: {result.language})
              </span>
            )}
          </p>
          <p className="text-sm text-gray-700 leading-relaxed">
            {result.transcript}
          </p>
        </div>
      )}

      {/* ── Extracted text (from OCR) ── */}
      {result.extracted_text && (
        <div className="bg-gray-50 border border-gray-200 rounded-xl p-4">
          <p className="text-xs font-semibold text-gray-600 mb-2 flex items-center gap-2">
            <span>📝</span> Extracted Text (OCR)
          </p>
          <p className="text-sm text-gray-700 leading-relaxed">
            {result.extracted_text}
          </p>
        </div>
      )}

      {/* ── Similar reports (from duplicate detection) ── */}
      {result.similar_reports?.length > 0 && (
        <div className="bg-amber-50 border border-amber-200 rounded-xl p-4">
          <p className="text-xs font-semibold text-amber-700 mb-2 flex items-center gap-2">
            <span>🔗</span> Similar Reports Detected
          </p>
          <ul className="space-y-1">
            {result.similar_reports.map((sr, i) => (
              <li key={i} className="text-xs text-amber-800">
                &quot;{sr.text_preview}&quot; — {Math.round(sr.similarity * 100)}%
                similar
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* ── Groq complaint summary ── */}
      <PredictionSummary
        isHarassing={isHarassing}
        category={result.category}
        confidence={result.confidence}
        textToSummarize={
          result.text_preview || result.transcript || result.extracted_text
        }
      />

      {/* ── Meta info ── */}
      <div className="flex items-center justify-between text-[11px] text-gray-400 pt-2 border-t border-gray-100">
        <span>
          Model:{' '}
          <strong className="text-gray-600">{result.model || 'baseline'}</strong>
        </span>
        {result.timestamp && (
          <span>{new Date(result.timestamp).toLocaleString()}</span>
        )}
      </div>
    </Card>
  );
}

ResultDisplay.propTypes = {
  result: PropTypes.shape({
    label: PropTypes.string,
    category: PropTypes.string,
    confidence: PropTypes.number,
    model: PropTypes.string,
    explanation: PropTypes.array,
    transcript: PropTypes.string,
    language: PropTypes.string,
    risk_score: PropTypes.number,
    extracted_text: PropTypes.string,
    similar_reports: PropTypes.array,
    text_preview: PropTypes.string,
    timestamp: PropTypes.string,
  }),
};
