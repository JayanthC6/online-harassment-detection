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
    <div className="grid grid-cols-12 gap-gutter animate-slide-up mt-8">
      {/* Dials & Telemetry (Col 8) */}
      <div className="col-span-12 lg:col-span-8 flex flex-col gap-gutter">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-gutter h-full">
          {/* Risk Score Dial */}
          <div className="glass-panel clip-path-chamfer p-6 flex flex-col items-center justify-center relative overflow-hidden h-64">
            <div className="absolute -right-8 -bottom-8 opacity-10">
              <Layers size={120} className={isHarassing ? "text-error" : "text-primary-fixed"} />
            </div>
            <h3 className="font-label-caps text-label-caps text-on-surface-variant uppercase tracking-wider mb-4">Risk Classification</h3>
            <RiskBadge
              isHarassing={isHarassing}
              category={result.category}
              riskScore={result.risk_score}
            />
          </div>

          {/* Confidence Dial */}
          <div className="glass-panel clip-path-chamfer p-6 flex flex-col items-center justify-center relative overflow-hidden h-64">
            <div className="absolute -right-8 -top-8 opacity-10">
              <Activity size={120} className="text-primary-fixed" />
            </div>
            <h3 className="font-label-caps text-label-caps text-on-surface-variant uppercase tracking-wider mb-4">Attribution Confidence</h3>
            <ConfidenceBar
              confidence={result.confidence}
              isHarassing={isHarassing}
            />
          </div>
        </div>

        {/* AI Insights & Secondary Classifications */}
        <div className="glass-panel clip-path-chamfer p-6 flex flex-col gap-4 border-l-4 border-secondary-container">
          <div className="font-label-caps text-label-caps text-on-surface flex items-center gap-2">
            <Lightbulb size={18} className="text-secondary-container" /> AI Insights & Secondary Labels
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              {!result.secondary_labels || Object.keys(result.secondary_labels).length === 0 ? (
                <p className="text-sm text-slate-500 italic">No secondary categories detected.</p>
              ) : (
                <div className="space-y-3">
                  {Object.entries(result.secondary_labels).map(([label, conf]) => (
                    <div key={label} className="flex items-center gap-3">
                      <span className="text-sm text-on-surface w-32 truncate">{label}</span>
                      <div className="flex-1">
                        <RedactionBar score={conf} tier="amber" />
                      </div>
                      <span className="text-xs font-medium text-primary-fixed w-10 text-right font-mono tabular-nums">
                        {(conf * 100).toFixed(0)}%
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>
            <div>
              <PredictionSummary
                isHarassing={isHarassing}
                category={result.category}
                confidence={result.confidence}
                textToSummarize={result.text_preview || result.transcript || result.extracted_text}
              />
            </div>
          </div>
        </div>
      </div>

      {/* Terminal Evidence (Col 4) */}
      <div className="col-span-12 lg:col-span-4 terminal-block border border-outline-variant clip-path-chamfer-lg p-6 relative h-auto min-h-[400px] flex flex-col">
        <div className="absolute top-0 left-0 w-full h-8 bg-surface-container-high border-b border-outline-variant flex items-center px-4 gap-2 font-label-caps text-label-caps text-on-surface-variant">
          <span className="w-3 h-3 rounded-full bg-error"></span>
          <span className="w-3 h-3 rounded-full bg-surface-variant"></span>
          <span className="w-3 h-3 rounded-full bg-surface-variant"></span>
          <span className="ml-2 opacity-50">/var/log/analysis_extract.txt</span>
        </div>
        
        <div className="mt-8 flex-1 overflow-y-auto font-metadata-sm text-metadata-sm text-[#00ff00] opacity-80 leading-relaxed font-mono">
          <p className="mb-1">&gt; INITIALIZING FORENSIC PARSER...</p>
          <p className="mb-1">&gt; DECRYPTING PAYLOAD...</p>
          
          <div className="my-4">
            <ToxicWordHighlight explanation={result.explanation} />
          </div>
          
          {result.model && result.model !== 'baseline' && (!result.explanation || !result.explanation.length) && (
            <p className="mb-1 text-secondary-container">&gt; [INFO] Word-level explanations primarily available for heuristic matches. Current engine: {result.model}.</p>
          )}

          {result.transcript && (
            <>
              <p className="mb-1 mt-4">&gt; EXTRACTING AUDIO TRANSCRIPT...</p>
              <div className="bg-black/50 p-2 my-2 border-l-2 border-primary-fixed text-on-surface break-words">
                {result.transcript}
              </div>
            </>
          )}

          {result.extracted_text && (
            <>
              <p className="mb-1 mt-4">&gt; EXTRACTING OCR TEXT...</p>
              <div className="bg-black/50 p-2 my-2 border-l-2 border-primary-fixed text-on-surface break-words">
                {result.extracted_text}
              </div>
            </>
          )}
          
          {result.similar_reports?.length > 0 && (
            <>
              <p className="mb-1 mt-4 text-error">&gt; CORRELATING THREAT INTEL...</p>
              <ul className="space-y-2 my-2">
                {result.similar_reports.map((sr, i) => (
                  <li key={i} className="bg-black/50 p-2 border-l-2 border-error">
                    &quot;{sr.text_preview}&quot; <span className="text-error">({Math.round(sr.similarity * 100)}% match)</span>
                  </li>
                ))}
              </ul>
            </>
          )}

          <p className="animate-pulse mt-4">_</p>
        </div>
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
