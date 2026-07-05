interface StatusBarProps {
  text: string
  count: string
  stats: { kept_count: number; discarded_count: number } | null
}

export default function StatusBar({ text, count, stats }: StatusBarProps) {
  const kept = stats?.kept_count ?? 0
  const discarded = stats?.discarded_count ?? 0

  return (
    <div id="status-bar">
      <span id="status-text">{text}</span>
      <span style={{ display: 'flex', gap: 16, alignItems: 'center' }}>
        {stats !== null && (
          <span style={{ fontSize: 11 }}>
            Kept: {kept} / Discarded: {discarded}
          </span>
        )}
        <span id="status-count">{count}</span>
      </span>
    </div>
  )
}
