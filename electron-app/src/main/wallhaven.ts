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
}

export interface TagInfo {
  name: string
  is_nsfw?: boolean
}

export interface PageMeta {
  current: number
  last: number
  total: number
}

export interface SearchParams {
  categories: string     // '100' (general) | '010' (anime) | '001' (people) | '111' (all)
  purity: string         // '100' (sfw) | '010' (sketchy) | '001' (nsfw) | '111' (all)
  sorting: string        // 'date_added' | 'relevancy' | 'random' | 'views' | 'favorites' | 'toplist'
  topRange?: string      // '1d' | '3d' | '1w' | '1m' | '3m' | '6m' | '1y'
  query?: string
  page: number
  atleast?: string       // minimum resolution e.g. '1920x1080'
  ratios?: string        // comma-separated, e.g. '16x9,16x10'
  colors?: string        // hex color without #
  ai_art_filter?: number // 0 = show AI, 1 = hide AI
}

const API = 'https://wallhaven.cc/api/v1'
const UA = 'waypaper-wallhaven/1.0'

let lastReq = 0
let requestCount = 0
const RATE_LIMIT_MS = 1500
const MAX_RETRIES = 2

async function request(url: string): Promise<any> {
  for (let attempt = 0; attempt <= MAX_RETRIES; attempt++) {
    try {
      const elapsed = Date.now() - lastReq
      if (elapsed < RATE_LIMIT_MS) {
        await new Promise(r => setTimeout(r, RATE_LIMIT_MS - elapsed))
      }
      const controller = new AbortController()
      const timeout = setTimeout(() => controller.abort(), 15000)
      const res = await fetch(url, {
        headers: { 'User-Agent': UA },
        signal: controller.signal,
      })
      clearTimeout(timeout)
      if (!res.ok) {
        if (res.status === 429 && attempt < MAX_RETRIES) {
          await new Promise(r => setTimeout(r, 3000))
          continue
        }
        throw new Error(`Wallhaven API error: ${res.status}`)
      }
      lastReq = Date.now()
      requestCount++
      return res.json()
    } catch (err: any) {
      if (attempt >= MAX_RETRIES) throw err
      if (err.name === 'AbortError') {
        await new Promise(r => setTimeout(r, 2000))
        continue
      }
      throw err
    }
  }
}

export async function search(params: SearchParams): Promise<{ items: WallpaperItem[]; meta: PageMeta }> {
  const urlParams = new URLSearchParams({
    categories: params.categories,
    purity: params.purity,
    sorting: params.sorting,
    page: String(params.page),
  })
  if (params.query) urlParams.set('q', params.query)
  if (params.topRange) urlParams.set('topRange', params.topRange)
  if (params.atleast) urlParams.set('atleast', params.atleast)
  if (params.ratios) urlParams.set('ratios', params.ratios)
  if (params.colors) urlParams.set('colors', params.colors)
  if (params.ai_art_filter !== undefined) urlParams.set('ai_art_filter', String(params.ai_art_filter))

  const url = `${API}/search?${urlParams.toString()}`
  const data = await request(url)

  const meta: PageMeta = {
    current: data.meta?.current_page ?? 1,
    last: data.meta?.last_page ?? 1,
    total: data.meta?.total ?? 0,
  }

  const items: WallpaperItem[] = (data.data || []).map((item: any) => ({
    id: item.id || '',
    thumb_url: item.thumbs?.small || '',
    full_url: item.path || '',
    resolution: item.resolution || '',
    tags: (item.tags || []).map((t: any) => ({ name: t.name || '', is_nsfw: t.is_nsfw })),
    purity: item.purity || 'sfw',
    category: item.category || 'general',
    file_size: item.file_size || 0,
    upload_date: item.created_at || '',
    likes: item.favorites || 0,
    views: item.views || 0,
  }))

  return { items, meta }
}

export function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

export async function fetchImageAsBase64(url: string): Promise<string> {
  const controller = new AbortController()
  const timeout = setTimeout(() => controller.abort(), 20000)
  const res = await fetch(url, {
    headers: { 'User-Agent': UA },
    signal: controller.signal,
  })
  clearTimeout(timeout)
  if (!res.ok) throw new Error(`fetch failed: ${res.status}`)
  const buf = await res.arrayBuffer()
  const base64 = Buffer.from(buf).toString('base64')
  const ext = url.split('.').pop()?.split('?')[0] || 'jpg'
  const mimes: Record<string, string> = { png: 'image/png', bmp: 'image/bmp', webp: 'image/webp', gif: 'image/gif' }
  const mime = mimes[ext] || 'image/jpeg'
  return `data:${mime};base64,${base64}`
}

export async function downloadToFile(url: string, destPath: string): Promise<string> {
  const controller = new AbortController()
  const timeout = setTimeout(() => controller.abort(), 60000)
  const res = await fetch(url, {
    headers: { 'User-Agent': UA },
    signal: controller.signal,
  })
  clearTimeout(timeout)
  if (!res.ok) throw new Error(`download failed: ${res.status}`)
  const buf = await res.arrayBuffer()
  const { writeFile } = await import('fs/promises')
  await writeFile(destPath, Buffer.from(buf))
  return destPath
}

export function extFromUrl(url: string): string {
  const match = url.match(/\.(\w+)(?:\?|#|$)/)
  return match ? match[1] : 'jpg'
}
