import { contextBridge, ipcRenderer } from 'electron'

const api = {
  searchWallhaven: (params: any) =>
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
  brainStatus: (id: string) =>
    ipcRenderer.invoke('brain-status', id),
  brainStatuses: (ids: string[]) =>
    ipcRenderer.invoke('brain-statuses', ids),
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
