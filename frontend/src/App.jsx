import { useState } from 'react'
import AnalyzeForm from './components/AnalyzeForm'
import Dashboard from './components/Dashboard'
import Header from './components/Header'
import Sidebar from './components/Sidebar'
import ChatbotPanel from './components/chatbot/ChatbotPanel'
import { useAuth } from './hooks/useAuth'
import LoginForm from './components/auth/LoginForm'

export default function App() {
  const [activeTab, setActiveTab] = useState('analyze')
  const [refreshKey, setRefreshKey] = useState(0)
  const { token, login, logout } = useAuth()

  const PAGE_TITLES = {
    analyze:    { title: 'Threat Hunt', sub: 'Analyze content for digital safety threats' },
    dashboard:  { title: 'Dashboard',  sub: 'Overview of detected incidents' },
    incidents:  { title: 'Incidents',  sub: 'Review and manage flagged content' },
    behavioral: { title: 'Behavioral Intelligence', sub: 'Actor profiling and risk trends' },
  }
  const page = PAGE_TITLES[activeTab] || PAGE_TITLES.analyze

  const isProtectedTab = activeTab === 'dashboard' || activeTab === 'incidents' || activeTab === 'behavioral';

  return (
    <div className="bg-bg min-h-screen text-text-primary font-sans antialiased">
      <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} />
      <Header  activeTab={activeTab} setActiveTab={setActiveTab} token={token} onLogout={logout} />

      {/* Main content — offset for sidebar + header */}
      <main
        style={{ marginLeft: 240, paddingTop: 56 }}
        className="min-h-screen"
      >
        <div className="p-6 max-w-[1400px] mx-auto">
          {/* Page header */}
          <div className="mb-6">
            <h1 className="text-2xl font-bold text-text-primary">{page.title}</h1>
            <p className="text-sm text-text-muted mt-0.5">{page.sub}</p>
          </div>

          {/* Unauthenticated Access to Protected Tab */}
          {!token && isProtectedTab ? (
            <div className="animate-fade-in mt-10">
              <div className="max-w-md mx-auto text-center mb-6">
                <p className="text-text-muted">You must be logged in to view this section.</p>
              </div>
              <LoginForm onLogin={login} />
            </div>
          ) : (
            <>
              {/* Tabs */}
              {activeTab === 'analyze' && (
                <div className="animate-fade-in">
                  <AnalyzeForm onNewResult={() => setRefreshKey(k => k + 1)} />
                </div>
              )}

              {isProtectedTab && (
                <div className="animate-fade-in">
                  <Dashboard refreshKey={refreshKey} activeTab={activeTab} />
                </div>
              )}
            </>
          )}
        </div>
      </main>
      
      {/* Global Chatbot */}
      <ChatbotPanel />
    </div>
  )
}
