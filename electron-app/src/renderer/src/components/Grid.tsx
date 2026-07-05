import { forwardRef, useState, useEffect } from 'react'
import type { WallpaperItem } from '../types'
import * as api from '../api'

interface GridProps {
  items: WallpaperItem[]
  mode: 'search' | 'library'
  onItemClick: (item: WallpaperItem) => void
}

interface GridItemImageProps {
  item: WallpaperItem
}

function GridItemImage({ item }: GridItemImageProps) {
  const [src, setSrc] = useState('')
  const [failed, setFailed] = useState(false)

  useEffect(() => {
    if (item.thumb_url) {
      setSrc(item.thumb_url)
    } else if (item.path) {
      api.readFileAsBase64(item.path).then(setSrc).catch(() => setFailed(true))
    } else {
      setFailed(true)
    }
  }, [item.thumb_url, item.path])

  if (!src || failed) {
    return <div className="grid-placeholder">No preview</div>
  }

  return <img src={src} alt={item.id} loading="lazy" onError={() => setFailed(true)} />
}

const Grid = forwardRef<HTMLDivElement, GridProps>(({ items, mode, onItemClick }, ref) => {
  if (items.length === 0) {
    return (
      <div id="grid" ref={ref}>
        <div className="grid-empty">No wallpapers found</div>
      </div>
    )
  }

  return (
    <div id="grid" ref={ref}>
      {items.map((item) => (
        <div
          key={item.id + (item.name || '')}
          className={`grid-item ${item.status === 'kept' ? 'kept' : ''} ${item.status === 'discarded' ? 'discarded' : ''}`}
          tabIndex={0}
          onClick={() => onItemClick(item)}
          onKeyDown={(e) => { if (e.key === 'Enter') onItemClick(item) }}
        >
          <GridItemImage item={item} />
          <div className="item-overlay">
            <span className="item-resolution">{item.resolution || item.name || item.id}</span>
            <span className="item-purity-badge" data-purity={item.purity}>{item.purity}</span>
          </div>
          {mode === 'search' && item.tags && item.tags.length > 0 && (
            <div className="item-tags">
              {item.tags.slice(0, 3).map(t => (
                <span key={t.name} className="item-tag">{t.name}</span>
              ))}
            </div>
          )}
        </div>
      ))}
    </div>
  )
})

Grid.displayName = 'Grid'
export default Grid
