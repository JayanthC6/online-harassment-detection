import PropTypes from 'prop-types';
import { Bar } from 'react-chartjs-2';

import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Tooltip,
} from 'chart.js';

ChartJS.register(CategoryScale, LinearScale, BarElement, Tooltip);

export default function AdvancedAnalytics({ analytics }) {
  if (!analytics) return null;

  const { risk_distribution, label_frequency, top_combinations } = analytics;

  // Risk Chart
  const riskLabels = ['High Risk', 'Medium Risk', 'Low Risk'];
  const riskData = {
    labels: riskLabels,
    datasets: [{
      data: [risk_distribution?.high || 0, risk_distribution?.medium || 0, risk_distribution?.low || 0],
      backgroundColor: ['#FF3333', '#FFD700', '#00E5FF'],
      borderRadius: 0,
      barThickness: 24,
    }]
  };

  // Multi-Label Chart
  const labelFreqEntries = Object.entries(label_frequency || {}).sort((a, b) => b[1] - a[1]).slice(0, 5);
  const freqData = {
    labels: labelFreqEntries.map(e => e[0].replace('_', ' ')),
    datasets: [{
      data: labelFreqEntries.map(e => e[1]),
      backgroundColor: '#334155',
      borderRadius: 0,
      barThickness: 24,
    }]
  };

  const chartOptions = {
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
      }
    },
    scales: {
      y: { 
        beginAtZero: true, 
        grid: { color: 'rgba(51, 65, 85, 0.5)' },
        border: { display: false },
        ticks: { font: { family: 'monospace', size: 11 }, color: '#64748b' }
      },
      x: { 
        grid: { display: false },
        border: { display: false },
        ticks: { font: { family: 'monospace', size: 11 }, color: '#64748b' }
      }
    }
  };

  return (
    <div className="space-y-4">
      <h2 className="text-sm font-bold text-off-white font-display uppercase tracking-wider mb-2">Analytics Overview</h2>
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-panel p-5 border border-slate-700 rounded-none shadow-sm">
          <h3 className="text-xs font-bold text-slate-500 font-mono uppercase tracking-wider mb-6">Risk Distribution</h3>
          <div className="h-56">
            <Bar data={riskData} options={chartOptions} />
          </div>
        </div>
        
        <div className="bg-panel p-5 border border-slate-700 rounded-none shadow-sm">
          <h3 className="text-xs font-bold text-slate-500 font-mono uppercase tracking-wider mb-6">Most Common Categories</h3>
          <div className="h-56">
            {labelFreqEntries.length > 0 ? (
              <Bar data={freqData} options={chartOptions} />
            ) : (
              <div className="h-full flex items-center justify-center text-slate-500 font-mono text-sm">No data</div>
            )}
          </div>
        </div>

        <div className="bg-panel p-5 border border-slate-700 rounded-none shadow-sm flex flex-col">
          <h3 className="text-xs font-bold text-slate-500 font-mono uppercase tracking-wider mb-4">Top Label Combinations</h3>
          <div className="flex-1 overflow-y-auto pr-2 space-y-2">
            {top_combinations && Object.keys(top_combinations).length > 0 ? (
              Object.entries(top_combinations).sort((a, b) => b[1] - a[1]).map(([combo, count]) => (
                <div key={combo} className="flex justify-between items-center text-sm p-3 bg-slate-900 border border-slate-700 rounded-none">
                  <span className="text-slate-300 font-mono truncate mr-2" title={combo}>{combo.replace(/,/g, ' + ')}</span>
                  <span className="font-bold text-slate-400 bg-slate-800 px-2 py-1 border border-slate-700 tabular-nums">{count}</span>
                </div>
              ))
            ) : (
              <div className="h-full flex items-center justify-center text-slate-500 font-mono text-sm">No data</div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

AdvancedAnalytics.propTypes = {
  analytics: PropTypes.shape({
    risk_distribution: PropTypes.object,
    confidence_distribution: PropTypes.object,
    model_usage: PropTypes.object,
    label_frequency: PropTypes.object,
    top_combinations: PropTypes.object
  })
};
