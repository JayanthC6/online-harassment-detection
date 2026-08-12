import { useState } from 'react'
import { ShieldCheck, BarChart3, Search } from 'lucide-react'
import AnalyzeForm from './components/AnalyzeForm'
import ScreenshotAnalyzeForm from './components/ScreenshotAnalyzeForm'
import Dashboard from './components/Dashboard'

const TABS = [
  { id: 'analyze', label: 'Analyze', icon: Search },
  { id: 'dashboard', label: 'Dashboard', icon: BarChart3 },
]

export default function App() {
  const [activeTab, setActiveTab] = useState('analyze')
  const [refreshKey, setRefreshKey] = useState(0)

  return (
    <div className="min-h-screen py-10 px-4 sm:px-6">
      <div className="max-w-4xl mx-auto space-y-8">

        {/* ── Header ── */}
        <header className="flex flex-col md:flex-row md:items-end justify-between gap-4">
          <div>
            <div className="flex items-center gap-3">
              <div className="p-2 bg-panel border border-slate-700 rounded-none text-off-white">
                <ShieldCheck size={28} strokeWidth={2.5} />
              </div>
              <h1 className="text-2xl font-bold font-display uppercase tracking-wider text-off-white">
                ShieldAI Forensic Console
              </h1>
            </div>
            <p className="text-sm text-slate-400 font-mono mt-2">
              Intelligent moderation workspace for text, audio, and visual content.
            </p>
          </div>
          
          {/* ── Tab navigation ── */}
          <nav className="flex gap-2 border-b border-slate-700 pb-0">
            {TABS.map((tab) => {
              const Icon = tab.icon;
              const isActive = activeTab === tab.id;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex items-center gap-2 tab-btn ${isActive ? 'active' : ''}`}
                >
                  <Icon size={16} className={isActive ? 'text-off-white' : 'text-slate-400'} />
                  {tab.label}
                </button>
              );
            })}
          </nav>
        </header>

        {/* ── Content ── */}
        <main className="animate-fade-in">
          {activeTab === 'analyze' && (
            <>
              <AnalyzeForm onNewResult={() => setRefreshKey((k) => k + 1)} />
              <ScreenshotAnalyzeForm onNewResult={() => setRefreshKey((k) => k + 1)} />
            </>
          )}
          {activeTab === 'dashboard' && (
            <Dashboard refreshKey={refreshKey} />
          )}
        </main>

        {/* ── Footer ── */}
        <footer className="text-center text-xs text-slate-500 font-mono pt-6 pb-4 space-y-1">
          <p>Built with TF-IDF + Logistic Regression · DistilBERT · Whisper · EasyOCR</p>
          <p className="text-slate-400 uppercase tracking-wider">Online Harassment Detection System</p>
        </footer>
      </div>
    </div>
  )
}
