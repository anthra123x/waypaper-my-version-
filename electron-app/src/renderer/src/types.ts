export interface WallpaperItem {
  id: string
  thumb_url: string
  full_url: string
  resolution: string
  tags: string[]
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
  last_cleanup: string
  last_recommend: string
}

export interface Api {
  searchWallhaven(params: { preset: string; query?: string; page: number }): Promise<{
    items: WallpaperItem[]; page: number; lastPage: number; total: number
  }>
  fetchImage(url: string): Promise<string>
  previewWallpaper(params: { id: string; fullUrl: string }): Promise<string>
  saveToLibrary(params: { id: string; fullUrl: string }): Promise<{ ok: boolean; path: string }>
  setWallpaper(params: { id: string; fullUrl: string }): Promise<{ ok: boolean; path: string }>
  discardWallpaper(params: { id: string; path?: string }): Promise<{ ok: boolean }>
  brainKeep(path: string): Promise<{ ok: boolean }>
  brainForget(path: string): Promise<{ ok: boolean }>
  brainStatus(id: string): Promise<{ status: 'kept' | 'discarded' | null }>
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
