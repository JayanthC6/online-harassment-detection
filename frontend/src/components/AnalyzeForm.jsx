import { useState, useRef } from 'react'
import { usePredict } from '../hooks/usePredict'
import ResultDisplay from './ResultDisplay'
import Card from './common/Card'
import Button from './common/Button'
import FileUpload from './common/FileUpload'
import ErrorAlert from './common/ErrorAlert'

const ALLOWED_AUDIO = '.mp3,.wav,.m4a,.mp4,.mov,.webm,.ogg'

export default function AnalyzeForm({ onNewResult }) {
  const [text, setText] = useState('')
  const [mode, setMode] = useState('text') // 'text' or 'audio'
  const [audioFile, setAudioFile] = useState(null)
  const fileRef = useRef(null)
  
  const { loading, error, result, predictText, predictAudio } = usePredict()

  /* ── Text analysis ── */
  const handleAnalyze = async () => {
    if (!text.trim()) return
    const data = await predictText(text)
    if (data && onNewResult) onNewResult(data)
  }

  /* ── Audio analysis ── */
  const handleAudioAnalyze = async () => {
    if (!audioFile) return
    const data = await predictAudio(audioFile)
    if (data && onNewResult) onNewResult(data)
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
      <Card>
        <div className="flex items-center gap-3 mb-4">
          <Button
            onClick={() => setMode('text')}
            variant="ghost"
            className={`text-xs ${mode === 'text' ? '!border-indigo-500 !text-indigo-700 !bg-indigo-50' : ''}`}
          >
            📝 Text
          </Button>
          <Button
            onClick={() => setMode('audio')}
            variant="ghost"
            className={`text-xs ${mode === 'audio' ? '!border-indigo-500 !text-indigo-700 !bg-indigo-50' : ''}`}
          >
            🎙️ Audio / Video
          </Button>
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
              <Button
                onClick={handleAnalyze}
                disabled={!text.trim()}
                loading={loading}
              >
                🔍 Analyze
              </Button>
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

            <FileUpload
              file={audioFile}
              onFileSelect={setAudioFile}
              accept={ALLOWED_AUDIO}
              icon="🎤"
              activeClasses={{
                container: '!border-indigo-400 !bg-indigo-50/50',
                text: 'text-indigo-700'
              }}
              titleText="Drop an audio/video file here or click to browse"
              supportedText="Supported: MP3, WAV, M4A, MP4, MOV, WebM, OGG (max 50MB)"
            />

            <div className="flex justify-end mt-3">
              <Button
                onClick={handleAudioAnalyze}
                disabled={!audioFile}
                loading={loading}
                loadingText="Transcribing & analyzing..."
              >
                🎙️ Analyze Audio
              </Button>
            </div>
          </>
        )}
      </Card>

      <ErrorAlert error={error} />

      {/* ── Result ── */}
      <ResultDisplay result={result} />
    </div>
  )
}
