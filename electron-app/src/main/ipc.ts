import { ipcMain } from 'electron'
import { readdir, unlink, mkdir, readFile } from 'fs/promises'
import { join, extname as getExt, basename } from 'path'
import { existsSync } from 'fs'
import * as wallhaven from './wallhaven'
import type { SearchParams } from './wallhaven'
import * as brain from './brain'
import { setWallpaper } from './wallpaper'
import { LIBRARY_DIR, TEMP_DIR } from './paths'

const SUPPORTED_EXTS = new Set(['.jpg', '.jpeg', '.png', '.bmp', '.webp'])

export function registerIpcHandlers(): void {
  ipcMain.handle('search-wallhaven', async (_event, params: SearchParams) => {
    const { items, meta } = await wallhaven.search(params)
    return { items, page: meta.current, lastPage: meta.last, total: meta.total }
  })

  ipcMain.handle('fetch-image', async (_event, url: string) => {
    return wallhaven.fetchImageAsBase64(url)
  })

  ipcMain.handle('preview-wallpaper', async (_event, params: { id: string; fullUrl: string }) => {
    await mkdir(TEMP_DIR, { recursive: true })
    const ext = wallhaven.extFromUrl(params.fullUrl)
    const dest = join(TEMP_DIR, `wh-${params.id}.${ext}`)
    await wallhaven.downloadToFile(params.fullUrl, dest)
    return dest
  })

  ipcMain.handle('save-to-library', async (_event, params: { id: string; fullUrl: string }) => {
    await mkdir(LIBRARY_DIR, { recursive: true })
    const ext = wallhaven.extFromUrl(params.fullUrl)
    const dest = join(LIBRARY_DIR, `wh-${params.id}.${ext}`)
    if (!existsSync(dest)) {
      await wallhaven.downloadToFile(params.fullUrl, dest)
    }
    await brain.keep(dest)
    return { ok: true, path: dest }
  })

  ipcMain.handle('set-wallpaper', async (_event, params: { id: string; fullUrl: string }) => {
    await mkdir(LIBRARY_DIR, { recursive: true })
    const ext = wallhaven.extFromUrl(params.fullUrl)
    const dest = join(LIBRARY_DIR, `wh-${params.id}.${ext}`)
    if (!existsSync(dest)) {
      await wallhaven.downloadToFile(params.fullUrl, dest)
    }
    const ok = await setWallpaper(dest)
    if (ok) {
      await brain.keep(dest)
    }
    return { ok, path: dest }
  })

  ipcMain.handle('discard-wallpaper', async (_event, params: { id: string; path?: string }) => {
    if (params.path) {
      await brain.discard(params.path)
    } else {
      await brain.discard(`wh-${params.id}.jpg`)
    }
    return { ok: true }
  })

  ipcMain.handle('brain-status', async (_event, id: string) => {
    const status = await brain.getStatus(id)
    return { status }
  })

  ipcMain.handle('brain-statuses', async (_event, ids: string[]) => {
    const statuses = await brain.getStatuses(ids)
    return { statuses }
  })

  ipcMain.handle('brain-stats', async () => {
    return brain.getStats()
  })

  ipcMain.handle('list-library', async () => {
    await mkdir(LIBRARY_DIR, { recursive: true })
    const entries = await readdir(LIBRARY_DIR, { withFileTypes: true })
    const libraryItems: Array<{ id: string; name: string; path: string; status: string | null }> = []
    const wids: string[] = []

    for (const entry of entries) {
      if (!entry.isFile()) continue
      const ext = getExt(entry.name).toLowerCase()
      if (!SUPPORTED_EXTS.has(ext)) continue
      const stem = basename(entry.name, ext)
      const wid = stem.startsWith('wh-') ? stem.slice(3) : stem
      const fullPath = join(LIBRARY_DIR, entry.name)
      libraryItems.push({ id: wid, name: stem, path: fullPath, status: null })
      wids.push(wid)
    }

    const statuses = await brain.getStatuses(wids)
    for (const item of libraryItems) {
      item.status = statuses[item.id] || null
    }

    libraryItems.sort((a, b) => a.name.localeCompare(b.name))
    return { items: libraryItems, count: libraryItems.length }
  })

  ipcMain.handle('delete-library', async (_event, id: string) => {
    for (const ext of ['jpg', 'jpeg', 'png', 'bmp', 'webp']) {
      const p = join(LIBRARY_DIR, `wh-${id}.${ext}`)
      if (existsSync(p)) {
        await brain.discard(p)
        await unlink(p)
        return { ok: true, deleted: p }
      }
    }
    return { ok: false, error: 'not found' }
  })

  ipcMain.handle('set-wallpaper-from-path', async (_event, filePath: string) => {
    const ok = await setWallpaper(filePath)
    if (ok) {
      await brain.keep(filePath)
    }
    return { ok }
  })

  ipcMain.handle('read-file-base64', async (_event, filePath: string) => {
    const buf = await readFile(filePath)
    const ext = getExt(filePath).toLowerCase()
    const mimes: Record<string, string> = { '.png': 'image/png', '.bmp': 'image/bmp', '.webp': 'image/webp' }
    return `data:${mimes[ext] || 'image/jpeg'};base64,${buf.toString('base64')}`
  })

  ipcMain.handle('health', async () => {
    return { ok: true, version: '1.0.0' }
  })
}
