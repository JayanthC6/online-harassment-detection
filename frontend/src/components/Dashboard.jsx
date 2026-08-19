import React, { Suspense } from 'react';
import { Shield, Sparkles, AlertTriangle } from 'lucide-react';
import { useAdminData } from '../hooks/useAdminData';
import LoadingState from './common/LoadingState';
import DashboardStats from './dashboard/DashboardStats';
import ModeratorQueue from './dashboard/ModeratorQueue';
import BehavioralIntelligence from './dashboard/BehavioralIntelligence';

const AdvancedAnalytics = React.lazy(() => import('./dashboard/AdvancedAnalytics'));
const TrendChart = React.lazy(() => import('./dashboard/TrendChart'));

/**
 * Maps the sidebar activeTab to the Dashboard's own sub-tab key.
 * - 'dashboard'  → 'overview'   (stats + charts + queue)
 * - 'incidents'  → 'incidents'  (moderator queue only, focused view)
 * - 'behavioral' → 'behavior'   (actor profiles & risk trends)
 */
function resolveInitialSubTab(sidebarTab) {
  if (sidebarTab === 'behavioral') return 'behavior';
  if (sidebarTab === 'incidents') return 'incidents';
  return 'overview';
}

export default function Dashboard({ refreshKey, activeTab: sidebarTab }) {
  const {
    stats, reportsData, conversationsData, profilesData,
    analytics, dailyCounts, anomalies, filters, loading, reportsLoading
  } = useAdminData(refreshKey);

  // Sub-tab is driven by the sidebar selection on mount/change
  const [subTab, setSubTab] = React.useState(() => resolveInitialSubTab(sidebarTab));

  // Sync when the user switches sidebar tabs without unmounting Dashboard
  React.useEffect(() => {
    setSubTab(resolveInitialSubTab(sidebarTab));
  }, [sidebarTab]);

  if (loading) {
    return <LoadingState message="Loading Digital Safety Intelligence..." />;
  }

  return (
    <div className="space-y-10 animate-fade-in pb-12">
      {/* ── Sub-tab navigation (hidden on Incidents — it has a single focused view) ── */}
      {sidebarTab !== 'incidents' && (
        <div className="flex border-b border-border mb-6 pb-0 gap-1">
          <button
            onClick={() => setSubTab('overview')}
            className={`tab-btn ${subTab === 'overview' ? 'active' : ''}`}
          >
            <Shield size={15} />
            Safety Reports
          </button>
          <button
            onClick={() => setSubTab('behavior')}
            className={`tab-btn ${subTab === 'behavior' ? 'active' : ''}`}
          >
            <Sparkles size={15} />
            Behavioral Intelligence
          </button>
        </div>
      )}

      {/* ── Incidents page: focused moderator queue ── */}
      {sidebarTab === 'incidents' && (
        <>
          <div className="flex items-center gap-2 mb-2">
            <AlertTriangle size={16} className="text-warning" />
            <p className="text-sm text-text-muted">
              Review and manage all flagged messages and conversations below.
            </p>
          </div>
          <ModeratorQueue
            reportsData={reportsData}
            conversationsData={conversationsData}
            filters={filters}
            loading={reportsLoading}
          />
        </>
      )}

      {/* ── Dashboard overview: stats + charts + queue ── */}
      {sidebarTab !== 'incidents' && subTab === 'overview' && (
        <>
          <DashboardStats stats={stats} />

          <Suspense fallback={
            <div className="h-48 flex items-center justify-center card text-text-muted text-sm font-mono">
              Loading charts...
            </div>
          }>
            {analytics && <AdvancedAnalytics analytics={analytics} />}
            {dailyCounts && dailyCounts.length > 0 && (
              <TrendChart dailyCounts={dailyCounts} anomalies={anomalies} />
            )}
          </Suspense>

          <ModeratorQueue
            reportsData={reportsData}
            conversationsData={conversationsData}
            filters={filters}
            loading={reportsLoading}
          />
        </>
      )}

      {/* ── Behavioral Intelligence ── */}
      {sidebarTab !== 'incidents' && subTab === 'behavior' && (
        <BehavioralIntelligence profilesData={profilesData} />
      )}
    </div>
  );
}
