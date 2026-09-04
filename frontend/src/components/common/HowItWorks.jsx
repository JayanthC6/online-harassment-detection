import React, { useState } from 'react';
import { ArrowLeft, Shield, AlertTriangle, Eye, HelpCircle, Phone, Globe, Loader2, Play, Search } from 'lucide-react';
import { apiClient } from '../../api/client';

export default function HowItWorks({ onBack, isLoggedIn }) {
  const [loadingId, setLoadingId] = useState(null);
  const [results, setResults] = useState({});
  const [error, setError] = useState(null);

  const [liveText, setLiveText] = useState('');
  const [liveResult, setLiveResult] = useState(null);
  const [isScanning, setIsScanning] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitSuccess, setSubmitSuccess] = useState(false);

  const handleLiveScan = async () => {
    if (!liveText.trim()) return;
    setIsScanning(true);
    setError(null);
    setLiveResult(null);
    setSubmitSuccess(false);
    
    try {
      const data = await apiClient('/predict', {
        method: 'POST',
        body: JSON.stringify({ text: liveText, persist: false })
      });
      setLiveResult(data);
    } catch (err) {
      setError(err.message || 'Failed to analyze');
    } finally {
      setIsScanning(false);
    }
  };

  const handleSubmitToAdmins = async () => {
    if (!liveText.trim() || !liveResult) return;
    setIsSubmitting(true);
    setError(null);
    
    try {
      await apiClient('/complaints', {
        method: 'POST',
        body: JSON.stringify({ text: liveText }),
      });
      setSubmitSuccess(true);
    } catch (err) {
      setError(err.message || 'Failed to submit complaint');
    } finally {
      setIsSubmitting(false);
    }
  };

  const DEMO_CARDS = [
    {
      id: "harassment_example",
      title: "Harassment",
      text: "Everyone would be better off if you just disappeared. We know you don't belong here, and soon everyone else will too."
    },
    {
      id: "phishing_example",
      title: "Phishing",
      text: "URGENT: Your account has been suspended for security reasons. Click here to verify your identity immediately: http://paypa1.com/account-verify-now"
    },
    {
      id: "threat_example",
      title: "Threat",
      text: "I know where you live. If you don't send me $5000 in Bitcoin by tomorrow, I will ruin your life and hurt your family."
    },
    {
      id: "clean_example",
      title: "Clean",
      text: "Hey, are we still meeting for lunch tomorrow at 12? Let me know!"
    }
  ];

  const handleAnalyze = async (example_id) => {
    setLoadingId(example_id);
    setError(null);
    try {
      const res = await fetch('/api/demo/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ example_id })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || 'Failed to analyze');
      
      setResults(prev => ({ ...prev, [example_id]: data }));
    } catch (err) {
      setError(err.message);
    } finally {
      setLoadingId(null);
    }
  };

  return (
    <div className="max-w-3xl mx-auto py-8 px-4 animate-fade-in">
      {onBack && (
        <button 
          onClick={onBack}
          className="flex items-center text-sm font-semibold text-text-muted hover:text-primary mb-6 transition-colors"
        >
          <ArrowLeft size={16} className="mr-1" /> Back to Login
        </button>
      )}

      <div className="card p-8">
        <h2 className="text-2xl font-bold text-text-primary mb-2 flex items-center gap-2">
          <HelpCircle className="text-primary" />
          Understanding ShieldAI
        </h2>
        <p className="text-text-secondary mb-8 leading-relaxed">
          ShieldAI is a digital safety triage platform designed to help organizations and analysts securely classify, prioritize, and investigate cyber threats.
        </p>

        <div className="space-y-8">
          {/* SECTION 1: The Process */}
          <section>
            <h3 className="text-lg font-bold text-text-primary border-b border-border pb-2 mb-4 flex items-center gap-2">
              <span className="bg-surface-3 text-text-primary rounded-full w-6 h-6 flex items-center justify-center text-xs">1</span>
              The Triage Pipeline
            </h3>
            <ul className="space-y-3 text-sm text-text-secondary list-disc pl-5">
              <li><strong>Data Ingestion:</strong> Incoming reports, texts, and multimodal content are securely ingested into the platform.</li>
              <li><strong>AI Analysis:</strong> Our hybrid neurosymbolic engine analyzes the content, identifying threat vectors (like phishing, hate speech, or harassment).</li>
              <li><strong>Scoring & Prioritization:</strong> Incidents are automatically assigned a severity score based on the risk detected, allowing analysts to focus on high-priority items.</li>
              <li><strong>Guided Investigation:</strong> Analysts use the dashboard and behavioral intel to track malicious actors and generate compliance-ready reports.</li>
            </ul>
          </section>

          {/* SECTION 2: Scope */}
          <section>
            <h3 className="text-lg font-bold text-text-primary border-b border-border pb-2 mb-4 flex items-center gap-2">
              <span className="bg-surface-3 text-text-primary rounded-full w-6 h-6 flex items-center justify-center text-xs">2</span>
              Supported Threat Categories
            </h3>
            <p className="text-sm text-text-secondary mb-3">ShieldAI's models are trained to detect and classify a wide range of digital threats, including:</p>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              <div className="bg-surface-2 p-3 rounded border border-border">
                <p className="font-semibold text-text-primary text-sm mb-1">Harassment & Bullying</p>
                <p className="text-xs text-text-muted">Targeted insults, sustained harassment, and severe cyberbullying.</p>
              </div>
              <div className="bg-surface-2 p-3 rounded border border-border">
                <p className="font-semibold text-text-primary text-sm mb-1">Threats</p>
                <p className="text-xs text-text-muted">Direct or implied threats of physical, emotional, or digital harm.</p>
              </div>
              <div className="bg-surface-2 p-3 rounded border border-border">
                <p className="font-semibold text-text-primary text-sm mb-1">Extortion & Blackmail</p>
                <p className="text-xs text-text-muted">Ransomware demands or threats of exposing private data (doxxing/sextortion).</p>
              </div>
              <div className="bg-surface-2 p-3 rounded border border-border">
                <p className="font-semibold text-text-primary text-sm mb-1">Phishing & Scams</p>
                <p className="text-xs text-text-muted">Fraudulent attempts to compromise credentials, including malicious URLs.</p>
              </div>
            </div>
          </section>

          {/* SECTION 3: Try It Live / Scanner */}
          <section>
            <h3 className="text-lg font-bold text-text-primary border-b border-border pb-2 mb-4 flex items-center gap-2">
              <span className="bg-surface-3 text-text-primary rounded-full w-6 h-6 flex items-center justify-center text-xs">3</span>
              {isLoggedIn ? 'Live Analysis Sandbox' : 'Try It Live'}
            </h3>
            <p className="text-sm text-text-secondary mb-4">
              {isLoggedIn 
                ? "Paste a text payload or email snippet below to see how the ShieldAI engine parses and classifies the content in real-time." 
                : "Select one of the examples below to see how our AI engine classifies content in real-time."}
              {!isLoggedIn && (
                <span className="ml-2 inline-flex items-center gap-1 bg-blue/20 text-blue px-2 py-0.5 rounded text-xs font-semibold">
                  <Play size={12} fill="currentColor" /> Live Analysis
                </span>
              )}
            </p>
            
            {error && (
              <div className="mb-4 p-3 bg-critical-bg border border-critical rounded text-sm text-critical">
                {error}
              </div>
            )}

            {isLoggedIn ? (
              <div className="bg-surface-2 p-4 rounded-lg border border-border">
                <textarea
                  value={liveText}
                  onChange={(e) => setLiveText(e.target.value)}
                  placeholder="Paste the harassing message, threat, or describe the incident here..."
                  className="input w-full h-24 resize-none mb-3"
                />
                <button
                  onClick={handleLiveScan}
                  disabled={isScanning || !liveText.trim()}
                  className="btn-primary flex items-center gap-2 w-full justify-center mb-4 disabled:opacity-50"
                >
                  {isScanning ? <Loader2 size={16} className="animate-spin" /> : <Search size={16} />}
                  {isScanning ? 'Scanning...' : 'Scan Now'}
                </button>

                {liveResult && (
                  <div className="mt-4 pt-4 border-t border-border animate-fade-in">
                    <div className="flex items-center gap-4 mb-3">
                      <span className={`badge ${
                          liveResult.primary_label === 'hate_speech' || liveResult.primary_label === 'threat' ? 'badge-danger' :
                          liveResult.primary_label === 'scam' || liveResult.primary_label === 'phishing' ? 'badge-critical' :
                          liveResult.primary_label === 'offensive_language' ? 'badge-warning' :
                          liveResult.primary_label === 'none' || liveResult.primary_label === 'clean' ? 'badge-success' : 'badge-muted'
                        } capitalize`}>
                        {(liveResult.primary_label || 'none').replace(/_/g, ' ')}
                      </span>
                      
                      <span className={`text-sm font-bold ${
                        liveResult.severity === 'Critical' ? 'text-critical' :
                        liveResult.severity === 'High' ? 'text-orange-500' :
                        liveResult.severity === 'Medium' ? 'text-yellow-500' :
                        'text-success'
                      }`}>
                        Severity: {liveResult.severity}
                      </span>
                    </div>

                    <div className="bg-surface-3 p-3 rounded text-sm text-text-primary flex items-start gap-2 mb-4">
                      <Shield size={16} className="text-primary shrink-0 mt-0.5" />
                      <div>
                        <span className="font-semibold block mb-0.5">Recommended Action:</span>
                        <span className="text-text-secondary">{liveResult.guidance_snippet}</span>
                      </div>
                    </div>

                  </div>
                )}
              </div>
            ) : (
              <div className="space-y-4">
                {DEMO_CARDS.map(card => {
                  const res = results[card.id];
                  const isLoading = loadingId === card.id;

                  return (
                    <div key={card.id} className="bg-surface-2 p-4 rounded-lg border border-border">
                      <div className="flex justify-between items-start gap-4 mb-3">
                        <div>
                          <p className="font-semibold text-text-primary text-sm mb-1">{card.title} Example</p>
                          <p className="text-sm text-text-muted italic">"{card.text}"</p>
                        </div>
                        <button 
                          onClick={() => handleAnalyze(card.id)}
                          disabled={isLoading}
                          className="btn-primary text-xs py-1.5 px-3 whitespace-nowrap flex items-center gap-1 disabled:opacity-50"
                        >
                          {isLoading ? <Loader2 size={14} className="animate-spin" /> : <Play size={14} fill="currentColor" />}
                          {isLoading ? 'Analyzing...' : 'Analyze'}
                        </button>
                      </div>

                      {res && (
                        <div className="mt-3 pt-3 border-t border-border animate-fade-in">
                          <div className="flex items-center gap-4 mb-2">
                            <span className={`badge ${
                                res.primary_label === 'hate_speech' || res.primary_label === 'threat' ? 'badge-danger' :
                                res.primary_label === 'scam' || res.primary_label === 'phishing' ? 'badge-critical' :
                                res.primary_label === 'offensive_language' ? 'badge-warning' :
                                res.primary_label === 'none' || res.primary_label === 'clean' ? 'badge-success' : 'badge-muted'
                              } capitalize`}>
                              {(res.primary_label || 'none').replace(/_/g, ' ')}
                            </span>
                            
                            <span className={`text-xs font-semibold ${
                              res.severity === 'Critical' ? 'text-critical' :
                              res.severity === 'High' ? 'text-orange-500' :
                              res.severity === 'Medium' ? 'text-yellow-500' :
                              'text-success'
                            }`}>
                              Severity: {res.severity}
                            </span>
                          </div>
                          <div className="bg-surface-3 p-3 rounded text-sm text-text-primary flex items-start gap-2">
                            <Shield size={16} className="text-primary shrink-0 mt-0.5" />
                            <div>
                              <span className="font-semibold block mb-0.5">Recommended Action:</span>
                              <span className="text-text-secondary">{res.guidance_snippet}</span>
                            </div>
                          </div>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            )}
          </section>
        </div>
      </div>
    </div>
  );
}
