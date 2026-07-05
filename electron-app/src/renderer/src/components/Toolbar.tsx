interface ToolbarProps {
  filters: SearchFilters | null
  query: string
  onFiltersChange: (filters: Partial<SearchFilters>) => void
  onSearchInput: (query: string) => void
  onModeChange: (mode: 'search' | 'library') => void
}

interface SearchFilters {
  categories: string
  purity: string
  sorting: string
  topRange?: string
  query?: string
  page: number
  atleast?: string
  ratios?: string
  colors?: string
  ai_art_filter?: number
}

function toggleFlag(value: string, bit: number): string {
  const bits = value.split('').map(Number)
  bits[bit] = bits[bit] ? 0 : 1
  return bits.join('')
}

export default function Toolbar({ filters, query, onFiltersChange, onSearchInput, onModeChange }: ToolbarProps) {
  const isSearch = filters !== null

  return (
    <div id="toolbar">
      <div id="mode-switcher">
        <button className={isSearch ? 'active' : ''} onClick={() => onModeChange('search')}>Search</button>
        <button className={!isSearch ? 'active' : ''} onClick={() => onModeChange('library')}>Library</button>
      </div>

      {isSearch && (
        <>
          <div className="filter-section">
            <label className="filter-label">Categories</label>
            <div className="chip-group">
              {[
                { label: 'General', bit: 0, flag: 'categories' as const },
                { label: 'Anime', bit: 1, flag: 'categories' as const },
                { label: 'People', bit: 2, flag: 'categories' as const },
              ].map(({ label, bit, flag }) => (
                <button
                  key={label}
                  className={`chip ${filters[flag][bit] === '1' ? 'active' : ''}`}
                  onClick={() => onFiltersChange({
                    [flag]: toggleFlag(filters[flag], bit)
                  })}
                >
                  {label}
                </button>
              ))}
            </div>
          </div>

          <div className="filter-section">
            <label className="filter-label">Purity</label>
            <div className="chip-group">
              {[
                { label: 'SFW', bit: 0, flag: 'purity' as const },
                { label: 'Sketchy', bit: 1, flag: 'purity' as const },
                { label: 'NSFW', bit: 2, flag: 'purity' as const },
              ].map(({ label, bit, flag }) => (
                <button
                  key={label}
                  className={`chip ${filters[flag][bit] === '1' ? 'active' : ''}`}
                  onClick={() => onFiltersChange({
                    [flag]: toggleFlag(filters[flag], bit)
                  })}
                >
                  {label}
                </button>
              ))}
            </div>
          </div>

          <div className="filter-section">
            <label className="filter-label">Sort</label>
            <select
              className="filter-select"
              value={filters.sorting}
              onChange={e => onFiltersChange({ sorting: e.target.value })}
            >
              <option value="date_added">Latest</option>
              <option value="relevancy">Relevance</option>
              <option value="random">Random</option>
              <option value="views">Most Viewed</option>
              <option value="favorites">Most Favorited</option>
              <option value="toplist">Top List</option>
            </select>
          </div>

          {filters.sorting === 'toplist' && (
            <div className="filter-section">
              <label className="filter-label">Range</label>
              <select
                className="filter-select"
                value={filters.topRange || '1m'}
                onChange={e => onFiltersChange({ topRange: e.target.value })}
              >
                <option value="1d">Today</option>
                <option value="3d">3 Days</option>
                <option value="1w">This Week</option>
                <option value="1m">This Month</option>
                <option value="3m">3 Months</option>
                <option value="6m">6 Months</option>
                <option value="1y">This Year</option>
              </select>
            </div>
          )}

          <div className="filter-section flex-1">
            <label className="filter-label">Search</label>
            <input
              type="text"
              className="filter-input"
              placeholder="Tags, ID, or text…"
              value={query}
              onChange={e => onSearchInput(e.target.value)}
            />
          </div>

          <div className="filter-section">
            <label className="filter-label">Min Res</label>
            <select
              className="filter-select"
              value={filters.atleast || ''}
              onChange={e => onFiltersChange({ atleast: e.target.value || undefined })}
            >
              <option value="">Any</option>
              <option value="1920x1080">Full HD</option>
              <option value="2560x1440">2K</option>
              <option value="3840x2160">4K</option>
              <option value="5120x2880">5K</option>
              <option value="7680x4320">8K</option>
            </select>
          </div>

          <div className="filter-section">
            <label className="filter-label">AI Art</label>
            <button
              className={`chip ${filters.ai_art_filter === 1 ? 'active' : ''}`}
              onClick={() => onFiltersChange({ ai_art_filter: filters.ai_art_filter === 1 ? 0 : 1 })}
            >
              Hide AI
            </button>
          </div>
        </>
      )}
    </div>
  )
}
