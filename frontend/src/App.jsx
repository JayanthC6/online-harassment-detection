import { useState } from 'react'
import AnalyzeForm from './components/AnalyzeForm'
import Dashboard from './components/Dashboard'

const TABS = [
  { id: 'analyze', label: '🔍 Analyze', icon: null },
  { id: 'dashboard', label: '📊 Dashboard', icon: null },
]

export default function App() {
  const [activeTab, setActiveTab] = useState('analyze')
  const [refreshKey, setRefreshKey] = useState(0)

  return (
    <div className="min-h-screen py-6 px-4 sm:px-6">
      <div className="max-w-3xl mx-auto space-y-6">

        {/* ── Header ── */}
        <header className="text-center space-y-2 pt-4 pb-2">
          <div className="flex items-center justify-center gap-3">
            <span className="text-3xl">🛡️</span>
            <h1 className="text-2xl font-bold bg-gradient-to-r from-indigo-400 via-purple-400 to-indigo-300 bg-clip-text text-transparent">
              ShieldAI
            </h1>
          </div>
          <p className="text-sm text-gray-500 max-w-md mx-auto">
            AI-powered harassment detection — paste text or upload audio to analyze for hate speech, threats, and offensive language.
          </p>
        </header>

        {/* ── Tab navigation ── */}
        <nav className="flex justify-center gap-1 border-b border-white/[0.06] pb-0">
          {TABS.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`tab-btn ${activeTab === tab.id ? 'active' : ''}`}
            >
              {tab.label}
            </button>
          ))}
        </nav>

        {/* ── Content ── */}
        <main className="animate-fade-in">
          {activeTab === 'analyze' && (
            <AnalyzeForm onNewResult={() => setRefreshKey((k) => k + 1)} />
          )}
          {activeTab === 'dashboard' && (
            <Dashboard refreshKey={refreshKey} />
          )}
        </main>

        {/* ── Footer ── */}
        <footer className="text-center text-xs text-gray-600 pt-6 pb-4 space-y-1">
          <p>Built with TF-IDF + Logistic Regression · DistilBERT · Whisper</p>
          <p className="text-gray-700">Online Harassment Detection System</p>
        </footer>
      </div>
    </div>
  )
}
