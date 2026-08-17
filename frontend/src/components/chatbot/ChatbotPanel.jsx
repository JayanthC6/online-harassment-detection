import React, { useState, useEffect, useRef } from 'react';
import { MessageSquare, X, Send, Loader2, ShieldAlert } from 'lucide-react';
import ReactMarkdown from 'react-markdown';

export default function ChatbotPanel() {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState('');
  
  const messagesEndRef = useRef(null);

  // Initialize session
  useEffect(() => {
    let sid = localStorage.getItem('shieldai_chat_session');
    if (!sid) {
      sid = 'session_' + Math.random().toString(36).substr(2, 9);
      localStorage.setItem('shieldai_chat_session', sid);
    }
    setSessionId(sid);
    
    // Load history
    fetch(`http://localhost:5000/chat/${sid}`)
      .then(res => res.json())
      .then(data => {
        if (data.messages && data.messages.length > 0) {
          setMessages(data.messages);
        } else {
          setMessages([{
            role: 'assistant',
            content: 'Hello! I am your ShieldAI Cyber Assistant. How can I help you with cyber security, digital threats, or recent cyber news today?'
          }]);
        }
      })
      .catch(err => console.error("Failed to load chat history:", err));
  }, []);

  // Auto-scroll to bottom
  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, isOpen]);

  const handleSend = async (e) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMessage = input.trim();
    setInput('');
    setMessages(prev => [...prev, { role: 'user', content: userMessage }]);
    setIsLoading(true);

    try {
      const res = await fetch('http://localhost:5000/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: sessionId, message: userMessage })
      });
      const data = await res.json();
      
      if (res.ok) {
        setMessages(prev => [...prev, { role: 'assistant', content: data.response }]);
      } else {
        setMessages(prev => [...prev, { role: 'assistant', content: 'Error: ' + data.error }]);
      }
    } catch (err) {
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
        className={`fixed bottom-6 right-6 h-14 w-14 bg-blue hover:bg-blue-dim text-white rounded-full shadow-blue-lg flex items-center justify-center transition-transform z-50 ${isOpen ? 'scale-0' : 'scale-100 hover:scale-105'}`}
        aria-label="Open Cyber Assistant"
      >
        <MessageSquare size={24} />
      </button>

      {/* Chat Panel */}
      <div 
        className={`fixed bottom-6 right-6 w-[380px] max-w-[calc(100vw-2rem)] h-[550px] max-h-[calc(100vh-2rem)] bg-surface-2 border border-border rounded-xl shadow-panel flex flex-col z-50 transition-all duration-300 origin-bottom-right ${isOpen ? 'scale-100 opacity-100' : 'scale-90 opacity-0 pointer-events-none'}`}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-border bg-surface rounded-t-xl">
          <div className="flex items-center gap-2.5">
            <div className="h-8 w-8 rounded-full bg-blue-glow flex items-center justify-center text-blue">
              <ShieldAlert size={16} />
            </div>
            <div>
              <h3 className="text-sm font-bold text-text-primary">Cyber Assistant</h3>
              <p className="text-2xs text-blue flex items-center gap-1.5"><span className="w-1.5 h-1.5 rounded-full bg-blue animate-pulse"></span> Online</p>
            </div>
          </div>
          <button 
            onClick={() => setIsOpen(false)}
            className="p-1.5 text-text-muted hover:text-text-primary hover:bg-surface-3 rounded-md transition-colors"
          >
            <X size={18} />
          </button>
        </div>

        {/* Message List */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.map((msg, idx) => (
            <div key={idx} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div 
                className={`max-w-[85%] p-3 rounded-lg text-sm leading-relaxed ${
                  msg.role === 'user' 
                    ? 'bg-blue text-white rounded-br-sm' 
                    : 'bg-surface border border-border text-text-primary rounded-bl-sm'
                }`}
              >
                {msg.role === 'user' ? (
                  msg.content
                ) : (
                  <div className="prose prose-sm prose-invert max-w-none prose-p:my-1 prose-a:text-blue prose-strong:text-blue-dim">
                    <ReactMarkdown>{msg.content}</ReactMarkdown>
                  </div>
                )}
              </div>
            </div>
          ))}
          {isLoading && (
            <div className="flex justify-start">
              <div className="bg-surface border border-border p-3 rounded-lg rounded-bl-sm flex items-center gap-2">
                <Loader2 size={14} className="text-blue animate-spin" />
                <span className="text-xs text-text-muted">Analyzing...</span>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <form onSubmit={handleSend} className="p-3 border-t border-border bg-surface rounded-b-xl flex gap-2">
          <input 
            type="text" 
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask about cyber news or incidents..."
            className="input-dark flex-1 h-10 text-sm"
            disabled={isLoading}
          />
          <button 
            type="submit" 
            disabled={!input.trim() || isLoading}
            className="h-10 w-10 bg-blue hover:bg-blue-dim text-white rounded-lg flex items-center justify-center disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <Send size={16} className={input.trim() ? "translate-x-[-1px] translate-y-[1px]" : ""} />
          </button>
        </form>
      </div>
    </>
  );
}
