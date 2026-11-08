import { useState, useEffect, useCallback } from 'react'
import AnalyzeForm from './components/AnalyzeForm'
import Dashboard from './components/Dashboard'
import Header from './components/Header'
import Sidebar from './components/Sidebar'
import ChatPage from './components/chatbot/ChatPage'
import ChatbotPanel from './components/chatbot/ChatbotPanel'
import { useAuth } from './hooks/useAuth'
import LoginForm from './components/auth/LoginForm'
import MyHistory from './components/complaints/MyHistory'
import HowItWorks from './components/common/HowItWorks'
import BackendHealthBanner from './components/common/BackendHealthBanner'

const VALID_TABS = [
  'analyze',
  'chat',
  'dashboard',
  'incidents',
  'offenders',
  'behavioral',
  'retention',
  'my_history',
  'how_it_works',
  'login'
];

const ADMIN_ONLY_TABS = ['dashboard', 'incidents', 'offenders', 'behavioral', 'retention'];

export default function App() {
  const { token, role, login, logout } = useAuth()

  // Compute initial tab from URL hash, then localStorage, then default role
  const getInitialTab = () => {
    // 1. Check URL hash (e.g., #offenders, #incidents)
    if (typeof window !== 'undefined' && window.location.hash) {
      const hash = window.location.hash.replace(/^#\/?/, '').trim().toLowerCase();
      if (hash && VALID_TABS.includes(hash)) {
        if (ADMIN_ONLY_TABS.includes(hash)) {
          if (token && role !== 'User') return hash;
          return 'login';
        }
        if (hash === 'my_history' && (!token || role !== 'User')) {
          return token ? 'dashboard' : 'login';
        }
        return hash;
      }
    }

    // 2. Check localStorage
    try {
      const saved = localStorage.getItem('shieldai_active_tab');
      if (saved && VALID_TABS.includes(saved)) {
        if (ADMIN_ONLY_TABS.includes(saved)) {
          if (token && role !== 'User') return saved;
          return 'login';
        }
        if (saved === 'my_history' && (!token || role !== 'User')) {
          return token ? 'dashboard' : 'login';
        }
        return saved;
      }
    } catch (e) {
      // Ignore localStorage errors
    }

    // 3. Fallback based on authentication
    if (!token) return 'analyze';
    if (role === 'User' || role === 'Guest') return 'analyze';
    return 'dashboard';
  };

  const [activeTab, setActiveTabState] = useState(getInitialTab);
  const [refreshKey, setRefreshKey] = useState(0);

  // Tab switcher with URL Hash and localStorage synchronization
  const setActiveTab = useCallback((tab) => {
    if (!VALID_TABS.includes(tab)) return;
    setActiveTabState(tab);
    try {
      localStorage.setItem('shieldai_active_tab', tab);
    } catch (e) {}

    // Update URL hash without forcing a jump if already set
    if (typeof window !== 'undefined') {
      const currentHash = window.location.hash.replace(/^#\/?/, '').trim().toLowerCase();
      if (currentHash !== tab) {
        window.location.hash = `#${tab}`;
      }
    }
  }, []);

  // Listen to browser hash changes (enables browser Back / Forward buttons)
  useEffect(() => {
    const handleHashChange = () => {
      const hash = window.location.hash.replace(/^#\/?/, '').trim().toLowerCase();
      if (hash && VALID_TABS.includes(hash) && hash !== activeTab) {
        if (ADMIN_ONLY_TABS.includes(hash) && (!token || role === 'User')) {
          setActiveTab('login');
        } else {
          setActiveTabState(hash);
          try {
            localStorage.setItem('shieldai_active_tab', hash);
          } catch (e) {}
        }
      }
    };

    window.addEventListener('hashchange', handleHashChange);
    return () => window.removeEventListener('hashchange', handleHashChange);
  }, [activeTab, token, role, setActiveTab]);

  // Sync hash and storage on mount or when activeTab updates
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const currentHash = window.location.hash.replace(/^#\/?/, '').trim().toLowerCase();
      if (currentHash !== activeTab) {
        window.location.hash = `#${activeTab}`;
      }
      try {
        localStorage.setItem('shieldai_active_tab', activeTab);
      } catch (e) {}
    }
  }, [activeTab]);

  // Handle auth changes (login / logout)
  useEffect(() => {
    if (!token && ADMIN_ONLY_TABS.includes(activeTab)) {
      setActiveTab('analyze');
    } else if (token && activeTab === 'login') {
      const target = (role === 'User') ? 'analyze' : 'dashboard';
      setActiveTab(target);
    }
  }, [token, role, activeTab, setActiveTab]);

  const PAGE_TITLES = {
    analyze: { title: 'ShieldAI Threat Scanner', sub: 'Multi-layered neural detection for online harassment, scams, threats, and phishing' },
    chat: { title: 'AI Cyber Safety Assistant', sub: 'Interactive guidance in Victim Support and Security Analyst modes' },
    dashboard: { title: 'Security Operations Center', sub: 'Real-time incident intelligence, Recharts threat trends, and triage command' },
    incidents: { title: 'Incident Moderation Queue', sub: 'Triage reported incidents and manage status workflows' },
    offenders: { title: 'Repeat Offender Intelligence', sub: 'Track persistent actors, fraudulent domains, phones, and extortion accounts' },
    behavioral: { title: 'Behavioral Threat Profiles', sub: 'Actor timeline tracking and safety score factors' },
    retention: { title: 'Data Retention & Privacy Purge', sub: 'PII sanitization policy and statutory record retention control' },
    my_history: { title: 'My Historical Scans', sub: 'Personal safety workspace and audit log' },
    how_it_works: { title: 'How ShieldAI Works', sub: 'Multi-layered AI detection architecture and response protocols' },
    login: { title: 'Admin & Operator Portal', sub: 'Sign in to access the Cyber Security Operations Center' },
  };

  const page = PAGE_TITLES[activeTab] || PAGE_TITLES.analyze;

  return (
    <div className="bg-bg min-h-screen text-text-primary font-sans antialiased flex flex-col selection:bg-cyan-500/30">
      {/* ── Persistent Backend Health Banner ── */}
      <BackendHealthBanner />

      {/* ── Fixed Sidebar ── */}
      <Sidebar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        token={token}
        role={role}
        onLogout={logout}
      />

      {/* ── Header ── */}
      <Header
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        token={token}
        onLogout={logout}
        role={role}
      />

      {/* ── Mobile Top Bar ── */}
      <div className="md:hidden flex items-center justify-between px-4 h-14 bg-bg/95 border-b border-border sticky top-0 z-20">
        <span className="font-bold text-base text-text-primary font-mono">
          Shield<span className="text-blue">AI</span>
        </span>
        <div className="flex items-center gap-1.5 text-xs font-mono">
          <button
            onClick={() => setActiveTab('analyze')}
            className={`px-2.5 py-1 rounded ${activeTab === 'analyze' ? 'bg-blue/20 text-blue' : 'text-text-muted'}`}
          >
            Scan
          </button>
          <button
            onClick={() => setActiveTab('chat')}
            className={`px-2.5 py-1 rounded ${activeTab === 'chat' ? 'bg-blue/20 text-blue' : 'text-text-muted'}`}
          >
            Chat
          </button>
          {token ? (
            <button
              onClick={() => setActiveTab('dashboard')}
              className={`px-2.5 py-1 rounded ${activeTab === 'dashboard' ? 'bg-blue/20 text-blue' : 'text-text-muted'}`}
            >
              SOC
            </button>
          ) : (
            <button
              onClick={() => setActiveTab('login')}
              className="px-2.5 py-1 rounded bg-blue/15 text-blue border border-blue/30"
            >
              Sign In
            </button>
          )}
        </div>
      </div>

      {/* ── Main Content Area ── */}
      <main
        style={{ marginLeft: 240, paddingTop: 56 }}
        className="min-h-screen flex-1"
      >
        <div className="p-6 max-w-[1600px] w-full mx-auto">
          {/* Page Title Header */}
          <div className="mb-6 pb-4 border-b border-border/50">
            <h1 className="text-2xl font-bold text-text-primary flex items-center gap-2">
              <span className="w-2 h-6 bg-blue rounded-full shadow-[0_0_10px_rgba(0,242,254,0.7)]" />
              {page.title}
            </h1>
            <p className="text-xs text-text-muted mt-1 font-mono tracking-wide">{page.sub}</p>
          </div>

          {/* ── Page Routing ── */}
          <>
            {/* 1. Public Scan Page */}
            {activeTab === 'analyze' && (
              <div className="animate-fade-in">
                <AnalyzeForm onNewResult={() => setRefreshKey(k => k + 1)} />
              </div>
            )}

            {/* 2. Public / Dedicated Chat Page */}
            {activeTab === 'chat' && (
              <div className="animate-fade-in">
                <ChatPage role={role} />
              </div>
            )}

            {/* 3. How It Works */}
            {activeTab === 'how_it_works' && (
              <div className="animate-fade-in bg-surface-solid rounded-xl border border-border shadow-sm p-2">
                <HowItWorks isLoggedIn={Boolean(token)} onBack={() => setActiveTab('analyze')} />
              </div>
            )}

            {/* 4. Admin Login Portal */}
            {activeTab === 'login' && !token && (
              <div className="max-w-md mx-auto py-12 animate-fade-in">
                <LoginForm onLogin={login} />
              </div>
            )}

            {/* 5. User History */}
            {activeTab === 'my_history' && role === 'User' && (
              <div className="animate-fade-in">
                <MyHistory key={refreshKey} />
              </div>
            )}

            {/* 6. Admin / Operator Operations Center */}
            {(activeTab === 'dashboard' || activeTab === 'incidents' || activeTab === 'offenders' || activeTab === 'retention' || activeTab === 'behavioral') && token && role !== 'User' && (
              <div className="animate-fade-in">
                <Dashboard refreshKey={refreshKey} activeTab={activeTab} setActiveTab={setActiveTab} />
              </div>
            )}
          </>
        </div>
      </main>

      {/* Floating Chatbot Assistant Widget (docked on non-chat pages) */}
      {activeTab !== 'chat' && <ChatbotPanel role={role} />}
    </div>
  );
}
