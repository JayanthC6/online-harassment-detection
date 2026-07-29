import { useState } from 'react'

/* ΓöÇΓöÇ shared result display component ΓöÇΓöÇ */
function ResultDisplay({ result }) {
  if (!result) return null

  const isHarassing = result.label === 'harassing'
  const conf = Math.round((result.confidence || 0) * 100)
  const rec = result.recommendation

  const SEVERITY_STYLES = {
    critical: 'bg-red-500/15 border-red-500/30 text-red-300',
    high: 'bg-orange-500/15 border-orange-500/30 text-orange-300',
    moderate: 'bg-yellow-500/15 border-yellow-500/30 text-yellow-300',
    low: 'bg-blue-500/15 border-blue-500/30 text-blue-300',
    safe: 'bg-emerald-500/15 border-emerald-500/30 text-emerald-300',
  }

  return (
    <div className="glass-card p-6 animate-slide-up space-y-4">
      {/* ΓöÇΓöÇ Verdict row ΓöÇΓöÇ */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div className="flex items-center gap-3">
          <span className={`badge text-sm ${isHarassing
            ? 'bg-red-500/20 text-red-300 border border-red-500/30'
            : 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'}`}>
            {isHarassing ? '≡ƒö┤ Harassing' : '≡ƒƒó Safe'}
          </span>
          {result.risk_level && (
            <span className="badge bg-white/5 text-gray-300 border border-white/10 text-[11px]">
              {result.risk_level}
            </span>
          )}
        </div>
        <div className="flex items-center gap-2">
          <div className="h-2 w-28 bg-white/10 rounded-full overflow-hidden">
            <div
              className={`h-full rounded-full transition-all duration-700 ${
                isHarassing
                  ? 'bg-gradient-to-r from-red-500 to-orange-500'
                  : 'bg-gradient-to-r from-emerald-500 to-teal-500'
              }`}
              style={{ width: `${conf}%` }}
            />
          </div>
          <span className="text-sm text-gray-400 font-mono tabular-nums">{conf}%</span>
        </div>
      </div>

      {/* ΓöÇΓöÇ Category tags ΓöÇΓöÇ */}
      {result.advanced_categories?.length > 0 && (
        <div className="flex gap-2 flex-wrap">
          {result.advanced_categories.map(cat => (
            <span key={cat} className="badge bg-indigo-500/10 text-indigo-300 border border-indigo-500/20">
              {cat}
            </span>
          ))}
        </div>
      )}

      {/* ΓöÇΓöÇ Language ΓöÇΓöÇ */}
      {result.detected_language && result.detected_language !== 'en' && (
        <div className="flex items-center gap-2 text-xs text-gray-500">
          <span>≡ƒîÉ</span>
          <span>Detected: <strong className="text-gray-300">{result.detected_language}</strong> ΓÇö auto-translated</span>
        </div>
      )}

      {/* ΓöÇΓöÇ Explainability: word-level (baseline model) ΓöÇΓöÇ */}
      {result.explanation?.length > 0 && (
        <div className="bg-violet-500/8 border border-violet-500/20 rounded-xl p-4">
          <p className="text-xs font-semibold text-violet-300 mb-3 flex items-center gap-2">
            <span>≡ƒö¼</span> Word-Level Contributions (TF-IDF ├ù LR coefficients)
          </p>
          <div className="flex gap-2 flex-wrap">
            {result.explanation.map((item, i) => (
              <div key={i} className="bg-violet-500/15 border border-violet-500/25 rounded-lg px-3 py-1.5 text-xs">
                <span className="text-violet-200 font-medium">{item.word}</span>
                <span className="text-violet-400/70 ml-1.5">+{item.contribution.toFixed(3)}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ΓöÇΓöÇ Explainability: model note ΓöÇΓöÇ */}
      {result.model && result.model !== 'baseline' && !result.explanation?.length && (
        <div className="text-xs text-gray-500 italic flex items-center gap-1.5">
          <span>Γä╣∩╕Å</span>
          Word-level explanations are only available for the baseline (linear) model.
          The current model ({result.model}) uses non-linear classification.
        </div>
      )}

      {/* ΓöÇΓöÇ XAI reasoning (advanced classifier) ΓöÇΓöÇ */}
      {result.reasons?.length > 0 && (
        <div className="bg-blue-500/8 border border-blue-500/20 rounded-xl p-4">
          <p className="text-xs font-semibold text-blue-300 mb-2 flex items-center gap-2">
            <span>≡ƒºá</span> AI Reasoning
          </p>
          <ul className="space-y-1">
            {result.reasons.map((r, i) => (
              <li key={i} className="text-xs text-blue-200/80 flex items-start gap-2">
                <span className="text-blue-400 mt-0.5">ΓåÆ</span> {r}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* ΓöÇΓöÇ Perspective API ΓöÇΓöÇ */}
      {result.perspective && (
        <div className="bg-cyan-500/8 border border-cyan-500/20 rounded-xl p-4">
          <p className="text-xs font-semibold text-cyan-300 mb-3 flex items-center gap-2">
            <span>≡ƒöÄ</span> Google Perspective API <span className="text-cyan-500/50 font-normal">(independent second opinion)</span>
          </p>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
            {Object.entries(result.perspective).map(([key, val]) => (
              <div key={key} className="text-center">
                <div className="text-lg font-bold text-cyan-200">{Math.round(val * 100)}%</div>
                <div className="text-[10px] text-cyan-400/60 uppercase tracking-wider">{key.replace('_', ' ')}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ΓöÇΓöÇ Evidence verification ΓöÇΓöÇ */}
      {result.is_duplicate && (
        <div className="bg-red-500/10 border border-red-500/30 rounded-xl p-3 animate-scale-in">
          <p className="text-xs font-semibold text-red-300 flex items-center gap-2">
            <span>≡ƒöü</span> DUPLICATE DETECTED ΓÇö A highly similar complaint already exists.
          </p>
        </div>
      )}
      {result.similar_cases?.length > 0 && !result.is_duplicate && (
        <div className="bg-amber-500/8 border border-amber-500/20 rounded-xl p-3">
          <p className="text-xs text-amber-300 flex items-center gap-2">
            <span>≡ƒöì</span> <strong>Evidence:</strong> {result.similar_cases.length} similar case(s) found.
          </p>
        </div>
      )}

      {/* ΓöÇΓöÇ Recommendation ΓöÇΓöÇ */}
      {rec && rec.severity !== 'safe' && (
        <div className={`border rounded-xl p-4 ${SEVERITY_STYLES[rec.severity] || SEVERITY_STYLES.moderate}`}>
          <p className="text-xs font-semibold mb-2 flex items-center gap-2">
            <span>ΓÜí</span> Recommended Action
            <span className={`ml-auto badge text-[10px] ${SEVERITY_STYLES[rec.severity]}`}>
              {rec.severity?.toUpperCase()}
            </span>
          </p>
          <p className="text-sm font-medium mb-1">{rec.action}</p>
          <p className="text-xs opacity-80 leading-relaxed">{rec.reasoning}</p>
          {rec.legal_note && (
            <p className="text-xs opacity-60 mt-2 border-t border-current/10 pt-2">
              ΓÜû∩╕Å {rec.legal_note}
            </p>
          )}
        </div>
      )}

      {/* ΓöÇΓöÇ LLM summary ΓöÇΓöÇ */}
      {result.llm_summary && (
        <div className="bg-white/[0.03] border border-white/[0.08] rounded-xl p-4">
          <p className="text-xs font-semibold text-gray-300 mb-3 flex items-center gap-2">
            <span>≡ƒôï</span> AI Incident Summary
          </p>
          <div className="grid grid-cols-2 gap-2 text-xs">
            <div className="bg-white/5 rounded-lg p-2.5">
              <span className="text-gray-500 block mb-0.5">Platform</span>
              <span className="text-gray-200 font-medium">{result.llm_summary.Platform}</span>
            </div>
            <div className="bg-white/5 rounded-lg p-2.5">
              <span className="text-gray-500 block mb-0.5">Threat Level</span>
              <span className="text-gray-200 font-medium">{result.llm_summary.Threat_Level}</span>
            </div>
            <div className="col-span-2 bg-white/5 rounded-lg p-2.5">
              <span className="text-gray-500 block mb-0.5">Incident</span>
              <span className="text-gray-200">{result.llm_summary.Incident}</span>
            </div>
          </div>
        </div>
      )}

      {/* ΓöÇΓöÇ Extracted text (OCR / transcript) ΓöÇΓöÇ */}
      {result.extracted_text && (
        <div className="bg-white/[0.03] border border-white/[0.08] rounded-xl p-4">
          <p className="text-xs font-semibold text-gray-400 mb-2 flex items-center gap-2">
            <span>≡ƒôä</span> Extracted Text (OCR)
          </p>
          <p className="text-sm text-gray-300 leading-relaxed">{result.extracted_text}</p>
        </div>
      )}

      {result.transcript && (
        <div className="bg-white/[0.03] border border-white/[0.08] rounded-xl p-4">
          <p className="text-xs font-semibold text-gray-400 mb-2 flex items-center gap-2">
            <span>≡ƒô¥</span> Transcript
            {result.language && <span className="text-gray-600 font-normal">(detected: {result.language})</span>}
          </p>
          <p className="text-sm text-gray-300 leading-relaxed">{result.transcript}</p>
        </div>
      )}
    </div>
  )
}

export default ResultDisplay
