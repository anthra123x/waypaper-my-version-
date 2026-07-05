import { forwardRef, useState, useEffect } from 'react'
import type { WallpaperItem } from '../types'
import * as api from '../api'

interface GridProps {
  items: WallpaperItem[]
  mode: 'search' | 'library'
  onItemClick: (item: WallpaperItem) => void
}

interface GridItemProps {
  item: WallpaperItem
  onClick: () => void
}

function GridItemImage({ item }: { item: WallpaperItem }) {
  const [src, setSrc] = useState<string>('')

  useEffect(() => {
    if (item.thumb_url) {
      setSrc(item.thumb_url)
    } else if (item.path) {
      api.readFileAsBase64(item.path).then(setSrc).catch(() => setSrc(''))
    }
  }, [item.thumb_url, item.path])

  if (!src) return null
  return <img src={src} alt={item.id} loading="lazy" />
}

const Grid = forwardRef<HTMLDivElement, GridProps>(({ items, onItemClick }, ref) => {
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
          <div className="item-label">
            {item.resolution || item.name || item.id}
          </div>
        </div>
      ))}
    </div>
  )
})

Grid.displayName = 'Grid'
export default Grid
