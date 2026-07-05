import type { WallpaperItem, BrainStats, SearchFilters } from './types'

const api = window.api

export async function searchWallhaven(filters: SearchFilters): Promise<{
  items: WallpaperItem[]; page: number; lastPage: number; total: number
}> {
  return api.searchWallhaven(filters)
}

export async function fetchImage(url: string): Promise<string> {
  return api.fetchImage(url)
}

export async function previewWallpaper(id: string, fullUrl: string): Promise<string> {
  return api.previewWallpaper({ id, fullUrl })
}

export async function saveToLibrary(id: string, fullUrl: string): Promise<{ ok: boolean; path: string }> {
  return api.saveToLibrary({ id, fullUrl })
}

export async function setWallpaper(id: string, fullUrl: string): Promise<{ ok: boolean; path: string }> {
  return api.setWallpaper({ id, fullUrl })
}

export async function discardWallpaper(id: string, filePath?: string): Promise<void> {
  await api.discardWallpaper({ id, path: filePath })
}

export async function listLibrary(): Promise<{ items: WallpaperItem[]; count: number }> {
  return api.listLibrary()
}

export async function brainStats(): Promise<BrainStats> {
  return api.brainStats()
}

export async function brainStatuses(ids: string[]): Promise<Record<string, 'kept' | 'discarded' | null>> {
  const result = await api.brainStatuses(ids)
  return result.statuses
}

export async function deleteLibrary(id: string): Promise<void> {
  await api.deleteLibrary(id)
}

export async function readFileAsBase64(filePath: string): Promise<string> {
  return api.readFileAsBase64(filePath)
}

export async function setWallpaperFromPath(path: string): Promise<{ ok: boolean }> {
  return api.setWallpaperFromPath(path)
}
