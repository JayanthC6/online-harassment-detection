import PropTypes from 'prop-types';
import { Bar } from 'react-chartjs-2';
import Card from '../common/Card';

const CATEGORY_COLORS = {
  hate_speech: 'rgba(220, 38, 38, 0.75)',
  offensive_language: 'rgba(217, 119, 6, 0.75)',
  none: 'rgba(156, 163, 175, 0.5)',
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
        backgroundColor: categories.map((c) => CATEGORY_COLORS[c] || 'rgba(156,163,175,0.5)'),
        borderRadius: 6,
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
        ticks: { color: '#6b7280', font: { size: 11 } },
        grid: { color: 'rgba(0,0,0,0.04)' },
      },
      x: {
        ticks: { color: '#374151', font: { size: 11 } },
        grid: { display: false },
      },
    },
  };

  return (
    <Card className="p-5">
      <p className="section-title">
        <span className="w-1.5 h-1.5 bg-orange-500 rounded-full" />
        Flagged Content by Category
      </p>
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
