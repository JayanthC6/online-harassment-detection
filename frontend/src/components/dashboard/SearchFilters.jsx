import PropTypes from 'prop-types';
import { Search, Filter, AlertTriangle } from 'lucide-react';

export default function SearchFilters({ filters }) {
  return (
    <div className="bg-white p-4 rounded-xl shadow-sm border border-slate-200 flex flex-wrap gap-4 items-end mb-6">
      <div className="flex-1 min-w-[200px] relative">
        <label className="block text-[10px] font-semibold text-slate-500 uppercase tracking-wider mb-1.5 flex items-center gap-1">
          <Search size={12} /> Search
        </label>
        <div className="relative">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            type="text"
            placeholder="Search messages..."
            className="w-full pl-9 pr-3 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition-all placeholder:text-slate-400 text-slate-700"
            value={filters.search}
            onChange={(e) => {
              filters.setSearch(e.target.value);
              filters.setPage(1);
            }}
          />
        </div>
      </div>

      <div className="w-40">
        <label className="block text-[10px] font-semibold text-slate-500 uppercase tracking-wider mb-1.5 flex items-center gap-1">
          <AlertTriangle size={12} /> Risk Level
        </label>
        <select
          className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition-all text-slate-700 bg-white"
          value={filters.riskLevel}
          onChange={(e) => {
            filters.setRiskLevel(e.target.value);
            filters.setPage(1);
          }}
        >
          <option value="">All Risks</option>
          <option value="high">High Risk</option>
          <option value="medium">Medium Risk</option>
          <option value="low">Safe / Low</option>
        </select>
      </div>

      <div className="w-44">
        <label className="block text-[10px] font-semibold text-slate-500 uppercase tracking-wider mb-1.5 flex items-center gap-1">
          <Filter size={12} /> Category
        </label>
        <select
          className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition-all text-slate-700 bg-white"
          value={filters.category}
          onChange={(e) => {
            filters.setCategory(e.target.value);
            filters.setPage(1);
          }}
        >
          <option value="">All Categories</option>
          <option value="hate_speech">Hate Speech</option>
          <option value="offensive_language">Offensive Language</option>
          <option value="none">Safe</option>
        </select>
      </div>
    </div>
  );
}

SearchFilters.propTypes = {
  filters: PropTypes.shape({
    search: PropTypes.string.isRequired,
    setSearch: PropTypes.func.isRequired,
    riskLevel: PropTypes.string.isRequired,
    setRiskLevel: PropTypes.func.isRequired,
    category: PropTypes.string.isRequired,
    setCategory: PropTypes.func.isRequired,
    setPage: PropTypes.func.isRequired,
  }).isRequired,
};
