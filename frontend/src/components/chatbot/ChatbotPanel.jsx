import React, { useState, useEffect, useRef } from 'react';
import { MessageSquare, X, Send, Loader2, ShieldAlert, Paperclip, FileText, Image, AlertCircle } from 'lucide-react';
import ReactMarkdown from 'react-markdown';

const MAX_FILE_MB = 50;
const ALLOWED_EXTS = ['pdf', 'txt', 'md', 'log', 'csv', 'json', 'docx', 'py', 'html', 'xml', 'png', 'jpg', 'jpeg', 'webp'];
const ACCEPT_ATTR = '.pdf,.txt,.md,.log,.csv,.json,.docx,.py,.html,.xml,.png,.jpg,.jpeg,.webp';

function FilePreview({ file, onRemove }) {
  const isImage = ['png', 'jpg', 'jpeg', 'webp'].includes(file.name.split('.').pop()?.toLowerCase());
  const sizeMb = (file.size / 1024 / 1024).toFixed(1);
  return (
    <div className="flex items-center gap-2 px-3 py-2 bg-surface border border-border-2 rounded-lg text-xs">
      {isImage ? <Image size={14} className="text-blue shrink-0" /> : <FileText size={14} className="text-blue shrink-0" />}
      <span className="text-text-primary font-medium truncate max-w-[160px]">{file.name}</span>
      <span className="text-text-muted shrink-0">{sizeMb} MB</span>
      <button onClick={onRemove} className="ml-auto text-text-muted hover:text-danger transition-colors shrink-0">
        <X size={12} />
      </button>
    </div>
  );
}

