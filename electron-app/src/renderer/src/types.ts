export interface TagInfo {
  name: string
  is_nsfw?: boolean
}

export interface WallpaperItem {
  id: string
  thumb_url: string
  full_url: string
  resolution: string
  tags: TagInfo[]
  purity: string
  category: string
  file_size: number
  upload_date: string
  likes: number
  views: number
  status: 'kept' | 'discarded' | null
  path?: string
  name?: string
}

export interface BrainStats {
  total_on_disk: number
  kept_count: number
  discarded_count: number
  tag_count: number
  top_tags: { tag: string; weight: number }[]
}

export interface SearchFilters {
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

export interface Api {
  searchWallhaven(params: SearchFilters): Promise<{
    items: WallpaperItem[]; page: number; lastPage: number; total: number
  }>
  fetchImage(url: string): Promise<string>
  previewWallpaper(params: { id: string; fullUrl: string }): Promise<string>
  saveToLibrary(params: { id: string; fullUrl: string }): Promise<{ ok: boolean; path: string }>
  setWallpaper(params: { id: string; fullUrl: string }): Promise<{ ok: boolean; path: string }>
  discardWallpaper(params: { id: string; path?: string }): Promise<{ ok: boolean }>
  brainStatus(id: string): Promise<{ status: 'kept' | 'discarded' | null }>
  brainStatuses(ids: string[]): Promise<{ statuses: Record<string, 'kept' | 'discarded' | null> }>
  brainStats(): Promise<BrainStats>
  listLibrary(): Promise<{ items: WallpaperItem[]; count: number }>
  deleteLibrary(id: string): Promise<{ ok: boolean; deleted?: string; error?: string }>
  health(): Promise<{ ok: boolean; version: string }>
  readFileAsBase64(filePath: string): Promise<string>
  setWallpaperFromPath(path: string): Promise<{ ok: boolean }>
}

declare global {
  interface Window {
    api: Api
  }
}
