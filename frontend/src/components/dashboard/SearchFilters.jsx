import PropTypes from 'prop-types';
import { Search, Filter, AlertTriangle } from 'lucide-react';

export default function SearchFilters({ filters }) {
  return (
    <div className="bg-panel p-4 border border-slate-700 flex flex-wrap gap-4 items-end mb-6">
      <div className="flex-1 min-w-[200px] relative">
        <label className="block text-[10px] font-bold text-slate-500 font-mono uppercase tracking-wider mb-1.5 flex items-center gap-1">
          <Search size={12} /> Search
        </label>
        <div className="relative">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
          <input
            type="text"
            placeholder="Search messages..."
            className="input-dark w-full pl-9 pr-3 py-2 text-sm"
            value={filters.search}
            onChange={(e) => {
              filters.setSearch(e.target.value);
              filters.setPage(1);
            }}
          />
        </div>
      </div>

      <div className="w-40">
        <label className="block text-[10px] font-bold text-slate-500 font-mono uppercase tracking-wider mb-1.5 flex items-center gap-1">
          <AlertTriangle size={12} /> Risk Level
        </label>
        <select
          className="input-dark w-full px-3 py-2 text-sm"
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
        <label className="block text-[10px] font-bold text-slate-500 font-mono uppercase tracking-wider mb-1.5 flex items-center gap-1">
          <Filter size={12} /> Category
        </label>
        <select
          className="input-dark w-full px-3 py-2 text-sm"
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
