import re

# 1. Patch SearchFilters.jsx
p1 = "frontend/src/components/dashboard/SearchFilters.jsx"
with open(p1, "r", encoding="utf-8") as f:
    text = f.read()

pattern = r'<option value="">All Categories</option>[\s\S]*?<option value="none">Safe</option>'
replacement = """<option value="">All Categories</option>
          <option value="clean">Clean / Safe</option>
          <option value="harassment">Harassment</option>
          <option value="threat">Threat</option>
          <option value="sextortion">Sextortion</option>
          <option value="phishing">Phishing</option>
          <option value="scam">Scam</option>
          <option value="abusive_language">Abusive Language</option>
          <option value="unsupported">Unsupported Language</option>"""

new_text, n = re.subn(pattern, replacement, text)
if n == 1:
    with open(p1, "w", encoding="utf-8") as f:
        f.write(new_text)
    print("SearchFilters.jsx updated")
else:
    print(f"Warning: pattern matched {n} times in SearchFilters.jsx")

# 2. Patch ModeratorQueue.jsx
p2 = "frontend/src/components/dashboard/ModeratorQueue.jsx"
with open(p2, "r", encoding="utf-8") as f:
    text2 = f.read()

# Update category badges and risk score display for unsupported
old_queue_badge = """                        <span className={`badge ${r.category === 'hate_speech' || r.category === 'threat' ? 'badge-danger' :
                            r.category === 'scam' || r.category === 'phishing' ? 'badge-critical' :
                              r.category === 'offensive_language' ? 'badge-warning' :
                                r.category === 'none' || r.category === 'clean' ? 'badge-success' : 'badge-muted'
                          } capitalize`}>
                          {(r.category || 'unknown').replace(/_/g, ' ')}
                        </span>
                      </td>
                      <td className="px-5 py-3">
                        <span className={`${r.risk_score >= 80 ? 'score-critical' :
                            r.risk_score >= 55 ? 'score-high' :
                              r.risk_score >= 30 ? 'score-medium' : 'score-low'
                          }`}>{Math.round(r.risk_score)}</span>"""

new_queue_badge = """                        <span className={`badge ${
                            r.category === 'unsupported' || r.severity_tier === 'Unsupported' || r.risk_level === 'unsupported' ? 'bg-purple-900/40 text-purple-300 border border-purple-500/40' :
                            r.category === 'threat' || r.category === 'sextortion' ? 'badge-danger' :
                            r.category === 'scam' || r.category === 'phishing' ? 'badge-critical' :
                            r.category === 'abusive_language' || r.category === 'harassment' ? 'badge-warning' :
                            r.category === 'none' || r.category === 'clean' ? 'badge-success' : 'badge-muted'
                          } capitalize`}>
                          {r.category === 'unsupported' || r.severity_tier === 'Unsupported' ? 'Unsupported' : (r.category || 'unknown').replace(/_/g, ' ')}
                        </span>
                      </td>
                      <td className="px-5 py-3">
                        {r.category === 'unsupported' || r.severity_tier === 'Unsupported' || r.risk_level === 'unsupported' ? (
                          <span className="text-purple-400 font-mono text-xs font-semibold px-1.5 py-0.5 rounded bg-purple-500/10 border border-purple-500/20">UNVERIFIED</span>
                        ) : (
                          <span className={`${r.risk_score >= 80 ? 'score-critical' :
                              r.risk_score >= 55 ? 'score-high' :
                                r.risk_score >= 30 ? 'score-medium' : 'score-low'
                            }`}>{Math.round(r.risk_score)}</span>
                        )}"""

if old_queue_badge in text2:
    text2 = text2.replace(old_queue_badge, new_queue_badge)
    with open(p2, "w", encoding="utf-8") as f:
        f.write(text2)
    print("ModeratorQueue.jsx updated successfully")
else:
    print("Note: old_queue_badge exact match not found in ModeratorQueue.jsx")

