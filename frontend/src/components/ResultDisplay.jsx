/**
 * ResultDisplay — shows the analysis result from /predict or /predict/audio.
 *
 * Only renders fields that the backend actually returns:
 *   - label (harassing / non_harassing)
 *   - category (hate_speech / offensive_language / none)
 *   - confidence (0-1)
 *   - model (baseline / distilbert)
 *   - explanation (array of {word, contribution} — baseline model only)
 *   - transcript + language (audio endpoint only)
 */
function ResultDisplay({ result }) {
  if (!result) return null

  const isHarassing = result.label === 'harassing'
  const conf = Math.round((result.confidence || 0) * 100)

  const CATEGORY_LABELS = {
    hate_speech: { text: 'Hate Speech', color: 'text-red-300 bg-red-500/15 border-red-500/25' },
    offensive_language: { text: 'Offensive Language', color: 'text-orange-300 bg-orange-500/15 border-orange-500/25' },
    none: { text: 'Clean', color: 'text-emerald-300 bg-emerald-500/15 border-emerald-500/25' },
  }

  const catInfo = CATEGORY_LABELS[result.category] || CATEGORY_LABELS.none

  return (
    <div className="glass-card p-6 animate-slide-up space-y-5">

      {/* ── Verdict row ── */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div className="flex items-center gap-3">
          {/* Harassing / Safe badge */}
          <span className={`badge text-sm ${isHarassing
            ? 'bg-red-500/20 text-red-300 border border-red-500/30'
            : 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'}`}>
            {isHarassing ? '🚨 Harassing' : '✅ Safe'}
          </span>

          {/* Category badge */}
          <span className={`badge text-xs border ${catInfo.color}`}>
            {catInfo.text}
          </span>
        </div>

        {/* Confidence bar */}
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

      {/* ── Explainability: word-level contributions (baseline model) ── */}
      {result.explanation?.length > 0 && (
        <div className="bg-violet-500/[0.08] border border-violet-500/20 rounded-xl p-4">
          <p className="text-xs font-semibold text-violet-300 mb-3 flex items-center gap-2">
            <span>🔬</span> Word-Level Contributions
            <span className="text-violet-500/50 font-normal">(TF-IDF × LR coefficients)</span>
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

      {/* ── Model note for non-baseline models ── */}
      {result.model && result.model !== 'baseline' && !result.explanation?.length && (
        <div className="text-xs text-gray-500 italic flex items-center gap-1.5">
          <span>ℹ️</span>
          Word-level explanations are only available for the baseline (linear) model.
          The current model ({result.model}) uses non-linear classification.
        </div>
      )}

      {/* ── Audio transcript (from /predict/audio) ── */}
      {result.transcript && (
        <div className="bg-white/[0.03] border border-white/[0.08] rounded-xl p-4">
          <p className="text-xs font-semibold text-gray-400 mb-2 flex items-center gap-2">
            <span>📝</span> Transcript
            {result.language && <span className="text-gray-600 font-normal">(detected: {result.language})</span>}
          </p>
          <p className="text-sm text-gray-300 leading-relaxed">{result.transcript}</p>
        </div>
      )}

      {/* ── Extracted text (from OCR) ── */}
      {result.extracted_text && (
        <div className="bg-white/[0.03] border border-white/[0.08] rounded-xl p-4 mt-4">
          <p className="text-xs font-semibold text-gray-400 mb-2 flex items-center gap-2">
            <span>📝</span> Extracted Text (OCR)
          </p>
          <p className="text-sm text-gray-300 leading-relaxed">{result.extracted_text}</p>
        </div>
      )}

      {/* ── Meta info ── */}
      <div className="flex items-center justify-between text-[11px] text-gray-600 pt-2 border-t border-white/[0.04]">
        <span>Model: <strong className="text-gray-400">{result.model || 'baseline'}</strong></span>
        {result.timestamp && (
          <span>{new Date(result.timestamp).toLocaleString()}</span>
        )}
      </div>
    </div>
  )
}

export default ResultDisplay
