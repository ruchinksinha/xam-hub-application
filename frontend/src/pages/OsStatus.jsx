import React, { useState, useEffect } from 'react'

function OsStatus() {
  const [osImages, setOsImages] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [deleting, setDeleting] = useState(null)
  const [downloading, setDownloading] = useState(false)
  const [downloadProgress, setDownloadProgress] = useState({})

  const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost'

  const fetchOsImages = async () => {
    try {
      setLoading(true)
      setError(null)
      const response = await fetch(`${API_BASE_URL}/api/os/list`)
      if (!response.ok) {
        throw new Error('Failed to fetch OS images')
      }
      const data = await response.json()
      setOsImages(data.images || [])
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleDelete = async (filename) => {
    if (!confirm(`Are you sure you want to delete ${filename}?`)) {
      return
    }

    try {
      setDeleting(filename)
      const response = await fetch(`${API_BASE_URL}/api/os/delete/${encodeURIComponent(filename)}`, {
        method: 'DELETE'
      })

      if (!response.ok) {
        throw new Error('Failed to delete OS image')
      }

      await fetchOsImages()
    } catch (err) {
      alert(`Failed to delete: ${err.message}`)
    } finally {
      setDeleting(null)
    }
  }

  const formatBytes = (bytes) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
  }

  const formatDate = (timestamp) => {
    return new Date(timestamp * 1000).toLocaleString()
  }

  const handleDownload = async () => {
    try {
      setDownloading(true)
      const response = await fetch(`${API_BASE_URL}/api/os/download`, {
        method: 'POST'
      })

      if (!response.ok) {
        throw new Error('Failed to start download')
      }

      const data = await response.json()

      if (data.already_exists) {
        alert('File already exists')
        await fetchOsImages()
        setDownloading(false)
        return
      }

      pollDownloadProgress()
    } catch (err) {
      alert(`Failed to start download: ${err.message}`)
      setDownloading(false)
    }
  }

  const pollDownloadProgress = async () => {
    const interval = setInterval(async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/api/os/download/progress`)
        if (!response.ok) {
          clearInterval(interval)
          setDownloading(false)
          return
        }

        const data = await response.json()
        setDownloadProgress(data.downloads || {})

        const activeDownloads = Object.values(data.downloads || {})
        const hasActiveDownload = activeDownloads.some(d => d.status === 'downloading')

        if (!hasActiveDownload) {
          clearInterval(interval)
          setDownloading(false)
          await fetchOsImages()

          const hasError = activeDownloads.some(d => d.status === 'error')
          if (hasError) {
            const errorDownload = activeDownloads.find(d => d.status === 'error')
            alert(`Download failed: ${errorDownload.error}`)
          }
        }
      } catch (err) {
        console.error('Error polling progress:', err)
      }
    }, 1000)
  }

  useEffect(() => {
    fetchOsImages()
  }, [])

  const activeDownload = Object.entries(downloadProgress).find(([_, progress]) => progress.status === 'downloading')

  return (
    <div className="os-status-page">
      <div className="page-header">
        <h1>Node OS Status</h1>
        <div className="header-actions">
          <button
            onClick={handleDownload}
            className="btn-download"
            disabled={downloading}
          >
            {downloading ? '⏳ Downloading...' : '⬇️ Download LineageOS'}
          </button>
          <button onClick={fetchOsImages} className="btn-refresh" disabled={loading}>
            🔄 Refresh
          </button>
        </div>
      </div>

      {downloading && activeDownload && (
        <div className="download-progress-card">
          <div className="progress-header">
            <h3>Downloading: {activeDownload[0]}</h3>
            <span className="progress-percentage">{activeDownload[1].progress}%</span>
          </div>
          <div className="progress-bar">
            <div
              className="progress-fill"
              style={{ width: `${activeDownload[1].progress}%` }}
            />
          </div>
          <div className="progress-info">
            <span>{formatBytes(activeDownload[1].downloaded)} / {formatBytes(activeDownload[1].total)}</span>
          </div>
        </div>
      )}

      {loading && (
        <div className="loading-message">
          <p>Loading OS images...</p>
        </div>
      )}

      {error && (
        <div className="error-message">
          <p>Error: {error}</p>
          <button onClick={fetchOsImages} className="btn-retry">Retry</button>
        </div>
      )}

      {!loading && !error && osImages.length === 0 && (
        <div className="empty-message">
          <p>No OS images downloaded yet</p>
          <p className="empty-hint">Click "Download LineageOS" to get started</p>
        </div>
      )}

      {!loading && !error && osImages.length > 0 && (
        <div className="os-images-table">
          <table>
            <thead>
              <tr>
                <th>Filename</th>
                <th>Size</th>
                <th>Downloaded</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {osImages.map((image) => (
                <tr key={image.filename}>
                  <td className="filename-cell">
                    <span className="file-icon">📦</span>
                    {image.filename}
                  </td>
                  <td>{formatBytes(image.size)}</td>
                  <td>{formatDate(image.modified)}</td>
                  <td>
                    <button
                      onClick={() => handleDelete(image.filename)}
                      className="btn-delete"
                      disabled={deleting === image.filename}
                    >
                      {deleting === image.filename ? 'Deleting...' : '🗑️ Delete'}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}

export default OsStatus
