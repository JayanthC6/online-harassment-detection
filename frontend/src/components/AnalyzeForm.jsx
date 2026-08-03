import { useState, useRef } from 'react'
import ResultDisplay from './ResultDisplay'

const ALLOWED_AUDIO = '.mp3,.wav,.m4a,.mp4,.mov,.webm,.ogg'

export default function AnalyzeForm({ onNewResult }) {
  const [text, setText] = useState('')
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [mode, setMode] = useState('text') // 'text' or 'audio'
  const [audioFile, setAudioFile] = useState(null)
  const fileRef = useRef(null)

  /* ── Text analysis ── */
  const handleAnalyze = async () => {
    if (!text.trim()) return
    setLoading(true)
    setError(null)
    setResult(null)
    try {
      const res = await fetch('/api/predict', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text }),
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.error || 'Request failed')
      setResult(data)
      if (onNewResult) onNewResult(data)
    } catch (err) {
      setError(err.message || 'Could not reach the analysis service. Is the Flask backend running?')
    } finally {
      setLoading(false)
    }
  }

  /* ── Audio analysis ── */
  const handleAudioAnalyze = async () => {
    if (!audioFile) return
    setLoading(true)
    setError(null)
    setResult(null)
    try {
      const formData = new FormData()
      formData.append('file', audioFile)
      const res = await fetch('/api/predict/audio', {
        method: 'POST',
        body: formData,
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.error || 'Audio analysis failed')
      setResult(data)
      if (onNewResult) onNewResult(data)
    } catch (err) {
      setError(err.message || 'Could not analyze audio. Is the backend running with Whisper installed?')
    } finally {
      setLoading(false)
    }
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) handleAnalyze()
  }

  const handleFileDrop = (e) => {
    e.preventDefault()
    e.currentTarget.classList.remove('dragover')
    const file = e.dataTransfer?.files?.[0]
    if (file) setAudioFile(file)
  }

  const quickExamples = [
    "You're worthless, just disappear already",
    "I hate all people from that country, they are subhuman",
    "Great job on the presentation today!",
  ]

  return (
    <div className="space-y-4">
      {/* ── Mode toggle ── */}
      <div className="glass-card p-6">
        <div className="flex items-center gap-3 mb-4">
          <button
            onClick={() => setMode('text')}
            className={`btn-ghost text-xs ${mode === 'text' ? '!border-indigo-500 !text-indigo-700 !bg-indigo-50' : ''}`}
          >
            📝 Text
          </button>
          <button
            onClick={() => setMode('audio')}
            className={`btn-ghost text-xs ${mode === 'audio' ? '!border-indigo-500 !text-indigo-700 !bg-indigo-50' : ''}`}
          >
            🎙️ Audio / Video
          </button>
        </div>

        {mode === 'text' ? (
          <>
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
                <span className="text-xs text-gray-400">Ctrl + Enter to analyze</span>
                <span className="text-xs text-gray-300">{text.length}/2000</span>
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

            {/* Quick examples — only before first result */}
            {!result && !loading && (
              <div className="mt-4 pt-4 border-t border-gray-100">
                <p className="text-[10px] text-gray-400 uppercase tracking-wider mb-2">Quick test examples</p>
                <div className="flex flex-wrap gap-2">
                  {quickExamples.map((ex, i) => (
                    <button
                      key={i}
                      onClick={() => setText(ex)}
                      className="text-xs text-gray-500 hover:text-gray-700 bg-gray-50 hover:bg-gray-100 border border-gray-200 rounded-lg px-3 py-1.5 transition-all duration-200 truncate max-w-[220px]"
                    >
                      "{ex.slice(0, 35)}..."
                    </button>
                  ))}
                </div>
              </div>
            )}
          </>
        ) : (
          /* ── Audio upload ── */
          <>
            <div className="section-title">
              <span className="w-1.5 h-1.5 bg-purple-500 rounded-full" />
              Audio / Video Upload
            </div>

            <div
              className={`drop-zone ${audioFile ? '!border-indigo-400 !bg-indigo-50/50' : ''}`}
              onDragOver={(e) => { e.preventDefault(); e.currentTarget.classList.add('dragover') }}
              onDragLeave={(e) => e.currentTarget.classList.remove('dragover')}
              onDrop={handleFileDrop}
              onClick={() => fileRef.current?.click()}
            >
              <input
                ref={fileRef}
                type="file"
                accept={ALLOWED_AUDIO}
                className="hidden"
                onChange={(e) => setAudioFile(e.target.files?.[0] || null)}
              />
              {audioFile ? (
                <div className="space-y-1">
                  <p className="text-sm text-indigo-700 font-medium">📁 {audioFile.name}</p>
                  <p className="text-xs text-gray-500">{(audioFile.size / (1024 * 1024)).toFixed(1)} MB — click to change</p>
                </div>
              ) : (
                <div className="space-y-2">
                  <p className="text-2xl">🎤</p>
                  <p className="text-sm text-gray-500">Drop an audio/video file here or click to browse</p>
                  <p className="text-xs text-gray-400">Supported: MP3, WAV, M4A, MP4, MOV, WebM, OGG (max 50MB)</p>
                </div>
              )}
            </div>

            <div className="flex justify-end mt-3">
              <button
                onClick={handleAudioAnalyze}
                disabled={loading || !audioFile}
                className="btn-primary"
              >
                {loading ? (
                  <span className="flex items-center gap-2">
                    <svg className="w-4 h-4 animate-spin" viewBox="0 0 24 24" fill="none"><circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" strokeDasharray="32" strokeLinecap="round" /></svg>
                    Transcribing & analyzing...
                  </span>
                ) : '🎙️ Analyze Audio'}
              </button>
            </div>
          </>
        )}
      </div>

      {/* ── Error display ── */}
      {error && (
        <div className="glass-card p-4 !border-red-300 !bg-red-50 animate-slide-up">
          <p className="text-sm text-red-700 flex items-center gap-2">
            <span>⚠️</span> {error}
          </p>
        </div>
      )}

      {/* ── Result ── */}
      <ResultDisplay result={result} />
    </div>
  )
}
