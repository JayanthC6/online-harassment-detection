import PropTypes from 'prop-types';
import { Line } from 'react-chartjs-2';
import { Activity } from 'lucide-react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Filler,
  Tooltip,
} from 'chart.js';

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Filler, Tooltip);

export default function TrendChart({ dailyCounts, anomalies }) {
  if (!dailyCounts || dailyCounts.length === 0) return null;

  const trendData = {
    labels: dailyCounts.map((d) => {
      // Format date nicely
      const date = new Date(d.date);
      return date.toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
    }),
    datasets: [
      {
        label: 'Flagged Reports',
        data: dailyCounts.map((d) => d.count),
        borderColor: '#00E5FF', // verified-teal
        backgroundColor: 'rgba(0, 229, 255, 0.1)',
        fill: true,
        tension: 0.4,
        pointBackgroundColor: dailyCounts.map((d) => {
          const isAnomaly = anomalies.some((a) => a.date === d.date);
          return isAnomaly ? '#FF3333' : '#1C1E27'; // redaction-red or panel
        }),
        pointBorderColor: dailyCounts.map((d) => {
          const isAnomaly = anomalies.some((a) => a.date === d.date);
          return isAnomaly ? '#FF3333' : '#00E5FF';
        }),
        pointBorderWidth: 2,
        pointRadius: dailyCounts.map((d) => {
          const isAnomaly = anomalies.some((a) => a.date === d.date);
          return isAnomaly ? 6 : 4;
        }),
        pointHoverRadius: 6,
      },
    ],
  };

  const trendOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: { 
      legend: { display: false },
      tooltip: {
        backgroundColor: '#1C1E27',
        titleColor: '#F8FAFC',
        bodyColor: '#94A3B8',
        borderColor: '#334155',
        borderWidth: 1,
        padding: 12,
        titleFont: { size: 13, family: 'monospace' },
        bodyFont: { size: 13, family: 'monospace' },
        cornerRadius: 0,
        displayColors: false,
      }
    },
    scales: {
      y: {
        beginAtZero: true,
        ticks: { color: '#64748b', font: { size: 11, family: 'monospace' }, stepSize: 1 },
        grid: { color: 'rgba(51, 65, 85, 0.5)' },
        border: { display: false }
      },
      x: {
        ticks: { color: '#64748b', font: { size: 11, family: 'monospace' }, maxRotation: 45 },
        grid: { display: false },
        border: { display: false }
      },
    },
    interaction: {
      mode: 'index',
      intersect: false,
    },
  };

  return (
    <div className="bg-panel p-5 border border-slate-700 rounded-none shadow-sm">
      <h3 className="text-xs font-bold text-slate-500 font-mono uppercase tracking-wider mb-6 flex items-center gap-1.5">
        <Activity size={14} className="text-slate-500" />
        Report Volume Trend (30 Days)
      </h3>
      <div className="h-[250px] w-full">
        <Line data={trendData} options={trendOptions} />
      </div>
    </div>
  );
}

TrendChart.propTypes = {
  dailyCounts: PropTypes.arrayOf(
    PropTypes.shape({
      date: PropTypes.string.isRequired,
      count: PropTypes.number.isRequired,
    })
  ),
  anomalies: PropTypes.arrayOf(
    PropTypes.shape({
      date: PropTypes.string.isRequired,
    })
  ).isRequired,
};
