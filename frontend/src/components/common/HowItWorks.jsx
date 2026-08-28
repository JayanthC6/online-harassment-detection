import React, { useState } from 'react';
import { ArrowLeft, Shield, AlertTriangle, Eye, HelpCircle, Phone, Globe, Loader2, Play } from 'lucide-react';

export default function HowItWorks({ onBack }) {
  const [loadingId, setLoadingId] = useState(null);
  const [results, setResults] = useState({});
  const [error, setError] = useState(null);

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
          ShieldAI is a digital safety triage platform designed to help organizations and individuals securely report and analyze cyber threats.
        </p>

        <div className="space-y-8">
          {/* SECTION 1: The Process */}
          <section>
            <h3 className="text-lg font-bold text-text-primary border-b border-border pb-2 mb-4 flex items-center gap-2">
              <span className="bg-surface-3 text-text-primary rounded-full w-6 h-6 flex items-center justify-center text-xs">1</span>
              The Process
            </h3>
            <ul className="space-y-3 text-sm text-text-secondary list-disc pl-5">
              <li><strong>Submit a Complaint:</strong> Provide details and any evidence (like screenshots or text logs) of the incident.</li>
              <li><strong>AI Analysis:</strong> Our system automatically analyzes the content, identifies potential threat categories, and assigns a preliminary severity level.</li>
              <li><strong>Analyst Review Queue:</strong> Your complaint is added to a secure queue for human review by our authorized analysts.</li>
              <li><strong>Status Tracking:</strong> You can check your "My Tickets" tab to view the AI-generated severity and any recommended guidance actions.</li>
            </ul>
          </section>

          {/* SECTION 2: Scope */}
          <section>
            <h3 className="text-lg font-bold text-text-primary border-b border-border pb-2 mb-4 flex items-center gap-2">
              <span className="bg-surface-3 text-text-primary rounded-full w-6 h-6 flex items-center justify-center text-xs">2</span>
              What Can Be Reported?
            </h3>
            <p className="text-sm text-text-secondary mb-3">You can report various forms of digital harassment and online threats, including but not limited to:</p>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              <div className="bg-surface-2 p-3 rounded border border-border">
                <p className="font-semibold text-text-primary text-sm mb-1">Harassment & Bullying</p>
                <p className="text-xs text-text-muted">Repeated unwanted contact, targeted insults, or coordinated harassment.</p>
              </div>
              <div className="bg-surface-2 p-3 rounded border border-border">
                <p className="font-semibold text-text-primary text-sm mb-1">Threats</p>
                <p className="text-xs text-text-muted">Direct or implied threats of physical, emotional, or digital harm.</p>
              </div>
              <div className="bg-surface-2 p-3 rounded border border-border">
                <p className="font-semibold text-text-primary text-sm mb-1">Extortion & Blackmail</p>
                <p className="text-xs text-text-muted">Demanding money or actions under threat of exposing private information.</p>
              </div>
              <div className="bg-surface-2 p-3 rounded border border-border">
                <p className="font-semibold text-text-primary text-sm mb-1">Phishing & Scams</p>
                <p className="text-xs text-text-muted">Fraudulent attempts to steal credentials, money, or identity.</p>
              </div>
            </div>
          </section>

          {/* SECTION 3: Try It Live */}
          <section>
            <h3 className="text-lg font-bold text-text-primary border-b border-border pb-2 mb-4 flex items-center gap-2">
              <span className="bg-surface-3 text-text-primary rounded-full w-6 h-6 flex items-center justify-center text-xs">3</span>
              Try It Live
            </h3>
            <p className="text-sm text-text-secondary mb-4">
              Select one of the examples below to see how our AI engine classifies content in real-time. 
              <span className="ml-2 inline-flex items-center gap-1 bg-blue/20 text-blue px-2 py-0.5 rounded text-xs font-semibold">
                <Play size={12} fill="currentColor" /> Live Analysis
              </span>
            </p>
            
            {error && (
              <div className="mb-4 p-3 bg-critical-bg border border-critical rounded text-sm text-critical">
                {error}
              </div>
            )}

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
          </section>

          {/* SECTION 4: Honest Limitations */}
          <section className="bg-critical-bg/20 border border-critical/30 rounded-lg p-5">
            <h3 className="text-lg font-bold text-critical flex items-center gap-2 mb-3">
              <AlertTriangle size={20} />
              Platform Limitations & Emergencies
            </h3>
            <p className="text-sm text-text-primary font-medium mb-2">
              This platform is NOT a substitute for emergency services.
            </p>
            <ul className="space-y-2 text-sm text-text-secondary list-disc pl-5 mb-4">
              <li><strong>No Real-time Monitoring:</strong> The system does not have 24/7 human monitoring.</li>
              <li><strong>No Guaranteed Response Times:</strong> Review and action on your complaint may take time depending on the organization's queue.</li>
              <li><strong>No Direct Law Enforcement Coordination:</strong> Filing a report here does not automatically dispatch police.</li>
            </ul>
            <div className="bg-critical/10 p-3 rounded-md border-l-4 border-critical">
              <p className="text-sm text-critical font-bold">
                Action Required: If you are in immediate danger or need urgent help, do not wait for a response here — contact the resources below or local emergency services directly first.
              </p>
            </div>
          </section>

          {/* SECTION 5: Privacy */}
          <section>
            <h3 className="text-lg font-bold text-text-primary border-b border-border pb-2 mb-4 flex items-center gap-2">
              <Eye className="text-primary" size={20} />
              Privacy & Data Handling
            </h3>
            <p className="text-sm text-text-secondary mb-2">
              We take your data seriously. Here is exactly what happens to the information you submit:
            </p>
            <ul className="space-y-2 text-sm text-text-secondary list-disc pl-5">
              <li><strong>Secure Storage:</strong> Your complaint details and evidence are stored securely in our database.</li>
              <li><strong>Authorized Access Only:</strong> Submitted data is visible ONLY to you and authorized organizational analysts/moderators reviewing the queue.</li>
              <li><strong>No End-to-End Encryption:</strong> While stored securely, data is not end-to-end encrypted or fully anonymized, as moderators need to view the evidence to provide assistance.</li>
            </ul>
          </section>

          {/* SECTION 6: Critical Resources */}
          <section>
            <h3 className="text-lg font-bold text-text-primary border-b border-border pb-2 mb-4 flex items-center gap-2">
              <Shield className="text-success" size={20} />
              Independent Critical Resources
            </h3>
            <p className="text-sm text-text-secondary mb-4">
              You can also contact these resources directly, any time, independent of filing a complaint here:
            </p>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="bg-surface-2 p-4 rounded-lg border border-border flex gap-3">
                <div className="bg-success/20 p-2 rounded-full h-fit">
                  <Phone size={18} className="text-success" />
                </div>
                <div>
                  <h4 className="font-bold text-text-primary text-sm mb-1">National Cyber Crime Reporting Portal</h4>
                  <p className="text-xs text-text-muted mb-2">For immediate assistance regarding cybercrime, financial fraud, or severe online threats.</p>
                  <p className="text-xs font-mono font-bold text-success flex items-center gap-1">
                    Call: 1930 <span className="text-text-muted font-sans font-normal">(24/7 helpline by I4C, MHA)</span>
                  </p>
                  <a href="https://cybercrime.gov.in" target="_blank" rel="noopener noreferrer" className="text-xs text-blue hover:underline flex items-center gap-1 mt-1">
                    <Globe size={12} /> cybercrime.gov.in
                  </a>
                </div>
              </div>

              <div className="bg-surface-2 p-4 rounded-lg border border-border flex gap-3">
                <div className="bg-blue-muted p-2 rounded-full h-fit border border-blue/20">
                  <Phone size={18} className="text-blue" />
                </div>
                <div>
                  <h4 className="font-bold text-text-primary text-sm mb-1">National Women Helpline</h4>
                  <p className="text-xs text-text-muted mb-2">24/7 emergency and non-emergency support for women.</p>
                  <p className="text-xs font-mono font-bold text-blue">Call: 181</p>
                </div>
              </div>
            </div>
          </section>
        </div>
      </div>
    </div>
  );
}
