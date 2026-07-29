import { useState } from 'react'
import ResultDisplay from './ResultDisplay'

export default function AnalyzeForm({ onNewResult }) {
  const [text, setText] = useState('')
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const handleAnalyze = async () => {
    if (!text.trim()) return
    setLoading(true)
    setError(null)
    try {
      const res = await fetch('/api/predict', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text }),
      })
      if (!res.ok) throw new Error('Request failed')
      const data = await res.json()
      setResult(data)
      if (onNewResult) onNewResult(data)
    } catch (err) {
      setError('Could not reach the analysis service. Is the Flask backend running?')
    } finally {
      setLoading(false)
    }
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) handleAnalyze()
  }

  const quickExamples = [
    "You're worthless, just disappear already",
    "I hate all people from that country, they are subhuman",
    "Great job on the presentation today!",
  ]

  return (
    <div className="space-y-4">
      <div className="glass-card p-6">
        <div className="section-title">
          <span className="w-1.5 h-1.5 bg-indigo-500 rounded-full" />
          Message Input
        </div>

        <textarea
          className="input-dark w-full min-h-28 p-4 text-sm resize-y"
          placeholder="Paste or type a message to analyze for harassment, threats, or hate speech..."
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={handleKeyDown}
          maxLength={2000}
        />

        <div className="flex items-center justify-between mt-3 flex-wrap gap-2">
          <div className="flex items-center gap-3">
            <span className="text-xs text-gray-600">Ctrl + Enter to analyze</span>
            <span className="text-xs text-gray-700">{text.length}/2000</span>
          </div>
          <button
            onClick={handleAnalyze}
            disabled={loading || !text.trim()}
            className="btn-primary"
          >
            {loading ? (
              <span className="flex items-center gap-2">
                <svg className="w-4 h-4 animate-spin" viewBox="0 0 24 24" fill="none"><circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" strokeDasharray="32" strokeLinecap="round" /></svg>
                Analyzing...
              </span>
            ) : '🔍 Analyze'}
          </button>
        </div>

        {/* Quick examples */}
        {!result && !loading && (
          <div className="mt-4 pt-4 border-t border-white/[0.06]">
            <p className="text-[10px] text-gray-600 uppercase tracking-wider mb-2">Quick test examples</p>
            <div className="flex flex-wrap gap-2">
              {quickExamples.map((ex, i) => (
                <button
                  key={i}
                  onClick={() => setText(ex)}
                  className="text-xs text-gray-500 hover:text-gray-300 bg-white/[0.03] hover:bg-white/[0.06] border border-white/[0.06] rounded-lg px-3 py-1.5 transition-all duration-200 truncate max-w-[220px]"
                >
                  "{ex.slice(0, 35)}..."
                </button>
              ))}
            </div>
          </div>
        )}
      </div>

      {error && (
        <div className="glass-card p-4 border-red-500/30 animate-slide-up">
          <p className="text-sm text-red-400 flex items-center gap-2">
            <span>⚠️</span> {error}
          </p>
        </div>
      )}

      <ResultDisplay result={result} />
    </div>
  )
}
