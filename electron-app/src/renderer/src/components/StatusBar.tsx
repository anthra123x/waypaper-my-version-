import type { BrainStats } from '../types'

interface StatusBarProps {
  text: string
  count: string
  stats: BrainStats | null
}

export default function StatusBar({ text, count, stats }: StatusBarProps) {
  const kept = stats?.kept_count ?? 0
  const discarded = stats?.discarded_count ?? 0

  return (
    <div id="status-bar">
      <span id="status-text">{text}</span>
      <div className="status-right">
        {stats !== null && (
          <span className="brain-stats">
            <span className="stat-kept">{kept} kept</span>
            <span className="stat-sep">/</span>
            <span className="stat-discarded">{discarded} discarded</span>
          </span>
        )}
        <span id="status-count">{count}</span>
      </div>
    </div>
  )
}
