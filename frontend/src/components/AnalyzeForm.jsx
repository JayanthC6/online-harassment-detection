import { useState, useRef } from 'react'
import {
  FileText,
  Mic,
  Image,
  Search,
  Sparkles,
  MessageSquare,
  Plus,
  Trash2,
  EyeOff,
  UploadCloud,
  CheckCircle2,
  Loader2,
  ShieldAlert,
  ArrowRight
} from 'lucide-react'
import { usePredict } from '../hooks/usePredict'
import ResultDisplay from './ResultDisplay'
import Card from './common/Card'
import Button from './common/Button'
import FileUpload from './common/FileUpload'
import ErrorAlert from './common/ErrorAlert'

const ALLOWED_AUDIO = '.mp3,.wav,.m4a,.mp4,.mov,.webm,.ogg'

export default function AnalyzeForm({ onNewResult }) {
  const [text, setText] = useState('')
  const [actorId, setActorId] = useState('')
  const [platform, setPlatform] = useState('generic')
  const [mode, setMode] = useState('text') // 'text', 'audio', 'conversation', 'file'
  const [audioFile, setAudioFile] = useState(null)
  const [importFile, setImportFile] = useState(null)
  const [messages, setMessages] = useState([{ text: '', sender: 'User 1' }])
  const [documentFile, setDocumentFile] = useState(null)
  const [doNotSave, setDoNotSave] = useState(false)
  const [isDragOver, setIsDragOver] = useState(false)

  const {
    loading,
    error,
    result,
    predictText,
    predictAudio,
    predictConversation,
    importConversation,
    predictFile
  } = usePredict()

  /* ── Text analysis ── */
  const handleAnalyze = async () => {
    if (!text.trim()) return
    const data = await predictText(text, actorId, !doNotSave)
    if (data && onNewResult) onNewResult(data)
  }

  /* ── Audio analysis ── */
  const handleAudioAnalyze = async () => {
    if (!audioFile) return
    const data = await predictAudio(audioFile, actorId, !doNotSave)
    if (data && onNewResult) onNewResult(data)
  }

  /* ── File analysis ── */
  const handleFileAnalyze = async () => {
    if (!documentFile) return
    const data = await predictFile(documentFile, actorId, !doNotSave)
    if (data && onNewResult) onNewResult(data)
  }

  /* ── Conversation analysis ── */
  const handleConversationAnalyze = async () => {
    if (importFile) {
      const data = await importConversation(importFile, !doNotSave)
      if (data && onNewResult) onNewResult(data)
      return
    }

    const validMessages = messages.filter(m => m.text.trim())
    if (validMessages.length === 0) return
    const data = await predictConversation(validMessages, !doNotSave)
    if (data && onNewResult) onNewResult(data)
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) handleAnalyze()
  }

  // 6 Representative Benchmark Cases for Phase 2 Verification
  const benchmarkCases = [
    {
      title: "Bank SMS (Phishing)",
      cat: "Phishing",
      color: "text-orange-400 border-orange-500/40 bg-orange-500/10",
      content: "Urgent: Your SBI net banking account has been temporarily blocked due to pending KYC verification. Click http://sbi-kyc-verify.top/auth immediately or access will terminate."
    },
    {
      title: "Lottery Scam (Scam)",
      cat: "Scam",
      color: "text-amber-400 border-amber-500/40 bg-amber-500/10",
      content: "Congratulations! Your mobile number won Rs 50,00,000 in Google Annual Lottery 2026. Send Rs 5,000 customs clearance fee via gift card to claim your prize."
    },
    {
      title: "Physical Threat",
      cat: "Threat",
      color: "text-red-400 border-red-500/40 bg-red-500/10",
      content: "I know exactly where you live and what time you leave your house. I will find you and kill you tonight."
    },
    {
      title: "Sextortion (Extortion)",
      cat: "Sextortion",
      color: "text-red-400 border-red-500/40 bg-red-500/10",
      content: "I have recorded a private video of you using your webcam. Transfer $800 in Bitcoin to my wallet within 24 hours or I will send it to all your contacts and family."
    },
    {
      title: "Abusive Insult",
      cat: "Abuse",
      color: "text-amber-400 border-amber-500/40 bg-amber-500/10",
      content: "You are the most pathetic, useless idiot I have ever met. Nobody likes you, get lost."
    },
    {
      title: "Harmless Message",
      cat: "Safe",
      color: "text-emerald-400 border-emerald-500/40 bg-emerald-500/10",
      content: "Hey, are you free for lunch today? Let's catch up at the cafeteria around 1:00 PM!"
    }
  ]

  // Global Drag & Drop Handler for Files
  const handleGlobalDrop = (e) => {
    e.preventDefault()
    setIsDragOver(false)
    const file = e.dataTransfer.files?.[0]
    if (!file) return

    const ext = file.name.split('.').pop()?.toLowerCase()
    if (['txt', 'json'].includes(ext) && file.name.toLowerCase().includes('chat')) {
      setImportFile(file)
      setMode('conversation')
    } else if (['mp3', 'wav', 'm4a', 'ogg'].includes(ext)) {
      setAudioFile(file)
      setMode('audio')
    } else {
      setDocumentFile(file)
      setMode('file')
    }
  }

  return (
    <div
      className="space-y-6"
      onDragOver={(e) => { e.preventDefault(); setIsDragOver(true); }}
      onDragLeave={() => setIsDragOver(false)}
      onDrop={handleGlobalDrop}
    >
      <Card className="relative overflow-hidden bg-surface/90 border border-border p-6 shadow-xl">
        {/* Drag Overlay */}
        {isDragOver && (
          <div className="absolute inset-0 bg-[#060913]/90 backdrop-blur-sm z-30 border-2 border-dashed border-blue flex flex-col items-center justify-center animate-fade-in">
            <UploadCloud size={48} className="text-blue animate-bounce" />
            <p className="text-sm font-bold text-white font-mono mt-3">Drop file here to analyze</p>
            <p className="text-xs text-text-muted">Chat exports (.txt, .json), documents (.pdf, .docx), images (.png, .jpg)</p>
          </div>
        )}

        {/* ── Evidence Type Tabs ── */}
        <div className="flex flex-wrap items-center justify-between gap-3 mb-6 pb-4 border-b border-border/50">
          <div className="flex flex-wrap gap-1">
            <button
              onClick={() => setMode('text')}
              className={`tab-btn ${mode === 'text' ? 'active' : ''}`}
            >
              <FileText size={14} /> Text Input
            </button>
            <button
              onClick={() => setMode('conversation')}
              className={`tab-btn ${mode === 'conversation' ? 'active' : ''}`}
            >
              <MessageSquare size={14} /> Chat Export (WhatsApp/IG)
            </button>
            <button
              onClick={() => setMode('file')}
              className={`tab-btn ${mode === 'file' ? 'active' : ''}`}
            >
              <FileText size={14} /> Document / Evidence
            </button>
            <button
              onClick={() => setMode('audio')}
              className={`tab-btn ${mode === 'audio' ? 'active' : ''}`}
            >
              <Mic size={14} /> Audio / Voice
            </button>
          </div>

          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              id="privacy-toggle"
              checked={doNotSave}
              onChange={(e) => setDoNotSave(e.target.checked)}
              className="w-4 h-4 rounded border-border bg-surface text-blue focus:ring-blue focus:ring-offset-bg cursor-pointer"
            />
            <label htmlFor="privacy-toggle" className="text-xs font-semibold text-text-muted hover:text-text-secondary flex items-center gap-1 cursor-pointer">
              <EyeOff size={13} />
              Private Scan (Do not save)
            </label>
          </div>
        </div>

        {/* ── Mode 1: Text Input ── */}
        {mode === 'text' && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <p className="section-title mb-0">Paste Message or Threat Text</p>
              <span className="text-2xs font-mono text-text-muted">
                {text.length} / 2000 characters
              </span>
            </div>

            <textarea
              className="input min-h-36 p-3.5 resize-y font-mono text-sm leading-relaxed bg-black/40 focus:bg-black/60 transition-colors border border-border"
              placeholder="Paste or type suspicious SMS, chat message, threat email, blackmail demand, or phishing link..."
              value={text}
              onChange={(e) => setText(e.target.value)}
              onKeyDown={handleKeyDown}
              maxLength={2000}
              disabled={loading}
            />

            <div className="flex flex-wrap items-center justify-between gap-3 pt-2">
              <div className="flex items-center gap-2">
                <input
                  type="text"
                  value={actorId}
                  onChange={(e) => setActorId(e.target.value)}
                  className="input text-xs py-1.5 w-44 font-mono"
                  placeholder="Sender / Actor ID (opt)"
                  disabled={loading}
                />
                <span className="text-2xs text-text-muted font-mono hidden sm:inline">
                  Press <kbd className="px-1.5 py-0.5 rounded bg-surface border border-border">Ctrl + Enter</kbd> to analyze
                </span>
              </div>

              <div className="flex items-center gap-2">
                {text && (
                  <button
                    type="button"
                    onClick={() => setText('')}
                    className="px-3 py-1.5 rounded-lg text-xs font-mono text-text-muted hover:text-text-primary transition-colors"
                  >
                    Clear
                  </button>
                )}
                <Button
                  onClick={handleAnalyze}
                  disabled={!text.trim() || loading}
                  loading={loading}
                >
                  <Search size={15} /> Analyze Message
                </Button>
              </div>
            </div>

            {/* Quick Benchmark Example Buttons */}
            <div className="mt-6 pt-5 border-t border-border/50">
              <p className="text-2xs text-text-muted uppercase tracking-widest font-mono font-bold mb-3 flex items-center gap-1.5">
                <Sparkles size={13} className="text-cyan-400" />
                Quick Benchmark Examples (Click to Test)
              </p>
              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2.5">
                {benchmarkCases.map((c, i) => (
                  <button
                    key={i}
                    type="button"
                    onClick={() => setText(c.content)}
                    className="p-2.5 rounded-lg bg-surface hover:bg-surface-2 border border-border hover:border-cyan-500/40 text-left transition-all group flex flex-col justify-between"
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-xs font-bold text-text-primary font-mono group-hover:text-cyan-300">
                        {c.title}
                      </span>
                      <span className={`text-[10px] font-mono uppercase px-1.5 py-0.5 rounded border ${c.color}`}>
                        {c.cat}
                      </span>
                    </div>
                    <p className="text-[11px] text-text-muted truncate font-mono">
                      "{c.content.slice(0, 45)}..."
                    </p>
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* ── Mode 2: Conversation Input ── */}
        {mode === 'conversation' && (
          <div className="space-y-4">
            <p className="section-title">Chat Conversation Analysis</p>

            <div className="mb-4">
              <p className="text-xs font-semibold text-text-muted uppercase tracking-wider mb-2">Import Chat Export</p>
              <FileUpload
                file={importFile}
                onFileSelect={setImportFile}
                accept=".txt,.json"
                icon={<FileText className="mx-auto h-6 w-6 text-slate-400 mb-2" />}
                titleText="Upload WhatsApp (.txt) or Instagram (.json) export"
                supportedText="Platform will be auto-detected based on file structure."
              />
            </div>

            <div className="flex items-center gap-4 my-4">
              <div className="flex-1 border-t border-border"></div>
              <span className="text-2xs text-text-muted uppercase tracking-widest font-semibold">or enter chat messages manually</span>
              <div className="flex-1 border-t border-border"></div>
            </div>

            <div className={`space-y-3 max-h-[360px] overflow-y-auto pr-2 ${importFile ? 'opacity-40 pointer-events-none' : ''}`}>
              {messages.map((msg, index) => (
                <div key={index} className="flex gap-2">
                  <div className="flex-1 space-y-2 p-3 rounded-lg bg-surface border border-border">
                    <div className="flex justify-between items-center">
                      <input
                        type="text"
                        value={msg.sender}
                        onChange={(e) => {
                          const newMessages = [...messages]
                          newMessages[index].sender = e.target.value
                          setMessages(newMessages)
                        }}
                        className="text-xs font-bold bg-transparent border-none p-0 focus:outline-none text-text-primary w-32 font-mono"
                        placeholder="Sender Name"
                      />
                      {messages.length > 1 && (
                        <button
                          onClick={() => setMessages(messages.filter((_, i) => i !== index))}
                          className="text-text-muted hover:text-danger transition-colors"
                        >
                          <Trash2 size={14} />
                        </button>
                      )}
                    </div>
                    <textarea
                      className="input w-full min-h-16 p-2 text-xs font-mono bg-black/40"
                      placeholder="Message content..."
                      value={msg.text}
                      onChange={(e) => {
                        const newMessages = [...messages]
                        newMessages[index].text = e.target.value
                        setMessages(newMessages)
                      }}
                      maxLength={1000}
                    />
                  </div>
                </div>
              ))}
            </div>

            <div className="mt-4 flex justify-between items-center border-t border-border/50 pt-4">
              <Button
                variant="ghost"
                onClick={() => setMessages([...messages, { text: '', sender: `User ${messages.length % 2 === 0 ? 1 : 2}` }])}
              >
                <Plus size={16} /> Add Message
              </Button>
              <Button
                onClick={handleConversationAnalyze}
                disabled={(!importFile && !messages.some(m => m.text.trim())) || loading}
                loading={loading}
              >
                <Search size={16} /> {importFile ? 'Analyze Imported Chat' : 'Analyze Conversation'}
              </Button>
            </div>
          </div>
        )}

        {/* ── Mode 3: File Document ── */}
        {mode === 'file' && (
          <div className="space-y-4">
            <p className="section-title">Upload Evidence Document or Screenshot</p>
            <FileUpload
              file={documentFile}
              onFileSelect={setDocumentFile}
              accept=".txt,.pdf,.png,.jpg,.jpeg,.json,.csv,.docx"
              icon={<FileText className="mx-auto h-8 w-8 text-text-muted mb-2" />}
              titleText="Drop a document or image file here"
              supportedText="Supported: TXT, PDF, DOCX, CSV, PNG, JPG (max 50MB)"
            />
            <div className="flex justify-end mt-4">
              <Button
                onClick={handleFileAnalyze}
                disabled={!documentFile || loading}
                loading={loading}
                loadingText="Extracting & analyzing..."
              >
                <Search size={16} /> Analyze File
              </Button>
            </div>
          </div>
        )}

        {/* ── Mode 4: Audio ── */}
        {mode === 'audio' && (
          <div className="space-y-4">
            <p className="section-title">Audio / Video Transcription & Analysis</p>
            <FileUpload
              file={audioFile}
              onFileSelect={setAudioFile}
              accept={ALLOWED_AUDIO}
              icon={<Mic className="mx-auto h-8 w-8 text-text-muted mb-2" />}
              titleText="Drop an audio/video file here or click to browse"
              supportedText="Supported: MP3, WAV, M4A, MP4, MOV, WebM, OGG (max 50MB)"
            />
            <div className="flex justify-end mt-4">
              <Button
                onClick={handleAudioAnalyze}
                disabled={!audioFile || loading}
                loading={loading}
                loadingText="Transcribing & analyzing..."
              >
                <Search size={16} /> Analyze Audio
              </Button>
            </div>
          </div>
        )}
      </Card>

      {/* ── Progress State (during analysis) ── */}
      {loading && (
        <Card className="p-6 bg-surface/90 border border-cyan-500/30 animate-fade-in shadow-xl">
          <div className="flex items-center gap-3 mb-4">
            <Loader2 size={20} className="animate-spin text-cyan-400" />
            <div>
              <h4 className="text-sm font-bold text-text-primary font-mono">
                Scanning Content & Evaluating Cyber Threat Signals...
              </h4>
              <p className="text-xs text-text-muted font-mono">
                Executing multi-layered ShieldAI safety pipeline
              </p>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-4 gap-2 text-xs font-mono">
            <div className="p-2.5 rounded bg-black/40 border border-cyan-500/30 text-cyan-300 flex items-center gap-2">
              <CheckCircle2 size={14} className="text-cyan-400 shrink-0" />
              <span>1. Normalization & De-obfuscation</span>
            </div>
            <div className="p-2.5 rounded bg-black/40 border border-cyan-500/30 text-cyan-300 flex items-center gap-2">
              <CheckCircle2 size={14} className="text-cyan-400 shrink-0" />
              <span>2. DistilBERT Neural Model</span>
            </div>
            <div className="p-2.5 rounded bg-black/40 border border-cyan-500/30 text-cyan-300 flex items-center gap-2">
              <CheckCircle2 size={14} className="text-cyan-400 shrink-0" />
              <span>3. Fraud & Phishing Rules</span>
            </div>
            <div className="p-2.5 rounded bg-black/40 border border-cyan-500/30 text-cyan-300 flex items-center gap-2">
              <CheckCircle2 size={14} className="text-cyan-400 shrink-0" />
              <span>4. Threat Aggregation</span>
            </div>
          </div>
        </Card>
      )}

      {/* ── Error Alert ── */}
      <ErrorAlert error={error} />

      {/* ── Result Display ── */}
      <ResultDisplay result={result} />
    </div>
  )
}