export default function ChatbotPanel({ role }) {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState('');
  const [selectedFile, setSelectedFile] = useState(null);
  const [fileError, setFileError] = useState('');

  const messagesEndRef = useRef(null);
  const fileInputRef = useRef(null);

  // Initialize session
  useEffect(() => {
    let sid = localStorage.getItem('shieldai_chat_session');
    if (!sid) {
      sid = 'session_' + Math.random().toString(36).substr(2, 9);
      localStorage.setItem('shieldai_chat_session', sid);
    }
    setSessionId(sid);

    fetch(`/chat/${sid}`)
      .then(res => res.json())
      .then(data => {
        if (data.messages && data.messages.length > 0) {
          setMessages(data.messages);
        } else {
          const isOrg = role && role !== 'User';
          setMessages([{
            role: 'assistant',
            content: isOrg 
              ? 'Hello! I am your **ShieldAI Investigative Analyst**.\n\nI can help you with:\n- 🛡️ Analyzing cyber threats\n- 📁 Evidence processing\n- 🔍 Recommending investigative tools (OSINT, IP tracking)\n- 🔐 Correlating threat actors'
              : 'Hello! I am your **ShieldAI Cyber Assistant**.\n\nI can help you with:\n- 🛡️ Cyber crime information\n- 📁 File analysis & summaries\n- 📰 Cyber security news\n- 🔐 Digital safety guidance\n\nYou can also **upload a file** (PDF, DOCX, TXT, images…) and I will analyze it for you.'
          }]);
        }
      })
      .catch(() => {});
  }, [role]);

  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, isOpen]);

  const handleFileSelect = (e) => {
    const file = e.target.files?.[0];
    setFileError('');
    if (!file) return;

    const ext = file.name.split('.').pop()?.toLowerCase();
    if (!ALLOWED_EXTS.includes(ext)) {
      setFileError(`Unsupported file type. Allowed: ${ALLOWED_EXTS.join(', ')}`);
      return;
    }
    const sizeMb = file.size / 1024 / 1024;
    if (sizeMb > MAX_FILE_MB) {
      setFileError(`File too large (${sizeMb.toFixed(1)} MB). Max ${MAX_FILE_MB} MB.`);
      return;
    }
    setSelectedFile(file);
  };

  const handleSend = async (e) => {
    e.preventDefault();
    if ((!input.trim() && !selectedFile) || isLoading) return;

    setIsLoading(true);
    setFileError('');

    // ── File upload path ──
    if (selectedFile) {
      const file = selectedFile;
      setSelectedFile(null);
      if (fileInputRef.current) fileInputRef.current.value = '';

      setMessages(prev => [...prev,
        { role: 'user', content: `📎 Uploaded: **${file.name}** (${(file.size / 1024 / 1024).toFixed(1)} MB)` },
        { role: 'assistant', content: '⏳ Reading and analyzing your file…' }
      ]);

      try {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('session_id', sessionId);
        const persona = role && role !== 'User' ? 'analyst' : 'user';
        formData.append('persona', persona);

        const res = await fetch('/chat/file', { method: 'POST', body: formData });
        const data = await res.json();

        setMessages(prev => {
          const updated = [...prev];
          // Replace the "analyzing..." placeholder
          updated[updated.length - 1] = {
            role: 'assistant',
            content: res.ok ? data.response : `Error: ${data.error}`
          };
          return updated;
        });
      } catch {
        setMessages(prev => {
          const updated = [...prev];
          updated[updated.length - 1] = { role: 'assistant', content: 'Network error while uploading file.' };
          return updated;
        });
      } finally {
        setIsLoading(false);
      }
      return;
    }

    // ── Text message path ──
    const userMessage = input.trim();
    setInput('');
    setMessages(prev => [...prev, { role: 'user', content: userMessage }]);

    try {
      const persona = role && role !== 'User' ? 'analyst' : 'user';
      const res = await fetch('/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: sessionId, message: userMessage, persona })
      });
      const data = await res.json();
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: res.ok ? data.response : `Error: ${data.error}`
      }]);
    } catch {
      setMessages(prev => [...prev, { role: 'assistant', content: 'Network error communicating with the server.' }]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <>
      {/* Floating Action Button */}
      <button
        onClick={() => setIsOpen(true)}
        className={`fixed bottom-6 right-6 h-14 w-14 text-bg rounded-full flex items-center justify-center z-50 transition-all duration-300 shadow-lg ${isOpen ? 'scale-0' : 'scale-100 hover:scale-105'}`}
        style={{ background: 'linear-gradient(135deg, #00F2FE, #00C4CE)' }}
        aria-label="Open Cyber Assistant"
      >
        <MessageSquare size={24} />
      </button>

      {/* Chat Panel */}
      <div
        className={`fixed bottom-6 right-6 w-[400px] max-w-[calc(100vw-2rem)] h-[580px] max-h-[calc(100vh-2rem)] bg-surface-2 border border-border rounded-xl flex flex-col z-50 transition-all duration-300 origin-bottom-right overflow-hidden ${isOpen ? 'scale-100 opacity-100' : 'scale-90 opacity-0 pointer-events-none'}`}
        style={{ boxShadow: '0 8px 48px rgba(0,242,254,0.08), 0 2px 16px rgba(0,0,0,0.6)' }}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-border bg-surface shrink-0">
          <div className="flex items-center gap-2.5">
            <div className="h-8 w-8 rounded-full bg-blue-glow border border-blue/30 flex items-center justify-center text-blue">
              <ShieldAlert size={16} />
            </div>
            <div>
              <h3 className="text-sm font-bold text-text-primary">
                {role && role !== 'User' ? 'Investigative Analyst' : 'Cyber Assistant'}
              </h3>
              <p className="text-xs text-blue flex items-center gap-1">
                <span className="w-1.5 h-1.5 rounded-full bg-blue animate-pulse inline-block" />
                Online · PDF, DOCX, TXT supported
              </p>
            </div>
          </div>
          <button onClick={() => setIsOpen(false)} className="p-1.5 text-text-muted hover:text-text-primary hover:bg-surface-3 rounded-md transition-colors">
            <X size={18} />
          </button>
        </div>

        {/* Message List */}
        <div className="flex-1 overflow-y-auto p-4 space-y-3 min-h-0">
          {messages.map((msg, idx) => (
            <div key={idx} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div
                className={`max-w-[90%] px-3 py-2.5 rounded-xl text-sm leading-relaxed ${
                  msg.role === 'user'
                    ? 'rounded-br-sm text-bg'
                    : 'rounded-bl-sm bg-surface border border-border text-text-primary'
                }`}
                style={msg.role === 'user' ? { background: 'linear-gradient(135deg, #00F2FE, #00C4CE)' } : {}}
              >
                {msg.role === 'user' ? (
                  <div className="prose prose-sm max-w-none">
                    <ReactMarkdown>{msg.content}</ReactMarkdown>
                  </div>
                ) : (
                  <div className="prose prose-sm prose-invert max-w-none prose-p:my-1 prose-a:text-blue prose-strong:text-blue-dim prose-headings:text-blue-dim prose-li:my-0.5">
                    <ReactMarkdown>{msg.content}</ReactMarkdown>
                  </div>
                )}
              </div>
            </div>
          ))}
          {isLoading && !messages.find(m => m.content.includes('⏳')) && (
            <div className="flex justify-start">
              <div className="bg-surface border border-border px-3 py-2.5 rounded-xl rounded-bl-sm flex items-center gap-2">
                <Loader2 size={14} className="text-blue animate-spin" />
                <span className="text-xs text-text-muted">Thinking…</span>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* File preview */}
        {selectedFile && (
          <div className="px-3 pb-0 pt-2 shrink-0">
            <FilePreview file={selectedFile} onRemove={() => { setSelectedFile(null); if (fileInputRef.current) fileInputRef.current.value = ''; }} />
          </div>
        )}

        {/* File error */}
        {fileError && (
          <div className="px-3 pb-0 pt-1 shrink-0">
            <p className="text-xs text-danger flex items-center gap-1">
              <AlertCircle size={12} /> {fileError}
            </p>
          </div>
        )}

        {/* Input Area */}
        <form onSubmit={handleSend} className="p-3 border-t border-border bg-surface shrink-0">
          <div className="flex gap-2 items-end">
            {/* Hidden file input */}
            <input
              ref={fileInputRef}
              type="file"
              accept={ACCEPT_ATTR}
              className="hidden"
              onChange={handleFileSelect}
            />
            {/* Attach button */}
            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              className="h-10 w-10 flex items-center justify-center text-text-muted hover:text-blue hover:bg-blue-glow border border-border rounded-lg transition-colors shrink-0"
              title={`Attach file (max ${MAX_FILE_MB} MB)`}
            >
              <Paperclip size={16} />
            </button>

            <input
              type="text"
              value={input}
              onChange={e => setInput(e.target.value)}
              placeholder={selectedFile ? 'Add a note (optional) then send…' : 'Ask about cyber news or incidents…'}
              className="input-dark flex-1 h-10 text-sm"
              disabled={isLoading}
            />

            <button
              type="submit"
              disabled={(!input.trim() && !selectedFile) || isLoading}
              className="h-10 w-10 flex items-center justify-center text-bg rounded-lg disabled:opacity-50 disabled:cursor-not-allowed transition-all shrink-0"
              style={{ background: 'linear-gradient(135deg, #00F2FE, #00C4CE)' }}
            >
              {isLoading ? <Loader2 size={16} className="animate-spin" /> : <Send size={15} />}
            </button>
          </div>
          <p className="text-[10px] text-text-muted mt-1.5 pl-12">
            Supports PDF, DOCX, TXT, CSV, JSON, images · Max {MAX_FILE_MB} MB
          </p>
        </form>
      </div>
    </>
  );
}
