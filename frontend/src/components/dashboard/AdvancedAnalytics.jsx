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
      backgroundColor: ['rgba(244, 63, 94, 0.8)', 'rgba(245, 158, 11, 0.8)', 'rgba(16, 185, 129, 0.8)'],
      borderRadius: 6,
      barThickness: 24,
    }]
  };

  // Multi-Label Chart
  const labelFreqEntries = Object.entries(label_frequency || {}).sort((a, b) => b[1] - a[1]).slice(0, 5);
  const freqData = {
    labels: labelFreqEntries.map(e => e[0].replace('_', ' ')),
    datasets: [{
      data: labelFreqEntries.map(e => e[1]),
      backgroundColor: 'rgba(99, 102, 241, 0.8)',
      borderRadius: 6,
      barThickness: 24,
    }]
  };

  const chartOptions = {
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
      }
    },
    scales: {
      y: { 
        beginAtZero: true, 
        grid: { color: 'rgba(241, 245, 249, 1)' },
        border: { display: false },
        ticks: { font: { family: 'Inter', size: 11 }, color: '#94a3b8' }
      },
      x: { 
        grid: { display: false },
        border: { display: false },
        ticks: { font: { family: 'Inter', size: 11 }, color: '#64748b' }
      }
    }
  };

  return (
    <div className="space-y-4">
      <h2 className="text-sm font-semibold text-slate-800 uppercase tracking-wider mb-2">Analytics Overview</h2>
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white p-5 rounded-xl shadow-sm border border-slate-200">
          <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-6">Risk Distribution</h3>
          <div className="h-56">
            <Bar data={riskData} options={chartOptions} />
          </div>
        </div>
        
        <div className="bg-white p-5 rounded-xl shadow-sm border border-slate-200">
          <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-6">Most Common Categories</h3>
          <div className="h-56">
            {labelFreqEntries.length > 0 ? (
              <Bar data={freqData} options={chartOptions} />
            ) : (
              <div className="h-full flex items-center justify-center text-slate-400 text-sm">No data</div>
            )}
          </div>
        </div>

        <div className="bg-white p-5 rounded-xl shadow-sm border border-slate-200 flex flex-col">
          <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-4">Top Label Combinations</h3>
          <div className="flex-1 overflow-y-auto pr-2 space-y-2">
            {top_combinations && Object.keys(top_combinations).length > 0 ? (
              Object.entries(top_combinations).sort((a, b) => b[1] - a[1]).map(([combo, count]) => (
                <div key={combo} className="flex justify-between items-center text-sm p-3 bg-slate-50 rounded-lg border border-slate-100">
                  <span className="text-slate-700 truncate mr-2 font-medium" title={combo}>{combo.replace(/,/g, ' + ')}</span>
                  <span className="font-semibold text-indigo-700 bg-indigo-50 px-2.5 py-1 rounded-md text-xs tabular-nums">{count}</span>
                </div>
              ))
            ) : (
              <div className="h-full flex items-center justify-center text-slate-400 text-sm">No data</div>
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
