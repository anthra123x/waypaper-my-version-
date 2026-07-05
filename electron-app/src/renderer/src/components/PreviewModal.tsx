import { useState, useEffect } from 'react'
import type { WallpaperItem } from '../types'
import * as api from '../api'

interface PreviewModalProps {
  item: WallpaperItem
  mode: 'search' | 'library'
  localPath: string | null
  onSet: () => void
  onSave: () => void
  onDiscard: () => void
  onDelete: () => void
  onClose: () => void
  onTagClick: (tag: string) => void
}

export default function PreviewModal({
  item, mode, localPath, onSet, onSave, onDiscard, onDelete, onClose, onTagClick,
}: PreviewModalProps) {
  const [imageSrc, setImageSrc] = useState('')
  const [loadingImg, setLoadingImg] = useState(true)

  useEffect(() => {
    setLoadingImg(true)
    const load = async () => {
      try {
        if (localPath) {
          setImageSrc(await api.readFileAsBase64(localPath))
        } else if (item.path) {
          setImageSrc(await api.readFileAsBase64(item.path))
        } else if (item.full_url) {
          setImageSrc(await api.fetchImage(item.full_url))
        }
      } catch {
        setImageSrc('')
      }
      setLoadingImg(false)
    }
    load()
  }, [item, localPath])

  useEffect(() => {
    const handleEsc = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }
    document.addEventListener('keydown', handleEsc)
    return () => document.removeEventListener('keydown', handleEsc)
  }, [onClose])

  const formatBytes = (bytes: number) => {
    if (!bytes) return ''
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  }

  return (
    <div id="preview-overlay" onClick={(e) => { if (e.target === e.currentTarget) onClose() }}>
      <div id="preview-modal">
        <div id="preview-image-container">
          {imageSrc ? (
            <img src={imageSrc} alt={item.id} id="preview-image" />
          ) : loadingImg ? (
            <div id="preview-loader">
              <div className="spinner" />
              <span>Loading…</span>
            </div>
          ) : (
            <div id="preview-loader" style={{ color: '#e03131' }}>Failed to load image</div>
          )}
        </div>

        <div id="preview-right-col">
          <div id="preview-sidebar">
            <div className="preview-meta">
              <div className="preview-meta-row">
                <span className="preview-label">ID</span>
                <span className="preview-value">{item.id}</span>
              </div>
              {item.resolution && (
                <div className="preview-meta-row">
                  <span className="preview-label">Resolution</span>
                  <span className="preview-value">{item.resolution}</span>
                </div>
              )}
              {item.file_size > 0 && (
                <div className="preview-meta-row">
                  <span className="preview-label">Size</span>
                  <span className="preview-value">{formatBytes(item.file_size)}</span>
                </div>
              )}
              <div className="preview-meta-row">
                <span className="preview-label">Purity</span>
                <span className={`preview-value purity-badge-${item.purity}`}>{item.purity}</span>
              </div>
              <div className="preview-meta-row">
                <span className="preview-label">Category</span>
                <span className="preview-value">{item.category}</span>
              </div>
              {item.views > 0 && (
                <div className="preview-meta-row">
                  <span className="preview-label">Views</span>
                  <span className="preview-value">{item.views.toLocaleString()}</span>
                </div>
              )}
              {item.likes > 0 && (
                <div className="preview-meta-row">
                  <span className="preview-label">Favorites</span>
                  <span className="preview-value">{item.likes.toLocaleString()}</span>
                </div>
              )}
            </div>

            {item.tags && item.tags.length > 0 && (
              <div className="preview-tags-section">
                <div className="preview-label">Tags</div>
                <div className="preview-tags-list">
                  {item.tags.map(t => (
                    <button
                      key={t.name}
                      className={`preview-tag ${t.is_nsfw ? 'nsfw' : ''}`}
                      onClick={() => { onTagClick(t.name); onClose() }}
                      title={t.is_nsfw ? 'NSFW tag' : `Search for "${t.name}"`}
                    >
                      {t.name}
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>

          <div id="preview-actions">
            {mode === 'search' && (
              <>
                <button className="btn-primary" onClick={onSet}>Set Wallpaper</button>
                <button className="btn-secondary" onClick={onSave}>Save to Library</button>
                <button className="btn-danger" onClick={onDiscard}>Discard</button>
              </>
            )}
            {mode === 'library' && (
              <>
                <button className="btn-danger" onClick={onDiscard}>Discard</button>
                <button className="btn-danger" onClick={onDelete}>Delete</button>
              </>
            )}
            <button className="btn-cancel" onClick={onClose}>Cancel</button>
          </div>
        </div>
      </div>
    </div>
  )
}
