import { useAdminData } from '../hooks/useAdminData';
import LoadingState from './common/LoadingState';
import DashboardStats from './dashboard/DashboardStats';
import CategoryChart from './dashboard/CategoryChart';
import TrendChart from './dashboard/TrendChart';
import RecentFlagsTable from './dashboard/RecentFlagsTable';

import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  PointElement,
  LineElement,
  Filler,
  Tooltip,
} from 'chart.js';

ChartJS.register(CategoryScale, LinearScale, BarElement, PointElement, LineElement, Filler, Tooltip);

export default function Dashboard({ refreshKey }) {
  const { stats, recent, dailyCounts, anomalies, loading } = useAdminData(refreshKey);

  if (loading) {
    return <LoadingState message="Loading dashboard..." />;
  }

  const categories = Object.keys(stats.category_breakdown);

  return (
    <div className="space-y-4 animate-fade-in">
      {/* ── Anomaly banner ── */}
      {anomalies.length > 0 && (
        <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 animate-slide-up">
          <p className="text-sm font-semibold text-amber-800 flex items-center gap-2">
            <span>⚠️</span> Unusual Activity Detected
          </p>
          {anomalies.map((a, i) => (
            <p key={i} className="text-xs text-amber-700 mt-1">
              Spike on <strong>{a.date}</strong>: {a.count} reports vs {a.avg.toFixed(1)} avg (z-score: {a.z_score.toFixed(1)})
            </p>
          ))}
        </div>
      )}

      {/* ── Stat cards ── */}
      <DashboardStats 
        totalFlagged={stats.total_flagged} 
        categoriesCount={categories.length} 
        activeModel={stats.model} 
      />

      {/* ── Category chart ── */}
      <CategoryChart categories={categories} stats={stats} />

      {/* ── Trend chart ── */}
      <TrendChart dailyCounts={dailyCounts} anomalies={anomalies} />

      {/* ── Recent table ── */}
      <RecentFlagsTable recent={recent} />
    </div>
  );
}
