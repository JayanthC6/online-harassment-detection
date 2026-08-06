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
        borderColor: '#6366f1', // indigo-500
        backgroundColor: 'rgba(99, 102, 241, 0.1)',
        fill: true,
        tension: 0.4,
        pointBackgroundColor: dailyCounts.map((d) => {
          const isAnomaly = anomalies.some((a) => a.date === d.date);
          return isAnomaly ? '#f43f5e' : '#ffffff'; // rose-500 or white
        }),
        pointBorderColor: dailyCounts.map((d) => {
          const isAnomaly = anomalies.some((a) => a.date === d.date);
          return isAnomaly ? '#f43f5e' : '#6366f1';
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
        backgroundColor: 'rgba(15, 23, 42, 0.9)',
        padding: 12,
        titleFont: { size: 13, family: 'Inter' },
        bodyFont: { size: 13, family: 'Inter' },
        cornerRadius: 8,
        displayColors: false,
      }
    },
    scales: {
      y: {
        beginAtZero: true,
        ticks: { color: '#94a3b8', font: { size: 11, family: 'Inter' }, stepSize: 1 },
        grid: { color: 'rgba(241, 245, 249, 1)' },
        border: { display: false }
      },
      x: {
        ticks: { color: '#64748b', font: { size: 11, family: 'Inter' }, maxRotation: 45 },
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
    <div className="bg-white p-5 rounded-xl shadow-sm border border-slate-200">
      <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-6 flex items-center gap-1.5">
        <Activity size={14} className="text-indigo-500" />
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
