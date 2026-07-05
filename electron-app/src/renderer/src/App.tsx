import { useState, useEffect, useCallback, useRef } from 'react'
import type { WallpaperItem, BrainStats, SearchFilters } from './types'
import * as api from './api'
import Toolbar from './components/Toolbar'
import StatusBar from './components/StatusBar'
import Grid from './components/Grid'
import Pagination from './components/Pagination'
import PreviewModal from './components/PreviewModal'

const DEFAULT_FILTERS: SearchFilters = {
  categories: '111',
  purity: '100',
  sorting: 'toplist',
  page: 1,
  atleast: '1920x1080',
}

export default function App() {
  const [mode, setMode] = useState<'search' | 'library'>('search')
  const [filters, setFilters] = useState<SearchFilters>(DEFAULT_FILTERS)
  const [items, setItems] = useState<WallpaperItem[]>([])
  const [page, setPage] = useState(1)
  const [lastPage, setLastPage] = useState(1)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [previewItem, setPreviewItem] = useState<WallpaperItem | null>(null)
  const [previewLocalPath, setPreviewLocalPath] = useState<string | null>(null)
  const [stats, setStats] = useState<BrainStats | null>(null)
  const [searchQuery, setSearchQuery] = useState('')
  const gridRef = useRef<HTMLDivElement>(null)
  const searchTimerRef = useRef<ReturnType<typeof setTimeout>>()

  const fetchStats = useCallback(async () => {
    try { setStats(await api.brainStats()) } catch {}
  }, [])

  const checkStatuses = useCallback(async (newItems: WallpaperItem[]) => {
    const ids = newItems.map(i => i.id).filter(Boolean)
    if (ids.length === 0) return newItems
    try {
      const statuses = await api.brainStatuses(ids)
      return newItems.map(item => ({ ...item, status: statuses[item.id] || null }))
    } catch {
      return newItems.map(item => ({ ...item, status: null }))
    }
  }, [])

  const doSearch = useCallback(async (f: SearchFilters) => {
    setLoading(true)
    setError('')
    try {
      const data = await api.searchWallhaven(f)
      const withStatus = await checkStatuses(data.items)
      setItems(withStatus)
      setPage(data.page)
      setLastPage(data.lastPage)
    } catch (err: any) {
      setError(err?.message || 'Search failed')
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
        purity: '',
        category: '',
        file_size: 0,
        upload_date: '',
        likes: 0,
        views: 0,
      })))
      setPage(1)
      setLastPage(1)
    } catch (err: any) {
      setError(err?.message || 'Failed to load library')
      setItems([])
    }
    setLoading(false)
  }, [])

  useEffect(() => {
    if (mode === 'search') {
      doSearch({ ...filters, page: 1 })
    } else {
      loadLibrary()
    }
  }, [mode])

  useEffect(() => {
    fetchStats()
  }, [fetchStats, items])

  const handleModeChange = (newMode: 'search' | 'library') => {
    setPreviewItem(null)
    setPreviewLocalPath(null)
    setMode(newMode)
  }

  const handleFiltersChange = (newFilters: Partial<SearchFilters>) => {
    const merged = { ...filters, ...newFilters, page: 1 }
    setFilters(merged)
    doSearch(merged)
  }

  const handleSearchInput = (query: string) => {
    setSearchQuery(query)
    clearTimeout(searchTimerRef.current)
    searchTimerRef.current = setTimeout(() => {
      const merged = { ...filters, query, page: 1 }
      setFilters(merged)
      doSearch(merged)
    }, 350)
  }

  const handlePageChange = (newPage: number) => {
    if (newPage < 1 || newPage > lastPage || loading) return
    const merged = { ...filters, page: newPage }
    setFilters(merged)
    doSearch(merged)
  }

  const handleRefresh = () => {
    if (mode === 'search') {
      doSearch({ ...filters, page: 1 })
    } else {
      loadLibrary()
    }
  }

  const handleItemClick = async (item: WallpaperItem) => {
    setPreviewItem(item)
    setPreviewLocalPath(null)
    if (mode === 'search' && item.full_url) {
      try {
        const localPath = await api.previewWallpaper(item.id, item.full_url)
        setPreviewLocalPath(localPath)
      } catch {}
    }
  }

  const handleTagClick = (tag: string) => {
    setSearchQuery(tag)
    const merged = { ...filters, query: tag, page: 1 }
    setFilters(merged)
    doSearch(merged)
  }

  const handleSet = async () => {
    if (!previewItem) return
    try {
      await api.setWallpaper(previewItem.id, previewItem.full_url)
      fetchStats()
      setPreviewItem(null)
      setPreviewLocalPath(null)
    } catch {}
  }

  const handleSave = async () => {
    if (!previewItem) return
    try {
      await api.saveToLibrary(previewItem.id, previewItem.full_url)
      fetchStats()
      setPreviewItem(null)
      setPreviewLocalPath(null)
    } catch {}
  }

  const handleDiscard = async () => {
    if (!previewItem) return
    try {
      await api.discardWallpaper(previewItem.id, previewItem.path)
      fetchStats()
      setPreviewItem(null)
      setPreviewLocalPath(null)
      if (mode === 'library') loadLibrary()
      else doSearch(filters)
    } catch {}
  }

  const handleDelete = async () => {
    if (!previewItem) return
    if (!confirm(`Delete ${previewItem.name || previewItem.id} from library?`)) return
    try {
      await api.deleteLibrary(previewItem.id)
      fetchStats()
      setPreviewItem(null)
      setPreviewLocalPath(null)
      loadLibrary()
    } catch {}
  }

  const handleClosePreview = () => {
    setPreviewItem(null)
    setPreviewLocalPath(null)
  }

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLSelectElement) return

      if (previewItem) {
        if (e.key === 'Escape' || e.key === 'k' || e.key === 'K') handleClosePreview()
        else if (e.key === 'Enter' && mode === 'search') handleSet()
        else if (e.key === 'd' || e.key === 'D') handleDiscard()
        else if (e.key === 's' || e.key === 'S') handleSave()
        else if (e.key === 'y' || e.key === 'Y') handleDelete()
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
        } else if (e.key === 'ArrowLeft') handlePageChange(page - 1)
        else if (e.key === 'ArrowRight') handlePageChange(page + 1)
      }
    }

    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [previewItem, mode, page, lastPage, loading, filters])

  const statusText = loading ? 'Loading…' : error || (mode === 'search' ? `Wallhaven` : 'Library')

  return (
    <div id="app">
      <StatusBar
        text={statusText}
        count={`${items.length} items`}
        stats={stats}
      />
      {mode === 'search' && (
        <Toolbar
          filters={filters}
          query={searchQuery}
          onFiltersChange={handleFiltersChange}
          onSearchInput={handleSearchInput}
          onModeChange={handleModeChange}
        />
      )}
      {mode === 'library' && (
        <Toolbar
          filters={null}
          query=""
          onFiltersChange={() => {}}
          onSearchInput={() => {}}
          onModeChange={handleModeChange}
        />
      )}
      <Grid ref={gridRef} items={items} mode={mode} onItemClick={handleItemClick} />
      {mode === 'search' && <Pagination page={page} lastPage={lastPage} onPageChange={handlePageChange} />}
      {previewItem && (
        <PreviewModal
          item={previewItem}
          mode={mode}
          localPath={previewLocalPath}
          onSet={handleSet}
          onSave={handleSave}
          onDiscard={handleDiscard}
          onDelete={handleDelete}
          onClose={handleClosePreview}
          onTagClick={handleTagClick}
        />
      )}
    </div>
  )
}
