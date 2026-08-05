import { useState } from 'react'
import AnalyzeForm from './components/AnalyzeForm'
import ScreenshotAnalyzeForm from './components/ScreenshotAnalyzeForm'
import Dashboard from './components/Dashboard'
import LoginForm from './components/auth/LoginForm'
import { useAuth } from './hooks/useAuth'

const TABS = [
  { id: 'analyze', label: '🔍 Analyze' },
  { id: 'dashboard', label: '📊 Dashboard' },
]

export default function App() {
  const [activeTab, setActiveTab] = useState('analyze')
  const [refreshKey, setRefreshKey] = useState(0)
  const { token, login, logout } = useAuth()

  return (
    <div className="min-h-screen py-8 px-4 sm:px-6">
      <div className="max-w-3xl mx-auto space-y-6">

        {/* ── Header ── */}
        <header className="text-center space-y-2 pt-4 pb-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <span className="text-3xl">🛡️</span>
              <h1 className="text-2xl font-bold text-gray-900">
                ShieldAI
              </h1>
            </div>
            {token && (
              <button
                onClick={logout}
                className="text-sm px-3 py-1.5 text-gray-600 hover:text-gray-900 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors"
              >
                Sign Out
              </button>
            )}
          </div>
          <p className="text-sm text-gray-500 max-w-md mx-auto">
            AI-powered harassment detection — paste text or upload audio to analyze for hate speech, threats, and offensive language.
          </p>
        </header>

        {/* ── Tab navigation ── */}
        <nav className="flex justify-center gap-1 border-b border-gray-200 pb-0">
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
            <>
              <AnalyzeForm onNewResult={() => setRefreshKey((k) => k + 1)} />
              <ScreenshotAnalyzeForm onNewResult={() => setRefreshKey((k) => k + 1)} />
            </>
          )}
          {activeTab === 'dashboard' && (
            token ? (
              <Dashboard refreshKey={refreshKey} />
            ) : (
              <LoginForm onLogin={login} />
            )
          )}
        </main>

        {/* ── Footer ── */}
        <footer className="text-center text-xs text-gray-400 pt-6 pb-4 space-y-1">
          <p>Built with TF-IDF + Logistic Regression · DistilBERT · Whisper · EasyOCR</p>
          <p className="text-gray-300">Online Harassment Detection System</p>
        </footer>
      </div>
    </div>
  )
}
