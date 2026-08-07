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
    <div className="space-y-10 animate-fade-in pb-12 mt-6">
      <div className="flex flex-col gap-1">
        <h1 className="text-2xl font-semibold tracking-tight text-slate-900 flex items-center gap-2">
          <Shield className="text-indigo-600" size={24} />
          Digital Safety Intelligence
        </h1>
        <p className="text-sm text-slate-500">
          Review, analyze, and manage digital safety reports across the platform.
        </p>
      </div>

      <div className="flex border-b border-slate-200 mb-6">
        <button
          onClick={() => setActiveTab('overview')}
          className={`px-4 py-3 text-sm font-medium border-b-2 transition-colors ${
            activeTab === 'overview'
              ? 'border-indigo-600 text-indigo-600'
              : 'border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300'
          }`}
        >
          Safety Reports
        </button>
        <button
          onClick={() => setActiveTab('behavior')}
          className={`px-4 py-3 text-sm font-medium border-b-2 transition-colors flex items-center gap-2 ${
            activeTab === 'behavior'
              ? 'border-indigo-600 text-indigo-600'
              : 'border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300'
          }`}
        >
          <Sparkles size={14} />
          Behavioral Intelligence
        </button>
      </div>

      {activeTab === 'overview' ? (
        <>
          {/* ── Stat cards ── */}
          <DashboardStats stats={stats} />

          {/* ── Advanced Analytics (Lazy Loaded) ── */}
          <Suspense fallback={<div className="h-48 flex items-center justify-center bg-slate-50 rounded-xl border border-slate-100 text-slate-400 text-sm">Loading charts...</div>}>
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
