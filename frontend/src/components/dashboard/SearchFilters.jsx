import PropTypes from 'prop-types';
import { Search, Filter, AlertTriangle } from 'lucide-react';

export default function SearchFilters({ filters }) {
  const labelClass = "block text-2xs font-semibold text-text-muted uppercase tracking-widest mb-1.5 flex items-center gap-1.5";

  return (
    <div className="flex flex-wrap gap-3 items-end">
      {/* Search */}
      <div className="flex-1 min-w-[200px]">
        <label className={labelClass}><Search size={11} /> Search</label>
        <div className="relative">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-text-muted pointer-events-none" />
          <input
            type="text"
            placeholder="Search messages..."
            className="input pl-9"
            value={filters.search}
            onChange={(e) => { filters.setSearch(e.target.value); filters.setPage(1); }}
          />
        </div>
      </div>

      {/* Risk Level */}
      <div className="w-40">
        <label className={labelClass}><AlertTriangle size={11} /> Risk Level</label>
        <select
          className="input"
          value={filters.riskLevel}
          onChange={(e) => { filters.setRiskLevel(e.target.value); filters.setPage(1); }}
          style={{ appearance: 'none', backgroundImage: "url(\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 24 24' fill='none' stroke='%2300F2FE' stroke-width='2'%3E%3Cpath d='M6 9l6 6 6-6'/%3E%3C/svg%3E\")", backgroundRepeat: 'no-repeat', backgroundPosition: 'right 10px center', paddingRight: '30px' }}
        >
          <option value="">All Risks</option>
          <option value="high">High Risk</option>
          <option value="medium">Medium Risk</option>
          <option value="low">Safe / Low</option>
        </select>
      </div>

      {/* Category */}
      <div className="w-44">
        <label className={labelClass}><Filter size={11} /> Category</label>
        <select
          className="input"
          value={filters.category}
          onChange={(e) => { filters.setCategory(e.target.value); filters.setPage(1); }}
          style={{ appearance: 'none', backgroundImage: "url(\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 24 24' fill='none' stroke='%2300F2FE' stroke-width='2'%3E%3Cpath d='M6 9l6 6 6-6'/%3E%3C/svg%3E\")", backgroundRepeat: 'no-repeat', backgroundPosition: 'right 10px center', paddingRight: '30px' }}
        >
          <option value="">All Categories</option>
          <option value="hate_speech">Hate Speech</option>
          <option value="offensive_language">Offensive Language</option>
          <option value="threat">Threat</option>
          <option value="scam">Scam</option>
          <option value="phishing">Phishing</option>
          <option value="none">Safe</option>
        </select>
      </div>
    </div>
  );
}

SearchFilters.propTypes = {
  filters: PropTypes.shape({
    search:      PropTypes.string.isRequired,
    setSearch:   PropTypes.func.isRequired,
    riskLevel:   PropTypes.string.isRequired,
    setRiskLevel:PropTypes.func.isRequired,
    category:    PropTypes.string.isRequired,
    setCategory: PropTypes.func.isRequired,
    setPage:     PropTypes.func.isRequired,
  }).isRequired,
};
