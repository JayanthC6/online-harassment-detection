import { useState } from 'react'
import AnalyzeForm from './components/AnalyzeForm'
import ScreenshotAnalyzeForm from './components/ScreenshotAnalyzeForm'
import Dashboard from './components/Dashboard'
import Header from './components/Header'
import Sidebar from './components/Sidebar'

export default function App() {
  const [activeTab, setActiveTab] = useState('analyze')
  const [refreshKey, setRefreshKey] = useState(0)

  return (
    <div className="text-on-background font-body-md text-body-md antialiased overflow-x-hidden selection:bg-primary-fixed selection:text-on-primary-fixed">
      {/* ── TopAppBar ── */}
      <Header activeTab={activeTab} setActiveTab={setActiveTab} />
      
      {/* ── SideNavBar ── */}
      <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} />

      {/* ── Main Content Canvas ── */}
      <main className="md:ml-64 pt-24 pb-20 px-margin max-w-container-max mx-auto min-h-screen flex flex-col gap-gutter">
        {activeTab === 'analyze' && (
          <div className="animate-fade-in space-y-8">
            <header className="flex items-end justify-between border-b border-outline-variant/30 pb-4 mb-4">
              <div>
                <h1 className="font-headline-xl text-headline-xl text-primary-fixed glitch tracking-tight" data-text="Threat Hunt">Threat Hunt</h1>
                <p className="font-label-caps text-label-caps text-secondary-container mt-2 tracking-widest uppercase">Input Manual Scan // Awaiting Payload</p>
              </div>
            </header>
            <AnalyzeForm onNewResult={() => setRefreshKey((k) => k + 1)} />
            <ScreenshotAnalyzeForm onNewResult={() => setRefreshKey((k) => k + 1)} />
          </div>
        )}
        
        {activeTab === 'dashboard' && (
          <div className="animate-fade-in space-y-8">
            <header className="flex items-end justify-between border-b border-outline-variant/30 pb-4 mb-4">
              <div>
                <h1 className="font-headline-xl text-headline-xl text-primary-fixed glitch tracking-tight" data-text="Incident Archive">Incident Archive</h1>
                <p className="font-label-caps text-label-caps text-secondary-container mt-2 tracking-widest uppercase">Global Telemetry // Review</p>
              </div>
            </header>
            <Dashboard refreshKey={refreshKey} />
          </div>
        )}

        {/* ── Footer ── */}
        <footer className="fixed bottom-0 w-full z-50 flex justify-between items-center px-margin py-2 bg-surface-container-lowest/95 backdrop-blur-sm border-t border-primary-fixed/20 hidden md:flex">
          <div className="text-primary-fixed font-label-caps text-label-caps">ShieldAI System - Status: Operational</div>
          <div className="flex gap-6 pr-64">
            <span className="font-metadata-sm text-metadata-sm text-on-tertiary-fixed-variant">Protocol v2.4</span>
            <span className="font-metadata-sm text-metadata-sm text-on-tertiary-fixed-variant">Online Harassment Detection System</span>
          </div>
        </footer>
      </main>
    </div>
  )
}
