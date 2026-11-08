import React, { useState, useEffect, useRef } from 'react';
import {
  MessageSquare,
  Send,
  Loader2,
  ShieldAlert,
  Paperclip,
  FileText,
  Image as ImageIcon,
  X,
  Sparkles,
  UserCheck,
  Cpu,
  HelpCircle,
  AlertCircle
} from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import Card from '../common/Card';

const MAX_FILE_MB = 50;
const ALLOWED_EXTS = ['pdf', 'txt', 'md', 'log', 'csv', 'json', 'docx', 'png', 'jpg', 'jpeg', 'webp'];

export default function ChatPage({ role }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState('');
  const [selectedFile, setSelectedFile] = useState(null);
  const [fileError, setFileError] = useState('');
  const [chatMode, setChatMode] = useState(role && role !== 'User' ? 'analyst' : 'victim');

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
          setMessages([{
            role: 'assistant',
            content: chatMode === 'analyst'
              ? 'Hello! I am your **ShieldAI Cyber Safety Assistant** (SOC Analyst Mode).\n\nI provide structured forensic assessments, indicators of compromise (IoCs), attacker tactics, confidence levels, and legal context under the Information Technology Act.\n\nPaste suspicious content, headers, or threat text below to begin analysis.'
              : 'Hello! I am your **ShieldAI Cyber Safety Assistant** (Victim Support Mode).\n\nIf you are facing online harassment, blackmail, scams, or distressing messages, I am here to help you navigate this safely and calmly.\n\nYou can paste the message you received or ask me questions about next steps.'
          }]);
        }
      })
      .catch(() => {});
  }, [chatMode]);

  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages]);

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
    e?.preventDefault();
    if ((!input.trim() && !selectedFile) || isLoading) return;

    setIsLoading(true);
    setFileError('');

    // File upload
    if (selectedFile) {
      const file = selectedFile;
      setSelectedFile(null);
      if (fileInputRef.current) fileInputRef.current.value = '';

      setMessages(prev => [
        ...prev,
        { role: 'user', content: `📎 Uploaded: **${file.name}** (${(file.size / 1024 / 1024).toFixed(1)} MB)` },
        { role: 'assistant', content: '⏳ Reading and analyzing your file…' }
      ]);

      try {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('session_id', sessionId);
        formData.append('persona', chatMode);

        const res = await fetch('/chat/file', { method: 'POST', body: formData });
        const data = await res.json();

        setMessages(prev => {
          const updated = [...prev];
          updated[updated.length - 1] = {
            role: 'assistant',
            content: res.ok ? data.response : `Error: ${data.error}`,
            engine: data.engine || 'rules'
          };
          return updated;
        });
      } catch {
        setMessages(prev => {
          const updated = [...prev];
          updated[updated.length - 1] = { role: 'assistant', content: 'Network error while analyzing file.' };
          return updated;
        });
      } finally {
        setIsLoading(false);
      }
      return;
    }

    // Text message
    const userMessage = input.trim();
    setInput('');
    setMessages(prev => [...prev, { role: 'user', content: userMessage }]);

    try {
      const res = await fetch('/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          message: userMessage,
          persona: chatMode
        })
      });
      const data = await res.json();
      setMessages(prev => [
        ...prev,
        {
          role: 'assistant',
          content: res.ok ? data.response : `Error: ${data.error}`,
          engine: data.engine || 'rules'
        }
      ]);
    } catch {
      setMessages(prev => [
        ...prev,
        { role: 'assistant', content: 'Network error communicating with the chat service.' }
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleStarterPrompt = (promptText) => {
    setInput(promptText);
  };

  return (
    <div className="max-w-5xl mx-auto space-y-4 animate-fade-in pb-12">
      {/* ── Chat Header & Mode Switch ── */}
      <Card className="p-4 bg-surface/90 border border-border flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-blue/10 border border-blue/30 flex items-center justify-center text-blue shadow-[0_0_15px_rgba(0,242,254,0.2)]">
            <MessageSquare size={20} />
          </div>
          <div>
            <h2 className="text-base font-bold text-text-primary flex items-center gap-2">
              ShieldAI Safety Chatbot
            </h2>
            <p className="text-xs text-text-muted font-mono">
              Interactive cyber safety advisor with dual victim support & analyst intelligence modes
            </p>
          </div>
        </div>

        {/* Mode Selector */}
        <div className="flex items-center bg-black/40 p-1 rounded-xl border border-border/60 shrink-0">
          <button
            type="button"
            onClick={() => setChatMode('victim')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-mono font-semibold transition-all ${
              chatMode === 'victim'
                ? 'bg-cyan-500/20 text-cyan-400 border border-cyan-500/40 shadow-sm'
                : 'text-text-muted hover:text-text-primary'
            }`}
          >
            <UserCheck size={14} />
            Victim Mode
          </button>
          <button
            type="button"
            onClick={() => setChatMode('analyst')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-mono font-semibold transition-all ${
              chatMode === 'analyst'
                ? 'bg-purple-500/20 text-purple-400 border border-purple-500/40 shadow-sm'
                : 'text-text-muted hover:text-text-primary'
            }`}
          >
            <Cpu size={14} />
            Analyst Mode
          </button>
        </div>
      </Card>

      {/* ── Mode Explainer Banner ── */}
      <div className="px-4 py-2 rounded-lg bg-surface/40 border border-border/40 text-xs text-text-muted flex items-center gap-2">
        <Sparkles size={14} className={chatMode === 'analyst' ? 'text-purple-400' : 'text-cyan-400'} />
        <span>
          {chatMode === 'analyst'
            ? 'Analyst Mode active: Structured technical indicators, threat classification, IoCs, confidence scores, and legal provisions.'
            : 'Victim Mode active: Calm, supportive guidance, emergency numbers (112), helpline 1930, cybercrime.gov.in portal reporting, and step-by-step safety measures.'}
        </span>
      </div>

      {/* ── Conversation Stream Container ── */}
      <Card className="min-h-[500px] max-h-[640px] flex flex-col bg-surface/80 border border-border overflow-hidden">
        {/* Messages List */}
        <div className="flex-1 overflow-y-auto p-5 space-y-4">
          {messages.map((msg, idx) => (
            <div
              key={idx}
              className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-[85%] px-4 py-3 rounded-2xl text-sm leading-relaxed ${
                  msg.role === 'user'
                    ? 'rounded-br-sm text-white shadow-md'
                    : 'rounded-bl-sm bg-black/60 border border-border/60 text-text-primary shadow-inner'
                }`}
                style={
                  msg.role === 'user'
                    ? { background: 'linear-gradient(135deg, #00F2FE 0%, #0284c7 100%)' }
                    : {}
                }
              >
                <div className="prose prose-sm prose-invert max-w-none prose-p:my-1.5 prose-a:text-blue prose-strong:text-cyan-300 prose-headings:text-text-primary">
                  <ReactMarkdown>{msg.content}</ReactMarkdown>
                </div>

                {/* Engine Indicator */}
                {msg.engine && (
                  <div className="mt-2 pt-2 border-t border-border/40 flex items-center justify-between text-[11px] font-mono">
                    <span
                      className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded font-semibold ${
                        msg.engine === 'claude'
                          ? 'bg-purple-950/60 text-purple-300 border border-purple-800/40'
                          : 'bg-cyan-950/60 text-cyan-300 border border-cyan-800/40'
                      }`}
                    >
                      <span className={`w-1.5 h-1.5 rounded-full ${msg.engine === 'claude' ? 'bg-purple-400' : 'bg-cyan-400'}`} />
                      Engine: {msg.engine === 'claude' ? 'Claude 3.5' : 'Rule Engine Fallback'}
                    </span>
                  </div>
                )}
              </div>
            </div>
          ))}

          {isLoading && (
            <div className="flex justify-start">
              <div className="p-3 rounded-2xl rounded-bl-sm bg-black/60 border border-border text-text-muted flex items-center gap-2 text-xs font-mono">
                <Loader2 size={14} className="animate-spin text-blue" />
                ShieldAI is evaluating content...
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Quick Sample Questions (when messages count is low) */}
        {messages.length <= 2 && (
          <div className="px-5 py-3 bg-black/30 border-t border-border/40 flex flex-wrap gap-2 text-xs">
            <span className="text-text-muted font-mono flex items-center gap-1">Try asking:</span>
            {[
              "Someone emailed claiming they hacked my webcam and demanding $800 BTC. What should I do?",
              "Received an SMS: 'Your SBI account is blocked. Update KYC at http://sbi-kyc-verify.top immediately.'",
              "Is sharing private photos without consent punishable under the IT Act in India?"
            ].map((prompt, i) => (
              <button
                key={i}
                type="button"
                onClick={() => handleStarterPrompt(prompt)}
                className="px-2.5 py-1 rounded-md bg-surface border border-border/60 text-text-secondary hover:text-white hover:border-blue/40 text-[11px] transition-colors"
              >
                "{prompt.slice(0, 45)}..."
              </button>
            ))}
          </div>
        )}

        {/* Selected File Preview */}
        {selectedFile && (
          <div className="px-5 py-2 bg-black/40 border-t border-border/50 flex items-center justify-between text-xs font-mono">
            <div className="flex items-center gap-2 text-blue truncate">
              <FileText size={14} />
              <span className="truncate">{selectedFile.name}</span>
              <span className="text-text-muted">({(selectedFile.size / 1024 / 1024).toFixed(1)} MB)</span>
            </div>
            <button
              onClick={() => setSelectedFile(null)}
              className="text-text-muted hover:text-red-400"
            >
              <X size={14} />
            </button>
          </div>
        )}

        {fileError && (
          <div className="px-5 py-1.5 text-xs text-red-300 bg-red-950/40 border-t border-red-800/40 font-mono">
            {fileError}
          </div>
        )}

        {/* Input Bar */}
        <form onSubmit={handleSend} className="p-4 bg-black/50 border-t border-border flex items-center gap-2">
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileSelect}
            className="hidden"
            accept=".pdf,.txt,.md,.log,.csv,.json,.docx,.png,.jpg,.jpeg,.webp"
          />
          <button
            type="button"
            onClick={() => fileInputRef.current?.click()}
            className="p-2.5 rounded-lg text-text-muted hover:text-text-primary hover:bg-surface border border-border transition-colors cursor-pointer"
            title="Attach file or screenshot evidence"
            aria-label="Attach file"
          >
            <Paperclip size={18} />
          </button>

          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={
              chatMode === 'analyst'
                ? 'Paste threat data, headers, phishing SMS or ask an investigative question...'
                : 'Describe what happened or paste a message you are concerned about...'
            }
            className="input flex-1 py-2.5 text-xs"
            disabled={isLoading}
          />

          <button
            type="submit"
            disabled={(!input.trim() && !selectedFile) || isLoading}
            className="btn-primary px-4 py-2.5 rounded-lg flex items-center gap-1.5 text-xs font-mono font-bold disabled:opacity-40 cursor-pointer"
          >
            {isLoading ? <Loader2 size={16} className="animate-spin" /> : <Send size={16} />}
            <span>Send</span>
          </button>
        </form>
      </Card>
    </div>
  );
}

