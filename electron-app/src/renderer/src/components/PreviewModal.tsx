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
}

export default function PreviewModal({
  item, mode, localPath, onSet, onSave, onDiscard, onDelete, onClose,
}: PreviewModalProps) {
  const [imageSrc, setImageSrc] = useState<string>('')
  const [loadingImg, setLoadingImg] = useState(true)

  useEffect(() => {
    setLoadingImg(true)
    if (mode === 'library' && item.path) {
      api.readFileAsBase64(item.path)
        .then(setImageSrc)
        .catch(() => setImageSrc(''))
        .finally(() => setLoadingImg(false))
    } else if (item.full_url) {
      api.fetchImage(item.full_url)
        .then(setImageSrc)
        .catch(() => setImageSrc(''))
        .finally(() => setLoadingImg(false))
    } else {
      setLoadingImg(false)
    }
  }, [item, mode])

  useEffect(() => {
    const handleEsc = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }
    document.addEventListener('keydown', handleEsc)
    return () => document.removeEventListener('keydown', handleEsc)
  }, [onClose])

  return (
    <div id="preview-overlay" onClick={(e) => { if (e.target === e.currentTarget) onClose() }}>
      <div id="preview-modal">
        <div id="preview-image-container">
          {imageSrc ? (
            <img src={imageSrc} alt={item.id} id="preview-image" />
          ) : loadingImg ? (
            <div id="preview-loader">Loading…</div>
          ) : (
            <div id="preview-loader" style={{ color: '#e03131' }}>Failed to load image</div>
          )}
        </div>
        <div id="preview-info">
          <span id="preview-id">{item.id}</span>
          {item.resolution && <span>{item.resolution}</span>}
          {item.tags && item.tags.length > 0 && (
            <span id="preview-tags">Tags: {item.tags.slice(0, 8).join(', ')}</span>
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
  )
}
