import React, { Suspense } from 'react';
import { Shield, Sparkles } from 'lucide-react';
import { useAdminData } from '../hooks/useAdminData';
import LoadingState from './common/LoadingState';
import DashboardStats from './dashboard/DashboardStats';
import ModeratorQueue from './dashboard/ModeratorQueue';
import BehavioralIntelligence from './dashboard/BehavioralIntelligence';

const AdvancedAnalytics = React.lazy(() => import('./dashboard/AdvancedAnalytics'));
const TrendChart = React.lazy(() => import('./dashboard/TrendChart'));

export default function Dashboard({ refreshKey }) {
  const { stats, reportsData, conversationsData, profilesData, analytics, dailyCounts, anomalies, filters, loading, reportsLoading } = useAdminData(refreshKey);
  const [activeTab, setActiveTab] = React.useState('overview'); // overview, behavior

  if (loading) {
    return <LoadingState message="Loading Digital Safety Intelligence..." />;
  }

  return (
    <div className="space-y-10 animate-fade-in pb-12">
      <div className="flex border-b border-outline-variant/30 mb-6 pb-2 gap-4">
        <button
          onClick={() => setActiveTab('overview')}
          className={`flex items-center gap-2 px-4 py-2 font-label-caps text-label-caps transition-all ${
            activeTab === 'overview'
              ? 'text-primary-fixed border-b-2 border-primary-fixed'
              : 'text-on-surface-variant hover:text-primary-fixed-dim'
          }`}
        >
          <Shield size={16} />
          Safety Reports
        </button>
        <button
          onClick={() => setActiveTab('behavior')}
          className={`flex items-center gap-2 px-4 py-2 font-label-caps text-label-caps transition-all ${
            activeTab === 'behavior'
              ? 'text-primary-fixed border-b-2 border-primary-fixed'
              : 'text-on-surface-variant hover:text-primary-fixed-dim'
          }`}
        >
          <Sparkles size={16} />
          Behavioral Intelligence
        </button>
      </div>

      {activeTab === 'overview' ? (
        <>
          {/* ── Stat cards ── */}
          <DashboardStats stats={stats} />

          {/* ── Advanced Analytics (Lazy Loaded) ── */}
          <Suspense fallback={<div className="h-48 flex items-center justify-center bg-panel border border-slate-700 text-slate-400 text-sm font-mono">Loading charts...</div>}>
            {analytics && <AdvancedAnalytics analytics={analytics} />}
            {dailyCounts && dailyCounts.length > 0 && <TrendChart dailyCounts={dailyCounts} anomalies={anomalies} />}
          </Suspense>

          {/* ── Moderator Queue ── */}
          <ModeratorQueue 
            reportsData={reportsData}
            conversationsData={conversationsData}
            filters={filters} 
            loading={reportsLoading} 
          />
        </>
      ) : (
        <BehavioralIntelligence profilesData={profilesData} />
      )}
    </div>
  );
}
