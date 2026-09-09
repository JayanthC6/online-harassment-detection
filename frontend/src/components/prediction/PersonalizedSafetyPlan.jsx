import React, { useState } from 'react';
import PropTypes from 'prop-types';
import { ShieldAlert, CheckCircle, FileText, Lock, AlertTriangle, ArrowRight } from 'lucide-react';
import Card from '../common/Card';
import EvidenceViewer from './EvidenceViewer';

export default function PersonalizedSafetyPlan({ result }) {
  const plan = result?.evidence_plan;
  
  // Local state for evidence readiness tracking (client-side only)
  const [checkedItems, setCheckedItems] = useState({});

  React.useEffect(() => {
    if (plan) {
      window.dispatchEvent(new CustomEvent('setChatbotPredictionContext', { detail: result }));
    }
    return () => {
      window.dispatchEvent(new CustomEvent('setChatbotPredictionContext', { detail: null }));
    };
  }, [plan, result]);

  if (!plan) return null;

  const toggleCheck = (idx) => {
    setCheckedItems(prev => ({
      ...prev,
      [idx]: !prev[idx]
    }));
  };

  return (
    <div className="space-y-6 mt-8 animate-slide-up">
      <div className="flex items-center gap-3 border-b border-border pb-4">
        <ShieldAlert className="text-blue" size={24} />
        <h2 className="text-lg font-semibold text-text-primary">Personalized Safety & Evidence Plan</h2>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Left Column: Summary and Evidence */}
        <div className="space-y-6">
          <Card className="border-blue/30 bg-blue-muted/10">
            <h3 className="text-sm font-semibold text-blue mb-2 flex items-center gap-2">
              <AlertTriangle size={16} />
              Case Summary
            </h3>
            <p className="text-lg font-bold text-text-primary mb-1">{plan.case_summary}</p>
            <p className="text-sm text-text-secondary">{plan.why_flagged}</p>
          </Card>

          <Card>
            <h3 className="text-sm font-semibold text-text-primary mb-4 flex items-center gap-2">
              <FileText size={16} className="text-warning" />
              Evidence to Preserve
            </h3>
            {plan.evidence_checklist?.length > 0 ? (
              <div className="space-y-3">
                {plan.evidence_checklist.map((item, idx) => (
                  <label key={idx} className="flex items-start gap-3 cursor-pointer group">
                    <div className="relative flex items-center justify-center mt-0.5">
                      <input 
                        type="checkbox" 
                        className="peer sr-only"
                        checked={!!checkedItems[idx]}
                        onChange={() => toggleCheck(idx)}
                      />
                      <div className="w-4 h-4 border border-border rounded bg-surface peer-checked:bg-blue peer-checked:border-blue transition-colors"></div>
                      <CheckCircle size={12} className="absolute text-background opacity-0 peer-checked:opacity-100 transition-opacity" />
                    </div>
                    <span className={`text-sm select-none transition-colors ${checkedItems[idx] ? 'text-text-muted line-through' : 'text-text-secondary group-hover:text-text-primary'}`}>
                      {item}
                    </span>
                  </label>
                ))}
              </div>
            ) : (
              <p className="text-sm text-text-muted italic">No specific evidence items identified.</p>
            )}
          </Card>

          <Card>
            <h3 className="text-sm font-semibold text-text-primary mb-4 flex items-center gap-2">
              <Lock size={16} className="text-blue" />
              Evidence Preservation Guidance
            </h3>
            <ul className="space-y-2">
              {plan.preservation_guidance?.map((item, idx) => (
                <li key={idx} className="text-sm text-text-secondary flex items-start gap-2">
                  <span className="text-blue mt-1">•</span>
                  <span>{item}</span>
                </li>
              ))}
              {(!plan.preservation_guidance || plan.preservation_guidance.length === 0) && (
                <li className="text-sm text-text-muted italic">No preservation guidance available.</li>
              )}
            </ul>
          </Card>
        </div>

        {/* Right Column: Actions and Viewer */}
        <div className="space-y-6">
          <Card className={result.severity_tier === 'Safe' ? "border-success/30 bg-success/5" : "border-danger/30 bg-danger/5"}>
            <h3 className={`text-sm font-semibold mb-4 flex items-center gap-2 ${result.severity_tier === 'Safe' ? 'text-success' : 'text-danger'}`}>
              {result.severity_tier === 'Safe' ? <CheckCircle size={16} /> : <ShieldAlert size={16} />}
              Immediate Safety Actions
            </h3>
            <ul className="space-y-3">
              {plan.safety_actions?.map((item, idx) => (
                <li key={idx} className="text-sm text-text-primary flex items-start gap-2 bg-background p-2 rounded border border-border/50">
                  <ArrowRight size={14} className={`${result.severity_tier === 'Safe' ? 'text-success' : 'text-danger'} mt-0.5 shrink-0`} />
                  <span className="leading-snug">{item}</span>
                </li>
              ))}
              {(!plan.safety_actions || plan.safety_actions.length === 0) && (
                <li className="text-sm text-text-muted italic">No immediate safety actions required.</li>
              )}
            </ul>
          </Card>

          <Card>
            <h3 className="text-sm font-semibold text-text-primary mb-4 flex items-center gap-2">
              <CheckCircle size={16} className="text-success" />
              Recommended Next Steps
            </h3>
            <ul className="space-y-2">
              {plan.recommended_steps?.map((item, idx) => (
                <li key={idx} className="text-sm text-text-secondary flex items-start gap-2">
                  <span className="text-success font-bold mt-0.5">{(idx + 1).toString()}.</span>
                  <span>{item}</span>
                </li>
              ))}
              {(!plan.recommended_steps || plan.recommended_steps.length === 0) && (
                <li className="text-sm text-text-muted italic">No recommended steps identified.</li>
              )}
            </ul>
          </Card>
        </div>
      </div>

      <EvidenceViewer result={result} />
    </div>
  );
}

PersonalizedSafetyPlan.propTypes = {
  result: PropTypes.object.isRequired,
};
