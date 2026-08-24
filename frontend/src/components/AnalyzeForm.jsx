import { useState, useRef } from 'react'
import { FileText, Mic, Image, Search, Sparkles, MessageSquare, Plus, Trash2 } from 'lucide-react'
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
  const [platform, setPlatform] = useState('generic') // For screenshots
  const [mode, setMode] = useState('text') // 'text', 'audio', 'conversation', 'screenshot'
  const [audioFile, setAudioFile] = useState(null)
  const [importFile, setImportFile] = useState(null)
  const [messages, setMessages] = useState([{ text: '', sender: 'User 1' }])
  const [documentFile, setDocumentFile] = useState(null)
  
  const { loading, error, result, predictText, predictAudio, predictConversation, importConversation, predictFile } = usePredict()

  /* ── Text analysis ── */
  const handleAnalyze = async () => {
    if (!text.trim()) return
    const data = await predictText(text, actorId)
    if (data && onNewResult) onNewResult(data)
  }

  /* ── Audio analysis ── */
  const handleAudioAnalyze = async () => {
    if (!audioFile) return
    const data = await predictAudio(audioFile, actorId)
    if (data && onNewResult) onNewResult(data)
  }

  /* ── File analysis ── */
  const handleFileAnalyze = async () => {
    if (!documentFile) return
    const data = await predictFile(documentFile, actorId)
    if (data && onNewResult) onNewResult(data)
  }

  /* ── Conversation analysis ── */
  const handleConversationAnalyze = async () => {
    if (importFile) {
      const data = await importConversation(importFile);
      if (data && onNewResult) onNewResult(data);
      return;
    }
    
    const validMessages = messages.filter(m => m.text.trim());
    if (validMessages.length === 0) return;
    const data = await predictConversation(validMessages);
    if (data && onNewResult) onNewResult(data);
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) handleAnalyze()
  }

  const quickExamples = [
    "You're worthless, just disappear already",
    "I hate all people from that country, they are subhuman",
    "Send 0.5 BTC to this address or your photos will be leaked",
    "Urgent Action Required: Please verify your account at http://login-secure-update.com",
  ]

  return (
    <div className="space-y-4">
      {/* ── Mode toggle ── */}
      <Card className="">
        {/* ── Evidence type tabs ── */}
        <div className="flex flex-wrap gap-0 mb-5 pb-4 border-b border-border">
          <button
            onClick={() => setMode('text')}
            className={`tab-btn ${mode === 'text' ? 'active' : ''}`}
          >
            <FileText size={14} /> Text
          </button>
          <button
            onClick={() => setMode('audio')}
            className={`tab-btn ${mode === 'audio' ? 'active' : ''}`}
          >
            <Mic size={14} /> Audio / Video
          </button>
          <button
            onClick={() => setMode('conversation')}
            className={`tab-btn ${mode === 'conversation' ? 'active' : ''}`}
          >
            <MessageSquare size={14} /> Conversation
          </button>
          <button
            onClick={() => setMode('file')}
            className={`tab-btn ${mode === 'file' ? 'active' : ''}`}
          >
            <FileText size={14} /> File Document
          </button>
        </div>

        {mode === 'conversation' ? (
          <>
            <p className="section-title">Conversation Input</p>
            
            <div className="mb-5">
              <p className="text-xs font-semibold text-text-muted uppercase tracking-wider mb-2">Import Chat Export</p>
              <FileUpload
                file={importFile}
                onFileSelect={setImportFile}
                accept=".txt,.json"
                icon={<FileText className="mx-auto h-6 w-6 text-slate-400 mb-2" />}
                titleText="Upload WhatsApp (.txt) or Instagram (.json) export"
                supportedText="Platform will be auto-detected based on file type."
              />
            </div>

            <div className="flex items-center gap-4 mb-4">
              <div className="flex-1 border-t border-border"></div>
              <span className="text-2xs text-text-muted uppercase tracking-widest font-semibold">or manually enter</span>
              <div className="flex-1 border-t border-border"></div>
            </div>
            
            <div className={`space-y-3 max-h-[400px] overflow-y-auto pr-2 ${importFile ? 'opacity-50 pointer-events-none' : ''}`}>
              {messages.map((msg, index) => (
                <div key={index} className="flex gap-2">
                  <div className="flex-1 space-y-2 panel p-3">
                    <div className="flex justify-between items-center">
                      <input 
                        type="text" 
                        value={msg.sender}
                        onChange={(e) => {
                          const newMessages = [...messages];
                          newMessages[index].sender = e.target.value;
                          setMessages(newMessages);
                        }}
                        className="text-xs font-semibold bg-transparent border-none p-0 focus:outline-none text-text-primary w-32 font-mono"
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
                      className="input-dark w-full min-h-16 p-2 text-sm resize-y"
                      placeholder="Message content..."
                      value={msg.text}
                      onChange={(e) => {
                        const newMessages = [...messages];
                        newMessages[index].text = e.target.value;
                        setMessages(newMessages);
                      }}
                      maxLength={1000}
                    />
                  </div>
                </div>
              ))}
            </div>
            
            <div className="mt-4 flex justify-between items-center border-t border-border pt-4">
              <Button
                variant="ghost"
                onClick={() => setMessages([...messages, { text: '', sender: `User ${messages.length % 2 === 0 ? 1 : 2}` }])}
              >
                <Plus size={16} /> Add Message
              </Button>
              <Button
                onClick={handleConversationAnalyze}
                disabled={(!importFile && !messages.some(m => m.text.trim()))}
                loading={loading}
              >
                <Search size={16} /> {importFile ? 'Analyze Imported Chat' : 'Analyze Conversation'}
              </Button>
            </div>
          </>
        ) : mode === 'text' ? (
          <>
            <p className="section-title">Message Input</p>
            
            <div className="mb-4">
              <input 
                type="text" 
                value={actorId}
                onChange={(e) => setActorId(e.target.value)}
                className="input max-w-xs"
                placeholder="Actor ID (optional)"
              />
            </div>

            <textarea
              className="input min-h-32 p-3 resize-y"
              placeholder="Paste or type a message to analyze for digital safety threats..."
              value={text}
              onChange={(e) => setText(e.target.value)}
              onKeyDown={handleKeyDown}
              maxLength={2000}
            />

            <div className="flex items-center justify-between mt-4 flex-wrap gap-2">
              <div className="flex items-center gap-3">
                <span className="text-2xs text-text-muted font-mono">Ctrl + Enter to analyze</span>
                <span className="text-2xs text-text-muted font-mono">{text.length}/2000</span>
              </div>
              <Button
                onClick={handleAnalyze}
                disabled={!text.trim()}
                loading={loading}
              >
                <Search size={16} /> Analyze Text
              </Button>
            </div>

            {/* Quick examples — only before first result */}
            {!result && !loading && (
              <div className="mt-5 pt-4 border-t border-border">
                <p className="text-2xs text-text-muted uppercase tracking-widest font-semibold mb-3">Quick test examples</p>
                <div className="flex flex-wrap gap-2">
                  {quickExamples.map((ex, i) => (
                    <button
                      key={i}
                      onClick={() => setText(ex)}
                      className="text-xs text-text-muted hover:text-text-secondary bg-surface-2 hover:bg-surface-3 border border-border hover:border-border-2 px-3 py-1.5 rounded transition-colors truncate max-w-[240px] font-mono"
                    >
                      "{ex.slice(0, 35)}..."
                    </button>
                  ))}
                </div>
              </div>
            )}
          </>
        ) : mode === 'audio' ? (
          /* ── Audio upload ── */
          <>
            <p className="section-title">Audio / Video Upload</p>
            
            <div className="mb-4">
              <input 
                type="text" 
                value={actorId}
                onChange={(e) => setActorId(e.target.value)}
                className="input max-w-xs"
                placeholder="Actor ID (optional)"
              />
            </div>

            <FileUpload
              file={audioFile}
              onFileSelect={setAudioFile}
              accept={ALLOWED_AUDIO}
              icon={<Mic className="mx-auto h-8 w-8 text-text-muted mb-2" />}
              activeClasses={{
                container: '!border-blue !bg-blue-muted',
                text: 'text-text-primary'
              }}
              titleText="Drop an audio/video file here or click to browse"
              supportedText="Supported: MP3, WAV, M4A, MP4, MOV, WebM, OGG (max 50MB)"
            />

            <div className="flex justify-end mt-4">
              <Button
                onClick={handleAudioAnalyze}
                disabled={!audioFile}
                loading={loading}
                loadingText="Transcribing & analyzing..."
              >
                <Search size={16} /> Analyze Audio
              </Button>
            </div>
          </>
        ) : mode === 'file' ? (
          /* ── File upload ── */
          <>
            <p className="section-title">File Upload</p>
            
            <div className="mb-4">
              <input 
                type="text" 
                value={actorId}
                onChange={(e) => setActorId(e.target.value)}
                className="input max-w-xs"
                placeholder="Actor ID (optional)"
              />
            </div>

            <FileUpload
              file={documentFile}
              onFileSelect={setDocumentFile}
              accept=".txt,.pdf,.png,.jpg,.jpeg"
              icon={<FileText className="mx-auto h-8 w-8 text-text-muted mb-2" />}
              activeClasses={{
                container: '!border-blue !bg-blue-muted',
                text: 'text-text-primary'
              }}
              titleText="Drop a document or image file here"
              supportedText="Supported: TXT, PDF, PNG, JPG (max 50MB)"
            />

            <div className="flex justify-end mt-4">
              <Button
                onClick={handleFileAnalyze}
                disabled={!documentFile}
                loading={loading}
                loadingText="Extracting & analyzing..."
              >
                <Search size={16} /> Analyze File
              </Button>
            </div>
          </>
        ) : null}
      </Card>

      <ErrorAlert error={error} />

      {/* ── Result ── */}
      <ResultDisplay result={result} />
    </div>
  )
}
