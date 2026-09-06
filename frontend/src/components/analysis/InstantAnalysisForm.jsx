import { useState } from 'react';
import { apiClient } from '../../api/client';
import { MessageSquare, AlertTriangle, ShieldCheck } from 'lucide-react';
import ResultDisplay from '../ResultDisplay';

export default function InstantAnalysisForm({ onNewResult }) {
  const [text, setText] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [result, setResult] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!text) {
      setError('Please provide text to analyze.');
      return;
    }
    setError('');
    setResult(null);
    setLoading(true);

    try {
      const data = await apiClient('/predict/instant', {
        method: 'POST',
        body: JSON.stringify({ text }),
      });
      
      setResult(data);
      if (onNewResult) onNewResult();
      
    } catch (err) {
      setError(err.message || 'An error occurred while analyzing the text.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="max-w-3xl mx-auto card overflow-hidden shadow-neon animate-fade-in">
        <div className="px-6 py-5 border-b border-border bg-surface-solid">
          <h3 className="font-bold text-text-primary flex items-center gap-2">
            <ShieldCheck className="text-blue" size={20} />
            Instant Content Analysis
          </h3>
          <p className="text-sm text-text-muted mt-1">
            Check messages or text for digital safety threats. 
          </p>
          <div className="mt-3 p-3 bg-blue-muted/30 border-l-4 border-blue text-sm text-text-secondary">
            <strong>Disclaimer:</strong> This tool provides automated guidance only, is not a substitute for reporting to official resources, and no one reviews or acts on what you paste here.
          </div>
        </div>
        
        <div className="p-6">
          <form onSubmit={handleSubmit} className="space-y-6">
            {error && (
              <div className="p-3 bg-critical-bg border-l-4 border-critical text-critical text-sm">
                {error}
              </div>
            )}
            
            <div>
              <label className="block text-sm font-bold text-text-primary mb-2 flex items-center gap-2">
                <MessageSquare size={16} className="text-text-muted" />
                Text to Analyze
              </label>
              <textarea
                value={text}
                onChange={(e) => setText(e.target.value)}
                placeholder="Paste the message or content you want to check..."
                className="input w-full h-32 resize-none"
              />
            </div>
            
            <div className="pt-4 border-t border-border flex justify-end">
              <button
                type="submit"
                disabled={loading || !text}
                className="btn-primary"
              >
                {loading ? 'Analyzing...' : 'Analyze Now'}
              </button>
            </div>
          </form>
        </div>
      </div>

      {result && (
        <div className="max-w-3xl mx-auto space-y-6 animate-fade-in mb-6">
           <ResultDisplay 
              result={result} 
              onFeedback={() => {}} 
              detailed={true} 
           />
        </div>
      )}

      {/* Persistent Crisis Resources Footer (Always Visible) */}
      <div className="max-w-3xl mx-auto border border-blue/30 bg-blue-muted/10 rounded-lg p-5 flex gap-3 shadow-sm mt-6">
        <div className="flex-shrink-0 mt-0.5">
          <AlertTriangle size={20} className="text-blue" />
        </div>
        <div className="space-y-2 w-full">
          <p className="text-sm font-bold text-text-primary">Need Immediate Help?</p>
          <p className="text-sm text-text-secondary leading-relaxed">
            AI classification is not perfect. Regardless of the analysis above, if you feel unsafe or are experiencing cyber harassment, extortion, or abuse, help is available.
          </p>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mt-3">
            <div className="bg-surface-solid p-3 rounded border border-border">
              <p className="text-xs font-semibold text-text-muted uppercase tracking-wider mb-1">National Cyber Crime</p>
              <p className="text-sm font-mono font-bold text-text-primary flex items-center gap-2">
                1930
              </p>
              <a href="https://cybercrime.gov.in" target="_blank" rel="noopener noreferrer" className="text-xs text-blue hover:underline mt-1 inline-block">
                cybercrime.gov.in
              </a>
            </div>
            <div className="bg-surface-solid p-3 rounded border border-border">
              <p className="text-xs font-semibold text-text-muted uppercase tracking-wider mb-1">Women's Helpline</p>
              <p className="text-sm font-mono font-bold text-text-primary flex items-center gap-2">
                181
              </p>
              <p className="text-xs text-text-muted mt-1">Available 24/7</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
