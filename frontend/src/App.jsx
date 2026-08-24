import { useState, useEffect } from 'react'
import AnalyzeForm from './components/AnalyzeForm'
import Dashboard from './components/Dashboard'
import Header from './components/Header'
import Sidebar from './components/Sidebar'
import ChatbotPanel from './components/chatbot/ChatbotPanel'
import { useAuth } from './hooks/useAuth'
import LoginForm from './components/auth/LoginForm'
import SubmitComplaint from './components/complaints/SubmitComplaint'
import MyTickets from './components/complaints/MyTickets'

export default function App() {
  const { token, role, login, logout } = useAuth()
  
  // Determine default tab based on role
  const getDefaultTab = () => {
    if (!token) return 'login';
    if (role === 'User') return 'submit_complaint';
    return 'dashboard';
  };

  const [activeTab, setActiveTab] = useState(getDefaultTab())
  const [refreshKey, setRefreshKey] = useState(0)

  // Redirect if role changes (login/logout)
  useEffect(() => {
    setActiveTab(getDefaultTab());
  }, [token, role]);

  const PAGE_TITLES = {
    login:            { title: 'Welcome to ShieldAI', sub: 'Cyber Threat Triage Platform' },
    submit_complaint: { title: 'File a Complaint', sub: 'Securely report cyber threats or harassment' },
    my_tickets:       { title: 'My Tickets', sub: 'Status of your reported incidents' },
    analyze:          { title: 'Threat Hunt', sub: 'Analyze content for digital safety threats' },
    dashboard:        { title: 'Organization Dashboard',  sub: 'Overview of all reported incidents' },
    incidents:        { title: 'Complaint Queue',  sub: 'Review and triage user complaints' },
    behavioral:       { title: 'Behavioral Intelligence', sub: 'Actor profiling and risk trends' },
  }
  
  const page = PAGE_TITLES[activeTab] || PAGE_TITLES.login

  if (!token) {
    return (
      <div className="bg-bg min-h-screen text-text-primary font-sans antialiased flex flex-col items-center justify-center">
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

  const isUserRole = role === 'User';
  const isOrgRole = !isUserRole;

  return (
    <div className="bg-bg min-h-screen text-text-primary font-sans antialiased">
      <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} role={role} />
      <Header  activeTab={activeTab} setActiveTab={setActiveTab} token={token} onLogout={logout} role={role} />

      <main
        style={{ marginLeft: 240, paddingTop: 56 }}
        className="min-h-screen"
      >
        <div className="p-6 max-w-[1400px] mx-auto">
          <div className="mb-6">
            <h1 className="text-2xl font-bold text-text-primary">{page.title}</h1>
            <p className="text-sm text-text-muted mt-0.5">{page.sub}</p>
          </div>

          <>
            {isUserRole && activeTab === 'submit_complaint' && (
              <div className="animate-fade-in">
                <SubmitComplaint onNewResult={() => setActiveTab('my_tickets')} />
              </div>
            )}
            
            {isUserRole && activeTab === 'my_tickets' && (
              <div className="animate-fade-in">
                <MyTickets refreshKey={refreshKey} />
              </div>
            )}

            {isOrgRole && activeTab === 'analyze' && (
              <div className="animate-fade-in">
                <AnalyzeForm onNewResult={() => setRefreshKey(k => k + 1)} />
              </div>
            )}

            {isOrgRole && (activeTab === 'dashboard' || activeTab === 'incidents' || activeTab === 'behavioral') && (
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
