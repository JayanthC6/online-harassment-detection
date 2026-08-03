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
 *   - risk_score (0-100, from risk scoring)
 */
import { useState } from 'react'

function ResultDisplay({ result }) {
  if (!result) return null

  const [summary, setSummary] = useState(null)
  const [summaryLoading, setSummaryLoading] = useState(false)
  const [summaryError, setSummaryError] = useState(null)

  const isHarassing = result.label === 'harassing'
  const conf = Math.round((result.confidence || 0) * 100)

  const CATEGORY_LABELS = {
    hate_speech: { text: 'Hate Speech', color: 'text-red-700 bg-red-50 border-red-200' },
    offensive_language: { text: 'Offensive Language', color: 'text-amber-700 bg-amber-50 border-amber-200' },
    none: { text: 'Clean', color: 'text-emerald-700 bg-emerald-50 border-emerald-200' },
  }

  const catInfo = CATEGORY_LABELS[result.category] || CATEGORY_LABELS.none

  /* ── Groq summarization ── */
  const handleSummarize = async () => {
    setSummaryLoading(true)
    setSummaryError(null)
    try {
      const res = await fetch('/api/summarize', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          text: result.text_preview || result.transcript || result.extracted_text || '',
          category: result.category,
          confidence: result.confidence,
        }),
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.error || 'Summarization failed')
      setSummary(data)
    } catch (err) {
      setSummaryError(err.message)
    } finally {
      setSummaryLoading(false)
    }
  }

  return (
    <div className="glass-card p-6 animate-slide-up space-y-5">

      {/* ── Verdict row ── */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div className="flex items-center gap-3">
          {/* Harassing / Safe badge */}
          <span className={`badge text-sm border ${isHarassing
            ? 'bg-red-50 text-red-700 border-red-200'
            : 'bg-emerald-50 text-emerald-700 border-emerald-200'}`}>
            {isHarassing ? '🚨 Harassing' : '✅ Safe'}
          </span>

          {/* Category badge */}
          <span className={`badge text-xs border ${catInfo.color}`}>
            {catInfo.text}
          </span>

          {/* Risk score badge */}
          {result.risk_score != null && (
            <span className={`badge text-xs border ${
              result.risk_score >= 70 ? 'bg-red-50 text-red-700 border-red-200'
              : result.risk_score >= 40 ? 'bg-amber-50 text-amber-700 border-amber-200'
              : 'bg-gray-50 text-gray-600 border-gray-200'
            }`}>
              Risk: {Math.round(result.risk_score)}
            </span>
          )}
        </div>

        {/* Confidence bar */}
        <div className="flex items-center gap-2">
          <div className="h-2 w-28 bg-gray-100 rounded-full overflow-hidden">
            <div
              className={`h-full rounded-full transition-all duration-700 ${
                isHarassing
                  ? 'bg-red-500'
                  : 'bg-emerald-500'
              }`}
              style={{ width: `${conf}%` }}
            />
          </div>
          <span className="text-sm text-gray-500 font-mono tabular-nums">{conf}%</span>
        </div>
      </div>

      {/* ── Explainability: word-level contributions (baseline model) ── */}
      {result.explanation?.length > 0 && (
        <div className="bg-violet-50 border border-violet-200 rounded-xl p-4">
          <p className="text-xs font-semibold text-violet-700 mb-3 flex items-center gap-2">
            <span>🔬</span> Word-Level Contributions
            <span className="text-violet-400 font-normal">(TF-IDF × LR coefficients)</span>
          </p>
          <div className="flex gap-2 flex-wrap">
            {result.explanation.map((item, i) => (
              <div key={i} className="bg-violet-100 border border-violet-200 rounded-lg px-3 py-1.5 text-xs">
                <span className="text-violet-800 font-medium">{item.word}</span>
                <span className="text-violet-500 ml-1.5">+{item.contribution.toFixed(3)}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ── Model note for non-baseline models ── */}
      {result.model && result.model !== 'baseline' && !result.explanation?.length && (
        <div className="text-xs text-gray-400 italic flex items-center gap-1.5">
          <span>ℹ️</span>
          Word-level explanations are only available for the baseline (linear) model.
          The current model ({result.model}) uses non-linear classification.
        </div>
      )}

      {/* ── Audio transcript (from /predict/audio) ── */}
      {result.transcript && (
        <div className="bg-gray-50 border border-gray-200 rounded-xl p-4">
          <p className="text-xs font-semibold text-gray-600 mb-2 flex items-center gap-2">
            <span>📝</span> Transcript
            {result.language && <span className="text-gray-400 font-normal">(detected: {result.language})</span>}
          </p>
          <p className="text-sm text-gray-700 leading-relaxed">{result.transcript}</p>
        </div>
      )}

      {/* ── Extracted text (from OCR) ── */}
      {result.extracted_text && (
        <div className="bg-gray-50 border border-gray-200 rounded-xl p-4">
          <p className="text-xs font-semibold text-gray-600 mb-2 flex items-center gap-2">
            <span>📝</span> Extracted Text (OCR)
          </p>
          <p className="text-sm text-gray-700 leading-relaxed">{result.extracted_text}</p>
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
                "{sr.text_preview}" — {Math.round(sr.similarity * 100)}% similar
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* ── Groq complaint summary ── */}
      {isHarassing && !summary && (
        <button
          onClick={handleSummarize}
          disabled={summaryLoading}
          className="btn-ghost text-xs w-full justify-center"
        >
          {summaryLoading ? (
            <span className="flex items-center gap-2">
              <svg className="w-3 h-3 animate-spin" viewBox="0 0 24 24" fill="none"><circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" strokeDasharray="32" strokeLinecap="round" /></svg>
              Generating summary...
            </span>
          ) : '📋 Generate Incident Summary'}
        </button>
      )}

      {summaryError && (
        <p className="text-xs text-red-600">{summaryError}</p>
      )}

      {summary && (
        <div className="bg-indigo-50 border border-indigo-200 rounded-xl p-4 space-y-3">
          <p className="text-xs font-semibold text-indigo-700 flex items-center gap-2">
            <span>📋</span> Incident Summary
          </p>
          <div className="space-y-2 text-sm">
            <div>
              <span className="text-xs font-semibold text-gray-500 uppercase">Description</span>
              <p className="text-gray-700 mt-0.5">{summary.incident_description}</p>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <span className="text-xs font-semibold text-gray-500 uppercase">Category</span>
                <p className="text-gray-700 mt-0.5">{summary.category}</p>
              </div>
              <div>
                <span className="text-xs font-semibold text-gray-500 uppercase">Severity</span>
                <p className={`mt-0.5 font-medium ${
                  summary.severity === 'high' ? 'text-red-700'
                  : summary.severity === 'medium' ? 'text-amber-700'
                  : 'text-gray-700'
                }`}>{summary.severity?.toUpperCase()}</p>
              </div>
            </div>
            <div>
              <span className="text-xs font-semibold text-gray-500 uppercase">Suggested Action</span>
              <p className="text-gray-700 mt-0.5">{summary.suggested_action}</p>
            </div>
          </div>
        </div>
      )}

      {/* ── Meta info ── */}
      <div className="flex items-center justify-between text-[11px] text-gray-400 pt-2 border-t border-gray-100">
        <span>Model: <strong className="text-gray-600">{result.model || 'baseline'}</strong></span>
        {result.timestamp && (
          <span>{new Date(result.timestamp).toLocaleString()}</span>
        )}
      </div>
    </div>
  )
}

export default ResultDisplay
