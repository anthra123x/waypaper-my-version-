interface ToolbarProps {
  mode: 'search' | 'library'
  query: string
  preset: string
  onModeChange: (mode: 'search' | 'library') => void
  onSearch: (query: string) => void
  onPresetChange: (preset: string) => void
}

export default function Toolbar({ mode, query, preset, onModeChange, onSearch, onPresetChange }: ToolbarProps) {
  return (
    <div id="toolbar">
      <div id="mode-switcher">
        <button
          className={mode === 'search' ? 'active' : ''}
          onClick={() => onModeChange('search')}
        >
          Search
        </button>
        <button
          className={mode === 'library' ? 'active' : ''}
          onClick={() => onModeChange('library')}
        >
          Library
        </button>
      </div>
      {mode === 'search' && (
        <div id="search-controls">
          <input
            type="text"
            id="search-input"
            placeholder="Search tags…"
            value={query}
            onChange={(e) => onSearch(e.target.value)}
          />
          <select
            id="preset-select"
            value={preset}
            onChange={(e) => onPresetChange(e.target.value)}
          >
            <option value="random">Random</option>
            <option value="general">General</option>
            <option value="anime">Anime</option>
            <option value="manga">Manga</option>
            <option value="sketch">Sketch</option>
          </select>
        </div>
      )}
    </div>
  )
}
