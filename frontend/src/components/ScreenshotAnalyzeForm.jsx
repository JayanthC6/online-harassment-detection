import { useState, useRef } from 'react'
import ResultDisplay from './ResultDisplay'

const ALLOWED_IMAGE = '.png,.jpg,.jpeg,.webp'

export default function ScreenshotAnalyzeForm({ onNewResult }) {
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [imageFile, setImageFile] = useState(null)
  const fileRef = useRef(null)

  const handleImageAnalyze = async () => {
    if (!imageFile) return
    setLoading(true)
    setError(null)
    setResult(null)
    try {
      const formData = new FormData()
      formData.append('file', imageFile)
      const res = await fetch('/api/predict/screenshot', {
        method: 'POST',
        body: formData,
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.error || 'Screenshot analysis failed')
      setResult(data)
      if (onNewResult) onNewResult(data)
    } catch (err) {
      setError(err.message || 'Could not analyze screenshot. Is the backend running?')
    } finally {
      setLoading(false)
    }
  }

  const handleFileDrop = (e) => {
    e.preventDefault()
    e.currentTarget.classList.remove('dragover')
    const file = e.dataTransfer?.files?.[0]
    if (file) setImageFile(file)
  }

  return (
    <div className="space-y-4">
      <div className="glass-card p-6 mt-4">
        <div className="section-title">
          <span className="w-1.5 h-1.5 bg-emerald-500 rounded-full" />
          Screenshot Upload
        </div>

        <div
          className={`drop-zone ${imageFile ? 'border-emerald-500/30 bg-emerald-500/5' : ''}`}
          onDragOver={(e) => { e.preventDefault(); e.currentTarget.classList.add('dragover') }}
          onDragLeave={(e) => e.currentTarget.classList.remove('dragover')}
          onDrop={handleFileDrop}
          onClick={() => fileRef.current?.click()}
        >
          <input
            ref={fileRef}
            type="file"
            accept={ALLOWED_IMAGE}
            className="hidden"
            onChange={(e) => setImageFile(e.target.files?.[0] || null)}
          />
          {imageFile ? (
            <div className="space-y-1">
              <p className="text-sm text-emerald-300 font-medium">📁 {imageFile.name}</p>
              <p className="text-xs text-gray-500">{(imageFile.size / (1024 * 1024)).toFixed(1)} MB — click to change</p>
            </div>
          ) : (
            <div className="space-y-2">
              <p className="text-2xl">🖼️</p>
              <p className="text-sm text-gray-400">Drop a screenshot here or click to browse</p>
              <p className="text-xs text-gray-600">Supported: PNG, JPG, WEBP (max 10MB)</p>
            </div>
          )}
        </div>

        <div className="flex justify-end mt-3">
          <button
            onClick={handleImageAnalyze}
            disabled={loading || !imageFile}
            className="btn-primary"
            style={!loading && imageFile ? { background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)' } : {}}
          >
            {loading ? (
              <span className="flex items-center gap-2">
                <svg className="w-4 h-4 animate-spin" viewBox="0 0 24 24" fill="none"><circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" strokeDasharray="32" strokeLinecap="round" /></svg>
                Extracting text & analyzing...
              </span>
            ) : '🖼️ Analyze Screenshot'}
          </button>
        </div>
      </div>

      {error && (
        <div className="glass-card p-4 !border-red-500/30 animate-slide-up">
          <p className="text-sm text-red-400 flex items-center gap-2">
            <span>⚠️</span> {error}
          </p>
        </div>
      )}

      {result && <ResultDisplay result={result} />}
    </div>
  )
}
