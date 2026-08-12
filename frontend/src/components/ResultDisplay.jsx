import PropTypes from 'prop-types';
import { Layers, Lightbulb, FileText, Link, Info, Activity } from 'lucide-react';
import Card from './common/Card';
import RiskBadge from './prediction/RiskBadge';
import RedactionBar from './common/RedactionBar';
import ConfidenceBar from './prediction/ConfidenceBar';
import ToxicWordHighlight from './prediction/ToxicWordHighlight';
import PredictionSummary from './prediction/PredictionSummary';
import ConversationResultDisplay from './ConversationResultDisplay';
import GuidancePanel from './prediction/GuidancePanel';

export default function ResultDisplay({ result }) {
  if (!result) return null;

  if (result.messages) {
    return <ConversationResultDisplay result={result} />;
  }

  const isHarassing = result.label === 'harassing';

  return (
    <div className="space-y-6 animate-slide-up mt-8">
      {/* ── SECTION 2: PREDICTION ── */}
      <div className="space-y-3">
        <h2 className="text-sm font-bold text-off-white font-display flex items-center gap-2">
          <Layers size={18} className="text-slate-500" />
          Incident Analysis Report
        </h2>
        
        <Card className="p-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            <div className="space-y-6">
              <div>
                <p className="text-xs font-semibold text-slate-500 font-mono uppercase tracking-wider mb-3">Incident Classification</p>
                <div className="flex items-center gap-4">
                  <RiskBadge
                    isHarassing={isHarassing}
                    category={result.category}
                    riskScore={result.risk_score}
                  />
                </div>
              </div>
              
              <div>
                <p className="text-xs font-semibold text-slate-500 font-mono uppercase tracking-wider mb-3">Confidence Score</p>
                <ConfidenceBar
                  confidence={result.confidence}
                  isHarassing={isHarassing}
                />
              </div>
            </div>

            <div className="space-y-4 border-t md:border-t-0 md:border-l border-slate-700 pt-4 md:pt-0 md:pl-8">
              <div className="flex items-center justify-between mb-2">
                <p className="text-xs font-semibold text-slate-500 font-mono uppercase tracking-wider">Detected Categories</p>
              </div>
              
              {!result.secondary_labels || Object.keys(result.secondary_labels).length === 0 ? (
                <p className="text-sm text-slate-500 italic">No secondary categories detected.</p>
              ) : (
                <div className="space-y-3">
                  {Object.entries(result.secondary_labels).map(([label, conf]) => (
                    <div key={label} className="flex items-center gap-3">
                      <span className="text-sm text-off-white w-32 truncate">{label}</span>
                      <div className="flex-1">
                        <RedactionBar score={conf} tier="amber" />
                      </div>
                      <span className="text-xs font-medium text-slate-400 w-10 text-right font-mono tabular-nums">
                        {(conf * 100).toFixed(0)}%
                      </span>
                    </div>
                  ))}
                </div>
              )}
              
              <div className="pt-4 mt-2 border-t border-slate-700">
                <div className="flex items-center justify-between text-xs text-slate-500">
                  <span className="flex items-center gap-1.5 font-mono"><Activity size={12} /> Model Engine</span>
                  <span className="font-medium text-slate-400 font-mono">{result.model || 'distilbert'}</span>
                </div>
              </div>
            </div>
          </div>
        </Card>
      </div>

      {/* ── SECTION 3: AI INSIGHTS ── */}
      <div className="space-y-3 pt-4">
        <h2 className="text-sm font-bold text-off-white font-display flex items-center gap-2">
          <Lightbulb size={18} className="text-slate-500" />
          AI Insights
        </h2>

        <div className="grid grid-cols-1 gap-4">
          
          {/* Explainability Card */}
          <Card className="p-0 overflow-hidden">
            <div className="px-5 py-4 border-b border-slate-700 bg-panel">
              <h3 className="text-xs font-bold text-slate-400 font-mono uppercase tracking-wider">Explainability Analysis</h3>
            </div>
            <div className="p-5">
              <ToxicWordHighlight explanation={result.explanation} />
              {result.model && result.model !== 'baseline' && (!result.explanation || !result.explanation.length) && (
                <div className="text-xs text-slate-400 flex items-start gap-2 bg-slate-800/50 p-3 border border-slate-700">
                  <Info size={14} className="mt-0.5 text-slate-500 flex-shrink-0" />
                  <p>Word-level explanations are primarily available for baseline models or heuristic matches. The current engine ({result.model}) did not extract specific tokens.</p>
                </div>
              )}
            </div>
          </Card>

          {/* Incident Summary Card */}
          <Card className="p-0 overflow-hidden">
            <div className="px-5 py-4 border-b border-slate-700 bg-panel">
              <h3 className="text-xs font-bold text-slate-400 font-mono uppercase tracking-wider">Incident Summary</h3>
            </div>
            <div className="p-5">
              <PredictionSummary
                isHarassing={isHarassing}
                category={result.category}
                confidence={result.confidence}
                textToSummarize={result.text_preview || result.transcript || result.extracted_text}
              />
            </div>
          </Card>

          {/* Context Cards (Audio / OCR / Similar) */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            
            {result.transcript && (
              <Card className="p-5 bg-panel border-slate-700">
                <p className="text-xs font-semibold text-slate-400 font-mono mb-3 flex items-center gap-2 uppercase tracking-wider">
                  <FileText size={14} /> Transcript {result.language && <span className="normal-case font-normal text-slate-500">({result.language})</span>}
                </p>
                <p className="text-sm text-off-white leading-relaxed">
                  {result.transcript}
                </p>
              </Card>
            )}

            {result.extracted_text && (
              <Card className="p-5 bg-panel border-slate-700">
                <p className="text-xs font-semibold text-slate-400 font-mono mb-3 flex items-center gap-2 uppercase tracking-wider">
                  <FileText size={14} /> OCR Extracted Text
                </p>
                <p className="text-sm text-off-white leading-relaxed">
                  {result.extracted_text}
                </p>
              </Card>
            )}

            {result.similar_reports?.length > 0 && (
              <Card className="p-5 border-alert-amber/50">
                <p className="text-xs font-semibold text-alert-amber font-mono mb-3 flex items-center gap-2 uppercase tracking-wider">
                  <Link size={14} /> Similar Reports
                </p>
                <ul className="space-y-2">
                  {result.similar_reports.map((sr, i) => (
                    <li key={i} className="text-sm text-off-white leading-snug">
                      &quot;{sr.text_preview}&quot; <span className="font-mono text-alert-amber ml-1">({Math.round(sr.similarity * 100)}% match)</span>
                    </li>
                  ))}
                </ul>
              </Card>
            )}
            
          </div>
          
          {/* Guidance Panel */}
          {result.guidance && (
            <div className="mt-6">
              <GuidancePanel guidance={result.guidance} />
            </div>
          )}
        </div>
      </div>
      
      <div className="text-center pt-4">
        <p className="text-[10px] text-slate-600 font-mono">Analyzed at {new Date(result.timestamp || Date.now()).toLocaleString()}</p>
      </div>
    </div>
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
    secondary_labels: PropTypes.object,
  }),
};
