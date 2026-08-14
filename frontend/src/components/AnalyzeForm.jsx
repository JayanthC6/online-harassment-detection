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
  
  const { loading, error, result, predictText, predictAudio, predictConversation, importConversation } = usePredict()

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
    <div className="space-y-6">
      {/* ── Mode toggle ── */}
      <Card className="border-outline-variant">
        {/* ── Evidence type tabs ── */}
        <div className="flex flex-wrap gap-4 mb-6 pb-6 border-b border-outline-variant/30">
          <button
            onClick={() => setMode('text')}
            className={`flex items-center gap-2 px-4 py-2 font-label-caps text-label-caps transition-all ${mode === 'text' ? 'text-primary-fixed border-b-2 border-primary-fixed' : 'text-on-surface-variant hover:text-primary-fixed-dim'}`}
          >
            <FileText size={16} /> Text
          </button>
          <button
            onClick={() => setMode('audio')}
            className={`flex items-center gap-2 px-4 py-2 font-label-caps text-label-caps transition-all ${mode === 'audio' ? 'text-primary-fixed border-b-2 border-primary-fixed' : 'text-on-surface-variant hover:text-primary-fixed-dim'}`}
          >
            <Mic size={16} /> Audio / Video
          </button>
          <button
            onClick={() => setMode('conversation')}
            className={`flex items-center gap-2 px-4 py-2 font-label-caps text-label-caps transition-all ${mode === 'conversation' ? 'text-primary-fixed border-b-2 border-primary-fixed' : 'text-on-surface-variant hover:text-primary-fixed-dim'}`}
          >
            <MessageSquare size={16} /> Conversation
          </button>
        </div>

        {mode === 'conversation' ? (
          <>
            <div className="section-title">
              Conversation Input
            </div>
            
            <div className="mb-6">
              <p className="text-sm font-bold text-slate-400 font-mono uppercase tracking-wider mb-2">Import Chat Export</p>
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
              <div className="flex-1 border-t border-slate-700"></div>
              <span className="text-xs text-slate-500 uppercase tracking-wider font-bold font-mono">OR MANUALLY ENTER</span>
              <div className="flex-1 border-t border-slate-700"></div>
            </div>
            
            <div className={`space-y-4 max-h-[400px] overflow-y-auto pr-2 ${importFile ? 'opacity-50 pointer-events-none' : ''}`}>
              {messages.map((msg, index) => (
                <div key={index} className="flex gap-2">
                  <div className="flex-1 space-y-2 bg-panel p-3 border border-slate-700">
                    <div className="flex justify-between items-center">
                      <input 
                        type="text" 
                        value={msg.sender}
                        onChange={(e) => {
                          const newMessages = [...messages];
                          newMessages[index].sender = e.target.value;
                          setMessages(newMessages);
                        }}
                        className="text-xs font-semibold bg-transparent border-none p-0 focus:ring-0 text-off-white w-32 font-mono"
                        placeholder="Sender Name"
                      />
                      {messages.length > 1 && (
                        <button 
                          onClick={() => setMessages(messages.filter((_, i) => i !== index))}
                          className="text-slate-500 hover:text-redaction-red transition-colors"
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
            
            <div className="mt-4 flex justify-between items-center border-t border-slate-700 pt-4">
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
            <div className="section-title">
              Message Input
            </div>
            
            <div className="mb-4">
              <input 
                type="text" 
                value={actorId}
                onChange={(e) => setActorId(e.target.value)}
                className="input-dark w-full max-w-xs text-sm"
                placeholder="Actor Identifier (Optional)"
              />
            </div>

            <textarea
              className="input-dark w-full min-h-32 p-4 text-sm resize-y"
              placeholder="Paste or type a message to analyze for digital safety threats..."
              value={text}
              onChange={(e) => setText(e.target.value)}
              onKeyDown={handleKeyDown}
              maxLength={2000}
            />

            <div className="flex items-center justify-between mt-4 flex-wrap gap-2">
              <div className="flex items-center gap-3">
                <span className="text-xs text-slate-500 font-mono">Ctrl + Enter to analyze</span>
                <span className="text-xs text-slate-400 font-mono">{text.length}/2000</span>
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
              <div className="mt-6 pt-4 border-t border-slate-700">
                <p className="text-[10px] text-slate-500 uppercase tracking-wider mb-3 font-mono">Quick test examples</p>
                <div className="flex flex-wrap gap-2">
                  {quickExamples.map((ex, i) => (
                    <button
                      key={i}
                      onClick={() => setText(ex)}
                      className="text-xs text-slate-400 hover:text-off-white bg-panel hover:bg-slate-800 border border-slate-700 px-3 py-1.5 transition-colors truncate max-w-[240px] font-mono"
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
              Audio / Video Upload
            </div>
            
            <div className="mb-4">
              <input 
                type="text" 
                value={actorId}
                onChange={(e) => setActorId(e.target.value)}
                className="input-dark w-full max-w-xs text-sm"
                placeholder="Actor Identifier (Optional)"
              />
            </div>

            <FileUpload
              file={audioFile}
              onFileSelect={setAudioFile}
              accept={ALLOWED_AUDIO}
              icon={<Mic className="mx-auto h-8 w-8 text-slate-500 mb-2" />}
              activeClasses={{
                container: '!border-off-white !bg-slate-800',
                text: 'text-off-white'
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
        )}
      </Card>

      <ErrorAlert error={error} />

      {/* ── Result ── */}
      <ResultDisplay result={result} />
    </div>
  )
}
