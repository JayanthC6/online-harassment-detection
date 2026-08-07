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
  const [mode, setMode] = useState('text') // 'text', 'audio', 'conversation'
  const [audioFile, setAudioFile] = useState(null)
  const [messages, setMessages] = useState([{ text: '', sender: 'User 1' }])
  
  const { loading, error, result, predictText, predictAudio, predictConversation } = usePredict()

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
      {/* ── AI Assistant Header ── */}
      <div className="flex items-center gap-4 px-2">
        <div className="w-12 h-12 bg-indigo-100 text-indigo-600 rounded-full flex items-center justify-center shrink-0">
          <Sparkles size={24} />
        </div>
        <div>
          <h2 className="text-lg font-semibold text-slate-800">How can I help you analyze content today?</h2>
          <p className="text-sm text-slate-500">Submit text, audio, or a full conversation for digital safety analysis.</p>
        </div>
      </div>

      {/* ── Mode toggle ── */}
      <Card className="border-indigo-100 shadow-sm">
        <div className="flex flex-wrap items-center gap-2 mb-6 border-b border-slate-100 pb-4">
          <Button
            onClick={() => setMode('text')}
            variant="ghost"
            className={`text-sm ${mode === 'text' ? '!bg-slate-100 !text-slate-900 !border-slate-300' : ''}`}
          >
            <FileText size={16} className={mode === 'text' ? 'text-indigo-600' : 'text-slate-400'} /> Text
          </Button>
          <Button
            onClick={() => setMode('audio')}
            variant="ghost"
            className={`text-sm ${mode === 'audio' ? '!bg-slate-100 !text-slate-900 !border-slate-300' : ''}`}
          >
            <Mic size={16} className={mode === 'audio' ? 'text-indigo-600' : 'text-slate-400'} /> Audio / Video
          </Button>
          <Button
            onClick={() => setMode('conversation')}
            variant="ghost"
            className={`text-sm ${mode === 'conversation' ? '!bg-slate-100 !text-slate-900 !border-slate-300' : ''}`}
          >
            <MessageSquare size={16} className={mode === 'conversation' ? 'text-indigo-600' : 'text-slate-400'} /> Conversation
          </Button>
        </div>

        {mode === 'conversation' ? (
          <>
            <div className="section-title">
              Conversation Input
            </div>
            
            <div className="space-y-4 max-h-[400px] overflow-y-auto pr-2">
              {messages.map((msg, index) => (
                <div key={index} className="flex gap-2">
                  <div className="flex-1 space-y-2 bg-slate-50 p-3 rounded-lg border border-slate-200">
                    <div className="flex justify-between items-center">
                      <input 
                        type="text" 
                        value={msg.sender}
                        onChange={(e) => {
                          const newMessages = [...messages];
                          newMessages[index].sender = e.target.value;
                          setMessages(newMessages);
                        }}
                        className="text-xs font-semibold bg-transparent border-none p-0 focus:ring-0 text-slate-700 w-32"
                        placeholder="Sender Name"
                      />
                      {messages.length > 1 && (
                        <button 
                          onClick={() => setMessages(messages.filter((_, i) => i !== index))}
                          className="text-slate-400 hover:text-rose-500 transition-colors"
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
            
            <div className="mt-4 flex justify-between items-center border-t border-slate-100 pt-4">
              <Button
                variant="ghost"
                onClick={() => setMessages([...messages, { text: '', sender: `User ${messages.length % 2 === 0 ? 1 : 2}` }])}
              >
                <Plus size={16} /> Add Message
              </Button>
              <Button
                onClick={handleConversationAnalyze}
                disabled={!messages.some(m => m.text.trim())}
                loading={loading}
              >
                <Sparkles size={16} /> Analyze Conversation
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
                <span className="text-xs text-slate-400">Ctrl + Enter to analyze</span>
                <span className="text-xs text-slate-300">{text.length}/2000</span>
              </div>
              <Button
                onClick={handleAnalyze}
                disabled={!text.trim()}
                loading={loading}
              >
                <Sparkles size={16} /> Analyze Text
              </Button>
            </div>

            {/* Quick examples — only before first result */}
            {!result && !loading && (
              <div className="mt-6 pt-4 border-t border-slate-100">
                <p className="text-[10px] text-slate-400 uppercase tracking-wider mb-3">Quick test examples</p>
                <div className="flex flex-wrap gap-2">
                  {quickExamples.map((ex, i) => (
                    <button
                      key={i}
                      onClick={() => setText(ex)}
                      className="text-xs text-slate-500 hover:text-slate-800 bg-slate-50 hover:bg-slate-100 border border-slate-200 rounded-md px-3 py-1.5 transition-colors truncate max-w-[240px]"
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
              icon={<Mic className="mx-auto h-8 w-8 text-slate-400 mb-2" />}
              activeClasses={{
                container: '!border-indigo-400 !bg-indigo-50/50',
                text: 'text-indigo-700'
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
                <Sparkles size={16} /> Analyze Audio
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
