import { useState, useEffect } from 'react'
import InstantAnalysisForm from './components/analysis/InstantAnalysisForm'
import AnalyzeForm from './components/AnalyzeForm'
import Dashboard from './components/Dashboard'
import Header from './components/Header'
import Sidebar from './components/Sidebar'
import ChatbotPanel from './components/chatbot/ChatbotPanel'
import { useAuth } from './hooks/useAuth'
import LoginForm from './components/auth/LoginForm'
import MyHistory from './components/complaints/MyHistory'
import HowItWorks from './components/common/HowItWorks'

export default function App() {
  const { token, role, login, logout } = useAuth()
  
  // Determine default tab based on role
  const getDefaultTab = () => {
    if (!token) return 'login';
    // If Admin/Moderator, default to dashboard. If User/Guest, default to analyze.
    if (role === 'User' || role === 'Guest') return 'analyze';
    return 'dashboard';
  };

  const [activeTab, setActiveTab] = useState(getDefaultTab())
  const [refreshKey, setRefreshKey] = useState(0)

  // Redirect if role changes (login/logout)
  useEffect(() => {
    setActiveTab(getDefaultTab());
  }, [token, role]);

  const PAGE_TITLES = {
    login:            { title: 'Welcome to ShieldAI', sub: 'Cyber Threat Intelligence Platform' },
    instant_analysis: { title: 'Instant Analysis', sub: 'Instantly check content for digital safety threats' },
    my_history:       { title: 'My History', sub: 'Personal Cyber Safety Workspace - Historical Logs' },
    dashboard:        { title: 'Organization Dashboard',  sub: 'Cyber Security Operations Center - Central Command' },
    incidents:        { title: 'Complaint Queue',  sub: 'Review and triage user complaints' },
    behavioral:       { title: 'Behavioral Intelligence', sub: 'Actor profiling and risk trends' },
    how_it_works:     { title: 'How It Works', sub: 'Understanding the ShieldAI Platform' },
    analyze:          { title: 'Threat Hunt', sub: 'Manual analysis of content or files' },
  }
  
  const page = PAGE_TITLES[activeTab] || PAGE_TITLES.login

  if (!token) {
    if (activeTab === 'how_it_works') {
      return (
        <div className="bg-bg min-h-screen text-text-primary font-sans antialiased">
          <HowItWorks onBack={() => setActiveTab('login')} />
        </div>
      );
    }
    
    return (
      <div className="bg-bg min-h-screen text-text-primary font-sans antialiased flex flex-col items-center justify-center relative">
         <div className="absolute top-6 right-6">
           <button 
             onClick={() => setActiveTab('how_it_works')}
             className="text-sm font-semibold text-text-muted hover:text-primary transition-colors flex items-center gap-1.5"
           >
             How It Works
           </button>
         </div>
         <div className="mb-6 text-center">
            <h1 className="text-3xl font-bold text-text-primary">{page.title}</h1>
            <p className="text-text-muted mt-2">{page.sub}</p>
         </div>
         <div className="w-full max-w-md">
            <LoginForm onLogin={login} />
         </div>
      </div>
    );
  }

  return (
    <div className="bg-bg min-h-screen text-text-primary font-sans antialiased">
      <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} role={role} />
      <Header  activeTab={activeTab} setActiveTab={setActiveTab} token={token} onLogout={logout} role={role} />

      <main
        style={{ marginLeft: 240, paddingTop: 56 }}
        className="min-h-screen"
      >
        <div className="p-6 max-w-[1400px] mx-auto">
          <div className="mb-6 pb-4 border-b border-border/50">
            <h1 className="text-2xl font-bold text-text-primary flex items-center gap-2">
              <span className="w-2 h-6 bg-blue rounded-full shadow-[0_0_8px_rgba(0,242,254,0.6)]"></span>
              {page.title}
            </h1>
            <p className="text-sm text-text-muted mt-1 font-mono tracking-wide">{page.sub}</p>
          </div>

          <>
            {activeTab === 'how_it_works' && (
              <div className="animate-fade-in bg-surface-solid rounded-lg border border-border shadow-sm">
                <HowItWorks isLoggedIn={true} />
              </div>
            )}



            {activeTab === 'analyze' && (
              <div className="animate-fade-in">
                <AnalyzeForm onNewResult={() => setRefreshKey(k => k + 1)} />
              </div>
            )}

            {activeTab === 'my_history' && role === 'User' && (
              <div className="animate-fade-in">
                <MyHistory key={refreshKey} />
              </div>
            )}

            {(activeTab === 'dashboard' || activeTab === 'incidents' || activeTab === 'behavioral') && role !== 'User' && role !== 'Guest' && (
              <div className="animate-fade-in">
                <Dashboard refreshKey={refreshKey} activeTab={activeTab} />
              </div>
            )}
          </>
        </div>
      </main>
      
      <ChatbotPanel role={role} />
    </div>
  )
}
