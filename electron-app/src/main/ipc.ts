import { ipcMain } from 'electron'
import { readdir, unlink, mkdir } from 'fs/promises'
import { join, extname, basename } from 'path'
import { existsSync } from 'fs'
import * as wallhaven from './wallhaven'
import * as brain from './brain'
import { setWallpaper } from './wallpaper'
import { LIBRARY_DIR, TEMP_DIR } from './paths'

const SUPPORTED_EXTS = new Set(['.jpg', '.jpeg', '.png', '.bmp'])

export function registerIpcHandlers(): void {
  ipcMain.handle('search-wallhaven', async (_event, params: { preset: string; query?: string; page: number }) => {
    const { items, meta } = await wallhaven.search(params.preset, params.query, params.page)
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
    const prefs = params.path
      ? await brain.discard(params.path)
      : await brain.discard(`wh-${params.id}.jpg`)
    return { ok: true }
  })

  ipcMain.handle('brain-keep', async (_event, path: string) => {
    await brain.keep(path)
    return { ok: true }
  })

  ipcMain.handle('brain-forget', async (_event, path: string) => {
    await brain.forget(path)
    return { ok: true }
  })

  ipcMain.handle('brain-status', async (_event, id: string) => {
    const status = await brain.getStatus(id)
    return { status }
  })

  ipcMain.handle('brain-stats', async () => {
    return brain.getStats()
  })

  ipcMain.handle('list-library', async () => {
    await mkdir(LIBRARY_DIR, { recursive: true })
    const files: any[] = []
    const entries = await readdir(LIBRARY_DIR, { withFileTypes: true })
    for (const entry of entries) {
      if (!entry.isFile()) continue
      const ext = extname(entry.name).toLowerCase()
      if (!SUPPORTED_EXTS.has(ext)) continue
      const stem = basename(entry.name, ext)
      const wid = stem.startsWith('wh-') ? stem.slice(3) : stem
      const status = await brain.getStatus(wid)
      files.push({
        id: wid,
        name: stem,
        path: join(LIBRARY_DIR, entry.name),
        status,
      })
    }
    files.sort((a, b) => a.name.localeCompare(b.name))
    return { items: files, count: files.length }
  })

  ipcMain.handle('delete-library', async (_event, id: string) => {
    for (const ext of ['jpg', 'jpeg', 'png', 'bmp']) {
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
    const { readFile } = await import('fs/promises')
    const buf = await readFile(filePath)
    const ext = extname(filePath).toLowerCase()
    const mime = ext === '.png' ? 'image/png' : ext === '.bmp' ? 'image/bmp' : 'image/jpeg'
    return `data:${mime};base64,${buf.toString('base64')}`
  })

  ipcMain.handle('health', async () => {
    return { ok: true, version: '1.0.0' }
  })
}
