export interface WallpaperItem {
  id: string
  thumb_url: string
  full_url: string
  resolution: string
  tags: string[]
}

export interface PageMeta {
  current: number
  last: number
  total: number
}

const API = 'https://wallhaven.cc/api/v1'
const UA = 'waypaper-wallhaven/1.0'

const CAT_PRESETS: Record<string, Record<string, string>> = {
  random:  { categories: '111', purity: '100', sorting: 'random' },
  anime:   { categories: '010', purity: '100', sorting: 'random' },
  manga:   { categories: '010', purity: '100', q: 'manga panel', sorting: 'random' },
  sketch:  { categories: '111', purity: '010', sorting: 'random' },
  general: { categories: '100', purity: '100', sorting: 'random' },
}

let lastReq = 0

async function request(url: string): Promise<any> {
  const elapsed = Date.now() - lastReq
  if (elapsed < 1500) {
    await new Promise(r => setTimeout(r, 1500 - elapsed))
  }
  const res = await fetch(url, { headers: { 'User-Agent': UA } })
  if (!res.ok) {
    throw new Error(`Wallhaven API error: ${res.status} ${res.statusText}`)
  }
  lastReq = Date.now()
  return res.json()
}

export async function search(
  preset: string,
  query: string = '',
  page: number = 1
): Promise<{ items: WallpaperItem[]; meta: PageMeta }> {
  const p = CAT_PRESETS[preset] || CAT_PRESETS.random
  const params = new URLSearchParams({
    categories: p.categories,
    purity: p.purity,
    sorting: p.sorting,
    page: String(page),
  })
  if (query) {
    params.set('q', query)
  } else if (p.q) {
    params.set('q', p.q)
  }

  const url = `${API}/search?${params.toString()}`
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
    tags: (item.tags || []).map((t: any) => t.name || ''),
  }))

  return { items, meta }
}

export async function fetchImageAsBase64(url: string): Promise<string> {
  const res = await fetch(url, { headers: { 'User-Agent': UA } })
  if (!res.ok) throw new Error(`fetch failed: ${res.status}`)
  const buf = await res.arrayBuffer()
  const base64 = Buffer.from(buf).toString('base64')
  const ext = url.split('.').pop()?.split('?')[0] || 'jpg'
  const mime = ext === 'png' ? 'image/png' : ext === 'bmp' ? 'image/bmp' : 'image/jpeg'
  return `data:${mime};base64,${base64}`
}

export async function downloadToFile(url: string, destPath: string): Promise<string> {
  const res = await fetch(url, { headers: { 'User-Agent': UA } })
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
