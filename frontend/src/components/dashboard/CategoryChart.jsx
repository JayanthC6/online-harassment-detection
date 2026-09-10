import PropTypes from 'prop-types';
import { Bar } from 'react-chartjs-2';
import Card from '../common/Card';

const CATEGORY_COLORS = {
  hate_speech: '#F43F5E', // critical
  offensive_language: '#F97316', // danger
  none: '#10B981', // success
};

const CATEGORY_LABELS = {
  hate_speech: 'Hate Speech',
  offensive_language: 'Offensive Language',
  none: 'Clean',
};

export default function CategoryChart({ categories, stats }) {
  if (categories.length === 0) return null;

  const chartData = {
    labels: categories.map((c) => CATEGORY_LABELS[c] || c.replace('_', ' ')),
    datasets: [
      {
        data: categories.map((c) => stats.category_breakdown[c]),
        backgroundColor: categories.map((c) => CATEGORY_COLORS[c] || '#334155'),
        borderRadius: 0,
        maxBarThickness: 48,
      },
    ],
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: { legend: { display: false } },
    scales: {
      y: {
        beginAtZero: true,
        ticks: { color: '#64748b', font: { size: 11, family: 'monospace' } },
        grid: { color: 'rgba(51, 65, 85, 0.5)' },
        border: { display: false },
      },
      x: {
        ticks: { color: '#64748b', font: { size: 11, family: 'monospace' } },
        grid: { display: false },
        border: { display: false },
      },
    },
  };

  return (
    <Card className="p-5 bg-black/40 border border-border/50 rounded-xl shadow-[inset_0_0_15px_rgba(0,0,0,0.5)]">
      <h3 className="text-xs font-bold text-text-muted font-mono uppercase tracking-wider mb-6 flex items-center gap-1.5 drop-shadow-[0_0_2px_rgba(255,255,255,0.1)]">
        <span className="w-1.5 h-1.5 bg-blue rounded-full shadow-[0_0_5px_rgba(0,242,254,0.5)]" />
        Flagged Content by Category
      </h3>
      <div className="h-52">
        <Bar data={chartData} options={chartOptions} />
      </div>
    </Card>
  );
}

CategoryChart.propTypes = {
  categories: PropTypes.arrayOf(PropTypes.string).isRequired,
  stats: PropTypes.shape({
    category_breakdown: PropTypes.objectOf(PropTypes.number).isRequired,
  }).isRequired,
};
