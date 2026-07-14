import { useState } from 'react'

const LABEL_STYLES = {
  harassing: 'bg-red-50 text-red-800',
  non_harassing: 'bg-green-50 text-green-800',
}

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

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5">
      <textarea
        className="w-full min-h-24 rounded-lg border border-gray-300 p-3 text-sm resize-y focus:outline-none focus:ring-2 focus:ring-slate-400"
        placeholder="Paste or type a message to analyze..."
        value={text}
        onChange={(e) => setText(e.target.value)}
      />
      <div className="flex justify-end mt-3">
        <button
          onClick={handleAnalyze}
          disabled={loading}
          className="bg-slate-800 text-white text-sm font-medium px-4 py-2 rounded-lg disabled:opacity-50"
        >
          {loading ? 'Analyzing...' : 'Analyze message'}
        </button>
      </div>

      {error && <p className="text-sm text-red-600 mt-3">{error}</p>}

      {result && !error && (
        <div className="mt-4 pt-4 border-t border-gray-200 flex items-center justify-between flex-wrap gap-2">
          <div className="flex items-center gap-3">
            <span className={`text-xs font-medium px-2.5 py-1 rounded-md ${LABEL_STYLES[result.label] || ''}`}>
              {result.label === 'harassing' ? 'Harassing' : 'Non-harassing'}
            </span>
            <span className="text-sm text-gray-600">Category: {result.category.replace('_', ' ')}</span>
          </div>
          <span className="text-sm text-gray-600">
            Confidence: <strong className="text-gray-900 font-medium">{Math.round(result.confidence * 100)}%</strong>
          </span>
        </div>
      )}
    </div>
  )
}
