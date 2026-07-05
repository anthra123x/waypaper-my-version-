import { useState, useEffect, useCallback, useRef } from 'react'
import type { WallpaperItem, BrainStats } from './types'
import * as api from './api'
import Toolbar from './components/Toolbar'
import StatusBar from './components/StatusBar'
import Grid from './components/Grid'
import Pagination from './components/Pagination'
import PreviewModal from './components/PreviewModal'

export default function App() {
  const [mode, setMode] = useState<'search' | 'library'>('search')
  const [page, setPage] = useState(1)
  const [lastPage, setLastPage] = useState(1)
  const [query, setQuery] = useState('')
  const [preset, setPreset] = useState('random')
  const [items, setItems] = useState<WallpaperItem[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [previewItem, setPreviewItem] = useState<WallpaperItem | null>(null)
  const [previewPath, setPreviewPath] = useState<string | null>(null)
  const [stats, setStats] = useState<BrainStats | null>(null)
  const gridRef = useRef<HTMLDivElement>(null)

  const fetchStats = useCallback(async () => {
    try {
      setStats(await api.brainStats())
    } catch {}
  }, [])

  const checkStatuses = useCallback(async (newItems: WallpaperItem[]) => {
    const updated = await Promise.all(
      newItems.map(async (item) => {
        if (!item.id) return item
        try {
          const status = await api.brainStatus(item.id)
          return { ...item, status }
        } catch {
          return item
        }
      })
    )
    setItems(updated)
  }, [])

  const doSearch = useCallback(async (p: string, q: string, pg: number) => {
    setLoading(true)
    setError('')
    try {
      const data = await api.searchWallhaven(p, q, pg)
      const newItems = data.items.map(i => ({ ...i, status: null }))
      setItems(newItems)
      setPage(data.page)
      setLastPage(data.lastPage)
      await checkStatuses(newItems)
    } catch (err: any) {
      setError(err.message || 'Search failed')
      setItems([])
    }
    setLoading(false)
  }, [checkStatuses])

  const loadLibrary = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const data = await api.listLibrary()
      setItems(data.items.map(i => ({
        ...i,
        thumb_url: '',
        full_url: '',
        resolution: '',
        tags: [],
      })))
      setPage(1)
      setLastPage(1)
    } catch (err: any) {
      setError(err.message || 'Failed to load library')
      setItems([])
    }
    setLoading(false)
  }, [])

  useEffect(() => {
    if (mode === 'search') {
      doSearch(preset, query, 1)
    } else {
      loadLibrary()
    }
  }, [mode])

  useEffect(() => {
    fetchStats()
  }, [fetchStats, items])

  const handleModeChange = (newMode: 'search' | 'library') => {
    setPreviewItem(null)
    setPreviewPath(null)
    setMode(newMode)
  }

  const handleSearch = (newQuery: string) => {
    setQuery(newQuery)
    doSearch(preset, newQuery, 1)
  }

  const handlePresetChange = (newPreset: string) => {
    setPreset(newPreset)
    doSearch(newPreset, query, 1)
  }

  const handlePageChange = (newPage: number) => {
    if (newPage < 1 || newPage > lastPage || loading) return
    doSearch(preset, query, newPage)
  }

  const handleRefresh = () => {
    if (mode === 'search') {
      doSearch(preset, query, 1)
    } else {
      loadLibrary()
    }
  }

  const handleItemClick = async (item: WallpaperItem) => {
    setPreviewItem(item)
    setPreviewPath(null)
    if (mode === 'search' && item.full_url) {
      try {
        const localPath = await api.previewWallpaper(item.id, item.full_url)
        setPreviewPath(localPath)
      } catch {}
    }
  }

  const handleSet = async () => {
    if (!previewItem) return
    try {
      await api.setWallpaper(previewItem.id, previewItem.full_url)
      await fetchStats()
      setPreviewItem(null)
      setPreviewPath(null)
    } catch (err: any) {
      setError(err.message || 'Failed to set wallpaper')
    }
  }

  const handleSave = async () => {
    if (!previewItem) return
    try {
      await api.saveToLibrary(previewItem.id, previewItem.full_url)
      await fetchStats()
      setPreviewItem(null)
      setPreviewPath(null)
    } catch (err: any) {
      setError(err.message || 'Failed to save')
    }
  }

  const handleDiscard = async () => {
    if (!previewItem) return
    try {
      await api.discardWallpaper(previewItem.id, previewItem.path)
      await fetchStats()
      setPreviewItem(null)
      setPreviewPath(null)
      if (mode === 'library') loadLibrary()
      else doSearch(preset, query, page)
    } catch {}
  }

  const handleDelete = async () => {
    if (!previewItem) return
    if (!confirm(`Delete ${previewItem.name || previewItem.id} from library?`)) return
    try {
      await api.deleteLibrary(previewItem.id)
      await fetchStats()
      setPreviewItem(null)
      setPreviewPath(null)
      loadLibrary()
    } catch {}
  }

  const handleClosePreview = () => {
    setPreviewItem(null)
    setPreviewPath(null)
  }

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLSelectElement) return

      if (previewItem) {
        if (e.key === 'Escape' || e.key === 'k' || e.key === 'K') {
          handleClosePreview()
        } else if (e.key === 'Enter' && mode === 'search') {
          handleSet()
        } else if (e.key === 'd' || e.key === 'D') {
          handleDiscard()
        } else if (e.key === 's' || e.key === 'S') {
          handleSave()
        } else if (e.key === 'y' || e.key === 'Y') {
          handleDelete()
        }
      } else {
        if (e.key === '1') handleModeChange('search')
        else if (e.key === '2') handleModeChange('library')
        else if (e.key === 'r' || e.key === 'R') handleRefresh()
        else if (e.key === 'j' || e.key === 'J') {
          const els = gridRef.current?.querySelectorAll('.grid-item')
          if (!els?.length) return
          const focused = document.activeElement?.closest('.grid-item')
          const idx = focused ? Array.from(els).indexOf(focused as HTMLElement) : -1
          const next = els[Math.min(idx + 1, els.length - 1)] as HTMLElement
          next?.focus()
          next?.scrollIntoView({ block: 'nearest' })
        } else if (e.key === 'k' || e.key === 'K') {
          const els = gridRef.current?.querySelectorAll('.grid-item')
          if (!els?.length) return
          const focused = document.activeElement?.closest('.grid-item')
          const idx = focused ? Array.from(els).indexOf(focused as HTMLElement) : els.length
          const prev = els[Math.max(idx - 1, 0)] as HTMLElement
          prev?.focus()
          prev?.scrollIntoView({ block: 'nearest' })
        } else if (e.key === 'ArrowLeft') {
          handlePageChange(page - 1)
        } else if (e.key === 'ArrowRight') {
          handlePageChange(page + 1)
        }
      }
    }

    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [previewItem, mode, page, lastPage, loading])

  const statusText = loading ? 'Loading…' : error || (mode === 'search' ? `Wallhaven ${preset}` : 'Library')

  return (
    <div id="app">
      <StatusBar text={statusText} count={`${items.length} items`} stats={stats} />
      <Toolbar
        mode={mode}
        query={query}
        preset={preset}
        onModeChange={handleModeChange}
        onSearch={handleSearch}
        onPresetChange={handlePresetChange}
      />
      <Grid
        ref={gridRef}
        items={items}
        mode={mode}
        onItemClick={handleItemClick}
      />
      <Pagination page={page} lastPage={lastPage} onPageChange={handlePageChange} />
      {previewItem && (
        <PreviewModal
          item={previewItem}
          mode={mode}
          localPath={previewPath}
          onSet={handleSet}
          onSave={handleSave}
          onDiscard={handleDiscard}
          onDelete={handleDelete}
          onClose={handleClosePreview}
        />
      )}
    </div>
  )
}
