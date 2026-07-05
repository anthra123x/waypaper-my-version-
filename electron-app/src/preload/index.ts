import { contextBridge, ipcRenderer } from 'electron'

const api = {
  searchWallhaven: (params: { preset: string; query?: string; page: number }) =>
    ipcRenderer.invoke('search-wallhaven', params),
  fetchImage: (url: string) =>
    ipcRenderer.invoke('fetch-image', url),
  previewWallpaper: (params: { id: string; fullUrl: string }) =>
    ipcRenderer.invoke('preview-wallpaper', params),
  saveToLibrary: (params: { id: string; fullUrl: string }) =>
    ipcRenderer.invoke('save-to-library', params),
  setWallpaper: (params: { id: string; fullUrl: string }) =>
    ipcRenderer.invoke('set-wallpaper', params),
  discardWallpaper: (params: { id: string; path?: string }) =>
    ipcRenderer.invoke('discard-wallpaper', params),
  brainKeep: (path: string) =>
    ipcRenderer.invoke('brain-keep', path),
  brainForget: (path: string) =>
    ipcRenderer.invoke('brain-forget', path),
  brainStatus: (id: string) =>
    ipcRenderer.invoke('brain-status', id) as Promise<{ status: 'kept' | 'discarded' | null }>,
  brainStats: () =>
    ipcRenderer.invoke('brain-stats'),
  listLibrary: () =>
    ipcRenderer.invoke('list-library'),
  deleteLibrary: (id: string) =>
    ipcRenderer.invoke('delete-library', id),
  health: () =>
    ipcRenderer.invoke('health'),
  readFileAsBase64: (filePath: string) =>
    ipcRenderer.invoke('read-file-base64', filePath),
  setWallpaperFromPath: (path: string) =>
    ipcRenderer.invoke('set-wallpaper-from-path', path),
}

contextBridge.exposeInMainWorld('api', api)
