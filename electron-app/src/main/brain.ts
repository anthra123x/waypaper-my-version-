import { readFile, writeFile, mkdir } from 'fs/promises'
import { existsSync } from 'fs'
import { createHash } from 'crypto'
import { basename } from 'path'

const UA = 'waypaper-brain/1.0'
const API = 'https://wallhaven.cc/api/v1'

interface Prefs {
  kept: Record<string, KeptEntry>
  discarded: Record<string, DiscardedEntry>
  tag_weights: Record<string, number>
  tag_count: number
  last_cleanup: string
  last_recommend: string
}

interface KeptEntry {
  path: string
  tags: string[]
  time: string
}

interface DiscardedEntry {
  path: string
  time: string
}

let prefsPath = ''
let libraryDirPath = ''

export function initPaths(prefs: string, lib: string) {
  prefsPath = prefs
  libraryDirPath = lib
}

function now(): string {
  return new Date().toISOString().replace('Z', '').replace(/\.\d{3}/, '')
}

function defaultPrefs(): Prefs {
  return {
    kept: {},
    discarded: {},
    tag_weights: {},
    tag_count: 0,
    last_cleanup: '',
    last_recommend: '',
  }
}

export async function loadPrefs(): Promise<Prefs> {
  try {
    const raw = await readFile(prefsPath, 'utf-8')
    return JSON.parse(raw)
  } catch {
    return defaultPrefs()
  }
}

export async function savePrefs(prefs: Prefs): Promise<void> {
  await mkdir(prefsPath.substring(0, prefsPath.lastIndexOf('/')), { recursive: true })
  await writeFile(prefsPath, JSON.stringify(prefs, null, 2), 'utf-8')
}

export function widFrom(path: string): string {
  const stem = basename(path).replace(/\.[^.]+$/, '')
  if (stem.startsWith('wh-')) {
    return stem.slice(3)
  }
  const localId = createHash('md5').update(path).digest('hex').slice(0, 12)
  return `local_${localId}`
}

async function fetchTags(wid: string): Promise<string[]> {
  if (!wid || wid.startsWith('local_')) return []
  try {
    const res = await fetch(`${API}/w/${wid}`, { headers: { 'User-Agent': UA } })
    if (!res.ok) return []
    const data = (await res.json()).data
    return (data.tags || []).map((t: any) => t.name || '')
  } catch {
    return []
  }
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

export async function getStats(): Promise<BrainStats> {
  const prefs = await loadPrefs()
  const { readdir } = await import('fs/promises')
  let totalOnDisk = 0
  try {
    const files = await readdir(libraryDirPath)
    totalOnDisk = files.length
  } catch {}

  const sorted = Object.entries(prefs.tag_weights).sort((a, b) => b[1] - a[1])
  const topTags = sorted.slice(0, 10).map(([tag, weight]) => ({ tag, weight }))

  return {
    total_on_disk: totalOnDisk,
    kept_count: Object.keys(prefs.kept).length,
    discarded_count: Object.keys(prefs.discarded).length,
    tag_count: prefs.tag_count,
    top_tags: topTags,
    last_cleanup: prefs.last_cleanup,
    last_recommend: prefs.last_recommend,
  }
}

export async function keep(path: string): Promise<Prefs> {
  const wid = widFrom(path)
  const prefs = await loadPrefs()
  if (prefs.kept[wid]) return prefs

  const isLocal = wid.startsWith('local_')
  const tags = isLocal ? [] : await fetchTags(wid)

  prefs.kept[wid] = { path, tags, time: now() }
  if (!isLocal) {
    for (const t of tags) {
      prefs.tag_weights[t] = (prefs.tag_weights[t] || 0) + 1
    }
    prefs.tag_count = Object.values(prefs.tag_weights).reduce((a, b) => a + b, 0)
  }
  delete prefs.discarded[wid]
  await savePrefs(prefs)
  return prefs
}

export async function discard(path: string): Promise<Prefs> {
  const wid = widFrom(path)
  if (!wid) return loadPrefs()
  const prefs = await loadPrefs()

  prefs.discarded[wid] = { path, time: now() }
  if (prefs.kept[wid]) {
    for (const t of prefs.kept[wid].tags || []) {
      prefs.tag_weights[t] = (prefs.tag_weights[t] || 1) - 0.5
      if (prefs.tag_weights[t] <= 0) {
        delete prefs.tag_weights[t]
      }
    }
    delete prefs.kept[wid]
  }
  await savePrefs(prefs)
  return prefs
}

export async function forget(path: string): Promise<Prefs> {
  const wid = widFrom(path)
  if (!wid) return loadPrefs()
  const prefs = await loadPrefs()
  delete prefs.kept[wid]
  delete prefs.discarded[wid]
  await savePrefs(prefs)
  return prefs
}

export async function getStatus(wid: string): Promise<'kept' | 'discarded' | null> {
  const prefs = await loadPrefs()
  if (prefs.kept[wid]) return 'kept'
  if (prefs.discarded[wid]) return 'discarded'
  return null
}

export async function getStatusForPath(path: string): Promise<'kept' | 'discarded' | null> {
  return getStatus(widFrom(path))
}
